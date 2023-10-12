import os
import shutil
from pathlib import Path
import subprocess
from subprocess import CompletedProcess
import asyncio
from asyncio import Semaphore, Lock
import fileinput
import io
import sys
import click



async def foo(pipelinelock: Semaphore, inputlock: Lock, cpulock: Semaphore, outputlock: Lock, from_path: Path, tmp_path:Path, to_path: Path, rm_original: bool):
    async with pipelinelock:
        async with inputlock:
            cmd = "cp " + str(from_path.absolute()) + " " + str(tmp_path.absolute())
            print(cmd)
            stdout = io.StringIO()
            stderr = io.StringIO()
            proc = await asyncio.create_subprocess_shell(cmd, asyncio.subprocess.PIPE, asyncio.subprocess.PIPE)
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                print("error copying " +from_path.name+" to tmp folder", stdout.decode(), stderr.decode())
                return
        
        async with cpulock:
            cmd = "gpg -e --batch --trust-model always -r edgedevice --output " + str(tmp_path.absolute()) + ".enc " + str(tmp_path.absolute()) 
            print(cmd)
            proc = await asyncio.create_subprocess_shell(cmd, asyncio.subprocess.PIPE, asyncio.subprocess.PIPE)
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                print("error running gpg " +tmp_path.name+".enc")
                return
        
        async with outputlock:
            cmd = "cp " + str(tmp_path.absolute()) + ".enc " + str(to_path.absolute()) + ".enc"
            print(cmd)
            proc = await asyncio.create_subprocess_shell(cmd, asyncio.subprocess.PIPE, asyncio.subprocess.PIPE)
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                print("error copying " +tmp_path.name+".enc to tmp folder")
                return
        
    cmd = "rm " + str(tmp_path.absolute()) + " " + str(tmp_path.absolute()) + ".enc"
    print(cmd)
    proc = await asyncio.create_subprocess_shell(cmd, asyncio.subprocess.PIPE, asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        print("error cleaning up " +tmp_path.name+" in tmp folder")
        return

    if rm_original:    
        cmd = "rm " + str(from_path.absolute()) 
        print(cmd)
        proc = await asyncio.create_subprocess_shell(cmd, asyncio.subprocess.PIPE, asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            print("error cleaning up " +tmp_path.name+" in tmp folder")
            return



async def setup_stdin(rm_original: bool, same_input_output_lock: bool):

    pipelinelock = Semaphore(10)
    cpulock = Semaphore(5)
    locka = Lock()
    lockb = Lock()

    all = []
    for line in sys.stdin.readlines():
        line = line.strip()
        vid = Path(line)
        if not vid.name.endswith('.avi.done'):
            continue
        
        # print(str(original_path.absolute()))

        tmp_path = Path("/tmp/"+vid.name)
        usb_path = Path("./"+vid.name)

        # print(str(tmp_path.absolute()))
        all.append(asyncio.create_task(foo(pipelinelock, locka, cpulock, locka if same_input_output_lock else lockb, vid, tmp_path, usb_path, rm_original)))
    
    for t in all:
        await t


@click.command()
@click.option('--rm-original', is_flag=True, help='should the original be deleted')
@click.option('--same-input-output-lock', is_flag=True, help='should the original be deleted')
def main(rm_original, same_input_output_lock):
    asyncio.run(setup_stdin(rm_original, same_input_output_lock))

if __name__ == "__main__":
    main()


