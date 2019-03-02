import argparse
import sys
from cmd import Cmd
from zosutils import IOWrapper


class WrappingShell(Cmd):
    TERMINATOR_STRING = 'previous_command_ended_Gcv9we7WYtGqRR7gEPRaw9ZquqZUZurj'
    COMMAND_TERMINATOR = 'echo ' + TERMINATOR_STRING + '\n'

    DEFAULT_PROMPT = '> '

    def __init__(self, cmdline, codepage, name='shell', sync_stdout=False):
        Cmd.__init__(self)
        self.name = name
        self.prompt = self.name + self.DEFAULT_PROMPT
        self.wrapper = IOWrapper(cmdline, codepage, stdio=False)
        self.stop = False
        if sync_stdout:
            self.termination_command = self.COMMAND_TERMINATOR
            self.termination_string = self.TERMINATOR_STRING
            self.synchronous_commands = True
        else:
            self.termination_command = ''
            self.synchronous_commands = False
            self.wrapper.start_readout()

    def preloop(self):
        # Set up command completion
        Cmd.preloop(self)
        if self.synchronous_commands:
            print('Waiting for ' + self.name + ' activation')
            self.wrapper.synchronous_thread_out(self.termination_string)

    def encode_and_send(self, args):
        data = args.encode()
        self.wrapper.writein(self.wrapper.to_ebcdic(data))
        if self.synchronous_commands:
            sys.stdout.write(self.wrapper.synchronous_thread_out(self.termination_string))

    def prepare_command(self, args):
        # Detect if we got a command to run in background
        if args.split(' ')[-1] == '&' or args[-1] == '&':
            sync_character = ''
        else:
            sync_character = ';'
        return args + sync_character + self.termination_command

    def default(self, args):
        self.poll_subprocess()
        command = self.prepare_command(args)
        self.encode_and_send(command)

    def do_tsocmd(self, args):
        real_args = 'tsocmd ' + args
        self.default(real_args)

    def get_name(self):
        return self.name

    def emptyline(self):
        self.poll_subprocess()

    def postcmd(self, stop, args):
        return self.stop

    def terminate(self):
        self.wrapper.terminate()
        self.stop = True

    def do_exit(self, args=None):
        """Quits the shell"""
        confirm = input("This will terminate the connection to " +
                        self.get_name() + ", are you sure? (y/N) ")
        try:
            if confirm[0].upper() == 'Y':
                self.terminate()
        except IndexError:
            return
        else:
            return

    def do_EOF(self, args=None):
        """Quits the shell"""
        self.do_exit()

    def poll_subprocess(self):
        if self.wrapper.poll() is not None:
            print('Subprocess terminated, exiting')
            self.terminate()


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
        shell = WrappingShell(wrapped_command, wrapping_encoding,
                              sync_stdout=local_arguments.asyncio)
    else:
        shell = WrappingShell(wrapped_command, wrapping_encoding,
                              name=local_arguments.name,
                              sync_stdout=local_arguments.asyncio)
    shell.cmdloop()
