from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('detenus', '0006_cellule_structure'),
    ]

    operations = [
        migrations.AddField(
            model_name='centrepenitencier',
            name='province',
            field=models.CharField(blank=True, default='', max_length=80, verbose_name='Province'),
        ),
        migrations.AddField(
            model_name='centrepenitencier',
            name='ville',
            field=models.CharField(blank=True, default='', max_length=80, verbose_name='Ville'),
        ),
        migrations.AddField(
            model_name='centrepenitencier',
            name='latitude',
            field=models.DecimalField(blank=True, decimal_places=7, max_digits=10, null=True, verbose_name='Latitude'),
        ),
        migrations.AddField(
            model_name='centrepenitencier',
            name='longitude',
            field=models.DecimalField(blank=True, decimal_places=7, max_digits=10, null=True, verbose_name='Longitude'),
        ),
    ]
