from setuptools import setup

setup(name='cashpassport-tracker',
      version='1.0',
      description='Python based webscraper to collect data from cashpassport',
      author='Oliver Bell',
      author_email='freshollie@gmail.com',
      url='https://github.com/freshollie/cashpassport-tracker',
      install_requires=['requests',
                        'markdown',
                        'mechanicalsoup', 
                        'beautifulsoup4',
                        'python-dateutil'
                        'flask']
     )