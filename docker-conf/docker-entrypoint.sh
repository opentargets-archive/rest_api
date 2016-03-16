#!/bin/bash
set -e

sysctl -w net.core.somaxconn=65535

exec "$@"