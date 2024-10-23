import os
import subprocess
import time
from pathlib import Path
from subprocess import CompletedProcess

import click
import schedule
import sqlalchemy as sa
from flask.config import Config as FlaskConfig
from sqlalchemy.orm import Query
from sqlalchemy.orm import sessionmaker as SessionMaker
from sqlalchemy.orm.session import Session

from model import Base as ModelBase
from model import VideoFile

flaskconfig = FlaskConfig(root_path="")

flaskconfig.from_object("config.defaults")
if "ENVIRONMENT" in os.environ:
    flaskconfig.from_envvar("ENVIRONMENT")


def system_gst_check() -> str:
    # nvidia hw encoder
    p: CompletedProcess[str] = subprocess.run(
        "gst-inspect-1.0 | grep -q 'nvv4l2h265enc:'", shell=True, capture_output=False
    )
    if p.returncode == 0:
        return " nvv4l2decoder mjpeg=true ! nvv4l2h265enc bitrate=2000000 "

    # osx hw encoder
    p: CompletedProcess[str] = subprocess.run(
        "gst-inspect-1.0 | grep -q 'vtenc_h265_hw:'", shell=True, capture_output=False
    )
    if p.returncode == 0:
        return " jpegdec ! vtenc_h265_hw bitrate=2000 "
    raise Exception("unknown gst plugins")


gst_internal_plugins = system_gst_check()


def next_videos(session: Session):
    results: Query[VideoFile] = session.query(VideoFile).from_statement(
        sa.text(
            """
        select video_files.* from video_files
        cross join (
            select coalesce(max(start_datetime), to_timestamp(0)) as latest_reencoded
            from video_files
            where video_files.reencoded_stdout is not null
            or video_files.reencoded_stderr is not null
        ) latest_reencoded
        where video_files.decrypted_path is not null
        and video_files.reencoded_stdout is null
        and video_files.reencoded_stderr is null
        and video_files.start_datetime >= latest_reencoded.latest_reencoded
        order by video_files.start_datetime asc;
        """
        )
    )
    return list(results)


def run_reencode(output_dir: Path, sessionmaker: SessionMaker):
    video_files: list[VideoFile] = []

    with sessionmaker() as session:
        video_files = next_videos(session)

    # print(video_files)
    while len(video_files) > 0:
        video_file: VideoFile = video_files.pop(0)
        # print(video_file)
        decrypted_path = Path(video_file.decrypted_path)
        last_dot_index: int = decrypted_path.name.index(".")
        if last_dot_index < 0:
            last_dot_index = None
        mkv_out_file: Path = output_dir / Path(decrypted_path.name[0:last_dot_index] + "_reenc.mkv")

        cmd: str = (
            "gst-launch-1.0 filesrc location='%s' ! avidemux ! \
            %s ! \
            h265parse ! matroskamux ! filesink location='%s'"
            % (str(decrypted_path.absolute()), gst_internal_plugins, str(mkv_out_file.absolute()))
        )

        update_reencoded_path = None

        p: CompletedProcess[str] = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if (
            p.returncode == 0
            and p.stderr.find("No such file") < 0
            and p.stderr.find("Failed to start") < 0
        ):
            update_reencoded_path = str(mkv_out_file.absolute())

            try:
                # shutil.copy(mkv_out_file,  Path('/usbdrive/') / mkv_out_file.name )
                pass
            except:
                # FileNotFoundError or some other permissions error. Drive must not be inserted. Ignore.
                pass

        with sessionmaker() as session:
            session.execute(
                sa.text(
                    "update video_files set \
                                    reencoded_path = :reencoded_path, reencoded_datetime = current_timestamp, \
                                    reencoded_stdout = :reencoded_stdout, reencoded_stderr = :reencoded_stderr \
                                    where decrypted_path = :decrypted_path;"
                ),
                {
                    "reencoded_path": update_reencoded_path,
                    "reencoded_stdout": p.stdout,
                    "reencoded_stderr": p.stderr,
                    "decrypted_path": str(decrypted_path.absolute()),
                },
            )
            session.commit()

        with sessionmaker() as session:
            video_files = next_videos(session)


@click.command()
@click.option("--dbname", default=flaskconfig.get("DBNAME"))
@click.option("--dbuser", default=flaskconfig.get("DBUSER"))
@click.option("--output_dir", default=flaskconfig.get("VIDEO_OUTPUT_DIR"))
@click.option("--print_queue", is_flag=True)
def main(dbname, dbuser, output_dir, print_queue):
    output_dir = Path(output_dir)

    sa_engine = sa.create_engine("postgresql+psycopg2://%s@/%s" % (dbuser, dbname), echo=True)
    sessionmaker = SessionMaker(sa_engine)

    ModelBase.metadata.create_all(sa_engine)

    if print_queue:
        with sessionmaker() as session:
            video_files = next_videos(session)
            for v in video_files:
                print(v.decrypted_path)
        return

    def runonce(output_dir, sessionmaker):
        run_reencode(output_dir, sessionmaker)
        return schedule.CancelJob

    schedule.every(1).seconds.do(runonce, output_dir, sessionmaker)

    schedule.every(5).minutes.do(run_reencode, output_dir, sessionmaker)

    while 1:
        n = schedule.idle_seconds()
        if n is None:
            # no more jobs
            break
        elif n > 0:
            # sleep exactly the right amount of time
            click.echo(f"sleeping for: {n}")
            time.sleep(n)
        schedule.run_pending()


if __name__ == "__main__":
    main()
