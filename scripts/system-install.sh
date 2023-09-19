

SCRIPTNAME="$0"
scriptdir="$(dirname -- "$( readlink -f -- "$0")")"

USERNAME="$(whoami)"
USERHOME="/home/$USERNAME"

cd "$USERHOME"

if [ "$UID" -lt 1000 ] ; then
  echo "This script should be run as a non-root user with 'sudo' access"
  exit 1
fi

if [ "x$ENVIRONMENT" == "x" ] || ! [ -e "$ENVIRONMENT" ] ; then
  echo "No ENVIRONMENT specified. Please add an export ENVIRONMENT line to .bashrc and restart"
  exit 1
fi

function help {
  echo "usage: $SCRIPTNAME  [--do-github] [--do-copy-numpy] "
  exit 1
}

while (( "$#" )); do
   case $1 in
      --do-github)
        DO_GITHUB="y"
         ;;
      --do-copy-numpy)
        DO_COPY_PY_PANDAS_TO_VENV="y"
        ;;
      *)
          help
          ;;
   esac
   shift
done

if ! which iftop ; then sudo apt -y install iftop ; fi
if ! which traceroute ; then sudo apt -y install traceroute ; fi
if ! which jq ; then sudo apt -y install jq ; fi
if ! which curl ; then sudo apt -y install curl ; fi
if ! which mount.cifs ; then sudo apt -y install cifs-utils ; fi
if ! dpkg -s python3-pip | grep "Status: install ok installed" ; then sudo apt -y install python3-pip ; fi
if ! dpkg -s python3-venv | grep "Status: install ok installed" ; then sudo apt -y install python3-venv ; fi
if ! dpkg -s python3-dev | grep "Status: install ok installed" ; then sudo apt -y install python3-dev ; fi
if ! which netplan ; then sudo apt -y install netplan.io ; fi
if ! which rsync ; then sudo apt -y install rsync ; fi
if ! which tmux ; then sudo apt -y install tmux ; fi
if ! which parallel ; then sudo apt -y install parallel ; fi
if ! which par2 ; then sudo apt -y install par2 ; fi
if ! which nmap ; then sudo apt -y install nmap ; fi

WRITE_RTC_UDEV_RULE=0

RTC_UDEV_RULE_FILE="/etc/udev/rules.d/60-rtc-custom.rules"
# RTC_UDEV_RULE_FILE="arst.txt"
RTC_UDEV_RULE_STR='ACTION=="add", SUBSYSTEM=="rtc", ATTRS{hctosys}=="0", RUN+="/usr/sbin/hwclock -s --utc"'

if [ -e "$RTC_UDEV_RULE_FILE" ] ; then
  if grep -q "$RTC_UDEV_RULE_STR" "$RTC_UDEV_RULE_FILE" ; then
    # no need to write udev rule
    WRITE_RTC_UDEV_RULE=1
  fi
fi


if [ $WRITE_RTC_UDEV_RULE ] ; then
    sudo /bin/bash <<EOF
        echo '# set hwclock from the correct clock on startup' > $RTC_UDEV_RULE_FILE
        echo '$RTC_UDEV_RULE_STR' >> $RTC_UDEV_RULE_FILE
EOF
fi


if journalctl -u systemd-timesyncd.service | tail -n 1 | grep -q -E 'synchroniz.*ntp\.org' ; then
    echo "synchronization with online ntp server looks good."
    echo "Running hwclock to set hw time and update drift"
    sudo /bin/bash <<EOF
        hwclock -w --update-drift
EOF
    echo "Success. Run 'sudo hwclock -w --update-drift' in 4 hours"
fi


NEW_PM_ID="$(sed -n 's/^< POWER_MODEL ID=\([0-9]*\) NAME=MODE_15W_6CORE >/\1/p' /etc/nvpmodel.conf)"
if ! ( echo "$NEW_PM_ID" | grep -e '^[0-9][0-9]*$' ) ; then
  NEW_PM_ID="$(sed -n 's/^< POWER_MODEL ID=\([0-9]*\) NAME=15W >/\1/p' /etc/nvpmodel.conf)"
  if ! ( echo "$NEW_PM_ID" | grep -e '^[0-9][0-9]*$' ) ; then
    echo "could not get nv power model from /etc/nvpmodel.conf"
    exit 1
  fi
