
import os
import platform
from netifaces import interfaces, ifaddresses, AF_INET6

import sys

from common_util import *


class NetworkController(object):
    """docstring for NetworkController"""
    def __init__(self, host_controller):
        super(NetworkController, self).__init__()
        self._host_controller = host_controller
        self._last_external_ip = None
        self._last_local_ip = None
        self._miniupnp = None
        self._miniupnp_module = None
        self._using_upnp = False
        try:
            dependencies_path = None
            is_windows = os.name == 'nt'
            if is_windows:
                dependencies_path = os.path.join(NEBULA_ROOT, 'dep/win64')
                sys.path.append(dependencies_path)

            import miniupnpc
            self._miniupnp_module = miniupnpc
            self._miniupnp = self._miniupnp_module.UPnP()
            self._miniupnp.discoverdelay = 50
            self._using_upnp = True
            if is_windows:
                sys.path.remove(dependencies_path)
        except Exception, e:
            inst = self._host_controller.get_instance()
            if not inst.local_debug:
                raise Exception('MiniUPnP is not available, and nebs is not configured for local debugging. Failing. '
                                'You can manually override this check by setting `LOCAL_DEBUG=1` in your `nebs.conf`,'
                                ' but note that this host will likely be unavailable outside your local network.')

    def get_external_ip(self):
        return self._last_external_ip

    def get_local_ip(self):
        return self._last_local_ip

    # NOTE: Explicitly not including this.
    # It would eat an error that should be handled above.
    # def has_ip_changed(self):
    #     rd = self.update_external_ip()
    #     if rd.success:
    #         return rd.data
    #     else

    def refresh_external_ip(self):
        _log = get_mylog()
        rd = Error()
        if self.miniupnp_available():
            _log.debug('using miniupnp to get my IP')
            rd = self._upnp_refresh_external_ip()
            if rd.success:
                # make sure that our upnp state is updated
                self._using_upnp = True
        if not rd.success:
            # try to fallback to local
            inst = self._host_controller.get_instance()
            if inst.local_debug:
                _log.debug('Falling back to local debug mode')
                self._using_upnp = False
                rd = self._legacy_refresh_ip()
            else:
                # todo: handle disconnecting gracefully.
                # Need to still track updates, check for a network change occasionally,
                # and hope that we come back.
                # TODO - Also prevent us from trying to make new outgoing connections. <---- BIG
                rd = Error('Failed to connect to a upnp device. We should handle this gracefully.')
        _log.debug('refresh_external_ip->RD({},{})'.format(rd.success, rd.data))
        return rd

    def _upnp_refresh_external_ip(self):
        # () -> ResultAndData(True, bool:changed)
        # () -> ResultAndData(False, str:message)
        rd = Error()
        _log = get_mylog()
        old_ip = self._last_external_ip
        try:
            # todo: There's probably a way to enumerate all the upnp devices to make sure that if we have an IP already,
            #  and it's in the list of devices (but not first), we can stay on that device.
            ndevices = self._miniupnp.discover()
            if ndevices == 0:
                return Error('No UPnP devices found')

            self._miniupnp.selectigd()
            local_ipaddress = self._miniupnp.lanaddr
            external_ipaddress = self._miniupnp.externalipaddress()
            _log.debug('Woo we got an external ID!')
            self._last_external_ip = external_ipaddress
            self._last_local_ip = local_ipaddress
            _log.debug('old, now= {}, {}'.format(old_ip, external_ipaddress))
            rd = Success(external_ipaddress != old_ip)
        except Exception, e:
            rd = Error('Exception during miniupnpc operation: {}'.format(e.message))

        return rd

    def _legacy_refresh_ip(self):
        rd = Error()
        old_ip = self._last_external_ip
        ipv6s = self._get_ipv6_list()
        if len(ipv6s) > 0:
            if old_ip is not None and old_ip in ipv6s:
                rd = Success(False)
            else:
                self._last_external_ip = ipv6s[0]
                self._last_local_ip = ipv6s[0]
                rd = Success(self._last_external_ip != old_ip)
        return rd

    def create_port_mapping(self, bound_port):
        # type: (int) -> ResultAndData
        # type: (int) -> ResultAndData(True, int)
        # type: (int) -> ResultAndData(False, str)
        """

        :type bound_port: int
        """
        rd = Error()
        if self.using_upnp():
            rd = self._create_upnp_mapping(bound_port)
        else:
            # if it's local debu, we don't need to make a mapping
            rd = Success(bound_port)
        return rd

    def _create_upnp_mapping(self, bound_port):
        # type: (int) -> ResultAndData
        # type: (int) -> ResultAndData(True, int:external_port)
        # type: (int) -> ResultAndData(False, str:message)
        rd = Error('Unspecified error during NetworkController::create_upnp_mapping')
        try:
            external_port = bound_port
            # find a free port for the redirection
            r = self._miniupnp.getspecificportmapping(external_port, 'TCP')
            while r is not None and external_port < 65536:
                external_port += 1
                r = self._miniupnp.getspecificportmapping(external_port, 'TCP')

            b = self._miniupnp.addportmapping(external_port
                                              , 'TCP'
                                              , self._last_local_ip
                                              , bound_port
                                              , 'nebs port mapping {}'.format(external_port)
                                              , '')
            rd = Success(external_port)
        except Exception, e:
            rd = Error('Exception during miniupnpc operation: {}'.format(e.message))

        return rd

    def _all_ip6_list(self):
        ip_list = []
        for interface in interfaces():
            for link in ifaddresses(interface)[AF_INET6]:
                ip_list.append(link['addr'])
        # add ::1 to the end of the list so if we're in debug mode,
        #  its only a last resort.
        if '::1' in ip_list:
            ip_list.remove('::1')
            ip_list.append('::1')
        return ip_list

    def _get_ipv6_list(self):
        """Returns all suitable (public) ipv6 addresses for this host"""
        valid_ips = [ip for ip in self._all_ip6_list() if ('%' not in ip)]
        # if we're calling this then we can safely assume that we're in local debug mode.
        return valid_ips

    def miniupnp_available(self):
        # type: () -> bool
        """
        Returns True if we're using miniupnp for networking.
        We can safely assume that if the module wasn't loaded, and we successfully instantiated this object, that this
        object can use local debugging if this is false. (eg classic ip lookup)
        """
        return self._miniupnp is not None

    def using_upnp(self):
        # type: () -> bool
        return self.miniupnp_available() and self._using_upnp
