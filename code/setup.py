# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

setup(name='te',
      version=2.0,
      description="text input exerciser",
      long_description=
      '''
      TextExerciser is an iterative, feedback-driven text input exerciser for Android apps.
      It dedicates to generating valid text inputs that can satisfy input constraints.
      ''',
      classifiers=[],
      keywords='ui trigger, text input exerciser',
      author='',
      author_email='',
      license='MIT',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=True,
      install_requires=[],
      entry_points={
          'console_scripts': [
              'te = src.te:main'
          ]
      }
      )
