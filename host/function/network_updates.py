import os
from datetime import datetime

from common_util import ResultAndData, send_error_and_close, Error, Success, get_mylog, datetime_from_string
from common.RelativePath import RelativePath
from host import Cloud
# from host.function.network.ls_handler import list_files_handler
from host.function.recv_files import recv_file_tree
from host.function.send_files import send_tree, send_file_to_local, send_file_to_other, complete_sending_files
from host.util import check_response, mylog, find_deletable_children, \
    get_matching_clouds, FILE_SYNC_PROPOSAL_ACKNOWLEDGE, \
    FILE_SYNC_PROPOSAL_REJECT, FILE_SYNC_PROPOSAL_ACCEPT, FILE_CHANGE_TYPE_CREATE, \
    FILE_CHANGE_TYPE_MODIFY, FILE_CHANGE_TYPE_DELETE, FILE_CHANGE_TYPE_MOVE
from messages import HostVerifyHostFailureMessage, HostVerifyHostRequestMessage, InvalidStateMessage, \
    UnknownIoErrorMessage, FileSyncResponseMessage, RemoveFileMessage, FileSyncCompleteMessage
from msg_codes import *

__author__ = 'Mike'


def verify_host(db, cloud_uname, cname, local_id, other_id):
    """
    Returns either (False, error_string) or (True, matching_mirror)
    """
    rd = ResultAndData(False, None)
    # I'm naming this a mirror because that's what it is.
    # The other host was told to come look for a particular mirror here.
    # if that mirror isn't here, (but another mirror of that cloud is), don't
    # process this request.
    mirror = db.session.query(Cloud).filter_by(my_id_from_remote=local_id).first()
    if mirror is None:
        err = 'That mirror isn\'t on this host.'
        rd = ResultAndData(False, err)
    else:
        rd = mirror.get_remote_conn()

    if rd.success:
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
        except Exception as e:
            rd = ResultAndData(False, e)
    return rd


def handle_fetch(host_obj, connection, address, msg_obj):
    _log = get_mylog()
    db = host_obj.get_instance().make_db_session()
    _log.debug('handle_fetch 1')
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
    _log.debug('handle_fetch 2')

    matching_mirror = rd.data

    their_ip = address[0]
    _log.debug('The connected host is via IP="{}"'.format(their_ip))

    rel_path = RelativePath()
    rd = rel_path.from_relative(requested_root)
    if not rd.success:
        err = InvalidStateMessage('{} is not a valid path'.format(requested_root))
        send_error_and_close(err, connection)

    # db.session.close()
    send_tree(other_id, matching_mirror, rel_path, connection)
    _log.debug('Bottom of handle_fetch')
    _log.debug('handle_fetch 3')


# def handle_file_change(host_obj, connection, address, msg_obj):
#     # This is called on HOST_FILE_PUSH, indicating that the next message
#     # says what we're doing.
#     # See .../host/function/local_updates.py@update_peer() for the other end.
#     db = host_obj.get_db()
#     _log = get_mylog()
#     my_id = msg_obj.tid
#     cloudname = msg_obj.cname
#     cloud_uname = msg_obj.cloud_uname
#     updated_file = msg_obj.fpath
#     their_ip = address[0]
#
#     rd = get_matching_clouds(db, my_id)
#     if not rd.success:
#         Error()
#         return
#     matching_mirror = rd.data
#
#     # I used to search through IncomingHostEntries here to make
#     # sure this mirror was told to expect the incoming host.
#     # See 303ef2f which is the last with this commented code
#     # However, the remote doesn't tell us that anymore.
#     # We need a new way to verify that Host->Host transfers are okay.
#     # This will involve some better TLS thing or some sort of E2E authentication.
#
#     rd = _retrieve_file_from_connection(host_obj, connection, db, matching_mirror)
#     if not rd.success:
#         _log.error(rd.data)
#
#     _log.debug('[{}]bottom of handle_file_change(...,{})'
#           .format(my_id, msg_obj.serialize()))


