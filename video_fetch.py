
from datetime import datetime,timezone
import click
import codecs
import os
from pathlib import Path
import psycopg2
from psycopg2.pool import SimpleConnectionPool
import re
import schedule
import subprocess
import time


# py38encodings = ['ascii', 'utf_32', 'utf_32_be', 'utf_32_le', 'utf_16', 'utf_16_be', 'utf_16_le', 'utf_7',
#  'utf_8', 'utf_8_sig','big5', 'big5hkscs', 'cp037', 'cp273', 'cp424', 'cp437', 'cp500', 'cp720',
#  'cp737', 'cp775', 'cp850', 'cp852', 'cp855', 'cp856', 'cp857', 'cp858', 'cp860', 'cp861', 'cp862',
#  'cp863', 'cp864', 'cp865', 'cp866', 'cp869', 'cp874', 'cp875', 'cp932', 'cp949', 'cp950', 'cp1006',
#  'cp1026', 'cp1125', 'cp1140', 'cp1250', 'cp1251', 'cp1252', 'cp1253', 'cp1254', 'cp1255', 'cp1256',
#  'cp1257', 'cp1258', 'euc_jp', 'euc_jis_2004', 'euc_jisx0213', 'euc_kr', 'gb2312', 'gbk', 'gb18030',
#  'hz', 'iso2022_jp', 'iso2022_jp_1', 'iso2022_jp_2', 'iso2022_jp_2004', 'iso2022_jp_3', 'iso2022_jp_ext',
#  'iso2022_kr', 'latin_1', 'iso8859_2', 'iso8859_3', 'iso8859_4', 'iso8859_5', 'iso8859_6', 'iso8859_7',
#  'iso8859_8', 'iso8859_9', 'iso8859_10', 'iso8859_11','iso8859_13', 'iso8859_14', 'iso8859_15',
#  'iso8859_16', 'johab', 'koi8_r', 'koi8_t', 'koi8_u', 'kz1048', 'mac_cyrillic', 'mac_greek',
#  'mac_iceland', 'mac_latin2', 'mac_roman', 'mac_turkish', 'ptcp154', 'shift_jis', 'shift_jis_2004',
#  'shift_jisx0213', ]

# # print(subprocess.run("echo $SHELL", shell=True, capture_output=True))
# loc_enc = subprocess.run("echo $LANG | awk '{split($0, a, \".\"); printf a[2]}'", shell=True, capture_output=True)
# # print(loc_enc)
# def findencoding():
#     for e in py38encodings:
#         try:
#             found = codecs.lookup(loc_enc.stdout.decode(e))
#             return found
#         except:
#             pass
#     raise Exception('shell encoding not found')

# shell_enc = findencoding().name

from flask.config import Config as FlaskConfig
flaskconfig = FlaskConfig(root_path='')

flaskconfig.from_object('config.defaults')
if 'ENVIRONMENT' in os.environ:
    flaskconfig.from_envvar('ENVIRONMENT')

def depth_first_video_files(cameradir: Path):
    try:
        date_dirs = [x for x in cameradir.iterdir() if x.is_dir()]
        date_dirs.sort(key=lambda x: datetime.strptime(x.name, '%d-%m-%Y'), reverse=True)
        for date_dir in date_dirs:
            hour_dirs = [x for x in date_dir.iterdir() if x.is_dir()]
            hour_dirs.sort(key=lambda x: int(x.name), reverse=True)
            for hour_dir in hour_dirs:
                vid_files = [x for x in hour_dir.iterdir() if x.is_file() and re.match('.*-(\d+)\.', x.name)]
                vid_files.sort(key=lambda x: re.match('.*-(\d+)\.', x.name)[1], reverse=True)
                for v in vid_files:
                    yield v
    except GeneratorExit:
        return


