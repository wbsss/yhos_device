import gevent
import web


def start():
    gevent.spawn(web.web_server_start_localhost, None)
    while (True):
        gevent.sleep(1)
    pass