pynexld
=======

Intended to be lightweight Python NeXML -> JSON-LD

See also:
  * inspired by Carl Boettiger's R package (https://github.com/cboettig/nexld)
  * a product of the  Computable evolutionary phenotype knowledge workshop 
(see https://github.com/phenoscape/KB-DataFest-2017)
  * https://hackmd.io/CwdgZghhxgjAtMAxgIxIgHATgKzwziAAzwBsAJkQEwixICmRERSQA===?both
  * https://gitter.im/phenoscape-kb-datafest/nexml-to-json-ld

Status:
  * Sort of works (see @TODO comments in the code)
  * Python 2.7 or >3.2

Installation
============

    pip install -r requirements.txt
    python setup.py install

or simply:

    python setup.py develop
    
Running
=======

     nexml2jsonld.py data/example.xml > example.json


Testing
=======

    python -m pytest

or

    python setup.py test

or (if you have checked out [nexld](https://github.com/phenoscape/nexld) as the 
    "sister" directory of pynexld then:

    bash test.sh

