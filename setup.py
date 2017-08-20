import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(name='parseecpy',
      version='0.1',
      description='Parsec tool interface',
      url='https://github.com/alexfurtunatoifrn/parsecpy',
      author='Alex Furtunato',
      author_email='alexfurtunato@gmail.com',
      license='MIT',
      packages=['parsecpy'],
      install_requires=[
            'pandas',
            'matplotlib>=2.0.2',
            ],
      scripts=['bin/parsecpy_runprocess', 'bin/parsecpy_processlogs',
               'bin/parsecpy_createinputs'],
      long_description=read('README.md'),
      classifiers=[
          "Development Status :: 3 - Alpha",
          "Topic :: Utilities",
          "License :: MIT License",
      ],
      zip_safe=False)