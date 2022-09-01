"""A setuptools based setup module.
See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""
import setuptools
from setuptools import setup
from os import path
import re
import four_letter_blocks

here = path.abspath(path.dirname(__file__))
project_url = 'https://donkirkby.github.io/four-letter-blocks/'

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    readme = f.read()
    # Replace relative path with URL, and drop .md suffix.
    long_description = re.sub(r']:\s*docs/(.*?)(\.md)?$',
                              r']: ' + project_url + r'\1',
                              readme,
                              flags=re.MULTILINE)

setup(name='four_letter_blocks',
      version=four_letter_blocks.__version__,
      description='Crossword puzzle assembled from blocks of four letters',
      long_description=long_description,
      long_description_content_type='text/markdown',
      url=project_url,
      author='Don Kirkby',
      classifiers=[  # https://pypi.org/classifiers/
          'Development Status :: 5 - Production/Stable',
          'Intended Audience :: End Users/Desktop',
          'Topic :: Games/Entertainment :: Puzzle Games',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3.10'],
      keywords='puzzle wordgame crossword',
      packages=setuptools.find_packages(),
      install_requires=['PySide6', 'numpy'],
      extras_require={'dev': ['pytest',
                              'coverage',
                              'space-tracer']},
      entry_points={
          'gui_scripts': [
              'four_letter_blocks=four_letter_blocks.__main__:main']},
      project_urls={
          'Bug Reports': 'https://github.com/donkirkby/four-letter-blocks/issues',
          'Source': 'https://github.com/donkirkby/four-letter-blocks'})
