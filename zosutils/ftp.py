"""FTP library exploiting the peculiar z/OS features"""
import ftplib
import io
import string
import random


class FTP():
    """Object to interact with the mainframe FTP capabilities"""
    DEFAULT_TEMPORARY_PATH = '/tmp'

    def __init__(self, hostname, username, password, port=21, passive=True):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port
        self.passive = passive
        self.ftp = ftplib.FTP()

    def connect(self):
        """Establish a connection"""
        # Create the connection
        self.ftp.connect(self.hostname, self.port)
        self.ftp.login(self.username, self.password)
        if self.passive:
            self.ftp.set_pasv(True)

    def gen_random_filename(self, path=DEFAULT_TEMPORARY_PATH,
                            chars=string.ascii_lowercase + string.digits,
                            length=16):
        """Generate a random filename and check if the file already exists"""
        filename = path + '/' + ''.join(random.choice(chars) for x in range(length))
        found_files = []
        while True:
            try:
                self.ftp.retrlines('LIST ' + filename,
                                   callback=found_files.append)
            except ftplib.error_perm:
                break
        return filename

    def upload_string_as_file(self, bytestring, remotefile, permissions='600'):
        """Upload a string into a file"""
        fp = io.BytesIO(bytestring)
        self.ftp.storlines('STOR ' + remotefile, fp)
        self.ftp.sendcmd('SITE CHMOD ' + permissions + ' ' + remotefile)
        fp.close()

    def run_jcl(self, jcl):
        """Run a string as a JCL batch"""
        self.ftp.sendcmd('site filetype=jes')
        jclfp = io.BytesIO(jcl.encode())
        self.ftp.storlines('STOR FTPJOB', jclfp)

    def close(self):
        """Close the connection"""
        self.ftp.close()
