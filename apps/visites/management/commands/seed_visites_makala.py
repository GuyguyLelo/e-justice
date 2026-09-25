from datetime import datetime, time, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.detenus.models import CentrePenitencier, Detenu
from apps.visites.models import StatutVisite, TypeVisiteur, Visite, Visiteur


VISITEURS_EXTRA = [
    {
        'nom': 'KABONGO', 'prenom': 'Helene', 'type': TypeVisiteur.FAMILLE,
        'piece': "Carte d'identite", 'numero': 'CI-MAK-701', 'tel': '0812220101',
        'relation': 'Soeur',
    },
    {
        'nom': 'MUTOMBO', 'prenom': 'Jacques', 'type': TypeVisiteur.AVOCAT,
        'piece': 'Barreau', 'numero': 'AV-KIN-201', 'tel': '0812220102',
        'relation': 'Conseil', 'cabinet': 'Cabinet MUTOMBO',
    },
]


class Command(BaseCommand):
    help = 'Cree 10 visites de demonstration pour la Prison centrale de Makala (C001)'

    def handle(self, *args, **options):
        centre = CentrePenitencier.objects.filter(code='C001').first()
        if not centre:
            self.stderr.write('Centre C001 (Makala) introuvable.')
            return

        visiteurs = list(Visiteur.objects.order_by('pk'))
        for row in VISITEURS_EXTRA:
            obj, created = Visiteur.objects.get_or_create(
                numero_piece=row['numero'],
                defaults={
                    'nom': row['nom'],
                    'prenom': row['prenom'],
                    'type_visiteur': row['type'],
                    'piece_identite': row['piece'],
                    'telephone': row['tel'],
                    'relation_detenu': row['relation'],
                    'cabinet_avocat': row.get('cabinet', ''),
                },
            )
            if created:
                self.stdout.write('Visiteur cree: %s %s' % (obj.nom, obj.prenom))
            visiteurs.append(obj)

        visiteurs = list(Visiteur.objects.order_by('pk'))
        detenus = list(
            Detenu.objects.filter(centre=centre, statut='INCARCERE').order_by('nom', 'prenom')
        )
        if len(detenus) < 5:
            self.stderr.write('Pas assez de detenus incarcérés à Makala.')
            return

        today = timezone.localdate()
        slots = [
            (0, StatutVisite.TERMINEE, today, time(8, 15), 30, 'Colis alimentaire'),
            (1, StatutVisite.EN_COURS, today, time(9, 45), 45, 'Documents juridiques'),
            (2, StatutVisite.PROGRAMMEE, today, time(11, 0), 30, 'Vetements propres'),
            (3, StatutVisite.PROGRAMMEE, today, time(13, 30), 30, 'Vivres'),
            (4, StatutVisite.ANNULEE, today, time(14, 15), 30, ''),
            (5, StatutVisite.REFUSEE, today, time(15, 0), 30, 'Telephone portable'),
            (6, StatutVisite.PROGRAMMEE, today, time(16, 20), 60, 'Livres'),
            (7, StatutVisite.TERMINEE, today - timedelta(days=1), time(10, 10), 30, 'Vivres'),
            (8, StatutVisite.PROGRAMMEE, today + timedelta(days=1), time(9, 20), 30, 'Colis'),
            (9, StatutVisite.TERMINEE, today - timedelta(days=3), time(11, 40), 45, 'Habits'),
        ]

        created = 0
        for i, statut, jour, heure, duree, objets in slots:
            detenu = detenus[i % len(detenus)]
            visiteur = visiteurs[i % len(visiteurs)]
            dt = timezone.make_aware(datetime.combine(jour, heure))
            if Visite.objects.filter(detenu=detenu, visiteur=visiteur, date_visite=dt).exists():
                continue
            kwargs = {
                'detenu': detenu,
                'visiteur': visiteur,
                'date_visite': dt,
                'duree_minutes': duree,
                'statut': statut,
                'objets_apportes': objets or None,
                'observations': 'Visite de demonstration — Prison centrale de Makala',
            }
            if statut == StatutVisite.REFUSEE:
                kwargs['motif_refus'] = 'Objet non autorise a l entree'
            if statut == StatutVisite.ANNULEE:
                kwargs['observations'] = 'Visite annulee par le visiteur'
            Visite.objects.create(**kwargs)
            created += 1
            self.stdout.write(
                '%s | %s %s -> %s %s | %s'
                % (dt.strftime('%d/%m/%Y %H:%M'), visiteur.nom, visiteur.prenom,
                   detenu.nom, detenu.prenom, statut)
            )

        total = Visite.objects.filter(detenu__centre=centre).count()
        self.stdout.write(self.style.SUCCESS(
            'Makala: %s visites creees (total centre: %s)' % (created, total)
        ))
