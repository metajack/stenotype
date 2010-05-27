# -*- mode: python -*-

from twisted.application import service, internet
from twisted.web import server, resource
from twisted.words.protocols.jabber import jid
from wokkel.client import XMPPClient

from wokkel import client
from stenotype import StenotypeResource, StenoBot

LOG_TRAFFIC = True

application = service.Application('Stenotype')


client = XMPPClient(jid.internJID('link@dmt.im'), 'XXXXX')
client.logTraffic = True

bot = StenoBot('stenotype@chat.speeqe.com', 'stenobot')
bot.setHandlerParent(client)

client.setServiceParent(application)

site = server.Site(StenotypeResource(bot))
server = internet.TCPServer(8000, site)
server.setServiceParent(application)
