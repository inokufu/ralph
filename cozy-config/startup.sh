#!/bin/bash

set -m

# cozy-stack serve in background
cozy-stack serve --allow-root &

# wait for the server to start
until cozy-stack status
do
  sleep 1
done

INSTANCE_DOMAIN="cozy.ralph-cozy-stack-1:8080"

# add minimal instance
cozy-stack instances add --passphrase cozy --apps settings $INSTANCE_DOMAIN

# generate a new auth token every 15 minutes
/etc/cozy/gentoken.sh $INSTANCE_DOMAIN 900 &

# bring back cozy-stack serve to the foreground
fg %1