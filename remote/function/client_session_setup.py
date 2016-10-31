from uuid import uuid4
from common_util import mylog, send_error_and_close, ResultAndData, Error, Success
from remote import User, Cloud, Session, get_db
from msg_codes import *
from messages import *
from remote.models.ClientCloudHostMapping import ClientCloudHostMapping
from remote.util import get_cloud_by_name, validate_session_id

__author__ = 'Mike'


def setup_client_session(connection, address, msg_obj):
    msg_type = msg_obj.type
    if msg_type is not CLIENT_SESSION_REQUEST:
        err = InvalidStateMessage('Somehow tried to setup_client_session '
                                  'without CLIENT_SESSION_REQUEST')
        send_error_and_close(err, connection)
        return
    username = msg_obj.uname
    password = msg_obj.passw

    # user = db.session.query(User).filter_by(username=username).first()
    # if user is None:
    #     mylog('ERR: user was none')
    #     send_generic_error_and_close(connection)  # todo send proper error
    #     return
    # if not user.check_password(password):
    #     mylog('ERR: user pass wrong')
    #     send_generic_error_and_close(connection)  # todo send proper error
    #     return
    #
    # # At this point, user exists, provided correct password.
    # # Now we assign them a session ID.
    # # THAT'S IT. They'll come ask us for a cloud later.
    #
    # session = Session(user)
    # db.session.add(session)
    #
    # # session.user = user
    # db.session.commit()
    db = get_db()
    rd = do_setup_client_session(db, username, password)
    if rd.success:
        session = rd.data
        user = session.user
        msg = ClientSessionResponseMessage(session.uuid)
        connection.send_obj(msg)
        mylog('Session Setup, user,sid={},{}'.format(user.id, session.uuid))
    else:
        msg = AuthErrorMessage()  # todo: This should have a message. Really all errors should.
        connection.send_obj(msg)


def do_setup_client_session(db, username, password):
    # type: (SimpleDB, str, str) -> ResultAndData
    rd = Error()
    user = db.session.query(User).filter_by(username=username).first()
    if user is None:
        msg = 'ERR: user was none'
        mylog(msg)
        return Error(msg)

    if not user.check_password(password):
        msg = 'ERR: user pass wrong'
        mylog(msg)
        return Error(msg)

    # At this point, user exists, provided correct password.
    # Now we assign them a session ID.
    # THAT'S IT. They'll come ask us for a cloud later.

    session = Session(user)
    db.session.add(session)
    db.session.commit()

    return Success(session)


def get_cloud_host(connection, address, msg_obj):
    msg_type = msg_obj.type
    if msg_type is not CLIENT_GET_CLOUD_HOST_REQUEST:
        err = InvalidStateMessage('Somehow tried to get_cloud_host '
                                  'without CLIENT_GET_CLOUD_HOST_REQUEST')
        send_error_and_close(err, connection)
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
        err = InvalidStateMessage('Somehow there is no user for this session')
        send_error_and_close(err, connection)
        return

    cloud = db.session.query(Cloud).filter_by(name=cloudname).first()
    if cloud is None:
        mylog('ERR: cloud was none')
        send_generic_error_and_close(connection)  # todo send proper error
        return

    # verify user can access the cloud
    if not cloud.can_access(user):
        # mylog('ERR: user cannot access')
        # mylog('{}'.format([owner.username for owner in cloud.owners.all()]))
        err = InvalidPermissionsMessage('User cannot access this cloud')
        send_error_and_close(err, connection)
        return

    # at this point, user exists, and has permission for this cloud.
    # Now we find a host for the cloud for this client.
    # We track that client,cloud -> host mapping.
    # We tell the client to go to that host.
    # Later, the host will ask us to verify we told that client to come there.

    host = None
    if len(cloud.active_hosts()) > 0:
        host = cloud.active_hosts()[0]  # todo:13 make this random

    if host is None:
        err = NoActiveHostMessage(cloud.creator_name(), cloud.name)
        send_error_and_close(err, connection)
        return
    # todo:13 confirm that the host is alive, and can handle this response

    host_mapping = ClientCloudHostMapping(sess_obj, cloud, host)
    db.session.add(host_mapping)
    db.session.commit()

    # tell client
    msg = ClientGetCloudHostResponseMessage(session_id, cloud.name, host.ipv6,
                                            host.port, host.ws_port)
    connection.send_obj(msg)

    mylog(
        'Mapped client,cloud=({},{}) to host={}'.format(sess_obj.id, cloudname,
                                                        host.id))

# Note: I originally had it in my comments for the remote to give the client
#   some piece of authentication that the host would be able to trust.
#   I'm not sure how to do that, so I did this instead.


def host_verify_client(connection, address, msg_obj):
    """
    Authorize the client's attempt to access the mirror that sent us this
    request. If there is no ClientCloudHostMapping for this request, then
    respond with HOST_VERIFY_CLIENT_FAILURE. Else HOST_VERIFY_CLIENT_SUCCESS.
    """

    msg_type = msg_obj.type
    if msg_type is not HOST_VERIFY_CLIENT_REQUEST:
        err = InvalidStateMessage('Somehow tried to host_verify_client '
                                  'without HOST_VERIFY_CLIENT_REQUEST')
        send_error_and_close(err, connection)
        return
    db = get_db()
    cloudname = msg_obj.cname
    cloud_uname = msg_obj.cloud_uname
    session_id = msg_obj.sid
    mirror_id = msg_obj.id

    rd = validate_session_id(db, session_id)
    if not rd.success:
        err = HostVerifyClientFailureMessage(rd.data)
        send_error_and_close(err, connection)
        return
    else:
        sess_obj = rd.data

    cloud = get_cloud_by_name(db, cloud_uname, cloudname)
    if cloud is None:
        msg = 'No matching cloud {}'.format((cloud_uname, cloudname))
        err = HostVerifyClientFailureMessage(msg)
        send_error_and_close(err, connection)
        return

    mapping = sess_obj.host_mappings.filter_by(host_id=mirror_id, cloud_id=cloud.id).first()
    if mapping is None:
        msg = 'No mapping between client and mirror for this host'
        err = HostVerifyClientFailureMessage(msg)
        send_error_and_close(err, connection)
        return
    else:
        response = HostVerifyClientSuccessMessage(mirror_id, session_id, cloud_uname, cloudname, sess_obj.user.id)
        connection.send_obj(response)

