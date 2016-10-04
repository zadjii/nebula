import socket
import ssl
import os
from netifaces import interfaces, ifaddresses, AF_INET6
# from host import Cloud
from host.models.Client import Client
from host.models.Cloud import Cloud
from messages import HostVerifyClientRequestMessage
from msg_codes import send_generic_error_and_close, HOST_VERIFY_CLIENT_SUCCESS
from common_util import *


def validate_host_id(db, host_id, conn):
    rd = get_matching_clouds(db, host_id)
    if not rd.success:
        send_generic_error_and_close(conn)
        raise Exception(rd.data)
    return rd


def get_matching_clouds(db, host_id):
    rd = ERROR()
    matching_id_clouds = db.session.query(Cloud)\
        .filter(Cloud.my_id_from_remote == host_id)

    if matching_id_clouds.count() <= 0:
        rd = ERROR('Received a message intended for id={},'
                   ' but I don\'t have any clouds with that id'
                   .format(host_id))
    else:
        rd = ResultAndData(True, matching_id_clouds)
    return rd


def all_ip6_list():
    ip_list = []
    for interface in interfaces():
        for link in ifaddresses(interface)[AF_INET6]:
            ip_list.append(link['addr'])
    # add ::1 to the end of the list so if we're in debug mode,
    #  its only a last resort.
    if '::1' in ip_list:
        ip_list.remove('::1')
        ip_list.append('::1')
    return ip_list


def get_ipv6_list():
    """Returns all suitable (public) ipv6 addresses for this host"""
    valid_ips = [ip for ip in all_ip6_list() if ('%' not in ip)]
    # todo: remove this from the Release build  of nebula, so the conditional
    #   is never even checked.
    if os.environ.get('NEBULA_LOCAL_DEBUG', False):
        return valid_ips
    else:
        return [ip for ip in valid_ips if (not ip == '::1')]


def check_response(expected, recieved):
    if not(int(expected) == int(recieved)):
        raise Exception('Received wrong msg-code, '
                        'expected {}, recieved {}'.format(expected, recieved))


def get_clouds_by_name(db, uname, cname):
    # return [cloud for cloud in db.session.query(Cloud).filter_by(name=cname)
    #         if cloud.owner_name() == uname]
    # Hosts don't know about owner names yet, todo:15
    return [cloud for cloud in db.session.query(Cloud).filter_by(name=cname)]


def get_client_session(db, uuid, cloud_uname, cloud_cname):
    rd = ERROR()
    matching_clients = db.session.query(Client).filter_by(uuid=uuid).all()
    if len(matching_clients) < 1:
        rd = ERROR('No matching session')
    else:
        for client in matching_clients:
            if client.cloud.name == cloud_cname: # todo:15 use uname/cname
                rd = ResultAndData(True, client)
                break
        if not rd.success:
            rd = ERROR('No matching session')
    return rd


def validate_or_get_client_session(db, uuid, cloud_uname, cloud_cname):
    rd = get_client_session(db, uuid, cloud_uname, cloud_cname)
    mylog('validate_or_get_client_session[{}]={}'.format(0, rd))
    if rd.success:
        client = rd.data
        client.refresh()
        db.session.commit()
        mylog('validate_or_get_client_session[{}]={}'.format(1, rd))
        # great, this client is good to go
        pass
    else:
        clouds = get_clouds_by_name(db, cloud_uname, cloud_cname)
        # okay, so weirdness. Technically, nebs is going to be asking each
        # remote if any of these clouds were the right one.
        # and technically, there could be two different remotes with the same
        # un/cn pair on them. So one of them could be true, the other not.
        # they could both be true. one could even fake that it's true to spoof
        # the real one.
        # obviously, #fixme #todo:16
        verified_cloud = False
        for cloud in clouds:
            # for each cloud, connect to it, ask about the client.
            # if the client is alright, make an entry for it and return it.
            # otherwise, keep looking.
            rd = cloud.get_remote_conn()
            mylog('validate_or_get_client_session[{}]={}'.format(2, rd))
            if rd.success:
                conn = rd.data
                msg = HostVerifyClientRequestMessage(cloud.my_id_from_remote
                                                     , uuid
                                                     , cloud_uname
                                                     , cloud_cname)
                conn.send_obj(msg)
                response = conn.recv_obj()
                if response.type == HOST_VERIFY_CLIENT_SUCCESS:
                    # client = Client(uuid, response.user_id)
                    client = Client()
                    client.uuid = uuid
                    client.user_id = response.user_id
                    db.session.add(client)
                    cloud.clients.append(client)
                    db.session.commit()
                    rd = ResultAndData(True, client)
                    mylog('validate_or_get_client_session[{}]={}'.format(3, rd))
                    mylog('client.cloud={}'.format(client.cloud))
                    verified_cloud = True
                    break
                else:
                    continue
        if not verified_cloud:
            rd = ERROR()
            mylog('validate_or_get_client_session[{}]={}'.format(4, rd))
    if not rd.success:
        rd = ResultAndData(False,
                           'Could not verify client session={}'.format(uuid))
        print rd.data
    return rd


def setup_remote_socket(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    # ipv6: 
    # s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    # s.connect((host, port, 0, 0))
    # s.create_connection((host, port))
    # TODO May want to use:
    # socket.create_connection(address[, timeout[, source_address]])
    # cont  instead, where address is a (host,port) tuple. It'll try and
    # cont  auto-resolve? which would be dope.
    sslSocket = ssl.wrap_socket(s)
    return sslSocket
