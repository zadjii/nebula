#!/bin/bash

python nebr.py kill -i jenkins
python nebr.py -i jenkins
rm ./instances/remote/jenkins/nebr.conf

# This is for nebs, not nebr
# echo "PORT = 23457\nWSPORT = 34568" > ./instances/remote/jenkins/nebr.conf

python nebr.py migrate -i jenkins
python nebr.py start -i jenkins 
