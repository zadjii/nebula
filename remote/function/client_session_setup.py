from uuid import uuid4
from host.util import mylog
from messages import ClientSessionAlertMessage, ClientSessionResponseMessage, \
    ClientGetCloudHostResponseMessage

__author__ = 'Mike'


from datetime import datetime
import getpass
from werkzeug.security import check_password_hash
from remote import User, Cloud, Session, get_db
from msg_codes import *


def setup_client_session(connection, address, msg_obj):
    msg_type = msg_obj.type
    if msg_type is not CLIENT_SESSION_REQUEST:
        send_generic_error_and_close(connection)  # todo send proper error
        return
    db = get_db()
    # cloudname = msg_obj.cname
    username = msg_obj.uname
    password = msg_obj.passw
    # mylog('This was weird, cname,uname,passw= {},{},{}'.format(cloudname, username, password))
    # mylog('weirdpt2: {}'.format(msg_obj.__dict__))
    # cloud = db.session.query(Cloud).filter_by(name=cloudname).first()
    # if cloud is None:
    #     mylog('ERR: cloud was none')
    #     send_generic_error_and_close(connection)  # todo send proper error
    #     return
    user = db.session.query(User).filter_by(username=username).first()
    if user is None:
        mylog('ERR: user was none')
        send_generic_error_and_close(connection)  # todo send proper error
        return
    if not user.check_password(password):
        mylog('ERR: user pass wrong')
        send_generic_error_and_close(connection)  # todo send proper error
        return
    # if not cloud.can_access(user):
    #     mylog('ERR: user cannot access')
    #     mylog('{}'.format([owner.username for owner in cloud.owners.all()]))
    #     send_generic_error_and_close(connection)  # todo send proper error
    #     return


    # at this point, user exists, provided correct password, and has permission
    #   for this cloud.
    # Now we assign them a session ID, and tell a host that they are coming,
    #   and tell them their id and where to go.

    # host = cloud.hosts.first()
    # todo: make this^ random
    # if host is None:
    #     mylog('ERR: host was none')
    #     send_generic_error_and_close(connection)  # todo send proper error
    #     return
    # fixme confirm that the host is alive, and can handle this response
    session = Session()
    db.session.add(session)
    # session.cloud = cloud
    session.user = user
    # session.host = host
    sess_uuid = str(uuid4())
    # sess_uuid = str(uuid4().int)
    # print 'uuid={}'.format(sess_uuid)
    session.uuid = sess_uuid  # todo this is probably bad.
    db.session.commit()

    # tell host
    # msg = ClientSessionAlertMessage(cloudname, user.id, session.uuid, address[0])
    # host.send_msg(msg)
    # host.send_msg(make_client_session_alert(
    #     cloudname, user.id, session.uuid, address[0])
    # )

    # tell client
    # send_msg(
    #     make_client_session_response(cloudname, session.uuid, host.ip,host.port)
    #     , connection
    # )
    # msg = ClientSessionResponseMessage(cloudname, session.uuid, host.ip, host.port)
    msg = ClientSessionResponseMessage(session.uuid)
    connection.send_obj(msg)

    mylog('I think i setup the session, user={}, sid={}'.format(user.id, session.uuid))


def get_cloud_host(connection, address, msg_obj):
    msg_type = msg_obj.type
    if msg_type is not CLIENT_GET_CLOUD_HOST_REQUEST:
        send_generic_error_and_close(connection)  # todo send proper error
        return
    db = get_db()
    cloudname = msg_obj.cname
    session_id = msg_obj.sid

    sess_obj = db.session.query(Session).filter_by(uuid=session_id).first()
    if sess_obj is None:
        # fixme send error
        mylog('CGCHRq: no session? {}'.format(session_id))
        return
    user = sess_obj.user
    if user is None:
        # fixme return error
        mylog('CGCHRq: no user? {}'.format(sess_obj.user_id))
        return
    cloud = db.session.query(Cloud).filter_by(name=cloudname).first()
    if cloud is None:
        mylog('ERR: cloud was none')
        send_generic_error_and_close(connection)  # todo send proper error
        return

    if not cloud.can_access(user):
        mylog('ERR: user cannot access')
        mylog('{}'.format([owner.username for owner in cloud.owners.all()]))
        send_generic_error_and_close(connection)  # todo send proper error
        return

    # at this point, user exists, and has permission
    #   for this cloud.
    # Now we  tell a host that they are coming,
    #   and tell them their id and where to go.

    # host = match.hosts.first()
    host = None
    if len(cloud.active_hosts()) > 0:
        host = cloud.active_hosts()[0]  # todo make this random

    mylog('cloud[{}] hosts = {}'.format(cloud.name
                                        , [host.id for host in cloud.hosts.all()]))
    mylog('cloud[{}] ACTIVE hosts = {}'.format(cloud.name
                                               , [host.id for host in cloud.active_hosts()]))

    if host is None:
        mylog('ERR: host was none')
        msg = ClientGetCloudHostResponseMessage(session_id, cloud.name, '', 0, 0)
        connection.send_obj(msg)  # fixme
        # send_generic_error_and_close(connection)  # todo send proper error
        return
    # fixme confirm that the host is alive, and can handle this response

    # tell host
    # msg = ClientSessionAlertMessage(sess_obj.uuid, user.id, address[0])
    # host.send_msg(msg)
    # fixme Hosts no longer get a CSA, the client must get some auth from the
    #    remote that the host can trust.

    # tell client
    msg = ClientGetCloudHostResponseMessage(session_id, cloud.name, host.ipv6, host.port, host.ws_port)
    connection.send_obj(msg)

    mylog('I think i setup the host for this session')



