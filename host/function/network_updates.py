import os
from datetime import datetime

from common_util import ResultAndData, send_error_and_close, Error, Success
from host import Cloud
# from host.function.network.ls_handler import list_files_handler
from host.function.recv_files import recv_file_tree
from host.function.send_files import send_tree
from host.util import check_response, mylog, validate_host_id, find_deletable_children
from messages import HostVerifyHostFailureMessage, HostVerifyHostRequestMessage
from msg_codes import *

__author__ = 'Mike'


def verify_host(db, cloud_uname, cname, local_id, other_id):
    """
    Returns either (False, error_string) or (True, matching_mirror)
    """
    rd = ResultAndData(False, None)
    mylog('verify_host 0')
    # I'm naming this a mirror because that's what it is.
    # The other host was told to come look for a particular mirror here.
    # if that mirror isn't here, (but another mirror of that cloud is), don't
    # process this request.
    mirror = db.session.query(Cloud).filter_by(my_id_from_remote=local_id).first()
    mylog('verify_host 1')
    if mirror is None:
        err = 'That mirror isn\'t on this host.'
        rd = ResultAndData(False, err)
        mylog('verify_host 2')
    else:
        rd = mirror.get_remote_conn()
        if rd.success:
            mylog('verify_host 3')
            rem_conn = rd.data
            msg = HostVerifyHostRequestMessage(local_id, other_id, cloud_uname, cname)
            try:
                rem_conn.send_obj(msg)
                response = rem_conn.recv_obj()
                if response.type == HOST_VERIFY_HOST_SUCCESS:
                    rd = ResultAndData(True, mirror)
                elif response.type == HOST_VERIFY_HOST_FAILURE:
                    rd = ResultAndData(False, 'Remote responded with failure: "{}"'.format(response.message))
                else:
                    rd = ResultAndData(False, 'Unknown error while attempting to verify host')
            except Exception, e:
                rd = ResultAndData(False, e)
    mylog('verify_host 4')
    return rd


def handle_fetch(host_obj, connection, address, msg_obj):
    mylog('handle_fetch 0')
    db = host_obj.get_instance().make_db_session ()
    mylog('handle_fetch 1')
    # the id's are swapped because they are named from the origin host's POV.
    other_id = msg_obj.my_id
    local_id = msg_obj.other_id
    cloudname = msg_obj.cname
    cloud_uname = msg_obj.cloud_uname
    requested_root = msg_obj.root

    # Go to the remote, ask them if the fetching host is ok'd to be here.
    rd = verify_host(db, cloud_uname, cloudname, local_id, other_id)
    if not rd.success:
        err = HostVerifyHostFailureMessage(rd.data)
        send_error_and_close(err, connection)
        return
    mylog('handle_fetch 2')

    matching_mirror = rd.data

    their_ip = address[0]
    mylog('The connected host is via IP="{}"'.format(their_ip))

    send_tree(db, other_id, matching_mirror, requested_root, connection)
    mylog('Bottom of handle_fetch', '32')
    mylog('handle_fetch 3')


def handle_file_change(host_obj, connection, address, msg_obj):
    # This is called on HOST_FILE_PUSH, indicating that the next message
    # says what we're doing.
    # See .../host/function/local_updates.py@update_peer() for the other end.
    db = host_obj.get_db()
    my_id = msg_obj.tid
    cloudname = msg_obj.cname
    cloud_uname = msg_obj.cloud_uname
    updated_file = msg_obj.fpath
    their_ip = address[0]

    rd = validate_host_id(db, my_id, connection)
    # validate_host_id will raise an exception if there is no cloud
    matching_id_clouds = rd.data

    # todo:33 replace all the calls to this with a function.
    matching_cloud = matching_id_clouds.filter_by(username=cloud_uname, name=cloudname).first()
    if matching_cloud is None:
        send_generic_error_and_close(connection)
        raise Exception(
            'host came asking for cloudname=\'' + cloudname + '\''
            + ', however, I don\'t have a matching cloud.'
        )

    # I used to search through IncomingHostEntries here to make
    # sure this mirror was told to expect the incoming host.
    # See 303ef2f which is the last with this commented code
    # However, the remote doesn't tell us that anymore.
    # We need a new way to verify that Host->Host transfers are okay.
    # This will involve some better TLS thing or some sort of E2E authentication.

    # We now look at the next message to see what to do.
    #  - HFT: Receive children.
    #  - RF: Delete children
    resp_obj = connection.recv_obj()
    resp_type = resp_obj.type

    if resp_type == HOST_FILE_TRANSFER:
        recv_file_tree(host_obj, resp_obj, matching_cloud, connection, db)
    elif resp_type == REMOVE_FILE:
        handle_remove_file(host_obj, resp_obj, matching_cloud, connection, db)

    mylog('[{}]bottom of handle_file_change(...,{})'
          .format(my_id, msg_obj.serialize()))


