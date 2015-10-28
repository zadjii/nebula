__author__ = 'Mike'
from msg_codes import *
from messages import *
_decoder_table = {
    FILE_IS_NOT_DIR_ERROR: -5
    , FILE_IS_DIR_ERROR: -4
    , UNPREPARED_HOST_ERROR: -3
    , AUTH_ERROR: -2
    , GENERIC_ERROR: -1
    , NEW_HOST_MSG: NewHostMessage.deserialize # 0
    , ASSIGN_HOST_ID: 1
    , HOST_HANDSHAKE: 2
    , REMOTE_HANDSHAKE: 3
    , REM_HANDSHAKE_GO_FETCH: 4
    , REQUEST_CLOUD: 5
    , GO_RETRIEVE_HERE: 6
    , PREPARE_FOR_FETCH: 7
    , HOST_HOST_FETCH: 8
    , HOST_FILE_TRANSFER: 9
    , MAKE_CLOUD_REQUEST: 10
    , MAKE_CLOUD_RESPONSE: 11
    , MAKE_USER_REQUEST: 12
    , MAKE_USER_RESPONSE: 13
    , MIRRORING_COMPLETE: 14
    , GET_HOSTS_REQUEST: 15
    , GET_HOSTS_RESPONSE: 16
    , COME_FETCH: 17
    , REMOVE_FILE: 18
    , HOST_FILE_PUSH: 19
    , STAT_FILE_REQUEST: 20
    , STAT_FILE_RESPONSE: 21
    , LIST_FILES_REQUEST: 22
    , LIST_FILES_RESPONSE: BaseMessage.deserialize # 23
    , READ_FILE_REQUEST: 24
    , READ_FILE_RESPONSE: 25
    , CLIENT_SESSION_REQUEST: 26
    , CLIENT_SESSION_ALERT: 27
    , CLIENT_SESSION_RESPONSE: 28
    , CLIENT_FILE_PUT: 29
    , CLIENT_FILE_TRANSFER: 30
}


class MessageDeserializer(object):
    @staticmethod
    def decode_msg(json_string):
        json_dict = json.loads(json_string)
        if 'type' not in json_dict.keys():
            raise
        msg_type = json_dict['type']
        return _decoder_table[msg_type](json_dict)

