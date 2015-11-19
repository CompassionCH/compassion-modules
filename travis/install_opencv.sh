#!/bin/sh

# Downloads, builds, and installs OpenCV 3.0.0 to $OPENCV_ROOT/install.
# Note that OPENCV_ROOT has to be set before calling this script.
# You will have to add $OPENCV_ROOT/install/lib/python2.7/site-packages
# to your PYTHONPATH in order to use OpenCV from python.

set -ex

: "${OPENCV_ROOT?You have to set OPENCV_ROOT before running this script!}"

OPENCV_BUILD_DIR=${OPENCV_ROOT}/build
OPENCV_INSTALL_DIR=${OPENCV_ROOT}/install
OPENCV_CONTRIB_DIR=${OPENCV_ROOT}/contrib

git clone https://github.com/Itseez/opencv.git -b 3.0.0 ${OPENCV_ROOT}
git clone https://github.com/Itseez/opencv_contrib -b 3.0.0 ${OPENCV_CONTRIB_DIR}

mkdir -p ${OPENCV_BUILD_DIR}
mkdir -p ${OPENCV_INSTALL_DIR}

cd ${OPENCV_BUILD_DIR}

cmake \
-DCMAKE_INSTALL_PREFIX=${OPENCV_INSTALL_DIR} \
-DOPENCV_EXTRA_MODULES_PATH=${OPENCV_CONTRIB_DIR}/modules \
-DBUILD_PERF_TESTS=OFF \
-DBUILD_TESTS=OFF \
-DBUILD_opencv_java=OFF \
${OPENCV_ROOT}

make -j4
make -j4 install
