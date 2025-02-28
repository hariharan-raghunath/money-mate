import logging
from logging.handlers import TimedRotatingFileHandler

'''logging.basicConfig(filename='../logs/application.log', level=logging.DEBUG,
                    format='%(asctime)s:%(levelname)s:%(message)s')'''


def setlogger():
    formatter = logging.Formatter(fmt='%(asctime)2s %(levelname)-2s %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    handler = TimedRotatingFileHandler('./logs/application.log', when='midnight', interval=1, backupCount=15)
    handler.suffix = "%Y-%m-%d"
    handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    return logger
