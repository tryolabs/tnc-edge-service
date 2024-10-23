import concurrent.futures
import json
import re
import sys
from datetime import datetime, timedelta, timezone

import boto3
import click
import requests

(client_id, client_secret) = json.load(open("secret_box_creds.json"))


class Token:
    def __init__(self):
        self.token_str = None
        self.token_exp = datetime.now()

    def __call__(self):
        if self.token_str and self.token_exp > datetime.now():
            return self.token_str

        resp = requests.post(
            "https://api.box.com/oauth2/token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "client_credentials",
                "box_subject_type": "enterprise",
                "box_subject_id": "994495604",
            },
        )
        if resp.status_code > 299:
            click.echo(f"{resp.status_code} {resp.headers} {resp.content}")
        j = resp.json()
        self.token_str = j["access_token"]
        self.token_exp = datetime.now() + timedelta(seconds=j["expires_in"] - 200)
        return self.token_str


token = Token()

s = boto3.Session(profile_name="AWSAdministratorAccess-867800856651")
try:
    from secret_aws_s3_creds import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

    s = boto3.Session(
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name="us-east-1",
    )
except:
    pass

s3 = s.resource("s3")


def box_folder_get_items(folder_id, offset):
    url = "https://api.box.com/2.0/folders/{}/items".format(folder_id)
    params = {}
    if offset:
        params["offset"] = offset
    headers = {"Authorization": "Bearer " + token()}
    # print(url, params, headers)
    resp = requests.get(url, params, headers=headers)
    if resp.status_code > 299:
        click.echo(f"{resp.status_code} {resp.headers} {resp.content}")
    return resp.json()


def box_folder_upload_item(folder_id, fname, f):
    url = "https://upload.box.com/api/2.0/files/content"

    headers = {"Authorization": "Bearer " + token()}
    attrs = {"name": fname, "parent": {"id": folder_id}}
    fdict = {
        "attributes": (None, json.dumps(attrs)),
        "file": (fname, f),
    }
    # click.echo(f'{url} {attrs} {headers}')
    resp = requests.post(url, files=fdict, headers=headers)
    if resp.status_code > 299:
        click.echo(f"{resp.status_code} {resp.headers} {resp.content}")
    # click.echo(f'{resp.status_code} {resp.headers} {resp.content}')
    return resp


def box_create_folder(folder_id, fname):
    url = "https://api.box.com/2.0/folders"
    # url = 'http://localhost:50001/2.0/folders'

    headers = {
        "Authorization": "Bearer " + token(),
        "User-Agent": "python-requests/2.32.3",
    }
    data = {"name": fname, "parent": {"id": folder_id}}
    # click.echo(f'{url} {attrs} {headers}')
    resp = requests.post(url, json=data, headers=headers)
    if resp.status_code > 299:
        click.echo(f"{resp.status_code} {resp.headers} {resp.content}")
    # click.echo(f'{resp.status_code} {resp.headers} {resp.content}')
    return resp.json()


@click.group()
def main():
    pass