fi

if ! grep -e '^< PM_CONFIG DEFAULT='"$NEW_PM_ID"' >' /etc/nvpmodel.conf  ; then 
  echo "setting new default power level" 
  sudo sed -i"" 's/^< PM_CONFIG DEFAULT=.* >/< PM_CONFIG DEFAULT='"$NEW_PM_ID"' >/' /etc/nvpmodel.conf
fi

if ! ( sudo nvpmodel -q | grep -e '^'"$NEW_PM_ID"'$' )  ; then 
  echo "setting new power level"  
  sudo nvpmodel -m "$NEW_PM_ID"
fi


if ! (hostname | grep -e '^edge[a-z0-9][a-z0-9]*$' ) ; then
  echo "set the hostname to 'edgeX'!"
  echo "be sure to use the command 'sudo hostnamectl set-hostname <edgeX>'"
  exit 1
fi

if ! grep -E "^127\.[0-9\.]*\s*$(hostname)" /etc/hosts ; then
  if ! grep -E "^127\.[0-9\.]*\s*ubuntu$" /etc/hosts ; then
    echo "aah I assumed the old hostname was 'ubuntu', but it's not in /etc/hosts! exiting!"
    exit 1
  fi
  sudo sed -i"" 's/^127\.\([0-9\.\t ]*\)ubuntu.*$/127.\1'"$(hostname)"'/' /etc/hosts
fi


NVFANCONTROL_FILE=/etc/nvfancontrol.conf
# NVFANCONTROL_FILE=arst.txt

if [ -e "$NVFANCONTROL_FILE" ] ; then 
  if ! grep -q -E "FAN_DEFAULT_PROFILE\s*cool" "$NVFANCONTROL_FILE" ; then 
    sudo /bin/bash <<EOF
      systemctl stop nvfancontrol
      sed -i"" 's/FAN_DEFAULT_PROFILE.*$/FAN_DEFAULT_PROFILE cool/' "$NVFANCONTROL_FILE"
      rm /var/lib/nvfancontrol/status
      systemctl start nvfancontrol
EOF
  fi
fi

if [ "$DO_GITHUB" ] ; then

  if ! [ -d "$USERHOME/actions-runner" ] ||
    ! [ -e "$USERHOME/actions-runner/.runner" ] ||
    ! [ -e "$USERHOME/actions-runner/.credentials" ]  ; then
    echo "Need to install github.com Self-hosted Actions Runner"
    echo "follow instructions at https://github.com/productOps/tnc-edge-service/settings/actions/runners/new"
    echo "if permission is denied, contact github repo admins"
    echo "use these configs:"
    echo "  Enter the name of the runner group ... "
    echo "    hit [Enter] to accept default"
    echo "  Enter the name of the runner:"
    echo "    use convention [edge2] where [2] is unique to this box"
    echo "  Enter any additional labels ... :"
    echo "    add label [edge-jetson]"
    echo "  Enter the name of work folder:"
    echo "    hit [Enter] to accept default"
    echo ""
    echo "rerun this install script when complete"

    exit 1
  fi

  if ! [ -e "/etc/systemd/system/github-actions-runner.service" ] ; then
    cat > ./github-actions-runner.service << EOF
[Unit]
Description=Github Self-served Actions Runner Service
After=network.target
StartLimitIntervalSec=0

[Service]
User=$USERNAME
Group=$USERNAME
WorkingDirectory=$USERHOME/actions-runner
ExecStart=/usr/bin/bash ./run.sh
Restart=always
RestartSec=3600

[Install]
WantedBy=default.target

EOF
      sudo cp ./github-actions-runner.service /etc/systemd/system/github-actions-runner.service
      rm ./github-actions-runner.service

      sudo systemctl daemon-reload 
      sudo systemctl enable "github-actions-runner.service"
      sudo systemctl start "github-actions-runner.service"
  fi

  if ! systemctl is-active "github-actions-runner.service" ; then
    echo "critical issue with github actions runner!"
    echo ""
    journalctl -u github-actions-runner.service
    exit 1
  fi
fi


TMP_FILE="$(mktemp)"
cat > $TMP_FILE << EOF
[Unit]
Description=TNC Edge Service
After=network.target
StartLimitIntervalSec=0

