#!/bin/bash

# Make sure only root can run our script
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 1>&2
   exit 1
fi

IP=192.168.200.113
USER=openerp

# opencv 
scp $USER@$IP:lib/libopencv/* /usr/local/lib/
./tools/makelink.sh

# python-opencv
scp $USER@$IP:lib/pythonopencv/* /usr/local/lib/python2.7/

# zxing
if [ -d "$HOME/.libZxing" ]; then
    rm -rf $HOME/.libZxing
fi
mkdir $HOME/.libZxing

scp $USER@$IP:lib/zxing/* ~/.libZxing/
