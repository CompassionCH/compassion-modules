#!/bin/sh

# Downloads, builds, and installs OpenCV 3.1.0 to $OPENCV_ROOT/install.
# Note that OPENCV_ROOT has to be set to some writable absolute path
# before calling this script.
# You will have to add $OPENCV_ROOT/install/lib/python2.7/site-packages
# to your PYTHONPATH in order to use OpenCV from python.

set -ex

: "${OPENCV_ROOT?You have to set OPENCV_ROOT before running this script!}"

OPENCV_BUILD_DIR=${OPENCV_ROOT}/build
OPENCV_INSTALL_DIR=${OPENCV_ROOT}/install

git clone https://github.com/Itseez/opencv.git -b 3.1.0 ${OPENCV_ROOT}

mkdir -p ${OPENCV_BUILD_DIR}
mkdir -p ${OPENCV_INSTALL_DIR}

cd ${OPENCV_BUILD_DIR}

cmake \
-DCMAKE_INSTALL_PREFIX=${OPENCV_INSTALL_DIR} \
-DBUILD_PERF_TESTS=OFF \
-DBUILD_TESTS=OFF \
-DBUILD_opencv_java=OFF \
${OPENCV_ROOT}

make -j4
make -j4 install
