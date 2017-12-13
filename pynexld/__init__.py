#!/usr/bin/env python
from __future__ import print_function, division
from xml.etree import ElementTree as ET
import json
import sys

def add_meta_to_obj(meta_el, curr_obj):
    subatt = meta_el.attrib
    sat = subatt['{http://www.w3.org/2001/XMLSchema-instance}type']
    if sat == 'ResourceMeta':
        prop_name = subatt['rel']
        val = subatt['href']
    elif sat in {'LiteralMeta', 'nex:LiteralMeta'}:
        prop_name = subatt['property']
        val = subatt['content']
    else:
        raise NotImplementedError('meta with type "{}"'.format(sat))
    if prop_name in curr_obj:
        prev = curr_obj[prop_name]
        if isinstance(prev, list):
            prev.append(val)
        else:
            curr_obj[prop_name] = [prev, val]
    else:
        curr_obj[prop_name] = val

_raw_rep_tags = ['meta', 'otu', 'node', 'tree', 'edge']
_ns_rep_tags = ['{}{}'.format('{http://www.nexml.org/2009}', i) for i in _raw_rep_tags]
_repeatable_nex_tags_list = _raw_rep_tags + _ns_rep_tags
_REPEATABLE_NEX_EL = frozenset(_repeatable_nex_tags_list)

def new_sub_obj(parent, child, par_dict):
    sub_etag = child.tag
    targ_obj = par_dict.get(sub_etag)
    nso = {}
    nso['@type'] = sub_etag
    for k, v in child.attrib.items():
        if k == 'id':
            nso['@id'] = v
        else:
            nso[k] = v
    if targ_obj is None:
        if sub_etag in _REPEATABLE_NEX_EL:
            targ_obj = [nso]
            par_dict[sub_etag] = targ_obj
        else:
            par_dict[sub_etag] = nso
    else:
        if sub_etag not in _REPEATABLE_NEX_EL:
            raise ValueError('Did not expect a repeated "{}" element'.format(sub_etag))
        targ_obj.append(nso)
    return nso


def flatten_into_dict(el, curr_obj):
    for sub in el:
        if sub.tag == '{http://www.nexml.org/2009}meta':
            add_meta_to_obj(sub, curr_obj)
        else:
            sd = new_sub_obj(el, sub, curr_obj)
            flatten_into_dict(sub, sd)
            #print('sub attrib={} tag={}'.format(sub.attrib, sub.tag))

def nexml_to_json_ld(path):
    tree = ET.parse(path)
    r = tree.getroot()
    d = {}
    nexml_dict = {}
    d[r.tag] = nexml_dict
    flatten_into_dict(r, nexml_dict)
    return d

if __name__ == '__main__':
    for fn in sys.argv[1:]:
        print(json.dumps(nexml_to_json_ld(fn), indent=2, sort_keys=True))
