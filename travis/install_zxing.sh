#!/bin/sh

# Downloads and builds zxing and python-zxing in $ZXING_ROOT.
# Note that ZXING_ROOT has to be set to some writable absolute path
# before calling this script.

# Adapted from install instructions in
# https://github.com/oostendo/python-zxing/blob/master/README.md

set -ex

: "${ZXING_ROOT?You have to set ZXING_ROOT before running this script!}"

ZXING_VERSION=3.2.2-SNAPSHOT

git clone https://github.com/zxing/zxing.git ${ZXING_ROOT}
cd ${ZXING_ROOT}
# We need a commit that was added after release 3.2.1
# Should be replaced by cloning 3.2.2 as soon as it's available.
git checkout 9910fcfaa9be4e3c81efe7febdb121d59baa07e9

cd ${ZXING_ROOT}
# Disable rat plugin to avoid incorrect license header errors; save time by
# not building and running tests.
mvn install -Drat.skip=true -Dmaven.test.skip=true -Dmaven.javadoc.skip=true
cp zxingorg/target/zxingorg-${ZXING_VERSION}/WEB-INF/lib/jcommander-*.jar jcommander.jar
cp zxingorg/target/zxingorg-${ZXING_VERSION}/WEB-INF/lib/jai-imageio-core-*.jar jai-imageio-core.jar

cd ${ZXING_ROOT}/core
mvn install -Drat.skip=true -Dmaven.test.skip=true -Dmaven.javadoc.skip=true
cp target/core-${ZXING_VERSION}.jar ../core.jar

cd ${ZXING_ROOT}/javase
mvn install -Drat.skip=true -Dmaven.test.skip=true -Dmaven.javadoc.skip=true
cp target/javase-${ZXING_VERSION}.jar ../javase.jar
