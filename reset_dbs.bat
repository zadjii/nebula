echo off
set BASEDIR="."

rd /s /q %BASEDIR%\host\db_repository
rd /s /q %BASEDIR%\remote\db_repository

del %BASEDIR%\host\host.db
del %BASEDIR%\remote\remote.db

python %BASEDIR%\host_db_create.py
python %BASEDIR%\remote_db_create.py