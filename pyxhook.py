#!/usr/bin/python
#
# $Id: pyxhook.py,v 1.1.2.3 2008/03/07 04:38:22 nanotube Exp $
#f
# pyxhook -- an extension to emulate some of the PyHook library on linux.
#
#    Copyright (C) 2008 Tim Alexander <dragonfyre13@gmail.com>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#    Thanks to Alex Badea <vamposdecampos@gmail.com> for writing the Record
#    demo for the xlib libraries. It helped me immensely working with these
#    in this library.
#
#    Thanks to the python-xlib team. This wouldn't have been possible without
#    your code.
#    
#    This requires: 
#    at least python-xlib 1.4
#    xwindows must have the "record" extension present, and active.

import sys
import os
import re
import time
import threading
import Image

from Xlib import X, XK, display, error
from Xlib.ext import record
from Xlib.protocol import rq

#######################################################################
########################START CLASS DEF################################
#######################################################################

class pyxhook(threading.Thread):
    """This is the main class. Instantiate it, and you can hand it KeyDown and KeyUp (functions in your own code) which execute to parse the pyxhookkeyevent class that is returned.

    This simply takes these two values for now:
    KeyDown = The function to execute when a key is pressed, if it returns anything. It hands the function an argument that is the pyxhookkeyevent class.
    KeyUp = The function to execute when a key is released, if it returns anything. It hands the function an argument that is the pyxhookkeyevent class.
    """

    def printevent(event):
        print event

    def __init__(self, captureclicks = True, clickimagedimensions = {"width":150, "height":150}, logdir = ".", KeyDown = printevent, KeyUp = printevent):
        threading.Thread.__init__(self)
        self.finished = threading.Event()
        
        # Give these some initial values
        self.rootx = 0
        self.rooty = 0
        self.ison = {"shift":False, "caps":False}
        
        # Compile our regex statements.
        self.isshift = re.compile('^Shift')
        self.iscaps = re.compile('^Caps_Lock')
        self.shiftablechar = re.compile('^[a-z0-9]$|^minus$|^equal$|^bracketleft$|^bracketright$|^semicolon$|^backslash$|^apostrophe$|^comma$|^period$|^slash$|^grave$')
        self.logrelease = re.compile('.*')
        self.isspace = re.compile('^space$')
        
        # Assign what we got from being passed in.
        self.KeyDown = KeyDown
        self.KeyUp = KeyUp
        self.captureclicks = captureclicks
        self.image = clickimagedimensions
        self.logdir = logdir
        
        # Hook to our display.
        self.local_dpy = display.Display()
        self.record_dpy = display.Display()
        
        #Make sure the image directory is there. If not, create it.
        self.imagedir = os.path.join(self.logdir, "images")
        originalDir = os.getcwd()
        os.chdir(self.logdir)
        try:
            os.makedirs("images", 0777) 
        except OSError, detail:
            if(detail.errno==17): pass
            else: print "error creating click image directory"
        except: print "error creating click image directory"
        os.chdir(originalDir)

    def run(self):
        # Check if the extension is present
        if not self.record_dpy.has_extension("RECORD"):
            print "RECORD extension not found"
            sys.exit(1)
        r = self.record_dpy.record_get_version(0, 0)
        print "RECORD extension version %d.%d" % (r.major_version, r.minor_version)

        # Create a recording context; we only want key and mouse events
        self.ctx = self.record_dpy.record_create_context(
                0,
                [record.AllClients],
                [{
                        'core_requests': (0, 0),
                        'core_replies': (0, 0),
                        'ext_requests': (0, 0, 0, 0),
                        'ext_replies': (0, 0, 0, 0),
                        'delivered_events': (0, 0),
                        'device_events': (X.KeyPress, X.ButtonPress),
                        'errors': (0, 0),
                        'client_started': False,
                        'client_died': False,
                }])

        # Enable the context; this only returns after a call to record_disable_context,
        # while calling the callback function in the meantime
        self.record_dpy.record_enable_context(self.ctx, self.processevents)
        # Finally free the context
        self.record_dpy.record_free_context(self.ctx)

    def cancel(self):
        self.finished.set()
        self.local_dpy.record_disable_context(self.ctx)
        self.local_dpy.flush()

    def processevents(self, reply):
        if reply.category != record.FromServer:
            return
        if reply.client_swapped:
            print "* received swapped protocol data, cowardly ignored"
            return
        if not len(reply.data) or ord(reply.data[0]) < 2:
            # not an event
            return
        data = reply.data
        while len(data):
            event, data = rq.EventField(None).parse_binary_value(data, self.record_dpy.display, None, None)
            if event.type == X.KeyPress:
                keydownevent = self.keypressevent(event)
                if keydownevent != -1:
                    self.KeyDown(keydownevent)
            elif event.type == X.KeyRelease:
                keyupevent = self.keyreleaseevent(event)
                if keyupevent != -1:
                    self.KeyUp(keyupevent)
            if self.captureclicks == True:
                if event.type == X.ButtonPress:
                    self.buttonpressevent(event)
                elif event.type == X.ButtonRelease:
                    self.buttonreleaseevent(event)
                #~ elif event.type == X.MotionNotify:
                    #~ self.mousemoveevent(event)
        
        #~ if self.finished.isSet():
            #~ self.record_dpy.record_disable_context(self.ctx)
            #~ self.record_dpy.flush()
            #~ return
        
        print "processing events..."

    def keypressevent(self, event):
        matchto = self.lookup_keysym(self.local_dpy.keycode_to_keysym(event.detail, 0))
        if self.shiftablechar.match(self.lookup_keysym(self.local_dpy.keycode_to_keysym(event.detail, 0))): ## This is a character that can be typed.
            if self.ison["shift"] == False:
                keysym = self.local_dpy.keycode_to_keysym(event.detail, 0)
                return self.makekeyhookevent(keysym, event)
            else:
                keysym = self.local_dpy.keycode_to_keysym(event.detail, 1)
                return self.makekeyhookevent(keysym, event)
        else: ## Not a typable character.
            keysym = self.local_dpy.keycode_to_keysym(event.detail, 0)
            if self.isshift.match(matchto):
                self.ison["shift"] = self.ison["shift"] + 1
                return -1
            elif self.iscaps.match(matchto):
                if self.ison["caps"] == False:
                    self.ison["shift"] = self.ison["shift"] + 1
                    self.ison["caps"] = True
                if self.ison["caps"] == True:
                    self.ison["shift"] = self.ison["shift"] - 1
                    self.ison["caps"] = False
                return -1
            elif self.logrelease.match(matchto):
                return self.makekeyhookevent(keysym, event)
            else:
                if self.isspace.match(matchto):
                    return self.makekeyhookevent(keysym, event)
                else:
                    return self.makekeyhookevent(keysym, event)
    
    def keyreleaseevent(self, event):
        if self.shiftablechar.match(self.lookup_keysym(self.local_dpy.keycode_to_keysym(event.detail, 0))):
            if self.ison["shift"] == False:
                keysym = self.local_dpy.keycode_to_keysym(event.detail, 0)
            else:
                keysym = self.local_dpy.keycode_to_keysym(event.detail, 1)
        else:
            keysym = self.local_dpy.keycode_to_keysym(event.detail, 0)
        matchto = self.lookup_keysym(keysym)
        if self.isshift.match(matchto):
            self.ison["shift"] = self.ison["shift"] - 1
            return -1
        elif self.logrelease.match(matchto):
            return self.makekeyhookevent(keysym, event)
        else:
            return -1

    def buttonpressevent(self, event):
            self.clickx = self.rootx
            self.clicky = self.rooty

    def buttonreleaseevent(self, event):
        if (self.clickx == self.rootx) and (self.clicky == self.rooty):
            #print "ButtonClick " + str(event.detail) + " x=" + str(self.rootx) + " y=" + str(self.rooty)
            if (event.detail == 1) or (event.detail == 2) or (event.detail == 3):
                self.captureclick()
        else:
            pass
        #    sys.stdout.write("ButtonDown " + str(event.detail) + " x=" + str(self.clickx) + " y=" + str(self.clicky) + "\n")
        #    sys.stdout.write("ButtonUp " + str(event.detail) + " x=" + str(self.rootx) + " y=" + str(self.rooty) + "\n")
        #sys.stdout.flush()

    def mousemoveevent(self, event):
        self.rootx = event.root_x
        self.rooty = event.root_y

    def lookup_keysym(self, keysym):
        for name in dir(XK):
            if name[:3] == "XK_" and getattr(XK, name) == keysym:
                return name[3:]
        return "[%d]" % keysym

    def asciivalue(self, keysym):
        asciinum = XK.string_to_keysym(self.lookup_keysym(keysym))
        if asciinum < 256:
            return asciinum
        else:
            return 0
    
    def makekeyhookevent(self, keysym, event):
        storewm = self.xwindowinfo()
        if event.type == X.KeyPress:
            MessageName = "key down"
        elif event.type == X.KeyRelease:
            MessageName = "key up"
        elif event.type == X.ButtonPress:
            if event.detail == 1:
                MessageName = "mouse left down"
            elif event.detail == 2:
                MessageName = "mouse right down"
            elif event.detail == 3:
                MessageName = "mouse middle down"
        elif event.type == X.ButtonRelease:
            if event.detail == 1:
                MessageName = "mouse left up"
            elif event.detail == 2:
                MessageName = "mouse right up"
            elif event.detail == 3:
                MessageName = "mouse middle up"
        return pyxhookkeyevent(storewm["name"], storewm["handle"], storewm["class"], self.lookup_keysym(keysym), self.asciivalue(keysym), False, event.detail, MessageName)
    
    def xwindowinfo(self):
        try:
            windowvar = self.local_dpy.get_input_focus().focus
            wmname = windowvar.get_wm_name()
            wmclass = windowvar.get_wm_class()
            wmhandle = str(windowvar)[20:30]
        except:
            ## This is to keep things running smoothly. It almost never happens, but still...
            return {"name":None, "class":None, "handle":None}
        if (wmname == None) and (wmclass == None):
            try:
                windowvar = windowvar.query_tree().parent
                wmname = windowvar.get_wm_name()
                wmclass = windowvar.get_wm_class()
                wmhandle = str(windowvar)[20:30]
            except:
                ## This is to keep things running smoothly. It almost never happens, but still...
                return {"name":None, "class":None, "handle":None}
        if wmclass == None:
            return {"name":wmname, "class":wmclass, "handle":wmhandle}
        else:
            return {"name":wmname, "class":wmclass[0], "handle":wmhandle}
    
    def capturewindow(self, Window = None, start_x = 0, start_y = 0, width = None, height = None, saveto = "image.png"):
        # This is a work in progress.
        AllPlanes = ~0
        if Window == None:
            Window = self.local_dpy.get_input_focus().focus
            
            if Window == 0:
                print "Could not get active window."
                return 1
            
            ## Handle the possiblity that this window is a sub-class of the above window, only used to log the time the last user event occured.
            ## It's expected that, if needed, this will be handled outside the method if Window is not None coming into the method.
            if Window.get_wm_name() == None:
                Window = Window.query_tree().parent

        
        if (width == None) and (height == None):
            geom = Window.get_geometry()
            height = geom.height
            width = geom.width
        
        try:
            raw = Window.get_image(start_x, start_y, width, height, X.ZPixmap, AllPlanes)
            Image.fromstring("RGBX", (width, height), raw.data, "raw", "BGRX").convert("RGB").save(saveto)
            return 0
        except error.BadDrawable:
            print "bad drawable when attempting to get an image!  Closed the window?"
        except error.BadMatch:
            print "bad match when attempting to get an image! probably specified an area outside the window (too big?)"
        except error.BadValue:
            print "getimage: bad value error - tell me about this one, I've not managed to make it happen yet"
        except:
            print "Undefined error. Sorry."
     
    def captureclick(self):
        rootwin = self.local_dpy.get_input_focus().focus.query_tree().root
        if rootwin == 0:
            rootwin = self.local_dpy.get_input_focus()
        maxx = rootwin.get_geometry().width
        maxy = rootwin.get_geometry().height

        ## See if the bounds to capture are off the screen. If they are, set them to the max on screen amount.
        if self.rootx - (self.image["width"] / 2) < 0:
            print "clipping xcoord bounds"
            xcoord = 0
        else: xcoord = self.rootx - (self.image["width"] / 2)
        
        if self.rooty - (self.image["height"] / 2) < 0:
            print "clipping ycoord bounds"
            ycoord = 0
        else: ycoord = self.rooty - (self.image["height"] / 2)
        
        if xcoord + self.image["width"] > maxx:
            print "clipping xrange bounds"
            rangex = maxx - xcoord
        else: rangex = self.image["width"]
        
        if ycoord + self.image["height"] > maxy:
            print "clipping yrange bounds"
            rangey = maxy - ycoord
        else: rangey = self.image["height"]
        
        print os.path.join(self.imagedir, "click-" + str(time.time()) + "-" + str(self.xwindowinfo()["class"]) + ".png")
        
        try:
            self.capturewindow(rootwin, xcoord, ycoord, rangex, rangey, os.path.join(self.imagedir, "click-" + str(time.time()) + "-" + str(self.xwindowinfo()["class"]) + ".png"))
        except:
            print "Encountered an error capturing the image for the window. Continuing anyway."
         
