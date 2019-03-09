"""SSH key management and conversion"""
import subprocess
import tempfile
from string import Template

DEFAULT_KEYLENGTH = '1024'

SSHD_CONFIG_TEMPLATE = '''
# ssh-keygen -t rsa -f rsatest -b 2048 -N ''
Port ${SERVER_PORT}
ListenAddress ${LISTEN_ADDRESS}
HostKey ${RSA_SERVER_KEY}
AuthorizedKeysFile ${AUTHORIZED_KEYS_FILE}
AllowUsers ${USERNAME}
PasswordAuthentication no
# Change to yes if the AuthorizedKeysFile is in /tmp or something similar
StrictModes ${STRICT_MODES}
Subsystem   sftp    /usr/lib/ssh/sftp-server
'''

def gen_rsa_key(keylength=1024):
    """Generate RSA private and public keys"""
    optkeylength = keylength
    binopenssl = 'openssl'
    optgenrsa = 'genrsa'
    optrsa = 'rsa'
    optpubout = '-pubout'
    # RSA key generation
    proc = subprocess.run([binopenssl, optgenrsa, optkeylength],
                          capture_output=True)
    key = proc.stdout
    # Public key
    proc = subprocess.run([binopenssl, optrsa, optpubout],
                          input=key, capture_output=True)
    pubkey = proc.stdout
    return(key, pubkey)

def get_ecdsa_fingerprint(host, port):
    """Generate ECDSA host fingerprint"""
    # ssh-keyscan -t ecdsa -p $PORT $HOST
    binsshkeyscan = 'ssh-keyscan'
    optkeytype = '-t'
    keytype = 'ecdsa'
    optport = '-p'
    proc = subprocess.run([binsshkeyscan, optkeytype, keytype,
                           optport, port, host], capture_output=True)
    proc.check_returncode()
    return proc.stdout

def pub_rsa_to_openssh(key):
    """Convert RSA public key into OpenSSH format"""
    fp = tempfile.NamedTemporaryFile()
    fp.write(key)
    fp.read()
    fname = fp.name
    binsshkeygen = 'ssh-keygen'
    optimport = '-i'
    optfile = '-f'
    optformat = '-m'
    valpkcs8 = 'PKCS8'
    proc = subprocess.run([binsshkeygen, optimport, optfile,
                           fname, optformat, valpkcs8], capture_output=True)
    proc.check_returncode()
    opensshpubkey = proc.stdout
    fp.close()
    return opensshpubkey

def gen_sshd_config(port, ListenAddress, RSAHostKeyPath, AuthorizedKeysFile,
                    AllowUsers, StrictModes):
    """Generate a minimal sshd_config file"""
    config = Template(SSHD_CONFIG_TEMPLATE).substitute(
        SERVER_PORT=port,
        LISTEN_ADDRESS=ListenAddress,
        RSA_SERVER_KEY=RSAHostKeyPath,
        AUTHORIZED_KEYS_FILE=AuthorizedKeysFile,
        USERNAME=AllowUsers,
        STRICT_MODES=StrictModes,
        )
    return config