[Service]
User=$USERNAME
Group=$USERNAME
WorkingDirectory=$USERHOME/tnc-edge-service
Environment=ENVIRONMENT=$ENVIRONMENT
ExecStart=$USERHOME/tnc-edge-service/venv/bin/python3 edge_http.py
Restart=always
RestartSec=30

[Install]
WantedBy=default.target

EOF

if ! [ -e "/etc/systemd/system/tnc-edge-http.service" ] ; then
  sudo cp $TMP_FILE /etc/systemd/system/tnc-edge-http.service

  sudo systemctl daemon-reload 
  sudo systemctl enable "tnc-edge-http.service"
  sudo systemctl start "tnc-edge-http.service"
elif ! sudo diff $TMP_FILE /etc/systemd/system/tnc-edge-http.service >/dev/null; then
  sudo cp $TMP_FILE /etc/systemd/system/tnc-edge-http.service

  sudo systemctl daemon-reload 
  sudo systemctl restart "tnc-edge-http.service"
fi
rm $TMP_FILE


if ! systemctl status postgresql ; then
  sudo apt -y install postgresql
fi

if [ -z "$(find /usr/include/ -name libpq-fe.h)" ] ; then
  sudo apt -y install libpq-dev
fi

if ! systemctl is-enabled postgresql ; then
  sudo systemctl daemon-reload 
  sudo systemctl enable postgresql
fi

if ! systemctl is-active postgresql ; then
  sudo systemctl start postgresql
  sleep 2
  if ! systemctl is-active postgresql ; then
      echo "fatal error with postgresql server"
      echo "fix and rerun this script"
      exit 1
  fi
fi

if ! ( echo "select 1;" | psql postgres ) ; then
  sudo -u postgres psql <<EOF
CREATE USER $USERNAME;
EOF
fi

if ! ( echo "\dt;" | psql edge ) ; then
  sudo -u postgres psql <<EOF
CREATE DATABASE edge;
GRANT ALL ON DATABASE edge TO $USERNAME;
EOF
fi

if ! [ -e /etc/docker/daemon.json ] || ! jq -e '.runtimes.nvidia' /etc/docker/daemon.json ; then
  sudo nvidia-ctk runtime configure
  sudo systemctl restart docker.service
fi

if ! python2 -c 'import pip' ; then
  curl https://bootstrap.pypa.io/pip/2.7/get-pip.py -L --output get-pip.py
  python2 get-pip.py
fi

if ! python2 -c 'import virtualenv' ; then
  python2 -m pip install virtualenv
fi


if ! [ -d "$USERHOME/.ssh" ] ; then
  mkdir "$USERHOME/.ssh"
  chmod go-rwx "$USERHOME/.ssh"
fi

if ! [ -e "$USERHOME/.ssh/authorized_keys" ] ; then
  touch "$USERHOME/.ssh/authorized_keys"
  chmod go-rwx "$USERHOME/.ssh/authorized_keys"
fi

while read k; do
  if ! grep -q "$k" "$USERHOME/.ssh/authorized_keys" ; then
    echo "$k" >> "$USERHOME/.ssh/authorized_keys"
  fi
done <"$scriptdir"/edge_authorized_keys.txt



# turn off Ubuntu screen off events
gsettings set org.gnome.desktop.session idle-delay 0
gsettings set org.gnome.desktop.screensaver lock-enabled false
gsettings set org.gnome.desktop.screensaver ubuntu-lock-on-suspend false


# turn off Ubuntu auto apt updates
sudo sed -i"" -e 's/^APT::Periodic::Update-Package-Lists "\?1"\?;/APT::Periodic::Update-Package-Lists "0";/' /etc/apt/apt.conf.d/10periodic
sudo sed -i"" -e 's/^APT::Periodic::Download-Upgradeable-Packages "\?1"\?;/APT::Periodic::Download-Upgradeable-Packages "0";/' /etc/apt/apt.conf.d/10periodic

# systemctl status fwupd
sudo systemctl stop fwupd
sudo systemctl disable fwupd

# disable internet-connectivity polls
if ! [ -e /etc/NetworkManager/conf.d/20-connectivity-ubuntu.conf ] ; then
  # writing to this file overwrites default internet checking behavior. 
  # Empty file means no internet polling
  # see https://askubuntu.com/a/1094558
  sudo touch /etc/NetworkManager/conf.d/20-connectivity-ubuntu.conf
