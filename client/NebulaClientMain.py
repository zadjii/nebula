import sys, os

from client.ClientInstance import ClientInstance
from client.ClientSettings import ClientSettings
from client.HostSession import RemoteSession, HostSession
from common_util import *
from connections.RawConnection import RawConnection


def main(args):
    print('nebula client')
    print(args)
    # remote = RemoteSession('foo', 12345)

    settings = ClientSettings()
    instance = None
    rd = settings.load_settings()
    if rd.success:
        instance = ClientInstance(settings)

    remote_addr = settings.default_remote_address
    # get remote from args
    # remote_addr = 'localhost'  # fixme: remove debug hard-coded values
    instance.remote_address = remote_addr
    remote_session = instance.get_remote_session()

    # todo: Default username should be stored per-remote
    username = settings.default_username
    # Get some user input
    username = 'Mike-Griese'  # fixme: remove debug hard-coded values
    instance.username = username

    # todo: Default cloudname should be stored per-remote
    if (settings.default_uname is None) or (settings.default_cname is None):
        un_cn = None
    else:
        un_cn = get_full_cloudname(settings.default_uname, settings.default_cname)
    # process args to get the remote we're connecting to
    un_cn = 'Mike-Griese/AfterglowWedding2017'  # fixme: remove debug hard-coded values
    if un_cn is None:
        print('Must enter a cloudname')
        return

    host_session = None
    rd = Error()
    sid = settings.get_sid(instance.remote_address, instance.username)
    if sid is None:
        if instance.username is None:
            print('Enter Username')
            return
        print('Enter Password')
        # prompt for password
        # password = raw_input('Enter Password')
        password = 'Mike Griese'  # fixme: remove debug hard-coded values
        rd = remote_session.create_client_session(instance.username, password)
        if rd.success:
            host_session = rd.data
        else:
            print('Failed to connect to remote, error:\n{}'.format(rd.data))
    else:
        host_session = HostSession(sid, remote_session)
        rd = Success()

    print('host_session success={}'.format(rd.success))
    if rd.success:
        rd = validate_cloudname(un_cn)
    if rd.success:
        uname, cname = rd.data
        instance.uname = uname
        instance.cname = cname
        print('getting host for ({},{})'.format(instance.uname, instance.cname))
        rd = host_session.get_host(instance.uname, instance.cname)

    if rd.success:
        print('Connected to host')
        # host_session.connect()
        rd = host_session.ls('/')
        if rd.success:
            print(rd.data.ls)


if __name__ == '__main__':
    main(sys.argv)
