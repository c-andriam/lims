#!/usr/bin/env python3
"""Tests des archives: corruption, base absente et chemins dangereux."""
import importlib.util
import io
import pathlib
import tarfile
import tempfile
import unittest

spec = importlib.util.spec_from_file_location(
    'validate_backup', pathlib.Path(__file__).with_name('validate-backup.py'))
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = pathlib.Path(self.tmp.name) / 'backup.tar.gz'

    def archive(self, entries):
        with tarfile.open(self.path, 'w:gz') as archive:
            for name, data in entries:
                member = tarfile.TarInfo(name)
                member.size = len(data)
                archive.addfile(member, io.BytesIO(data))

    def test_complete_archive(self):
        self.archive([('filestorage/Data.fs', b'FS21test'),
                      ('blobstorage/.layout', b'bushy')])
        validator.validate(self.path)

    def test_missing_blobs_is_rejected(self):
        self.archive([('filestorage/Data.fs', b'FS21test')])
        with self.assertRaises(ValueError):
            validator.validate(self.path)

    def test_empty_database_is_rejected(self):
        self.archive([('filestorage/Data.fs', b'FS21'),
                      ('blobstorage/.layout', b'bushy')])
        with self.assertRaises(ValueError):
            validator.validate(self.path)

    def test_truncated_gzip_is_rejected(self):
        self.archive([('filestorage/Data.fs', b'FS21test'),
                      ('blobstorage/.layout', b'bushy')])
        self.path.write_bytes(self.path.read_bytes()[:-8])
        with self.assertRaises(EOFError):
            validator.validate(self.path)

    def test_path_traversal_is_rejected(self):
        self.archive([('../escape', b'invalide')])
        with self.assertRaises(ValueError):
            validator.validate(self.path)

    def test_link_is_rejected(self):
        with tarfile.open(self.path, 'w:gz') as archive:
            member = tarfile.TarInfo('escape')
            member.type = tarfile.SYMTYPE
            member.linkname = '/etc'
            archive.addfile(member)
        with self.assertRaises(ValueError):
            validator.validate(self.path)


if __name__ == '__main__':
    unittest.main()
