#!/bin/bash
wget -O opencv.zip https://github.com/Itseez/opencv/archive/3.2.0.zip
unzip opencv.zip
cd opencv-3.2.0
mkdir build
cd build
echo "Start cmake"
cmake -D CMAKE_BUILD_TYPE=RELEASE -D CMAKE_INSTALL_PREFIX=/usr/local -D BUILD_NEW_PYTHON_SUPPORT=ON ..
echo "Start make"
make
echo "Start make install"
sudo make install
echo "Opencv successfully installed"