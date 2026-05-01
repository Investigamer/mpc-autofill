#!/usr/bin/env bash
set -Eeuo pipefail

# Set PUID, PGID, and name for non-root user
: "${PUID:=1000}"
: "${PGID:=1000}"
: "${APP_RUN_MODE:=server}"
: "${APP_NON_ROOT_USER:=urza}"
: "${APP_NON_ROOT_GROUP:=urza}"
: "${IMPORT_DRIVES_FILENAME:=drives.csv}"

# Check that we have a valid APP_RUN_MODE
if [ "$APP_RUN_MODE" != "worker" ] && [ "$APP_RUN_MODE" != "server" ]; then
  echo "ERROR: APP_RUN_MODE must be 'server' or 'worker'! Current value: '$APP_RUN_MODE'" >&2
  exit 1
fi

# Create or update non-root user group
if ! getent group "$APP_NON_ROOT_GROUP" >/dev/null; then
  addgroup --gid "$PGID" "$APP_NON_ROOT_GROUP"
else
  groupmod -g "$PGID" "$APP_NON_ROOT_GROUP"
fi

# Create or update non-root user
if ! id -u "$APP_NON_ROOT_USER" >/dev/null 2>&1; then
  adduser --disabled-password \
          --gecos "" \
          --uid "$PUID" \
          --gid "$PGID" \
          "$APP_NON_ROOT_USER"
else
  usermod -u "$PUID" -g "$PGID" "$APP_NON_ROOT_USER"
fi

# Create default drives.csv if one isn't provided
CSV_FILE_DST="./config/$IMPORT_DRIVES_FILENAME"
CSV_FILE_SRC="./config-staging/drives.example.csv"
echo "======================================================"
if [ ! -f "$CSV_FILE_DST" ]; then
  echo "  ⚠️ No $IMPORT_DRIVES_FILENAME provided, generating default drives.csv ..."
  head -n 1 "$CSV_FILE_SRC"; echo "" > "./config/drives.csv"
else
  echo "  ✅ Found a $IMPORT_DRIVES_FILENAME file"
fi

# Warn the user if no client secrets file is provided
JSON_SECRETS_FILE="./config/client_secrets.json"
echo "======================================================"
if [ ! -f "$JSON_SECRETS_FILE" ]; then
  echo "  ⚠️ 'client_secrets.json' file is missing!           "
  echo " ---------------------------------------------------- "
  echo "  > Set up a Google Service Account and copy the      "
  echo "    JSON key to a client_secrets.json file located    "
  echo "    in the mounted config directory.                  "
else
  echo "  ✅ Found a client_secrets.json file                 "
fi

# Create default user.toml if one isn't provided
TOML_FILE_DST="/app/MPCAutofill/config/user.toml"
TOML_FILE_SRC="/app/MPCAutofill/config-staging/user.example.toml"
echo "======================================================"
if [ ! -f "$TOML_FILE_DST" ]; then
  echo "  ⚠️ 'user.toml' config file is missing!              "
  echo " ---------------------------------------------------- "
  echo "  > Creating a basic user.toml file in the mounted    "
  echo "    config directory.                                 "
  echo "  > If not providing the necessary environment        "
  echo "    variables in your docker-compose, you should      "
  echo "    edit this user.toml file to configure the app.    "
  cp $TOML_FILE_SRC $TOML_FILE_DST
else
  echo "  ✅ Found a user.toml config file"
fi
echo "======================================================"

# Relocate staged default config
DEFAULTS_FILE_DST="./config/default.toml"
DEFAULTS_FILE_SRC="./config-staging/default.toml"
if [ ! -f "$DEFAULTS_FILE_DST" ]; then
  cp -f "$DEFAULTS_FILE_SRC" "$DEFAULTS_FILE_DST"
  echo "  ✅ Successfully copied 'default.toml' file          "
else
  echo "  ✅ Defaults file 'default.toml' already exists.     "
fi
echo "======================================================"

# Change ownership
chown -R "$PUID":"$PGID" /app

# Drop privileges, execute entrypoint
echo "  ✅ Step complete: PRE-RUN                           "
echo "======================================================"
if [ "$APP_RUN_MODE" = "server" ]; then
  gosu "$APP_NON_ROOT_USER" ./scripts/entrypoint.sh
  echo " ✅ Step complete: ENTRYPOINT                         "
  echo "======================================================"
  exec gosu "$APP_NON_ROOT_USER" "$@"
else
  echo " ✅ Initializing worker mode!                         "
  echo "======================================================"
  exec gosu "$APP_NON_ROOT_USER" python manage.py qcluster
fi
