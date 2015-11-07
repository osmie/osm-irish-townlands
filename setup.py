#! /usr/bin/env python

from setuptools import setup

setup(name="django-osm-irish-townlands",
      version="1.0.0",
      author="Rory McCann",
      author_email="rory@technomancy.org",
      packages=['irish_townlands', 'irish_townlands.management', 'irish_townlands.management.commands', 'irish_townlands.migrations'],
      package_data={'irish_townlands': ['templates/irish_townlands/*', 'static/*.png', 'static/img/langflags/*', 'locale/*/*/*', 'templatetags/*']},
      license='GPLv3',
      description='',
      install_requires=[
          'django',
          'iso8601',
          'requests',
          'solid_i18n',
      ],
)
