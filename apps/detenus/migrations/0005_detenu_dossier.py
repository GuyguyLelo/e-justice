from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('detenus', '0004_fichedetenu'),
    ]

    operations = [
        migrations.AddField(
            model_name='detenu',
            name='dossier',
            field=models.FileField(
                blank=True,
                help_text='Fichier du dossier judiciaire (PDF, image ou document)',
                null=True,
                upload_to='detenus/dossiers/',
                verbose_name='Dossier du détenu',
            ),
        ),
    ]
