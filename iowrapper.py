nimport argparse
import sys
import subprocess
import threading

# Try loading EBCDIC from pip install
try:
    import ebcdic
except ImportError:
    pass


class IOWrapper():
    # Convert to EBCDIC from the current codec
    def to_ebcdic(self, asciibytes):
        return asciibytes.decode().encode(self.codepage)

    # Convert from EBCDIC
    def to_local(self, ebcdicbytes):
        return ebcdicbytes.decode(self.codepage)

    # Manage the stdin conversion for the subprocess
    def thread_in(self):
        while self.p.poll() is None:
            data = sys.stdin.buffer.readline()
            # Remove the newline character(s)
            data = data.splitlines()[0]
            self.p.stdin.buffer.write(self.to_ebcdic(data))
            # Add a newline in EBCDIC
            self.p.stdin.buffer.write(b'\x15')
            # Check if the process terminated before flushing
            if self.p.poll() is not None:
                break
            self.p.stdin.buffer.flush()

    # Manage the stdout from the subprocess
    def thread_out(self):
        while self.p.poll() is None:
            # Scan the input until the EBCDIC newline \x15 is found
            returndata = b''
            data = self.p.stdout.buffer.readline(1)
            while data and data != b'\x15':
                returndata += data
                data = self.p.stdout.buffer.readline(1)
            sys.stdout.write(self.to_local(returndata))
            # Print the local newline, Python takes care of \r, \n, \r\n
            sys.stdout.write('\n')
            sys.stdout.flush()

    def synchronous_thread_out(self, termination_string):
        input_buffer = b''
        output_block = ''
        current_line = ''
        while current_line != termination_string:
            if self.p.poll() is not None:
                break
            # Scan the input until the EBCDIC newline \x15 is found
            data = self.p.stdout.buffer.readline(1)
            while data and data != b'\x15':
                input_buffer += data
                data = self.p.stdout.buffer.readline(1)
            # Use rstrip to remove a trailing whitespaces and newlines
            # some platforms add it, some don't
            current_line = self.to_local(input_buffer).rstrip()
            if current_line != termination_string:
                # Also add the local newline, Python takes care of \r, \n, \r\n
                output_block += current_line + '\n'
            input_buffer = b''
        return output_block

    def writein(self, bytedata):
        self.stdin.buffer.write(bytedata)
        self.stdin.buffer.write(b'\x15')
        self.stdin.buffer.flush()

    def start_readout(self):
        t_out = threading.Thread(target=self.thread_out)
        t_out.start()

    def terminate(self):
        self.p.terminate()

    def poll(self):
        return self.p.poll()

    def __init__(self, command, transcoding_codepage='cp037', stdio=True):
        self.codepage = transcoding_codepage
        # Start the process to wrap
        self.p = subprocess.Popen(args=command,
                                  stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE,
                                  universal_newlines=True)
        # Access to stdin and stdout
        self.stdin = self.p.stdin
        self.stdout = self.p.stdout
        if stdio:
            # The stdin/stdout are managed by Python so we can do the transcoding
            t_in = threading.Thread(target=self.thread_in)
            t_out = threading.Thread(target=self.thread_out)
            t_in.start()
            t_out.start()


if __name__ == '__main__':
    # Argument parsing
    parser = argparse.ArgumentParser(
        description='Wraps a CLI program stdin/stdout in an encoding converter')
    parser.add_argument('-e', '--encoding', type=str, help='set the encoding (default cp037)',
                        default='cp037')
    subparsers = parser.add_subparsers(title='subcommand',
                                       description='external command to wrap',
                                       help='program to execute')
    command_parser = subparsers.add_parser('cmd', add_help=False)

    local_arguments, wrapped_command = parser.parse_known_args()
    wrapping_encoding = local_arguments.encoding

    cmd = IOWrapper(wrapped_command, wrapping_encoding)
