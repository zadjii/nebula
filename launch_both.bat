@echo off
set NEBULA_LOCAL_DEBUG=True

if (%0) == () (
    goto DEFAULT
) else (
    goto INSTANCE
)

:DEFAULT
start "Host - Nebula" /max cmd /k "python %~dp0/nebs.py start" & 
start "Remote - Nebula" /max cmd /k "python %~dp0/nebr.py start" &

goto EXIT

:INSTANCE
start "Host - Nebula" /max cmd /k "python %~dp0/nebs.py start -i %1" & 
start "Remote - Nebula" /max cmd /k "python %~dp0/nebr.py start -i %1" &

goto EXIT

:EXIT