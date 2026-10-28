"""Couverture des zones peu testées : decks Anki, filtres de progression, certificats, fichiers protégés, notes."""

import io
import json
import sqlite3
import tempfile
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest
from django.core.files.base import ContentFile
from django.urls import reverse

from access.models import AccessRequest
from courses.anki import count_apkg_cards
from courses.models import ContentBlock, CourseCompletion, StudentNote
from courses.templatetags.progress_tags import done_count, duration, total_minutes


def build_apkg(card_count):
    """Fabrique un .apkg minimal (zip contenant une base SQLite `collection.anki2`)."""
    with tempfile.TemporaryDirectory() as folder:
        db_path = Path(folder) / 'collection.anki2'
        connection = sqlite3.connect(db_path)
        connection.execute('CREATE TABLE cards (id INTEGER PRIMARY KEY)')
        connection.executemany('INSERT INTO cards (id) VALUES (?)', [(i,) for i in range(card_count)])
        connection.commit()
        connection.close()
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as archive:
            archive.write(db_path, 'collection.anki2')
    buffer.seek(0)
    return buffer


class TestAnkiDeck:
    def test_counts_cards(self):
        assert count_apkg_cards(build_apkg(7)) == 7

    def test_unreadable_file_returns_none(self):
        assert count_apkg_cards(io.BytesIO(b'pas un zip')) is None

    def test_zip_without_collection_returns_none(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as archive:
            archive.writestr('autre.txt', 'x')
        buffer.seek(0)
        assert count_apkg_cards(buffer) is None


class TestProgressFilters:
    def test_done_count_and_total_minutes(self):
        lessons = [SimpleNamespace(id=1, duration_minutes=10), SimpleNamespace(id=2, duration_minutes=None)]
        assert done_count(lessons, {1}) == 1
        assert done_count(lessons, 'invalide') == 0
        assert done_count(lessons, None) == 0
        assert total_minutes(lessons) == 10

    @pytest.mark.parametrize(
        ('minutes', 'expected'),
        [(45, '45 min'), (90, '1 h 30'), (120, '2 h'), (0, ''), (None, ''), ('x', '')],
    )
    def test_duration(self, minutes, expected):
        assert duration(minutes) == expected


@pytest.fixture
def lesson(course):
    module = course.modules.create(title='M', order=1)
    return module.lessons.create(title='L', slug='l', order=1)


@pytest.mark.django_db
class TestCertificates:
    def test_task_stores_pdf_on_completion(self, student, course, monkeypatch):
        from courses import tasks

        monkeypatch.setattr(tasks, 'render_pdf', lambda template, context: b'%PDF-test')
        completion = CourseCompletion.objects.create(student=student, course=course)
        tasks.generate_certificate_pdf.run(completion.id)

        completion.refresh_from_db()
        assert completion.certificate_pdf.read() == b'%PDF-test'

    def test_task_ignores_empty_render(self, student, course, monkeypatch):
        from courses import tasks

        monkeypatch.setattr(tasks, 'render_pdf', lambda template, context: b'')
        completion = CourseCompletion.objects.create(student=student, course=course)
        tasks.generate_certificate_pdf.run(completion.id)

        completion.refresh_from_db()
        assert not completion.certificate_pdf

    def test_download_returns_pdf(self, client, student, course):
        completion = CourseCompletion.objects.create(student=student, course=course)
        completion.certificate_pdf.save('c.pdf', ContentFile(b'%PDF-ok'))
        client.force_login(student)

        response = client.get(reverse('download_certificate', args=[course.slug]))
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/pdf'
        assert b''.join(response.streaming_content) == b'%PDF-ok'

    def test_download_without_file_redirects_with_message(self, client, student, course):
        CourseCompletion.objects.create(student=student, course=course)
        client.force_login(student)
        response = client.get(reverse('download_certificate', args=[course.slug]))
        assert response.status_code == 302

    def test_download_requires_own_completion(self, client, student, course):
        client.force_login(student)
        assert client.get(reverse('download_certificate', args=[course.slug])).status_code == 404


@pytest.mark.django_db
class TestProtectedMedia:
    @pytest.fixture
    def file_block(self, lesson):
        block = ContentBlock.objects.create(lesson=lesson, type='file', order=1)
        block.file_content.save('doc.pdf', ContentFile(b'secret'))
        return block

    def test_enrolled_student_downloads_file(self, client, student, course, file_block):
        AccessRequest.objects.create(student=student, course=course, status='APPROVED')
        client.force_login(student)
        response = client.get(reverse('download_protected_media', args=[file_block.id, 'file_content']))
        assert response.status_code == 200
        assert b''.join(response.streaming_content) == b'secret'

    def test_other_student_is_forbidden(self, client, student, file_block):
        client.force_login(student)
        response = client.get(reverse('download_protected_media', args=[file_block.id, 'file_content']))
        assert response.status_code == 403

    def test_unknown_field_is_404(self, client, admin_user, file_block):
        client.force_login(admin_user)
        response = client.get(reverse('download_protected_media', args=[file_block.id, 'title']))
        assert response.status_code == 404

    def test_file_url_is_never_public(self, file_block):
        assert file_block.file_content.url == '#'


@pytest.mark.django_db
class TestStudentNotes:
    @pytest.fixture
    def text_block(self, lesson):
        lesson.is_free = True
        lesson.save()
        return ContentBlock.objects.create(lesson=lesson, type='text', order=1)

    def test_note_is_created_updated_and_deleted(self, client, student, course, text_block):
        client.force_login(student)
        url = reverse('save_block_note', args=[course.slug, text_block.id])
        ajax = {'headers': {'X-Requested-With': 'XMLHttpRequest'}}

        response = client.post(url, {'note_content': ' ma note '}, **ajax)
        assert json.loads(response.content) == {'ok': True, 'content': 'ma note'}
        assert StudentNote.objects.get(student=student, block=text_block).content == 'ma note'

        client.post(url, {'note_content': 'v2'}, **ajax)
        assert StudentNote.objects.filter(student=student, block=text_block).count() == 1

        client.post(url, {'note_content': '   '}, **ajax)
        assert not StudentNote.objects.exists()

    def test_note_requires_access_to_paid_lesson(self, client, student, course, text_block):
        text_block.lesson.is_free = False
        text_block.lesson.save()
        client.force_login(student)
        response = client.post(reverse('save_block_note', args=[course.slug, text_block.id]), {'note_content': 'x'})
        assert response.status_code == 403
