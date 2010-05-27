import urllib, base64, hmac
from hashlib import sha1
from xml.sax.saxutils import escape, quoteattr

from twisted.web import client

TWILIO_API_URL = 'https://api.twilio.com/2008-08-01'

# Twilio REST Helpers
# ===========================================================================

class Account:
    """Twilio account object that provides helper functions for making
    REST requests to the Twilio API.  This helper library works both in
    standalone python applications using the urllib/urlib2 libraries and
    inside Google App Engine applications using urlfetch.
    """

    def __init__(self, id, token):
        self.id = id
        self.token = token

    def request(self, path, method=None, vars=None):
        if not path or len(path) == 0:
            raise ValueError('Invalid path parameter')
        if method and method not in ['GET', 'POST', 'DELETE', 'PUT']:
            raise NotImplementedError(
                "HTTP %s method not implemented" % method)

        if path[0] == '/':
            uri = TWILIO_API_URL + '/Accounts/%s' % self.id + path
        else:
            uri = TWILIO_API_URL + '/Accounts/%s/' % self.id + path

        if vars and len(vars) > 0:
            if uri.find('?') > 0:
                if uri[-1] != '&':
                    uri += '&'
                uri = uri + urllib.urlencode(vars)
            else:
                uri = uri + '?' + urllib.urlencode(vars)

        credentials = base64.encodestring('%s:%s' % (self.id, self.token))
        credentials = credentials.replace('\n', '')
        authorization = {'Authorization': 'Basic %s' % credentials}
        return client.getPage(uri, method=method, headers=authorization)


# TwiML Response Helpers
# ===========================================================================

class Verb:
    """Twilio basic verb object.
    """
    def __init__(self, **kwargs):
        self.name = self.__class__.__name__
        self.body = None
        self.nestables = None
        
        self.verbs = []
        self.attrs = {}
        for k, v in kwargs.items():
            if k == "sender": k = "from"
            if v: self.attrs[k] = quoteattr(str(v))
    
    def __repr__(self):
        s = '<%s' % self.name
        keys = self.attrs.keys()
        keys.sort()
        for a in keys:
            s += ' %s=%s' % (a, self.attrs[a])
        if self.body or len(self.verbs) > 0:
            s += '>'
            if self.body:
                s += escape(self.body)
            if len(self.verbs) > 0:
                s += '\n'
                for v in self.verbs:
                    for l in str(v)[:-1].split('\n'):
                        s += "\t%s\n" % l
            s += '</%s>\n' % self.name
        else:
            s += '/>\n'
        return s
    
    def append(self, verb):
        if not self.nestables:
            raise TwilioException("%s is not nestable" % self.name)
        if verb.name not in self.nestables:
            raise TwilioException("%s is not nestable inside %s" % \
                (verb.name, self.name))
        self.verbs.append(verb)
        return verb
    
    def asUrl(self):
        return urllib.quote(str(self))
    
    def addSay(self, text, **kwargs):
        return self.append(Say(text, **kwargs))
    
    def addPlay(self, url, **kwargs):
        return self.append(Play(url, **kwargs))
    
    def addPause(self, **kwargs):
        return self.append(Pause(**kwargs))
    
    def addRedirect(self, url=None, **kwargs):
        return self.append(Redirect(url, **kwargs))   
    
    def addHangup(self, **kwargs):
        return self.append(Hangup(**kwargs)) 
    
    def addGather(self, **kwargs):
        return self.append(Gather(**kwargs))
    
    def addNumber(self, number, **kwargs):
        return self.append(Number(number, **kwargs))
    
    def addDial(self, number=None, **kwargs):
        return self.append(Dial(number, **kwargs))
    
    def addRecord(self, **kwargs):
        return self.append(Record(**kwargs))
    
    def addConference(self, name, **kwargs):
        return self.append(Conference(name, **kwargs))
        
    def addSms(self, msg, **kwargs):
        return self.append(Sms(msg, **kwargs))

class Response(Verb):
    """Twilio response object.
    
    version: Twilio API version e.g. 2008-08-01
    """
    def __init__(self, version=None, **kwargs):
        Verb.__init__(self, version=version, **kwargs)
        self.nestables = ['Say', 'Play', 'Gather', 'Record', 'Dial',
            'Redirect', 'Pause', 'Hangup', 'Sms']

class Say(Verb):
    """Say text
    
    text: text to say
    voice: MAN or WOMAN
    language: language to use
    loop: number of times to say this text
    """
    MAN = 'man'
    WOMAN = 'woman'
    
    ENGLISH = 'en'
    SPANISH = 'es'
    FRENCH = 'fr'
    GERMAN = 'de'
    
    def __init__(self, text, voice=None, language=None, loop=None, **kwargs):
        Verb.__init__(self, voice=voice, language=language, loop=loop,
            **kwargs)
        self.body = text
        if voice and (voice != self.MAN and voice != self.WOMAN):
            raise TwilioException( \
                "Invalid Say voice parameter, must be 'man' or 'woman'")
        if voice and (voice != self.MAN and voice != self.WOMAN):
            raise TwilioException( \
                "Invalid Say language parameter, must be " + \
                "'en', 'es', 'fr', or 'de'")

class Play(Verb):
    """Play audio file at a URL
    
    url: url of audio file, MIME type on file must be set correctly
    loop: number of time to say this text
    """
    def __init__(self, url, loop=None, **kwargs):
        Verb.__init__(self, loop=loop, **kwargs)
        self.body = url

class Pause(Verb):
    """Pause the call
    
    length: length of pause in seconds
    """
    def __init__(self, length=None, **kwargs):
        Verb.__init__(self, length=length, **kwargs)

