#!/bin/bash 
umount /myshare || true
set -e
mkdir -p /myshare 
mount -t cifs -o "username=$mount_username,password=$mount_password,vers=2.0" $nas_path/CGOAnsible$/Tenable /myshare
mkdir -p /tmp/tenable 
cp -p /myshare/* /tmp/tenable
cd /tmp/tenable
rpm -ivh /tmp/tenable/NessusAgent-10.2.1-es8.x86_64_RH8.rpm
/opt/nessus_agent/sbin/nessuscli agent link --host=cloud.tenable.com --port=443 --key=9819640248148aef1d21f8d48fe2f70072aa45a016e3604508f2ca45dc77fa71
/sbin/service nessusagent start