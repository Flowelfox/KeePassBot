import os
from setuptools import setup


requirements = [
    'psycopg2-binary',
    'certifi == 2017.11.5',
    'colorama == 0.3.9',
    'emoji == 0.4.5',
    'future == 0.16.0',
    'libkeepass == 0.2.0',
    'lxml == 4.1.1',
    'sqlalchemy',
    'pycrypto == 2.6.1',
    'python-telegram-bot == 8.1.1',
    'coloredlogs'
]
setup(
    name='keepassbot',
    version='1.0',
    description='Bot for telegram which can read .kdbx files.',
    url='https://github.com/Flowelcat/KeePassBot',
    author='Flowelcat',
    author_email='flowelcat@gmail.com',
    license='GNU',
    packages=["src"],
    zip_safe=False,
    install_requires=requirements,
    python_requires='>3.6.0',
    entry_points=dict(console_scripts=[
        'startbot = src.app:main',
        'init_db = src.scripts.init_db:main',
    ]),
    )


if not os.path.exists('logs'):
    os.mkdir('logs')
