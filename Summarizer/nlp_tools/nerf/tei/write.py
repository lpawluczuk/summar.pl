import gzip
import os

from xml.sax.saxutils import escape

__all__ = ["TEIWriter", "write"]
    
def _writeProlog(out):
    out.write("""<?xml version="1.0" encoding="UTF-8"?>
<teiCorpus xmlns:xi="http://www.w3.org/2001/XInclude" xmlns="http://www.tei-c.org/ns/1.0">
 <xi:include href="NKJP_1M_header.xml"/>
 <TEI>
  <xi:include href="header.xml"/>
  <text xml:lang="pl">
   <body>""")
 
def _writeEpilogue(out):
    out.write("""</body>
  </text>
 </TEI>
</teiCorpus>
""")

def _ptr2target(id):
    if id.startswith('morph'):
        return 'ann_morphosyntax.xml#%s' % id
    else:
        return id

def _writeNE(out, ne):
#    print "NE:", ne.id, ne.type, ne.subtype,\
#            ne.base, ne.derivType, ne.derivedFrom
    out.write("""
     <seg xml:id="%s">
      <fs type="named">
       <f name="type">
        <symbol value="%s"/>
       </f>""" % (ne.id, ne.type))
    if ne.subtype is not None:
        out.write("""
       <f name="subtype">
        <symbol value="%s"/>
       </f>""" % ne.subtype)
    if ne.derivType is not None:
        out.write("""
       <f name="derived">
        <fs type="derivation">
         <f name="derivType">
          <symbol value="%s"/>
         </f>""" % ne.derivType)
        if ne.derivedFrom is not None:
            out.write("""
         <f name="derivedFrom">
          <string>%s</string>
         </f>""" % escape(derivedFrom).encode('utf-8'))
        out.write("""
        </fs>
       </f>""")

#        derivedFrom = "" if ne.derivedFrom is None else ne.derivedFrom 
#        out.write("""
#       <f name="derived">
#        <fs type="derivation">
#         <f name="derivType">
#          <symbol value="%s"/>
#         </f>
#         <f name="derivedFrom">
#          <string>%s</string>
#         </f>
#        </fs>
#       </f>""" % (ne.derivType, escape(derivedFrom).encode('utf-8')))
    out.write("""
       <f name="orth">
        <string>%s</string>
       </f>""" % escape(ne.orth).encode('utf-8'))
    out.write("""
      </fs>""")
    for ptr in ne.ptrs:
        out.write("""
      <ptr target="%s"/>""" % _ptr2target(ptr.id))
    out.write("""
     </seg>""")

def _correct_ne_ids(named_sent_id, all_names):
    for i, ne in enumerate(all_names, start=1):
        ne.id = '%s_n%d' % (named_sent_id, i)
        # print ne.id

def _writeSent(out, named_sent_id, sent_id, names_list):
    all_names = reduce(lambda names1, names2: names1 + names2,
                       map(lambda name: name.get_descendant_names_and_self(), 
                           names_list))
    out.write("""
    <s xml:id="%s" corresp="ann_morphosyntax.xml#%s">""" 
                % (named_sent_id, sent_id))
    _correct_ne_ids(named_sent_id, all_names)
    for ne in all_names:
        _writeNE(out, ne)
    out.write("""
    </s>""")

def _writeEmptySent(out, named_sent_id, sent_id):
    out.write("""
    <s xml:id="%s" corresp="ann_morphosyntax.xml#%s"/>""" 
                % (named_sent_id, sent_id))

def _writeParagraph(out, par_id, contents):
    out.write("""
   <p xml:id="%s" corresp="ann_morphosyntax.xml#%s">"""
             % (par_id.replace('morph', 'named'), par_id))
    for sent_id, sent_names in contents:
        named_sent_id = sent_id.replace('morph', 'named')
        if sent_names != []:
            _writeSent(out, named_sent_id, sent_id, sent_names)
        else:
            _writeEmptySent(out, named_sent_id, sent_id)
    #print 'written:', par_id.replace('morph', 'named')
    out.write("""
   </p>""")
    
def write(out, paragraphs):
    _writeProlog(out)
    for par_id, contents in paragraphs:
        _writeParagraph(out, par_id, contents)
    _writeEpilogue(out)
