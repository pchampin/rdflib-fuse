#!/usr/bin/env python
#
# TODO LICENSE LGPL
#
# This file is largely inspired by 
# https://github.com/libfuse/python-fuse/blob/323099c3616cf6e49761ccba6e58ed3a24f5646b/example/hello.py

from __future__ import print_function

import collections, errno, os, re, stat, sys, time
try:
    import _find_fuse_parts
except ImportError:
    pass
import fuse
import rdflib

if not hasattr(fuse, '__version__'):
    raise RuntimeError("your fuse-py doesn't know of fuse.__version__, probably it's too old.")

fuse.fuse_python_api = (0, 2)


class MyStat(fuse.Stat):
    def __init__(self, timestamp=0):
        self.st_mode = 0
        self.st_ino = 0
        self.st_dev = 0
        self.st_nlink = 0
        self.st_uid = os.getuid()
        self.st_gid = os.getgid()
        self.st_size = 0
        self.st_atime = timestamp
        self.st_mtime = timestamp
        self.st_ctime = timestamp

class RdfFS(fuse.Fuse):

    def __init__(self, *args, **kw):
        super(RdfFS, self).__init__(*args, **kw)
        self.parser.add_option(
            "-S", "--store",
            help="rdflib store specification, "
                 "of the form :{store-plugin}:{config-string}) "
                 "(REQUIRED)",
        )
        self.parser.add_option(
            "-F", "--format",
            help="RDF format in which to expose graphs "
                 "(defaults to 'turtle')",
            default="turtle",
        )
        self._root = None
        self._timestamp = time.time()
        self._open = {}

    def parse(self, *args, **kw):
        fuseargs = super(RdfFS, self).parse(*args, **kw)
        options = self.cmdline[0]
        help = '-h' in sys.argv or '--help' in sys.argv
        if not help:
            if options.store is None:
                print("%s: option -S/--store is required" % sys.argv[0],
                    file=sys.stderr)
                exit(kw.get('errex', -1))
            self._store = open_store(options.store)
            self._root = make_root(self._store)
            self._format = options.format
        return fuseargs

    # FS API

    def getattr(self, path):
        #print("===", "getattr", path)
        node = self._get_node(path)
        if node is None:
            #print("===", "get_attr", "error", path)
            return -errno.ENOENT

        st = MyStat(self._timestamp)
        if node == LEAF:
            st.st_mode = stat.S_IFREG | 0o444
            st.st_nlink = 1
            st.st_size = len(self._get_content(path))
        else:
            st.st_mode = stat.S_IFDIR | 0o755
            st.st_nlink = 2
            st.st_size = 4096
        return st

    def readdir(self, path, offset):
        #print("===", "readdir", path)
        for e in  '.', '..':
            yield fuse.Direntry(e)
        node = self._get_node(path)
        try:
            for e in node.keys():
                yield fuse.Direntry(e)
        except:
            pass

    def open(self, path, flags):
        #print("===", "open", path)
        node = self._get_node(path)
        if node != LEAF:
            return -errno.ENOENT
        accmode = os.O_RDONLY | os.O_WRONLY | os.O_RDWR
        if (flags & accmode) != os.O_RDONLY:
            return -errno.EACCES
        self._open[path] = self._get_content(path)
        

    def read(self, path, size, offset):
        #print("===", "read", path, size, offset)
        content = self._open.get(path)
        if content is None:
            return -errno.ENOENT
        return content[offset:offset+size]

    # protected methods

    def _get_node(self, path):
        #print("===", "_get_node", path)
        if path == '/':
            return self._root
        parts = [ x if x else '%'  for x in path[1:].split('/')]
        node = self._root
        for part in parts:
            if node == LEAF or part not in node:
                return None
            node = node[part]
        return node

    def _get_graph(self, path):
        #print("===", "_get_graph", path)
        uri = rdflib.URIRef(re.sub(r'/%(/?)', r'/\1', path[1:]))
        return rdflib.Graph(
            store=self._store,
            identifier=uri,
        )

    def _get_content(self, path):
        #print("===", "_get_content", path)
        g = self._get_graph(path)
        # ugly hack to prevent spurious namespaces in Turtle serializer:
        # we copy the graph in a pristine graph
        h = rdflib.Graph(identifier=g.identifier)
        h.addN( (s, p, o, h) for (s, p, o) in self._get_graph(path))
        return h.serialize(format=self._format, base=h.identifier)



def open_store(store_spec):
    if store_spec[0] != ':':
        store_spec = ':Sleepycat:%s' % store_spec
    _, store_type, store_cfg = store_spec.split(':', 2)
    return rdflib.plugin.get(store_type, rdflib.store.Store)(store_cfg)

def make_root(store):
    root = make_rec_dict()
    for ctx in store.contexts():
        #print("===", ctx.identifier, len(ctx))
        path = ctx.identifier.split('/')
        path = [ x.encode('utf8') or '%' for x in path ]
        cwd = root
        for i in path[:-1]:
            cwd = cwd[i]
        cwd[path[-1]] = LEAF
    return root

def make_rec_dict():
    return collections.defaultdict(make_rec_dict)

LEAF = object()



def main():
    usage="""
%s {mountpoint} -S {store-spec} [options]

""" % sys.argv[0] + fuse.Fuse.fusage
    server = RdfFS(version="%prog " + fuse.__version__,
                     usage=usage,
                     dash_s_do='setsingle')

    server.parse(errex=1)
    server.main()


if __name__ == '__main__':
    main()
    #debug()
