# -*- coding: utf-8 -*-
"""Contrats des vues natives: octets exportes, noms et absence d'ecritures.

Execution avec bin/zopepy -m unittest, sans serveur SMTP ni site Plone.
La ZODB en memoire detecte une modification du PDF pendant l'export.
"""
import io
import unittest
import zipfile

from persistent import Persistent
from transaction import TransactionManager
from ZODB import DB
from ZODB.MappingStorage import MappingStorage
from zExceptions import NotFound

from senaite.trimeta.samplefields.coa import download, email, workflow, views
from senaite.trimeta.samplefields.coa.pdf import get_pdf


class Pdf(Persistent):
    def __init__(self, data, filename):
        self.data = data
        self.filename = filename


class Report(object):
    def __init__(self, uid, code, pdf):
        self.uid, self.code, self.pdf = uid, code, pdf

    def getPdf(self):
        return self.pdf

    def getId(self):
        return self.uid


class Response(object):
    def __init__(self):
        self.headers = {}
        self.body = b""
        self.location = None

    def setHeader(self, name, value):
        self.headers[name] = value

    def write(self, data):
        self.body += data

    def redirect(self, url):
        self.location = url
        return url


class Request(dict):
    def __init__(self):
        super(Request, self).__init__()
        self.response = Response()
        self.form = self

    def set(self, key, value):
        self[key] = value

    def get_header(self, key):
        return None


class Context(object):
    def __init__(self):
        self.messages = []
        self.plone_utils = self

    def absolute_url(self):
        return "http://nohost/client"

    def addPortalMessage(self, message, level):
        self.messages.append((message, level))


class EmailViewForTest(email.TrimetaEmailView):
    @property
    def reports(self):
        return self.selected

    @property
    def attachments(self):
        return []


class TestCoaDelivery(unittest.TestCase):
    def patch(self, obj, name, value):
        previous = getattr(obj, name)
        self.addCleanup(setattr, obj, name, previous)
        setattr(obj, name, value)

    def setUp(self):
        self.manager = TransactionManager()
        self.database = DB(MappingStorage())
        self.connection = self.database.open(transaction_manager=self.manager)
        self.addCleanup(self.database.close)
        self.addCleanup(self.connection.close)
        self.addCleanup(self.manager.abort)
        self.root = self.connection.root()
        self.root['one'] = Pdf(b'%PDF-1.4\nFIRST\n%%EOF', 'stored-one.pdf')
        self.root['two'] = Pdf(b'%PDF-1.4\nSECOND\n%%EOF', 'stored-two.pdf')
        self.manager.commit()
        self.one = Report('one', 'ECH 1', self.root['one'])
        self.two = Report('two', 'ech 1', self.root['two'])
        self.missing = Report('missing', 'MISSING', None)
        self.reports = dict((r.uid, r) for r in (self.one, self.two, self.missing))
        self.context, self.request = Context(), Request()
        self.patch(workflow.api, 'get_object_by_uid', lambda uid: self.reports.get(uid))
        self.patch(email.api, 'get_uid', lambda report: report.uid)
        self.patch(download.fn, 'get_report_filename',
                   lambda report: download.fn.build_filename(report.code, report.uid))

    def assert_pdfs_unchanged(self):
        for key, filename in [('one', 'stored-one.pdf'), ('two', 'stored-two.pdf')]:
            self.assertEqual(self.root[key].filename, filename)
            self.assertFalse(self.root[key]._p_changed)

    def test_single_download_preserves_bytes_and_quotes_name(self):
        download.TrimetaDownloadView(self.one, self.request)()
        self.assertEqual(self.request.response.body, self.one.pdf.data)
        self.assertEqual(self.request.response.headers['Content-Disposition'],
                         'inline; filename="ECH_1.pdf"')
        self.assertEqual(self.request.response.headers['Content-Type'], 'application/pdf')
        self.assert_pdfs_unchanged()

    def test_single_missing_or_empty_pdf_is_not_found(self):
        for pdf in (None, Pdf(b'', 'empty.pdf')):
            report = Report('empty', '', pdf)
            with self.assertRaises(NotFound):
                download.TrimetaDownloadView(report, self.request)()
        self.assertEqual(self.request.response.body, b'')

    def test_group_of_one_returns_original_pdf(self):
        workflow.TrimetaDownloadReportsAdapter(self.context, self.request)('download_reports', ['one'])
        self.assertEqual(self.request.response.body, self.one.pdf.data)
        self.assertEqual(self.request.response.headers['Content-Disposition'],
                         'attachment; filename="ECH_1.pdf"')
        self.assert_pdfs_unchanged()

    def test_zip_keeps_distinct_pdf_bytes_and_unique_case_insensitive_names(self):
        workflow.TrimetaDownloadReportsAdapter(self.context, self.request)(
            'download_reports', ['one', 'two', 'one'])
        with zipfile.ZipFile(io.BytesIO(self.request.response.body)) as archive:
            self.assertEqual(archive.namelist(), ['ECH_1.pdf', 'ech_1-2.pdf', 'ECH_1-3.pdf'])
            self.assertEqual(archive.read('ECH_1.pdf'), self.one.pdf.data)
            self.assertEqual(archive.read('ech_1-2.pdf'), self.two.pdf.data)
            self.assertEqual(archive.read('ECH_1-3.pdf'), self.one.pdf.data)
        self.assert_pdfs_unchanged()

    def test_no_pdf_redirects_without_empty_archive(self):
        result = workflow.TrimetaDownloadReportsAdapter(self.context, self.request)(
            'download_reports', ['missing', 'unknown'])
        self.assertEqual(result, self.context.absolute_url())
        self.assertEqual(self.request.response.body, b'')
        self.assertNotIn('Content-Type', self.request.response.headers)
        self.assertTrue(self.context.messages)

    def test_invalid_report_does_not_hide_the_available_one(self):
        workflow.TrimetaDownloadReportsAdapter(self.context, self.request)(
            'download_reports', ['unknown', 'one', 'missing'])
        self.assertEqual(self.request.response.body, self.one.pdf.data)
        self.assertTrue(self.context.messages)
        self.assert_pdfs_unchanged()

    def test_email_attachment_names_and_bytes_are_consistent(self):
        view = EmailViewForTest(self.context, self.request)
        view.selected = [self.one, self.two, self.missing]
        attachments = view.email_attachments
        self.assertEqual([a.get_filename() for a in attachments], ['ECH_1.pdf', 'ech_1-2.pdf'])
        self.assertEqual([a.get_payload(decode=True) for a in attachments],
                         [self.one.pdf.data, self.two.pdf.data])
        self.assertEqual(view.get_report_filename(self.two), 'ech_1-2.pdf')
        self.assert_pdfs_unchanged()

    def test_reader_tolerates_invalid_reference(self):
        self.assertIsNone(get_pdf(None))
        self.assertIsNone(get_pdf(object()))

    def test_historical_imports_use_the_same_implementations(self):
        self.assertIs(views.TrimetaDownloadView, download.TrimetaDownloadView)
        self.assertIs(views.TrimetaEmailView, email.TrimetaEmailView)
        self.assertIs(views.TrimetaDownloadReportsAdapter, workflow.TrimetaDownloadReportsAdapter)


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromTestCase(TestCoaDelivery)
