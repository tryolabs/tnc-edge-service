#!/bin/bash
# visit https://github.com/productOps/tnc-edge-service/settings/actions/runners/new?arch=arm64&os=linux

# replace this entire script with the contents of that webpage!
# (but don't run the ./run.sh line at the end. )

# don't commit the secret token to this file!

# Create a folder
mkdir actions-runner
cd actions-runner

# Download the latest runner package
curl -o actions-runner-linux-arm64-2.304.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.304.0/actions-runner-linux-arm64-2.304.0.tar.gz

# Optional: Validate the hash
echo "34c49bd0e294abce6e4a073627ed60dc2f31eee970c13d389b704697724b31c6  actions-runner-linux-arm64-2.304.0.tar.gz" | shasum -a 256 -c

# Extract the installer
tar xzf ./actions-runner-linux-arm64-2.304.0.tar.gz

# Configure
# Create the runner and start the configuration experience
./config.sh --url https://github.com/productOps/tnc-edge-service --token XXXXXXXX
