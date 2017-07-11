#!/bin/bash

# see http://steveadams.io/2016/08/18/Environment-Variable-Templates.html
# for the source of this hack

eval "cat <<EOF
$(<$1)
EOF
"