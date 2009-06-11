from baseclasses import BaseTimerClass
import logging

class LogFlusher(BaseTimerClass):
    '''Flushes the log file write buffer to disk.
    
    This is also one of the simplest time-based worker threads, so would
    serve as a good example if you want to write your own.
    '''
    def __init__(self, settings, cmdoptions, mainthread, *args, **kwargs):
        '''Takes two extra arguments: list of logger names to flush, and
        log message string.'''
        BaseTimerClass.__init__(self, settings, cmdoptions, mainthread, *args, **kwargs)
        
        self.interval = self.settings['Log Maintenance']['Flush Interval']
        #self.loggers_to_flush = loggers_to_flush
        
        self.task_function = self.flush_log_write_buffer
        
    def flush_log_write_buffer(self, loggers_to_flush, log_message="Logger %s: flushing file write buffers due to timer."):
        ''' flushes all relevant log buffers.
        
        log_message must contain one string format placeholder '%s'
        to take the logger name. see default argument value for an example.
        '''
        for loggername in loggers_to_flush:
            logger = logging.getLogger(loggername)
            logging.getLogger('').debug("Logger %s: flushing file write buffers due to timer." % loggername)
            for handler in logger.handlers:
                handler.flush()
    

    