# -*- coding: UTF-8

__author__ = 'kz'

from http import client

E_HENTAI_GALLERY_HOST = 'g.e-hentai.org'
HTTP_CLIENT_CHUNK_SIZE = 10240
HTTP_CLIENT_CONNECTION_TIMEOUT = 20
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
        'User-Agent': USER_AGENT # TODO: Custom user-agent
    }

    def __init__(self, host=E_HENTAI_GALLERY_HOST, port=None):
        """
        Init client
        :param host: string - remote server host
        :param port: int    - remote server port
        """
        self._host = host
        self._port = port
        self._response = None
        self._connect()

    def _connect(self):
        """
        Connect to specified host
        """
        self._connection = client.HTTPConnection(self._host, self._port, timeout=HTTP_CLIENT_CONNECTION_TIMEOUT)

    def get(self, uri):
        """
        Get content of page
        :param uri: string - request uri
        :return:    string - decoded response
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
        :param uri: string - request uri
        """
        try:
            self._connection.request('GET', uri, headers=self._headers)
            self._response = self._connection.getresponse()
        except client.BadStatusLine:
            self._connect()
            self.sendRequest(uri)

    def getHeader(self, name):
        """
        Get response header
        :param name: string - header name
        :return:     string - header value
        """
        return self._response.getheader(name)

    def getChunk(self, size=HTTP_CLIENT_CHUNK_SIZE):
        """
        Get next chunk of response data
        :param size: int    - chunk size to fetch at once
        :return:     binary - response chunk
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
