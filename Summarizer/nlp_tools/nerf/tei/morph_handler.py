'''
Created on 17-03-2011

@author: lennyn
'''

import xml.sax

from ner.data import Segment

XML_NS = 'http://www.w3.org/XML/1998/namespace'

class MorphHandler(xml.sax.ContentHandler):
    '''
    classdocs
    '''

    def __init__(self, queue):
        '''
        Constructor
        '''
        self.queue = queue

        # self.par_id = None
        # self.sent_id = None
        # self.curr_segments = None

        self.seg_id = None
        self.in_segment = False
        self.in_orth = False
        self.in_base = False
        self.in_ctag = False
        self.in_msd = False
        self.in_string = False
        
        self.orth = None
        self.base = None
        self.ctag = None
        self.nps = None
        
        self.id2interp = None
    
    def startElement(self, name, attrs):
        if name == 'p':
            self.par_id = attrs.getValue('xml:id')
        elif name == 's':
            self.curr_segments = []
            self.sent_id = attrs.getValue('xml:id')
        elif name == 'seg':
            self.seg_id = attrs.getValue('xml:id')
            self.id2interp = {}
            self.in_segment = True
            self.nps = False
        elif name == 'f':
            if attrs.getValue('name') == 'choice':
                base, ctag, morph = self.id2interp[attrs.getValue('fVal')[1:]]
                self.curr_segments.append(
                        Segment(self.seg_id, self.orth, base,
                            ctag, morph, self.nps))
            elif attrs.getValue('name') == 'nps':
                self.nps = True
            else:
                if attrs.getValue('name') == 'orth':
                    self.in_orth = True
                    self.orth = ""
                else:
                    self.in_orth = False
                if attrs.getValue('name') == 'base':
                    self.in_base = True
                    self.base = ""
                else:
                    self.in_base = False
                self.in_ctag = attrs.getValue('name') == 'ctag'
                self.in_msd = attrs.getValue('name') == 'msd'
        elif name == 'string':
            self.in_string = True
        elif name == 'symbol':
            if self.in_ctag:
                self.ctag = attrs.getValue('value')
            elif self.in_msd:
                id = attrs.getValue('xml:id')
                self.id2interp[id] = (self.base, self.ctag,
                        attrs.getValue('value'))
    
    def characters(self, content):
        if self.in_base and self.in_string:
            self.base += content.strip()
        elif self.in_orth and self.in_string:
            self.orth += content.strip()
    
    def endElement(self, name):
        if name == 's':
            self.queue.put((self.par_id, self.sent_id, self.curr_segments))
        elif name == 'seg':
            self.in_segment = False
        elif name == 'f':
            self.in_orth = False
            self.in_base = False
            self.in_ctag = False
            self.in_msd = False
        elif name == 'string':
            self.in_string = False

    def endDocument(self):
        self.queue.put(None)
