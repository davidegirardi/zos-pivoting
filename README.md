# zos-pivoting

Library set to get a secure reverse shell by submitting a JCL job via FTP on zOS.

The library contains:

 * `config.ini` a sample configuration file
 * `ftp2shell.py` the main script, it uses the config file and the next items
 * `wrappingshell.py` uses the IO wrapping in zosutils to get a nice interactive shell via netcat or other
 * `zosutils/iowrapper.py` wraps the stdin/stdout of a command and performs transparent re-encoding (EBCDIC to UTF8 or other encodings supported by python)
 * `sshutils/ssh_utils.py` generation and management of ssh keys and fingerprinting
 * `zosutils/zosftp.py` talks FTP and uses the extra features of the zOS FTP

## Design
I thins it was time to have real secure reverse shells. This project uses the new ssh stdin and stout redirection to get a fully interactive reverse shell on a mainframe.

This can be applied to other systems running ssh.

Do the cleanup by yourself, this is a design choice.

## Requirements
You have to create a user in your machine to get the reverse connection on your `cc_server` (see the config file).

It's up to you to manage what that user can do. The user does not need an interactive shell.

## Dependencies
As an optional dependendency for exotic encondings/codepages you can install the `ebcdic` package for python.

## Future Steps
* Automate the pivoting by parsin the output of netstat/NETSTAT and:
    - ssh -R
    - ssh -L
    - starting a local sshd
* Persistence via ssh keys
* Port to other systems

