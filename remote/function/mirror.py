from messages import PrepareForFetchMessage, GoRetrieveHereMessage
from msg_codes import send_generic_error_and_close
from remote import get_db, Host, Cloud, Session


def mirror_complete(connection, address, msg_obj):
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

    matching_cloud.hosts.append(matching_host)
    db.session.commit()
    print 'Host[{}] finished mirroring cloud \'{}\''.format(host_id, cloudname)


def host_request_cloud(connection, address, msg_obj):
    db = get_db()
    host_id = msg_obj.id
    cloudname = msg_obj.cname
    username = msg_obj.uname
    password = msg_obj.passw

    print('User provided {},{},{},{}'.format(
        host_id, cloudname, username, password
    ))
    matching_host = db.session.query(Host).get(host_id)
    if matching_host is None:
        send_generic_error_and_close(connection)
        raise Exception('There was no host with the ID[{}], wtf'.format(host_id))

    match = db.session.query(Cloud).filter_by(name=cloudname).first()
    if match is None:
        send_generic_error_and_close(connection)
        raise Exception('No cloud with name ' + cloudname)

    # user = db.session.query(User).filter_by(username=username).first()
    user = match.owners.filter_by(username=username).first()
    if user is None:
        send_generic_error_and_close(connection)
        print [owner.username for owner in match.owners.all()]
        raise Exception(username + ' is not an owner of ' + cloudname)
    # todo validate their password
    # todo  validate the user is an owner of the cloud
    # Here we've established that they are an owner.
    # print 'Here, they will have successfully been able to mirror?'
    respond_to_mirror_request(connection, address, host_id, match)


def client_mirror(connection, address, msg_obj):
    db = get_db()
    session_id = msg_obj.sid
    host_id = msg_obj.host_id
    cloud_uname = msg_obj.cloud_uname
    # the cloud uname is currently unused, it will eventually be used
    cloudname = msg_obj.cname

    matching_host = db.session.query(Host).get(host_id)
    if matching_host is None:
        send_generic_error_and_close(connection)
        raise Exception('There was no host with the ID[{}], wtf'.format(host_id))
    # todo: It'll be easier on the DB to find the user first, then filter their
    # owned clouds to find the match

    match = db.session.query(Cloud).filter_by(name=cloudname).first()
    if match is None:
        send_generic_error_and_close(connection)
        raise Exception('No cloud with name ' + cloudname)

    session = db.session.query(Session).filter_by(uuid=session_id).first()
    if session is None:
        send_generic_error_and_close(connection)
        raise Exception('provided session ID does not exist')
    user = session.user
    cloud_user = match.owners.filter_by(username=user.name).first()
    if cloud_user is None:
        send_generic_error_and_close(connection)
        print [owner.username for owner in match.owners.all()]
        raise Exception(user.name + ' is not an owner of ' + cloudname)
    # user is an owner, and the host exists
    respond_to_mirror_request(connection,address,host_id,match)


def respond_to_mirror_request(connection, address, requester_id, cloud):
    """Assumes that the requester has already been validated"""
    ip = '0'
    port = 0
    # rand_host = match.hosts.first()
    rand_host = None
    if len(cloud.active_hosts()) > 0:
        rand_host = cloud.active_hosts()[0]  # todo make this random
    if rand_host is not None:
        # ip = rand_host.ip
        ip = rand_host.ipv6
        port = rand_host.port
        # msg = PrepareForFetchMessage(host_id, cloudname, address[0]) # ipv4, old
        msg = PrepareForFetchMessage(requester_id, cloud.name, ip) # ipv6
        # fixme ssl up in here
        # rand_host.send_msg(msg)
        # mylog('Not telling [{}]<{}> about [{}]<{}>'.format(
        #     rand_host.id, rand_host.ipv6, matching_host.id, matching_host.ipv6))
        # prep_for_fetch_msg = make_prepare_for_fetch_json(host_id, cloudname, address[0])
        # rand_host.send_msg(prep_for_fetch_msg)

        # port = rand_host.port
        # print 'rand host is ({},{})'.format(ip, port)
        # context = SSL.Context(SSL.SSLv23_METHOD)
        # context.use_privatekey_file(KEY_FILE)
        # context.use_certificate_file(CERT_FILE)
        # s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #
        # # s = SSL.Connection(context, s)
        # # whatever fuck it lets just assume it's good todo
        #
        # s.connect((ip, port))
        # send_msg(prep_for_fetch_msg, s)
        # print 'nebr completed talking to rand_host'
        # s.close()
    msg = GoRetrieveHereMessage(0, ip, port)
    connection.send_obj(msg)
    # send_msg(make_go_retrieve_here_json(0, ip, port), connection)

    print 'nebr has reached the end of host_request_cloud'