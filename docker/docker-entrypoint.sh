#!/bin/bash
set -e

sysctl -w net.core.somaxconn=65535 || echo "Could not increase maximum connection, try in privileged mode"
OUTPUT="$(sysctl net.core.somaxconn)"
echo $OUTPUT
export SOCKET_MAX_CONN="${OUTPUT##* }"
#cp -r /pipeline/source/* /var/www/app/ || echo "no source to copy"

exec "$@"