def _retrieve_file_from_connection(host_obj, connection, db, mirror):
    # We now look at the next message to see what to do.
    #  - HFT: Receive children.
    #  - RF: Delete children
    resp_obj = connection.recv_obj()
    resp_type = resp_obj.type

    rd = Error('Unexpected message type {} (expected {} or {})'.format(resp_type, HOST_FILE_TRANSFER, REMOVE_FILE))
    if resp_type == HOST_FILE_TRANSFER:
        rd = recv_file_tree(host_obj, resp_obj, mirror, connection, db)
    elif resp_type == REMOVE_FILE:
        rd = handle_remove_file(host_obj, resp_obj, mirror, db)
    return rd


def handle_remove_file(host_obj, msg_obj, mirror, db):
    # type: (Host, BaseMessage, Cloud, SimpleDB) -> Any
    if mirror is None:
        pass  # fixme magic error

    id = msg_obj.id  # I believe this is the ID of the mirror it's intended for.
                     # Should be == mirror.my_id_from_remote fixme test this assumption.
    cloud_uname = msg_obj.cloud_uname
    cname = msg_obj.cname
    # relative_path = msg_obj.fpath
    relative_path = RelativePath()
    rd = relative_path.from_relative(msg_obj.fpath)
    if not rd.success:
        return rd

    rd = do_remove_file(host_obj, mirror, relative_path, db)
    if not rd.success:
        mylog('[{}] Failed to delete {}'.format(mirror.my_id_from_remote, relative_path))
    else:
        mylog('[{}] Successfully deleted {}'.format(mirror.my_id_from_remote, relative_path))

    return rd


def do_remove_file(host_obj, mirror, relative_path, db):
    # type: (HostController, Cloud, RelativePath, SimpleDB) -> ResultAndData
    rd = Error()
    timestamp = datetime.utcnow()
    # Things to do:
    #  - remove all children nodes from DB older than timestamp
    #  - remove same set of child files
    #  - DON'T clean up .nebs - The host who sent this delete should also send that update.

    full_path = relative_path.to_absolute(mirror.root_directory)
    file_node = mirror.get_child_node(relative_path)
    if file_node is None:
        err = 'There was no node in the tree for path:{}'.format(relative_path.to_string())
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
    if os.path.exists(full_path):
        if os.path.isdir(full_path):
            os.rmdir(full_path)
        else:
            os.remove(full_path)
    else:
        mylog('The file doesn\'t exist - may have already been deleted')

    db.session.commit()
    rd = Success(deletables)

    return rd

def prepare_and_do_file_change_proposal(host_obj, msg_obj):
    # type: (HostController, FileSyncProposalMessage) -> ResultAndData
    # type: (HostController, FileSyncProposalMessage) -> ResultAndData(True, int)
    # type: (HostController, FileSyncProposalMessage) -> ResultAndData(False, BasMessage)


    # 07-Mar-2020: This represents the 12a1, 14a2, 17a3 cases in the flow chart.
    # We're handling the 11a message here, _from the host we asked_ in
    # `handle_file_sync_request`

    db = host_obj.get_db()
    _log = get_mylog()
    requestor_id = msg_obj.src_id
    # TODO: validate the requestor with the remote
    #
    # TODO 07-Mar-2020: I don't think the above comment is needed anymore. We
    # should go through and update the names in here.

    _log.debug('Attempting to handle a FileSyncProposal={}'.format(msg_obj.serialize()))

    mirror_id = msg_obj.tgt_id
    change_type = msg_obj.change_type
    proposed_last_sync = msg_obj.sync_time
    is_dir = msg_obj.is_dir

    rd = get_matching_clouds(db, mirror_id)
    if not rd.success:
        # todo: this error isn't very informative
        response = InvalidStateMessage(rd.data)
        # connection.send_obj(response)
        return rd
    matching_mirror = rd.data

    rd, src_path = RelativePath.make_relative(msg_obj.rel_path)
    if not rd.success:
        # todo: this error isn't very informative
        response = UnknownIoErrorMessage(rd.data)
        # connection.send_obj(response)
        return rd

    tgt_path = None
    if msg_obj.tgt_path is not None:
        rd, tgt_path = RelativePath.make_relative(msg_obj.tgt_path)
        if not rd.success:
            # todo: this error isn't very informative
            response = UnknownIoErrorMessage(rd.data)
            # connection.send_obj(response)
            return rd

    rd = _do_file_change_proposal(db, matching_mirror, src_path, tgt_path, change_type, is_dir, proposed_last_sync)
    if not rd.success:
        _log.error('Encountered an error in _do_file_change_proposal="{}"'.format(rd.data))
        rd = InvalidStateMessage(rd.data)
    return rd


