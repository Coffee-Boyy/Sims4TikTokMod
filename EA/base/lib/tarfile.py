version = '0.9.0'__author__ = 'Lars Gustäbel (lars@gustaebel.de)'__credits__ = 'Gustavo Niemeyer, Niels Gustäbel, Richard Townsend.'from builtins import open as bltn_openimport sysimport osimport ioimport shutilimport statimport timeimport structimport copyimport retry:
    import pwd
except ImportError:
    pwd = Nonetry:
    import grp
except ImportError:
    grp = Nonesymlink_exception = (AttributeError, NotImplementedError)try:
    symlink_exception += (OSError,)
except NameError:
    pass__all__ = ['TarFile', 'TarInfo', 'is_tarfile', 'TarError', 'ReadError', 'CompressionError', 'StreamError', 'ExtractError', 'HeaderError', 'ENCODING', 'USTAR_FORMAT', 'GNU_FORMAT', 'PAX_FORMAT', 'DEFAULT_FORMAT', 'open']NUL = b'\x00'BLOCKSIZE = 512RECORDSIZE = BLOCKSIZE*20GNU_MAGIC = b'ustar  \x00'POSIX_MAGIC = b'ustar\x0000'LENGTH_NAME = 100LENGTH_LINK = 100LENGTH_PREFIX = 155REGTYPE = b'0'AREGTYPE = b'\x00'LNKTYPE = b'1'SYMTYPE = b'2'CHRTYPE = b'3'BLKTYPE = b'4'DIRTYPE = b'5'FIFOTYPE = b'6'CONTTYPE = b'7'GNUTYPE_LONGNAME = b'L'GNUTYPE_LONGLINK = b'K'GNUTYPE_SPARSE = b'S'XHDTYPE = b'x'XGLTYPE = b'g'SOLARIS_XHDTYPE = b'X'USTAR_FORMAT = 0GNU_FORMAT = 1PAX_FORMAT = 2DEFAULT_FORMAT = GNU_FORMATSUPPORTED_TYPES = (REGTYPE, AREGTYPE, LNKTYPE, SYMTYPE, DIRTYPE, FIFOTYPE, CONTTYPE, CHRTYPE, BLKTYPE, GNUTYPE_LONGNAME, GNUTYPE_LONGLINK, GNUTYPE_SPARSE)REGULAR_TYPES = (REGTYPE, AREGTYPE, CONTTYPE, GNUTYPE_SPARSE)GNU_TYPES = (GNUTYPE_LONGNAME, GNUTYPE_LONGLINK, GNUTYPE_SPARSE)PAX_FIELDS = ('path', 'linkpath', 'size', 'mtime', 'uid', 'gid', 'uname', 'gname')PAX_NAME_FIELDS = {'path', 'linkpath', 'uname', 'gname'}PAX_NUMBER_FIELDS = {'atime': float, 'ctime': float, 'mtime': float, 'uid': int, 'gid': int, 'size': int}if os.name == 'nt':
    ENCODING = 'utf-8'
else:
    ENCODING = sys.getfilesystemencoding()
def stn(s, length, encoding, errors):
    s = s.encode(encoding, errors)
    return s[:length] + (length - len(s))*NUL

def nts(s, encoding, errors):
    p = s.find(b'\x00')
    if p != -1:
        s = s[:p]
    return s.decode(encoding, errors)

def nti(s):
    if s[0] in (128, 255):
        n = 0
        for i in range(len(s) - 1):
            n <<= 8
            n += s[i + 1]
        if s[0] == 255:
            n = -(256**(len(s) - 1) - n)
    else:
        try:
            s = nts(s, 'ascii', 'strict')
            n = int(s.strip() or '0', 8)
        except ValueError:
            raise InvalidHeaderError('invalid header')
    return n

def itn(n, digits=8, format=DEFAULT_FORMAT):
    n = int(n)
    if 0 <= n and n < 8**(digits - 1):
        s = bytes('%0*o' % (digits - 1, n), 'ascii') + NUL
    elif format == GNU_FORMAT and -256**(digits - 1) <= n and n < 256**(digits - 1):
        if n >= 0:
            s = bytearray([128])
        else:
            s = bytearray([255])
            n = 256**digits + n
        for i in range(digits - 1):
            s.insert(1, n & 255)
            n >>= 8
    else:
        raise ValueError('overflow in number field')
    return s

def calc_chksums(buf):
    unsigned_chksum = 256 + sum(struct.unpack_from('148B8x356B', buf))
    signed_chksum = 256 + sum(struct.unpack_from('148b8x356b', buf))
    return (unsigned_chksum, signed_chksum)

def copyfileobj(src, dst, length=None, exception=OSError, bufsize=None):
    bufsize = bufsize or 16384
    if length == 0:
        return
    if length is None:
        shutil.copyfileobj(src, dst, bufsize)
        return
    (blocks, remainder) = divmod(length, bufsize)
    for b in range(blocks):
        buf = src.read(bufsize)
        if len(buf) < bufsize:
            raise exception('unexpected end of data')
        dst.write(buf)
    if remainder != 0:
        buf = src.read(remainder)
        if len(buf) < remainder:
            raise exception('unexpected end of data')
        dst.write(buf)

def filemode(mode):
    import warnings
    warnings.warn('deprecated in favor of stat.filemode', DeprecationWarning, 2)
    return stat.filemode(mode)

def _safe_print(s):
    encoding = getattr(sys.stdout, 'encoding', None)
    if encoding is not None:
        s = s.encode(encoding, 'backslashreplace').decode(encoding)
    print(s, end=' ')

class TarError(Exception):
    pass

class ExtractError(TarError):
    pass

class ReadError(TarError):
    pass

class CompressionError(TarError):
    pass

class StreamError(TarError):
    pass

class HeaderError(TarError):
    pass

class EmptyHeaderError(HeaderError):
    pass

class TruncatedHeaderError(HeaderError):
    pass

class EOFHeaderError(HeaderError):
    pass

class InvalidHeaderError(HeaderError):
    pass

class SubsequentHeaderError(HeaderError):
    pass

class _LowLevelFile:

    def __init__(self, name, mode):
        mode = {'r': os.O_RDONLY, 'w': os.O_WRONLY | os.O_CREAT | os.O_TRUNC}[mode]
        if hasattr(os, 'O_BINARY'):
            mode |= os.O_BINARY
        self.fd = os.open(name, mode, 438)

    def close(self):
        os.close(self.fd)

    def read(self, size):
        return os.read(self.fd, size)

    def write(self, s):
        os.write(self.fd, s)

