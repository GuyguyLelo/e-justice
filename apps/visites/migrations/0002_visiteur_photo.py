from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('visites', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='visiteur',
            name='photo',
            field=models.ImageField(
                blank=True,
                help_text="Photo d'identité du visiteur",
                null=True,
                upload_to='visiteurs/photos/',
                verbose_name='Photo',
            ),
        ),
    ]
