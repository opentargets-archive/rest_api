from app import create_app, celery
from envparse import env

# Celery worker: Read the flask app config and start the worker(s)
# Celery env to set up the celery broker and backend
env.read_envfile()
app = create_app(env('OPENTARGETS_API_CONFIG', default='default'))
app.app_context().push()

