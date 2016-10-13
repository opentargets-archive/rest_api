======================================
FLASK App for the CTTV CoreDB REST API
======================================

To test locally

- clone repository
- ```cd flask-rest-api```
- ```pip install -r requirements.txt``` (possiby in a virtualenv)
- ```python manage.py runserver``` runs the dev server. Do not use in production.
- ```python manage.py test``` runs the test suites.

By default the rest api is available at [http://localhost:5000](http://localhost:5000)

Swagger YAML documentation is exposed at  [http://localhost:5000/api/docs/swagger.yaml](http://localhost:5000/api/docs/swagger.yaml)

It expects to have an Elasticsearch instance on [http://localhost:9200](http://localhost:9200). Alternative configurations are available using the `CTTV_API_CONFIG` environment variable
Valid `CTTV_API_CONFIG` options:

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

run the container. Please use the correct link for the hostname `elastic`, either with the `--link` or the `--ad-host` option
```bash
docker run -d -p 8008:80 --name cttv_rest_api --add-host elastic:10.0.2.2 --ulimit nofile=65535:65535 -e "OPENTARGETS_API_CONFIG=dockerlink" rest_api:local
```

or get it from [quay.io](https://quay.io/repository/cttv/rest_api)
```bash
docker run -d -p 8008:80 --name cttv_rest_api --add-host elastic:10.0.2.2 --ulimit nofile=65535:65535 -e "OPENTARGETS_API_CONFIG=dockerlink" quay.io/cttv/rest_api

```

Supposing the container runs in `localhost` and expose port `8008`, Swagger UI is available at: [http://localhost:8008/api-docs](http://localhost:8008/api-docs)