#! /usr/bin/env python

from setuptools import setup

setup(name="django-osm-irish-townlands",
      version="0.0.1",
      author="Rory McCann",
      author_email="rory@technomancy.org",
      packages=['irish_townlands', 'irish_townlands.management.commands'],
      license='GPLv3',
      description='',
      install_requires=[
          'django',
      ],
      )
