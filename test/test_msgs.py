__author__ = 'zadjii'

from datetime import datetime
from msg_codes import *
from werkzeug.security import generate_password_hash

def test_msgs():
    print '#' * 80
    print '# Running test_msgs to see json of various message types '
    print '#' * 80
    print '_____Making NEW_HOST_MSG[0] json_____'
    msg = make_new_host_json()
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

