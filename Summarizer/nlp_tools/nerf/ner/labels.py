# encoding: utf-8

"""
Translation between a list of labels and a list of named entities (NEs),
where list of NEs represents a collection of NEs trees.
"""

from ..ner.data import NamedEntity, Segment

__all__ = ["decode", "encode", "tuple2label", "label2tuple"]

_last_id = 0

def _get_next_id():
    _last_id += 1
    return 'n_%d' % _last_id

def _get_new_ne_types(ne):
    return [netype.replace('-s', '') for netype in ne if netype.endswith('-s')]

def _get_cont_ne_types(ne):
    return [netype.replace('-c', '') for netype in ne if netype.endswith('-c')]

def _recover_new_ne_types(part_res, cont_ne_types, curr_segid, max_dist,
        id2sent_pos):
    if len(cont_ne_types) == 0:
        return []
    else:
        max_nest = len(cont_ne_types) - 1
        cont_ne = _get_last_ne_of_type(part_res, cont_ne_types[0], max_nest)
        if cont_ne is None or _get_distance(part_res, cont_ne,
                curr_segid, id2sent_pos) > max_dist:
            recovered_nes = [cont_ne_types[0]]
            recovered_nes.extend(_recover_new_ne_types(part_res,
                cont_ne_types[1:], curr_segid, max_dist, id2sent_pos))
            return recovered_nes
        else:
            return []

def _get_new_nes_list(segid, new_ne_types, curr_nes_num, generate_ne_id):
    """
    Returns the list of new named entities (as maps)
    @param segid: current segment id
    @param new_ne_types: list of ne types for current segment suffixed with '-s'
    @param curr_nes_num: number of already found nes - needed in setting ne id
    """
    res = []
    next_ne_num = curr_nes_num + 1
    for ne_name in [ne_name for ne_name in reversed(new_ne_types)]:
        ne_type = ne_name.replace('-s', '')
        if '@' in ne_type:
            deriv_type = ne_type.split('@')[1]
            ne_type = ne_type.split('@')[0]
        else:
            deriv_type = None
        # ne_id = generate_ne_id(sent_id, next_ne_num)
        ne_id = generate_ne_id(next_ne_num)
        next_ne_num += 1
        ne_ptrs = []
        if len(res) != 0:
            res[-1]['ptrs'].append(ne_id)
        new_ne = {'gentype':ne_type, 'id':ne_id, 'ptrs':ne_ptrs}
        if not deriv_type is None:
            new_ne['derivType'] = deriv_type
        res.append(new_ne)

    if len(res) != 0:
        # TODO: Może potrzebna metoda konstrukcji odnosnikow ?
        # Doklejenie "ann_morph..." mozna przeprowadzic w postprocessingu.
        # res[-1]['ptrs'].append('ann_morphosyntax.xml#' + segid)
        res[-1]['ptrs'].append(segid)

    return res

#def generate_ne_id(sentid, ne_num):
#    """
#    Generates ne id with particular number
#    @param sentid: current sentence id
#    @param ne_num: number of the ne
#    """
#    # TODO !
#    return sentid.replace('morph', 'named') + '-n' + str(ne_num)

def _get_last_ne_of_type(part_res, ne_type, max_nest):
    """
    Returns the last ne in part_res with conditions specified
    @param part_res: current result
    @param ne_type: type of ne
    @param max_nest: max nest level for returned ne
    """
    for name in reversed(part_res):
        if name['gentype'] == ne_type and\
                _get_nest_level(part_res, name) <= max_nest:
            return name
    return None

def _get_nest_level(part_res, name):
    for it_name in part_res:
        if _is_child_of(name, it_name):
            return _get_nest_level(part_res, it_name) + 1
    return 0

def _is_child_of(name, parent_name):
    return name['id'] in parent_name['ptrs']

def _first_good_cont(part_res, cont_ne_types, curr_segid, max_dist,
        id2sent_pos):
    """
    Returns first suffixed with '-c' named entity 
    that is in fact continuation of previously started one
    """
    if len(cont_ne_types) == 0:
        return None
    else:
        max_nest = len(cont_ne_types) - 1
        cont_ne = _get_last_ne_of_type(part_res, cont_ne_types[0], max_nest)
        if cont_ne is None or _get_distance(part_res, cont_ne,
                curr_segid, id2sent_pos) > max_dist:
            return _first_good_cont(part_res, cont_ne_types[1:], curr_segid,
                    max_dist, id2sent_pos)
        else:
            return cont_ne

def _get_distance(part_res, ne_type, from_segid, id2sent_pos):
    """
    Returns distance from the last occurrence of ne_type in part_res
    to the segment with id==from_segid
    """
    segid1 = _get_seg_ids(ne_type, part_res)[-1]
    segid2 = from_segid
    return abs(id2sent_pos[segid1] - id2sent_pos[segid2])

