# About scripts

This folder contains various scripts for the project. The scripts vary from one-time setups to runtime systems.

- system-install.sh
  - Setup script for creating the linux environment on an NVidia Jetson device running Linux4Tegra.
  - Installs linux packages required by the project
  - Sets up some system-level configurations specific to the edge system, like the hardware power target, hardware clock, fan speed, etc.
  - Sets up several systemd units for running python files within this project, including the http server, scheduled python tasks, cleanup scripts, etc.
  - Optionally sets up additional components, like the numpy python package, and AI model lifecycle control systemd units.
  - Idempotent. This script can be re-run without risk of clobbering its own outputs.
- app-install.sh
  - Setup script for creating the python venv and pip installing packages.
  - run after system-install.sh
  - this script is _not_ fully integrated with the new ENVIRONMENT="config/<boat_name>.py" paradigm
- gh_install.sh
  - Setup script to make the edge device a registered Github Actions Self-hosted Runner.
  - Not enabled on the edge
- vpn-install.sh
  - installs the OpenVPN connection to vpn.riskedge.fish
  - this is a separate vpn from THALOS's GlobalProtect vpn
  - Not enabled on the edge. Enabled in some development environments only (the lab).
- adduser_*.sh
  - Script for granting partner employees access to the edge machines.
  - these scripts depend on `secret_*` files for credentials and keys
  - these scripts were never used in production. The partners did not get access to the edge machines.
- netplan-autoswitcher.sh
  - The installation environment used a DHCP network, but the production environment used a static IP network.
  - This script is designed to detect the current environment and switch the linux network model to match
- box_dot_com
  - This collection of scripts is for bulk upload/download between the box.com api and the s3 api.
  - These scripts were only used a handful of times to support data copying requests
- video_bulk_copy
  - This collection of scripts is for copying video files on the edge device from/to USB drives
  - These scripts were only used a handful of times to support data copying requests
 
