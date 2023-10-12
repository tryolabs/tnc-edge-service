#!/bin/bash


scriptdir="$(dirname -- "$( readlink -f -- "$0")")"

if [ "$UID" -lt 1000 ] ; then
  echo "This script should be run as a non-root user with 'sudo' access"
  exit 1
fi

if ! [ -e "$scriptdir/secret_adduser_ondeck.txt" ] ; then
  echo "Cannot adduser without secrets file containing password"
  exit 1
fi

USERHOME="/home/ondeck"

sudo /bin/bash <<EOF

adduser ondeck < "$scriptdir/secret_adduser_ondeck.txt"

if ! [ -d "$USERHOME/.ssh" ] ; then
  mkdir "$USERHOME/.ssh"
  chmod go-rwx "$USERHOME/.ssh"
  chown ondeck:ondeck "$USERHOME/.ssh"
fi

if ! [ -e "$USERHOME/.ssh/authorized_keys" ] ; then
  touch "$USERHOME/.ssh/authorized_keys"
  chmod go-rwx "$USERHOME/.ssh/authorized_keys"
  chown ondeck:ondeck "$USERHOME/.ssh/authorized_keys"
fi

while read -r k; do
  if ! grep -q "\$k" "$USERHOME/.ssh/authorized_keys" ; then
    echo "\$k" >> "$USERHOME/.ssh/authorized_keys"
  fi
done <"$scriptdir/ondeck_authorized_keys.txt"

EOF

# mktemp

# ondeck ALL=NOPASSWD: /usr/bin/docker *


gapp_creds_config_line=$(sudo grep -E '^export GOOGLE_APPLICATION_CREDENTIALS=' "$USERHOME/.bashrc")

if [ $? -eq 0 ] && [ "x$gapp_creds_config_line" != "x" ] ; then
  # eval to make this value available in this script
  eval "$gapp_creds_config_line"
else

  # set it up in .bashrc
  sudo /bin/bash <<EOF
echo export GOOGLE_APPLICATION_CREDENTIALS="$USERHOME/google_application_credentials.json" >> "$USERHOME/.bashrc"
EOF

  # and make this value available in this script
  GOOGLE_APPLICATION_CREDENTIALS="$USERHOME/google_application_credentials.json"
fi

if ! [ -e "$GOOGLE_APPLICATION_CREDENTIALS" ] ; then
  if ! [ -e "$scriptdir/secret_ondeck_gcr_token.json" ]  ; then
    echo "cannot find and cannot install google app creds json file!"
    echo "make the creds available in this scripts dir and rerun this script"
    exit 1
  fi
  sudo cp "$scriptdir/secret_ondeck_gcr_token.json" "$GOOGLE_APPLICATION_CREDENTIALS"
  sudo chown ondeck:ondeck "$GOOGLE_APPLICATION_CREDENTIALS"
fi


