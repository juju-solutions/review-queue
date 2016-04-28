import difflib
import filecmp
import logging
import itertools
import os
import tempfile

import arrow  # noqa
import requests

from pygments.formatters import HtmlFormatter
from pygments.util import StringIO

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
        charmstore, entity_id, includes=None, get_files=False,
        channel=None):
    includes = includes or [
        'revision-info',
        'promulgated',
        'id-name',
        'owner',
    ]
    if get_files:
        includes.append('manifest')
    return charmstore._meta(entity_id, includes, channel=channel)


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

        changes = custom_dircmp(
            tmp_from_dir or self.from_dir,
            self.to_dir).report_full_closure_changes()

        # do diff
        if tmp_from_dir:
            os.rmdir(tmp_from_dir)

        return [
            c.set_root_dirs(self.from_root_dir, self.to_root_dir)
            for c in changes
        ]


class custom_dircmp(filecmp.dircmp):
    def __init__(self, *args, **kw):
        filecmp.dircmp.__init__(self, *args, **kw)
        self.methodmap['subdirs'] = custom_dircmp.phase4

    def phase3(self):
        xx = filecmp.cmpfiles(
            self.left, self.right, self.common_files, shallow=False)
        self.same_files, self.diff_files, self.funny_files = xx

    def phase4(self):
        # This method is identical to the one built-in to python, but we
        # have to override it so that subdirs use our custom dircmp class
        self.subdirs = {}
        for x in self.common_dirs:
            a_x = os.path.join(self.left, x)
            b_x = os.path.join(self.right, x)
            self.subdirs[x] = custom_dircmp(a_x, b_x, self.ignore, self.hide)

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

    def pygments_diff(self, comments, **kw):
        from pygments import highlight
        from pygments.lexers import DiffLexer

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
            TableFormatter(linenos="table", comments=comments))

    def _get_lines(self, filename):
        if not filename:
            return []
        return open(filename, 'r').readlines()


class TableFormatter(HtmlFormatter):
    def __init__(self, *args, **kw):
        self.comments = kw.pop('comments', {}) or {}
        super(TableFormatter, self).__init__(*args, **kw)

    def _wrap_tablelinenos(self, inner):
        dummyoutfile = StringIO()
        lncount = 0
        for t, line in inner:
            if t:
                lncount += 1
                dummyoutfile.write(line)

        fl = self.linenostart
        mw = len(str(lncount + fl - 1))
        sp = self.linenospecial
        st = self.linenostep
        la = self.lineanchors
        aln = self.anchorlinenos
        nocls = self.noclasses
        if sp:
            lines = []

            for i in range(fl, fl+lncount):
                if i % st == 0:
                    if i % sp == 0:
                        if aln:
                            lines.append('<a href="#%s-%d" class="special">%*d</a>' %
                                         (la, i, mw, i))
                        else:
                            lines.append('<span class="special">%*d</span>' % (mw, i))
                    else:
                        if aln:
                            lines.append('<a href="#%s-%d">%*d</a>' % (la, i, mw, i))
                        else:
                            lines.append('%*d' % (mw, i))
                else:
                    lines.append('')
            ls = '\n'.join(lines)
        else:
            lines = []
            for i in range(fl, fl+lncount):
                if i % st == 0:
                    if aln:
                        lines.append('<a href="#%s-%d">%*d</a>' % (la, i, mw, i))
                    else:
                        lines.append('%*d' % (mw, i))
                else:
                    lines.append('')
            ls = '\n'.join(lines)

        yield 0, ('<table class="%stable">' % self.cssclass)
        lineno = fl
        for lineno_html, code in itertools.izip(ls.split('\n'), dummyoutfile.getvalue().split('\n')):
            if nocls:
                yield 0, ('<tr><td><pre style="line-height: 125%">' +
                          lineno_html + '</pre></td><td class="code">' +
                          self._wrap_code_line(code) + '</td></tr>')
            else:
                yield 0, ('<tr><td class="linenos"><pre>' +
                          lineno_html + '</pre></td><td class="code">' +
                          self._wrap_code_line(code) + '</td></tr>')
            if lineno in self.comments:
                yield 0, self.render_diff_comment(lineno, self.comments[lineno])

            lineno += 1
        yield 0, '</table>'

    def render_diff_comment(self, lineno, comments):
        return render_diff_comment(lineno, comments)

    def _wrap_code_line(self, code_line):
        style = []
        if self.prestyles:
            style.append(self.prestyles)
        if self.noclasses:
            style.append('line-height: 125%')
        style = '; '.join(style)

        # the empty span here is to keep leading empty lines from being
        # ignored by HTML parsers
        return ('<pre' + (style and ' style="%s"' % style) + '><span></span>' +
                code_line + '</pre>')


def render_diff_comment(lineno, comments):
    lines = []
    lines.append('<tr><td colspan="2" class="diff-comment">')
    for c in comments:
        panel = '''
        <div class="panel panel-default">
          <div class="panel-heading">
            <a href="/users/{user}">{user}</a> commented
            <span title="{timestamp}">{human_timestamp}</span></div>
          <div class="panel-body">
            {comment}
          </div>
        </div>
        '''.format(
            user=c.user.nickname,
            timestamp=c.created_at,
            human_timestamp=arrow.get(c.created_at).humanize(),
            comment=c.text.replace('\n', '<br>'))
        lines.append(panel)
    lines.append('</td></tr>')
    return ''.join(lines)
