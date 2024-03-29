"""
This test battery needs a running ES server on localhost
"""

import logging
import os
import sys
import time
import unittest
from ssl import SSLContext
from unittest.mock import MagicMock, patch

from eslogging.handlers import ESHandler, ESHandlerIgnoreESLogs

sys.path.insert(0, os.path.abspath('.'))
LOGGER_NAME = "ESHandlerIgnoreESLogsTes"
TEST_INDEX_NAME = "pythontest"


class ESHandlerTestCase(unittest.TestCase):
    DEFAULT_ES_SERVER = 'localhost'
    DEFAULT_ES_PORT = 9200

    def getESHost(self):
        return os.getenv('TEST_ES_SERVER', ESHandlerTestCase.DEFAULT_ES_SERVER)

    def getESPort(self):
        try:
            return int(os.getenv('TEST_ES_PORT', ESHandlerTestCase.DEFAULT_ES_PORT))
        except ValueError:
            return ESHandlerTestCase.DEFAULT_ES_PORT

    def setUp(self):
        self.log = logging.getLogger(LOGGER_NAME)
        test_handler = logging.StreamHandler(stream=sys.stderr)
        self.log.addHandler(test_handler)

    def tearDown(self):
        del self.log

    def test_ping(self):
        handler = ESHandler(hosts=[{'host': self.getESHost(), 'port': self.getESPort()}],
                            auth_type=ESHandler.AuthType.NO_AUTH,
                            es_index_name=TEST_INDEX_NAME,
                            use_ssl=False,
                            raise_on_indexing_exceptions=True)
        es_test_server_is_up = handler.test_es_source()
        self.assertEqual(True, es_test_server_is_up)

    def test_buffered_log_insertion_flushed_when_buffer_full(self):
        handler = ESHandler(hosts=[{'host': self.getESHost(), 'port': self.getESPort()}],
                            auth_type=ESHandler.AuthType.NO_AUTH,
                            use_ssl=False,
                            buffer_size=2,
                            flush_frequency_in_sec=1000,
                            es_index_name=TEST_INDEX_NAME,
                            es_additional_fields={'App': 'Test', 'Environment': 'Dev'},
                            raise_on_indexing_exceptions=True)

        es_test_server_is_up = handler.test_es_source()
        self.log.info("ES services status is:  {0!s}".format(es_test_server_is_up))
        self.assertEqual(True, es_test_server_is_up)

        log = logging.getLogger(LOGGER_NAME)
        log.setLevel(logging.DEBUG)
        log.addHandler(handler)
        log.warning("First Message")
        log.info("Seccond Message")
        self.assertEqual(0, len(handler._buffer))
        handler.close()

    def test_es_log_extra_argument_insertion(self):
        self.log.info("About to test elasticsearch insertion")
        handler = ESHandler(hosts=[{'host': self.getESHost(), 'port': self.getESPort()}],
                            auth_type=ESHandler.AuthType.NO_AUTH,
                            use_ssl=False,
                            es_index_name=TEST_INDEX_NAME,
                            es_additional_fields={'App': 'Test', 'Environment': 'Dev'},
                            raise_on_indexing_exceptions=True)

        es_test_server_is_up = handler.test_es_source()
        self.log.info("ES services status is:  {0!s}".format(es_test_server_is_up))
        self.assertEqual(True, es_test_server_is_up)

        log = logging.getLogger(LOGGER_NAME)
        log.addHandler(handler)
        log.warning("Extra arguments Message", extra={"Arg1": 300, "Arg2": 400})
        self.assertEqual(1, len(handler._buffer))
        self.assertEqual(handler._buffer[0]['Arg1'], 300)
        self.assertEqual(handler._buffer[0]['Arg2'], 400)
        self.assertEqual(handler._buffer[0]['App'], 'Test')
        self.assertEqual(handler._buffer[0]['Environment'], 'Dev')
        handler.flush()
        self.assertEqual(0, len(handler._buffer))

    def test_buffered_log_insertion_after_interval_expired(self):
        handler = ESHandler(hosts=[{'host': self.getESHost(), 'port': self.getESPort()}],
                            auth_type=ESHandler.AuthType.NO_AUTH,
                            use_ssl=False,
                            flush_frequency_in_sec=0.1,
                            es_index_name=TEST_INDEX_NAME,
                            es_additional_fields={'App': 'Test', 'Environment': 'Dev'},
                            raise_on_indexing_exceptions=True)

        es_test_server_is_up = handler.test_es_source()
        self.log.info("ES services status is:  {0!s}".format(es_test_server_is_up))
        self.assertEqual(True, es_test_server_is_up)

        log = logging.getLogger(LOGGER_NAME)
        log.addHandler(handler)
        log.warning("Extra arguments Message", extra={"Arg1": 300, "Arg2": 400})
        self.assertEqual(1, len(handler._buffer))
        self.assertEqual(handler._buffer[0]['Arg1'], 300)
        self.assertEqual(handler._buffer[0]['Arg2'], 400)
        self.assertEqual(handler._buffer[0]['App'], 'Test')
        self.assertEqual(handler._buffer[0]['Environment'], 'Dev')
        time.sleep(1)
        self.assertEqual(0, len(handler._buffer))

    def test_fast_insertion_of_hundred_logs(self):
        handler = ESHandler(hosts=[{'host': self.getESHost(), 'port': self.getESPort()}],
                            auth_type=ESHandler.AuthType.NO_AUTH,
                            use_ssl=False,
                            buffer_size=500,
                            flush_frequency_in_sec=0.5,
                            es_index_name=TEST_INDEX_NAME,
                            raise_on_indexing_exceptions=True)
        log = logging.getLogger(LOGGER_NAME)
        log.setLevel(logging.DEBUG)
        log.addHandler(handler)
        for i in range(100):
            log.info("Logging line {0:d}".format(i), extra={'LineNum': i})
        handler.flush()
        self.assertEqual(0, len(handler._buffer))

    def test_index_name_frequency_functions(self):
        index_name = TEST_INDEX_NAME
        handler = ESHandler(hosts=[{'host': self.getESHost(), 'port': self.getESPort()}],
                            auth_type=ESHandler.AuthType.NO_AUTH,
                            es_index_name=index_name,
                            use_ssl=False,
                            index_name_frequency=ESHandler.IndexNameFrequency.DAILY,
                            raise_on_indexing_exceptions=True)
        self.assertEqual(
            handler._index_name_func.__func__(index_name),
            ESHandler._get_daily_index_name(index_name)
        )

        handler = ESHandler(hosts=[{'host': self.getESHost(), 'port': self.getESPort()}],
                            auth_type=ESHandler.AuthType.NO_AUTH,
                            es_index_name=index_name,
                            use_ssl=False,
                            index_name_frequency=ESHandler.IndexNameFrequency.WEEKLY,
                            raise_on_indexing_exceptions=True)
        self.assertEqual(
            handler._index_name_func.__func__(index_name),
            ESHandler._get_weekly_index_name(index_name)
        )

        handler = ESHandler(hosts=[{'host': self.getESHost(), 'port': self.getESPort()}],
                            auth_type=ESHandler.AuthType.NO_AUTH,
                            es_index_name=index_name,
                            use_ssl=False,
                            index_name_frequency=ESHandler.IndexNameFrequency.MONTHLY,
                            raise_on_indexing_exceptions=True)
        self.assertEqual(
            handler._index_name_func.__func__(index_name),
            ESHandler._get_monthly_index_name(index_name)
        )

        handler = ESHandler(hosts=[{'host': self.getESHost(), 'port': self.getESPort()}],
                            auth_type=ESHandler.AuthType.NO_AUTH,
                            es_index_name=index_name,
                            use_ssl=False,
                            index_name_frequency=ESHandler.IndexNameFrequency.YEARLY,
                            raise_on_indexing_exceptions=True)
        self.assertEqual(
            handler._index_name_func.__func__(index_name),
            ESHandler._get_yearly_index_name(index_name)
        )

    def test_get_es_client_with_kwargs(self):
        ssl_context = MagicMock(spec=SSLContext)
        with patch('eslogging.handlers.Elasticsearch') as es_mock:
            handler = ESHandler(ssl_context=ssl_context, unknown_arg="unknown-value")
            es_client = handler._get_es_client()
            args, kwargs = es_mock.call_args_list[-1]
            self.assertDictContainsSubset(dict(ssl_context=ssl_context, unknown_arg="unknown-value"), kwargs, )
            self.assertEqual(es_mock.call_count, 1)




