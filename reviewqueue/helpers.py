import difflib
import filecmp
import logging
import os
import tempfile

import arrow  # noqa
import requests

from binaryornot.check import is_binary
from launchpadlib.launchpad import Launchpad
from theblues.charmstore import CharmStore

log = logging.getLogger(__name__)


def human_vote(vote):
    """Return integer ``vote`` as a +/- string"""
    if vote < 0:
        return '-{}'.format(vote)
    else:
        return '+{}'.format(vote)


def human_status(status):
    """Return string ``status`` as a human-friendly string"""
    return " ".join(s.capitalize() for s in status.split('_'))


def get_lp(login=True):
    if not login:
        return Launchpad.login_anonymously('review-queue', 'production')

    return Launchpad.login_with(
        'review-queue', 'production',
        credentials_file='lp-creds',
        credential_save_failed=lambda: None)


def charmstore(settings):
    return CharmStore(settings['charmstore.api.url'])


def get_charmstore_entity(
        charmstore, entity_id, includes=None, get_files=False):
    includes = includes or [
        'revision-info',
        'promulgated',
        'id-name'
    ]
    if get_files:
        includes.append('manifest')
    return charmstore._meta(entity_id, includes)


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
    def __init__(self, from_dir, to_dir, from_root_dir=None, to_root_dir=None):
        self.from_dir = from_dir
        self.to_dir = to_dir
        self.from_root_dir = from_root_dir
        self.to_root_dir = to_root_dir

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

        return [
            c.set_root_dirs(self.from_root_dir, self.to_root_dir)
            for c in changes
        ]


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
        self.from_root_dir = None
        self.to_root_dir = None

    def set_root_dirs(self, from_root_dir, to_root_dir):
        self.from_root_dir = from_root_dir
        self.to_root_dir = to_root_dir
        return self

    @property
    def description(self):
        return self.relative_right_file_path or self.relative_left_file_path

    @property
    def relative_right_file_path(self):
        return self.relative_file_path(
            self.to_root_dir, self.right_file)

    @property
    def relative_left_file_path(self):
        return self.relative_file_path(
            self.from_root_dir, self.left_file)

    def relative_file_path(self, root_path, file_path):
        if not (root_path and file_path and
                file_path.startswith(root_path)):
            return file_path or ''
        return file_path[len(root_path):].strip(os.sep)

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

    def pygments_diff(self, **kw):
        from pygments import highlight
        from pygments.lexers import DiffLexer
        from pygments.formatters import HtmlFormatter

        if self.is_dir_comparison():
            return ''
        if self.is_binary_comparison():
            return ''

        from_lines = self._get_lines(self.left_file)
        to_lines = self._get_lines(self.right_file)
        if not (from_lines or to_lines):
            return ''

        diff_lines = difflib.unified_diff(
            from_lines, to_lines,
            fromfile=self.relative_left_file_path,
            tofile=self.relative_right_file_path,
        )
        diff_text = ''.join(diff_lines)
        return highlight(
            diff_text,
            DiffLexer(),
            HtmlFormatter(linenos=True))

    def _get_lines(self, filename):
        if not filename:
            return []
        return open(filename, 'r').readlines()