class Redirect(Verb):
    """Redirect call flow to another URL
    
    url: redirect url
    """
    GET = 'GET'
    POST = 'POST'
    
    def __init__(self, url=None, method=None, **kwargs):
        Verb.__init__(self, method=method, **kwargs)
        if method and (method != self.GET and method != self.POST):
            raise TwilioException( \
                "Invalid method parameter, must be 'GET' or 'POST'")
        self.body = url

class Hangup(Verb):
    """Hangup the call
    """
    def __init__(self, **kwargs):
        Verb.__init__(self)

class Gather(Verb):
    """Gather digits from the caller's keypad
    
    action: URL to which the digits entered will be sent
    method: submit to 'action' url using GET or POST
    numDigits: how many digits to gather before returning
    timeout: wait for this many seconds before returning
    finishOnKey: key that triggers the end of caller input
    """
    GET = 'GET'
    POST = 'POST'

    def __init__(self, action=None, method=None, numDigits=None, timeout=None,
        finishOnKey=None, **kwargs):
        
        Verb.__init__(self, action=action, method=method,
            numDigits=numDigits, timeout=timeout, finishOnKey=finishOnKey,
            **kwargs)
        if method and (method != self.GET and method != self.POST):
            raise TwilioException( \
                "Invalid method parameter, must be 'GET' or 'POST'")
        self.nestables = ['Say', 'Play', 'Pause']

class Number(Verb):
    """Specify phone number in a nested Dial element.
    
    number: phone number to dial
    sendDigits: key to press after connecting to the number
    """
    def __init__(self, number, sendDigits=None, **kwargs):
        Verb.__init__(self, sendDigits=sendDigits, **kwargs)
        self.body = number
        
class Sms(Verb):
    """ Send a Sms Message to a phone number
    
    to: whom to send message to, defaults based on the direction of the call
    sender: whom to send message from.
    action: url to request after the message is queued
    method: submit to 'action' url using GET or POST
    statusCallback: url to hit when the message is actually sent
    """
    GET = 'GET'
    POST = 'POST'
    
    def __init__(self, msg, to=None, sender=None, method=None, action=None,
        statusCallback=None, **kwargs):
        Verb.__init__(self, action=action, method=method, to=to, sender=sender,
            statusCallback=statusCallback, **kwargs)
        if method and (method != self.GET and method != self.POST):
            raise TwilioException( \
                "Invalid method parameter, must be GET or POST")
        self.body = msg

class Conference(Verb):
    """Specify conference in a nested Dial element.
    
    name: friendly name of conference 
    muted: keep this participant muted (bool)
    beep: play a beep when this participant enters/leaves (bool)
    startConferenceOnEnter: start conf when this participants joins (bool)
    endConferenceOnExit: end conf when this participants leaves (bool)
    waitUrl: TwiML url that executes before conference starts
    waitMethod: HTTP method for waitUrl GET/POST
    """
    GET = 'GET'
    POST = 'POST'
    
    def __init__(self, name, muted=None, beep=None,
        startConferenceOnEnter=None, endConferenceOnExit=None, waitUrl=None,
        waitMethod=None, **kwargs):
        Verb.__init__(self, muted=muted, beep=beep,
            startConferenceOnEnter=startConferenceOnEnter,
            endConferenceOnExit=endConferenceOnExit, waitUrl=waitUrl,
            waitMethod=waitMethod, **kwargs)
        if waitMethod and (waitMethod != self.GET and waitMethod != self.POST):
            raise TwilioException( \
                "Invalid waitMethod parameter, must be GET or POST")
        self.body = name

class Dial(Verb):
    """Dial another phone number and connect it to this call
    
    action: submit the result of the dial to this URL
    method: submit to 'action' url using GET or POST
    """
    GET = 'GET'
    POST = 'POST'
    
    def __init__(self, number=None, action=None, method=None, **kwargs):
        Verb.__init__(self, action=action, method=method, **kwargs)
        self.nestables = ['Number', 'Conference']
        if number and len(number.split(',')) > 1:
            for n in number.split(','):
                self.append(Number(n.strip()))
        else:
            self.body = number
        if method and (method != self.GET and method != self.POST):
            raise TwilioException( \
                "Invalid method parameter, must be GET or POST")

class Record(Verb):
    """Record audio from caller
    
    action: submit the result of the dial to this URL
    method: submit to 'action' url using GET or POST
    maxLength: maximum number of seconds to record
    timeout: seconds of silence before considering the recording complete
    """
    GET = 'GET'
    POST = 'POST'
    
    def __init__(self, action=None, method=None, maxLength=None, 
        timeout=None, **kwargs):
        Verb.__init__(self, action=action, method=method, maxLength=maxLength,
            timeout=timeout, **kwargs)
        if method and (method != self.GET and method != self.POST):
            raise TwilioException( \
                "Invalid method parameter, must be GET or POST")

# Twilio Utility function and Request Validation
# ===========================================================================

class Utils:
    def __init__(self, id, token):
        """initialize a twilio utility object
        
        id: Twilio account SID/ID
        token: Twilio account token
        
        returns a Twilio util object
        """
        self.id = id
        self.token = token
    
    def validateRequest(self, uri, postVars, expectedSignature):
        """validate a request from twilio
        
        uri: the full URI that Twilio requested on your server
        postVars: post vars that Twilio sent with the request
        expectedSignature: signature in HTTP X-Twilio-Signature header
        
        returns true if the request passes validation, false if not
        """
        
        # append the POST variables sorted by key to the uri
        s = uri
        if len(postVars) > 0:
            for k, v in sorted(postVars.items()):
                s += k + v
        
        # compute signature and compare signatures
        return (base64.encodestring(hmac.new(self.token, s, sha1).digest()).\
            strip() == expectedSignature)
