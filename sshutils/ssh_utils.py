"""SSH key management and conversion"""
import subprocess
import tempfile


DEFAULT_KEYLENGTH = '1024'

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
