# zos-pivoting

Library set to get a secure reverse shell by submitting a JCL job via FTP on zOS.

The library contains:

 * `config.ini` a sample configuration file
 * `ftp2shell.py` the main script, it uses the config file and the next items
 * `iowrapper.py` wraps the stdin/stdout of a command and performs transparent re-encoding (EBCDIC to UTF8 or other encodings supported by python)
 * `wrappingshell.py` uses the IO wrapping to get a nice interactive shell via netcat or other
 * `ssh_utils.py` generation and management of ssh keys and fingerprinting
 * `zosftp.py` talks FTP and uses the extra features of the zOS FTP

## Requirements
You have to create an ssh user to get the reverse connection on your `cc_server` (see the config file).

It's up to you to manage what that user can do. The user does not need an interactive shell.

Do the cleanup by yourself, this is a design choice.

## Dependencies
As an optional dependendency for exotic encondings/codepages you can install the `ebcdic` package for python.

