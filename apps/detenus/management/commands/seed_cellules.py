from django.core.management.base import BaseCommand

from apps.detenus.models import Cellule, CentrePenitencier, TypePopulationCellule


STRUCTURES = {
    'C001': [
        ('A', 'Hommes', TypePopulationCellule.HOMMES, 20, 'A-%02d'),
        ('B', 'Hommes', TypePopulationCellule.HOMMES, 24, 'B-%02d'),
        ('C', 'Hommes', TypePopulationCellule.HOMMES, 10, 'C-%02d'),
        ('D', 'Hommes', TypePopulationCellule.HOMMES, 15, 'D-%02d'),
        ('F', 'Femmes', TypePopulationCellule.FEMMES, 10, 'F-%02d'),
    ],
    'PMN': [
        ('PM', 'Hommes (militaire)', TypePopulationCellule.HOMMES, 25, 'PM-%02d'),
        ('PM-F', 'Femmes (militaire)', TypePopulationCellule.FEMMES, 5, 'PM-F%d'),
    ],
}


class Command(BaseCommand):
    help = 'Cree la structure des pavillons et cellules pour C001 et PMN'

    def handle(self, *args, **options):
        created = 0
        for code_centre, pavillons in STRUCTURES.items():
            centre = CentrePenitencier.objects.filter(code=code_centre).first()
            if not centre:
                self.stderr.write('Centre %s introuvable.' % code_centre)
                continue
            for pavillon, nom, population, nombre, fmt in pavillons:
                for i in range(1, nombre + 1):
                    cell_code = fmt % i
                    _, was = Cellule.objects.get_or_create(
                        centre=centre,
                        code=cell_code,
                        defaults={
                            'pavillon': pavillon,
                            'nom_pavillon': nom,
                            'type_population': population,
                            'capacite': 4,
                            'actif': True,
                        },
                    )
                    if was:
                        created += 1
        self.stdout.write(self.style.SUCCESS('Cellules creees: %s (total %s)' % (
            created, Cellule.objects.count(),
        )))