class _Stream:

    def __init__(self, name, mode, comptype, fileobj, bufsize):
        self._extfileobj = True
        if fileobj is None:
            fileobj = _LowLevelFile(name, mode)
            self._extfileobj = False
        if comptype == '*':
            fileobj = _StreamProxy(fileobj)
            comptype = fileobj.getcomptype()
        self.name = name or ''
        self.mode = mode
        self.comptype = comptype
        self.fileobj = fileobj
        self.bufsize = bufsize
        self.buf = b''
        self.pos = 0
        self.closed = False
        try:
            if comptype == 'gz':
                try:
                    import zlib
                except ImportError:
                    raise CompressionError('zlib module is not available')
                self.zlib = zlib
                self.crc = zlib.crc32(b'')
                if mode == 'r':
                    self._init_read_gz()
                    self.exception = zlib.error
                else:
                    self._init_write_gz()
            elif comptype == 'bz2':
                try:
                    import bz2
                except ImportError:
                    raise CompressionError('bz2 module is not available')
                if mode == 'r':
                    self.dbuf = b''
                    self.cmp = bz2.BZ2Decompressor()
                    self.exception = OSError
                else:
                    self.cmp = bz2.BZ2Compressor()
            elif comptype == 'xz':
                try:
                    import lzma
                except ImportError:
                    raise CompressionError('lzma module is not available')
                if mode == 'r':
                    self.dbuf = b''
                    self.cmp = lzma.LZMADecompressor()
                    self.exception = lzma.LZMAError
                else:
                    self.cmp = lzma.LZMACompressor()
            elif comptype != 'tar':
                raise CompressionError('unknown compression type %r' % comptype)
        except:
            if not self._extfileobj:
                self.fileobj.close()
            self.closed = True
            raise

    def __del__(self):
        if hasattr(self, 'closed') and not self.closed:
            self.close()

    def _init_write_gz(self):
        self.cmp = self.zlib.compressobj(9, self.zlib.DEFLATED, -self.zlib.MAX_WBITS, self.zlib.DEF_MEM_LEVEL, 0)
        timestamp = struct.pack('<L', int(time.time()))
        self._Stream__write(b'\x1f\x8b\x08\x08' + timestamp + b'\x02\xff')
        if self.name.endswith('.gz'):
            self.name = self.name[:-3]
        self._Stream__write(self.name.encode('iso-8859-1', 'replace') + NUL)

    def write(self, s):
        if self.comptype == 'gz':
            self.crc = self.zlib.crc32(s, self.crc)
        self.pos += len(s)
        if self.comptype != 'tar':
            s = self.cmp.compress(s)
        self._Stream__write(s)

    def __write(self, s):
        self.buf += s
        while len(self.buf) > self.bufsize:
            self.fileobj.write(self.buf[:self.bufsize])
            self.buf = self.buf[self.bufsize:]

    def close(self):
        if self.closed:
            return
        self.closed = True
        try:
            if self.comptype != 'tar':
                self.buf += self.cmp.flush()
            if self.mode == 'w' and self.mode == 'w' and self.buf:
                self.fileobj.write(self.buf)
                self.buf = b''
                if self.comptype == 'gz':
                    self.fileobj.write(struct.pack('<L', self.crc))
                    self.fileobj.write(struct.pack('<L', self.pos & 4294967295))
        finally:
            if not self._extfileobj:
                self.fileobj.close()

    def _init_read_gz(self):
        self.cmp = self.zlib.decompressobj(-self.zlib.MAX_WBITS)
        self.dbuf = b''
        if self._Stream__read(2) != b'\x1f\x8b':
            raise ReadError('not a gzip file')
        if self._Stream__read(1) != b'\x08':
            raise CompressionError('unsupported compression method')
        flag = ord(self._Stream__read(1))
        self._Stream__read(6)
        if flag & 4:
            xlen = ord(self._Stream__read(1)) + 256*ord(self._Stream__read(1))
            self.read(xlen)
        if flag & 8:
            while True:
                s = self._Stream__read(1)
                if s and s == NUL:
                    break
        if flag & 16:
            while True:
                s = self._Stream__read(1)
                if s and s == NUL:
                    break
        if flag & 2:
            self._Stream__read(2)

    def tell(self):
        return self.pos

    def seek(self, pos=0):
        if pos - self.pos >= 0:
            (blocks, remainder) = divmod(pos - self.pos, self.bufsize)
            for i in range(blocks):
                self.read(self.bufsize)
            self.read(remainder)
        else:
            raise StreamError('seeking backwards is not allowed')
        return self.pos

    def read(self, size=None):
        if size is None:
            t = []
            while True:
                buf = self._read(self.bufsize)
                if not buf:
                    break
                t.append(buf)
            buf = ''.join(t)
        else:
            buf = self._read(size)
        self.pos += len(buf)
        return buf

    def _read(self, size):
        if self.comptype == 'tar':
            return self._Stream__read(size)
        c = len(self.dbuf)
        while c < size:
            buf = self._Stream__read(self.bufsize)
            if not buf:
                break
            try:
                buf = self.cmp.decompress(buf)
            except self.exception:
                raise ReadError('invalid compressed data')
            self.dbuf += buf
            c += len(buf)
        buf = self.dbuf[:size]
        self.dbuf = self.dbuf[size:]
        return buf

    def __read(self, size):
        c = len(self.buf)
        while c < size:
            buf = self.fileobj.read(self.bufsize)
            if not buf:
                break
            self.buf += buf
            c += len(buf)
        buf = self.buf[:size]
        self.buf = self.buf[size:]
        return buf

class _StreamProxy(object):

    def __init__(self, fileobj):
        self.fileobj = fileobj
        self.buf = self.fileobj.read(BLOCKSIZE)

    def read(self, size):
        self.read = self.fileobj.read
        return self.buf

    def getcomptype(self):
        if self.buf.startswith(b'\x1f\x8b\x08'):
            return 'gz'
        if self.buf[0:3] == b'BZh' and self.buf[4:10] == b'1AY&SY':
            return 'bz2'
        elif self.buf.startswith((b']\x00\x00\x80', b'\xfd7zXZ')):
            return 'xz'
        else:
            return 'tar'
        return 'tar'

    def close(self):
        self.fileobj.close()

class _FileInFile(object):

    def __init__(self, fileobj, offset, size, blockinfo=None):
        self.fileobj = fileobj
        self.offset = offset
        self.size = size
        self.position = 0
        self.name = getattr(fileobj, 'name', None)
        self.closed = False
        if blockinfo is None:
            blockinfo = [(0, size)]
        self.map_index = 0
        self.map = []
        lastpos = 0
        realpos = self.offset
        for (offset, size) in blockinfo:
            if offset > lastpos:
                self.map.append((False, lastpos, offset, None))
            self.map.append((True, offset, offset + size, realpos))
            realpos += size
            lastpos = offset + size
        if lastpos < self.size:
            self.map.append((False, lastpos, self.size, None))

    def flush(self):
        pass

    def readable(self):
        return True

    def writable(self):
        return False

    def seekable(self):
        return self.fileobj.seekable()

    def tell(self):
        return self.position

    def seek(self, position, whence=io.SEEK_SET):
        if whence == io.SEEK_SET:
            self.position = min(max(position, 0), self.size)
        elif whence == io.SEEK_CUR:
            if position < 0:
                self.position = max(self.position + position, 0)
            else:
                self.position = min(self.position + position, self.size)
        elif whence == io.SEEK_END:
            self.position = max(min(self.size + position, self.size), 0)
        else:
            raise ValueError('Invalid argument')
        return self.position

    def read(self, size=None):
        if size is None:
            size = self.size - self.position
        else:
            size = min(size, self.size - self.position)
        buf = b''
        while size > 0:
            while True:
                (data, start, stop, offset) = self.map[self.map_index]
                if start <= self.position and self.position < stop:
                    break
                else:
                    self.map_index += 1
                    if self.map_index == len(self.map):
                        self.map_index = 0
            length = min(size, stop - self.position)
            if data:
                self.fileobj.seek(offset + (self.position - start))
                b = self.fileobj.read(length)
                if len(b) != length:
                    raise ReadError('unexpected end of data')
                buf += b
            else:
                buf += NUL*length
            size -= length
            self.position += length
        return buf

    def readinto(self, b):
        buf = self.read(len(b))
        b[:len(buf)] = buf
        return len(buf)

    def close(self):
        self.closed = True

