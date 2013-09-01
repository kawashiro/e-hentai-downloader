__author__ = 'kz'

__all__ = ['EHTMLParser', 'EHTMLParserException']

import re
from html.parser import HTMLParser
from EHentaiDownloader import Http


class EHTMLParserException(Exception):
    """
    Parsing exception
    """
    MESSAGE_PAGES = 'Unable to fetch pages. The server answered:\n{0}'
    MESSAGE_SUBPAGES = 'Unable to fetch subpages. The server answered:\n{0}'
    MESSAGE_IMAGE = 'Unable to parse image page. The server answered:\n{0}'


class EHTMLParser():
    """
    Parser for e-hentai pages
    """
    def __init__(self, baseUri):
        """
        Init. (c) Captain Obvious
        """
        self.content = ''
        self._baseUri = baseUri
        self._subpageUri = self._baseUri + '?p={0}'

    def _raiseParserException(self, template):
        """
        Raise parser exception
        """
        message = re.sub('<[^<]+?>', '', self.content)
        message = re.sub('[\r\n\t\s\0]+', ' ', message)
        raise EHTMLParserException(template.format(message))

    def _getSubpages(self):
        """
        Get all parsed subpages from page
        """
        pages = None
        try:
            # TODO: Simplify it
            paginator = self.content[self.content.find('<td class="ptdd">'):self.content.rfind('<td onclick="sp(1)">')]
            lastPage = re.findall('sp\((\d+)\)', paginator)[-1]
            pages = list(self._subpageUri.format(i) for i in range(1, int(lastPage) + 1))
        except IndexError:
            self._raiseParserException(EHTMLParserException.MESSAGE_SUBPAGES)
        return pages

    def _getPages(self):
        """
        Links to pages on subpage
        """
        # TODO: Simplify it
        imagesBlock = self.content[self.content.find('<div id="gdt">'):self.content.rfind('<table class="ptb"')]
        pages = re.findall(Http.HTTP_SCHEME + Http.E_HENTAI_GALLERY_HOST + '(/s/[0-9a-f]+/\d+\-\d+)', imagesBlock)
        if not pages:
            self._raiseParserException(EHTMLParserException.MESSAGE_PAGES)
        return pages

    def _getImage(self):
        """
        Get direct link to image
        """
        try:
            parser = HTMLParser()
            match = re.search('<img id="img" src="http://(?P<host>[^"/:]+)(:(?P<port>\d+))?(?P<uri>[^"]*)"',
                              self.content)
            return {
                'host': match.group('host'),
                'port': match.group('port'),
                'uri':  parser.unescape(match.group('uri')),
            }
        except AttributeError:
            self._raiseParserException(EHTMLParserException.MESSAGE_IMAGE)

    def __getitem__(self, item):
        """
        Get parsed result
        """
        if item == 'pages':
            return self._getPages()
        elif item == 'subpages':
            return self._getSubpages()
        elif item == 'image':
            return self._getImage()
        else:
            raise IndexError
