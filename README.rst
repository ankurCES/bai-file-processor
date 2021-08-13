bai-file-processor
===================

Python module for parsing and writing Bai files.

Built on top of BAI2 Python package with additional Export features added


Requirements
------------

Python 3.3+ are supported.


Installation
------------

.. code-block:: bash

    pip install bai-file-processor


Usage
-----

To use bai file processor in a project

.. code-block:: python

     from bai_file_processor import bai_parser

     # parse from a file & export as CSV (summary & Transactions)
     bai_parser.extract_bai_components('XXXXX.bai', export_csv=True, filepath='output')
     
     # parse from a file & extract data as dictionary
     header_dict, grp_header_dict, list_transactions, summary_accounts = bai_parser.extract_bai_components('XXXX.bai')
     
     # WIth debug      
     bai_parser.extract_bai_components('XXXX.bai',debug=True)


Models
------

Models structure::

    Bai2File
        Bai2FileHeader
        Group
            GroupHeader
            Account
                AccountIdentifier
                TransactionDetail
                AccountTrailer
            GroupTrailer
        Bai2FileTrailer


