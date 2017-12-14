#!/usr/bin/env python
"""Install for a lightweight NeXML (phylogenetics format) to JSON-LD project.
setup.py based on:
    https://github.com/pypa/sampleproject,
    https://packaging.python.org/en/latest/single_source_version.html
"""

from setuptools import setup, find_packages
from codecs import open
import os
import re

package_name = 'pynexld'

abs_top_dir = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(abs_top_dir, 'README.md'), 'r', encoding='utf-8') as f:
    long_description = f.read()


def find_version():
    ifp = os.path.join(abs_top_dir, package_name, '__init__.py')
    if_content = open(ifp, 'r', encoding='utf-8').read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]\s$", if_content, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string in {}".format(ifp))

# Arguments marked as "Required" below must be included for upload to PyPI.
# Fields marked as "Optional" may be commented out.

setup(name=package_name,  # Required
      version=find_version(),  # Required
      description='A NeXML (phylogenetics format) to JSON-LD converter',  # Required
      long_description=long_description,  # Optional
      url='https://github.com/phenoscape/pynexld',  # Optional
      author='Phenoscape Computable Evolutionary Phenotype Workshop 2017',  # Optional
      author_email='pypa-dev@googlegroups.com',  # Optional
      classifiers=['Development Status :: 3 - Alpha',
                   'Intended Audience :: Science/Research',
                   'Intended Audience :: Developers',
                   'Natural Language :: English',
                   'License :: OSI Approved :: BSD License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python :: 2.7',
                   'Programming Language :: Python :: 3.4',
                   'Programming Language :: Python :: 3.3',
                   'Topic :: Scientific/Engineering :: Bio-Informatics',
                   ],
       keywords='phylogenetics',  # Optional
       packages=find_packages(exclude=['contrib', 'docs', 'tests']),  # Required
       install_requires=['lxml', 'PyLD'],  # Optional
       extras_require={'test': ['pytest'],},
       entry_points={'console_scripts': ['nexml2jsonld.py=pynexld:main', ],},
)