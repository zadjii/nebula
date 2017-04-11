#!/bin/bash

python nebr.py kill -i jenkins
python nebr.py -i jenkins
rm ./instances/jenkins/remote/nebr.conf

echo "PORT = 23457\nWSPORT = 34568" > ./instances/jenkins/remote/nebr.conf

python nebr.py migrate -i jenkins
python nebr.py start -i jenkins 
