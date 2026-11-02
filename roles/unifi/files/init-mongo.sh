#!/bin/bash
# Creates the UniFi application's MongoDB user, with the roles the
# linuxserver.io image documents. The mongo image runs this only on its first
# start, with an empty data directory. The passwords are read from the
# Compose secrets and handed to mongosh through its environment, so they
# never appear in a command line or in this script.
set -euo pipefail

UNIFI_ROOT_PASSWORD="$(cat /run/secrets/db_root_password)" \
UNIFI_APP_PASSWORD="$(cat /run/secrets/db_password)" \
mongosh --quiet --norc <<'EOF'
const env = process.env;
const admin = db.getSiblingDB(env.MONGO_AUTHSOURCE);
admin.auth(env.MONGO_INITDB_ROOT_USERNAME, env.UNIFI_ROOT_PASSWORD);
const name = env.MONGO_DBNAME;
admin.createUser({
  user: env.MONGO_USER,
  pwd: env.UNIFI_APP_PASSWORD,
  roles: [
    "clusterMonitor",
    { db: name, role: "dbOwner" },
    { db: name + "_stat", role: "dbOwner" },
    { db: name + "_audit", role: "dbOwner" },
    { db: name + "_restore", role: "dbOwner" },
  ],
});
EOF
