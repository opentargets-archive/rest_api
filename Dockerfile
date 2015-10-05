# base image
FROM debian:jessie
MAINTAINER Andrea Pierleoni <andreap@ebi.ac.uk>

# Install required packages
RUN \
  apt-get update && apt-get install -y --no-install-recommends \
    python-software-properties \
    python-setuptools \
    build-essential \
    supervisor \
    python-dev \
    python \
    wget \
    ca-certificates \
    openssh-server \
    git
RUN wget --no-check-certificate https://raw.github.com/pypa/pip/master/contrib/get-pip.py && \
  python get-pip.py && \
  pip install uWSGI==2.0.9 Flask==0.10.1


# Create directories
RUN mkdir -p /var/www/app  /var/www/app-conf /var/log/supervisor
WORKDIR /var/www/app

#copy code
COPY . /var/www/app


#copy configuration files
COPY docker-conf/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

#install app requirements
RUN pip install -r /var/www/app/requirements.txt && \
  pip install -e git+https://github.com/CTTV/flask-restful-swagger.git@657faa7377f5dcf7718f4e094d50aa2dd86999cf#egg=flask_restful_swagger

#declare app port
EXPOSE 8008

#run supervisor to run uwsgi to run the flask app
CMD ["supervisord"]