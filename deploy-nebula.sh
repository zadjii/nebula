#!/bin/bash
# This is left as a reference for something else to use in the future.


JENKINS_PATH=/var/lib/jenkins/workspace/nebula-github

# ~/dev/public/nebula/ should probably not be in /home/ but whatever
NEB_OUT_PATH=~/dev/public/nebula/

start_dir=$PWD
cd $JENKINS_PATH

cp -r !(instances) $NEB_OUT_PATH
cp -r .git $NEB_OUT_PATH
cp -r .gitignore $NEB_OUT_PATH

cd $NEB_OUT_PATH
for dir in $NEB_OUT_PATH/instances/remote/*/
do
    dir=${dir%*/}
    instance=${dir##*/}
    echo Migrating remote instance \'$instance\'
    python nebr.py -i $instance migrate-db
done

cd $NEB_OUT_PATH
for dir in $NEB_OUT_PATH/instances/host/*/
do
    dir=${dir%*/}
    instance=${dir##*/}
    echo Migrating host instance \'$instance\'
    python nebs.py -i $instance migrate-db
done

cd $start_dir


