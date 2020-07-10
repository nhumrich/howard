from setuptools import setup
from os import path

here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='howard',
    version='1.6.1',
    packages=['howard'],
    install_requires=["python-dateutil"],
    long_description=long_description,
    url='https://github.com/nhumrich/howard',
    long_description_content_type='text/markdown',
    license='MIT',
    author='nhumrich',
    author_email='',
    description='Convert dictionaries to dataclasses and back'
)
