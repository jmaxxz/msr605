#!/usr/bin/python
#!python
import msr605
import sys
import re
import binascii

def main():
	try:
		reader = msr605.MSR605("/dev/tty.usbserial", test=False, timeout=120)
		reader.reset()
		print 'Reader firmware: '+ reader.get_firmware_version()
		reader.select_bpi(1,0,1)
		reader.set_hico()
		data = []
		print 'swipe card to read'
		try:
			reader.reset()
			data = reader.read_raw()
			sdata = (data[0].rstrip('\x00'), data[1].rstrip('\x00'), data[2].rstrip('\x00'))
			print '------------------------------------------------------------'
			print 'track 1: ' + binascii.hexlify(sdata[0])
			print 'track 2: ' + binascii.hexlify(sdata[1])
			print 'track 3: ' + binascii.hexlify(sdata[2])
			print '------------------------------------------------------------'
			print 'swipe a card to write'
			reader.reset()
			reader.select_bpi(1,0,1)
			reader.set_hico()
			reader.write_raw(*sdata)
			print 'Done!'
		except msr605.ReadError:
			print >> sys.stderr, 'ERROR: Could not read card'
		except msr605.ReadWriteError:
			print >> sys.stderr, 'ERROR: Could not write card'
	except KeyboardInterrupt:
		reader.close()
		print "Shutdown requested...exiting"
	reader.close()
	sys.exit(0)

if __name__ == "__main__":
	main()
