from common_util import mylog
from messages import GetHostsResponseMessage, GetActiveHostsResponseMessage
from msg_codes import send_generic_error_and_close, GET_HOSTS_REQUEST
from remote import get_db, Host, Cloud


def get_hosts_response(connection, address, msg_obj):
    db = get_db()
    host_id = msg_obj.id
    cloudname = msg_obj.cname

    matching_host = db.session.query(Host).get(host_id)
    if matching_host is None:
        send_generic_error_and_close(connection)
        raise Exception('There was no host with the ID[{}], wtf'.format(host_id))

    matching_cloud = db.session.query(Cloud).filter_by(name=cloudname).first()
    if matching_cloud is None:
        send_generic_error_and_close(connection)
        raise Exception('No cloud with name ' + cloudname)
    if msg_obj.type == GET_HOSTS_REQUEST:
        msg = GetHostsResponseMessage(matching_cloud)
    else:
        msg = GetActiveHostsResponseMessage(matching_cloud)
    connection.send_obj(msg)
    if msg_obj.type == GET_HOSTS_REQUEST:
        mylog('responded to Host[{}] asking for hosts of \'{}\''.format(
            host_id, cloudname))
    else:
        mylog('responded to Host[{}] asking for ACTIVE hosts of \'{}\''.format(
            host_id, cloudname))
