#README

This is the code that defines our CI/CD flow on CircleCI

#### dev
Deploying to `dev` is automatic for all branches. 
However only the `master` branch is kept running at all times. All other branches are turned off by default (see the `stop-instance` step in config.yml). To allow traffic to pass, one must "start" the instance in the appEngine console.
We have chosen to do this to keep AppEngine costs down.

Each **branch** that gets deployed and has been started can be reached as
https://<branchname>-dot-open-targets-eu-dev.appspot.com/v<major>/platform

The version that gets deployed in production and staging is instead versioned by github **tag**. 
To deploy staging add a `staging-*whateveryouwant123` tag and to deploy to
production add a `prod-*` tag.

#### staging
Any `stag-*` tag gets deployed to https://staging-api.opentargets.io). 
Each **tag** that gets deployed can be reached as
https://<tagname>-dot-open-targets-staging.appspot.com/v<major>/platform
as well as https://<tagname>.staging-api.opentargets.io/v<major>/platform

Notice that `staging`, differently than `dev`, has a nginx proxy working in front of it. This replicates the production environment and allows load testing with loader.io (there is a token in the nginx.conf that authorizes the domain).

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
TAG=$( echo staging-`date "+%Y%m%d-%H%M"`); git tag $TAG && git push origin $TAG

TAG=$( echo prod-`date "+%Y%m%d-%H%M"`); git tag $TAG && git push origin $TAG
```

### To delete stale "test" tags (except the last two):

```sh
git tag | grep prod-test | head -n -2 | xargs -n 1 -I% gitpush --delete origin %

git tag | grep staging-test | head -n -2 | xargs -n 1 -I% gitpush --delete origin %

```


## What about VERSION?
Deployment does not depend on a change in the VERSION file, but a different version will trigger a new google endpoint deployment and a new `openapi.yaml` specification

Each change in the API should correspond to a version change. 
To change the version, one needs to update the `VERSION` file. This automatically propagates to:
- openapi.yaml template and thus google endpoint definition
- swagger.yaml documentation

