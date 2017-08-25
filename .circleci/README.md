#README

This is the code that defines our CI/CD flow on CircleCI

Deploying to `dev` is automatic for all branches. Each **branch** that gets
deployed can be reached as
https://<branchname>-dot-opentargets-eu-dev.appspot.com/api/

The `master` branch deployment on our `dev` server is where our staging (https://staging.targetvalidation.org) points too.

Deploying to `production` only happens with manual approval. 

The version that gets deployed in production is versioned by github **tag** and
thus can be reached at can be reached as
https://<prod-tagname>-dot-opentargets-eu-dev.appspot.com/api/


### You might want to:

* change ES_URL variables in the `config.yml` to reflect the ES in your project. Use local urls only
