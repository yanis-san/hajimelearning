"""Lecture des decks Anki (.apkg) : comptage des cartes."""
import contextlib
import io
import logging
import os
import sqlite3
import tempfile
import zipfile

logger = logging.getLogger(__name__)

# Ordre de priorité : les exports récents contiennent un faux `collection.anki2`
# (1 carte « mettez Anki à jour ») à côté du vrai `collection.anki21b`.
_COLLECTION_NAMES = ('collection.anki21b', 'collection.anki21', 'collection.anki2')


def _decompress_zstd(data):
    try:
        import zstandard
    except ImportError:
        return None
    with zstandard.ZstdDecompressor().stream_reader(io.BytesIO(data)) as reader:
        return reader.read()


def count_apkg_cards(fileobj):
    """
    Retourne le nombre de cartes d'un .apkg, ou None si illisible.
    `fileobj` : fichier ouvert (UploadedFile, FieldFile...) positionnable.
    """
    tmp_path = None
    try:
        if hasattr(fileobj, 'seek'):
            fileobj.seek(0)
        with zipfile.ZipFile(fileobj) as zf:
            names = set(zf.namelist())
            name = next((n for n in _COLLECTION_NAMES if n in names), None)
            if name is None:
                return None
            data = zf.read(name)
            if name.endswith('21b'):
                data = _decompress_zstd(data)
                if data is None:
                    # Ne pas retomber sur collection.anki2 : c'est un leurre.
                    return None

        fd, tmp_path = tempfile.mkstemp(suffix='.anki2')
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
        conn = sqlite3.connect(tmp_path)
        try:
            (count,) = conn.execute('SELECT COUNT(*) FROM cards').fetchone()
        finally:
            conn.close()
        return int(count)
    except Exception:
        logger.warning("Impossible de lire le deck Anki", exc_info=True)
        return None
    finally:
        if hasattr(fileobj, 'seek'):
            with contextlib.suppress(Exception):
                fileobj.seek(0)
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
