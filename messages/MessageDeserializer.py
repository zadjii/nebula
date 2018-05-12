# last generated 2018-05-11 00:36:23.513000
import json
from msg_codes import *
from messages import *
from common_util import *
_decoder_table = {
    DIR_IS_NOT_EMPTY: DirIsNotEmptyMessage.deserialize # -19
    , FILE_ALREADY_EXISTS: FileAlreadyExistsMessage.deserialize # -18
    , ADD_CONTRIBUTOR_FAILURE: AddContributorFailureMessage.deserialize # -17
    , ADD_OWNER_FAILURE: AddOwnerFailureMessage.deserialize # -16
    , MIRROR_FAILURE: MirrorFailureMessage.deserialize # -15
    , SYSTEM_FILE_WRITE_ERROR: SystemFileWriteErrorMessage.deserialize # -14
    , UNKNOWN_IO_ERROR: UnknownIoErrorMessage.deserialize # -13
    , HOST_VERIFY_HOST_FAILURE: HostVerifyHostFailureMessage.deserialize # -12
    , INVALID_PERMISSIONS: InvalidPermissionsMessage.deserialize # -11
    , NO_ACTIVE_HOST: NoActiveHostMessage.deserialize # -10
    , INVALID_STATE: InvalidStateMessage.deserialize # -9
    , CLIENT_AUTH_ERROR: ClientAuthErrorMessage.deserialize # -8
    , HOST_VERIFY_CLIENT_FAILURE: HostVerifyClientFailureMessage.deserialize # -7
    , FILE_DOES_NOT_EXIST_ERROR: FileDoesNotExistErrorMessage.deserialize # -6
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
    , HOST_HOST_FETCH: HostHostFetchMessage.deserialize # 8
    , HOST_FILE_TRANSFER: HostFileTransferMessage.deserialize # 9
    , MAKE_CLOUD_REQUEST: MakeCloudRequestMessage.deserialize # 10
    , MAKE_CLOUD_RESPONSE: MakeCloudResponseMessage.deserialize # 11
    , MAKE_USER_REQUEST: MakeUserRequestMessage.deserialize # 12
    , MAKE_USER_RESPONSE: MakeUserResponseMessage.deserialize # 13
    , MIRRORING_COMPLETE: MirroringCompleteMessage.deserialize # 14
    , GET_HOSTS_REQUEST: GetHostsRequestMessage.deserialize # 15
    , GET_HOSTS_RESPONSE: GetHostsResponseMessage.deserialize # 16
    , FILE_TRANSFER_SUCCESS: FileTransferSuccessMessage.deserialize # 17
    , REMOVE_FILE: RemoveFileMessage.deserialize # 18
    , HOST_FILE_PUSH: HostFilePushMessage.deserialize # 19
    , STAT_FILE_REQUEST: StatFileRequestMessage.deserialize # 20
    , STAT_FILE_RESPONSE: StatFileResponseMessage.deserialize # 21
    , LIST_FILES_REQUEST: ListFilesRequestMessage.deserialize # 22
    , LIST_FILES_RESPONSE: ListFilesResponseMessage.deserialize # 23
    , READ_FILE_REQUEST: ReadFileRequestMessage.deserialize # 24
    , READ_FILE_RESPONSE: ReadFileResponseMessage.deserialize # 25
    , CLIENT_SESSION_REQUEST: ClientSessionRequestMessage.deserialize # 26
    , CLIENT_SESSION_REFRESH: ClientSessionRefreshMessage.deserialize # 27
    , CLIENT_SESSION_RESPONSE: ClientSessionResponseMessage.deserialize # 28
    , CLIENT_FILE_PUT: ClientFilePutMessage.deserialize # 29
    , CLIENT_FILE_TRANSFER: ClientFileTransferMessage.deserialize # 30
    , CLIENT_GET_CLOUDS_REQUEST: ClientGetCloudsRequestMessage.deserialize # 31
    , CLIENT_GET_CLOUDS_RESPONSE: ClientGetCloudsResponseMessage.deserialize # 32
    , CLIENT_GET_CLOUD_HOST_REQUEST: ClientGetCloudHostRequestMessage.deserialize # 33
    , CLIENT_GET_CLOUD_HOST_RESPONSE: ClientGetCloudHostResponseMessage.deserialize # 34
    , GET_ACTIVE_HOSTS_REQUEST: GetActiveHostsRequestMessage.deserialize # 35
    , GET_ACTIVE_HOSTS_RESPONSE: GetActiveHostsResponseMessage.deserialize # 36
    , CLIENT_MIRROR: ClientMirrorMessage.deserialize # 37
    , CLIENT_GET_CLOUD_HOSTS_REQUEST: ClientGetCloudHostsRequestMessage.deserialize # 38
    , CLIENT_GET_CLOUD_HOSTS_RESPONSE: ClientGetCloudHostsResponseMessage.deserialize # 39
    , HOST_VERIFY_CLIENT_REQUEST: HostVerifyClientRequestMessage.deserialize # 40
    , HOST_VERIFY_CLIENT_SUCCESS: HostVerifyClientSuccessMessage.deserialize # 41
    , HOST_VERIFY_HOST_REQUEST: HostVerifyHostRequestMessage.deserialize # 42
    , HOST_VERIFY_HOST_SUCCESS: HostVerifyHostSuccessMessage.deserialize # 43
    , MIRROR_SUCCESS: MirrorSuccessMessage.deserialize # 44
    , CLIENT_ADD_OWNER: ClientAddOwnerMessage.deserialize # 45
    , ADD_OWNER_SUCCESS: AddOwnerSuccessMessage.deserialize # 46
    , GET_USER_ID: GetUserIdMessage.deserialize # 47
    , USER_ID_RESPONSE: UserIdResponseMessage.deserialize # 48
    , CLIENT_ADD_CONTRIBUTOR: ClientAddContributorMessage.deserialize # 49
    , ADD_CONTRIBUTOR: AddContributorMessage.deserialize # 50
    , ADD_CONTRIBUTOR_SUCCESS: AddContributorSuccessMessage.deserialize # 51
    , REFRESH_MESSAGE: RefreshMessageMessage.deserialize # 52
    , HOST_MOVE_REQUEST: HostMoveRequestMessage.deserialize # 53
    , HOST_MOVE_RESPONSE: HostMoveResponseMessage.deserialize # 54
    , CLIENT_UPGRADE_CONNECTION_REQUEST: ClientUpgradeConnectionRequestMessage.deserialize # 55
    , ENABLE_ALPHA_ENCRYPTION_RESPONSE: EnableAlphaEncryptionResponseMessage.deserialize # 56
    , CLIENT_MAKE_DIRECTORY: ClientMakeDirectoryMessage.deserialize # 57
    , CLIENT_MAKE_DIRECTORY_RESPONSE: ClientMakeDirectoryResponseMessage.deserialize # 58
    , CLIENT_GET_PERMISSIONS: ClientGetPermissionsMessage.deserialize # 59
    , CLIENT_GET_PERMISSIONS_RESPONSE: ClientGetPermissionsResponseMessage.deserialize # 60
    , CLIENT_GET_SHARED_PATHS: ClientGetSharedPathsMessage.deserialize # 61
    , CLIENT_GET_SHARED_PATHS_RESPONSE: ClientGetSharedPathsResponseMessage.deserialize # 62
    , CLIENT_CREATE_LINK_REQUEST: ClientCreateLinkRequestMessage.deserialize # 63
    , CLIENT_CREATE_LINK_RESPONSE: ClientCreateLinkResponseMessage.deserialize # 64
    , HOST_RESERVE_LINK_REQUEST: HostReserveLinkRequestMessage.deserialize # 65
    , HOST_RESERVE_LINK_RESPONSE: HostReserveLinkResponseMessage.deserialize # 66
    , CLIENT_GET_LINK_HOST: ClientGetLinkHostMessage.deserialize # 67
    , CLIENT_READ_LINK: ClientReadLinkMessage.deserialize # 68
    , CLIENT_DELETE_FILE_REQUEST: ClientDeleteFileRequestMessage.deserialize # 69
    , CLIENT_DELETE_DIR_REQUEST: ClientDeleteDirRequestMessage.deserialize # 70
    , CLIENT_DELETE_RESPONSE: ClientDeleteResponseMessage.deserialize # 71
}


class MessageDeserializer(object):
    @staticmethod
    def decode_msg(json_string):
        _log = get_mylog()
        if _log is not None:
            _log.debug('->decoding "{}"'.format(json_string))
        json_dict = json.loads(json_string)
        if 'type' not in json_dict.keys():
            raise Exception()
        msg_type = json_dict['type']
        return _decoder_table[msg_type](json_dict)
