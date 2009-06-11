from threading import Thread, Event

class BaseEventClass(Thread):
    '''This is the base class for event-based threads.
    
    Event-based threads are ones that work off keyboard or mouse events.
    In addition to the parameters for timer-based threads, each one gets
    a Queue as an argument from which it pops off events.
    '''
    pass # not implemented yet...
