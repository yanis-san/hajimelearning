from django.db import migrations

REASONS = ['Cours particulier', 'Conditions Generales', 'Mentions Legales', 'Confidentialite']


def seed_reasons(apps, schema_editor):
    ContactReason = apps.get_model('contact', 'ContactReason')
    for order, label in enumerate(REASONS, start=10):
        ContactReason.objects.get_or_create(label=label, defaults={'order': order, 'is_active': True})


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_reasons, migrations.RunPython.noop),
    ]