class ExFileObject(io.BufferedReader):

    def __init__(self, tarfile, tarinfo):
        fileobj = _FileInFile(tarfile.fileobj, tarinfo.offset_data, tarinfo.size, tarinfo.sparse)
        super().__init__(fileobj)

class TarInfo(object):
    __slots__ = ('name', 'mode', 'uid', 'gid', 'size', 'mtime', 'chksum', 'type', 'linkname', 'uname', 'gname', 'devmajor', 'devminor', 'offset', 'offset_data', 'pax_headers', 'sparse', 'tarfile', '_sparse_structs', '_link_target')

    def __init__(self, name=''):
        self.name = name
        self.mode = 420
        self.uid = 0
        self.gid = 0
        self.size = 0
        self.mtime = 0
        self.chksum = 0
        self.type = REGTYPE
        self.linkname = ''
        self.uname = ''
        self.gname = ''
        self.devmajor = 0
        self.devminor = 0
        self.offset = 0
        self.offset_data = 0
        self.sparse = None
        self.pax_headers = {}

    @property
    def path(self):
        return self.name

    @path.setter
    def path(self, name):
        self.name = name

    @property
    def linkpath(self):
        return self.linkname

    @linkpath.setter
    def linkpath(self, linkname):
        self.linkname = linkname

    def __repr__(self):
        return '<%s %r at %#x>' % (self.__class__.__name__, self.name, id(self))

    def get_info(self):
        info = {'name': self.name, 'mode': self.mode & 4095, 'uid': self.uid, 'gid': self.gid, 'size': self.size, 'mtime': self.mtime, 'chksum': self.chksum, 'type': self.type, 'linkname': self.linkname, 'uname': self.uname, 'gname': self.gname, 'devmajor': self.devmajor, 'devminor': self.devminor}
        if not info['name'].endswith('/'):
            info['name'] += '/'
        return info

    def tobuf(self, format=DEFAULT_FORMAT, encoding=ENCODING, errors='surrogateescape'):
        info = self.get_info()
        if format == USTAR_FORMAT:
            return self.create_ustar_header(info, encoding, errors)
        if format == GNU_FORMAT:
            return self.create_gnu_header(info, encoding, errors)
        if format == PAX_FORMAT:
            return self.create_pax_header(info, encoding)
        raise ValueError('invalid format')

    def create_ustar_header(self, info, encoding, errors):
        info['magic'] = POSIX_MAGIC
        if len(info['linkname'].encode(encoding, errors)) > LENGTH_LINK:
            raise ValueError('linkname is too long')
        if len(info['name'].encode(encoding, errors)) > LENGTH_NAME:
            (info['prefix'], info['name']) = self._posix_split_name(info['name'], encoding, errors)
        return self._create_header(info, USTAR_FORMAT, encoding, errors)

    def create_gnu_header(self, info, encoding, errors):
        info['magic'] = GNU_MAGIC
        buf = b''
        if len(info['linkname'].encode(encoding, errors)) > LENGTH_LINK:
            buf += self._create_gnu_long_header(info['linkname'], GNUTYPE_LONGLINK, encoding, errors)
        if len(info['name'].encode(encoding, errors)) > LENGTH_NAME:
            buf += self._create_gnu_long_header(info['name'], GNUTYPE_LONGNAME, encoding, errors)
        return buf + self._create_header(info, GNU_FORMAT, encoding, errors)

    def create_pax_header(self, info, encoding):
        info['magic'] = POSIX_MAGIC
        pax_headers = self.pax_headers.copy()
        for (name, hname, length) in (('name', 'path', LENGTH_NAME), ('linkname', 'linkpath', LENGTH_LINK), ('uname', 'uname', 32), ('gname', 'gname', 32)):
            if hname in pax_headers:
                pass
            else:
                try:
                    info[name].encode('ascii', 'strict')
                except UnicodeEncodeError:
                    pax_headers[hname] = info[name]
                    continue
                if len(info[name]) > length:
                    pax_headers[hname] = info[name]
        for (name, digits) in (('uid', 8), ('gid', 8), ('size', 12), ('mtime', 12)):
            if name in pax_headers:
                info[name] = 0
            else:
                val = info[name]
                if 0 <= val:
                    pass
                if isinstance(val, float):
                    pax_headers[name] = str(val)
                    info[name] = 0
        if pax_headers:
            buf = self._create_pax_generic_header(pax_headers, XHDTYPE, encoding)
        else:
            buf = b''
        return buf + self._create_header(info, USTAR_FORMAT, 'ascii', 'replace')

    @classmethod
    def create_pax_global_header(cls, pax_headers):
        return cls._create_pax_generic_header(pax_headers, XGLTYPE, 'utf-8')

    def _posix_split_name(self, name, encoding, errors):
        components = name.split('/')
        for i in range(1, len(components)):
            prefix = '/'.join(components[:i])
            name = '/'.join(components[i:])
            if len(prefix.encode(encoding, errors)) <= LENGTH_PREFIX and len(name.encode(encoding, errors)) <= LENGTH_NAME:
                break
        raise ValueError('name is too long')
        return (prefix, name)

    @staticmethod
    def _create_header(info, format, encoding, errors):
        parts = [stn(info.get('name', ''), 100, encoding, errors), itn(info.get('mode', 0) & 4095, 8, format), itn(info.get('uid', 0), 8, format), itn(info.get('gid', 0), 8, format), itn(info.get('size', 0), 12, format), itn(info.get('mtime', 0), 12, format), b'        ', info.get('type', REGTYPE), stn(info.get('linkname', ''), 100, encoding, errors), info.get('magic', POSIX_MAGIC), stn(info.get('uname', ''), 32, encoding, errors), stn(info.get('gname', ''), 32, encoding, errors), itn(info.get('devmajor', 0), 8, format), itn(info.get('devminor', 0), 8, format), stn(info.get('prefix', ''), 155, encoding, errors)]
        buf = struct.pack('%ds' % BLOCKSIZE, b''.join(parts))
        chksum = calc_chksums(buf[-BLOCKSIZE:])[0]
        buf = buf[:-364] + bytes('%06o\x00' % chksum, 'ascii') + buf[-357:]
        return buf

    @staticmethod
    def _create_payload(payload):
        (blocks, remainder) = divmod(len(payload), BLOCKSIZE)
        if remainder > 0:
            payload += (BLOCKSIZE - remainder)*NUL
        return payload

    @classmethod
    def _create_gnu_long_header(cls, name, type, encoding, errors):
        name = name.encode(encoding, errors) + NUL
        info = {}
        info['name'] = '././@LongLink'
        info['type'] = type
        info['size'] = len(name)
        info['magic'] = GNU_MAGIC
        return cls._create_header(info, USTAR_FORMAT, encoding, errors) + cls._create_payload(name)

    @classmethod
    def _create_pax_generic_header(cls, pax_headers, type, encoding):
        binary = False
        for (keyword, value) in pax_headers.items():
            try:
                value.encode('utf-8', 'strict')
            except UnicodeEncodeError:
                binary = True
                break
        records = b''
        if binary:
            records += b'21 hdrcharset=BINARY\n'
        for (keyword, value) in pax_headers.items():
            keyword = keyword.encode('utf-8')
            if binary:
                value = value.encode(encoding, 'surrogateescape')
            else:
                value = value.encode('utf-8')
            l = len(keyword) + len(value) + 3
            n = p = 0
            while True:
                n = l + len(str(p))
                if n == p:
                    break
                p = n
            records += bytes(str(p), 'ascii') + b' ' + keyword + b'=' + value + b'\n'
        info = {}
        info['name'] = '././@PaxHeader'
        info['type'] = type
        info['size'] = len(records)
        info['magic'] = POSIX_MAGIC
        return cls._create_header(info, USTAR_FORMAT, 'ascii', 'replace') + cls._create_payload(records)

    @classmethod
    def frombuf(cls, buf, encoding, errors):
        if len(buf) == 0:
            raise EmptyHeaderError('empty header')
        if len(buf) != BLOCKSIZE:
            raise TruncatedHeaderError('truncated header')
        if buf.count(NUL) == BLOCKSIZE:
            raise EOFHeaderError('end of file header')
        chksum = nti(buf[148:156])
        if chksum not in calc_chksums(buf):
            raise InvalidHeaderError('bad checksum')
        obj = cls()
        obj.name = nts(buf[0:100], encoding, errors)
        obj.mode = nti(buf[100:108])
        obj.uid = nti(buf[108:116])
        obj.gid = nti(buf[116:124])
        obj.size = nti(buf[124:136])
        obj.mtime = nti(buf[136:148])
        obj.chksum = chksum
        obj.type = buf[156:157]
        obj.linkname = nts(buf[157:257], encoding, errors)
        obj.uname = nts(buf[265:297], encoding, errors)
        obj.gname = nts(buf[297:329], encoding, errors)
        obj.devmajor = nti(buf[329:337])
        obj.devminor = nti(buf[337:345])
        prefix = nts(buf[345:500], encoding, errors)
        if obj.name.endswith('/'):
            obj.type = DIRTYPE
        if obj.type == AREGTYPE and obj.type == GNUTYPE_SPARSE:
            pos = 386
            structs = []
            for i in range(4):
                try:
                    offset = nti(buf[pos:pos + 12])
                    numbytes = nti(buf[pos + 12:pos + 24])
                except ValueError:
                    break
                structs.append((offset, numbytes))
                pos += 24
            isextended = bool(buf[482])
            origsize = nti(buf[483:495])
            obj._sparse_structs = (structs, isextended, origsize)
        if obj.isdir():
            obj.name = obj.name.rstrip('/')
        if obj.type not in GNU_TYPES:
            obj.name = prefix + '/' + obj.name
        return obj

    @classmethod
    def fromtarfile(cls, tarfile):
        buf = tarfile.fileobj.read(BLOCKSIZE)
        obj = cls.frombuf(buf, tarfile.encoding, tarfile.errors)
        obj.offset = tarfile.fileobj.tell() - BLOCKSIZE
        return obj._proc_member(tarfile)

    def _proc_member(self, tarfile):
        if self.type in (GNUTYPE_LONGNAME, GNUTYPE_LONGLINK):
            return self._proc_gnulong(tarfile)
        if self.type == GNUTYPE_SPARSE:
            return self._proc_sparse(tarfile)
        if self.type in (XHDTYPE, XGLTYPE, SOLARIS_XHDTYPE):
            return self._proc_pax(tarfile)
        else:
            return self._proc_builtin(tarfile)

    def _proc_builtin(self, tarfile):
        self.offset_data = tarfile.fileobj.tell()
        offset = self.offset_data
        if self.isreg() or self.type not in SUPPORTED_TYPES:
            offset += self._block(self.size)
        tarfile.offset = offset
        self._apply_pax_info(tarfile.pax_headers, tarfile.encoding, tarfile.errors)
        return self

    def _proc_gnulong(self, tarfile):
        buf = tarfile.fileobj.read(self._block(self.size))
        try:
            next = self.fromtarfile(tarfile)
        except HeaderError:
            raise SubsequentHeaderError('missing or bad subsequent header')
        next.offset = self.offset
        if self.type == GNUTYPE_LONGNAME:
            next.name = nts(buf, tarfile.encoding, tarfile.errors)
        elif self.type == GNUTYPE_LONGLINK:
            next.linkname = nts(buf, tarfile.encoding, tarfile.errors)
        return next

    def _proc_sparse(self, tarfile):
        (structs, isextended, origsize) = self._sparse_structs
        del self._sparse_structs
        while isextended:
            buf = tarfile.fileobj.read(BLOCKSIZE)
            pos = 0
            for i in range(21):
                try:
                    offset = nti(buf[pos:pos + 12])
                    numbytes = nti(buf[pos + 12:pos + 24])
                except ValueError:
                    break
                if offset and numbytes:
                    structs.append((offset, numbytes))
                pos += 24
            isextended = bool(buf[504])
        self.sparse = structs
        self.offset_data = tarfile.fileobj.tell()
        tarfile.offset = self.offset_data + self._block(self.size)
        self.size = origsize
        return self

    def _proc_pax(self, tarfile):
        buf = tarfile.fileobj.read(self._block(self.size))
        if self.type == XGLTYPE:
            pax_headers = tarfile.pax_headers
        else:
            pax_headers = tarfile.pax_headers.copy()
        match = re.search(b'\\d+ hdrcharset=([^\\n]+)\\n', buf)
        if match is not None:
            pax_headers['hdrcharset'] = match.group(1).decode('utf-8')
        hdrcharset = pax_headers.get('hdrcharset')
        if hdrcharset == 'BINARY':
            encoding = tarfile.encoding
        else:
            encoding = 'utf-8'
        regex = re.compile(b'(\\d+) ([^=]+)=')
        pos = 0
        while True:
            match = regex.match(buf, pos)
            if not match:
                break
            (length, keyword) = match.groups()
            length = int(length)
            value = buf[match.end(2) + 1:match.start(1) + length - 1]
            keyword = self._decode_pax_field(keyword, 'utf-8', 'utf-8', tarfile.errors)
            if keyword in PAX_NAME_FIELDS:
                value = self._decode_pax_field(value, encoding, tarfile.encoding, tarfile.errors)
            else:
                value = self._decode_pax_field(value, 'utf-8', 'utf-8', tarfile.errors)
            pax_headers[keyword] = value
            pos += length
        try:
            next = self.fromtarfile(tarfile)
        except HeaderError:
            raise SubsequentHeaderError('missing or bad subsequent header')
        if 'GNU.sparse.map' in pax_headers:
            self._proc_gnusparse_01(next, pax_headers)
        elif 'GNU.sparse.size' in pax_headers:
            self._proc_gnusparse_00(next, pax_headers, buf)
        elif pax_headers.get('GNU.sparse.major') == '1' and pax_headers.get('GNU.sparse.minor') == '0':
            self._proc_gnusparse_10(next, pax_headers, tarfile)
        if self.type in (XHDTYPE, SOLARIS_XHDTYPE):
            next._apply_pax_info(pax_headers, tarfile.encoding, tarfile.errors)
            next.offset = self.offset
            if 'size' in pax_headers:
                offset = next.offset_data
                if next.isreg() or next.type not in SUPPORTED_TYPES:
                    offset += next._block(next.size)
                tarfile.offset = offset
        return next

    def _proc_gnusparse_00(self, next, pax_headers, buf):
        offsets = []
        for match in re.finditer(b'\\d+ GNU.sparse.offset=(\\d+)\\n', buf):
            offsets.append(int(match.group(1)))
        numbytes = []
        for match in re.finditer(b'\\d+ GNU.sparse.numbytes=(\\d+)\\n', buf):
            numbytes.append(int(match.group(1)))
        next.sparse = list(zip(offsets, numbytes))

    def _proc_gnusparse_01(self, next, pax_headers):
        sparse = [int(x) for x in pax_headers['GNU.sparse.map'].split(',')]
        next.sparse = list(zip(sparse[::2], sparse[1::2]))

    def _proc_gnusparse_10(self, next, pax_headers, tarfile):
        fields = None
        sparse = []
        buf = tarfile.fileobj.read(BLOCKSIZE)
        (fields, buf) = buf.split(b'\n', 1)
        fields = int(fields)
        while len(sparse) < fields*2:
            if b'\n' not in buf:
                buf += tarfile.fileobj.read(BLOCKSIZE)
            (number, buf) = buf.split(b'\n', 1)
            sparse.append(int(number))
        next.offset_data = tarfile.fileobj.tell()
        next.sparse = list(zip(sparse[::2], sparse[1::2]))

    def _apply_pax_info(self, pax_headers, encoding, errors):
        for (keyword, value) in pax_headers.items():
            if keyword == 'GNU.sparse.name':
                setattr(self, 'path', value)
            elif keyword == 'GNU.sparse.size':
                setattr(self, 'size', int(value))
            elif keyword == 'GNU.sparse.realsize':
                setattr(self, 'size', int(value))
            elif keyword in PAX_FIELDS:
                if keyword in PAX_NUMBER_FIELDS:
                    try:
                        value = PAX_NUMBER_FIELDS[keyword](value)
                    except ValueError:
                        value = 0
                if keyword == 'path':
                    value = value.rstrip('/')
                setattr(self, keyword, value)
        self.pax_headers = pax_headers.copy()

    def _decode_pax_field(self, value, encoding, fallback_encoding, fallback_errors):
        try:
            return value.decode(encoding, 'strict')
        except UnicodeDecodeError:
            return value.decode(fallback_encoding, fallback_errors)

    def _block(self, count):
        (blocks, remainder) = divmod(count, BLOCKSIZE)
        if remainder:
            blocks += 1
        return blocks*BLOCKSIZE

    def isreg(self):
        return self.type in REGULAR_TYPES

    def isfile(self):
        return self.isreg()

    def isdir(self):
        return self.type == DIRTYPE

    def issym(self):
        return self.type == SYMTYPE

    def islnk(self):
        return self.type == LNKTYPE

    def ischr(self):
        return self.type == CHRTYPE

    def isblk(self):
        return self.type == BLKTYPE

    def isfifo(self):
        return self.type == FIFOTYPE

    def issparse(self):
        return self.sparse is not None

    def isdev(self):
        return self.type in (CHRTYPE, BLKTYPE, FIFOTYPE)

