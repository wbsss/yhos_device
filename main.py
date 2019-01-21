#!/usr/bin/env python
# encoding: utf-8
from gevent import monkey
monkey.patch_all()
if __name__ == '__main__':
    import server
    server.start()
    pass