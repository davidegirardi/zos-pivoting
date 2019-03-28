# Testing
Testing data and scripts:

 * `EBCDIC` EBCDIC file
 * `synch_shell.sh` start an EBCDIC netcat bash shell and connects to localhost:1234
 * `async_shell.sh` same as above, but asynchronous (more like the default nc)
 * `mockup_shell.sh` same as `synch_shell.sh` but on port 3456 like the default mainframe reverse shell

### Example:
From a terminal run:
```
source update_pythonpath.sh
python reverseshellmanager.py cmd nc -l -p 1234
```
And on another one run:
```
bash testing/synch_shell.sh
```
Enjoy your local shell.
