#!/bin/sh
# Create the two tenant databases (empire_inc, kdy) and load their schema and seed data.
#
# In docker compose this runs once, from /docker-entrypoint-initdb.d, the first
# time the postgres container starts with an empty volume.
#
# Against any other server (drops and recreates both databases):
#   PGHOST=localhost PGPORT=55432 PGUSER=empire PGPASSWORD=empire-local-only SEED_DIR=db/seed sh db/load.sh
set -eu

SEED_DIR="${SEED_DIR:-/seed}"
export PGUSER="${PGUSER:-${POSTGRES_USER:-postgres}}"
export PGDATABASE=postgres

for pair in empire:empire_inc kdy:kdy; do
    tenant="${pair%%:*}"
    database="${pair##*:}"
    echo "loading $database from $SEED_DIR/$tenant"
    psql -v ON_ERROR_STOP=1 -q -c "DROP DATABASE IF EXISTS $database" -c "CREATE DATABASE $database"
    (
        cd "$SEED_DIR/$tenant"
        psql -v ON_ERROR_STOP=1 -q -d "$database" -f schema.sql
        psql -v ON_ERROR_STOP=1 -q -d "$database" -f load.sql
    )
done
echo "databases loaded"
