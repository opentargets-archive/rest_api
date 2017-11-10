#!/usr/bin/env bash

# this is complicated because gnu date and BSD date have different implementations
STALEDATE=$(date --version &>/dev/null && date --date="5 days ago" +"%Y-%m-%d" || date -v-5d +"%Y"-"%m"-"%d")
echo "will mark for deletion all Endpoints Versions that do not have existing AppEngine versions anymore"

# get a list of the AppEngine versions that do exist and refer to an endpoint service
gcloud --project=$GOOGLE_PROJECT_ID app versions list --format json | jq -r '.[]| .version.betaSettings.endpoints_service_name' > stillup
gcloud endpoints services list --project $GOOGLE_PROJECT_ID --format json | jq -r '.[]|.serviceName' > endptcfg

#comm will print elements which are just in "endptcfg" (and not in "stillup").
#comm will not print elements that appear just in "stillup". 
comm -23 <(sort endptcfg) <(sort stillup) | while read id
do
    gcloud --quiet --project $GOOGLE_PROJECT_ID endpoints services delete $id --async
done
