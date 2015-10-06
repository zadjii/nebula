from uuid import uuid4
from host.util import mylog

__author__ = 'Mike'


from datetime import datetime
import getpass
from werkzeug.security import check_password_hash
from remote import User, Cloud, Session, get_db
from msg_codes import *


def setup_client_session(connection, address, msg_obj):
    msg_type = msg_obj['type']
    if msg_type is not CLIENT_SESSION_REQUEST:
        send_generic_error_and_close(connection)  # todo send proper error
        return
    db = get_db()
    cloudname = msg_obj['cname']
    username = msg_obj['uname']
    password = msg_obj['pass']
    cloud = db.session.query(Cloud).filter_by(name=cloudname).first()
    if cloud is None:
        mylog('ERR: cloud was none')
        send_generic_error_and_close(connection)  # todo send proper error
        return
    user = db.session.query(User).filter_by(username=username).first()
    if user is None:
        mylog('ERR: user was none')
        send_generic_error_and_close(connection)  # todo send proper error
        return
    if not user.check_password(password):
        mylog('ERR: user pass wrong')
        send_generic_error_and_close(connection)  # todo send proper error
        return
    if not cloud.can_access(user):
        mylog('ERR: user cannot access')
        mylog('{}'.format([owner.username for owner in cloud.owners.all()]))
        send_generic_error_and_close(connection)  # todo send proper error
        return


    # at this point, user exists, provided correct password, and has permission
    #   for this cloud.
    # Now we assign them a session ID, and tell a host that they are coming,
    #   and tell them their id and where to go.

    host = cloud.hosts.first()
    # todo: make this^ random
    if host is None:
        mylog('ERR: host was none')
        send_generic_error_and_close(connection)  # todo send proper error
        return

    session = Session()
    db.session.add(session)
    session.cloud = cloud
    session.user = user
    session.host = host
    sess_uuid = str(uuid4())
    # sess_uuid = str(uuid4().int)
    # print 'uuid={}'.format(sess_uuid)
    session.uuid = sess_uuid  # todo this is probably bad.
    db.session.commit()
    # tell host
    host.send_msg(make_client_session_alert(
        cloudname, user.id, session.uuid, address[0])
    )


    # tell client
    send_msg(
        make_client_session_response(cloudname, session.uuid, host.ip)
        , connection
    )

    print 'I think i setup the session'

