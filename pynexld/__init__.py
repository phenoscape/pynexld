#!/usr/bin/env python
"""Python NeXML -> JSON-LD converter
"""
from __future__ import print_function, division
# noinspection PyUnresolvedReferences
from lxml import etree, objectify
from pyld import jsonld
import json
import sys
import os

VERBOSE = True


def add_meta_to_obj(meta_el, curr_obj):
    """Creates a key value pair in `curr_obj` from a `meta` NeXML element that is inside
    the corresponding XML element.

    @TODO: Some type conversion is needed - see example.xml bool. Check DendroPy code
    @TODO: handling all variants with if/else is not very generic
    @TODO: "nex:" prefix should really be obtained from the XML doc's namespace mapping rather
        than being hard-coded here
    """
    subatt = meta_el.attrib
    sat = subatt['{http://www.w3.org/2001/XMLSchema-instance}type']
    if sat in {'ResourceMeta', 'nex:ResourceMeta'}:
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


_REPEATABLE_NEX_EL, _NEXML_ATT_OR_EL = None, None


def _cache_nexml_element_names():
    """_REPEATABLE_NEX_EL with those NeXML tags that map to list
    and _NEXML_ATT_OR_EL with other NeXML tags or attributes that need to be emitted.
    """
    global _NEXML_ATT_OR_EL, _REPEATABLE_NEX_EL
    _raw_rep_tags = ['cell', 'char', 'characters', 'edge',
                     'meta', 'member', 'node', 'otu', 'otus',
                     'row', 'states', 'state', 'symbol',
                     'tree', 'trees', 'uncertain_state_set']
    _REPEATABLE_NEX_EL = frozenset(_raw_rep_tags)
    _non_rep_tags = []
    _nex_atts = ['label', 'length',
                 'source', 'target', 'version']
    _NEXML_ATT_OR_EL = frozenset(_raw_rep_tags + _non_rep_tags + _nex_atts)


_cache_nexml_element_names()

NEXML_PREF = 'http://www.nexml.org/2009'
BRACK_NEXML_PREF = '{' + NEXML_PREF + '}'
_CONVENTIONAL_URL_SHORTENINGS = {NEXML_PREF: 'nex',
                                 'http://www.w3.org/XML/1998/namespace': 'xml',
                                 }


def _url_prefix_to_short(url_pref):
    """Returns the commonly used short abbreviation for a few common URL prefixes."""
    return _CONVENTIONAL_URL_SHORTENINGS.get(url_pref)


def debug(msg):
    """Writes `msg` to stderr if VERBOSE is True."""
    if VERBOSE:
        sys.stderr.write('pynexld: {}\n'.format(msg))


def register_in_contexts(short, long_name, sub, context_mappings):
    """Adds the short <-> long_name mapping if needed. If `sub` is not
    in the JSON-LD context precursor, then sub -> long_name/sub is recorded there.
    """
    if not short:
        return
    s2l, l2s = context_mappings[:2]
    debug('Adding "{}" <-> "{}" mapping from XML'.format(short, long_name))
    if short not in s2l:
        s2l[short] = long_name
        l2s[long_name] = short
    register_in_jsonld_context(long_name, sub, context_mappings)


def register_in_jsonld_context(long_name, sub, context_mapptings):
    """Adds the sub -> long_name/sub to the JSON-LD context precursor if not there.

    Returns a new long_name only iff the argument of long_name was null and `sub` is a NeXML
        term (e.g. an undecorated <otu label="..." /> )
        element in NeXML has no prefix for otus or label, but they are in the default namespace
        for most (all?) NeXML instance docs.

    @TODO: Should propose a new short name if long/sub is registered to a different URL prefix to
        deal with name clashes in different namespaces.
    """
    if not sub:
        return
    if not long_name:
        if sub in _NEXML_ATT_OR_EL:
            nl = '{}/{}'.format(NEXML_PREF, sub)
            register_in_jsonld_context(NEXML_PREF, sub, context_mapptings)
            return nl
        if sub.endswith('label'):
            debug('not contextifying "{}"'.format(sub))
        return
    if not sub.startswith('{'):
        jldc = context_mapptings[2]
        fl = '{}/{}'.format(long_name, sub)
        if sub not in jldc:
            debug('Adding "{}" -> "{}" mapping to precursor of JSON-LD context'.format(sub, fl))
            jldc[sub] = fl
    else:
        debug('not contextifying "{}"'.format(sub))
    return None


