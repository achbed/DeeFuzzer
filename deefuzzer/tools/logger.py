#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from threading import Thread


class Logger:
    """A logging object"""

    def __init__(self, filepath):
        self.logger = logging.getLogger('myapp')
        self.hdlr = logging.FileHandler(filepath)
        self.formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        self.hdlr.setFormatter(self.formatter)
        self.logger.addHandler(self.hdlr)
        self.logger.setLevel(logging.INFO)

    def write_debug(self, message):
        self.logger.debug(message)

    def write_info(self, message):
        self.logger.info(message)

    def write_warning(self, message):
        self.logger.warning(message)

    def write_error(self, message):
        self.logger.error(message)

    def write_critical(self, message):
        self.logger.critical(message)


class QueueLogger(Thread):
    """A queue-based logging object"""

    def __init__(self, filepath, q):
        Thread.__init__(self)
        self.logger = Logger(filepath)
        self.q = q

    def run(self):
        while True:
            try:
                msg = self.q.get(1)
                if not isinstance(msg, dict):
                    self.logger.write_error(str(msg))
                else:
                    if 'msg' not in msg:
                        continue

                    if 'level' not in msg:
                        msg['level'] = 'error'
                       
                    if msg['level'] == 'debug':
                        self.logger.write_debug(msg['msg'])
                    elif msg['level'] == 'info':
                        self.logger.write_info(msg['msg'])
                    elif msg['level'] == 'warning':
                        self.logger.write_warning(msg['msg'])
                    elif msg['level'] == 'critical':
                        self.logger.write_critical(msg['msg'])
                    else:
                        self.logger.write_error(msg['msg'])
            except:
                pass


class ObjectQueueLog(object):
    """A class inheriting object, but with an attached QueueLogger and common logging functionality"""
    def __init__(self, logqueue):
        object.__init__(self)
        self.__logqueue = logqueue

    def log_msg_hook(self, msg):
        """
        Implement this in child classes to alter the log message before output.  Useful to prepend a class name
        or identifier for code tracing.
        :param msg: The message to alter
        :return: The message to log
        """
        return msg
    
    def log_msg(self, msg, level='error'):
        """Logs a message"""
        try:
            msg = self.log_msg_hook(str(msg))
            obj = {'msg': str(msg), 'level': str(level)}
            self.__logqueue.put(obj)
        except:
            pass

    def log_debug(self, msg):
        """Logs a message with a level of 'debug'"""
        self.log_msg(msg, 'debug')

    def log_info(self, msg):
        """Logs a message with a level of 'info'"""
        self.log_msg(msg, 'info')

    def log_warning(self, msg):
        """Logs a message with a level of 'warning'"""
        self.log_msg(msg, 'warning')

    def log_error(self, msg):
        """Logs a message with a level of 'error'"""
        self.log_msg(msg, 'error')

    def log_critical(self, msg):
        """Logs a message with a level of 'critical'"""
        self.log_msg(msg, 'critical')

                
class ThreadQueueLog(Thread):
    """A class inheriting Thread, but with an attached QueueLogger and common logging functionality"""
    
    def __init__(self, logqueue):
        Thread.__init__(self)
        self.__logqueue = logqueue
    
    def log_msg_hook(self, msg):
        """
        Implement this in child classes to alter the log message before output.  Useful to prepend a class name
        or identifier for code tracing.
        :param msg: The message to alter
        :return: The message to log
        """
        return msg
    
    def log_msg(self, msg, level='error'):
        """Logs a message"""
        try:
            msg = self.log_msg_hook(str(msg))
            obj = {'msg': str(msg), 'level': str(level)}
            self.__logqueue.put(obj)
        except:
            pass

    def log_debug(self, msg):
        """Logs a message with a level of 'debug'"""
        self.log_msg(msg, 'debug')

    def log_info(self, msg):
        """Logs a message with a level of 'info'"""
        self.log_msg(msg, 'info')

    def log_warning(self, msg):
        """Logs a message with a level of 'warning'"""
        self.log_msg(msg, 'warning')

    def log_error(self, msg):
        """Logs a message with a level of 'error'"""
        self.log_msg(msg, 'error')

    def log_critical(self, msg):
        """Logs a message with a level of 'critical'"""
        self.log_msg(msg, 'critical')
