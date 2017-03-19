from common_util import mylog, Error, ResultAndData, Success
from messages import ClientGetCloudHostsResponseMessage, AuthErrorMessage, InvalidStateMessage
from msg_codes import send_generic_error_and_close
from remote.util import get_user_from_session, get_cloud_by_name


def respond_to_client_get_cloud_hosts(remote_obj, connection, address, msg_obj):
    db = remote_obj.get_db()
    session_id = msg_obj.sid
    cloudname = msg_obj.cname
    rd = do_client_get_cloud_hosts(db, session_id, msg_obj.cloud_uname, cloudname)
    if not rd.success:
        msg = rd.data
    else:
        hosts = rd.data
        msg = ClientGetCloudHostsResponseMessage(session_id, hosts)

    connection.send_obj(msg)


def do_client_get_cloud_hosts(db, session_id, cloud_uname, cname):
    # type: (SimpleDB, str, str, str) -> ResultAndData
    # type: (SimpleDB, str, str, str) -> ResultAndData(True, [dict])
    # type: (SimpleDB, str, str, str) -> ResultAndData(False, BaseMessage)

    rd = get_user_from_session(db, session_id)
    if not rd.success:
        return ResultAndData(False, InvalidStateMessage(rd.data))
    else:
        user = rd.data

    # todo: also use uname to lookup cloud
    cloud = get_cloud_by_name(db, cloud_uname, cname)
    if cloud is None:
        return Error(InvalidStateMessage('Cloud {}/{} does not exist'.format(cloud_uname, cname)))
    if not cloud.has_owner(user):
        # Pretend that the cloud doesnt exist
        # todo: evaluate if this is a good answer
        return Error(InvalidStateMessage('Cloud {}/{} does not exist'.format(cloud_uname, cname)))

    # todo:37 maybe this should be an option in the API, to get all or only active
    # For now I'm defaulting to active, becuase all mirror attempts make a host,
    #   Which is bad todo:38
    hosts = [host.to_dict() for host in cloud.active_hosts()]
    # hosts = [host.to_dict() for host in cloud.hosts.all()]
    return Success(hosts)


