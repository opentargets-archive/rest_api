# base image without rest api code to be used in wercker
FROM ubuntu:xenial
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
    nginx-extras

RUN wget --no-check-certificate https://bootstrap.pypa.io/get-pip.py && \
  python get-pip.py


# setup
RUN mkdir -p /var/www/app /var/www/app-conf /var/log/supervisor && \
 rm /etc/nginx/sites-enabled/default && \
 ln -sf /dev/stdout /var/log/nginx/access.log && \
 ln -sf /dev/stderr /var/log/nginx/error.log

WORKDIR /var/www/app



#copy configuration files
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY nginx.conf /etc/nginx/
COPY nginx-rest-api.conf /etc/nginx/sites-enabled/
COPY nginx-servers.conf /etc/nginx/sites-enabled/
COPY server.crt /etc/ssl/nginx/
COPY server.key /etc/ssl/nginx/


#install swagger ui
RUN cd /var/www &&  \
    curl -sL https://github.com/CTTV/swagger-ui/archive/master.tar.gz | tar xz && \
    mv swagger-ui-master swagger-ui

#declare app port
EXPOSE 80 443 8008 8009

#define entrypoint
COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]

#run supervisor to run uwsgi to run the flask app
CMD ["supervisord"]