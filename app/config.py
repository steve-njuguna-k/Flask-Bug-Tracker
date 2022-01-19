from distutils.debug import DEBUG
from re import L


class Config(object):
    SECRET_KEY='thisissecret'

class DevConfig(Config):
    DEBUG=True

class ProdConfig(Config):
    pass

