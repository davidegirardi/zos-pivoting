rm -f testing/fifo
mkfifo testing/fifo
python zosutils/stdiotranscoder.py cmd nc localhost 1234 < testing/fifo | bash -s > testing/fifo 2>&1
rm -f testing/fifo
