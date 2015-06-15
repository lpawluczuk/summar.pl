#def flatten(l):
#    v = []
#    for elem in l:
#        v.extend(elem)
#    return v

def flatten_pairs(l):
    for (l1, l2) in l:
        for x, y in zip(l1, l2):
            yield (x, y)

def _stats(pairs, void_label):
    """Return precision, recall, F-measure."""
    tp = 0 # true positives
    fp = 0 # false positives
    tn = 0 # true negatives
    fn = 0 # false negatives

    for x, y in pairs:
        if x == void_label:
            if y == void_label:
                tn = tn + 1
            else:
                fp = fp + 1
        if x != void_label:
            if y == x:
                tp = tp + 1
            else:
                fn = fn + 1
                if y != void_label:
                    fp = fp + 1
    
    prec = rec = 0.0
    if tp + fp != 0: prec = tp / float(tp + fp)
    if tp + fn != 0: rec = tp / float(tp + fn)
    if prec == 0.0 and rec == 0.0:
    	return (0.0, 0.0, 0.0)
    F = (2*prec*rec) / (prec + rec)
    return (prec, rec, F)

def stats(data, tager, void_id):
    """Compute statistics scored with tager on given data."""
    labels_and_tagged = ((labels, tager.tag(sent)) for (sent, labels) in data)
    return _stats(flatten_pairs(labels_and_tagged), void_id)
