from OpenSSL import SSL
from OpenSSL import crypto
from twisted.internet.ssl import ContextFactory

from host.models.Remote import Remote


class RemoteSSLContextFactory(ContextFactory):
    """
    A factory for creating SSL contexts based on information in a
    host.models.Remote object.
    """
    _context = None

    def __init__(self
                 # , remote=None
                 , host_instance=None
                 , sslmethod=SSL.TLSv1_2_METHOD
                 , _contextFactory=SSL.Context):
        # self.remote = remote
        self.host_instance = host_instance
        self.sslmethod = sslmethod
        self._contextFactory = _contextFactory

        # Create a context object right now.  This is to force validation of
        # the given parameters so that errors are detected earlier rather
        # than later.
        self.cacheContext()

    def cacheContext(self):
        ctx = self._contextFactory(self.sslmethod)
        # Disallow SSLv2!  It's insecure!  SSLv3 has been around since
        # 1996.  It's time to move on.
        ctx.set_options(SSL.OP_NO_SSLv2)

        # fixme isnt this JANKY
        remote_model = self.host_instance.get_db().session.query(Remote).get(1)
        with open(self.host_instance.cert_file, mode='w') as f:
            f.write(remote_model.certificate)
        with open(self.host_instance.key_file, mode='w') as f:
            f.write(remote_model.key)

        ctx.use_certificate_chain_file(self.host_instance.cert_file)
        ctx.use_privatekey_file(self.host_instance.key_file)

        # cert_chain = crypto.load_certificate(crypto.FILETYPE_PEM, self.remote.certificate)
        # key = crypto.load_privatekey(crypto.FILETYPE_PEM, self.remote.key)
        # ctx.use_certificate(cert_chain)
        # ctx.use_privatekey(key)

        self._context = ctx

    def __getstate__(self):
        d = self.__dict__.copy()
        del d['_context']
        return d

    def __setstate__(self, state):
        self.__dict__ = state

    def getContext(self):
        """
        Return an SSL context.
        """
        return self._context
