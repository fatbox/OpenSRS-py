#!/usr/bin/python

from distutils.core import setup

setup(name="OpenSRS",
      packages=['opensrs', ]
      requires=['xml.etree.ElementTree', 'httplib2']
     )
