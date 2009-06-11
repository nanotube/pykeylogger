from threading import Thread, Event
import logging
import time
import re

class BaseTimerClass(Thread):
    '''This is the base class for timer (delay) based threads.
    
    Timer-based threads are ones that do not need to be looking at
    keyboard-mouse events to do their job.
    '''
    def __init__(self, settings, cmdoptions, mainthread, *args, **kwargs):
        Thread.__init__(self)
        self.finished = Event()
        
        self.settings = settings # settings dict
        self.cmdoptions = cmdoptions # cli options dict
        self.mainthread = mainthread # reference to main thread
        self.args = args # arguments, if any, to pass to task_function
        self.kwargs = kwargs # keyword args, if any, to pass to task_function
        
        self.interval = None # set this in derived class
        
    def cancel(self):
        '''Stop the iteration'''
        self.finished.set()
    
    def task_function(self):
        '''to be overridden by derived classes'''
        pass
    
    def run(self):
        while not self.finished.isSet():
            self.finished.wait(self.interval)
            if not self.finished.isSet():
                self.task_function(*self.args, **self.kwargs)
                
        self.finished.set() # just in case :)

        
class LogRotator(BaseTimerClass):
    '''This rotates the logfiles for the specified loggers.
    
    This is also one of the simplest time-based worker threads, so would
    serve as a good example if you want to write your own.
    '''
    
    def __init__(self, *args, **kwargs):
        '''Takes an extra argument: loggers_to_rotate, a list names.'''
        BaseTimerClass.__init__(self, *args, **kwargs)
        
        self.interval = \
            float(self.settings['Log Maintenance']['Log Rotation Interval'])*60*60
        
        self.task_function = self.rotate_logs

    def rotate_logs(self, loggers_to_rotate):
        
        for loggername in loggers_to_rotate:
            logger = logging.getLogger(loggername)
            for handler in logger.handlers:
                try:
                    handler.doRollover()
                except AttributeError:
                    logging.getLogger('').debug("Logger %s, handler %r, "
                        "is not capable of rollover." % (loggername, handler))

        
class LogFlusher(BaseTimerClass):
    '''Flushes the logfile write buffers to disk for the specified loggers.'''
    def __init__(self, *args, **kwargs):
        '''Takes two extra arguments: list of logger names to flush, and
        log message string.'''
        BaseTimerClass.__init__(self, *args, **kwargs)
        
        self.interval = self.settings['Log Maintenance']['Flush Interval']
        #self.loggers_to_flush = loggers_to_flush
        
        self.task_function = self.flush_log_write_buffer
        
    def flush_log_write_buffer(self, loggers_to_flush, 
            log_message="Logger %s: flushing file write buffers with timer."):
        '''Flushes all relevant log buffers.
        
        log_message must contain one string format placeholder '%s'
        to take the logger name. See default argument value for an example.
        This string is customizable so that manual flushing can use a 
        different message.
        '''
        for loggername in loggers_to_flush:
            logger = logging.getLogger(loggername)
            logging.getLogger('').debug("Logger %s: flushing file write "
                        "buffers due to timer." % loggername)
            for handler in logger.handlers:
                handler.flush()

class OldLogDeleter(BaseTimerClass):
    '''Deletes old logs.
    
    Walks the log directory tree and removes old logfiles.

    Age of logs to delete is specified in .ini file settings.
    '''
    def __init__(self, *args, **kwargs):
        '''Takes an extra argument: list of base log names work on.'''
        BaseTimerClass.__init__(self, *args, **kwargs)
        
        self.interval = float(self.settings['Log Maintenance']['Age Check Interval'])*60*60
        #self.loggers_to_flush = loggers_to_flush
        
        self.task_function = self.delete_old_logs

    def delete_old_logs(self, list_of_filenames):
        logdir = self.settings['General']['Log Directory']
        max_log_age = float(self.settings['Log Maintenance']['Max Log Age'])*24*60*60
        filename_re = re.compile(r'(' + r'|'.join(list_of_filenames) + r')')
        for dirpath, dirnames, filenames in os.walk(logdir):
            for fname in filenames:
                if filename_re.search(fname):
                    filepath = os.path.join(dirpath, fname)
                    testvalue = time.time() - os.path.getmtime(filepath) > max_log_age
                
                if testvalue:
                    try:
                        os.remove(filepath)
                    except:
                        logging.getLogger('').debug("Error deleting old log "
                        "file: %s" % filepath)



        
if __name__ == '__main__':
    # some basic testing code
    class TestTimerClass(BaseTimerClass):
        def __init__(self, *args, **kwargs):
            BaseTimerClass.__init__(self, *args, **kwargs)
            self.interval = 1
            
            self.task_function = self.print_hello
        
        def print_hello(self, name='bob', *args):
            print "hello, %s" % name
            print args
            
    ttc = TestTimerClass('some stuff','more stuff','even more stuff', 'myname', 'some other name')
    ttc.start()
    time.sleep(5)
    ttc.cancel()
