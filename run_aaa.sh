#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 yourfile.aaa"
    exit 1
fi

aaa_repo_root=$(dirname $(readlink -f $0))
old_cwd=$(pwd)
aaa_file=$(readlink -f $1)

cd $aaa_repo_root
poetry run ./manage.py run $aaa_file
cd $old_cwd
