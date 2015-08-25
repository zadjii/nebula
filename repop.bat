echo off
call reset_dbs.bat
python db_autopopulate_000.py
echo "completed autopop"