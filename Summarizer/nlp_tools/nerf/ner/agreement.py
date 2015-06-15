#-*- coding: utf-8 -*-

class Agreement:
    def __init__(self, 
                 ignore_base=True, 
                 ignore_derivType=True,
                 ignore_derivedFrom=True):
        self.ignore_base = ignore_base
        self.ignore_derivType = ignore_derivType
        self.ignore_derivedFrom = ignore_derivedFrom

    def _get_names_num(self, names, predicate):
        res = 0
        for name in names:
            res += self._get_names_num(name.get_child_names(), predicate)
            # if categories is None or name.type in categories:
            if predicate is None or predicate(name):
                res += 1
        return res
    
    def _name2tuple(self, name):
        res = []
        res.append(frozenset([seg.id for seg in name.get_segs()]))
        res.append(name.type)
        res.append(name.subtype)
        if not self.ignore_base:
            res.append(name.base)
        if not self.ignore_derivType:
            res.append(name.derivType)
        if not self.ignore_derivedFrom:
            res.append(name.derivedFrom)
        
        return tuple(res)
    
    def _get_all_names(self, names, predicate):
        res = []
        for name in names:
            # if categories is None or name.type in categories:
            if predicate is None or predicate(name):
                res.append(name)
            res.extend(self._get_all_names(name.get_child_names(), predicate))
        return res
    
    def _names2tuples_multiset(self, names, predicate):
        res = {}
        for name in self._get_all_names(names, predicate):
            name_tuple = self._name2tuple(name)
            res.setdefault(name_tuple, 0)
            res[name_tuple] += 1
        return res

    def _get_names_ok(self, names_test, names_good, predicate):
        res = 0
        ne_test_tuples = self._names2tuples_multiset(names_test, 
                                                     predicate)
        ne_good_tuples = self._names2tuples_multiset(names_good, 
                                                     predicate)
        for test_tuple, _ in ne_test_tuples.iteritems():
            good_count = ne_good_tuples.get(test_tuple, 0)
            res += good_count
        return res
    
    def get_agreement(self, names_test, names_good, predicate=None):
        count_test = self._get_names_num(names_test, predicate)
        count_good = self._get_names_num(names_good, predicate)
        count_ok = self._get_names_ok(names_test, 
                                      names_good, 
                                      predicate)
        return (count_test, count_good, count_ok)
    