def handle_remove_file(host_obj, msg_obj, mirror, connection, db):
    # type: (Host, BaseMessage, Cloud, AbstractConnection, SimpleDB) -> Any
    if mirror is None:
        pass  # fixme magic error

    id = msg_obj.id  # I believe this is the ID of the mirror it's intended for.
                     # Should be == mirror.my_id_from_remote fixme test this assumption.
    cloud_uname = msg_obj.cloud_uname
    cname = msg_obj.cname
    relative_path = msg_obj.fpath
    rd = do_remove_file(host_obj, mirror, relative_path, db)
    if not rd.success:
        mylog('[{}] Failed to delete {}'.format(mirror.my_id_from_remote, relative_path))
    else:
        mylog('[{}] Successfully deleted {}'.format(mirror.my_id_from_remote, relative_path))


def do_remove_file(host_obj, mirror, relative_path, db):
    # type: (Host, Cloud, str, SimpleDB) -> ResultAndData
    rd = Error()
    timestamp = datetime.utcnow()
    # Things to do:
    #  - remove all children nodes from DB older than timestamp
    #  - remove same set of child files
    #  - DON'T clean up .nebs - The host who sent this delete should also send that update.
    full_path = os.path.join(mirror.root_directory, relative_path)

    file_node = mirror.get_child_node(relative_path)
    if file_node is None:
        err = 'There was no node in the tree for path:{}'.format(relative_path)
        return Error(err)

    is_root = file_node.is_root()
    if is_root:
        err = 'Deleting the root of the cloud is not allowed.'
        return Error(err)
    deletables = find_deletable_children(file_node, full_path, timestamp)
    # deletables should be in reverse BFS order, so as they are deleted they
    #   should have no children
    for rel_child_path, node in deletables:
        full_child_path = os.path.join(full_path, rel_child_path)
        db.session.delete(node)
        if os.path.isdir(full_child_path):
            os.rmdir(full_child_path)
        else:
            os.remove(full_child_path)
        # mylog('Deleted node, file for {}'.format(full_child_path), '34')
    db.session.delete(file_node)
    if os.path.isdir(full_path):
        os.rmdir(full_path)
    else:
        os.remove(full_path)
    # mylog('Deleted node, file for {}'.format(full_path), '35')
    db.session.commit()
    rd = Success(deletables)

    return rd

# todo make this work... later
# def filter_func2(connection, address):
#     dont_close = True
#     while dont_close:
#         # keep connection alive and keep processing msgs until reaching an endstate
#         # mostly used for client session type messages
#         msg_obj = recv_msg(connection)
#         msg_type = msg_obj['type']
#         # print 'The message is', msg_obj
#         # todo we should make sure the connection was from the remote or a client
#         # cont   that we were told about here, before doing ANY processing.
#         if msg_type == PREPARE_FOR_FETCH:
#             prepare_for_fetch(connection, address, msg_obj)
#             dont_close = False
#         elif msg_type == HOST_HOST_FETCH:
#             handle_fetch(connection, address, msg_obj)
#             dont_close = False
#         elif msg_type == COME_FETCH:
#             # handle_come_fetch(connection, address, msg_obj)
#             print 'COME_FETCH was a really fucking stupid idea.'
#         elif msg_type == HOST_FILE_PUSH:
#             handle_recv_file(connection, address, msg_obj)
#             dont_close = False
#         elif msg_type == CLIENT_SESSION_ALERT:
#             handle_client_session_alert(connection, address, msg_obj)
#         elif msg_type == STAT_FILE_REQUEST:
#             # fixme
#             pass
#             # handle_recv_file(connection, address, msg_obj)
#         elif msg_type == LIST_FILES_REQUEST:
#             list_files_handler(connection, address, msg_obj)
#         else:
#             print 'I don\'t know what to do with', msg_obj
#             dont_close = False
#     connection.close()


