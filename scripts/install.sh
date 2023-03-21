
if ! which iftop ; then sudo apt -y install iftop ; fi

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