fi

if ! which docker-credential-gcr ; then 
  # rm ./docker-credential-gcr ./docker-credential-gcr.tar.gz
  # curl -L 'https://github.com/GoogleCloudPlatform/docker-credential-gcr/releases/download/v2.1.8/docker-credential-gcr_linux_arm64-2.1.8.tar.gz' -o docker-credential-gcr.tar.gz
  # tar xzf docker-credential-gcr.tar.gz
  # sudo mv ./docker-credential-gcr /usr/local/bin

  # actually, I'm going to copy the script from google's docs:

  VERSION=2.1.8
  OS=linux  # or "darwin" for OSX, "windows" for Windows.
  if [ "x$(uname -p)" == 'xaarch64' ] ; then
    ARCH="arm64"  # or "386" for 32-bit OSs
  elif [ "x$(uname -p)" == 'xx86_64' ] ; then
    ARCH="amd64"  # or "386" for 32-bit OSs
  else
    echo "unknown system architecture"
    exit 1
  fi
  curl -fsSL "https://github.com/GoogleCloudPlatform/docker-credential-gcr/releases/download/v${VERSION}/docker-credential-gcr_${OS}_${ARCH}-${VERSION}.tar.gz" \
  | tar xz docker-credential-gcr \
  && chmod +x docker-credential-gcr \
  && sudo mv docker-credential-gcr /usr/local/bin/
fi

if ! [ -e "$USERHOME/.config/gcloud/docker_credential_gcr_config.json" ] ; then
  docker-credential-gcr config --token-source="env, store"
fi

if ! grep -E '^export GOOGLE_APPLICATION_CREDENTIALS=' "$USERHOME/.bashrc" ; then
  echo "export GOOGLE_APPLICATION_CREDENTIALS=$scriptdir/secret_ondeck_gcr_token.json" >> "$USERHOME/.bashrc"
fi

gsettings set org.gnome.Vino require-encryption false


if ! [ -d "$USERHOME/.aws" ] ; then
  mkdir "$USERHOME/.aws"
fi

if ! [ -e "$USERHOME/.aws/credentials" ] ; then
  if ! [ -e "$scriptdir/secret_aws_creds.txt" ] ; then
    echo "aws secret keys file not found! please add the secret and rerun this script"
    exit 1
  fi

  cp "$scriptdir/secret_aws_creds.txt" "$USERHOME/.aws/credentials"

  chmod go-rwx "$USERHOME/.aws/credentials"
fi


if [ -e "$USERHOME/.gnupg/pubring.kbx" ] && [ "x$USERNAME:$USERNAME" != "x$(stat --format '%U:%G' "$USERHOME/.gnupg/pubring.kbx")" ] ; then
  sudo chown $USERNAME:$USERNAME "$USERHOME/.gnupg/pubring.kbx"
fi


if ! [ -e /etc/netplan/01_eth0_dhcp.yaml* ] ; then
  cat > ./01_eth0_dhcp.yaml <<EOF
network:
  version: 2
  renderer: NetworkManager
  ethernets:
    eth0:
      dhcp4: true
EOF
  sudo cp ./01_eth0_dhcp.yaml /etc/netplan/01_eth0_dhcp.yaml
  rm ./01_eth0_dhcp.yaml
fi

if ! [ -e /etc/netplan/01_eth0_static.yaml* ] ; then
  cat > ./01_eth0_static.yaml <<EOF
network:
  version: 2
  renderer: NetworkManager
  ethernets:
    eth0:
      addresses:
        - 192.168.200.133/24
      nameservers:
      #  search: [mydomain, otherdomain]
        addresses: [192.168.200.7]
      routes: 
        - to: 0.0.0.0/0
          via: 192.168.200.7
EOF
  sudo cp ./01_eth0_static.yaml /etc/netplan/01_eth0_static.yaml.off
  rm ./01_eth0_static.yaml
fi

if ! [ -e "/etc/systemd/system/netplan-autoswitcher.service" ] ; then
  
  sudo cp "$scriptdir/netplan-autoswitcher.sh" /root/netplan-autoswitcher.sh

  cat > ./netplan-autoswitcher.service << EOF