@main.command()
def iter_box_folder_copy_to_s3():
    files_done = []
    with open("box_reupload.done", "r") as f:
        for line in f.readlines():
            r = line.strip()
            if len(r) > 0:
                files_done.append(r)

    folder_ids = [
        # ('220398416437', 'TNC EDGE Trip Video Files', 0),
        # ("220396095950", "Brancol", 0),
        # ("220391648604", "Manudo", 0),
        # ("220390115242", "Saint Patrick", 0),
        # ("220395794261", "Trip 1", 0),
        # ("220393770739", "Trip 2", 0),
        # ("220394471297", "Trip 3", 0),
        ("220398131847", "TNC EDGE Trip Video Files/Brancol/Trip 4", 0),
        ("220394924873", "TNC EDGE Trip Video Files/Brancol/Trip 5", 0),
        # ("220392935593", "Trip 1", 0),
        # ("220394387963", "Trip 2", 0),
        # ("220391716399", "Trip 3", 0),
        ("220394471384", "TNC EDGE Trip Video Files/Manudo/Trip 4", 0),
        ("220394795442", "TNC EDGE Trip Video Files/Manudo/Trip 5", 0),
        # ("220391925280", "Trip 1", 0),
        # ("220397471565", "Trip 2", 0),
        # ("220391989538", "Trip 3", 0),
        ("220394639856", "TNC EDGE Trip Video Files/Saint Patrick/Trip 4", 0),
        ("220392666703", "TNC EDGE Trip Video Files/Saint Patrick/Trip 5", 0),
    ]
    folder_ids = []

    files = []

    root = box_folder_get_items("0", 0)
    for f in filter(lambda x: x["name"] == "TNC EDGE Trip Video Files", root["entries"]):
        folder_ids.append(
            (
                f["id"],
                f["name"],
                0,
            )
        )

    with open("box_reupload.done", "a") as new_done:
        while len(folder_ids) > 0:
            (folder_id, folder_name, offset) = folder_ids.pop(0)

            if folder_name.endswith("/gps"):
                continue

            j = box_folder_get_items(folder_id, offset)

            if j["total_count"] - offset > j["limit"]:
                print("Warning: folder {} has too many items".format(folder_name))
                folder_ids.append((folder_id, folder_name, offset + 100))
            for f in filter(lambda x: x["type"] == "folder", j["entries"]):
                folder_ids.append((f["id"], folder_name + "/" + f["name"], 0))
            for f in filter(lambda x: x["type"] == "file", j["entries"]):
                if f["id"] in files_done:
                    continue
                files.append(
                    (
                        f["id"],
                        folder_name + "/" + f["name"],
                    )
                )
                url = "https://api.box.com/2.0/files/{}/content".format(f["id"])
                print(url)
                resp = requests.get(url, headers={"Authorization": "Bearer " + token()})
                with open("tmpfile", "wb") as tmp:
                    tmp.write(resp.content)
                s3.Object("dp.riskedge.fish", folder_name + "/" + f["name"]).put(
                    Body=open("tmpfile", "rb")
                )
                new_done.write(f["id"] + "\n")

    for i in files:
        print(files)


def box_navigate_path(path, all_box_folders):
    """
    Use the box.com api to find the folder associated with the path

    :param path:
    the path to find

    :param all_box_folders:
    a dict of box api return values. Key is box folder id. Dict is modified by method

    :return:
    box folder object.
    """

    if not re.match("^/([\w]([\w \.-]*\w)?/)*$", path):
        click.echo(f"bad path: {path}")
        sys.exit(1)

    fnames = path.split("/")[1:-1]

    def box_get_all(folder_id):
        offset = 0
        ret = box_folder_get_items(folder_id, offset)
        last_req = ret
        while last_req.get("total_count") > last_req.get("limit") + offset:
            offset += last_req.get("limit")
            last_req = box_folder_get_items(folder_id, offset)
            ret.get("entries").append(last_req.get("entries"))
        return ret

    if 0 not in all_box_folders.keys():
        root = box_get_all("0")
        root.update({"name": "", "id": "0"})
        all_box_folders[0] = root

    curr = all_box_folders[0]
    for fname in fnames:
        if fname in map(lambda x: x.get("name"), curr.get("entries")):
            f = next(filter(lambda x: x.get("name") == fname, curr.get("entries")))
            f_id = f.get("id")
        else:
            # have to create the folder in box
            resp = box_create_folder(curr.get("id"), fname)
            f_id = resp.get("id")
            curr.get("entries").append({"type": "folder", "id": f_id, "name": fname})

        if f_id in all_box_folders.keys():
            curr = all_box_folders[f_id]
        else:
            # have to populate the folder
            curr = box_get_all(f_id)
            curr.update({"name": fname, "id": f_id})
            all_box_folders[f_id] = curr

    return curr


# python3 box_reupload.py s3-uri-to-box dp.riskedge.fish 'TNC EDGE Trip Video Files/Saint Patrick/alt_hd_upload/'
# python3 box_reupload.py s3-uri-to-box dp.riskedge.fish 'TNC EDGE Trip Video Files/Brancol/alt_hd_upload/'


