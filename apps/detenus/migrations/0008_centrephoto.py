from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('detenus', '0007_centre_geolocalisation'),
    ]

    operations = [
        migrations.CreateModel(
            name='CentrePhoto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='centres/photos/', verbose_name='Photo')),
                ('legende', models.CharField(blank=True, default='', max_length=200, verbose_name='Légende')),
                ('ordre', models.PositiveIntegerField(default=0, verbose_name='Ordre')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name="Date d'ajout")),
                ('centre', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='photos',
                    to='detenus.centrepenitencier',
                    verbose_name='Centre',
                )),
            ],
            options={
                'verbose_name': 'Photo du centre',
                'verbose_name_plural': 'Photos du centre',
                'ordering': ['ordre', 'id'],
            },
        ),
    ]