[Unit]
Description=netplan Autoswitcher
After=network.target
StartLimitIntervalSec=0

[Service]
WorkingDirectory=/root
ExecStart=/bin/bash /root/netplan-autoswitcher.sh
Restart=always
RestartSec=120

[Install]
WantedBy=default.target

EOF
    sudo cp ./netplan-autoswitcher.service /etc/systemd/system/netplan-autoswitcher.service
    rm ./netplan-autoswitcher.service

    sudo systemctl daemon-reload 
    # sudo systemctl enable "netplan-autoswitcher.service"
    # sudo systemctl start "netplan-autoswitcher.service"
fi

sudo systemctl stop "netplan-autoswitcher.service"
sudo systemctl disable "netplan-autoswitcher.service"


TMP_FILE="$(mktemp)"
cat > $TMP_FILE << EOF
[Unit]
Description=Thalos Video Auto Decrypt
After=network.target
StartLimitIntervalSec=0

[Service]
User=$USERNAME
Group=$USERNAME
WorkingDirectory=$USERHOME/tnc-edge-service
Environment=ENVIRONMENT=$ENVIRONMENT
ExecStart=$USERHOME/tnc-edge-service/venv/bin/python3 video_fetch.py
Restart=always
RestartSec=300

[Install]
WantedBy=default.target

EOF

if ! [ -e "/etc/systemd/system/thalos-video-autodecrypt.service" ] ; then
  sudo cp $TMP_FILE /etc/systemd/system/thalos-video-autodecrypt.service

  sudo systemctl daemon-reload 
  sudo systemctl enable "thalos-video-autodecrypt.service"
  sudo systemctl start "thalos-video-autodecrypt.service"

elif ! sudo diff $TMP_FILE /etc/systemd/system/thalos-video-autodecrypt.service >/dev/null; then
  sudo cp $TMP_FILE /etc/systemd/system/thalos-video-autodecrypt.service

  sudo systemctl daemon-reload 
  sudo systemctl restart "thalos-video-autodecrypt.service"
fi
rm $TMP_FILE

if ! [ -d "/thalos" ] ; then
  sudo mkdir /thalos
  sudo chmod go+rwx /thalos
fi

if ! [ -d "/videos" ] ; then
  sudo mkdir /videos
  sudo chmod go+rwx /videos
fi

if ! [ -e "/etc/systemd/system/thalos.mount" ] ; then
  cat > ./thalos.mount << EOF
[Unit]
Description=Thalos fileshare mount
Requires=network-online.target
After=network-online.service

[Mount]
What=//192.168.200.5/stockage
Where=/thalos
Options=user=oceanlive,pass=OceanLive56,ro
Type=cifs

[Install]
WantedBy=multi-user.target
EOF
    sudo cp ./thalos.mount /etc/systemd/system/thalos.mount
    rm ./thalos.mount

    sudo systemctl daemon-reload 
fi

if ! [ -e "/etc/systemd/system/thalos.automount" ] ; then
  cat > ./thalos.automount << EOF
[Unit]
Description=Thalos fileshare automounter

[Automount]
Where=/thalos

[Install]
WantedBy=multi-user.target
EOF
    sudo cp ./thalos.automount /etc/systemd/system/thalos.automount
    rm ./thalos.automount

    sudo systemctl daemon-reload 
    sudo systemctl enable thalos.automount
    sudo systemctl start thalos.automount
fi




if ! [ -e "/etc/systemd/system/purge-video.service" ] ; then
  
  sudo cp "$scriptdir/purge-video.sh" /root/purge-video.sh

  cat > ./purge-video.service << EOF
[Unit]
Description=Video auto purge service
After=network.target
StartLimitIntervalSec=0

[Service]
WorkingDirectory=/root
ExecStart=/bin/bash /root/purge-video.sh
Restart=always
RestartSec=1200

[Install]
WantedBy=default.target

EOF
    sudo cp ./purge-video.service /etc/systemd/system/purge-video.service
    rm ./purge-video.service

    sudo systemctl daemon-reload 
    sudo systemctl enable "purge-video.service"
    sudo systemctl start "purge-video.service"
fi


if [ "x$(sudo docker image ls -q gcr.io/edge-gcr/edge-service-image:latest)" != "x" ] ; then

  TMP_FILE="$(mktemp)"
  cat > $TMP_FILE << EOF