def handle_file_change_proposal(host_obj, connection, address, msg_obj):
    # type: (HostController, AbstractConnection, str, BaseMessage) -> ResultAndData

    # # NOTE: as of Feb 2019, FileChangePropoasl messages aren't sent by a host
    # #   in response to a RemoteHandshake anymore. They are sent in response to
    # #   a FileSyncRequest from another host

    # # 07-Mar-2020: This represents the 12a1, 14a2, 17a3 cases in the flow chart.
    # # We're handling the 11a message here, _from the host we asked_ in
    # # `handle_file_sync_request`
    # #
    # # TODO: This isn't called anywhere yet. This needs to be called in
    # # local_updates.py:check_local_modifications. That method is going to
    # # recieve a RemoteMirrorHandshake, then find another mirror, and send a
    # # FileSyncRequest to that mirror. That other mirror will handle the message
    # # in handle_file_sync_request, and send a FileChangePropoasl back to us to
    # # handle here.

    db = host_obj.get_db()
    _log = get_mylog()
    # requestor_id = msg_obj.src_id
    # # TODO: validate the requestor with the remote
    # #
    # # TODO 07-Mar-2020: I don't think the above comment is needed anymore. We
    # # should go through and update the names in here.

    # _log.debug('Attempting to handle a FileSyncProposal={}'.format(msg_obj.serialize()))

    # mirror_id = msg_obj.tgt_id
    # change_type = msg_obj.change_type
    # proposed_last_sync = msg_obj.sync_time
    # is_dir = msg_obj.is_dir

    # rd = get_matching_clouds(db, mirror_id)
    # if not rd.success:
    #     # todo: this error isn't very informative
    #     response = InvalidStateMessage(rd.data)
    #     connection.send_obj(response)
    #     return rd
    # matching_mirror = rd.data

    # rd, src_path = RelativePath.make_relative(msg_obj.rel_path)
    # if not rd.success:
    #     # todo: this error isn't very informative
    #     response = UnknownIoErrorMessage(rd.data)
    #     connection.send_obj(response)
    #     return rd

    # tgt_path = None
    # if msg_obj.tgt_path is not None:
    #     rd, tgt_path = RelativePath.make_relative(msg_obj.tgt_path)
    #     if not rd.success:
    #         # todo: this error isn't very informative
    #         response = UnknownIoErrorMessage(rd.data)
    #         connection.send_obj(response)
    #         return rd

    # rd = _do_file_change_proposal(db, matching_mirror, src_path, tgt_path, change_type, is_dir, proposed_last_sync)

    rd = prepare_and_do_file_change_proposal(host_obj, msg_obj)

    if not rd.success:
        connection.send_obj(rd.data)
        return rd
    else:
        # We succeeded, the data is our response type (ACK, ACCEPT, REJECT)
        # if it's ack, just send it and be done
        # reject, send and be done
        # accept, send our response, then read the file transfer message
        response_type = rd.data
        response = FileSyncResponseMessage(response_type)
        connection.send_obj(response)

        if response_type is not FILE_SYNC_PROPOSAL_ACCEPT:
            return Success()

        rd = get_matching_clouds(db, msg_obj.tgt_id)
        if not rd.success:
            # This is very unexpected. We should have already failed in prepare_and_do_file_change_proposal if the mirror doesn't exist.
            # todo: this error isn't very informative
            response = InvalidStateMessage(rd.data)
            connection.send_obj(response)
            return rd
        matching_mirror = rd.data

        # handle the file transfer
        rd = _retrieve_file_from_connection(host_obj, connection, db, matching_mirror)
        if not rd.success:
            _log.error(rd.data)

    return rd


