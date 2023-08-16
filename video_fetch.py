
from datetime import datetime,timezone,timedelta
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
                    if v.name.endswith(".avi.done"):
                        yield v
    except GeneratorExit:
        return

def is_gpg(f: Path, passphrase_file: str):
    cmd = "cat %s | gpg --pinentry-mode loopback --passphrase-fd 0 \
                    --list-packets %s "%(
                    passphrase_file, 
                    str(f.absolute())
                    )
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return p.returncode == 0

def video_fetch(cpool: SimpleConnectionPool, thalos_dir: Path, output_dir: Path, passphrase_file: str, thalos_video_suffix: str):
    
    for cameradir in filter(lambda x: x.is_dir(), thalos_dir.iterdir()):
       
        new_vids: list[Path] = []

        discovered_matching_last_modified = 0
        last_start_datetime = None

        conn: psycopg2.connection = cpool.getconn()
        try:
            with conn.cursor() as cur:
                for vid_file in depth_first_video_files(cameradir):
                    start_datetime: datetime = datetime.strptime(
                        vid_file.name[0:len('20-07-2023-22-20')],
                        '%d-%m-%Y-%H-%M')
                    start_datetime = start_datetime.replace(tzinfo=timezone.utc)
                    if last_start_datetime is None:
                        last_start_datetime = start_datetime

                    if start_datetime + timedelta(days=2) < last_start_datetime :
                        # ok, we're too far back in time now. No reason to keep going back
                        # I'm done searching.
                        break

                    s = vid_file.stat()
                    last_modified: datetime = datetime.fromtimestamp(s.st_mtime, tz=timezone.utc)
                    cur.execute("select original_path, last_modified from video_files where original_path = %s;", 
                                (str(vid_file.absolute()),))
                    rows = list(cur)
                    if len(rows) == 0:
                        # we have never seen this file before!
                        new_vids.append(vid_file)
                        cur.execute("insert into video_files \
                                    (original_path, last_modified, start_datetime, cam_name) \
                                    values (%s, %s, %s, %s);", (
                            str(vid_file.absolute()), last_modified, start_datetime, cameradir.name))
                        conn.commit()
                    elif rows[0][1] != last_modified:
                        # found it, update the lastmodified
                        cur.execute("update video_files set last_modified = %s where original_path = %s;", 
                                    (last_modified, str(vid_file.absolute())))
                        conn.commit()
                    elif discovered_matching_last_modified > 3:
                        # I found files 4 where the lastmodified matches
                        # I'm done searching.
                        break
                    else:
                        # I can only be here if a row was found and the last_modified matches
                        discovered_matching_last_modified += 1
            
        finally:
            cpool.putconn(conn)

        if len(new_vids) == 0:
            # there are 0 videos for this camera. Skip this camera
            continue
        click.echo("working on {} new videos".format(len(new_vids)))

        new_vids.reverse()

        for new_vid in new_vids:
            s = new_vid.stat()
            last_modified = datetime.fromtimestamp(s.st_mtime, tz=timezone.utc)

            conn: psycopg2.connection = cpool.getconn()
            try:
                with conn.cursor() as cur:
                    cur.execute("select original_path, last_modified, start_datetime, \
                                decrypted_path, decrypted_datetime, stdout, stderr \
                                from video_files where original_path = %s;", (str(new_vid.absolute()),))
                    #schema: (original_path, last_modified, start_datetime, decrypted_path, decrypted_datetime, stdout, stderr)
                    rows = list(cur)
                    if len(rows) == 1 and rows[0][3] is not None:
                        # this script has already decrypted this video
                        # on to the next cameradir
                        continue

                    # compute the output filename
                    start_time: datetime = rows[0][2]
                    start_time = start_time.astimezone(timezone.utc)
                    # print(start_time)
                    str_start_time = start_time.isoformat().replace('-', '').replace(':', '').replace('+0000', 'Z')
                    output_filename = str_start_time + "_" + cameradir.name + ".avi"
                    # if output_filename.endswith('.done'):
                    #     output_filename = output_filename[0:-5]
                    output_file = Path(output_dir, output_filename)

                    # gpg decrypt the video
                    cmd = None
                    if is_gpg(new_vid, passphrase_file):
                        cmd = "cat %s | gpg --batch --yes \
                            --pinentry-mode loopback --passphrase-fd 0 \
                            --decrypt --output %s %s "%(
                            passphrase_file, 
                            str(output_file.absolute()), 
                            str(new_vid.absolute())
                            )
                    else:
                        cmd = "cp %s %s"%(
                            str(new_vid.absolute()),
                            str(output_file.absolute())
                            )
                    p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    if p.returncode == 0:
                        cur.execute("update video_files set decrypted_path = %s, \
                                    decrypted_datetime = %s, stdout = %s, stderr = %s \
                                    where original_path = %s;", (
                            str(output_file.absolute()), datetime.now(tz=timezone.utc), 
                            p.stdout, p.stderr, 
                            str(new_vid.absolute()))
                        )
                        conn.commit()
                    else:
                        cur.execute("update video_files set decrypted_path = %s, \
                                    decrypted_datetime = %s, stdout = %s, stderr = %s \
                                    where original_path = %s;", (
                            None, datetime.now(tz=timezone.utc), 
                            p.stdout, p.stderr, 
                            str(new_vid.absolute()))
                        )
                        conn.commit()
            finally:
                cpool.putconn(conn)

@click.command()
@click.option('--dbname', default=flaskconfig.get('DBNAME'))
@click.option('--dbuser', default=flaskconfig.get('DBUSER'))
@click.option('--thalos_video_dir', default=flaskconfig.get('THALOS_VIDEO_DIR'))
@click.option('--output_dir', default=flaskconfig.get('VIDEO_OUTPUT_DIR'))
@click.option('--passphrase_file', default=flaskconfig.get('VIDEO_PASSPHRASE_FILE'))
@click.option('--thalos_video_suffix', default=flaskconfig.get('THALOS_VIDEO_SUFFIX'))
@click.option('--print_latest', is_flag=True)
def main(dbname, dbuser, thalos_video_dir, output_dir, passphrase_file, thalos_video_suffix, print_latest):

    thalos_dir = Path(thalos_video_dir)
    output_dir = Path(output_dir)

    if print_latest:
        for cameradir in filter(lambda x: x.is_dir(), thalos_dir.iterdir()):
            i=0
            for vid_file in depth_first_video_files(cameradir):
                if i > 1:
                    break

                s = vid_file.stat()
                last_modified = datetime.fromtimestamp(s.st_mtime, tz=timezone.utc)
                click.echo("{} ({})".format(str(vid_file.absolute()), str(last_modified)))
                i+=1
        return

    cpool = SimpleConnectionPool(1, 1, database=dbname, user=dbuser)

    def runonce(cpool, thalos_dir, output_dir, passphrase_file, thalos_video_suffix):
        video_fetch(cpool, thalos_dir, output_dir, passphrase_file, thalos_video_suffix)
        return schedule.CancelJob

    schedule.every(1).seconds.do(runonce, cpool, thalos_dir, output_dir, passphrase_file, thalos_video_suffix )

    schedule.every(5).minutes.do(video_fetch, cpool, thalos_dir, output_dir, passphrase_file, thalos_video_suffix )


    while 1:
        n = schedule.idle_seconds()
        if n is None:
            # no more jobs
            click.echo("No more jobs. exiting")
            break
        elif n > 0:
            # sleep exactly the right amount of time
            click.echo("sleeping for: {}".format(n))
            time.sleep(n)
        schedule.run_pending()

if __name__ == '__main__':
    main()
