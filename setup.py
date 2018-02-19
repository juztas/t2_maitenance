#!/usr/bin/python
from distutils.core import setup

setup(name='t2Mon',
      version='0.1',
      description='T2 Monitoring scripts',
      author='Justas Balcas',
      author_email='juztas@gmail.com',
      url='https://github.com/jbalcas/T2_SCRIPTS',
      packages=['t2Mon'],
      install_requires=['potsdb', 'psutil'],
      package_dir={'': 'src/python/'},
      data_files=[('/etc/', ['packaging/t2_maitenance.conf'])],
      scripts=["src/executors/samtest-local"]
     )
