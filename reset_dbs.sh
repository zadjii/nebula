BASEDIR=$(dirname "$0")

rm -rf ${BASEDIR}/remote-root/src/remote/db_repository
rm -rf ${BASEDIR}/host-root/src/host/db_repository

rm -f ${BASEDIR}/remote-root/src/remote/remote.db
rm -f ${BASEDIR}/host-root/src/host/host.db

python ${BASEDIR}/remote-root/src/remote/database/db_create.py
python ${BASEDIR}/host-root/src/host/database/db_create.py