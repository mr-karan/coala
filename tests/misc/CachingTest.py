import unittest
import time

from pyprint.NullPrinter import NullPrinter

from coalib.misc.Caching import FileCache
from coalib.output.printers.LogPrinter import LogPrinter


class CachingTest(unittest.TestCase):

    def setUp(self):
        self.log_printer = LogPrinter(NullPrinter())
        self.cache = FileCache(self.log_printer, "coala_test", flush_cache=True)

    def test_track_new_files(self):
        self.cache.track_new_files(["test.c", "file.py"])
        data = self.cache.last_cache()
        self.assertEqual(data, {"test.c": -1, "file.py": -1})

    def test_write(self):
        self.cache.track_new_files(["test2.c"])

        data = self.cache.last_cache()
        self.assertEqual(data["test2.c"], -1)

        self.cache.write()
        data = self.cache.last_cache()
        self.assertNotEqual(data["test2.c"], -1)

    def test_self_add_to_changed_files(self):
        self.cache.track_new_files(["test3.c"])

        data = self.cache.last_cache()
        self.assertEqual(data["test3.c"], -1)

        self.cache.write()
        data = self.cache.last_cache()
        old_time = data["test3.c"]
        self.cache.add_to_changed_files({"test3.c"})
        self.cache.write()
        data = self.cache.last_cache()
        self.assertEqual(old_time, data["test3.c"])

        self.cache.track_new_files(["a.c", "b.c"])
        self.cache.write()
        old_data = self.cache.last_cache().copy()
        time.sleep(1)
        self.cache.add_to_changed_files({"a.c"})
        self.cache.write()
        new_data = self.cache.last_cache().copy()
        # Since b.c had not changed, the time would have been updated.
        self.assertNotEqual(old_data["b.c"], new_data["b.c"])
        # Since a.c had changed, the time would still be the initial
        # value of -1.
        self.assertEqual(old_data["a.c"], new_data["a.c"])
