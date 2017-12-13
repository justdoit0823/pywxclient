
import os
import sys

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

version = '0.1.0'


class PyTest(TestCommand):

    user_options = [('pytest-args=', 'a', "Arguments to pass into py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest

        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


setup(name='pywxclient',
      version=version,
      description="A simple WeChat client written in Python.",
      long_description=open(
          os.path.join(os.path.dirname(__file__), 'README.rst')).read(),
      classifiers=(
          'Development Status :: 5 - Production/Stable',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: Apache Software License',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: Implementation :: CPython',
      ),
      keywords='WeChat Python HTTP',
      author='justdoit0823',
      author_email='justdoit920823@gamil.com',
      url='https://github.com/justdoit0823/pywxclient',
      license='Apache 2.0',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=True,
      cmdclass={'test': PyTest},
      tests_require=('pytest==3.0.7',),
      install_requires=[
          # -*- Extra requirements: -*-
          'requests>=2.10.0',
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
