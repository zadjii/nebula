echo off
call reset_dbs.bat
rem  todo this is now two seperate repops, one for the host and another for the remote
python db_autopopulate_000.py
echo "completed autopop"