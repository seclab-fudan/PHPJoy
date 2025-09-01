#!/bin/bash
../"$1"/bin/neo4j stop

rm -rf ../neo4j/"$1"
cp -r ../neo4j-community-4.4.4 ../"$1"
../"$1"/bin/neo4j-admin import --database=neo4j \
  --nodes=nodes.csv \
  --nodes=fake_nodes.csv --relationships=rels.csv \
  --relationships=fake_rels.csv \
  --relationships=cpg_edges.csv \
  --trim-strings=true \
  --skip-duplicate-nodes=true \
  --skip-bad-relationships=true \
  --multiline-fields=true \
  --id-type=INTEGER \
  --force=true

#sed  -i "s/#dbms.connector.bolt.listen_address=:7687/dbms.connector.bolt.listen_address=:$2/g" ../"$1"/conf/neo4j.conf
#sed  -i "s/#dbms.connector.http.listen_address=:7474/dbms.connector.http.listen_address=:$3/g" ../"$1"/conf/neo4j.conf
#sed  -i "s/#dbms.default_listen_address=0.0.0.0/dbms.default_listen_address=0.0.0.0/g" ../"$1"/conf/neo4j.conf
#sed  -i "s/#dbms.security.auth_enabled=false/dbms.security.auth_enabled=false/g" ../"$1"/conf/neo4j.conf

sed -i "s/#dbms.connector.bolt.listen_address=:7687/dbms.connector.bolt.listen_address=:$2/g" ../"$1"/conf/neo4j.conf
sed -i "s/#dbms.connector.http.listen_address=:7474/dbms.connector.http.listen_address=:$3/g" ../"$1"/conf/neo4j.conf
sed -i "s/#dbms.default_listen_address=0.0.0.0/dbms.default_listen_address=0.0.0.0/g" ../"$1"/conf/neo4j.conf
sed -i "s/#dbms.security.auth_enabled=false/dbms.security.auth_enabled=false/g" ../"$1"/conf/neo4j.conf