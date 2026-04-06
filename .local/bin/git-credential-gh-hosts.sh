#!/bin/sh
TOKEN=$(grep 'oauth_token:' /data/.openclaw/.gh/hosts.yml | head -1 | sed 's/.*oauth_token: *//')
echo "username=x-access-token"
echo "password=$TOKEN"
