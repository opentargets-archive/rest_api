# base image
FROM ubuntu:wily
MAINTAINER Andrea Pierleoni <andreap@ebi.ac.uk>

# Install required packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends python-software-properties \
    build-essential \
    supervisor \
    python-dev \
    python \
    wget \
    curl \
    ca-certificates \
    openssh-server \
    git \
    sqlite3 \
    nginx

RUN wget --no-check-certificate https://bootstrap.pypa.io/get-pip.py && \
  python get-pip.py && \
  pip install uWSGI==2.0.9 Flask==0.10.1


# setup
RUN mkdir -p /var/www/app /var/www/app-conf /var/log/supervisor && \
 rm /etc/nginx/sites-enabled/default && \
 ln -sf /dev/stdout /var/log/nginx/access.log && \
 ln -sf /dev/stderr /var/log/nginx/error.log

WORKDIR /var/www/app
#copy code
COPY . /var/www/app


#copy configuration files
COPY docker-conf/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY docker-conf/nginx.conf /etc/nginx/
COPY docker-conf/nginx-rest-api.conf /etc/nginx/sites-enabled/

#install app requirements
RUN pip install -r /var/www/app/requirements.txt

#install swagger ui
RUN cd /var/www &&  \
    curl -sL https://github.com/CTTV/swagger-ui/archive/master.tar.gz | tar xz && \
    mv swagger-ui-master swagger-ui

#declare app port
EXPOSE 80 8008

#run supervisor to run uwsgi to run the flask app
CMD ["supervisord"]