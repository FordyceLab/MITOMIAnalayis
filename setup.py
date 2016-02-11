from setuptools import setup

setup(name='mitomi_analysis',
      version='0.1',
      description='Utilities for analyzing data from MITOMI experiments',
      url='https://github.com/FordyceLab/mitomi_analysis',
      author='Tyler Shimko',
      author_email='tshimko@stanford.edu',
      license='MIT',
      packages=['funniest'],
      install_requires=[
        'matplotlib'
        'numpy',
        'scripy',
      ],
      zip_safe=False)
