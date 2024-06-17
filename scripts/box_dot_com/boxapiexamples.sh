#!/bin/bash

CLIENT_ID=$(jq -r '.[0]' secret_box_creds.json)
CLIENT_SECRET=$(jq -r '.[1]' secret_box_creds.json)

curl -i -X POST "https://api.box.com/oauth2/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "client_id=$CLIENT_ID" \
     -d "client_secret=$CLIENT_SECRET" \
     -d "code=712912" \
     -d "grant_type=authorization_code"

curl -i -X POST "https://api.box.com/oauth2/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "client_id=$CLIENT_ID" \
     -d "client_secret=$CLIENT_SECRET" \
     -d "grant_type=client_credentials" \
     -d "box_subject_type=enterprise"  \
     -d "box_subject_id=15290560022"

curl -i -X POST "https://api.box.com/oauth2/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "client_id=$CLIENT_ID" \
     -d "client_secret=$CLIENT_SECRET" \
     -d "grant_type=client_credentials" \
     -d "box_subject_type=enterprise"  \
     -d "box_subject_id=994495604"

curl -i -X POST "https://api.box.com/oauth2/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "client_id=$CLIENT_ID" \
     -d "client_secret=$CLIENT_SECRET" \
     -d "grant_type=client_credentials" \
     -d "box_subject_type=user"  \
     -d "box_subject_id=15290560022"


curl -v -H 'Authorization: Bearer wYjFjTpWbjNVpnQmADaMnjU9vNJECoXF' 'https://api.box.com/2.0/folders/231635673007/items'