def byte_range_gen(total_bytes, chunksize):
    offset = 0
    while offset + chunksize < total_bytes:
        r = str(offset) + "-" + str(offset + chunksize - 1)
        # print(f'chunk {r}')
        yield "bytes=" + r
        offset += chunksize
    r = str(offset) + "-" + str(total_bytes - 1)
    # print(f'chunk {r} (last)')
    yield "bytes=" + r


S3_CHUNK_S = int(2 * 1024 * 1024)


@main.command()
@click.option("--dry-run", is_flag=True)
@click.option("--done-filename", default="s3_to_box.done")
@click.option("--max-workers", default=25)
@click.argument("s3_bucket")
@click.argument("s3_path_prefix")
@click.argument("box_name", default="/uncompressed-video/")
def s3_uri_to_box(s3_bucket, s3_path_prefix, box_name, dry_run, done_filename, max_workers):
    print(s3_bucket, s3_path_prefix)
    all_box_folders = dict()

    box_folder = box_navigate_path(box_name, all_box_folders)

    # box_boat_folders_req = box_folder_get_items(m[0].get('id'), 0)
    # box_boat_folders = list(filter(lambda f: f.get('type') == 'folder', box_boat_folders_req.get('entries')))

    already_done = []
    with open(done_filename) as f:
        already_done.extend(map(lambda s: s.strip(), f.readlines()))
    # print(already_done)

    s3c = s.client("s3")

    def iter_s3():
        paginator = s3c.get_paginator("list_objects_v2")
        for page in paginator.paginate(
            Bucket=s3_bucket,
            Prefix=s3_path_prefix,
        ):
            for c in page.get("Contents"):
                yield c.get("Key")

    with open(done_filename, "a") as f:
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as exe1:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as exe2:

                def doit(k):
                    if k in already_done:
                        # print('skipping')
                        return

                    k_split = k.split("/")
                    k_path = k_split[:-1]
                    k_fname = k_split[-1]

                    box_target_path = box_name + "/".join(k_path) + "/"

                    # print("box_target_path", box_target_path)

                    if not dry_run:
                        o = s3.Object(s3_bucket, k)

                        def dl_chunk(range):
                            # print(f"dl chunk {range} start")
                            resp = o.get(Range=range)
                            body = resp.get("Body")
                            b = body.read()
                            # print(f"dl chunk {range} done")
                            return b

                        bs = exe2.map(dl_chunk, byte_range_gen(o.content_length, S3_CHUNK_S))

                        b = b"".join(bs)
                        # resp = o.get()
                        # with resp.get('Body') as streamingBytes:
                        # b = streamingBytes.read()
                        click.echo(f"downloaded {k}")
                        box_target_f = box_navigate_path(box_target_path, all_box_folders)
                        resp = box_folder_upload_item(box_target_f.get("id"), k_fname, b)
                        if resp.status_code < 400:
                            click.echo(f"uploaded {k}")
                            f.write(k + "\n")
                        else:
                            click.echo("failed to upload")

                # print("all s3")
                # print(list(iter_s3()))
                results = list(exe1.map(doit, iter_s3()))
                print("done")


@main.command()
# @click.argument()
def list_box():
    root = box_folder_get_items("0", 0)
    print(root)