def _do_file_change_proposal(db, mirror, src_path, tgt_path, change_type, is_dir, proposed_last_sync):
    # type: (SimpleDB, Cloud, RelativePath, RelativePath, int, bool, datetime) -> ResultAndData
    # type: (SimpleDB, Cloud, RelativePath, RelativePath, int, bool, datetime) -> ResultAndData(True, int)
    # type: (SimpleDB, Cloud, RelativePath, RelativePath, int, bool, datetime) -> ResultAndData(False, str)
    _log = get_mylog()
    if src_path.is_root() or (tgt_path is not None and tgt_path.is_root()):
        return Error('cannot modify the root of a mirror')

    # cases:
    # No file & CREATE -> accept
    # No file & modify/delete/move -> reject
    # file & CREATE -> reject
    # (file.last_sync <= proposed.last_sync && proposed.last_sync < file.last_modified) -> reject
    # (file.last_sync < proposed.last_sync) -> accept
    # (file.last_sync == proposed.last_sync) -> ack
    # (file.last_sync > proposed.last_sync) -> reject

    src_node = mirror.get_child_node(src_path)
    rd = Error('I wasnt prepared for this case of file change proposal')

    if src_node is None:
        if change_type is FILE_CHANGE_TYPE_CREATE:
            rd = Success(FILE_SYNC_PROPOSAL_ACCEPT)
        else:
            rd = Success(FILE_SYNC_PROPOSAL_REJECT)
    else:
        if change_type is FILE_CHANGE_TYPE_CREATE:
            rd = Success(FILE_SYNC_PROPOSAL_REJECT)
        else:
            file_last_sync = src_node.last_sync
            file_last_modified = src_node.last_modified

            # Our local unsync'd changes (t_2, f_n, any) haven't been sent yet.
            # The file was modified since it's last sync, and our change timestamp is
            #       newer than the proposed sync timestamp.
            # We'll send the update later.
            if (file_last_sync <= proposed_last_sync) and (proposed_last_sync < file_last_modified):
                rd = Success(FILE_SYNC_PROPOSAL_REJECT)
            # It's a newer version of our file, or a file we didn't modify,
            #   - We'll recv the file's contents.
            elif (file_last_sync < proposed_last_sync):
                rd = Success(FILE_SYNC_PROPOSAL_ACCEPT)
            # We have whatever change they're talking about
            elif (file_last_sync == proposed_last_sync):
                # update our last sync timestamp
                src_node.last_sync = proposed_last_sync
                rd = Success(FILE_SYNC_PROPOSAL_ACKNOWLEDGE)
            # Our version is newer than the other's.
            #       The other should know that... *TODO?*
            elif (file_last_sync > proposed_last_sync):
                rd = Success(FILE_SYNC_PROPOSAL_REJECT)

    # Is it this function or _retrieve_file_from_connection's responsibility to update the file's last_sync
    # Answer: recv_file_transfer will update the last_modified timestamp

    _log.debug('Bottom of _do_file_change_proposal(type={}, src={}, proposed_last_sync={})'.format(change_type, src_path.to_string(), proposed_last_sync))
    return rd

def get_proposals_for_message(host_obj, msg_obj):

    rd = Error()

    db = host_obj.get_db()
    _log = get_mylog()
    requestor_id = msg_obj.src_id

    tgt_id = msg_obj.tgt_id
    uname = msg_obj.uname
    cname = msg_obj.cname
    sync_start = datetime_from_string(msg_obj.sync_start)
    sync_end = datetime_from_string(msg_obj.sync_end)

    # TODO: Make sure that remotes prepare for HOST_HOST_VERIFYs when replying
    # to a MirrorHandshake
    #
    # Validate the requestor with the remote - They should have just
    #       handshook the remote, and found they were out of date, which is when
    #       the remote sent them here.
    # 2020: This is _35a_ in the flow chart
    rd = verify_host(db, uname, cname, tgt_id, requestor_id)
    if not rd.success:
        _log.error(rd.data)
    else:
        # If we have files whose last_sync timestamp is in t:(t_0, t_1], send it to
        # the requestor as a `FileChangeProposal`

        cloud = rd.data

        _log.debug('Collecting updates between ({}, {}]'.format(sync_start, sync_end))

        # This is 10a:
        proposals = cloud.get_change_proposals(db,
                                               sync_start=sync_start,
                                               sync_end=sync_end,
                                               target_mirror_id=requestor_id)
        rd = Success((proposals, cloud))
    return rd


