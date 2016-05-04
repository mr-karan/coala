import calendar
import os
import pickle
import time

from coalib.output.Tagging import get_user_data_dir


def get_cache_data_path(log_printer, filename):
    """
    Get the full path of ``filename`` present in the user's cache directory.

    :param log_printer: A LogPrinter object to use for logging.
    :param filename:    The file whose path needs to be expanded.
    :return:            Full path of the file, assuming it's present in the
                        user's config directory.
    """
    return os.path.join(get_user_data_dir(
        log_printer, action="caching"), filename)


def delete_cache_files(log_printer, files):
    """
    Delete the cache files after displaying a warning saying the cache
    is corrupted and will be removed.

    :param log_printer: A LogPrinter object to use for logging.
    :param files:       The list of files to be deleted.
    :return:            True if all the given files were successfully deleted.
                        False otherwise.
    """
    error_files = []
    for file_name in files:
        file_path = get_cache_data_path(log_printer, file_name)
        cache_dir = os.path.dirname(file_path)
        try:
            os.remove(file_path)
        except OSError:
            error_files.append(file_name)

    if len(error_files) > 0:
        error_files = ", ".join(error_files)
        log_printer.warn("There was a problem deleting the following "
                         "files: " + error_files + ". Please delete "
                         "them manually from " + cache_dir)
        return False

    return True


def pickle_load(log_printer, filename, fallback=None):
    """
    Get the data stored in ``filename`` present in the user
    config directory. Example usage:

    >>> from pyprint.NullPrinter import NullPrinter
    >>> from coalib.output.printers.LogPrinter import LogPrinter
    >>> log_printer = LogPrinter(NullPrinter())
    >>> test_data = {"answer": 42}
    >>> pickle_dump(log_printer, "test_file", test_data)
    >>> pickle_load(log_printer, "test_file")
    {'answer': 42}
    >>> pickle_load(log_printer, "nonexistant_file")
    >>> pickle_load(log_printer, "nonexistant_file", fallback=42)
    42


    :param log_printer: A LogPrinter object to use for logging.
    :param filename:    The name of the file present in the user config
                        directory.
    :param fallback:    Return value to fallback to in case the file doesn't
                        exist.
    :return:            Data that is present in the file, if the file exists.
                        Otherwise the ``default`` value is returned.
    """
    filename = get_cache_data_path(log_printer, filename)
    if not os.path.isfile(filename):
        return fallback
    with open(filename, "rb") as f:
        try:
            return pickle.load(f)
        except (pickle.UnpicklingError, EOFError) as e:
            log_printer.warn("The caching database is corrupted and will "
                             "be removed. Each project will be re-cached "
                             "automatically in the next run time.")
            delete_cache_files(log_printer, files=[filename])
            return fallback


def pickle_dump(log_printer, filename, data):
    """
    Write ``data`` into the file ``filename`` present in the user
    config directory.

    :param log_printer: A LogPrinter object to use for logging.
    :param filename:    The name of the file present in the user config
                        directory.
    :param data:        Data to be serialized and written to the file using
                        pickle.
    """
    filename = get_cache_data_path(log_printer, filename)
    with open(filename, "wb") as f:
        return pickle.dump(data, f)


def time_consistent(log_printer, project_hash):
    """
    Verify if time is consistent with the last time was run. That is,
    verify that the last run time is in the past. Otherwise, the
    system time was changed and we need to flush the cache and rebuild.

    :param log_printer:  A LogPrinter object to use for logging.
    :param project_hash: A MD5 hash of the project directory to be used
                         as the key.
    :return:             Returns True if the time is consistent and as
                         expected; False otherwise.
    """
    time_db = pickle_load(log_printer, "time_db", {})
    if project_hash not in time_db:
        return False
    return time_db[project_hash] <= calendar.timegm(time.gmtime())


def update_time_db(log_printer, project_hash):
    """
    Update the last run time on the project.

    :param log_printer:  A LogPrinter object to use for logging.
    :param project_hash: A MD5 hash of the project directory to be used
                         as the key.
    """
    time_db = pickle_load(log_printer, "time_db", {})
    time_db[project_hash] = calendar.timegm(time.gmtime())
    pickle_dump(log_printer, "time_db", time_db)


def get_changed_files(files, cache):
    """
    Extract the list of files that had changed (or are new) with respect to
    the given ``cache`` data available.

    :param files: The list of collected files.
    :param cache: An instance of ``misc.Caching.FileCache`` to use as
                  a file cache buffer.
    :return:      The list of files that had changed since the last cache.
    """
    last_cache = None
    if cache:
        last_cache = cache.last_cache()
    changed_files = []

    if last_cache is None:
        # The first run on this project. So all files are new
        # and must be returned irrespective of whether caching is turned on.
        changed_files = files
    else:
        new_files = []
        for file_path in files:
            last_run = -1
            if file_path in last_cache:
                last_run = last_cache[file_path]
            else:
                new_files.append(file_path)
            if int(os.path.getmtime(file_path)) > last_run:
                changed_files.append(file_path)
    if cache:
        cache.track_new_files(new_files)
        cache.add_to_changed_files(changed_files)

    return changed_files
