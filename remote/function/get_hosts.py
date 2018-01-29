from common_util import mylog, get_mylog
from messages import GetHostsResponseMessage, GetActiveHostsResponseMessage, InvalidStateMessage
from msg_codes import send_generic_error_and_close, GET_HOSTS_REQUEST
from remote import Host, Cloud
from remote.models.Cloud import cloud_contributors
from remote.models.Mirror import Mirror
from remote.models.User import User


def get_hosts_response(remote_obj, connection, address, msg_obj):
    """
    Remote handler for the Host Get(Active)Hosts request. Replies with all of
      the mirrors for a particular cloud.
    This request is sent by a mirror (given by host_id) when it wants info on
      the other mirrors for this clouds, usually to tell them that there are
      updates to the files on this cloud.
    :param remote_obj:
    :param connection:
    :param address:
    :param msg_obj:
    :return:
    """
    _log = get_mylog()
    db = remote_obj.get_db()
    host_id = msg_obj.id
    mirror_id = msg_obj.id
    cloudname = msg_obj.cname
    cloud_uname = msg_obj.cloud_uname

    matching_mirror = db.session.query(Mirror).get(mirror_id)
    if matching_mirror is None:
        msg = 'There is no mirror matching id={}'.format(mirror_id)
        _log.error(msg)
        response = InvalidStateMessage(msg)
        connection.send_obj(response)
        connection.close()
        return

    # matching_host = db.session.query(Host).get(host_id)
    # if matching_host is None:
    #     send_generic_error_and_close(connection)
    #     raise Exception('There was no host with the ID[{}], wtf'.format(host_id))

    creator = db.session.query(User).filter_by(username=cloud_uname).first()
    if creator is None:
        err = 'No cloud matching {}/{}'.format(cloud_uname, cloudname)
        msg = InvalidStateMessage(err)
        connection.send_obj(msg)
        connection.close()
        _log.debug(err)
        # raise Exception(err)
        return

    matching_cloud = creator.created_clouds.filter_by(name=cloudname).first()

    if matching_cloud is None:
        send_generic_error_and_close(connection)
        raise Exception('No cloud with name ' + cloudname)

    # At this point, we've identified the mirror requesting this information
    #   (matching_mirror), and we know which cloud they are looking for info
    #   about (matching_cloud)

    if msg_obj.type == GET_HOSTS_REQUEST:
        msg = GetHostsResponseMessage(matching_cloud)
    else:
        msg = GetActiveHostsResponseMessage(matching_cloud)

    connection.send_obj(msg)

    log_msg = 'responded to Mirror[{}] asking for {} mirrors of \'{}/{}\''.format(
        mirror_id,
        'all' if msg_obj.type == GET_HOSTS_REQUEST else 'ACTIVE',
        cloud_uname, cloudname)
    _log.debug(log_msg)

