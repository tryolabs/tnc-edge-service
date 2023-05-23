
## WIP - probably working?

scriptdir="$(dirname -- "$( readlink -f -- "$0")")"

echo "Before running:"
echo "  1. ssh into vpn.riskedge.fish"
echo "  2. stay in the home dir"
echo "  3. run `./easyrsa/easyrsa --pki-dir=tnc-edge-vpn-pki build-client-full <edgeX> nopass`"
echo "  4. cat the files `tnc-edge-vpn-pki/private/edgeX.key` and `tnc-edge-vpn-pki/issued/edgeX.crt `"
echo "  5. edit an existing edgeX.ovpn and paste the key+cert"

function usage {
  echo "Usage:"
  echo "    vpn-install.sh <OpenVPN_Config_File.ovpn>"
}

if [ "x$1" == "x" ] || ! [ -e  "$1" ] ; then
  echo "no OpenVPN config file"
  echo ""
  usage
  exit 1
fi


if ! which openvpn ; then 
  echo "installing openvpn"
  sudo apt -y install openvpn 
fi

sudo cp "$1" /etc/openvpn/client/tnc-edge.conf
sudo systemctl enable openvpn-client@tnc-edge
sudo systemctl restart openvpn-client@tnc-edge

