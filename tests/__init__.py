import logging


logger = logging.getLogger('qgpkg')
logger.addHandler(logging.StreamHandler())


def nolog(lvl, msg, *args, **kwargs):
    pass