class ESHandlerIgnoreESLogsTestCase(unittest.TestCase):
    DEFAULT_ES_SERVER = 'localhost'
    DEFAULT_ES_PORT = 9200

    def getESHost(self):
        return os.getenv('TEST_ES_SERVER', ESHandlerTestCase.DEFAULT_ES_SERVER)

    def getESPort(self):
        try:
            return int(os.getenv('TEST_ES_PORT', ESHandlerTestCase.DEFAULT_ES_PORT))
        except ValueError:
            return ESHandlerTestCase.DEFAULT_ES_PORT

    def setUp(self):
        self.log = logging.getLogger(LOGGER_NAME)
        test_handler = logging.StreamHandler(stream=sys.stderr)
        self.log.addHandler(test_handler)

    def tearDown(self):
        del self.log

    def test_ping(self):
        handler = ESHandlerIgnoreESLogs(hosts=[{'host': self.getESHost(), 'port': self.getESPort()}],
                                        auth_type=ESHandler.AuthType.NO_AUTH,
                                        es_index_name=TEST_INDEX_NAME,
                                        use_ssl=False,
                                        raise_on_indexing_exceptions=True)
        es_test_server_is_up = handler.test_es_source()
        self.assertEqual(True, es_test_server_is_up)

    def test_buffered_log_insertion_flushed_when_buffer_full(self):
        handler = ESHandlerIgnoreESLogs(hosts=[{'host': self.getESHost(), 'port': self.getESPort()}],
                                        auth_type=ESHandler.AuthType.NO_AUTH,
                                        use_ssl=False,
                                        buffer_size=2,
                                        flush_frequency_in_sec=1000,
                                        es_index_name=TEST_INDEX_NAME,
                                        es_additional_fields={'App': 'Test', 'Environment': 'Dev'},
                                        raise_on_indexing_exceptions=True)

        es_test_server_is_up = handler.test_es_source()
        self.log.info("ES services status is:  {0!s}".format(es_test_server_is_up))
        self.assertEqual(True, es_test_server_is_up)

        log = logging.getLogger(LOGGER_NAME)
        log.setLevel(logging.DEBUG)
        log.addHandler(handler)
        log.warning("First Message")
        log.info("Seccond Message")
        self.assertEqual(0, len(handler._buffer))
        handler.close()

    def test_es_log_extra_argument_insertion(self):
        """ ToDo: fix this test to pass for IgnoreESLogs
        The problem here is that LogRecord gets extra arguments as members, in __dict__ property,
        ad there are also other members which are not desired to be part of ES document,
        so solution is to add an "extra" to constructor of Handler also, and search for those methods in _emit()
        by those extra saved in handler's instance.
        """
        self.log.info("About to test elasticsearch insertion")
        handler = ESHandlerIgnoreESLogs(hosts=[{'host': self.getESHost(), 'port': self.getESPort()}],
                                        auth_type=ESHandler.AuthType.NO_AUTH,
                                        use_ssl=False,
                                        es_index_name=TEST_INDEX_NAME,
                                        es_additional_fields={'App': 'Test', 'Environment': 'Dev'},
                                        raise_on_indexing_exceptions=True)

        es_test_server_is_up = handler.test_es_source()
        self.log.info("ES services status is:  {0!s}".format(es_test_server_is_up))
        self.assertEqual(True, es_test_server_is_up)

        log = logging.getLogger(LOGGER_NAME)
        log.addHandler(handler)
        log.warning("Extra arguments Message", extra={"Arg1": 300, "Arg2": 400})
        self.assertEqual(1, len(handler._buffer))
        self.assertEqual(handler._buffer[0]['Arg1'], 300)
        self.assertEqual(handler._buffer[0]['Arg2'], 400)
        self.assertEqual(handler._buffer[0]['App'], 'Test')
        self.assertEqual(handler._buffer[0]['Environment'], 'Dev')
        handler.flush()
        self.assertEqual(0, len(handler._buffer))

    def test_buffered_log_insertion_after_interval_expired(self):
        """ ToDo: fix this test to pass for IgnoreESLogs """
        handler = ESHandlerIgnoreESLogs(hosts=[{'host': self.getESHost(), 'port': self.getESPort()}],
                                        auth_type=ESHandler.AuthType.NO_AUTH,
                                        use_ssl=False,
                                        flush_frequency_in_sec=0.1,
                                        es_index_name=TEST_INDEX_NAME,
                                        es_additional_fields={'App': 'Test', 'Environment': 'Dev'},
                                        raise_on_indexing_exceptions=True)

        es_test_server_is_up = handler.test_es_source()
        self.log.info("ES services status is:  {0!s}".format(es_test_server_is_up))
        self.assertEqual(True, es_test_server_is_up)

        log = logging.getLogger(LOGGER_NAME)
        log.addHandler(handler)
        log.warning("Extra arguments Message", extra={"Arg1": 300, "Arg2": 400})
        self.assertEqual(1, len(handler._buffer))
        self.assertEqual(handler._buffer[0]['Arg1'], 300)
        self.assertEqual(handler._buffer[0]['Arg2'], 400)
        self.assertEqual(handler._buffer[0]['App'], 'Test')
        self.assertEqual(handler._buffer[0]['Environment'], 'Dev')
        time.sleep(1)
        self.assertEqual(0, len(handler._buffer))

    def test_fast_insertion_of_hundred_logs(self):
        handler = ESHandlerIgnoreESLogs(hosts=[{'host': self.getESHost(), 'port': self.getESPort()}],
                                        auth_type=ESHandler.AuthType.NO_AUTH,
                                        use_ssl=False,
                                        buffer_size=500,
                                        flush_frequency_in_sec=0.5,
                                        es_index_name=TEST_INDEX_NAME,
                                        raise_on_indexing_exceptions=True)
        log = logging.getLogger(LOGGER_NAME)
        log.setLevel(logging.DEBUG)
        log.addHandler(handler)
        for i in range(100):
            log.info("Logging line {0:d}".format(i), extra={'LineNum': i})
        handler.flush()
        self.assertEqual(0, len(handler._buffer))

    def test_index_name_frequency_functions(self):
        index_name = TEST_INDEX_NAME
        handler = ESHandlerIgnoreESLogs(hosts=[{'host': self.getESHost(), 'port': self.getESPort()}],
                                        auth_type=ESHandler.AuthType.NO_AUTH,
                                        es_index_name=index_name,
                                        use_ssl=False,
                                        index_name_frequency=ESHandler.IndexNameFrequency.DAILY,
                                        raise_on_indexing_exceptions=True)
        self.assertEqual(
            handler._index_name_func.__func__(index_name),
            ESHandler._get_daily_index_name(index_name)
        )

        handler = ESHandlerIgnoreESLogs(hosts=[{'host': self.getESHost(), 'port': self.getESPort()}],
                                        auth_type=ESHandler.AuthType.NO_AUTH,
                                        es_index_name=index_name,
                                        use_ssl=False,
                                        index_name_frequency=ESHandler.IndexNameFrequency.WEEKLY,
                                        raise_on_indexing_exceptions=True)
        self.assertEqual(
            handler._index_name_func.__func__(index_name),
            ESHandler._get_weekly_index_name(index_name)
        )

        handler = ESHandlerIgnoreESLogs(hosts=[{'host': self.getESHost(), 'port': self.getESPort()}],
                                        auth_type=ESHandler.AuthType.NO_AUTH,
                                        es_index_name=index_name,
                                        use_ssl=False,
                                        index_name_frequency=ESHandler.IndexNameFrequency.MONTHLY,
                                        raise_on_indexing_exceptions=True)
        self.assertEqual(
            handler._index_name_func.__func__(index_name),
            ESHandler._get_monthly_index_name(index_name)
        )

        handler = ESHandlerIgnoreESLogs(hosts=[{'host': self.getESHost(), 'port': self.getESPort()}],
                                        auth_type=ESHandler.AuthType.NO_AUTH,
                                        es_index_name=index_name,
                                        use_ssl=False,
                                        index_name_frequency=ESHandler.IndexNameFrequency.YEARLY,
                                        raise_on_indexing_exceptions=True)
        self.assertEqual(
            handler._index_name_func.__func__(index_name),
            ESHandlerIgnoreESLogs._get_yearly_index_name(index_name)
        )


if __name__ == '__main__':
    unittest.main()
