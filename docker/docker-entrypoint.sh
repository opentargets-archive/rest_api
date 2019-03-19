#!/bin/bash
set -e

# Run the REST API or the celery workers
if [[ -z "${CELERY_WORKER_ENV}" ]]; then
  echo "Run OpenTarget REST API because CELERY_WORKER_ENV is undefined"
else
  echo "Run celery workers"
  mv /etc/supervisor/conf.d/supervisord_celery.tmp /etc/supervisor/conf.d/supervisord.conf
fi

sysctl -w net.core.somaxconn=65535 || echo "Could not increase maximum connection, try in privileged mode"
OUTPUT="$(sysctl net.core.somaxconn)"
echo $OUTPUT
export SOCKET_MAX_CONN="${OUTPUT##* }"
#cp -r /pipeline/source/* /var/www/app/ || echo "no source to copy"

exec "$@"
