from twisted.application import service, internet
from twisted.web import server, resource

from wokkel import client

from stenotype import StenotypeResource

LOG_TRAFFIC = True


root = StenotypeResource()

site = server.Site(root)
server = internet.TCPServer(5555, site)
application = service.Application("Stenotype")
server.setServiceParent(application)
