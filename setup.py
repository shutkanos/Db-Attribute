from setuptools import setup

from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'readme.md'), encoding='utf-8') as f:
    long_description = f.read()

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='db_attribute',
    version='2.1.1',
    description='DataBase attribute package',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/shutkanos/Db-Attribute',

    author='Shutkanos',
    author_email='Shutkanos836926@mail.ru',

    license='MIT',

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],

    keywords='db database attribute dbattribute db_attribute databaseattribute auto_attribute',
    packages=['db_attribute'],

    install_requires=required,

    extras_require={
        'dev': [],
        'test': [],
    },
)