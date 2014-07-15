#! /usr/bin/python

import os
import cherrypy
import logging
from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
from ws4py.websocket import WebSocket
from ws4py.manager import WebSocketManager

cherrypy.config.update({'server.socket_port': 9000})
WebSocketPlugin(cherrypy.engine).subscribe()
cherrypy.tools.websocket = WebSocketTool()

logger = logging.getLogger('sensors')
logging.basicConfig(level=logging.DEBUG)

manager = WebSocketManager()

def replicate(data):
    """Replicate data to all connected endpoints
    """
    for l in data.splitlines():
        try:
            # FIXME: check against _subscriptions
            manager.broadcast(l, binary=True)
        except Exception, e:
            logger.error("Exception: " + unicode(e))

class SensorSocket(WebSocket):
    def __init__(self, *p, **kw):
        super(SensorSocket, self).__init__(*p, **kw)
        self._subscriptions = set()

    def handshake_ok(self):
        print "Opening %s" % self
        manager.add(self)

    def received_message(self, message):
        """Handle messages
        """
        # Ignore control messages
        if message.data.startswith('TOKEN'):
            return
        elif message.data.startswith('SUBSCRIBE'):
            self._subscriptions.append(message.data.split(" ")[2])
        else:
            replicate(message.data)
        return True

class Root(object):
    @cherrypy.expose
    def index(self):
        # FIXME: return viz page
        return 'Sensor test'

    @cherrypy.expose
    def ws(self):
        # you can access the class instance through
        handler = cherrypy.request.ws_handler
        print handler

if __name__ == '__main__':
    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': 9000,
        'tools.staticdir.root': os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
        }
    )
    WebSocketPlugin(cherrypy.engine).subscribe()
    cherrypy.tools.websocket = WebSocketTool()

    cherrypy.quickstart(Root(), '', config={
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': '.'
            },
        '/ws': {
            'tools.websocket.on': True,
            'tools.websocket.handler_cls': SensorSocket
            }
        }
    )
