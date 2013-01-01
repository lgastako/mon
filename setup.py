#!/usr/bin/env python

import os
from setuptools import setup
from setuptools import find_packages

if __name__ == "__main__":
    setup(name="mon",
          version="1.0.0",
          description="Take actions when files change",
          author="John Evans",
          author_email="lgastako@gmail.com",
          requires=["envoy", "glob2"],
          provides=["mon"],
          entry_points=dict(console_scripts=[
              "mon = mon:main"
          ]),
          url="https://github.com/lgastako/mon",
          license="MIT",
          classifiers=(
              "Development Status :: 5 - Production/Stable",
              "Intended Audience :: Developers",
              "Natural Language :: English",
              "License :: OSI Approved :: MIT License",
              "Programming Language :: Python",
              "Programming Language :: Python :: 2.5",
              "Programming Language :: Python :: 2.6",
              "Programming Language :: Python :: 2.7",
              "Programming Language :: Python :: 3.0",
              "Programming Language :: Python :: 3.1",
          ))
