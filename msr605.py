import time
import serial
import re
import codecs
import binascii

class MSRException(Exception):
    pass

class ReadError(MSRException):
    pass

class ReadWriteError(MSRException):
    pass

class CommandFormatError(MSRException):
    pass

class InvalidCommand(MSRException):
    pass

class InvalidCardSwipeForWrite(MSRException):
    pass

class SetError(MSRException):
    pass

class MSR605(serial.Serial):
    ESC_CHR = b'\x1B'
    FS_CHR = b'\x1C'

    TRACK_SENTINELS = (('%', '?'), (';', '?'), (';', '?'))

    def __init__(self, dev, test=True, timeout=10):
        super(MSR605, self).__init__(dev, 9600, 8, serial.PARITY_NONE, timeout=timeout)

        self.reset()
        if test:
            self.communication_test()
            self.ram_test()
            self.sensor_test()
            self.reset()

    def _read_status(self):
        exceptions = {
            b'\x31': ReadWriteError,
            b'\x32': CommandFormatError,
            b'\x34': InvalidCommand,
            b'\x39': InvalidCardSwipeForWrite,
            b'\x41': SetError,
        }
        self._expect(self.ESC_CHR)
        status = self.read(1)
        if status in exceptions:
            raise exceptions[status]()
        return status

    def _expect(self, data):
        read_data = self.read(len(data))
        if read_data != data:
            raise ReadError('Expected %s, got %s.' % (repr(data), repr(read_data)))

    def _read_until(self, end):
        data = b''
        while True:
            data += self.read(1)
            if data.endswith(end):
                return data

    def _send_command(self, command, *args):
        self.flushInput()
        self.flushOutput()
        self.write(self.ESC_CHR + command + b''.join(args))
        self.flush()

    def all_leds_off(self):
        self._send_command(b'\x81')

    def all_leds_on(self):
        self._send_command(b'\x82')

    def led_green_on(self):
        self._send_command(b'\x83')

    def led_yellow_on(self):
        self._send_command(b'\x84')

    def led_red_on(self):
        self._send_command(b'\x85')

    def sensor_test(self):
        self._send_command(b'\x86')
        if self.read(2) != (self.ESC_CHR + b'\x30'):
            raise MSRException('Sensor test failed.')

    def communication_test(self):
        self._send_command(b'\x65')
        if self.read(2) != (self.ESC_CHR + b'\x79'):
            raise MSRException('Communication test failed.')

    def ram_test(self):
        self._send_command(b'\x87')
        if self.read(2) != (self.ESC_CHR + b'\x30'):
            raise MSRException('RAM test failed.')

    def reset(self):
        self._send_command(b'\x61')

    def read_raw(self):
        def read_tracks():
            for tn in range(1, 4):
                self._expect(self.ESC_CHR + chr(tn).encode('ascii'))
                str_len = ord(self.read(1))
                yield self.read(str_len)
        self._send_command(b'\x6D')
        self._expect(self.ESC_CHR + b'\x73')
        tracks = tuple(read_tracks())
        self._expect(b'\x3F' + self.FS_CHR)
        self._read_status()
        return tracks

    def get_device_model(self):
        self._send_command(b'\x74')
        self._expect(self.ESC_CHR)
        model = self.read(1)
        self._expect('S')
        return model

    def get_firmware_version(self):
        self._send_command(b'\x76')
        self._expect(self.ESC_CHR)
        return self.read(8).decode("ascii")

    def set_hico(self):
        self._send_command(b'\x78')
        self._expect(self.ESC_CHR + b'\x30')

    def set_lowco(self):
        self._send_command(b'\x79')
        self._expect(self.ESC_CHR + b'\x30')

    def get_co_status(self):
        self._send_command(b'\x79')
        self._expect(self.ESC_CHR)
        return self.read(1)

    def set_leading_zero(self, t13, t2):
        self._send_command(b'\x7A', chr(t13).encode("ascii"), chr(t2).encode("ascii"))
        self._read_status()

    def check_leading_zero(self):
        self._send_command(b'\x6C')
        self._expect(self.ESC_CHR)
        t13 = ord(self.read(1))
        t2 = ord(self.read(1))
        return t13, t2

    def erase_card(self, t1=True, t2=True, t3=True):
        flags = (t1 and 1 or 0) | (t2 and 2 or 0) | (t3 and 4 or 0)
        self._send_command(b'\x63', chr(flags).encode("ascii"))
        self._read_status()

    def select_bpi(self, t1_density, t2_density, t3_density):
        self._send_command(b'\x62', t2_density and b'\xD2' or b'\x4B')
        self._read_status()
        self._send_command(b'\x62', t1_density and b'\xA1' or b'\xA0')
        self._read_status()
        self._send_command(b'\x62', t3_density and b'\xC1' or b'\xC0')
        self._read_status()

    def set_bpc(self, t1, t2, t3):
        self._send_command(b'\x6F', chr(t1).encode("ascii"), chr(t2).encode("ascii"), chr(t3).encode("ascii"))
        self._expect(self.ESC_CHR + b'\x30' + chr(t1).encode("ascii") + chr(t2).encode("ascii") + chr(t3).encode("ascii"))


    def _reverse_bits(self, s):
        nv = bytearray()
        value = bytearray(s)
        for b in value:
            reversed_byte = int('{:08b}'.format(b)[::-1], 2)
            nv.append(reversed_byte)
        return bytes(nv)

    def write_raw(self, *tracks):
        assert len(tracks) == 3
        raw_data_block = self.ESC_CHR + b'\x73'
        for tn, track in enumerate(tracks):
            raw_data_block += \
                self.ESC_CHR +\
                chr(tn + 1).encode("ascii") +\
                chr(len(track)).encode("ascii") +\
                self._reverse_bits(track)
        raw_data_block += b'\x3F' + self.FS_CHR
        self._send_command(b'\x6E', raw_data_block)
        self._read_status()

    def _set_iso_mode(self):
        self.select_bpi(True, False, True)
        self.set_bpc(7, 5, 5)
        self.set_leading_zero(61, 22)

    def write_iso(self, soft=False, *tracks):
        assert len(tracks) == 3
        if soft:
            return self._write_iso_soft(*tracks)
        return self._write_iso_native(*tracks)

    def _clean_iso_track_data(self, tracks):
        return [
            re.sub(r'^%s|%s$' % map(re.escape, sentinels), '', track)
            for sentinels, track in zip(self.TRACK_SENTINELS, tracks)
        ]

    def _write_iso_native(self, *tracks):
        tracks = self._clean_iso_track_data(tracks)
        data_block = self.ESC_CHR + b'\x73'
        data_block += ''.join(
            self.ESC_CHR + chr(tn + 1).encode("ascii") + track
            for tn, track in enumerate(tracks)
        )
        data_block += b'\x3F' + self.FS_CHR
        self._send_command(b'\x77', raw_data_block)
        self._read_status()

    def _write_iso_soft(self, *tracks):
        self._set_iso_mode()
        tracks = self._clean_iso_track_data(tracks)
        tracks = [
            (ss + track + es).encode('iso7811-2-track%d' % (tn + 1))
            for tn, ((ss, es), track) in enumerate(zip(self.TRACK_SENTINELS, tracks))
        ]
        return self.write_raw(*tracks)

    def read_iso(self, soft=False):
        if soft:
            return self._read_iso_soft()
        return self._read_iso_native()

    def _read_iso_native(self):
        self._send_command(b'\x72')
        self._expect(self.ESC_CHR + b'\x73')
        self._expect(self.ESC_CHR + b'\x01')
        track1 = self._read_until((b'\x1B\x02'))[:-2]
        track2 = self._read_until(b'\x1B\x03')[:-2]
        track3 = self._read_until(b'\x1C')[:-1]
        self._read_status()
        return track1, track2, track3

    def _read_iso_soft(self):
        self._set_iso_mode()
        return [
            track.decode('iso7811-2-track%d' % (tn + 1))
            for tn, track in enumerate(self.read_raw())
        ]


