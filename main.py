#!/usr/bin/env python3
# -*- coding: UTF-8

__author__ = 'kz'

# TODO: gettext or do something with crappy text constants

from EHentaiDownloader import Environment
import sys

if __name__ == '__main__':
    c = 1
    try:
        app = Environment.Application()
        app.init()
        app.run()
        c = 0
    except SystemExit:
        pass
    except KeyboardInterrupt:
        Environment.Log('Terminated', Environment.LOG_LEVEL_WARN)
    except Environment.InvalidArgumentException:
        pass
    except BaseException as e:
        if Environment.Application()['log_level'] == Environment.LOG_LEVEL_DEBUG:
            raise e
        print('\n%s: %s' % (type(e), str(e)), file=sys.stderr)
    exit(c)
