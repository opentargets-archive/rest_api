# base image
FROM jeethu/pypy:4.0.1
MAINTAINER Andrea Pierleoni <andreap@ebi.ac.uk>

# Install required packages
RUN set -e && \
    apt-get update && \
    apt-get -yq install wget supervisor python-setuptools gcc ca-certificates openssh-server git libssl-dev && \
    cd /tmp/ && \
    pip install --upgrade pip && \
    pip install uwsgi==2.0.11.2 uwsgitop==0.9 Flask==0.10.1  pyOpenSSL && \
    ln -s /usr/local/pypy-4.0.1-linux_x86_64-portable/bin/uwsgi* /usr/local/bin/ && \
    chmod +x /usr/local/bin/uwsgi && \
    apt-get -yq autoremove && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*



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
CMD ["/usr/bin/supervisord"]