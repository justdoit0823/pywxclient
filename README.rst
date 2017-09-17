
pywxclient
==========

.. image:: https://travis-ci.org/justdoit0823/pywxclient.svg?branch=master
    :target: https://travis-ci.org/justdoit0823/pywxclient


A simple WeChat client is based on Web HTTP api, supporting authorization, login, fetching message and sending message.

Here we go:


.. code-block:: pycon

   >>> from pywxclient.core import Session, SyncClient

   >>> s1 = Session()

   >>> c1 = SyncClient(s1)

   >>> c1.get_authorize_url()  # Open the url in web browser

   >>> c1.authorize()  # Continue authorize when returning False

   >>> c1.login()

   >>> c1.sync_check()

   >>> msgs = c1.sync_message()  # Here are your wechat messages

   >>> c1.flush_sync_key()


Features
========

  * WeChat authorization

  * WeChat login

  * Fetching WeChat contacts

  * Fetching all possible messages

  * Send text message

  * Send image message

  * Send video message

  * Send file message

  * Dump client as a dict

  * Load client from a dict

  * Local or network files uploading


**pywxclient aims to only support Python 3, so there is no guarantee for Python 2.**


Installation
============

We can simply use pip to install, as the following:

.. code-block:: bash

   $ pip install pywxclient

or installing from git

.. code-block:: bash

   $ pip install git+https://github.com/justdoit0823/pywxclient


Examples
========

In the examples directory, there are two simple python wechat client program as tutorials.

Or you can write a more complex wechat client with this `pywxclient` package.


How to Contribute
=================

Open an `issue <https://github.com/justdoit0823/pywxclient/issues>`_, join a discussion or make a pull request.
