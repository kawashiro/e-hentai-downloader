# -*- coding: UTF-8

__author__ = 'kz'

import re
from html.parser import HTMLParser


class EHTMLParserException(Exception):
    """
    Parsing exception
    """
    MESSAGE_PAGES = 'Unable to fetch pages. The server answered: {0}'
    MESSAGE_IMAGE = 'Unable to parse image page. The server answered: {0}'
    MESSAGE_BANDWIDTH_EXCEEDED = 'Bandwidth exceeded'


class TemporaryBanException(EHTMLParserException):
    """
    Exception on temporary ban (few seconds long)
    """
    pass


class EHTMLParser():
    """
    Parser for e-hentai pages
    """
    BANDWIDTH_EXCEEDED_STUB = 'http://ehgt.org/g/509s.gif'

    def __init__(self, baseUri):
        """
        Init. (c) Captain Obvious
        :param baseUri: string - gallery main page uri
        """
        self.content = ''
        self._baseUri = baseUri
        self._subpageUri = self._baseUri + '?p={0}'

    def _raiseParserException(self, template):
        """
        Raise parser exception
        :param template: string - error message template
        """
        message = re.sub('[\r\n\t\s\0]+', ' ', self.content)
        message = re.sub('<head>.*?</head>', '', message)
        message = re.sub('<[^<]+?>', '', message)
        message = HTMLParser().unescape(message).strip()
        temporaryBan = message.find('(Strike 0)') != -1
        if temporaryBan:
            raise TemporaryBanException
        raise EHTMLParserException(template.format(message))

    def _getSubpages(self):
        """
        Get all parsed subpages from page
        :return: list - list of all subpages
        """
        pages = None
        try:
            lastPage = re.findall('<td onclick="sp\((\d+)\)"><a.*?>\d+</a>', self.content)[-1]
            pages = list(self._subpageUri.format(i) for i in range(1, int(lastPage) + 1))
        except IndexError:
            # Gallery can contain only one subpage (the main page) so empty result is absolutely normal
            pass
        return pages

    def _getPages(self):
        """
        Links to pages on subpage
        :return: list - list of all pages on subpage
        """
        pages = re.findall('<div class="gdtm".*?>.*?<a href="(.*?)".*?</div></div>', self.content)
        if not pages:
            self._raiseParserException(EHTMLParserException.MESSAGE_PAGES)
        return pages

    def _getImage(self):
        """
        Get direct link to image
        :return: dict - parsed image info
        """
        try:
            parser = HTMLParser()
            match = re.search('<img id="img" src="(?P<full>http://(?P<host>[^"/:]+)(:(?P<port>\d+))?(?P<uri>[^"]*))"',
                              self.content)
            image = {
                'host': match.group('host'),
                'port': match.group('port'),
                'uri':  parser.unescape(match.group('uri')),
                'full_uri':  parser.unescape(match.group('full')),
            }
            if image['full_uri'] == self.BANDWIDTH_EXCEEDED_STUB:
                raise EHTMLParserException(EHTMLParserException.MESSAGE_BANDWIDTH_EXCEEDED)
            return image
        except AttributeError:
            self._raiseParserException(EHTMLParserException.MESSAGE_IMAGE)

    def _getMetadata(self):
        """
        Get gallery's meta info
        :return: dict - gallery metadata
        """
        parser = HTMLParser()
        titles = re.findall('<h1 id="g[jn]">(.*?)</h1>', self.content)
        additional = re.findall('<td class="gdt1">(.*?):?</td>.*?<td class="gdt2">(.*?):?</td>', self.content)
        meta = {
            'additional': {},
            'title': {
                'main': parser.unescape(titles[0]),
                'jap': parser.unescape(titles[1])
            },
        }
        for key, value in additional:
            meta['additional'][key] = re.sub('<[^<]+?>', '', parser.unescape(value))
        count, size = meta['additional']['Images'].split(' @ ')
        meta['count'] = int(count)
        meta['size'] = size
        return meta

    def __getitem__(self, item):
        """
        Get parsed result
        :param item: string
        """
        if item == 'pages':
            return self._getPages()
        elif item == 'subpages':
            return self._getSubpages()
        elif item == 'image':
            return self._getImage()
        elif item == 'meta':
            return self._getMetadata()
        else:
            raise IndexError(item)
