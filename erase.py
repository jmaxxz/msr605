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
		reader = msr605.MSR605("/dev/tty.usbserial-130", test=False, timeout=120)
		reader.reset()
		reader.select_bpi(1,0,1)
		reader.set_hico()
		print('swipe card to erase')
		while True:
			try:
				reader.reset()
				data = reader.erase_card()
				print('card erased')
			except msr605.ReadError:
				print('failed to erase')
			except msr605.ReadWriteError:
				eprint('ERROR: Could not erase card')
	except KeyboardInterrupt:
		print("Shutdown requested...exiting")
	sys.exit(0)

if __name__ == "__main__":
	main()
