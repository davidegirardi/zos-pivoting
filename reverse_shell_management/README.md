# Reverse Shell Management

 * `reverseshellmanager.py` extends `wrappingshell.py` to get a nice interactive shell with some post-exploitation commands
 * `wrappingshell.py` uses the stdio transcoder in zosutils to run a synchronous/asynchronous shell via `nc` or similar

## Usage
You can import the module and use the classes or call the scripts directly.

### Example
Open two terminals. Run this on the first one:
```
source update_pythonpath.sh
python reverse_shell_management/wrappingshell.py cmd nc -l -p 1234
```

Run this on the second one:
```
bash testing/synch_shell.sh
```

Enjoy a local shell.

