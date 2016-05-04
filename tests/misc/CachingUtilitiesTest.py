import calendar
import os
import unittest
import time

from pyprint.NullPrinter import NullPrinter

from coalib.misc.CachingUtilities import (
    get_cache_data_path, pickle_load, pickle_dump, delete_cache_files,
    time_consistent, update_time_db, get_changed_files)
from coalib.misc.Caching import FileCache
from coalib.output.printers.LogPrinter import LogPrinter


class CachingUtilitiesTest(unittest.TestCase):

    def setUp(self):
        current_dir = os.path.split(__file__)[0]
        self.caching_utils_test_dir = os.path.join(
            current_dir,
            "caching_utils_testfiles")
        self.log_printer = LogPrinter(NullPrinter())

    def test_pickling(self):
        test_data = {"answer": 42}

        pickle_dump(self.log_printer, "test_file", test_data)
        self.assertEqual(pickle_load(self.log_printer, "test_file"), test_data)
        os.remove(get_cache_data_path(self.log_printer, "test_file"))

        self.assertEqual(pickle_load(
            self.log_printer, "nonexistant_file"), None)
        self.assertEqual(pickle_load(
            self.log_printer, "nonexistant_file", fallback=42), 42)

    def test_corrupt_cache_files(self):
        file_path = get_cache_data_path(self.log_printer, "corrupt_file")
        with open(file_path, "wb") as f:
            data = [1] * 100
            f.write(bytes(data))

        self.assertTrue(os.path.isfile(file_path))
        self.assertEqual(pickle_load(
            self.log_printer, "corrupt_file", fallback=42), 42)

    def test_delete_cache_files(self):
        pickle_dump(self.log_printer, "coala_test", {"answer": 42})
        self.assertTrue(delete_cache_files(
            self.log_printer, files=["coala_test"]))
        self.assertFalse(os.path.isfile(get_cache_data_path(
            self.log_printer, "coala_test")))
        self.assertFalse(delete_cache_files(
            self.log_printer, files=["non_existant_file"]))

    def test_time_db(self):
        time_db = pickle_load(self.log_printer, "time_db", {})
        time_db["coala_test"] = calendar.timegm(time.gmtime()) + 100
        pickle_dump(self.log_printer, "time_db", time_db)
        self.assertFalse(time_consistent(self.log_printer, "coala_test"))
        update_time_db(self.log_printer, "coala_test")
        self.assertTrue(time_consistent(self.log_printer, "coala_test"))

    def test_get_changed_files(self):
        cache = FileCache(self.log_printer, "coala_test", flush_cache=True)
        files = ["a.c", "b.c"]
        file_paths = []

        for file_name in files:
            file_path = os.path.abspath(os.path.join(
                self.caching_utils_test_dir, file_name))
            file_paths.append(file_path)
            open(file_path, "w").close()
        self.assertEqual(get_changed_files(file_paths, cache), file_paths)

        cache.write()
        time.sleep(1)
        changed_file = file_paths[1]
        open(changed_file, "w").close()
        self.assertEqual(get_changed_files(file_paths, cache), [changed_file])
