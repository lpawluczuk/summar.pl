'''
Created on 17-03-2011

@author: lennyn
'''
import xml.sax
from ner.labels import dicts2names
from ner.data import NamedEntity

class NamesHandler(xml.sax.ContentHandler):
    '''
    classdocs
    '''


    def __init__(self, queue):
        '''
        Constructor
        '''
        self.queue = queue
        self.curr_names = None
        
        self.fname = None
        self.in_string = False
        
        self.ne_id = None
        self.type = None
        self.subtype = None
        self.derivType = None
        self.derivedFrom = None
        self.ptrs = None
        
        self.id2interp = None
    
    def startElement(self, name, attrs):
        if name == 's':
            self.curr_names = []
        elif name == 'seg':
            self.ne_id = attrs.getValue('xml:id')
            self.type = None
            self.subtype = None
            self.derivedFrom = None
            self.derivType = None
            self.ptrs = []
        elif name == 'f':
            self.fname = attrs.getValue('name')
        elif name == 'string':
            self.in_string = True
        elif name == 'symbol':
            if self.fname == 'derivType':
                self.derivType = attrs.getValue('value')
            elif self.fname == 'type':
                self.type = attrs.getValue('value')
            elif self.fname == 'subtype':
                self.subtype = attrs.getValue('value')
        elif name == 'ptr':
            self.ptrs.append(attrs.getValue('target').split('#')[-1])
    
    def endElement(self, name):
        if name == 's':
            self.queue.put(self.curr_names)
        elif name == 'seg':
            self.curr_names.append({
                            'id' : self.ne_id,
                            'type' : self.type,
                            'subtype' : self.subtype,
                            'ptrs' : self.ptrs,
                            'derivType' : self.derivType,
                            'derivedFrom' : self.derivedFrom,
                            })
    
    def characters(self, content):
        if self.in_string:
            if self.fname == 'derivedFrom':
                self.derivedFrom = content.strip()
    
    def endDocument(self):
        self.queue.put(None)
