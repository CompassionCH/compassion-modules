#!/bin/bash
# Install the Zxing library in $HOME/.libZxing

################################################################################
#                                                                              #
#                     TO ADD A NEW OPERATION DURING                            #
#                          THE INSTALLATION                                    #
#                  WRITE IN THE FUNCTION START_INSTALL                         #
#                                                                              #
################################################################################



# function that is started when answer is yes
Start_Install ()
{
    if [ ! -d "./zxing" ]; then
	git clone https://github.com/zxing/zxing
    fi
    apt-get update
    apt-get install cmake
    command -v convert >/dev/null 2>&1 || { echo >&2 "Install imagemagick.."; apt-get -y install imagemagick; }
    command -v maven >/dev/null 2>&1 || { echo >&2 "Install maven..";
	command -v gdebi >/dev/null 2>&1 || { echo >&2 "  Install gdebi.."; apt-get -y install gdebi; }
	wget http://ppa.launchpad.net/natecarlson/maven3/ubuntu/pool/main/m/maven3/maven3_3.2.1-0~ppa1_all.deb    
	gdebi maven3_3.2.1-0~ppa1_all.deb
	ln -s /usr/share/maven3/bin/mvn /usr/bin/maven
	rm maven3_3.2.1-0~ppa1_all.deb
    }
    command -v javac >/dev/null 2>&1 || { echo >&2 "Install java..";     apt-get -y install openjdk-7-jdk; }

    cd zxing
    # compile zxing
    maven install
    # -- CORE --
    # remove some file in order to move only the wanted one after
    rm core/target/core-*javadoc.jar
    rm core/target/core-*sources.jar
    # move
    mkdir $HOME/.libZxing
    mv core/target/core-*.jar $HOME/.libZxing/core.jar
    # -- JAVASE --
    rm javase/target/javase-*javadoc.jar
    rm javase/target/javase-*sources.jar
    mv javase/target/javase-*.jar $HOME/.libZxing/javase.jar
    # -- JCOMMANDER --
    mv zxingorg/target/zxingorg-*/WEB-INF/lib/jcommander*.jar $HOME/.libZxing/jcommander.jar
    mv zxingorg/target/zxingorg-*/WEB-INF/lib/jai-imageio-core*.jar $HOME/.libZxing/jai-imageio-core.jar
    cd ..
    # remove useless files
    rm -rf zxing
    chmod -R a+x ~/.libZxing

    # opencv
    git clone https://github.com/Itseez/opencv
    git clone https://github.com/Itseez/opencv_contrib
    sudo apt-get -y install libopencv-dev build-essential cmake git libgtk2.0-dev pkg-config python-dev python-numpy 
    sudo apt-get -y install libdc1394-22 libdc1394-22-dev libjpeg-dev libpng12-dev libtiff4-dev libjasper-dev 
    sudo apt-get -y install libavcodec-dev libavformat-dev libswscale-dev libxine-dev libgstreamer0.10-dev 
    sudo apt-get -y install libgstreamer-plugins-base0.10-dev libv4l-dev libtbb-dev libqt4-dev libfaac-dev 
    sudo apt-get -y install libmp3lame-dev libopencore-amrnb-dev libopencore-amrwb-dev libtheora-dev libvorbis-dev 
    sudo apt-get -y install maklibxvidcore-dev x264 v4l-utils unzip
    mkdir build
    cd build
    cmake -D OPENCV_EXTRA_MODULES_PATH=../opencv_contrib/modules -D CMAKE_BUILD_TYPE=Release -D CMAKE_INSTALL_PREFIX=/usr/local -D BUILD_PYTHON_SUPPORT=ON ../opencv
    make
    make install

    # clean
    cd ..
    rm -rf opencv opencv_contrib build

    exit 0
}


echo "In order to reinstall the libraries, delete the file ~/.libZxing"
# get a copy of the zxing
if [ ! -d "$HOME/.libZxing" ]; then
    Start_Install
fi