@main.command()
@click.option("--dry-run", is_flag=True)
@click.option("--max-workers", default=25)
@click.option("--done-filename", default="box_reupload2.done")
@click.argument("s3_bucket", default="dp.riskedge.fish")
@click.argument("s3_path_prefix", default="TNC EDGE Trip Video Files/Brancol/alt_hd_upload/")
@click.argument("box_name", default="uncompressed-video")
def hq_s3_to_box(dry_run, s3_bucket, s3_path_prefix, box_name, max_workers, done_filename):
    root = box_folder_get_items("0", 0)
    m = list(
        filter(
            lambda f: f.get("name") == box_name and f.get("type") == "folder", root.get("entries")
        )
    )
    if len(m) < 1:
        click.echo("box folder not found")
        sys.exit(1)
    if len(m) > 1:
        click.echo("too many box folders with name")
        sys.exit(1)

    box_boat_folders_req = box_folder_get_items(m[0].get("id"), 0)
    box_boat_folders = list(
        filter(lambda f: f.get("type") == "folder", box_boat_folders_req.get("entries"))
    )

    already_done = []
    with open(done_filename) as f:
        already_done.extend(map(lambda s: s.strip(), f.readlines()))
    # print(already_done)

    s3c = s.client("s3")

    def iter_s3():
        paginator = s3c.get_paginator("list_objects_v2")
        for page in paginator.paginate(
            Bucket=s3_bucket,
            Prefix=s3_path_prefix,
        ):
            for c in page.get("Contents"):
                yield c.get("Key")

    with open(done_filename, "a") as f:

        def doit(k):
            if k in already_done:
                # print('skipping')
                return
            ksplit = k.split("/")
            boat = ksplit[1]
            fname = ksplit[3]
            m = list(filter(lambda f: f.get("name") == boat, box_boat_folders))
            if len(m) < 1:
                click.echo(f"boat folder not found {boat}")
                return
            box_boat_id = m[0].get("id")

            m = re.match("^(\d+T\d+Z_cam[12].avi)(.done)?$", fname)
            if m:
                fname = m[1]
            else:
                m = re.match("^(\d+T\d+Z_cam[12])_reenc.mkv$", fname)
                if m:
                    fname = m[1] + ".mkv"
                else:
                    m = re.match("^(cam[12])_(\d\d-\d\d-\d\d\d\d-\d\d-\d\d).avi(.done)?$", fname)
                    if m:
                        dt = datetime.strptime(m[2], "%d-%m-%Y-%H-%M")
                        dt = dt.replace(tzinfo=timezone.utc)
                        dt_str = (
                            dt.isoformat().replace("-", "").replace(":", "").replace("+0000", "Z")
                        )
                        fname = dt_str + "_" + m[1] + ".avi"
                        print(k + "\n" + fname)
                    else:
                        click.echo(f"no match for fname {fname}")
                        sys.exit(1)

            if fname in already_done:
                # print('skipping')
                return
            if not dry_run:
                resp = s3.Object(s3_bucket, k).get()
                streamingBytes = resp.get("Body")
                b = streamingBytes.read()
                click.echo(f"downloaded {fname}")
                resp = box_folder_upload_item(box_boat_id, fname, b)
                if resp.status_code < 400:
                    click.echo(f"uploaded {fname}")
                    f.write(k + "\n")
                else:
                    click.echo("failed to upload")

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(doit, iter_s3()))
            print("done")


@main.command()
@click.argument("s3_bucket", default="dp.riskedge.fish")
@click.argument("s3_path_prefix", default="TNC EDGE Trip Video Files/Saint Patrick/alt_hd_upload/")
def list_s3(s3_bucket, s3_path_prefix):
    s3c = s.client("s3")

    def iter_s3():
        paginator = s3c.get_paginator("list_objects_v2")
        for page in paginator.paginate(
            Bucket=s3_bucket,
            Prefix=s3_path_prefix,
        ):
            for c in page.get("Contents"):
                yield c.get("Key")

    for k in iter_s3():
        ksplit = k.split("/")
        fname = ksplit[-1]

        m = re.match("^(\d+T\d+Z_cam[12].avi)(.done)?$", fname)
        if m:
            fname = m[1]
        else:
            m = re.match("^(\d+T\d+Z_cam[12])_reenc.mkv$", fname)
            if m:
                fname = m[1] + ".mkv"
            else:
                m = re.match("^(cam[12])_(\d\d-\d\d-\d\d\d\d-\d\d-\d\d).avi(.done)?$", fname)
                if m:
                    dt = datetime.strptime(m[2], "%d-%m-%Y-%H-%M")
                    dt = dt.replace(tzinfo=timezone.utc)
                    dt_str = dt.isoformat().replace("-", "").replace(":", "").replace("+0000", "Z")
                    fname = dt_str + "_" + m[1] + ".avi"
                    # print(k + "\n" + fname)
                else:
                    click.echo(f"no match for fname {fname}")
                    sys.exit(1)
        print(fname)


