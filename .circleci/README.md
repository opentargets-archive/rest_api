#README

This is the code that defines our CI/CD flow on CircleCI

Deploying to `dev` is automatic for all branches. Each **branch** that gets
deployed can be reached as
https://<branchname>-dot-opentargets-eu-dev.appspot.com/v<major>/platform

The `master` branch deployment on our `dev` server is where our staging (https://staging.targetvalidation.org) points too.

Deploying to `production` only happens with manual approval. 

To deploy staging add a `staging-*whateveryouwant123` tag and to deploy to
production add a `prod-*` tag.

The version that gets deployed in production and staging is versioned by github **tag** and
thus can be reached at:
https://<prod-tagname>-dot-opentargets-eu-dev.appspot.com/v<major>/platform


### You might want to:

* change ES_URL variables in the `config.yml` to reflect the ES for each project.


### To trigger a production deployment:
```sh
TAG=$( echo staging-test-`date "+%Y%m%d-%H%M"`); git tag $TAG && git push origin $TAG

TAG=$( echo prod-test-`date "+%Y%m%d-%H%M"`); git tag $TAG && git push origin $TAG
```


