@echo off
set NEBULA_LOCAL_DEBUG=True
start "Host - Nebula" /max cmd /k "python %~dp0/nebs.py start" & 
start "Remote - Nebula" /max cmd /k "python %~dp0/nebr.py start" &