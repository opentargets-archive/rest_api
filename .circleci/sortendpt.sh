#!/usr/bin/env bash

# Ugly script that checks for the existence of an existing Google Endpoints deployment.
# It spins a new one if:
# - VERSION changed
# - new branch

# Requires following env vars to be defined:
# GOOGLE_PROJECT_ID
# CIRCLE_BRANCH or CIRCLE_TAG
# API_VERSION_MINOR

############

if [ -n "${CIRCLE_TAG:+1}" ]; then
    export APPENG_VERSION=${CIRCLE_TAG}
elif [ -n "${CIRCLE_BRANCH:+1}" ]; then
    export APPENG_VERSION=${CIRCLE_BRANCH}
else
    echo -e "### No CIRCLE_TAG or CIRCLE_BRANCH defined"
    exit 1
fi

#TODO: decide if to keep master as default.. 
# if [ "${APPENG_VERSION}" != "master" ]; then


# is there an endpoint deployment for this branch?
if GCENDPOINT_VERSION=$(gcloud --project ${GOOGLE_PROJECT_ID} service-management \
                     configs list --format json \
                     --service=${APPENG_VERSION}.${GOOGLE_PROJECT_ID}.appspot.com \
                    | jq -r '.[0] | .id') ; then
    
    # yes, we could find an endpoint..
    echo -e "\n### Found a Google Endpoint for ${APPENG_VERSION}.${GOOGLE_PROJECT_ID}.appspot.com"
    
    echo -e "### Checking if the existing config [ ${GCENDPOINT_VERSION} ] matches the version \n"
    GCENDPOINT_API_VERSION=$(gcloud --project ${GOOGLE_PROJECT_ID} service-management \
                             configs describe ${GCENDPOINT_VERSION} --format json \
                             --service=${APPENG_VERSION}.${GOOGLE_PROJECT_ID}.appspot.com \
                            | jq -r '.apis[0] | .version')

    #if openapi.template.yaml has changed OR the version file is different
    # than the one deployed, redeploy the new configuration
    
    # NOTE how for tags (ie. when CIRCLE_BRANCH is unset) the API_VERSION_MINOR
    # should revert to plain semantic versioning.
    if [ "${GCENDPOINT_API_VERSION}" != "${API_VERSION_MINOR}${CIRCLE_BRANCH}" ] || [ $(git diff "HEAD@{1}" --name-only | grep openapi) ]; then
        echo -e "\n\n### API version mismatch or openAPI definition changed. "
        echo -e "### Re-deploying to Google Endpoints for API version: ${API_VERSION_MINOR}${CIRCLE_BRANCH}\n\n"
        envsubst < openapi.template.yaml > openapi.yaml
        gcloud --project ${GOOGLE_PROJECT_ID} service-management deploy openapi.yaml
    else
        echo -e "\n\n### API version matches. Will use the same Google Endpoint deployment.\n\n"
    fi
else
    # could not find an existing one
    echo -e "\n### Could not find an existing Google Endpoints deployment"
    echo -e "### Deploying to Google Endpoints for the [${APPENG_VERSION}.${GOOGLE_PROJECT_ID}.appspot.com] service\n"

    envsubst < openapi.template.yaml > openapi.yaml
    gcloud --project ${GOOGLE_PROJECT_ID} service-management deploy openapi.yaml
fi


echo -e "### get the ENDPOINT ID of the deployment to substitute"
export GCENDPOINT_VERSION=$(gcloud --project ${GOOGLE_PROJECT_ID} service-management \
                         configs list --format json \
                         --service=${APPENG_VERSION}.${GOOGLE_PROJECT_ID}.appspot.com \
                        | jq -r '.[0] | .id')