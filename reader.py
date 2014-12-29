#!/usr/bin/python
#!python
import msr605
import sys
import re


def main():
    try:
		reader = msr605.MSR605("/dev/tty.usbserial", test=False)
		reader.reset()
		print reader.get_firmware_version()
		print 'swipe a card'
		while True:
			try:
				data = reader.read_iso()

				formatB = re.match(r"%B(?P<card>[0-9]{1,19})\^(?P<name>.{2,26})\^(?P<year>[0-9]{2})(?P<month>[0-9]{2})(?P<serv>[0-9]{3})(?P<exdata>.*)\?", data[0])
				if formatB:
					print '------------------------------------------------------------'
					print 'Format     : B'
					print 'Name       : ' + formatB.group('name')
					print 'Primary #  : ' + formatB.group('card')
					print 'Exp month  : ' + formatB.group('month')
					print 'Exp year   : ' + formatB.group('year')
					print 'Serv code: : ' + formatB.group('serv')
					print 'Extra data : ' + formatB.group('exdata')
					print '------------------------------------------------------------'
				else:
					print data
			except msr605.ReadError:
				continue
			except msr605.ReadWriteError:
				print >> sys.stderr, 'ERROR: Could not read card'
    except KeyboardInterrupt:
        print "Shutdown requested...exiting"
    sys.exit(0)

if __name__ == "__main__":
    main()
