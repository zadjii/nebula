BASEDIR=$(dirname "$0")

rm -rf ${BASEDIR}/remote/db_repository
rm -rf ${BASEDIR}/host/db_repository
echo "repos deleted"
rm -f ${BASEDIR}/remote/remote.db
rm -f ${BASEDIR}/host/host.db
echo "dbs deleted"
python ${BASEDIR}/remote_db_create.py
python ${BASEDIR}/host_db_create.py
