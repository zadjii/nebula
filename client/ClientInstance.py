from client.HostSession import RemoteSession


class ClientInstance(object):
    """
    Usage:
    First instantiate a ClientSettings, and load_settings.
    That will populate the Settings object with the default settings.

    Then, parse commanline args and other input to further populate members of this class.
    eg.
    There's a default_remote_address in the settings, but the [-r address] parameter could overwrite that.
    """
    def __init__(self, client_settings):
        # type: (ClientSettings) -> ClientInstance
        """

        :param client_settings:
        """
        self.remote_address = client_settings.default_remote_address
        self.remote_port = client_settings.default_remote_port
        self.username = client_settings.default_username
        self.uname = client_settings.default_uname
        self.cname = client_settings.default_cname
        self.settings = client_settings

    def get_remote_session(self):
        return RemoteSession(self.remote_address, self.remote_port)



