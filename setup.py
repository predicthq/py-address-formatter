import os
from setuptools import find_packages, setup


def readme():
    with open('README.md') as f:
        return f.read()


setup(name='py-address-formatter',
      version='0.1.0',
      description='',
      long_description='',
      author='Denny Riadi',
      author_email='',
      entry_points={},
      classifiers=[
          'Programming Language :: Python :: 3.5',
          'Development Status :: 4 - Beta',
          'Topic :: Text Processing :: General',
          'Operating System :: POSIX :: Linux'
      ],
      packages=find_packages(),
      dependency_links=[],
      test_suite='tests',
      package_data={'': ['*.yaml']},
      setup_requires=[],
      tests_require=[],
      zip_safe=False)
