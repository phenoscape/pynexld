#!/usr/bin/env python
from __future__ import print_function, division
from pynexld import nexml_to_json_ld_dict


def test_example_file():
    d = nexml_to_json_ld_dict('data/example.xml')
    assert d is not None
