#!/bin/bash

I18_DIR=$(dirname $(readlink -f $0))
PROJECT_ROOT=$(readlink -f ${I18_DIR}/../..)
if [ ! -e ${PROJECT_ROOT}/outerspace.py ]; then
    echo "Please update script to point to proper project root, not $PROJECT_ROOT"
    exit 1
fi
# test for required scripts being available
if ! type msgmerge &> /dev/null;then
    echo "Utility msgmerge is not available, install it. Exiting..."
    exit 1
fi

TRANSLATION_DIR=$PROJECT_ROOT/client/resources/translations/
MESSAGES=${TRANSLATION_DIR}/OSPACE.pot

pushd $PROJECT_ROOT > /dev/null
find ./ -name "*.py" |  sed 's#^\./##' | grep -v "^tools" | xargs python2 ${I18_DIR}/pygettext.py -k N_ -o $MESSAGES && \
    for translation in $TRANSLATION_DIR/*/LC_MESSAGES/*.po; do
        msgmerge -U $translation $MESSAGES
        # as we are on git, no need for backups
        rm ${translation}~ &> /dev/null
    done
popd > /dev/null
