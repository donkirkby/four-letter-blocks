"""A setuptools based setup module.
See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""
import setuptools
from setuptools import setup
from os import path
import four_letter_blocks

here = path.abspath(path.dirname(__file__))
project_url = 'https://donkirkby.github.io/four-letter-blocks/'

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read().replace(']: docs/', ']: ' + project_url)

setup(name='four_letter_blocks',
      version=four_letter_blocks.__version__,
      description='Crossword puzzle assembled from blocks of four letters',
      long_description=long_description,
      long_description_content_type='text/markdown',
      url=project_url,
      author='Don Kirkby',
      classifiers=[  # https://pypi.org/classifiers/
          'Development Status :: 4 - Beta',
          'Intended Audience :: End Users/Desktop',
          'Topic :: Games/Entertainment :: Puzzle Games',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3.9'],
      keywords='puzzle wordgame crossword',
      packages=setuptools.find_packages(),
      install_requires=['PySide6'],
      extras_require={'dev': ['pytest',
                              'coverage']},
      entry_points={
          'gui_scripts': [
              'four_letter_blocks=four_letter_blocks.__main__:main']},
      project_urls={
          'Bug Reports': 'https://github.com/donkirkby/four-letter-blocks/issues',
          'Source': 'https://github.com/donkirkby/four-letter-blocks'})