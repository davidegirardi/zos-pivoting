rm -f testing/fifo
mkfifo testing/fifo
python iowrapper.py cmd nc localhost 1234 < testing/fifo | bash -c 'echo previous_command_ended_Gcv9we7WYtGqRR7gEPRaw9ZquqZUZurj && bash -s' > testing/fifo 2>&1
rm -f testing/fifo
