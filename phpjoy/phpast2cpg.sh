#!/bin/bash
BASEDIR=$(dirname "$0")
java -jar "$BASEDIR/phpast2cpg.jar" -n nodes.csv -e rels.csv -m strict -p predefined.csv
