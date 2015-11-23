#!/bin/sh

# Downloads and builds zxing and python-zxing in $ZXING_ROOT.
# Note that ZXING_ROOT has to be set to some writable absolute path
# before calling this script.

# Adapted from install instructions in
# https://github.com/oostendo/python-zxing/blob/master/README.md

set -ex

: "${ZXING_ROOT?You have to set ZXING_ROOT before running this script!}"

ZXING_PYTHON_DIR=${ZXING_ROOT}/python

git clone https://github.com/zxing/zxing.git ${ZXING_ROOT}
cd ${ZXING_ROOT}
# We need a commit that was added after release 3.2.1
# Should be replaced by cloning 3.2.2 as soon as it's available.
git checkout 9910fcfaa9be4e3c81efe7febdb121d59baa07e9

git clone git://github.com/oostendo/python-zxing.git ${ZXING_PYTHON_DIR}
cd ${ZXING_PYTHON_DIR}
# python-zxing does not have a stable release yet, so we just use the latest
# version that we have successfully tested before
git checkout 827db9794fef4d5589a75c89ebd6345338f092ad

cd ${ZXING_ROOT}
# Disable rat plugin to avoid incorrect license header errors; save time by
# not building and running tests.
mvn install -Drat.skip=true -Dmaven.test.skip=true

cd ${ZXING_ROOT}/core
wget http://central.maven.org/maven2/com/google/zxing/core/2.2/core-2.2.jar
mv core-2.2.jar core.jar
mvn install -Drat.skip=true -Dmaven.test.skip=true

cd ${ZXING_ROOT}/javase
wget http://central.maven.org/maven2/com/google/zxing/javase/2.2/javase-2.2.jar
mv javase-2.2.jar javase.jar
mvn install -Drat.skip=true -Dmaven.test.skip=true

cd ${ZXING_PYTHON_DIR}
# Check if bar code reader is working properly:
# - read sample.png that is part of the python-zxing distribution
# - return error code from python -> result can be interpreted in shell script
python -c "from zxing import tests; import sys; tests.testimage='${ZXING_PYTHON_DIR}/zxing/sample.png'; sys.exit(not tests.test_codereader())"
