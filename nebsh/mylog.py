from datetime import datetime

__author__ = 'Mike'

PRODUCTION = 0
DEBUG = 1
VERBOSE = 2

mylog_name = None
debug_level = PRODUCTION


def set_mylog_name(name):
    global mylog_name
    mylog_name = name


def set_mylog_production():
    global debug_level
    debug_level = PRODUCTION


def set_mylog_verbose():
    global debug_level
    debug_level = VERBOSE


def set_mylog_dbg():
    global debug_level
    debug_level = DEBUG


def mylog(message):
    if mylog_name is not None:
        print '{}|[{}] {}'.format(datetime.utcnow(), mylog_name, message)
    else:
        print '{}| {}'.format(datetime.utcnow(), message)


def log_dbg(message):
    global debug_level
    if debug_level >= DEBUG:
        mylog(message)


def log_verbose(message):
    global debug_level
    if debug_level >= DEBUG:
        mylog(message)