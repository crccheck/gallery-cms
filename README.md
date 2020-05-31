Gallery CMS
===========

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

See [`Makefile`](./Makefile)


Requirements
------------

    make install

MacOS packages:

    brew install exempi

For Ubuntu, refer to the [`Dockerfile`](./Dockerfile)


Dev workflow
------------

Run the Python server in one terminal:

    make dev

Run the client side server in another terminal:

    npm run dev
