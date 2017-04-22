#!/bin/bash

# "echo on"
set -o xtrace

# This should probably make sure it 
# pip install -r requirements.txt

python nebr.py kill -i jenkins
python nebr.py -i jenkins
# rm ./instances/remote/jenkins/nebr.conf

# This is for nebs, not nebr
# echo "PORT = 23457\nWSPORT = 34568" > ./instances/remote/jenkins/nebr.conf

python nebr.py migrate-db -i jenkins -l nebr.log
echo "Migrated old DB"
python nebr.py start -i jenkins -l nebr.log &
echo "Started nebr"
sleep 5
python nebr.py kill -i jenkins

# This should only really be done if the tests pass
# But there aren't any great remote-only tests ATM.

# ACTUALLY NO. DON'T DO THIS.
# The deployment of nebula should be someone else's responsibility.
# They can upgrade their version of nebula when they're ready.
# sudo -u zadjii sh ./deploy-nebula.sh
#Maybe in the future, I'll add a different deploy script that makes more sense.