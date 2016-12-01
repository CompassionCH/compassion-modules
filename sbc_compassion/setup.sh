#!/bin/bash

# Make sure only root can run our script
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 1>&2
   exit 1
fi

IP=192.168.201.202
USER=erp

# opencv 
scp $USER@$IP:lib/libopencv/* /usr/local/lib/
./tools/makelink.sh

# python-opencv
scp $USER@$IP:lib/pythonopencv/* /usr/local/lib/python2.7/dist-packages/

# zxing is not mandatory anymore to run the sbc module. It has been replaced by zbar which is faster and more robust for our application. This is why this section is commented

# zxing
#if [ -d "$HOME/.libZxing" ]; then
#   rm -rf $HOME/.libZxing
#fi
#mkdir $HOME/.libZxing
#
#scp $USER@$IP:lib/zxing/* ~/.libZxing/