class TarFile(object):
    debug = 0
    dereference = False
    ignore_zeros = False
    errorlevel = 1
    format = DEFAULT_FORMAT
    encoding = ENCODING
    errors = None
    tarinfo = TarInfo
    fileobject = ExFileObject

    def __init__(self, name=None, mode='r', fileobj=None, format=None, tarinfo=None, dereference=None, ignore_zeros=None, encoding=None, errors='surrogateescape', pax_headers=None, debug=None, errorlevel=None, copybufsize=None):
        modes = {'r': 'rb', 'a': 'r+b', 'w': 'wb', 'x': 'xb'}
        if mode not in modes:
            raise ValueError("mode must be 'r', 'a', 'w' or 'x'")
        self.mode = mode
        self._mode = modes[mode]
        if not fileobj:
            if not os.path.exists(name):
                self.mode = 'w'
                self._mode = 'wb'
            fileobj = bltn_open(name, self._mode)
            self._extfileobj = False
        else:
            if isinstance(fileobj.name, (str, bytes)):
                name = fileobj.name
            if name is None and hasattr(fileobj, 'name') and hasattr(fileobj, 'mode'):
                self._mode = fileobj.mode
            self._extfileobj = True
        self.name = os.path.abspath(name) if name else None
        self.fileobj = fileobj
        if format is not None:
            self.format = format
        if tarinfo is not None:
            self.tarinfo = tarinfo
        if dereference is not None:
            self.dereference = dereference
        if ignore_zeros is not None:
            self.ignore_zeros = ignore_zeros
        if encoding is not None:
            self.encoding = encoding
        self.errors = errors
        if pax_headers is not None and self.format == PAX_FORMAT:
            self.pax_headers = pax_headers
        else:
            self.pax_headers = {}
        if debug is not None:
            self.debug = debug
        if errorlevel is not None:
            self.errorlevel = errorlevel
        self.copybufsize = copybufsize
        self.closed = False
        self.members = []
        self._loaded = False
        self.offset = self.fileobj.tell()
        self.inodes = {}
        try:
            if self.mode == 'r':
                self.firstmember = None
                self.firstmember = self.next()
            if self.mode == 'a':
                while True:
                    self.fileobj.seek(self.offset)
                    try:
                        tarinfo = self.tarinfo.fromtarfile(self)
                        self.members.append(tarinfo)
                    except EOFHeaderError:
                        self.fileobj.seek(self.offset)
                        break
                    except HeaderError as e:
                        raise ReadError(str(e))
            if self.mode in ('a', 'w', 'x'):
                self._loaded = True
                if self.pax_headers:
                    buf = self.tarinfo.create_pax_global_header(self.pax_headers.copy())
                    self.fileobj.write(buf)
                    self.offset += len(buf)
        except:
            if not self._extfileobj:
                self.fileobj.close()
            self.closed = True
            raise

    @classmethod
    def open(cls, name=None, mode='r', fileobj=None, bufsize=RECORDSIZE, **kwargs):
        if name or not fileobj:
            raise ValueError('nothing to open')
        if mode in ('r', 'r:*'):

            def not_compressed(comptype):
                return cls.OPEN_METH[comptype] == 'taropen'

            for comptype in sorted(cls.OPEN_METH, key=not_compressed):
                func = getattr(cls, cls.OPEN_METH[comptype])
                if fileobj is not None:
                    saved_pos = fileobj.tell()
                try:
                    return func(name, 'r', fileobj, **kwargs)
                except (ReadError, CompressionError):
                    if fileobj is not None:
                        fileobj.seek(saved_pos)
                    continue
            raise ReadError('file could not be opened successfully')
        else:
            if ':' in mode:
                (filemode, comptype) = mode.split(':', 1)
                filemode = filemode or 'r'
                comptype = comptype or 'tar'
                if comptype in cls.OPEN_METH:
                    func = getattr(cls, cls.OPEN_METH[comptype])
                else:
                    raise CompressionError('unknown compression type %r' % comptype)
                return func(name, filemode, fileobj, **kwargs)
            if '|' in mode:
                (filemode, comptype) = mode.split('|', 1)
                filemode = filemode or 'r'
                comptype = comptype or 'tar'
                if filemode not in ('r', 'w'):
                    raise ValueError("mode must be 'r' or 'w'")
                stream = _Stream(name, filemode, comptype, fileobj, bufsize)
                try:
                    t = cls(name, filemode, stream, **kwargs)
                except:
                    stream.close()
                    raise
                t._extfileobj = False
                return t
            if mode in ('a', 'w', 'x'):
                return cls.taropen(name, mode, fileobj, **kwargs)
        raise ValueError('undiscernible mode')

    @classmethod
    def taropen(cls, name, mode='r', fileobj=None, **kwargs):
        if mode not in ('r', 'a', 'w', 'x'):
            raise ValueError("mode must be 'r', 'a', 'w' or 'x'")
        return cls(name, mode, fileobj, **kwargs)

    @classmethod
    def gzopen(cls, name, mode='r', fileobj=None, compresslevel=9, **kwargs):
        if mode not in ('r', 'w', 'x'):
            raise ValueError("mode must be 'r', 'w' or 'x'")
        try:
            import gzip
            gzip.GzipFile
        except (ImportError, AttributeError):
            raise CompressionError('gzip module is not available')
        try:
            fileobj = gzip.GzipFile(name, mode + 'b', compresslevel, fileobj)
        except OSError:
            if fileobj is not None and mode == 'r':
                raise ReadError('not a gzip file')
            raise
        try:
            t = cls.taropen(name, mode, fileobj, **kwargs)
        except OSError:
            fileobj.close()
            if mode == 'r':
                raise ReadError('not a gzip file')
            raise
        except:
            fileobj.close()
            raise
        t._extfileobj = False
        return t

    @classmethod
    def bz2open(cls, name, mode='r', fileobj=None, compresslevel=9, **kwargs):
        if mode not in ('r', 'w', 'x'):
            raise ValueError("mode must be 'r', 'w' or 'x'")
        try:
            import bz2
        except ImportError:
            raise CompressionError('bz2 module is not available')
        fileobj = bz2.BZ2File(fileobj or name, mode, compresslevel=compresslevel)
        try:
            t = cls.taropen(name, mode, fileobj, **kwargs)
        except (OSError, EOFError):
            fileobj.close()
            if mode == 'r':
                raise ReadError('not a bzip2 file')
            raise
        except:
            fileobj.close()
            raise
        t._extfileobj = False
        return t

    @classmethod
    def xzopen(cls, name, mode='r', fileobj=None, preset=None, **kwargs):
        if mode not in ('r', 'w', 'x'):
            raise ValueError("mode must be 'r', 'w' or 'x'")
        try:
            import lzma
        except ImportError:
            raise CompressionError('lzma module is not available')
        fileobj = lzma.LZMAFile(fileobj or name, mode, preset=preset)
        try:
            t = cls.taropen(name, mode, fileobj, **kwargs)
        except (lzma.LZMAError, EOFError):
            fileobj.close()
            if mode == 'r':
                raise ReadError('not an lzma file')
            raise
        except:
            fileobj.close()
            raise
        t._extfileobj = False
        return t

    OPEN_METH = {'tar': 'taropen', 'gz': 'gzopen', 'bz2': 'bz2open', 'xz': 'xzopen'}

    def close(self):
        if self.closed:
            return
        self.closed = True
        try:
            if self.mode in ('a', 'w', 'x'):
                self.fileobj.write(NUL*(BLOCKSIZE*2))
                self.offset += BLOCKSIZE*2
                (blocks, remainder) = divmod(self.offset, RECORDSIZE)
                if remainder > 0:
                    self.fileobj.write(NUL*(RECORDSIZE - remainder))
        finally:
            if not self._extfileobj:
                self.fileobj.close()

    def getmember(self, name):
        tarinfo = self._getmember(name)
        if tarinfo is None:
            raise KeyError('filename %r not found' % name)
        return tarinfo

    def getmembers(self):
        self._check()
        if not self._loaded:
            self._load()
        return self.members

    def getnames(self):
        return [tarinfo.name for tarinfo in self.getmembers()]

    def gettarinfo(self, name=None, arcname=None, fileobj=None):
        self._check('awx')
        if fileobj is not None:
            name = fileobj.name
        if arcname is None:
            arcname = name
        (drv, arcname) = os.path.splitdrive(arcname)
        arcname = arcname.replace(os.sep, '/')
        arcname = arcname.lstrip('/')
        tarinfo = self.tarinfo()
        tarinfo.tarfile = self
        if fileobj is None:
            if hasattr(os, 'lstat') and not self.dereference:
                statres = os.lstat(name)
            else:
                statres = os.stat(name)
        else:
            statres = os.fstat(fileobj.fileno())
        linkname = ''
        stmd = statres.st_mode
        if stat.S_ISREG(stmd):
            inode = (statres.st_ino, statres.st_dev)
            if self.dereference or statres.st_nlink > 1 and inode in self.inodes and arcname != self.inodes[inode]:
                type = LNKTYPE
                linkname = self.inodes[inode]
            else:
                type = REGTYPE
                if inode[0]:
                    self.inodes[inode] = arcname
        elif stat.S_ISDIR(stmd):
            type = DIRTYPE
        elif stat.S_ISFIFO(stmd):
            type = FIFOTYPE
        elif stat.S_ISLNK(stmd):
            type = SYMTYPE
            linkname = os.readlink(name)
        elif stat.S_ISCHR(stmd):
            type = CHRTYPE
        elif stat.S_ISBLK(stmd):
            type = BLKTYPE
        else:
            return
        tarinfo.name = arcname
        tarinfo.mode = stmd
        tarinfo.uid = statres.st_uid
        tarinfo.gid = statres.st_gid
        if type == REGTYPE:
            tarinfo.size = statres.st_size
        else:
            tarinfo.size = 0
        tarinfo.mtime = statres.st_mtime
        tarinfo.type = type
        tarinfo.linkname = linkname
        if pwd:
            try:
                tarinfo.uname = pwd.getpwuid(tarinfo.uid)[0]
            except KeyError:
                pass
        if grp:
            try:
                tarinfo.gname = grp.getgrgid(tarinfo.gid)[0]
            except KeyError:
                pass
        if hasattr(os, 'minor'):
            tarinfo.devmajor = os.major(statres.st_rdev)
            tarinfo.devminor = os.minor(statres.st_rdev)
        return tarinfo

    def list(self, verbose=True, *, members=None):
        self._check()
        if members is None:
            members = self
        for tarinfo in members:
            if verbose:
                _safe_print(stat.filemode(tarinfo.mode))
                _safe_print('%s/%s' % (tarinfo.uname or tarinfo.uid, tarinfo.gname or tarinfo.gid))
                if tarinfo.ischr() or tarinfo.isblk():
                    _safe_print('%10s' % ('%d,%d' % (tarinfo.devmajor, tarinfo.devminor)))
                else:
                    _safe_print('%10d' % tarinfo.size)
                _safe_print('%d-%02d-%02d %02d:%02d:%02d' % time.localtime(tarinfo.mtime)[:6])
            _safe_print(tarinfo.name + ('/' if tarinfo.isdir() else ''))
            if verbose:
                if tarinfo.issym():
                    _safe_print('-> ' + tarinfo.linkname)
                if tarinfo.islnk():
                    _safe_print('link to ' + tarinfo.linkname)
            print()

    def add(self, name, arcname=None, recursive=True, *, filter=None):
        self._check('awx')
        if arcname is None:
            arcname = name
        if self.name is not None and os.path.abspath(name) == self.name:
            self._dbg(2, 'tarfile: Skipped %r' % name)
            return
        self._dbg(1, name)
        tarinfo = self.gettarinfo(name, arcname)
        if tarinfo is None:
            self._dbg(1, 'tarfile: Unsupported type %r' % name)
            return
        if filter is not None:
            tarinfo = filter(tarinfo)
            if tarinfo is None:
                self._dbg(2, 'tarfile: Excluded %r' % name)
                return
        if tarinfo.isreg():
            with bltn_open(name, 'rb') as f:
                self.addfile(tarinfo, f)
        elif tarinfo.isdir():
            self.addfile(tarinfo)
            if recursive:
                for f in sorted(os.listdir(name)):
                    self.add(os.path.join(name, f), os.path.join(arcname, f), recursive, filter=filter)
        else:
            self.addfile(tarinfo)

    def addfile(self, tarinfo, fileobj=None):
        self._check('awx')
        tarinfo = copy.copy(tarinfo)
        buf = tarinfo.tobuf(self.format, self.encoding, self.errors)
        self.fileobj.write(buf)
        self.offset += len(buf)
        bufsize = self.copybufsize
        if fileobj is not None:
            copyfileobj(fileobj, self.fileobj, tarinfo.size, bufsize=bufsize)
            (blocks, remainder) = divmod(tarinfo.size, BLOCKSIZE)
            if remainder > 0:
                self.fileobj.write(NUL*(BLOCKSIZE - remainder))
                blocks += 1
            self.offset += blocks*BLOCKSIZE
        self.members.append(tarinfo)

    def extractall(self, path='.', members=None, *, numeric_owner=False):
        directories = []
        if members is None:
            members = self
        for tarinfo in members:
            if tarinfo.isdir():
                directories.append(tarinfo)
                tarinfo = copy.copy(tarinfo)
                tarinfo.mode = 448
            self.extract(tarinfo, path, set_attrs=not tarinfo.isdir(), numeric_owner=numeric_owner)
        directories.sort(key=lambda a: a.name)
        directories.reverse()
        for tarinfo in directories:
            dirpath = os.path.join(path, tarinfo.name)
            try:
                self.chown(tarinfo, dirpath, numeric_owner=numeric_owner)
                self.utime(tarinfo, dirpath)
                self.chmod(tarinfo, dirpath)
            except ExtractError as e:
                if self.errorlevel > 1:
                    raise
                else:
                    self._dbg(1, 'tarfile: %s' % e)

    def extract(self, member, path='', set_attrs=True, *, numeric_owner=False):
        self._check('r')
        if isinstance(member, str):
            tarinfo = self.getmember(member)
        else:
            tarinfo = member
        if tarinfo.islnk():
            tarinfo._link_target = os.path.join(path, tarinfo.linkname)
        try:
            self._extract_member(tarinfo, os.path.join(path, tarinfo.name), set_attrs=set_attrs, numeric_owner=numeric_owner)
        except OSError as e:
            if self.errorlevel > 0:
                raise
            elif e.filename is None:
                self._dbg(1, 'tarfile: %s' % e.strerror)
            else:
                self._dbg(1, 'tarfile: %s %r' % (e.strerror, e.filename))
        except ExtractError as e:
            if self.errorlevel > 1:
                raise
            else:
                self._dbg(1, 'tarfile: %s' % e)

    def extractfile(self, member):
        self._check('r')
        if isinstance(member, str):
            tarinfo = self.getmember(member)
        else:
            tarinfo = member
        if tarinfo.isreg() or tarinfo.type not in SUPPORTED_TYPES:
            return self.fileobject(self, tarinfo)
        if tarinfo.islnk() or tarinfo.issym():
            if isinstance(self.fileobj, _Stream):
                raise StreamError('cannot extract (sym)link as file object')
            else:
                return self.extractfile(self._find_link_target(tarinfo))
        else:
            return

    def _extract_member(self, tarinfo, targetpath, set_attrs=True, numeric_owner=False):
        targetpath = targetpath.rstrip('/')
        targetpath = targetpath.replace('/', os.sep)
        upperdirs = os.path.dirname(targetpath)
        if upperdirs and not os.path.exists(upperdirs):
            os.makedirs(upperdirs)
        if tarinfo.islnk() or tarinfo.issym():
            self._dbg(1, '%s -> %s' % (tarinfo.name, tarinfo.linkname))
        else:
            self._dbg(1, tarinfo.name)
        if tarinfo.isreg():
            self.makefile(tarinfo, targetpath)
        elif tarinfo.isdir():
            self.makedir(tarinfo, targetpath)
        elif tarinfo.isfifo():
            self.makefifo(tarinfo, targetpath)
        elif tarinfo.ischr() or tarinfo.isblk():
            self.makedev(tarinfo, targetpath)
        elif tarinfo.islnk() or tarinfo.issym():
            self.makelink(tarinfo, targetpath)
        elif tarinfo.type not in SUPPORTED_TYPES:
            self.makeunknown(tarinfo, targetpath)
        else:
            self.makefile(tarinfo, targetpath)
        if set_attrs:
            self.chown(tarinfo, targetpath, numeric_owner)
            if not tarinfo.issym():
                self.chmod(tarinfo, targetpath)
                self.utime(tarinfo, targetpath)

    def makedir(self, tarinfo, targetpath):
        try:
            os.mkdir(targetpath, 448)
        except FileExistsError:
            pass

    def makefile(self, tarinfo, targetpath):
        source = self.fileobj
        source.seek(tarinfo.offset_data)
        bufsize = self.copybufsize
        with bltn_open(targetpath, 'wb') as target:
            if tarinfo.sparse is not None:
                for (offset, size) in tarinfo.sparse:
                    target.seek(offset)
                    copyfileobj(source, target, size, ReadError, bufsize)
                target.seek(tarinfo.size)
                target.truncate()
            else:
                copyfileobj(source, target, tarinfo.size, ReadError, bufsize)

    def makeunknown(self, tarinfo, targetpath):
        self.makefile(tarinfo, targetpath)
        self._dbg(1, 'tarfile: Unknown file type %r, extracted as regular file.' % tarinfo.type)

    def makefifo(self, tarinfo, targetpath):
        if hasattr(os, 'mkfifo'):
            os.mkfifo(targetpath)
        else:
            raise ExtractError('fifo not supported by system')

    def makedev(self, tarinfo, targetpath):
        if not (hasattr(os, 'mknod') and hasattr(os, 'makedev')):
            raise ExtractError('special devices not supported by system')
        mode = tarinfo.mode
        if tarinfo.isblk():
            mode |= stat.S_IFBLK
        else:
            mode |= stat.S_IFCHR
        os.mknod(targetpath, mode, os.makedev(tarinfo.devmajor, tarinfo.devminor))

    def makelink(self, tarinfo, targetpath):
        try:
            if tarinfo.issym():
                os.symlink(tarinfo.linkname, targetpath)
            elif os.path.exists(tarinfo._link_target):
                os.link(tarinfo._link_target, targetpath)
            else:
                self._extract_member(self._find_link_target(tarinfo), targetpath)
        except symlink_exception:
            try:
                self._extract_member(self._find_link_target(tarinfo), targetpath)
            except KeyError:
                raise ExtractError('unable to resolve link inside archive')

    def chown(self, tarinfo, targetpath, numeric_owner):
        if os.geteuid() == 0:
            g = tarinfo.gid
            u = tarinfo.uid
            if not numeric_owner:
                try:
                    if grp:
                        g = grp.getgrnam(tarinfo.gname)[2]
                except KeyError:
                    pass
                try:
                    if pwd:
                        u = pwd.getpwnam(tarinfo.uname)[2]
                except KeyError:
                    pass
            try:
                if tarinfo.issym() and hasattr(os, 'lchown'):
                    os.lchown(targetpath, u, g)
                else:
                    os.chown(targetpath, u, g)
            except OSError:
                raise ExtractError('could not change owner')

    def chmod(self, tarinfo, targetpath):
        if hasattr(os, 'chmod'):
            try:
                os.chmod(targetpath, tarinfo.mode)
            except OSError:
                raise ExtractError('could not change mode')

    def utime(self, tarinfo, targetpath):
        if not hasattr(os, 'utime'):
            return
        try:
            os.utime(targetpath, (tarinfo.mtime, tarinfo.mtime))
        except OSError:
            raise ExtractError('could not change modification time')

    def next(self):
        self._check('ra')
        if self.firstmember is not None:
            m = self.firstmember
            self.firstmember = None
            return m
        if self.offset != self.fileobj.tell():
            self.fileobj.seek(self.offset - 1)
            if not self.fileobj.read(1):
                raise ReadError('unexpected end of data')
        tarinfo = None
        while True:
            try:
                tarinfo = self.tarinfo.fromtarfile(self)
            except EOFHeaderError as e:
                if self.ignore_zeros:
                    self._dbg(2, '0x%X: %s' % (self.offset, e))
                    self.offset += BLOCKSIZE
                    continue
            except InvalidHeaderError as e:
                if self.ignore_zeros:
                    self._dbg(2, '0x%X: %s' % (self.offset, e))
                    self.offset += BLOCKSIZE
                    continue
                elif self.offset == 0:
                    raise ReadError(str(e))
            except EmptyHeaderError:
                if self.offset == 0:
                    raise ReadError('empty file')
            except TruncatedHeaderError as e:
                if self.offset == 0:
                    raise ReadError(str(e))
            except SubsequentHeaderError as e:
                raise ReadError(str(e))
            break
        if tarinfo is not None:
            self.members.append(tarinfo)
        else:
            self._loaded = True
        return tarinfo

    def _getmember(self, name, tarinfo=None, normalize=False):
        members = self.getmembers()
        if tarinfo is not None:
            members = members[:members.index(tarinfo)]
        if normalize:
            name = os.path.normpath(name)
        for member in reversed(members):
            if normalize:
                member_name = os.path.normpath(member.name)
            else:
                member_name = member.name
            if name == member_name:
                return member

    def _load(self):
        while True:
            tarinfo = self.next()
            if tarinfo is None:
                break
        self._loaded = True

    def _check(self, mode=None):
        if self.closed:
            raise OSError('%s is closed' % self.__class__.__name__)
        if mode is not None and self.mode not in mode:
            raise OSError('bad operation for mode %r' % self.mode)

    def _find_link_target(self, tarinfo):
        if tarinfo.issym():
            linkname = '/'.join(filter(None, (os.path.dirname(tarinfo.name), tarinfo.linkname)))
            limit = None
        else:
            linkname = tarinfo.linkname
            limit = tarinfo
        member = self._getmember(linkname, tarinfo=limit, normalize=True)
        if member is None:
            raise KeyError('linkname %r not found' % linkname)
        return member

    def __iter__(self):
        if self._loaded:
            yield from self.members
            return
        index = 0
        if self.firstmember is not None:
            tarinfo = self.next()
            index += 1
            yield tarinfo
        while True:
            if index < len(self.members):
                tarinfo = self.members[index]
            elif not self._loaded:
                tarinfo = self.next()
                if not tarinfo:
                    self._loaded = True
                    return
            else:
                return
            index += 1
            yield tarinfo

    def _dbg(self, level, msg):
        if level <= self.debug:
            print(msg, file=sys.stderr)

    def __enter__(self):
        self._check()
        return self

    def __exit__(self, type, value, traceback):
        if type is None:
            self.close()
        else:
            if not self._extfileobj:
                self.fileobj.close()
            self.closed = True

