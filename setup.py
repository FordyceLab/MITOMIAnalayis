from setuptools import setup

setup(name='mitomi_analysis',
      version='0.1',
      description='Utilities for analyzing data from MITOMI experiments',
      url='https://github.com/FordyceLab/mitomi_analysis',
      author='Tyler Shimko',
      author_email='tshimko@stanford.edu',
      license='MIT',
      packages=['mitomi_analysis'],
      include_package_data=True,
      install_requires=[
        'matplotlib',
        'numpy',
        'scipy',
      ],
      scripts=['bin/mitomi'],
      zip_safe=False)
