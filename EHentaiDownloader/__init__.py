__author__ = 'kz'

__all__ = ['Environment', 'EHThread', 'Html', 'Http', 'singleton']


def singleton(cls):

    instances = {}

    def getInstance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]
    return getInstance
