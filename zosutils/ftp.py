import ftplib
import io
import string
import random


class FTP():
    DEFAULT_TEMPORARY_PATH = '/tmp'

    def __init__(self, hostname, username, password, port=21, passive=True):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port
        self.passive = passive
        self.ftp = ftplib.FTP()

    def connect(self):
        # Create the connection
        self.ftp.connect(self.hostname, self.port)
        self.ftp.login(self.username, self.password)
        if self.passive:
            self.ftp.set_pasv(True)

    def getds(self, dsname, outfile=''):
        if outfile == '':
            outfile = dsname
        # Get the dataset
        fp = open(outfile, 'wb')
        self.ftp.retrbinary('RETR %s' % dsname, fp.write)
        fp.close()

    def getdslist(self, outfile):
        fp = open(outfile, 'w')
        self.ftp.retrlines("LIST '*.*'", writeln + '\n')
        fp.close()

    def gen_random_filename(self, path=DEFAULT_TEMPORARY_PATH,
                            chars=string.ascii_lowercase + string.digits,
                            length=16):
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
        fp = io.BytesIO(bytestring)
        self.ftp.storlines('STOR ' + remotefile, fp)
        self.ftp.sendcmd('SITE CHMOD ' + permissions + ' ' + remotefile)
        fp.close()

    def run_jcl(self, jcl):
        self.ftp.sendcmd('site filetype=jes')
        jclfp = io.BytesIO(jcl.encode())
        self.ftp.storlines('STOR FTPJOB', jclfp)

    def close(self):
        self.ftp.close()
