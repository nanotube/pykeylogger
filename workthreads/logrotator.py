from baseclasses import BaseTimerClass
import logging

class LogRotator(BaseTimerClass):
    '''This will close out the specified handlers, rotate logfiles, then open fresh handlers.'''
    
    def __init__(self, settings, cmdoptions, mainthread, logs_to_rotate, *args, **kwargs):
        ''' takes an extra argument: list of logs_to_rotate, in form of logger names'''
        BaseTimerClass.__init__(self, settings, cmdoptions, mainthread, *args, **kwargs)
        
        self.interval = float(self.settings['Log Maintenance']['Log Rotation Interval'])*60*60
        self.logs_to_rotate = logs_to_rotate
        
        self.task_function = self.rotate_logs

    def rotate_logs(self):
        
        for loggername in loggers_to_rotate:
            logger = logging.getLogger(loggername)
            for handler in logger.handlers:
                try:
                    handler.doRollover()
                except AttributeError:
                    logging.getLogger('').debug("Logger %s, handler %r, is not capable of rollover." % (loggername, handler))
