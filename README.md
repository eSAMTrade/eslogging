# eslogging
This is a fork of [CMRESHandler.py](https://github.com/cmanaha/python-elasticsearch-logger) project. We didn't contribute to it as there's no maintenance of that project anymore.

Python Elasticsearch Log handler
********************************

This library provides an Elasticsearch logging appender compatible with the
python standard `logging <https://docs.python.org/2/library/logging.html>`_ library.

The code source is in github at `https://github.com/cmanaha/python-elasticsearch-logger
<https://github.com/cmanaha/python-elasticsearch-logger>`_


Installation
============
Install using pip::

    pip install eslogging


Requirements Python 3
=====================
This library requires the following dependencies
 - elasticsearch
 - requests

Additional requirements for Kerberos support
============================================
Additionally, the package support optionally kerberos authentication by adding the following dependecy
 - requests-kerberos

Additional requirements for AWS IAM user authentication (request signing)
=========================================================================
Additionally, the package support optionally AWS IAM user authentication by adding the following dependecy
 - requests-aws4auth

Building the sources & Testing
------------------------------
To create the package follow the standard python setup.py to compile.
To test, just execute the python tests within the test folder

Why using an appender rather than logstash or beats
---------------------------------------------------
In some cases is quite useful to provide all the information available within the LogRecords as it contains
things such as exception information, the method, file, log line where the log was generated.

If you are interested on understanding more about the differences between the agent vs handler
approach, I'd suggest reading `this conversation thread <https://github.com/cmanaha/python-elasticsearch-logger/issues/44/>`_

The same functionality can be implemented in many other different ways. For example, consider the integration
using `SysLogHandler <https://docs.python.org/3/library/logging.handlers.html#sysloghandler>`_ and
`logstash syslog plugin <https://www.elastic.co/guide/en/logstash/current/plugins-inputs-syslog.html>`_.


Contributing back
-----------------
Feel free to use this as is or even better, feel free to fork and send your pull requests over.

[![build Status](https://img.shields.io/pypi/status/eslogging.svg)](https://travis-ci.org/asuiu/eslogging)
[![downloads](https://img.shields.io/pypi/dd/eslogging)](https://pypi.org/project/eslogging/)
[![license](https://img.shields.io/pypi/l/eslogging.svg)](https://pypi.org/project/eslogging/)
