#!/usr/bin/python
#!python
import msr605
import sys
import re

def eprint(*args, **kwargs):
	print(*args, file=sys.stderr, **kwargs)

def main():
	try:
		reader = msr605.MSR605("/dev/tty.usbserial", test=False)
		reader.reset()
		print(reader.get_firmware_version())
		print('swipe a card')
		while True:
			try:
				data = reader.read_raw()

				formatB = re.match(r"%B(?P<card>[0-9]{1,19})\^(?P<name>.{2,26})\^(?P<year>[0-9]{2})(?P<month>[0-9]{2})(?P<serv>[0-9]{3})(?P<exdata>.*)\?", data[0])
				if formatB:
					print('------------------------------------------------------------')
					print('Format     : B')
					print('Name       : ' + formatB.group('name'))
					print('Primary #  : ' + formatB.group('card'))
					print('Exp month  : ' + formatB.group('month'))
					print('Exp year   : ' + formatB.group('year'))
					print('Serv code: : ' + formatB.group('serv'))
					print('Extra data : ' + formatB.group('exdata'))
					print('------------------------------------------------------------')
				else:
					print(data)
			except msr605.ReadError:
				continue
			except msr605.ReadWriteError:
				eprint('ERROR: Could not read card')
	except KeyboardInterrupt:
		print("Shutdown requested...exiting")
	sys.exit(0)

if __name__ == "__main__":
	main()

# First digit
#
# 1: International interchange OK
# 2: International interchange, use IC (chip) where feasible
# 5: National interchange only except under bilateral agreement
# 6: National interchange only except under bilateral agreement, use IC (chip) where feasible
# 7: No interchange except under bilateral agreement (closed loop)
# 9: Test

# Second digit
# 0: Normal
# 2: Contact issuer via online means
# 4: Contact issuer via online means except under bilateral agreement

# Third digit
# 0: No restrictions, PIN required
# 1: No restrictions
# 2: Goods and services only (no cash)
# 3: ATM only, PIN required
# 4: Cash only
# 5: Goods and services only (no cash), PIN required
# 6: No restrictions, use PIN where feasible
# 7: Goods and services only (no cash), use PIN where feasible