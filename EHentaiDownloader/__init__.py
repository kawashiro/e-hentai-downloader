__author__ = 'kz'

__all__ = ['Environment', 'EHThread', 'Html', 'Http', 'singleton']


def singleton(cls):
    """
    Singleton decorator
    @param cls
    """
    instances = {}

    def getInstance():
        """
        Get singleton's instance
        """
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]
    return getInstance
