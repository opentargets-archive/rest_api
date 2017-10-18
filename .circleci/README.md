#README

This is the code that defines our CI/CD flow on CircleCI

#### dev
Deploying to `dev` is automatic for all branches. Each **branch** that gets
deployed can be reached as
https://<branchname>-dot-open-targets-eu-dev.appspot.com/v<major>/platform

The version that gets deployed in production and staging is instead versioned by github **tag**. 
To deploy staging add a `staging-*whateveryouwant123` tag and to deploy to
production add a `prod-*` tag.

#### staging
Any `stag-*` tag gets deployed to https://staging-api.opentargets.io). 
Each **tag** that gets deployed can be reached as
https://<tagname>-dot-open-targets-staging.appspot.com/v<major>/platform
as well as https://<tagname>.staging-api.opentargets.io/v<major>/platform

#### production
Any `prod-*` tag gets deployed to https://api.opentargets.io). However:
- Deploying to `production` only happens with manual approval in CircleCI
- Traffic is not migrated automatically and needs to be done manually in each regional project.

Each **tag** that gets deployed can be reached as
https://<tagname>-dot-open-targets-api-prod-<us/jp/eu>.appspot.com/v<major>/platform
as well as through our proxy at https://<tagname>.api.opentargets.io/v<major>/platform
 


### You might want to:

* change ES_URL variables in the `config.yml` to reflect the ES for each project.


### To trigger a production deployment:
```sh
TAG=$( echo staging-test-`date "+%Y%m%d-%H%M"`); git tag $TAG && git push origin $TAG

TAG=$( echo prod-test-`date "+%Y%m%d-%H%M"`); git tag $TAG && git push origin $TAG
```


