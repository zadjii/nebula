@echo off
set NEBULA_LOCAL_DEBUG=True

if (%1) == () (
    goto DEFAULT
) else (
    goto INSTANCE
)

:DEFAULT
start "Host - Nebula" /max cmd /k "python %~dp0/nebs.py start -v debug" & 
start "Remote - Nebula" /max cmd /k "python %~dp0/nebr.py start -v debug" &

goto EXIT

:INSTANCE
start "Host - Nebula" /max cmd /k "python %~dp0/nebs.py start -v debug -i %1" & 
start "Remote - Nebula" /max cmd /k "python %~dp0/nebr.py start -v debug -i %1" &

goto EXIT

:EXIT