import difflib
import filecmp
import logging
import os
import tempfile

import arrow  # noqa
import requests

from binaryornot.check import is_binary
from theblues.charmstore import CharmStore

log = logging.getLogger(__name__)


def charmstore(settings):
    return CharmStore(settings['charmstore.api.url'])


def download_file(url):
    r = requests.get(url, stream=True)
    f = tempfile.NamedTemporaryFile(delete=False)
    log.debug('Downloading %s to %s', url, f.name)
    with f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
    return f.name


class Diff(object):
    def __init__(self, from_dir, to_dir):
        self.from_dir = from_dir
        self.to_dir = to_dir

    def get_changes(self):
        tmp_from_dir = None
        if not self.from_dir:
            tmp_from_dir = tempfile.mkdtemp()

        changes = dircmp(
            tmp_from_dir or self.from_dir,
            self.to_dir).report_full_closure_changes()

        # do diff
        if tmp_from_dir:
            os.rmdir(tmp_from_dir)

        return changes


class dircmp(filecmp.dircmp):
    def phase3(self):
        xx = filecmp.cmpfiles(
            self.left, self.right, self.common_files, shallow=False)
        self.same_files, self.diff_files, self.funny_files = xx

    def report_full_closure_changes(self):
        # Report on self and subdirs recursively
        changes = self.report_changes()
        for sd in self.subdirs.itervalues():
            changes.extend(sd.report_full_closure_changes())
        return changes

    def report_changes(self):
        # Return differences between a and b
        # print 'diff', self.left, self.right
        changes = []

        # file removed
        for f in self.left_only:
            changes.append(
                Change(os.path.join(self.left, f), None))

        # file added
        for f in self.right_only:
            fpath = os.path.join(self.right, f)
            if os.path.isdir(fpath):
                for root, dirs, files in os.walk(fpath):
                    if not files:
                        changes.append(
                            Change(None, root))
                    else:
                        changes.extend([
                            Change(None, os.path.join(root, filename))
                            for filename in files])
            else:
                changes.append(
                    Change(None, fpath))

        # file modified
        for f in self.diff_files:
            changes.append(
                Change(os.path.join(self.left, f),
                       os.path.join(self.right, f)))

        for f in self.funny_files:
            changes.append(
                Change(os.path.join(self.left, f),
                       os.path.join(self.right, f)))

        return changes


class Change(object):
    def __init__(self, left_file, right_file):
        self.left_file = left_file
        self.right_file = right_file

    @property
    def description(self):
        return self.right_file or self.left_file

    def is_binary_comparison(self):
        return (
            (self.left_file and is_binary(self.left_file)) or
            (self.right_file and is_binary(self.right_file))
        )

    def is_dir_comparison(self):
        return (
            os.path.isdir(self.left_file or '') or
            os.path.isdir(self.right_file or ''))

    def html_diff(self, **kw):
        if self.is_dir_comparison():
            return ''
        if self.is_binary_comparison():
            return ''

        from_lines = self._get_lines(self.left_file)
        to_lines = self._get_lines(self.right_file)

        diff = difflib.HtmlDiff().make_table(
            from_lines, to_lines, **kw)

        try:
            diff = diff.decode('utf-8')
        except UnicodeDecodeError:
            diff = u''

        return diff

    def _get_lines(self, filename):
        if not filename:
            return []
        return open(filename, 'r').readlines()