def is_tarfile(name):
    try:
        t = open(name)
        t.close()
        return True
    except TarError:
        return False
open = TarFile.open
def main():
    import argparse
    description = 'A simple command-line interface for tarfile module.'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-v', '--verbose', action='store_true', default=False, help='Verbose output')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-l', '--list', metavar='<tarfile>', help='Show listing of a tarfile')
    group.add_argument('-e', '--extract', nargs='+', metavar=('<tarfile>', '<output_dir>'), help='Extract tarfile into target dir')
    group.add_argument('-c', '--create', nargs='+', metavar=('<name>', '<file>'), help='Create tarfile from sources')
    group.add_argument('-t', '--test', metavar='<tarfile>', help='Test if a tarfile is valid')
    args = parser.parse_args()
    if args.test is not None:
        src = args.test
        if is_tarfile(src):
            with open(src, 'r') as tar:
                tar.getmembers()
                print(tar.getmembers(), file=sys.stderr)
            if args.verbose:
                print('{!r} is a tar archive.'.format(src))
        else:
            parser.exit(1, '{!r} is not a tar archive.\n'.format(src))
    elif args.list is not None:
        src = args.list
        if is_tarfile(src):
            with TarFile.open(src, 'r:*') as tf:
                tf.list(verbose=args.verbose)
        else:
            parser.exit(1, '{!r} is not a tar archive.\n'.format(src))
    elif args.extract is not None:
        if len(args.extract) == 1:
            src = args.extract[0]
            curdir = os.curdir
        elif len(args.extract) == 2:
            (src, curdir) = args.extract
        else:
            parser.exit(1, parser.format_help())
        if is_tarfile(src):
            with TarFile.open(src, 'r:*') as tf:
                tf.extractall(path=curdir)
            if args.verbose:
                if curdir == '.':
                    msg = '{!r} file is extracted.'.format(src)
                else:
                    msg = '{!r} file is extracted into {!r} directory.'.format(src, curdir)
                print(msg)
        else:
            parser.exit(1, '{!r} is not a tar archive.\n'.format(src))
    elif args.create is not None:
        tar_name = args.create.pop(0)
        (_, ext) = os.path.splitext(tar_name)
        compressions = {'.gz': 'gz', '.tgz': 'gz', '.xz': 'xz', '.txz': 'xz', '.bz2': 'bz2', '.tbz': 'bz2', '.tbz2': 'bz2', '.tb2': 'bz2'}
        tar_mode = 'w:' + compressions[ext] if ext in compressions else 'w'
        tar_files = args.create
        with TarFile.open(tar_name, tar_mode) as tf:
            for file_name in tar_files:
                tf.add(file_name)
        if args.verbose:
            print('{!r} file created.'.format(tar_name))
if __name__ == '__main__':
    main()