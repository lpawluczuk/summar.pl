# encoding: utf-8

def filternone(l):
    return filter(lambda x: x != None, l)

def sentence(sent, alph):
    return [(filternone([alph.observation(x) for x in singles]),
        filternone([alph.observation(x) for x in pairs]))
        for singles, pairs in sent]

def labels(labels, alph):
    return [alph.label(x) for x in labels]
