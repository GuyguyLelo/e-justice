from django.core.management.base import BaseCommand
from django.db.models.signals import post_save

from apps.detenus.models import CentrePenitencier, create_centre_admin
from apps.detenus.prisons_rdc import PRISONS_RDC


GEO_FIELDS = ('nom', 'ville', 'province', 'latitude', 'longitude', 'adresse', 'type_centre')


class Command(BaseCommand):
    help = 'Integre les prisons principales de la RDC et leur geolocalisation'

    def handle(self, *args, **options):
        post_save.disconnect(create_centre_admin, sender=CentrePenitencier)
        created = 0
        updated = 0
        try:
            for data in PRISONS_RDC:
                payload = dict(data)
                centre = CentrePenitencier.objects.filter(code=payload['code']).first()
                if centre:
                    for field in GEO_FIELDS:
                        setattr(centre, field, payload[field])
                    centre.save()
                    updated += 1
                    self.stdout.write('MAJ %s %s' % (centre.code, centre.nom))
                else:
                    payload.setdefault('capacite_actuelle', 0)
                    centre = CentrePenitencier.objects.create(**payload)
                    created += 1
                    self.stdout.write('NEW %s %s' % (centre.code, centre.nom))
        finally:
            post_save.connect(create_centre_admin, sender=CentrePenitencier)

        self.stdout.write(self.style.SUCCESS(
            'Prisons RDC : %s creees, %s mises a jour, total referentiel %s'
            % (created, updated, len(PRISONS_RDC))
        ))
