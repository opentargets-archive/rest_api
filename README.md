## Open Targets REST API

Circle CI build: [![CircleCI](https://circleci.com/gh/opentargets/rest_api.svg?style=svg&circle-token=a6f30fb72fe7b0b079ad0f3cd232ef02a43b9e35)](https://circleci.com/gh/opentargets/rest_api)

(maintained, but not used in dev/prod:) [![Docker Repository on Quay](https://quay.io/repository/opentargets/rest_api/status "Docker Repository on Quay")](https://quay.io/repository/opentargets/rest_api)

## How to deploy

Documentation on how we deploy the public version lives at https://github.com/opentargets/rest_api/tree/master/.circleci


## Contributing
### Testing locally

- clone repository
- ```cd flask-rest-api```
- ```pip install -r requirements.txt``` (possiby in a virtualenv)
- ```python manage.py runserver``` runs the dev server. Do not use in production.
- ```python manage.py runserver -p 8123``` runs the dev server on port `8123`
- ```python manage.py test``` runs the test suites.

By default the rest api is available at [http://localhost:5000](http://localhost:5000)

Swagger YAML documentation is exposed at  [http://localhost:5000/api/docs/swagger.yaml](http://localhost:5000/api/docs/swagger.yaml)

### Elasticsearch backend
It expects to have an Elasticsearch instance on [http://localhost:9200](http://localhost:9200). 
Alternative configurations are available using the `OPENTARGETS_API_CONFIG` environment variable
Valid `OPENTARGETS_API_CONFIG` options:

- `development`: default option
- `staging`: to be used in staging area
- `production`: to be used in production area
- `testing`: to be used for tests

see the `config.py` file for details


### debugging
We never run flask directly. Even in the manage.py script we spawn off a
WSGIServer(). Hence Flask debug mode does not work out of the box. 

To debug while running flask locally (ie. using `python manage.py runserver`) 
one can pass `API_DEBUG=True` instead than the traditional `FLASK_DEBUG=True`
environment variable to turn on the Flask debugger and increase the level of logging. 
This works by wrapping the app in werkzeug middleware.
More details on http://stackoverflow.com/questions/10364854/flask-debug-true-does-not-work-when-going-through-uwsgi

However this will not work when the app is run by `uwsgi`, as it is in 
the docker container and in production. _This is intentional since DEBUG
mode there would allow code injection._

## Docker Container
### Build
You can build the container from source:
```bash
docker build -t rest_api:local .
```
or use our docker containers on quay.io ([![Docker Repository on Quay](https://quay.io/repository/opentargets/rest_api/status "Docker Repository on Quay")](https://quay.io/repository/opentargets/rest_api))

### Running with Docker on HTTP

**Pre-requisites**
 * The REST API Docker image URL on [Quay.io](https://quay.io/repository/opentargets/rest_api?tab=tags)
 * The correct image tag for the Open Targets release you're running (e.g. 19.02.1)
 * The URL of the Elasticsearch server
 * The data version, e.g. 19.02
 
```
docker run -p 8080:80 \
-e "ELASTICSEARCH_URL=http://localhost:9200" \
-e "OPENTARGETS_DATA_VERSION=19.02" \
--privileged quay.io/opentargets/rest_api:19.02.1
```

### Running with Docker on HTTPS

**Pre-requisites**

As above, _plus_:

* Appropriate SSL certificates in `./nginx_ssl` called `server.crt` and `server.key`

Naming the certificate and key files `server.crt` and `server.key` means that you don't need to edit `nginx.template`.

Note that this example presents the REST API on port 7443; customise the command as required.

```
docker run -p 7443:443 \
-e "ELASTICSEARCH_URL=http://localhost:9200" \
-e "OPENTARGETS_DATA_VERSION=19.02" \
-v "$(pwd)"/nginx_ssl:/etc/ssl/nginx \
--privileged quay.io/opentargets/rest_api:19.02.1
```

If there are issues with the certificate not being presented, ensure that the volume mapping for `./nginx_ssl` is correct.

For more options available when using `docker run` you can take a look at the [ansible role](https://github.com/opentargets/biogen_instance/blob/master/roles/web/tasks/main.yml) that we use to spin a single instance of our frontend stack.

### Check that it's running

Supposing the container runs in `localhost` and expose port `8080`, Swagger UI is available at: [http://localhost:8080/v3/platform/docs](http://localhost:8080/v3/platform/docs)

You can ping the API with `curl localhost:8080/v3/platform/public/utils/ping`

You can check that is talking to your instance of Elasticsearch by using the `/platform/latest/public/utils/stats` method.

#### Why privileged mode?

The REST API container runs 3 services talking and launching each other: nginx, uwsgi and the actual flask app.
nginx and uwsgi talks trough a binary protocol in a unix socket.
it is very efficient, but by default sockets have a small queue, so if nginx is under heavy load and sends too many requests to uwsgi they get rejected by the socket and raise an error. to increase the size of the queue unfortunately you need root privileges.
at the moment we think that the performance gain is worth the privileged mode. but it strongly depends on the environment you deploy the container into

# Copyright
Copyright 2014-2018 Biogen, Celgene Corporation, EMBL - European Bioinformatics Institute, GlaxoSmithKline, Takeda Pharmaceutical Company and Wellcome Sanger Institute

This software was developed as part of the Open Targets project. For more information please see: http://www.opentargets.org

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

