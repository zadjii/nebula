import os, sys
import socket
from subprocess import Popen, PIPE
from time import sleep
# openssl genrsa 1024 > remote/key
# openssl req -new -x509 -nodes -sha1 -days 365 -key remote/key > remote/cert
from common_util import NEBULA_ROOT

# NOTE: You'll have to do this from *nix, unless you have openssl in your PATH
#   on windows. I didn't, so I just go WSL to run this command.

CSR = """
[ req ]
distinguished_name="remote.test.io"
prompt="no"

[ remote.test.io ]
C="US"
ST="Washington"
L="Seattle"
O="Nebula Remote Testing"
CN="remote.test.io"
"""


def main(argv):
    key_file = 'remote.ca.key'
    csr_file = 'remote.ca.csr'
    cert_file = 'remote.ca.chain.crt'

    instance_name = 'default' if (len(argv) < 2) else argv[1]

    key_file = 'instances/remote/{}/{}'.format(instance_name, key_file)
    csr_file = 'instances/remote/{}/{}'.format(instance_name, csr_file)
    cert_file = 'instances/remote/{}/{}'.format(instance_name, cert_file)

    key_file = os.path.join(NEBULA_ROOT, key_file)
    csr_file = os.path.join(NEBULA_ROOT, csr_file)
    cert_file = os.path.join(NEBULA_ROOT, cert_file)

    print('Writing key and cert to {}, {}'.format(key_file, cert_file))

    if not os.path.exists(os.path.dirname(key_file)):
        os.makedirs(os.path.dirname(key_file))
    with open(csr_file, mode='wb') as f:
        f.write(CSR)

    gen_key = Popen('openssl genrsa 1024', stdout=PIPE, shell=True)
    key, _ = gen_key.communicate()
    with open(key_file, mode='wb') as f:
        f.write(key)
    print('wrote key')

    gen_cert = Popen('openssl req -config {} -new -x509 -nodes -sha1 -days 365 -key {}'.format(csr_file, key_file), stdout=PIPE, shell=True)
    cert, _ = gen_cert.communicate()
    with open(cert_file, mode='wb') as f:
        f.write(cert)
    print('wrote cert')


if __name__ == '__main__':
    main(sys.argv)
