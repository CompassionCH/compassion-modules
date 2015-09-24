#!/bin/bash
# Install the Zxing library in $HOME/.libZxing

# start Start_Install function when yes (case insesitive)
Yes_No ()
{
  # print question
  echo -n "The directory 'zxing' already exists, do you want to use it?: "

  # read answer
  read YnAnswer

  # all to lower case
  YnAnswer=$(echo $YnAnswer | awk '{print tolower($0)}')

  # check and act on given answer
  case $YnAnswer in
    "yes")  Start_Install ;;
    "no")   rm -rf zxing; ./setup.sh ;;
    *)      echo "Please answer yes or no" ; Yes_No ;;
  esac
}




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
    sudo apt-get update
    sudo apt-get install gdebi openjdk-7-jdk
    wget http://ppa.launchpad.net/natecarlson/maven3/ubuntu/pool/main/m/maven3/maven3_3.2.1-0~ppa1_all.deb    
    sudo gdebi maven3_3.2.1-0~ppa1_all.deb
    sudo ln -s /usr/share/maven3/bin/mvn /usr/bin/maven
    cd zxing
    # compile zxing
    maven install
    # -- CORE --
    # remove some file in order to move only the wanted one after
    rm core/target/core-*javadoc.jar
    rm core/target/core-*sources.jar
    # move
    if [ ! -d "$HOME/.libZxing" ]; then
	mkdir $HOME/.libZxing
    fi
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
    rm maven3_3.2.1-0~ppa1_all.deb
    exit 0
}


# get a copy of the zxing
if [ -d "./zxing" ]; then
    Yes_No
else
    git clone https://github.com/zxing/zxing
    Start_Install
fi
