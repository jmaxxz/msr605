#!/usr/bin/python
#!python
import msr605
import sys
import re
import binascii

def eprint(*args, **kwargs):
	print(*args, file=sys.stderr, **kwargs)

def main():
	try:
		reader = msr605.MSR605("/dev/tty.usbserial-130", test=False)
		print('swipe a card')
		while True:
			try:
				reader.reset()
				data = reader.read_raw()
				sdata = (data[0].rstrip(b'\x00'), data[1].rstrip(b'\x00'), data[2].rstrip(b'\x00'))
				print('------------------------------------------------------------')
				print('track 1: ' + binascii.hexlify(sdata[0]).decode('ascii'))
				print('track 2: ' + binascii.hexlify(sdata[1]).decode('ascii'))
				print('track 3: ' + binascii.hexlify(sdata[2]).decode('ascii'))
				print('------------------------------------------------------------')
			except msr605.ReadError:
				continue
			except msr605.ReadWriteError:
				eprint('ERROR: Could not read card')
	except KeyboardInterrupt:
		print("Shutdown requested...exiting")
	sys.exit(0)

if __name__ == "__main__":
    main()