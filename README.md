Gallery CMS
===========

[![Build Status](https://travis-ci.org/crccheck/gallery-cms.svg?branch=master)](https://travis-ci.org/crccheck/gallery-cms) [![codecov](https://codecov.io/gh/crccheck/gallery-cms/branch/master/graph/badge.svg)](https://codecov.io/gh/crccheck/gallery-cms)

A simple online gallery where the images are the database.

There are many programs and websites for managing your photos. But they all
have a high level of [lock-in]. With Gallery CMS, all the data is stored using
standard [IPTC] metadata instead of a database. If you bring your photos into
another program/site, that data will go with it.

With Gallery CMS, you'll be able to share a rich gallery with content on any
Internet connected machine with a file system (see [Requirements]).

This is *not a replacement* for a media manager. It's designed for small
tweaks; things like mass-tagging and naming should be done elsewhere.

  [lock-in]: https://en.wikipedia.org/wiki/Vendor_lock-in
  [IPTC]: http://www.sno.phy.queensu.ca/~phil/exiftool/TagNames/IPTC.html

Usage
-----

Run `python gallery/gallery.py --help` to get started.

### Environment variables

* `CIPHER_KEY` -- Control how thumbnail urls are generated
* `OAUTH_CLIENT_ID`
* `OAUTH_CLIENT_SECRET`
* `PORT` -- Change what port the web server runs on
* `REDIS_URL` -- Connection url to Redis


Requirements
------------

    make install

Ubuntu packages:

    apt-get install libexiv2-dev libboost-python-dev

Redis is also required for session storage persistence, but it would be easy to
make this completely database free.

Google Oauth2 app is required to accept logins and edits.


Dev workflow
------------

    npm run dev

### Running tests in Docker

    make docker/test


Notes
-----

Apple's _Preview_ can read and write metadata, but it may not be IPTC metdata.
We only support IPTC for now.
