#!/usr/bin/python

from setuptools import setup

setup(
        name="OpenSRS",
        packages=['opensrs', ],
        install_requires=['httplib2', ],
        version='0.1.2',
        description='Higher level Python interface to the OpenSRS XML API',
        long_description=open('README.md').read(),
        author='Evan Borgstrom',
        author_email='evan@fatbox.ca',
        url='https://github.com/fatbox/OpenSRS-py',
        classifiers=[
            'Development Status :: 4 - Beta',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: BSD License',
            'Natural Language :: English',
            'Topic :: Software Development :: Libraries',
            'Topic :: Software Development :: Libraries :: Python Modules',
            ],
        )
