# last generated 2016-04-10 21:56:22.766000
import json
from msg_codes import *
from messages import *
_decoder_table = {
    FILE_DOES_NOT_EXIST_ERROR: FileDoesNotExistErrorMessage.deserialize # -6
    , FILE_IS_NOT_DIR_ERROR: FileIsNotDirErrorMessage.deserialize # -5
    , FILE_IS_DIR_ERROR: FileIsDirErrorMessage.deserialize # -4
    , UNPREPARED_HOST_ERROR: UnpreparedHostErrorMessage.deserialize # -3
    , AUTH_ERROR: AuthErrorMessage.deserialize # -2
    , GENERIC_ERROR: GenericErrorMessage.deserialize # -1
    , NEW_HOST: NewHostMessage.deserialize # 0
    , ASSIGN_HOST_ID: AssignHostIdMessage.deserialize # 1
    , HOST_HANDSHAKE: HostHandshakeMessage.deserialize # 2
    , REMOTE_HANDSHAKE: RemoteHandshakeMessage.deserialize # 3
    , REM_HANDSHAKE_GO_FETCH: RemHandshakeGoFetchMessage.deserialize # 4
    , REQUEST_CLOUD: RequestCloudMessage.deserialize # 5
    , GO_RETRIEVE_HERE: GoRetrieveHereMessage.deserialize # 6
    , PREPARE_FOR_FETCH: PrepareForFetchMessage.deserialize # 7
    , HOST_HOST_FETCH: HostHostFetchMessage.deserialize # 8
    , HOST_FILE_TRANSFER: HostFileTransferMessage.deserialize # 9
    , MAKE_CLOUD_REQUEST: MakeCloudRequestMessage.deserialize # 10
    , MAKE_CLOUD_RESPONSE: MakeCloudResponseMessage.deserialize # 11
    , MAKE_USER_REQUEST: MakeUserRequestMessage.deserialize # 12
    , MAKE_USER_RESPONSE: MakeUserResponseMessage.deserialize # 13
    , MIRRORING_COMPLETE: MirroringCompleteMessage.deserialize # 14
    , GET_HOSTS_REQUEST: GetHostsRequestMessage.deserialize # 15
    , GET_HOSTS_RESPONSE: GetHostsResponseMessage.deserialize # 16
    , REMOVE_FILE: RemoveFileMessage.deserialize # 18
    , HOST_FILE_PUSH: HostFilePushMessage.deserialize # 19
    , STAT_FILE_REQUEST: StatFileRequestMessage.deserialize # 20
    , STAT_FILE_RESPONSE: StatFileResponseMessage.deserialize # 21
    , LIST_FILES_REQUEST: ListFilesRequestMessage.deserialize # 22
    , LIST_FILES_RESPONSE: ListFilesResponseMessage.deserialize # 23
    , READ_FILE_REQUEST: ReadFileRequestMessage.deserialize # 24
    , READ_FILE_RESPONSE: ReadFileResponseMessage.deserialize # 25
    , CLIENT_SESSION_REQUEST: ClientSessionRequestMessage.deserialize # 26
    , CLIENT_SESSION_ALERT: ClientSessionAlertMessage.deserialize # 27
    , CLIENT_SESSION_RESPONSE: ClientSessionResponseMessage.deserialize # 28
    , CLIENT_FILE_PUT: ClientFilePutMessage.deserialize # 29
    , CLIENT_FILE_TRANSFER: ClientFileTransferMessage.deserialize # 30
    , CLIENT_GET_CLOUDS_REQUEST: ClientGetCloudsRequestMessage.deserialize # 31
    , CLIENT_GET_CLOUDS_RESPONSE: ClientGetCloudsResponseMessage.deserialize # 32
    , CLIENT_GET_CLOUD_HOST_REQUEST: ClientGetCloudHostRequestMessage.deserialize # 33
    , CLIENT_GET_CLOUD_HOST_RESPONSE: ClientGetCloudHostResponseMessage.deserialize # 34
    , GET_ACTIVE_HOSTS_REQUEST: GetActiveHostsRequestMessage.deserialize # 35
    , GET_ACTIVE_HOSTS_RESPONSE: GetActiveHostsResponseMessage.deserialize # 36
}


class MessageDeserializer(object):
    @staticmethod
    def decode_msg(json_string):
        print '\t\t-> decoding"{}"'.format(json_string)
        json_dict = json.loads(json_string)
        if 'type' not in json_dict.keys():
            raise
        msg_type = json_dict['type']
        return _decoder_table[msg_type](json_dict)
