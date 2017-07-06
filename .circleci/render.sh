#!/bin/bash
eval "cat <<EOF
$(<$1)
EOF
"