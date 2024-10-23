#!/bin/bash

# netplan auto switcher!

if [ "$UID" -gt 0 ]; then
  echo "this script must be run as root"
  exit 1
fi

FOUND=""
for file in /etc/netplan/01_eth0_dhcp.yaml*; do
  if [ -e "$file" ]; then
    FOUND="y"
  fi
done
if ! [ "$FOUND" ]; then
  echo "could not find /etc/netplan/01_eth0_dhcp.yaml*"
  exit 1
fi

FOUND=""
for file in /etc/netplan/01_eth0_static.yaml*; do
  if [ -e "$file" ]; then
    FOUND="y"
  fi
done
if ! [ "$FOUND" ]; then
  echo "could not find /etc/netplan/01_eth0_static.yaml*"
  exit 1
fi

function switch_to_dhcp {
  echo "switching netplan to dhcp"
  mv /etc/netplan/01_eth0_dhcp.yaml* /etc/netplan/01_eth0_dhcp.yaml
  mv /etc/netplan/01_eth0_static.yaml /etc/netplan/01_eth0_static.yaml.off
  netplan apply
  systemctl try-restart openvpn-client@tnc-edge.service github-actions-runner.service
}

function switch_to_static {
  echo "switching netplan to static"
  mv /etc/netplan/01_eth0_static.yaml* /etc/netplan/01_eth0_static.yaml
  mv /etc/netplan/01_eth0_dhcp.yaml /etc/netplan/01_eth0_dhcp.yaml.off
  netplan apply
  systemctl try-restart openvpn-client@tnc-edge.service github-actions-runner.service
}

if grep -q "method=manual" /run/NetworkManager/system-connections/netplan-eth0.nmconnection; then
  ROUTE="$(grep -e "route.*=0.0.0.0/0," /run/NetworkManager/system-connections/netplan-eth0.nmconnection)"
  GATEWAYIP="${ROUTE##*,}"

  if ! ping "$GATEWAYIP" -c 3 >/dev/null 2>&1; then
    switch_to_dhcp
    exit 0
  fi

elif grep -q "method=auto" /run/NetworkManager/system-connections/netplan-eth0.nmconnection; then
  GATEWAYIP="$(nmcli d show eth0 | grep IP4.GATEWAY | awk '{print $2;}')"
  STATICGWIP="$(grep "via:" /etc/netplan/01_eth0_static.yaml* | awk '{print $2;}')"

  if [ "$GATEWAYIP" == "$STATICGWIP" ]; then
    if ping "$STATICGWIP" -c 3 >/dev/null 2>&1; then
      if ping "api.oceanbox2.com" -c 3 >/dev/null 2>&1; then
        switch_to_static
        exit 0
      fi
    fi
  fi

else
  echo "something is wrong with the NetworkManager config that netplan generated"
  exit 1
fi
