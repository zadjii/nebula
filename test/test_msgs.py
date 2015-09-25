from host import HOST_PORT
from datetime import datetime
from msg_codes import *
from remote import get_db, Cloud
from werkzeug.security import generate_password_hash
__author__ = 'zadjii'

def test_msgs():
    print '#' * 80
    print '# Running test_msgs to see json of various message types '
    print '#' * 80
    print '_____Making NEW_HOST_MSG[0] json_____'
    msg = make_new_host_json(HOST_PORT)
    print get_msg_size(msg), decode_msg_size(get_msg_size(msg))
    print msg

    print '_____Making ASSIGN_HOST_ID[1] json_____'
    msg = make_assign_host_id_json(22, 'todo', 'todo')
    print get_msg_size(msg), decode_msg_size(get_msg_size(msg))
    print msg

    print '_____Making HOST_HANDSHAKE[2] json_____'
    msg = make_host_handshake_json(22, 23456, datetime.utcnow().isoformat())
    print get_msg_size(msg), decode_msg_size(get_msg_size(msg))
    print msg

    # print '_____Making REMOTE_HANDSHAKE[3] json_____'
    # msg = 'Fuck it, not implemented yet'

    # print '_____Making REM_HANDSHAKE_GO_FETCH[4] json_____'
    # msg = 'Fuck it, not implemented yet'

    print '_____Making REQUEST_CLOUD[5] json_____'
    msg = make_request_cloud_json(22, 'fake-cloudname', 'asdf', generate_password_hash('asdf'))
    print get_msg_size(msg), decode_msg_size(get_msg_size(msg))
    print msg

    print '_____Making GO_RETRIEVE_HERE[6] json_____'
    msg = make_go_retrieve_here_json(22, 'localhost', 23456)
    print get_msg_size(msg), decode_msg_size(get_msg_size(msg))
    print msg

    print '_____Making PREPARE_FOR_FETCH[7] json_____'
    msg = make_prepare_for_fetch_json(22, 'fake-cloudname', 'localhost')
    print get_msg_size(msg), decode_msg_size(get_msg_size(msg))
    print msg

    print '_____Making HOST_HOST_FETCH[8] json_____'
    msg = make_host_host_fetch(22, 'fake-cloudname', '/')
    print get_msg_size(msg), decode_msg_size(get_msg_size(msg))
    print msg

    print '_____Making HOST_FILE_TRANSFER[9] json_____'
    msg = make_host_file_transfer(22, 'fake-cloudname', '/foo.file', False, 4000)
    print get_msg_size(msg), decode_msg_size(get_msg_size(msg))
    print msg

    # print '_____Making MAKE_CLOUD_REQUEST[10] json_____'
    # print 'Fuck it, not implemented yet'

    # print '_____Making MAKE_CLOUD_RESPONSE[11] json_____'
    # print 'Fuck it, not implemented yet'

    # print '_____Making MAKE_USER_REQUEST[12] json_____'
    # print 'Fuck it, not implemented yet'

    # print '_____Making MAKE_USER_RESPONSE[13] json_____'
    # print 'Fuck it, not implemented yet'

    print '_____Making MIRRORING_COMPLETE[14] json_____'
    msg = make_mirroring_complete(22, 'fake-cloudname')
    print get_msg_size(msg), decode_msg_size(get_msg_size(msg))
    print msg

    print '_____Making GET_HOSTS_REQUEST[15] json_____'
    msg = make_get_hosts_request(22, 'fake-cloudname')
    print get_msg_size(msg), decode_msg_size(get_msg_size(msg))
    print msg

    print '_____Making GET_HOSTS_RESPONSE[16] json_____'
    db = get_db()
    cloud = db.session.query(Cloud).first()
    msg = make_get_hosts_response(cloud)
    print get_msg_size(msg), decode_msg_size(get_msg_size(msg))
    print msg
    #
    # print '_____Making COME_FETCH[17] json_____'
    # msg = make_come_fetch(22, 23456, 'fake-cloudname', '/foo.file')
    # print get_msg_size(msg), decode_msg_size(get_msg_size(msg))
    # print msg

    print '_____Making REMOVE_FILE[18] json_____'
    msg = make_remove_file(22, 'fake-cloudname', '/foo.file')
    print get_msg_size(msg), decode_msg_size(get_msg_size(msg))
    print msg

    print '_____Making HOST_FILE_PUSH[19] json_____'
    msg = make_host_file_push(22, 'fake-cloudname', '/foo.txt')
    print get_msg_size(msg), decode_msg_size(get_msg_size(msg))
    print msg

    print '_____Making STAT_FILE_REQUEST[20] json_____'
    msg = make_stat_request('fake-cloudname', './test_msgs')
    print get_msg_size(msg), decode_msg_size(get_msg_size(msg))
    print msg

    print '_____Making STAT_FILE_RESPONSE[21] json_____'
    path = os.path.join(sys.path[0], 'run_tests.py')
    print path
    msg = make_stat_response('fake-cloudname', './run_tests.py', path)
    print get_msg_size(msg), decode_msg_size(get_msg_size(msg))
    print msg

    path = sys.path[0]  # os.path.join(sys.path[0], '.')
    print path
    msg = make_stat_response('fake-cloudname', '.', path)
    print get_msg_size(msg), decode_msg_size(get_msg_size(msg))
    print msg

    path = os.path.join(sys.path[0], '..')
    print path
    msg = make_stat_response('fake-cloudname', '..', path)
    print get_msg_size(msg), decode_msg_size(get_msg_size(msg))
    print msg

    print '_____Making LIST_FILES_REQUEST[22] json_____'
    msg = make_list_files_request('fake-cloudname', './test_msgs')
    print get_msg_size(msg), decode_msg_size(get_msg_size(msg))
    print msg

    print '_____Making LIST_FILES_RESPONSE[23] json_____'
    path = os.path.join(sys.path[0], 'run_tests.py')
    print path
    # msg = make_list_files_response('fake-cloudname', './run_tests.py', path)
    print get_msg_size(msg), decode_msg_size(get_msg_size(msg))
    print msg

    path = sys.path[0]  # os.path.join(sys.path[0], '.')
    print path
    msg = make_list_files_response('fake-cloudname', '.', path)
    print get_msg_size(msg), decode_msg_size(get_msg_size(msg))
    print msg

    path = os.path.join(sys.path[0], '..')
    print path
    msg = make_list_files_response('fake-cloudname', '..', path)
    print get_msg_size(msg), decode_msg_size(get_msg_size(msg))
    print msg
