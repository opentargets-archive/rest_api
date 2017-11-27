#!/usr/bin/env bash

echo ... will remove all STOPPED AppEngine versions older than 5 days

gcloud --project=$GOOGLE_PROJECT_ID app versions list \
    --format json \
    --filter="(version.createTime < '-p5d') AND version.servingStatus=STOPPED" |\
     jq -r '.[] | .id' |\
     while read id
     do
        echo "Attempting to delete: $id in project $PROJECT"
        # TODO: to fix.. unless you send deletes as a background process,
        #  gcloud interrupts execution after the first succesful deletion (crazy!)
        gcloud --project=$GOOGLE_PROJECT_ID --quiet app versions delete $id || echo 'failed. will try again another time'
     done
