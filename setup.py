from setuptools import setup

setup(name='cashpassport-tracker',
      version='1.1',
      description='Python based service to track and notify of new transactions on cashpassport using cashpassport-api',
      author='Oliver Bell',
      author_email='freshollie@gmail.com',
      url='https://github.com/freshollie/cashpassport-tracker',
      install_requires=['requests',
                        'markdown',
                        'dateutil-parser'
                        'psycopg2']
     )