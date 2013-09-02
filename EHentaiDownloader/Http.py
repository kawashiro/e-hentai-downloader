__author__ = 'kz'

__all__ = ['Client', 'ReadResponseException', 'E_HENTAI_GALLERY_HOST', 'HTTP_CLIENT_CHUNK_SIZE', 'HTTP_SCHEME', 'USER_AGENT']

from http import client

# TODO: Move some crap in config
E_HENTAI_GALLERY_HOST = 'g.e-hentai.org'
HTTP_CLIENT_CHUNK_SIZE = 10240
HTTP_SCHEME = 'http://'
USER_AGENT = 'Mozilla/5.0 (X11; Linux i686; rv:23.0) Gecko/20100101 Firefox/23.0'


class ReadResponseException(Exception):
    """
    Exception if connection is closed by remote server or transfer completed
    """
    pass


class Client:
    """
    Simple HTTP-client for browsing ;)
    """
    _headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ru,en-us;q=0.7,en;q=0.3',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Host': E_HENTAI_GALLERY_HOST,
        'User-Agent': USER_AGENT
    }

    def __init__(self, host=E_HENTAI_GALLERY_HOST, port=None):
        """
        Init client
        """
        self._host = host
        self._port = port
        self._response = None
        self._connect()

    def _connect(self):
        """
        Connect to specified host
        """
        self._connection = client.HTTPConnection(self._host, self._port)

    def get(self, uri):
        """
        Get content of page
        @param uri Request uri
        """
        self.sendRequest(uri)
        content = b''
        while True:
            try:
                content += self.getChunk()
            except ReadResponseException:
                break
        return content.decode()

    def sendRequest(self, uri):
        """
        Send prepared request to a server
        @param uri Request uri
        """
        try:
            # TODO: Timeout!
            self._connection.request('GET', uri, headers=self._headers)
            self._response = self._connection.getresponse()
        except client.BadStatusLine:
            self._connect()
            self.sendRequest(uri)

    def getChunk(self, size=HTTP_CLIENT_CHUNK_SIZE):
        """
        Get next chunk of response data
        @param size Chunk size to fetch at once
        """
        chunk = None
        if not self._response.closed:
            chunk = self._response.read(size)
        if not chunk:
            raise ReadResponseException
        return chunk

    def close(self):
        """
        Close connection
        """
        self._connection.close()
