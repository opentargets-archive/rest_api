#!/usr/bin/env bash
set -o allexport
source VERSION
BASEPATH=/v${API_VERSION}/platform

if [ -z "${DEPLOYEDURL+1}" ]; then

    if [ -n "${CIRCLE_TAG:+1}" ]; then
        DEPLOYEDURL=${CIRCLE_TAG}-dot-${GOOGLE_PROJECT_ID}.appspot.com
    elif [ -n "${CIRCLE_BRANCH:+1}" ]; then
        DEPLOYEDURL=${CIRCLE_BRANCH}-dot-${GOOGLE_PROJECT_ID}.appspot.com
    else
        echo -e "### No CIRCLE_TAG or CIRCLE_BRANCH defined"
        exit 1
    fi
fi

echo -e "### Pointing at ${DEPLOYEDURL}${BASEPATH}\n"


echo -e "### Activating python virtualenv ...\n"
pip install virtualenv
virtualenv venv
. venv/bin/activate
pip install -r .circleci/runscope/requirements.txt

echo -e " Waiting for 200 response from ${DEPLOYEDURL}${BASEPATH}\n"
until $(curl --output /dev/null --silent --head --fail https://${DEPLOYEDURL}${BASEPATH}/public/utils/ping) || (( count++ >= 10 )); do
    printf '.'
    sleep 20
done

echo -e "### Run python script with Runscope Trigger URL\n"
python .circleci/runscope/app.py "https://api.runscope.com/radar/bucket/${RUNSCOPE_BUCKET_UUID}/trigger?runscope_environment=${RUNSCOPE_ENV_UUID_EU_DEV}&host=${DEPLOYEDURL}&basePath=${BASEPATH}"