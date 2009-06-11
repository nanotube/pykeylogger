from threading import Thread, Event

class BaseTimerClass(Thread):
    '''This is the base class for timer (delay) based threads.
    
    Timer-based threads are ones that do not need to be looking at
    keyboard-mouse events to do their job.
    '''
    def __init__(self, settings, cmdoptions, mainthread, args=[], kwargs={}):
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

class BaseEventClass(Thread):
    '''This is the base class for event-based threads.
    
    Event-based threads are ones that work off keyboard or mouse events.
    In addition to the parameters for timer-based threads, each one gets
    a Queue as an argument from which it pops off events.
    '''
    pass # not implemented yet...
    
    
if __name__ == '__main__':
    # some basic testing code
    class TestTimerClass(BaseTimerClass):
        def __init__(self, *args, **kwargs):
            BaseTimerClass.__init__(self, *args, **kwargs)
            self.interval = 2
            
            self.task_function = self.print_hello
        
        def print_hello(self):
            print "hello"
            
    ttc = TestTimerClass('some stuff','more stuff','even more stuff')
    ttc.start()
    time.sleep(10)
    ttc.cancel()