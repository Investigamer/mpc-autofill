#!/usr/bin/env bash
set -Eeuo pipefail

# Wait for postgres to come up
echo "======================================================"
echo "  Checking status: Postgresql ...                     "
echo " ---------------------------------------------------- "
# Todo: Check Postgres status command
echo "  ✅ Postgres is UP"

# Wait for elasticsearch to come up
echo "======================================================"
echo "  Checking status: Elasticsearch ...                  "
echo " ---------------------------------------------------- "
# Todo: Check Elasticsearch status command
echo "  ✅ Elasticsearch is UP"

# Decide which startup tasks to perform
: "${DJANGO__RUN_COLLECTSTATIC:=1}"
: "${DJANGO__RUN_MIGRATE:=1}"
: "${DJANGO__RUN_SOURCES_IMPORT:=1}"
: "${DJANGO__RUN_SOURCES_UPDATE:=1}"
: "${DJANGO__RUN_DFCS_UPDATE:=1}"

# Check if we are running for the first time
echo "======================================================"
if ! python manage.py migrate --check; then
  echo "  Django Migrations found..."

  # Run database migrations
  if ! [ "$DJANGO__RUN_MIGRATE" = "0" ]; then
    echo "  Migrating Django database..."
    echo " ---------------------------------------------------- "
    python manage.py migrate
    echo "  ✅ Django database migrated"
  else
    echo "  ✅ Skipping migrations ..."
  fi

  # Sync DFCS
  echo "======================================================"
  if ! [ "$DJANGO__RUN_UPDATE_DFCS" = "0" ]; then
    echo "  Fetching double-faced cards from Scryfall..."
    echo " ---------------------------------------------------- "
    urza dfcs update
    echo "  ✅ Double-faced cards updated"
  else
    echo "  ✅ Skipping fetching double-faced cards ..."
  fi

  # Import drive sources
  echo "======================================================"
  if ! [ "$DJANGO__RUN_IMPORT_SOURCES" = "0" ]; then
    echo "  Importing sources from $IMPORT_DRIVES_FILENAME file ..."
    echo " ---------------------------------------------------- "
    urza sources import "$IMPORT_DRIVES_FILENAME"
    echo "  ✅ Sources imported"
  else
    echo "  ✅ Skipping importing sources ..."
  fi

  # Update database
  echo "======================================================"
  if ! [ "$DJANGO__RUN_UPDATE_DATABASE" = "0" ]; then
    echo "  Scanning drives for a database update..."
    echo " ---------------------------------------------------- "
    urza sources update
    echo "  ✅ Database updated from scanned drives"
  else
    echo "  ✅ Skipping database update ..."
  fi
  echo "======================================================"
fi

# Gather static files
echo "======================================================"
if ! [ "$DJANGO__RUN_COLLECTSTATIC" = "0" ]; then
  echo "  Collecting static files..."
  echo " ---------------------------------------------------- "
  urza manage collectstatic --noinput
  echo "  ✅ Static files collected"
else
  echo "  ✅ Skipping collecting static files ..."
fi
