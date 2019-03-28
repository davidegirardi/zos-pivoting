# z/OS Utils

 * `ftp.py` talk FTP and uses the extra features of the FTP server in z/OS
 * `jcl.py` generate JCL cards
 * `stdiotranscoder.py` wrap the stdin/stdout of a command and performs transparent re-encoding (EBCDIC to UTF8 or other encodings supported by python). In other words: makes nc/ncat support EBCDIC and other character encoding systems

## Shell usage
`stdiotranscoder.py` works from the commandline too. For example:

```
$ python zosutils/stdiotranscoder.py cmd cat testing/EBCDIC
No one can read this! EBCDIC you!
```

