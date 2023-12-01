import requests

from datetime import datetime, timezone, timedelta

import boto3


class Token:
    def __init__(self):
        self.token_str = None
        self.token_exp = datetime.now()
    
    def __call__(self):
        if self.token_str and self.token_exp > datetime.now():
            return self.token_str
        
        resp = requests.post(
            'https://api.box.com/oauth2/token',
            data={
                'client_id': "k3pz02l4qjf0asbixuox4wq3cufouf89",
                'client_secret': "gzk5Ct4j490LupgjfPFpbzigHmYgzIKw",
                'grant_type': "client_credentials",
                'box_subject_type': "enterprise",
                'box_subject_id': "994495604",
            }
        )
        j = resp.json()
        self.token_str = j['access_token']
        self.token_exp = datetime.now() + timedelta(seconds=j['expires_in']-200)
        return self.token_str

token = Token()

s = boto3.Session(profile_name='AWSAdministratorAccess-867800856651')
s3 = s.resource('s3')

files_done = []
with open('box_reupload.done', 'r') as f:
    for line in f.readlines():
        r = line.strip()
        if len(r) > 0:
            files_done.append(r)

def folder_get_items(folder_id, offset):
    url='https://api.box.com/2.0/folders/{}/items'.format(folder_id)
    params = {}
    if offset:
        params['offset'] = offset
    headers={"Authorization": "Bearer "+token()}
    print(url, params, headers)
    resp = requests.get(
        url,
        params,
        headers=headers
    )
    return resp.json()



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

root = folder_get_items('0', 0)
for f in filter(lambda x: x['name'] == 'TNC EDGE Trip Video Files', root['entries']):
    folder_ids.append((f['id'], f['name'], 0,))

with open('box_reupload.done', 'a') as new_done:

    while len(folder_ids) > 0:
        (folder_id, folder_name, offset) = folder_ids.pop(0)

        if folder_name.endswith('/gps'):
            continue

        
        j = folder_get_items(folder_id, offset)

        if j['total_count'] - offset > j['limit']:
            print("Warning: folder {} has too many items".format(folder_name))
            folder_ids.append((folder_id, folder_name , offset+100))
        for f in filter(lambda x: x['type'] == 'folder', j['entries']):
            folder_ids.append((f['id'], folder_name + "/" + f['name'], 0))
        for f in filter(lambda x: x['type'] == 'file', j['entries']):
            if f['id'] in files_done:
                continue
            files.append((f['id'], folder_name + "/" + f['name'],))
            url='https://api.box.com/2.0/files/{}/content'.format(f['id'])
            print(url)
            resp = requests.get(
                url,
                headers={"Authorization": "Bearer "+token()}
            )
            with open('tmpfile', 'wb') as tmp:
                tmp.write(resp.content)
            s3.Object('dp.riskedge.fish', folder_name + "/" + f['name']).put(Body=open('tmpfile', 'rb'))
            new_done.write(f['id'] + '\n')
    


for i in files:
    print(files)
