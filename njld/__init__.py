#!/usr/bin/env python
from __future__ import print_function, division
from xml.etree import ElementTree as ET
import sys

def add_meta_to_obj(meta_el, curr_obj):
    subatt = meta_el.attrib
    sat = subatt['{http://www.w3.org/2001/XMLSchema-instance}type']
    if sat == 'ResourceMeta':
        prop_name = subatt['rel']
        val = subatt['href']
    elif sat == 'LiteralMeta':
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


def flatten_into_dict(el, d, curr_obj):
    for sub in el:
        if sub.tag == '{http://www.nexml.org/2009}meta':
            add_meta_to_obj(sub, curr_obj)
        else:
            print('sub attrib={} tag={}'.format(sub.attrib, sub.tag))

def nexml_to_json_ld(path):
    tree = ET.parse(path)
    r = tree.getroot()
    d = {}
    nexml_dict = {}
    d[r.tag] = nexml_dict
    flatten_into_dict(r, d, nexml_dict)

if __name__ == '__main__':
    for fn in sys.argv[1:]:
        nexml_to_json_ld(fn)
