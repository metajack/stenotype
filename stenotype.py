ACCOUNT_SID = 'AC21f3bef2b1fca38c3a765fdda8fb72cf'
AUTH_TOKEN = '941e4c5d19b0820b88aa0565e899b766'
CALLER_ID = '5057103920'

from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET

import txilio

class StenotypeResource(Resource):
    isLeaf = True

    def render_GET(self, request):
        print 'got a get'

        account = txilio.Account(ACCOUNT_SID, AUTH_TOKEN)
        d = account.request('Calls', 'GET', {'Status': 2})

        def _done(res):
            request.write(str(res))
            request.finish()

        d.addBoth(_done)
        return NOT_DONE_YET
