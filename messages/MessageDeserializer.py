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
    , ASSIGN_HOST_ID: AssignHostIDMessage.deserialize # 1
    , HOST_HANDSHAKE: HostHandshakeMessage.deserialize # 2
    , REMOTE_HANDSHAKE: 3
    , REM_HANDSHAKE_GO_FETCH: 4
    , REQUEST_CLOUD: RequestCloudMessage.deserialize # 5
    , GO_RETRIEVE_HERE: GoRetrieveMessage.deserialize # 6
    , PREPARE_FOR_FETCH: PrepareForFetchMessage.deserialize # 7
    , HOST_HOST_FETCH: HostHostFetchMessage.deserialize # 8
    , HOST_FILE_TRANSFER: HostFileTransferMessage.deserialize # 9
    , MAKE_CLOUD_REQUEST: 10
    , MAKE_CLOUD_RESPONSE: 11
    , MAKE_USER_REQUEST: 12
    , MAKE_USER_RESPONSE: 13
    , MIRRORING_COMPLETE: MirroringCompleteMessage.deserialize # 14
    , GET_HOSTS_REQUEST: GetHostsRequestMessage.deserialize # 15
    , GET_HOSTS_RESPONSE: GetHostsResponseMessage.deserialize # 16
    , COME_FETCH: 17
    , REMOVE_FILE: RemoveFileMessage.deserialize # 18
    , HOST_FILE_PUSH: HostFilePushMessage.deserialize # 19
    , STAT_FILE_REQUEST: StatFileRequestMessage.deserialize # 20
    , STAT_FILE_RESPONSE: StatFileResponseMessage.deserialize # 21
    , LIST_FILES_REQUEST: ListFilesRequestMessage.deserialize # 22
    , LIST_FILES_RESPONSE: ListFilesResponseMessage.deserialize # 23
    , READ_FILE_REQUEST: 24
    , READ_FILE_RESPONSE: 25
    , CLIENT_SESSION_REQUEST: ClientSessionRequestMessage.deserialize # 26
    , CLIENT_SESSION_ALERT: ClientSessionAlertMessage.deserialize # 27
    , CLIENT_SESSION_RESPONSE: ClientSessionResponseMessage.deserialize #28
    , CLIENT_FILE_PUT: ClientFilePutMessage.deserialize # 29
    , CLIENT_FILE_TRANSFER: ClientFileTransferMessage.deserialize #30
    , CLIENT_GET_CLOUDS_REQUEST: ClientGetCloudsRequest.deserialize #31
    , CLIENT_GET_CLOUDS_RESPONSE: ClientGetCloudsResponse.deserialize #32
    , CLIENT_GET_CLOUD_HOST_REQUEST: ClientGetCloudHostRequest.deserialize #33
    , CLIENT_GET_CLOUD_HOST_RESPONSE: ClientGetCloudHostResponse.deserialize #34
}


class MessageDeserializer(object):
    @staticmethod
    def decode_msg(json_string):
        print 'decoding"{}"'.format(json_string)
        json_dict = json.loads(json_string)
        if 'type' not in json_dict.keys():
            raise
        msg_type = json_dict['type']
        return _decoder_table[msg_type](json_dict)

