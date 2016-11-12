from common_util import mylog
from messages import ClientGetCloudHostsResponseMessage
from msg_codes import send_generic_error_and_close
from remote import get_db
from remote.util import get_user_from_session


def respond_to_client_get_cloud_hosts(connection, address, msg_obj):
    db = get_db()
    session_id = msg_obj.sid
    rd = get_user_from_session(db, session_id)
    if not rd.success:
        mylog('generic CGCHsR error: "{}"'.format(rd.data), '31')  # fixme
        return
    else:
        user = rd.data

    # todo: also use uname to lookup cloud
    cloudname = msg_obj.cname
    cloud = user.owned_clouds.filter_by(name=cloudname).first()
    if cloud is None:
        mylog('User({}) does not own the requested cloud:{}'.format(
            user.id, cloudname))  # fixme send error
        send_generic_error_and_close(connection)
        return

    hosts = [host.to_dict() for host in cloud.hosts.all()]
    msg = ClientGetCloudHostsResponseMessage(
        session_id
        , hosts
    )
    connection.send_obj(msg)


