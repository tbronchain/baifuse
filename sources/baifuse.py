#!/usr/bin/env python

from sys import argv, exit
from time import time
from fuse import FUSE, Operations, LoggingMixIn
import os

import stat
import errno

from baidupan.baidupan import BaiduPan

BAIDUPATH="/"

class BaiFuse(LoggingMixIn, Operations):
    def __init__(self, root, token):
        self.root = root
        self.token = token
        self.api = BaiduPan(self.token)

    def get_path(self, path):
        return os.path.join(BAIDUPATH,path)

#    def chmod(self, path, mode):
#        return True

#    def chown(self, path, uid, gid):
#        return True

#    def create(self, path, mode):
#        f = self.sftp.open(path, 'w')
#        f.chmod(mode)
#        f.close()
#        return 0

#    def destroy(self, path):
#        self.sftp.close()
#        self.client.close()

    def getattr(self, path, fh=None):
        resp = json.loads(self.api.meta(self.get_path(path)))
        if 'list' not in resp:
            return {}
        return {
            'st_ino': 0,
            'st_dev': 0,
            'st_atime': 0,
            'st_mtime': resp['list'][0]['mtime'],
            'st_ctime': resp['list'][0]['ctime'],
            'st_gid': os.getgid(),
            'st_uid': os.getuid(),
            'st_mode': ((stat.S_IFDIR | 0755) if resp['list'][0]['isdir'] else (stat.S_IFREG | 0755)),
            'st_size': resp['list'][0]['size'],
            'st_nlink': (2 if resp['list'][0]['isdir'] else 1),
            }

    def mkdir(self, path, mode):
        self.api.mkdir(self.get_path(path))
        #return?

    def read(self, path, size, offset, fh):
        return self.api.download(self.get_path(path),
                                 headers={'Range':"Range: bytes=%s-%s"%(offset,offset+size)})

    def readdir(self, path, fh):
        resp = json.loads(self.api.ls(self.get_path(path)))
        return ['.', '..'] + [name['path'].encode('utf-8') for name in resp['list']]

#    def readlink(self, path):
#        return self.sftp.readlink(path)

#    def rename(self, old, new):
#        return self.sftp.rename(old, self.root + new)

    def rmdir(self, path):
        self.api.rm(self.get_path(path))
        # return ?

#    def symlink(self, target, source):
#        return self.sftp.symlink(source, target)

#    def truncate(self, path, length, fh=None):
#        return self.sftp.truncate(path, length)

#    def unlink(self, path):
#        return self.sftp.unlink(path)

#    def utimens(self, path, times=None):
#        return self.sftp.utime(path, times)

    def write(self, path, data, offset, fh):
        # can't use the api -> need file dissociation + merge (super file)
        return self.api.upload(path)


if __name__ == '__main__':
    if len(argv) != 3:
        print('usage: %s <mountpoint> <token>' % argv[0])
        exit(1)
    fuse = FUSE(BaiFuse(argv[1], argv[2]), argv[1], foreground=True, nothreads=True)
