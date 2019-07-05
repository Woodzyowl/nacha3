=====
nacha
=====

.. image:: https://travis-ci.org/DisruptiveLabs/nacha.png
   :target: https://travis-ci.org/DisruptiveLabs/nacha

.. image:: https://coveralls.io/repos/DisruptiveLabs/nacha/badge.png?branch=master
  :target: https://coveralls.io/r/DisruptiveLabs/nacha?branch=master

`NACHA <http://www.regaltek.com/docs/NACHA Format.pdf>`_ is a fixed sized
record format used to represent financial transactions composed like this:

.. code::

    FileHeader
        CompanyBatchHeader
            EntryDetail
                EntryDetailAddendum
                ...
            ...
        CompanyBatchControl
        ...
    FileControl

which we express using `bryl <https://github.com/balanced/bryl/>`_. Writing is
done like this:

.. code:: python

    with open('sample.nacha', 'w') as fo:
        writer = nacha.Writer(fo)
        with writer.begin_file(
             ...
             ):
             with writer.begin_company_batch(
                  ...
                  ):
                 writer.entry(...):
                 ...
            ...

Reading is done by iterating records like this:

.. code:: python

    with open('sample.nacha', 'r') as fo:
        reader = Reader(fo, include_terminal=True)
        for record, terminal in reader:
            ...

Or structured like this:

.. code:: python

    with open('sample.nacha', 'r') as fo:
        reader = Reader(fo)
        reader.file_header()
        for company_batch_header in reader.company_batches():
            for entry_detail, entry_addenda in reader.entries():
                ...
            reader.company_batch_control()
        reader.file_control()

===
use
===

.. code:: bash

   $ pip install nacha3

===
dev
===

.. code:: bash

   $ git clone https://github.com/rockxraj68/nacha3.git
   $ cd nacha
   $ mkvirtualenv nacha
   (nacha)$ pip install -e .[tests]
   (nacha)$ py.test tests.py --cov=nacha --cov-report term-missing 
