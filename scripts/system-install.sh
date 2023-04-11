
if ! which iftop ; then sudo apt -y install iftop ; fi
if ! which traceroute ; then sudo apt -y install traceroute ; fi

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


if ! [ -d "$HOME/actions-runner" ] ||
   ! [ -e "$HOME/actions-runner/.runner" ] ||
   ! [ -e "$HOME/actions-runner/.credentials" ]  ; then
  echo "Need to install github.com Self-hosted Actions Runner"
  echo "follow instructions at https://github.com/productOps/dp-tnc-edge/settings/actions/runners/new"
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

[Service]
User=edge
Group=edge
WorkingDirectory=/home/edge/actions-runner
ExecStart=/usr/bin/bash ./run.sh
Restart=always

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


if ! [ -e "/etc/systemd/system/tnc-edge-http.service" ] ; then
  cat > ./tnc-edge-http.service << EOF
[Unit]
Description=TNC Edge Service
After=network.target

[Service]
User=edge
Group=edge
WorkingDirectory=/home/edge/tnc-edge-service
Environment=ENVIRONMENT=/home/edge/tnc-edge-service/config/prod.py
ExecStart=/home/edge/tnc-edge-service/venv/bin/python3 edge_http.py
Restart=always
RestartSec=30

[Install]
WantedBy=default.target

EOF
    sudo cp ./tnc-edge-http.service /etc/systemd/system/tnc-edge-http.service
    rm ./tnc-edge-http.service

    sudo systemctl daemon-reload 
    sudo systemctl enable "tnc-edge-http.service"
    sudo systemctl start "tnc-edge-http.service"
fi


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
CREATE USER edge;
EOF
fi

if ! ( echo "\dt;" | psql edge ) ; then
  sudo -u postgres psql <<EOF
CREATE DATABASE edge;
GRANT ALL ON DATABASE edge TO edge;
EOF
fi
