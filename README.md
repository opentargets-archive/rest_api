======================================
FLASK App for the CTTV CoreDB REST API
======================================

To test locally

- clone repository
- ```cd flask-rest-api```
- ```pip install -r requirements.txt``` (possiby in a virtualenv)
- ```python manage.py runserver``` runs the dev server. Do not use in production.
- ```python manage.py runserver -p 8123``` runs the dev server on port `8123`
- ```python manage.py test``` runs the test suites.

By default the rest api is available at [http://localhost:5000](http://localhost:5000)

Swagger YAML documentation is exposed at  [http://localhost:5000/api/docs/swagger.yaml](http://localhost:5000/api/docs/swagger.yaml)

It expects to have an Elasticsearch instance on [http://localhost:9200](http://localhost:9200). 
Alternative configurations are available using the `OPENTARGETS_API_CONFIG` environment variable
Valid `OPENTARGETS_API_CONFIG` options:

- `development`: default option
- `staging`: to be used in staging area
- `production`: to be used in production area
- `dockerlink`: to be used in docker container
- `testing`: to be used for tests

see the `config.py` file for details



Run Docker Container
====================

build the container from source
```bash
docker build -t rest_api:local .
```

and then run the same container. 
Notice you can specify the elasticsearch server using the ELASTICSEARCH_URL environment variable:
```bash
docker run -d -p 8008:80 --name opentargets_rest_api -e "ELASTICSEARCH_URL=http://localhost:9200" --privileged rest_api:local
```

or get it from [docker hub](https://hub.docker.com/r/opentargets/rest_api/builds/)
```bash
docker run -d -p 8008:8008 --name opentargets_rest_api -e "ELASTICSEARCH_URL=http://localhost:9200" --privileged opentargets/rest_api

```
Notice that if you try to map port 80 inside the container with `-p 8008:80` you may get a `403 access forbidden` as it will check the domain to be `*.targetvalidation.org`.
Unless you map `localhost` to `local.targetvalidation.org` in your `/etc/host` this will cause issues.

* Check that is running *
Supposing the container runs in `localhost` and expose port `8008`, Swagger UI is available at: [http://localhost:8008/api-docs](http://localhost:8008/api-docs)
You can check that is talking to Elasticsearch by using the /public/utils/stats method.