def _xml_ns_name_to_short_long_url(s, context_mappings, as_iri=False):
    """Takes a name (`s`) from the XML parser which uses the {namespace}short_name
    convention.
    This registers the names in the context dictionaries and mappings for short to long.

    Returns the short_name, long_name, url_prefix For example:
        ('nex:otu', 'http://www.nexml.org/2009}otu', 'http://www.nexml.org/2009')
    or:
        ('_:xyz', 'xyz, None) for blank nodes
    or:
        ('xyz', 'xyz', None) for content with no namespaces that are not being treated as IRIs

    The `as_iri` arg can force the treatment of a string `s` as an IRI.
    """
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
            long_form = '{}/{}'.format(url_pref, within_ns_name)
            return s, long_form, url_pref
        return s, within_ns_name, None
    return within_ns_name, within_ns_name, None


def nexml_tag_should_be_list(sub_etag):
    """Returns True if `sub_etag` is a prefix:tag or tag string where tag is a list element in
    NeXML.
    """
    sp = sub_etag.split(':')
    if len(sp) > 1:
        sub_etag = sp[-1]
    return sub_etag in _REPEATABLE_NEX_EL


def add_child_xml_to_dict(child, par_dict, context_mappings):
    """Puts a DOM element `child` into a the temporary dict belonging to the parent `par_dict`,
    building up the context_mapping dicts as it goes."""
    short_tag, long_tag, url = _xml_ns_name_to_short_long_url(str(child.tag), context_mappings)
    targ_obj = par_dict.get(long_tag)
    # @TODO: Note the R impl handles types for nex:FloatTree differently here
    nso = {'@type': long_tag}
    for k, v in child.attrib.items():
        if k == 'id':
            nso['@id'] = v
        else:
            short_a, long_a, a_url = _xml_ns_name_to_short_long_url(k, context_mappings)
            # if isinstance(v, str) and v.startswith('nex:'):
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
    """Recursively adds the subtree of the DOM rooted at `el` into the temporary dict
    `curr_obj`,  building up the context_mapping dicts as it goes."""
    for sub in el:
        if sub.tag == '{http://www.nexml.org/2009}meta':
            add_meta_to_obj(sub, curr_obj)
        else:
            sd = add_child_xml_to_dict(sub, curr_obj, context_mappings)
            flatten_into_dict(sub, sd, context_mappings)
            # print('sub attrib={} tag={}'.format(sub.attrib, sub.tag))


def nexml_to_json_fully_qual_and_context_dicts(path=None, dom_root=None):
    """Returns a JSON representation of an NeXML instance doc (specified as the root of the
    DOM or the filepath to the XML doc) as a dictionary and corresponding context dict
    that can be transformed using jsonld.compact"""
    if dom_root is None:
        if not path:
            raise ValueError("Either dom_root or path must be sent to "
                             "nexml_to_json_fully_qual_and_context_dicts")
        if not os.path.exists(path):
            raise ValueError('The XML file "{}" does not exist'.format(path))
        parser = etree.XMLParser(remove_comments=True)
        tree = objectify.parse(path, parser=parser)
        dom_root = tree.getroot()
    # Short-to-long, and long-to-short dicts
    contexts = ({}, {}, {})
    for short, long_name in dom_root.nsmap.items():
        register_in_contexts(short, long_name, '', contexts)
    d = {}
    nexml_dict = add_child_xml_to_dict(dom_root, d, contexts)
    flatten_into_dict(dom_root, nexml_dict, contexts)
    return d, contexts[2]


def nexml_to_json_ld_dict(path=None, dom_root=None):
    """Returns a JSON-LD representation of an NeXML instance doc (specified as the root of the
    DOM or the filepath to the XML doc)"""
    payload, context = nexml_to_json_fully_qual_and_context_dicts(path=path, dom_root=dom_root)
    nex = payload.get('http://www.nexml.org/2009/nexml')
    if nex:
        b = nex.get('http://www.w3.org/XML/1998/namespace/base')
        if b:
            context['@base'] = b
            debug('Added @base -> "{}" mapping'.format(b))
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
