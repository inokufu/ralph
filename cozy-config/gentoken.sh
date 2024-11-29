#!/bin/bash

# $1: instance name
# $2: sleep time

# generate a new auth token for $1 instance every $2 seconds
while true
do
    cozy-stack instance token-cli $1 io.cozy.learningrecords io.cozy.doctypes > /etc/cozy/cozy-auth-token
    sleep $2
done