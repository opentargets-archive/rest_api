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