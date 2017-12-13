#!/usr/bin/env python
from __future__ import print_function, division
from lxml import etree, objectify
from pyld import jsonld
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
        val = subatt.get('content')
        if val is None:
            val = meta_el.text or ''
            val = val.strip()
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


####################################################################################################
# Fill: _REPEATABLE_NEX_EL with those NeXML tags that map to list
#      and _NEXML_ATT_OR_EL with other NeXML tags or attributes that need to be emitted.

_raw_rep_tags = ['cell', 'char', 'edge', 'meta', 'member', 'node', 'otu',
                 'row', 'states', 'state', 'symbol', 'tree', ]
_REPEATABLE_NEX_EL = frozenset(_raw_rep_tags)
_non_rep_tags = []
_nex_atts = ['label', 'length', 'otus',
             'source', 'target', 'trees', 'version']
_NEXML_ATT_OR_EL = frozenset(_raw_rep_tags + _non_rep_tags + _nex_atts)
del _raw_rep_tags
del _non_rep_tags
del _nex_atts
####################################################################################################

NEXML_PREF = 'http://www.nexml.org/2009'
BRACK_NEXML_PREF = '{' + NEXML_PREF + '}'
_CONVENTIONAL_URL_SHORTENINGS = {NEXML_PREF: 'nex',
                                 'http://www.w3.org/XML/1998/namespace': 'xml',
                                 }


def _url_prefix_to_short(url_pref):
    return _CONVENTIONAL_URL_SHORTENINGS.get(url_pref)


def debug(msg):
    if VERBOSE:
        sys.stderr.write('pynexld: {}\n'.format(msg))

def register_in_contexts(short, long, sub, context_mappings):
    if not short:
        return
    s2l, l2s = context_mappings[:2]
    debug('Adding "{}" <-> "{}" mapping from XML'.format(short, long))
    if short not in s2l:
        s2l[short] = long
        l2s[long] = short
    register_in_jsonld_context(long, sub, context_mappings)


def register_in_jsonld_context(long, sub, context_mapptings):
    if not sub:
        return
    if not long:
        if sub in _NEXML_ATT_OR_EL:
            nl = '{}/{}'.format(NEXML_PREF, sub)
            register_in_jsonld_context(NEXML_PREF, sub, context_mapptings)
            return nl
        if sub.endswith('label'):
            debug('not contextifying "{}"'.format(sub))
        return
    if not sub.startswith('{'):
        jldc = context_mapptings[2]
        fl = '{}/{}'.format(long, sub)
        if sub not in jldc:
            debug('Adding "{}" <-> "{}" mapping to precursor of JSON-LD context'.format(sub, fl))
            jldc[sub] = fl
    else:
        debug('not contextifying "{}"'.format(sub))
    return None

def _xml_ns_name_to_short_long_url(s, context_mappings, as_iri=False):
    # debug('to short "{}"'.format(s))
    sp = s.split('}')
    if len(sp) > 1:
        assert len(sp) == 2
        url_pref = sp[0].strip()
        assert url_pref.startswith('{')
        url_pref = url_pref[1:]
        s2l, l2s = context_mappings[:2]
        ns = l2s.get(url_pref)
        within_ns_name = sp[1]
        if ns is None:
            debug('shortening "{}"'.format(url_pref))
            ns = _url_prefix_to_short(url_pref)
            assert ns is not None
            register_in_contexts(ns, url_pref, within_ns_name, context_mappings)
        else:
            register_in_jsonld_context(url_pref, within_ns_name, context_mappings)
    else:
        within_ns_name = s
        ns, url_pref = '_', None
    debug('_xml_ns_name_to_short_long_url "{}" -> "{}:{}"'.format(s, ns, within_ns_name))
    if as_iri or ns != '_':
        s = '{}:{}'.format(ns, within_ns_name)
        if url_pref:
            l = '{}/{}'.format(url_pref, within_ns_name)
            return s, l, url_pref
        return s, within_ns_name, None
    return within_ns_name, within_ns_name, None


def nexml_tag_should_be_list(sub_etag):
    sp = sub_etag.split(':')
    if len(sp) > 1:
        sub_etag = sp[-1]
    return sub_etag in _REPEATABLE_NEX_EL


def add_child_xml_to_dict(child, par_dict, context_mappings):
    short_tag, long_tag, url = _xml_ns_name_to_short_long_url(str(child.tag), context_mappings)
    targ_obj = par_dict.get(long_tag)
    nso = {}
    nso['@type'] = long_tag
    for k, v in child.attrib.items():
        if k == 'id':
            nso['@id'] = v
        else:
            short_a, long_a, a_url = _xml_ns_name_to_short_long_url(k, context_mappings)
            #if isinstance(v, str) and v.startswith('nex:'):
            #    v = v[4:]
            #    debug("HACK!!!!!!!!")
            new_long_a = register_in_jsonld_context(a_url, k, context_mappings)
            if new_long_a is not None:
                long_a = new_long_a
            nso[long_a] = v
    if targ_obj is None:
        if nexml_tag_should_be_list(short_tag):
            targ_obj = [nso]
            par_dict[long_tag] = targ_obj
        else:
            par_dict[long_tag] = nso
    else:
        if not nexml_tag_should_be_list(short_tag):
            raise ValueError('Did not expect a repeated "{}" element'.format(short_tag))
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


def nexml_to_json_fully_qual_and_context_dicts(path=None, dom_root=None):
    if dom_root is None:
        parser = etree.XMLParser(remove_comments=True)
        tree = objectify.parse(path, parser=parser)
        dom_root = tree.getroot()
    # Short-to-long, and long-to-short dicts
    contexts = ({}, {}, {})
    for short, long in dom_root.nsmap.items():
        register_in_contexts(short, long, None, contexts)
    d = {}
    nexml_dict = add_child_xml_to_dict(dom_root, d, contexts)
    flatten_into_dict(dom_root, nexml_dict, contexts)
    return d, contexts[2]


def nexml_to_json_ld_dict(path=None, dom_root=None):
    payload, context = nexml_to_json_fully_qual_and_context_dicts(path=path, dom_root=dom_root)
    debug('payload = {}'.format(json.dumps(payload, indent=2, sort_keys=True)))
    debug('context = {}'.format(json.dumps(context, indent=2, sort_keys=True)))
    compacted = jsonld.compact(payload, context)
    return compacted


if __name__ == '__main__':
    if len(sys.argv) == 2:
        for filepath in sys.argv[1:]:
            print(json.dumps(nexml_to_json_ld_dict(path=filepath), indent=2, sort_keys=True))
    else:
        sys.exit('''Expecting one filepath to a NeXML doc as an argument.
JSON-LD will be written to standard output.
''')
