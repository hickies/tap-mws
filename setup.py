#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='tap-mws',
      version='0.0.1',
      description='Singer.io tap for extracting data from the Amazon MWS API',
      author='HICKIES',
      classifiers=['Programming Language :: Python :: 3 :: Only'],
      py_modules=['tap_mws'],
      install_requires=[
          'singer-python',
          'boto'
      ],
      entry_points='''
          [console_scripts]
          tap-mws=tap_mws:main
      ''',
      packages=find_packages(),
      package_data={
          'tap_mws': [
              'schemas/*.json'
          ]
      })
