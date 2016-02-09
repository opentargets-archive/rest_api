======================================
FLASK App for the CTTV CoreDB REST API
======================================

To test locally

- clone repository
- cd flask-rest-api
- pip install -r requirements.txt (possiby in a virtualenv)
- python manage.py runserver

will run the rest api on: http://localhost:5000
swagger is available at: http://localhost:5000/api-docs
it expects to have an elasticsearch instance on http://localhost:9200



Run Docker Container
====================

build the container
```docker build -t cttv_rest_api:local .```

run the container. Please use the correct link for 'elastic', either with the  ```--link``` or the ```--ad-host``` option
```run -d -p 8008:80 --name cttv_rest_api --add-host elastic:10.0.2.2 --ulimit nofile=65535:65535 -e "CTTV_API_CONFIG=dockerlink" cttv_rest_api:local```