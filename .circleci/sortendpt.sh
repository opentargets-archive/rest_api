#!/usr/bin/env bash

# Ugly script that checks for the existence of an existing Google Endpoints deployment.
# It spins a new one if:
# - VERSION changed
# - openapi.template.yml has changed
# - new branch

# Requires following env vars to be defined:
# GOOGLE_PROJECT_ID
# CIRCLE_BRANCH
# API_VERSION_MINOR

############

#TODO: decide if to keep master as default.. 
# if [ "${CIRCLE_BRANCH}" != "master" ]; then

# is there an endpoint deployment for this branch?
GCENDPOINT_VERSION=$(gcloud --project ${GOOGLE_PROJECT_ID} service-management \
                     configs list --format json \
                     --service=${CIRCLE_BRANCH}.${GOOGLE_PROJECT_ID}.appspot.com \
                    | jq -r '.[0] | .id') 


if [ -z "$GCENDPOINT_VERSION" ]; then
    # could not find an existing one
    echo -e "\n\n### Could not find an existing Google Endpoints deployment"
    echo -e "### Deploying to Google Endpoints for the ${CIRCLE_BRANCH} branch\n\n"

    envsubst < openapi.template.yaml > openapi.yaml
    gcloud --project ${GOOGLE_PROJECT_ID} service-management deploy openapi.yaml

else
    # could find an endpoint
    echo -e "\n\n### Found a Google Endpoint for ${CIRCLE_BRANCH}.${GOOGLE_PROJECT_ID}.appspot.com"
    
    echo -e "### Checking if the existing config [ ${GCENDPOINT_VERSION} ] matches the version \n\n"
    GCENDPOINT_API_VERSION=$(gcloud --project ${GOOGLE_PROJECT_ID} service-management \
                             configs describe ${GCENDPOINT_VERSION} --format json \
                             --service=${CIRCLE_BRANCH}.${GOOGLE_PROJECT_ID}.appspot.com \
                            | jq -r '.apis[0] | .version')

    #if openapi.template.yaml has changed OR the version file is different
    # than the one deployed, redeploy the new configuration
    if [ "${GCENDPOINT_API_VERSION}" != "${API_VERSION_MINOR}-${CIRCLE_BRANCH}" ] || [ $(git diff "HEAD@{1}" --name-only | grep openapi) ]; then
        echo -e "\n\n### API version mismatch. Re-deploying to Google Endpoints for branch: ${CIRCLE_BRANCH}\n\n"
        envsubst < openapi.template.yaml > openapi.yaml
        gcloud --project ${GOOGLE_PROJECT_ID} service-management deploy openapi.yaml
    else
        echo -e "\n\n### API version matches. Will use the same Google Endpoint deployment.\n\n"
    fi
fi

echo -e "### get the ENDPOINT ID of the deployment to substitute"
export GCENDPOINT_VERSION=$(gcloud --project ${GOOGLE_PROJECT_ID} service-management \
                         configs list --format json \
                         --service=${CIRCLE_BRANCH}.${GOOGLE_PROJECT_ID}.appspot.com \
                        | jq -r '.[0] | .id')