[Unit]
Description=Ondeck Runner
After=network.target
StartLimitIntervalSec=0

[Service]
User=$USERNAME
Group=$USERNAME
WorkingDirectory=$USERHOME/tnc-edge-service
Environment=ENVIRONMENT=$ENVIRONMENT
ExecStart=$USERHOME/tnc-edge-service/venv/bin/python3 run_ondeck.py
Restart=always
RestartSec=30

[Install]
WantedBy=default.target

EOF

  if ! [ -e "/etc/systemd/system/ondeck-runner.service" ] ; then
    sudo cp $TMP_FILE /etc/systemd/system/ondeck-runner.service

    sudo systemctl daemon-reload 
    sudo systemctl enable "ondeck-runner.service"
    sudo systemctl start "ondeck-runner.service"

  elif ! sudo diff $TMP_FILE /etc/systemd/system/ondeck-runner.service >/dev/null; then
    sudo cp $TMP_FILE /etc/systemd/system/ondeck-runner.service

    sudo systemctl daemon-reload 
    sudo systemctl restart "ondeck-runner.service"
  fi
  rm $TMP_FILE
fi


TMP_FILE="$(mktemp)"
cat > $TMP_FILE << EOF
[Unit]
Description=Thalos GPS Auto Import
After=network.target
StartLimitIntervalSec=0

[Service]
User=$USERNAME
Group=$USERNAME
WorkingDirectory=$USERHOME/tnc-edge-service
Environment=ENVIRONMENT=$ENVIRONMENT
ExecStart=$USERHOME/tnc-edge-service/venv/bin/python3 gps_fetch.py
Restart=always
RestartSec=300

[Install]
WantedBy=default.target

EOF

if ! [ -e "/etc/systemd/system/gps_fetch.service" ] ; then
  sudo cp $TMP_FILE /etc/systemd/system/gps_fetch.service

  sudo systemctl daemon-reload 
  sudo systemctl enable "gps_fetch.service"
  sudo systemctl start "gps_fetch.service"

elif ! sudo diff $TMP_FILE /etc/systemd/system/gps_fetch.service >/dev/null; then
  sudo cp $TMP_FILE /etc/systemd/system/gps_fetch.service

  sudo systemctl daemon-reload 
  sudo systemctl restart "gps_fetch.service"
fi
rm $TMP_FILE

if [ $DO_COPY_PY_PANDAS_TO_VENV ] ; then
  cp -r /usr/lib/python3/dist-packages/pytz* $USERHOME/tnc-edge-service/venv/lib/python3.8/site-packages/
  cp -r /usr/lib/python3/dist-packages/tzdata* $USERHOME/tnc-edge-service/venv/lib/python3.8/site-packages/
  cp -r /usr/lib/python3/dist-packages/numpy* $USERHOME/tnc-edge-service/venv/lib/python3.8/site-packages/
  cp -r /usr/lib/python3/dist-packages/pandas* $USERHOME/tnc-edge-service/venv/lib/python3.8/site-packages/
fi



TMP_FILE="$(mktemp)"
cat > $TMP_FILE << EOF
[Unit]
Description=S3 Upload Tnc Edge DB
After=network.target
StartLimitIntervalSec=0

[Service]
User=$USERNAME
Group=$USERNAME
WorkingDirectory=$USERHOME/tnc-edge-service
Environment=ENVIRONMENT=$ENVIRONMENT
ExecStart=$USERHOME/tnc-edge-service/venv/bin/python3 s3_uploader.py
Restart=always
RestartSec=3600

[Install]
WantedBy=default.target

EOF

if ! [ -e "/etc/systemd/system/s3_uploader.service" ] ; then
  sudo cp $TMP_FILE /etc/systemd/system/s3_uploader.service

  sudo systemctl daemon-reload 
  sudo systemctl enable "s3_uploader.service"
  sudo systemctl start "s3_uploader.service"

elif ! sudo diff $TMP_FILE /etc/systemd/system/s3_uploader.service >/dev/null; then
  sudo cp $TMP_FILE /etc/systemd/system/s3_uploader.service

  sudo systemctl daemon-reload 
  sudo systemctl restart "s3_uploader.service"
fi
rm $TMP_FILE