def _get_seg_ids(ne, nes_list):
    """Return segment ids related to ne named entity.

    :params:
    --------
    nes_list : list of all named entities.
    seg_ids : list of ids of all segments.
    """
    res = []
    for ptr in ne['ptrs']:
        nested_ne = [ne for ne in nes_list if ne['id'] == ptr]
        if len(nested_ne) == 0:
            res.append(ptr)
        else:
            res.extend(_get_seg_ids(nested_ne[0], nes_list))
    return res

def _postprocess_ne_types(nes_list):
    for ne in nes_list:
        oldtype = ne['gentype']
        if "." in oldtype:
            basetype = oldtype.split('.')[0]
            subtype = oldtype.split('.')[1]
        else:
            subtype = None
            basetype = oldtype
        ne['type'] = basetype
        ne['subtype'] = subtype
        del ne['gentype']

def _dict2name(name_dict, entities_dict):
    return NamedEntity(
                id=name_dict['id'],
                type=name_dict['type'],
                subtype=name_dict['subtype'],
                derivType=name_dict.get('derivType', None),
                ptrs=list(map(
                              lambda id: entities_dict[id], 
                              name_dict['ptrs'])))

def _retain_only_root_names(res):
    names_to_remove = set()
    for name in res:
        for desc_name in name.get_descendant_names():
            names_to_remove.add(desc_name)
    return [name for name in res if name not in names_to_remove]

def _sort_names_and_segs_key(e, segs):
    if isinstance(e, Segment):
        return (segs.index(e), 0)
    else:
        min_seg_idx, _ = \
            min([_sort_names_and_segs_key(ptr, segs) for ptr in e.ptrs])
        return (min_seg_idx, len(e.get_descendant_names()))

def _sort_names_and_segs(names, segs):
    names.sort(key=lambda name: _sort_names_and_segs_key(name, segs))
    for name in names:
        name.ptrs.sort(key=lambda name: _sort_names_and_segs_key(name, segs))

def dicts2names(names_dicts, segs):
    res = []
    entities_dict = {}
    
    for seg in segs:
        entities_dict[seg.id] = seg
    
    for name_dict in reversed(names_dicts):
        named_entity = _dict2name(name_dict, entities_dict)
        res.insert(0, named_entity)
        entities_dict[name_dict['id']] = named_entity
    res = _retain_only_root_names(res)
    _sort_names_and_segs(res, segs)
    return res

def decode(labels, segs, generate_ne_id=lambda k: "n_" + str(k),
        recover_not_started=False, max_dist=float('+infinity')):
    """Translate a list of labels in a sentence to a list of NEs.

    :params:
    --------
    labels :
        Labels in a sentence.
    segs :
        All segments in a sentence.
    generate_ne_id :
        Method of a new named entities ids generation.
    recover_not_started :
        If True, treat not started '-c' labels as '-s'. Otherwise ignore them.
    max_dist :
        Indicates how far from the rest of the name the '-c' name parts can be.
    """
    nes_list = []
    
    seg_ids = map(lambda seg: seg.id, segs)

    id2sent_pos = dict((seg_id, i) for i, seg_id in enumerate(seg_ids))
    for segid, label in zip(seg_ids, labels):
        new_ne_types = _get_new_ne_types(label)
        cont_ne_types = _get_cont_ne_types(label)

        if recover_not_started:
            new_ne_types.extend(_recover_new_ne_types(nes_list, cont_ne_types,
                segid, max_dist, id2sent_pos))

        new_nes = _get_new_nes_list(segid, new_ne_types, len(nes_list),
                generate_ne_id)
        cont_ne = _first_good_cont(nes_list, cont_ne_types, segid, max_dist,
                id2sent_pos)
        if not cont_ne is None:
            if len(new_nes) > 0:
                cont_ne['ptrs'].append(new_nes[0]['id'])
            else:
                # cont_ne['ptrs'].append('ann_morphosyntax.xml#' + segid)
                cont_ne['ptrs'].append(segid)

        nes_list.extend(new_nes)
    _postprocess_ne_types(nes_list)
    return dicts2names(nes_list, segs)

def _name2labels_dict(name):
    upper_dict = {}
    segs = name.get_segs()
    upper_dict[segs[0]] = ['%s-s' % name.get_label()]
    lower_dict = {}
    for seg in segs[1:]:
        upper_dict[seg] = ['%s-c' % name.get_label()]
    for subname in filter(lambda ptr: isinstance(ptr, NamedEntity), name.ptrs):
        lower_dict.update(_name2labels_dict(subname))
    
    for seg, labels_list in lower_dict.iteritems():
        upper_labels_list = upper_dict[seg]
        upper_dict[seg] = labels_list + upper_labels_list
    return upper_dict
        

def encode(names, segs):
    """Translate a list of NEs a sentence to a list of labels."""
    seg2labels = {}
    for name in names:
        seg2labels.update(_name2labels_dict(name))
    return [tuple(seg2labels.get(seg, [])) for seg in segs]

def tuple2label(label):
    if len(label) == 0:
        return 'O'
    return "NE_" + '#'.join(label)

def label2tuple(lstr):
    if lstr == 'O':
        return ()
    return tuple(lstr.lstrip("NE_").split("#"))

if __name__ == "__main__":
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)

