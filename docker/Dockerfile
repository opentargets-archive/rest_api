FROM quay.io/opentargets/opentargets_rest_api_base
LABEL maintainer="ops@opentargets.org"


# setup
RUN mkdir -p /var/www/app /var/www/app-conf /var/log/supervisor && \
 rm /etc/nginx/sites-enabled/default && \
 ln -sf /dev/stdout /var/log/nginx/access.log && \
 ln -sf /dev/stderr /var/log/nginx/error.log


#copy configuration files
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY docker/nginx.conf /etc/nginx/
COPY docker/nginx-rest-api.conf /etc/nginx/sites-enabled/
COPY docker/nginx-servers.conf /etc/nginx/sites-enabled/
COPY docker/selfsigned.server.crt /etc/ssl/nginx/server.crt
COPY docker/selfsigned.server.key /etc/ssl/nginx/server.key

#install swagger ui
RUN cd /var/www &&  \
    curl -sL https://github.com/CTTV/swagger-ui/archive/master.tar.gz | tar xz && \
    mv swagger-ui-master swagger-ui

WORKDIR /var/www/app

#copy requirements and install them
COPY requirements.txt /var/www/app
RUN pip install -r /var/www/app/requirements.txt

#copy the rest of the code (excluding what's in .dockerignore)
COPY . /var/www/app

#declare app port
EXPOSE 80 443 8080 8009

#define entrypoint
COPY docker/docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]

#run supervisor to run uwsgi to run the flask app
CMD ["supervisord"]