class pyxhookkeyevent:
    """This is the class that is returned with each key event.f
    It simply creates the variables below in the class.
    
    Window = The name of the window.
    WindowName = The handle of the window.
    WindowProcName = The backend process for the window.
    Key = The key pressed, shifted to the correct caps value.
    Ascii = An ascii representation of the key. It returns 0 if the ascii value is not between 31 and 256.
    KeyID = This is just False for now. Dunno what I need here.
    ScanCode = Please don't use this. It differs for pretty much every type of keyboard. X11 abstracts this information anyway.
    MessageName = "key down", "key up" for keyboard, "mouse left|right|middle down", "mouse left|right|middle up" for mouse.
    """
    
    def __init__(self, Window, WindowName, WindowProcName, Key, Ascii, KeyID, ScanCode, MessageName):
        self.Window         = Window
        self.WindowName     = WindowName
        self.WindowProcName = WindowProcName
        self.Key            = Key
        self.Ascii          = Ascii
        self.KeyID          = KeyID
        self.ScanCode       = ScanCode
        self.MessageName = MessageName
    
    def __str__(self):
        return "Window: " + str(self.Window) + "\nWindow Handle: " + str(self.WindowName) + "\nWindow's Process Name: " + str(self.WindowProcName) + "\nKey Pressed: " + str(self.Key) + "\nAscii Value: " + str(self.Ascii) + "\nKeyID: " + str(self.KeyID) + "\nScanCode: " + str(self.ScanCode) + "\nMessageName: " + str(self.MessageName) + "\n"
    
    
#######################################################################
#########################END CLASS DEF#################################
#######################################################################
    
if __name__ == '__main__':
    hm = pyxhook()
    hm.start()
    time.sleep(10)
    hm.cancel()
