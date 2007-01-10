import zlib
import base64

def password_obfuscate(password):
    return base64.b64encode(zlib.compress(password))
def password_recover(password):
    return zlib.decompress(base64.b64decode(password))




#~ if __name__ == '__main__':
    #some test code here. 
    #~ def hello(name="bla"):
        #~ print "hello, ", name

    #~ myt = MyTimer(1.0, 5, hello, ["bob"])
    #~ myt.start()
    #~ time.sleep(4)
    #~ myt.cancel()
    #~ print "next timer"
    #~ myt = MyTimer(1.0, 0, hello, ["bob"])
    #~ myt.start()
    #~ time.sleep(6)
    #~ myt.cancel()