def list_box_fid(box_folder_id, recurse):
    all_box = []

    offset = 0
    res = box_folder_get_items(box_folder_id, offset)
    all_box.extend(res.get("entries"))
    # print(res)

    while res.get("total_count") > len(res.get("entries")) + res.get("offset"):
        offset += 100
        res = box_folder_get_items(box_folder_id, offset)
        all_box.extend(res.get("entries"))

    if recurse:
        for f in filter(lambda x: x.get("type") == "folder", all_box):
            all_box.extend(list_box_fid(f.get("id"), recurse))

    return all_box


@main.command()
@click.argument("box_name", default="uncompressed-video/Saint Patrick")
@click.option("-r", "recurse", is_flag=True)
def list_box(box_name, recurse):
    # box_name = 'uncompressed-video'
    box_folder_id = "0"
    for fname in box_name.split("/"):
        res = box_folder_get_items(box_folder_id, 0)
        m = list(
            filter(
                lambda f: f.get("name") == fname and f.get("type") == "folder", res.get("entries")
            )
        )
        if len(m) < 1:
            click.echo(f"box folder not found {fname}")
            sys.exit(1)
        if len(m) > 1:
            click.echo(f"too many box folders with name {fname}")
            sys.exit(1)
        box_folder_id = m[0].get("id")

    all_box = list_box_fid(box_folder_id, recurse)

    for f in all_box:
        print(f.get("name"))


@main.command()
@click.argument("box_name", default="uncompressed-video/Saint Patrick")
def move_box(box_name):
    # box_name = 'uncompressed-video'
    box_folder_id = "0"
    for fname in box_name.split("/"):
        res = box_folder_get_items(box_folder_id, 0)
        m = list(
            filter(
                lambda f: f.get("name") == fname and f.get("type") == "folder", res.get("entries")
            )
        )
        if len(m) < 1:
            click.echo(f"box folder not found {fname}")
            sys.exit(1)
        if len(m) > 1:
            click.echo(f"too many box folders with name {fname}")
            sys.exit(1)
        box_folder_id = m[0].get("id")

    def iter_files():
        offset = 0
        res = box_folder_get_items(box_folder_id, offset)
        for entry in res.get("entries"):
            yield entry

        while res.get("total_count") > len(res.get("entries")) + res.get("offset"):
            offset += 100
            res = box_folder_get_items(box_folder_id, offset)
            for entry in res.get("entries"):
                yield entry

    dayfolders = {}
    filestomove = []

    for f in iter_files():
        fname = f.get("name")
        ftype = f.get("type")
        if ftype == "file":
            filestomove.append(f)
        elif ftype == "folder":
            try:
                day_str = fname.split("T")[0]
                if day_str not in dayfolders.keys():
                    dayfolders.update({day_str: f})
            except ValueError as e:
                click.echo(f"unknownfolder {fname}")
        else:
            click.echo(f"unknowntype {ftype} on {fname}")

    # print(dayfolders)
    # print(filestomove[0:2])

    def add_day_folder(parent_id, foldername):
        url = "https://api.box.com/2.0/folders"
        j = {"name": foldername, "parent": {"id": parent_id}}
        print("new folder", url, j)
        resp = requests.post(url, headers={"Authorization": "Bearer " + token()}, json=j)
        return resp.json()

    def move_file_to_folder(box_file_id, box_parent_id):
        url = f"https://api.box.com/2.0/files/{box_file_id}"
        j = {"parent": {"id": box_parent_id}}
        print("moving file", url, j)
        # sys.exit(1)
        resp = requests.put(url, headers={"Authorization": "Bearer " + token()}, json=j)
        return resp.json()

    for f in filestomove:
        fname = f.get("name")
        try:
            day_str = fname.split("T")[0]
            if day_str not in dayfolders.keys():
                resp = add_day_folder(box_folder_id, day_str)
                dayfolders.update({day_str: resp})

            parent = dayfolders.get(day_str)
            move_file_to_folder(f.get("id"), parent.get("id"))

        except ValueError as e:
            click.echo(f"unparsable filedate, cannot move {fname}")


if __name__ == "__main__":
    main()