class ISO7811_2(codecs.Codec):
    TRACK1_CHARS = ' !"#$%&\'()*+`,./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_'
    TRACK23_CHARS = '0123456789:;<=>?'

    @classmethod
    def _reverse_bits(cls, value, nbits):
        return sum(
            1 << (nbits - 1 - i)
            for i in range(nbits)
            if (value >> i) & 1
        )

    @classmethod
    def _with_parity(cls, value, nbits):
        if sum(1 for i in range(nbits) if (value >> i) & 1) % 2 != 0:
            return value
        return value | (1 << (nbits - 1))

    @classmethod
    def _iso_encode_data(cls, data, mapping, nbits):
        def make_data():
            lrc = 0
            for v in map(mapping.index, data):
                lrc ^= v
                yield chr(cls._with_parity(v, nbits)).encode("ascii")
            yield chr(cls._with_parity(lrc, nbits)).encode("ascii")
        enc = b''.join(make_data())
        return enc, len(enc)

    @classmethod
    def _iso_decode_data(cls, data, mapping, nbits):
        dec = ''.join(
            mapping[cls._reverse_bits(ord(c) >> 1, nbits - 1)]
            for c in data
        )
        return dec, len(dec)

    @classmethod
    def encode_track1(cls, data):
        return cls._iso_encode_data(data, cls.TRACK1_CHARS, 7)

    @classmethod
    def encode_track23(cls, data):
        return cls._iso_encode_data(data, cls.TRACK23_CHARS, 5)

    @classmethod
    def decode_track1(cls, data):
        return cls._iso_decode_data(data, cls.TRACK1_CHARS, 7)

    @classmethod
    def decode_track23(cls, data):
        return cls._iso_decode_data(data, cls.TRACK23_CHARS, 5)

    @classmethod
    def codec_search(cls, name):
        return {
            'iso7811-2-track1': (cls.encode_track1, cls.decode_track1, None, None),
            'iso7811-2-track2': (cls.encode_track23, cls.decode_track23, None, None),
            'iso7811-2-track3': (cls.encode_track23, cls.decode_track23, None, None),
        }.get(name, None)
codecs.register(ISO7811_2.codec_search)
