#!/usr/bin/env python
from __future__ import print_function, division
from xml.etree import ElementTree
import json
import sys

VERBOSE = True

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
del _repeatable_nex_tags_list
del _ns_rep_tags
del _raw_rep_tags

_CONVENTIONAL_URL_SHORTENINGS = {'http://www.nexml.org/2009': 'nex',
                                 }
def _url_prefix_to_short(url_pref):
    return _CONVENTIONAL_URL_SHORTENINGS.get(url_pref)

def debug(msg):
    if VERBOSE:
        sys.stderr.write('pynexld: {}\n'.format(msg))

def _xml_ns_name_to_short(s, context_mappings):
    debug('to short "{}"'.format(s))
    sp = s.split('}')
    if sp > 1:
        assert len(sp) == 2
        url_pref = sp[0].strip()
        assert url_pref.startswith('{')
        url_pref = url_pref[1:]
        s2l, l2s = context_mappings
        ns = l2s.get(url_pref)
        if ns is None:
            debug('shortening "{}"'.format(url_pref))
            ns = _url_prefix_to_short(url_pref)
            assert ns is not None
            s2l[ns] = url_pref
            l2s[url_pref] = ns
            debug('Adding "{}" <-> "{}" mapping from XML'.format(ns, url_pref))
        within_ns_name = sp[1]
    else:
        within_ns_name = s
        ns = '_'
    print('_xml_ns_name_to_short "{}" -> "{}:{}"'.format(s, ns, within_ns_name))
    return within_ns_name

def add_child_xml_to_dict(child, par_dict, context_mappings):
    sub_etag = _xml_ns_name_to_short(child.tag, context_mappings)
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


def flatten_into_dict(el, curr_obj, context_mappings):
    for sub in el:
        if sub.tag == '{http://www.nexml.org/2009}meta':
            add_meta_to_obj(sub, curr_obj)
        else:
            sd = add_child_xml_to_dict(sub, curr_obj, context_mappings)
            flatten_into_dict(sub, sd, context_mappings)
            # print('sub attrib={} tag={}'.format(sub.attrib, sub.tag))


def nexml_to_json_ld_dict(path=None, dom_root=None):
    if dom_root is None:
        tree = ElementTree.parse(path)
        dom_root = tree.getroot()
    # Short-to-long, and long-to-short dicts
    contexts = ({}, {})
    d = {}
    nexml_dict = add_child_xml_to_dict(dom_root, d, contexts)
    flatten_into_dict(dom_root, nexml_dict, contexts)
    return d


if __name__ == '__main__':
    if len(sys.argv) == 2:
        for filepath in sys.argv[1:]:
            print(json.dumps(nexml_to_json_ld_dict(path=filepath), indent=2, sort_keys=True))
    else:
        sys.exit('''Expecting one filepath to a NeXML doc as an argument.
JSON-LD will be written to standard output.
''')
