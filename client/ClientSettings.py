import json
import os, sys
from common_util import *


class ClientSettings(object):

    def __init__(self):
        self.default_remote_address = 'localhost'
        self.default_remote_port = 12345
        self.cache_user_sids = True
        # This needs to be:
        # {
        #   remotes:[
        #       {
        #           remote_address: str,
        #           user_sids: {
        #               foo:<sid>
        #               ,bar:<sid>
        #           }
        #       }
        #   ]
        # }
        self.remotes = []
        self.default_username = None
        self.default_uname = None
        self.default_cname = None

    def _get_filename(self):
        return 'nebula.settings'

    def _read_settings(self):
        rd = Error()
        if not os.path.exists(self._get_filename()):
            return Success({})
        try:
            with open(self._get_filename()) as f:
                blob = f.readlines()
                rd = Success(blob)
        except IOError, e:
            rd = Error(e.message)

        if rd.success:
            try:
                obj = json.loads(rd.data)
                rd = Success(obj)
            except Exception, e:
                msg = 'Error parsing settings'
                print(msg)
                rd = Error(e)
        return rd

    def load_settings(self):
        rd = self._read_settings()
        if not rd.success:
            return rd

        settings = rd.data
        if 'default_remote_address' in settings:
            self.default_remote_address = settings['default_remote_address']

        if 'default_remote_port' in settings:
            self.default_remote_port = settings['default_remote_port']

        if 'cache_user_sids' in settings:
            self.cache_user_sids = settings['cache_user_sids']

        if 'remotes' in settings:
            self.remotes = settings['remotes']

        if 'default_uname' in settings:
            self.default_uname = settings['default_uname']

        if 'default_cname' in settings:
            self.default_cname = settings['default_cname']
        return Success()

    def _get_remote_settings(self, remote_addr):
        remote = None
        for rem in self.remotes:
            if rem['remote_address'] == remote_addr:
                remote = rem
                break
        return remote

    def cache_sid(self, remote_addr, username, sid):
        if not self.cache_user_sids:
            print('asked to cache SID, but cache_user_sids is False')
        remote = self._get_remote_settings(remote_addr)
        if remote is not None:
            if 'user_sids' not in remote:
                remote['user_sids'] = {}
            remote['user_sids'][username] = sid

    def get_sid(self, remote_addr, username):
        sid = None
        remote = self._get_remote_settings(remote_addr)
        if remote is not None:
            if 'user_sids' not in remote:
                remote['user_sids'] = {}
            sid = remote['user_sids'][username]

        print('sid for ({},{})={}'.format(remote_addr, username, sid))

        return sid