def handle_file_sync_request(host_obj, connection, address, msg_obj):
    # type: (HostController, AbstractConnection, str, BaseMessage) -> ResultAndData
    """
    9a-19a in the flowchart

    """

    rd = Error()

    db = host_obj.get_db()
    _log = get_mylog()
    requestor_id = msg_obj.src_id

    tgt_id = msg_obj.tgt_id
    uname = msg_obj.uname
    cname = msg_obj.cname
    sync_start = datetime_from_string(msg_obj.sync_start)
    sync_end = datetime_from_string(msg_obj.sync_end)

    rd = get_proposals_for_message(host_obj, msg_obj)
    if not rd.success:
        return rd

    proposals, cloud = rd.data
    for p in proposals:
        # Send to requestor
        # This is _11a_ in the flowchart
        connection.send_obj(p)

        # Get the response from the requestor
        # This is _13a1, 15a2, 18a3_ in the flowchart
        response = connection.recv_obj()

        if response.type != FILE_SYNC_RESPONSE:
            err = 'Other host did not reply with a FILE_SYNC_RESPONSE'
            _log.error(err)
            connection.send_obj(InvalidStateMessage(err))
            return Error(err)

        sync_response_type = response.resp_type
        if sync_response_type == FILE_SYNC_PROPOSAL_ACCEPT:
            # TODO: if they accepted the file, send the file here
            # This is _16a2_

            matching_local_mirror = db.session.query(Cloud).filter_by(my_id_from_remote=requestor_id).first()

            rd, src_path = RelativePath.make_relative(msg_obj.rel_path)
            if not rd.success:
                # This is unexpected, by this point we should have already made a relative path from this path.
                return rd

            # TODO: I don't think we need the is_local_peer code here - we'll
            # handle that way sooner, in get_update_from_local_host
            is_local_peer = matching_local_mirror is not None

            if p.change_type == FILE_CHANGE_TYPE_CREATE or p.change_type == FILE_CHANGE_TYPE_MODIFY:
                if is_local_peer:
                    send_file_to_local(db, cloud, matching_local_mirror, src_path)
                else:
                    send_file_to_other(requestor_id, cloud, src_path, connection, recurse=False)

            # If we deleted the file, delete it here.
            elif p.change_type == FILE_CHANGE_TYPE_DELETE:
                msg = RemoveFileMessage(requestor_id, cloud.uname(), cloud.cname(), src_path.to_string())
                if is_local_peer:
                    handle_remove_file(host_obj, msg, matching_local_mirror, db)
                else:
                    connection.send_obj(msg)

            # TODO: If we _moved_ the file, move it here?
            elif p.change_type == FILE_CHANGE_TYPE_MOVE:
                # TODO: I don't think we support this at all yet
                err = 'We don\'t yet support FILE_CHANGE_TYPE_MOVE, but it happened...'
                _log.error(err)
                connection.send_obj(InvalidStateMessage(err))
                return Error(err)

            complete_sending_files(requestor_id, cloud, src_path, connection)

        elif (sync_response_type == FILE_SYNC_PROPOSAL_ACKNOWLEDGE) or (sync_response_type == FILE_SYNC_PROPOSAL_REJECT):
            # they either already have this change, or they rejected this
            # change, because their version of the file is newer. We don't need
            # to do anything here.
            pass

    # TODO: Send a FileSyncComplete to mark that we're done sending the changes
    #       we have on this interval.
    # This is _19a_ in the flowchart
    connection.send_obj(FileSyncCompleteMessage())


    return rd

