Gallery CMS
===========

[![Build Status](https://travis-ci.org/crccheck/gallery-cms.svg?branch=master)](https://travis-ci.org/crccheck/gallery-cms) [![codecov](https://codecov.io/gh/crccheck/gallery-cms/branch/master/graph/badge.svg)](https://codecov.io/gh/crccheck/gallery-cms)

A simple online gallery where the images are the database.

Use meta information from IPTC instead of a database.


Requirements
------------

make install

Ubuntu packages:

    apt-get install libexiv2-dev libboost-python-dev


Dev workflow
------------

Auto reload in dev. Run in two terminal windows:

    nodemon -w . --exec python gallery/gallery.py
    grunt dev

I've combined them into one window before, but the logging output becomes too
hard to read.
