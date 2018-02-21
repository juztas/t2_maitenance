#!/usr/bin/python
import os
from distutils.core import setup
from setupUtilities import list_packages, get_py_modules

CONFIG = [('/etc/', ['packaging/t2_maitenance.conf'])]

if os.path.isfile('/etc/t2_maitenance.conf'):
    CONFIG = []

setup(name='t2Mon',
      version='0.1',
      description='T2 Monitoring scripts',
      author='Justas Balcas',
      author_email='juztas@gmail.com',
      url='https://github.com/jbalcas/T2_SCRIPTS',
      packages=['t2Mon'] + list_packages(['src/python/t2Mon/']),
      py_modules=get_py_modules(['src/python/t2Mon']),
      install_requires=['potsdb'],
      package_dir={'': 'src/python/'},
      data_files=CONFIG,
      scripts=["src/executors/samtest-local", "src/executors/namenode-mon", "src/executors/datanode-mon"]
     )
