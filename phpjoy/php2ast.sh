#!/bin/bash

BASEDIR=$(dirname "$0")

if [ -z "$PHP7" ]; then
    PHP7=/opt/homebrew/bin/php
fi

$PHP7 "$BASEDIR"/php2ast/src/Parser.php "$@"
