#!/usr/bin/env python3
"""Verifie l'archive complete avant de la publier ou de la restaurer."""
import argparse
import gzip
import pathlib
import tarfile


def validate(path):
    # Force aussi la verification du CRC gzip apres la fin du flux tar.
    with gzip.open(path, 'rb') as stream:
        while stream.read(1024 * 1024):
            pass
    found_db = False
    found_blobs = False
    names = set()
    count = 0
    with tarfile.open(path, 'r|gz') as archive:
        for member in archive:
            name = pathlib.PurePosixPath(member.name)
            if name.is_absolute() or '..' in name.parts:
                raise ValueError('Chemin dangereux: ' + member.name)
            normalized = str(name)
            if normalized in names:
                raise ValueError('Entree dupliquee: ' + member.name)
            names.add(normalized)
            if not (member.isdir() or member.isfile()):
                raise ValueError('Type de fichier refuse: ' + member.name)
            if normalized.startswith('blobstorage/') or normalized == 'blobstorage':
                found_blobs = True
            if member.isfile():
                stream = archive.extractfile(member)
                header = stream.read(4)
                if normalized == 'filestorage/Data.fs':
                    if header != b'FS21' or member.size <= 4:
                        raise ValueError('Data.fs vide ou format ZODB invalide')
                    found_db = True
                # Lire integralement pour detecter les archives tronquees.
                while stream.read(1024 * 1024):
                    pass
                count += 1
    if not found_db or not found_blobs:
        raise ValueError('Archive incomplete: Data.fs et blobstorage requis')
    print('Archive verifiee: ZODB, blobs et %d fichiers' % count)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive')
    args = parser.parse_args()
    try:
        validate(args.archive)
    except (ValueError, OSError, tarfile.TarError, EOFError) as exc:
        parser.exit(1, 'ERREUR: %s\n' % exc)