def job(cpool: SimpleConnectionPool, thalos_dir: Path, output_dir: Path, passphrase_file: str):


    # cmd = "mount | grep -q /tmp/thalos"%()
    # p = subprocess.run(cmd, shell=True, capture_output=False)
    # if p.returncode != 0:
    #     print("video cifs not mounted")
    #     return
    

    
    for cameradir in filter(lambda x: x.is_dir(), thalos_dir.iterdir()):
       
        last_two = []

        conn: psycopg2.connection = cpool.getconn()
        try:
            with conn.cursor() as cur:
                for vid_file in depth_first_video_files(cameradir):
                    if len(last_two) < 2:
                        last_two.append(vid_file)

                    s = vid_file.stat()
                    last_modified = datetime.fromtimestamp(s.st_mtime, tz=timezone.utc)
                    cur.execute("select original_path, last_modified from video_files where original_path = %s;", (str(vid_file.absolute()),))
                    rows = list(cur)
                    if len(rows) == 0:
                        # we have never seen this file before!
                        cur.execute("insert into video_files (original_path, last_modified) values (%s, %s);", (str(vid_file.absolute()), last_modified))
                        conn.commit()
                    elif rows[0][1] != last_modified:
                        # found it, update the lastmodified
                        cur.execute("update video_files set last_modified = %s where original_path = %s;", (last_modified, str(vid_file.absolute())))
                        conn.commit()
                    elif len(last_two) >= 2:
                        # I found files where the lastmodified matches
                        # if I found my 2, then I'm done searching.
                        break
                cur.close()
        finally:
            cpool.putconn(conn)

        if len(last_two) < 2:
            # there are 0 or 1 videos for this camera. Wait a bit for this camera
            continue

        penultimate_vid = last_two[-1]

        s = penultimate_vid.stat()
        last_modified = datetime.fromtimestamp(s.st_mtime, tz=timezone.utc)

        conn: psycopg2.connection = cpool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("select * from video_files where original_path = %s;", (str(penultimate_vid.absolute()),))
                #schema: (original_path, last_modified, decrypted_path, decrypted_datetime, stdout, stderr)
                rows = list(cur)
                if len(rows) == 1 and rows[0][3] is not None:
                    # this script has already decrypted this video
                    # on to the next cameradir
                    continue

                # gpg decrypt the video

                output_file = Path(output_dir, penultimate_vid.name)

                cmd = "cat %s | gpg --batch --yes \
                    --pinentry-mode loopback --passphrase-fd 0 \
                    --decrypt --output %s %s "%(
                    passphrase_file, 
                    str(output_file.absolute()), 
                    str(penultimate_vid.absolute())
                    )
                p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if p.returncode == 0:
                    cur.execute("update video_files set decrypted_path = %s, \
                                decrypted_datetime = %s, stdout = %s, stderr = %s \
                                where original_path = %s;", (
                        str(output_file.absolute()), datetime.now(tz=timezone.utc), 
                        p.stdout, p.stderr, 
                        str(penultimate_vid.absolute()))
                    )
                    conn.commit()
                else:
                    cur.execute("update video_files set decrypted_path = %s, \
                                decrypted_datetime = %s, stdout = %s, stderr = %s \
                                where original_path = %s;", (
                        None, datetime.now(tz=timezone.utc), 
                        p.stdout, p.stderr, 
                        str(penultimate_vid.absolute()))
                    )
                    conn.commit()

                cur.close()
        finally:
            cpool.putconn(conn)

@click.command()
@click.option('--dbname')
@click.option('--dbuser')
@click.option('--thalos_video_dir', default='/thalos/videos')
@click.option('--output_dir', default='/videos')
@click.option('--passphrase_file', default='/dev/null')
def main(dbname, dbuser, thalos_video_dir, output_dir, passphrase_file):

    if not dbname:
        dbname = flaskconfig.get('DBNAME')
    if not dbuser:
        dbuser = flaskconfig.get('DBUSER')

    thalos_dir = Path(thalos_video_dir)
    output_dir = Path(output_dir)

    cpool = SimpleConnectionPool(1, 1, database=dbname, user=dbuser)
    
    schedule.every(5).seconds.do(job, cpool, thalos_dir, output_dir, passphrase_file )

    while 1:
        n = schedule.idle_seconds()
        if n is None:
            # no more jobs
            break
        elif n > 0:
            # sleep exactly the right amount of time
            print("sleeping for:", n)
            time.sleep(n)
        schedule.run_pending()

if __name__ == '__main__':
    main()
