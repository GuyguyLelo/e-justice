from datetime import date, datetime, time, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.detenus.models import CentrePenitencier, Detenu
from apps.personnel.models import Personnel, StatutPersonnel, TypePersonnel
from apps.visites.models import StatutVisite, TypeVisiteur, Visite, Visiteur


VISITEURS = [
    {'nom': 'KABEYA', 'prenom': 'Celine', 'type': TypeVisiteur.FAMILLE, 'piece': 'Carte d identite', 'numero': 'CI-450021', 'tel': '0811110001', 'relation': 'Epouse'},
    {'nom': 'MWANZA', 'prenom': 'Paul', 'type': TypeVisiteur.AVOCAT, 'piece': 'Barreau', 'numero': 'AV-KIN-88', 'tel': '0811110002', 'relation': 'Conseil', 'cabinet': 'Cabinet MWANZA'},
    {'nom': 'LUFUNGULA', 'prenom': 'Ange', 'type': TypeVisiteur.FAMILLE, 'piece': 'Carte d identite', 'numero': 'CI-450022', 'tel': '0811110003', 'relation': 'Frere'},
    {'nom': 'NGOMA', 'prenom': 'Esther', 'type': TypeVisiteur.AMI, 'piece': 'Passeport', 'numero': 'CD-889120', 'tel': '0811110004', 'relation': 'Amie'},
    {'nom': 'Tshimanga', 'prenom': 'Robert', 'type': TypeVisiteur.REPRESENTANT_LEGAL, 'piece': 'Carte d identite', 'numero': 'CI-450023', 'tel': '0811110005', 'relation': 'Tuteur'},
]

PERSONNEL_C001 = [
    ('PER-C001-01', 'KALALA', 'Joseph', TypePersonnel.DIRECTEUR),
    ('PER-C001-02', 'MBUYI', 'Patrick', TypePersonnel.GARDIEN),
    ('PER-C001-03', 'ILUNGA', 'Marie', TypePersonnel.INFIRMIER),
    ('PER-C001-04', 'KASONGO', 'Alain', TypePersonnel.AGENT_SECURITE),
    ('PER-C001-05', 'NSIMBA', 'Grace', TypePersonnel.AGENT_ADMINISTRATIF),
    ('PER-C001-06', 'LUMBU', 'Jean', TypePersonnel.CUISINIER),
]

PERSONNEL_PMN = [
    ('PER-PMN-01', 'MUKENDI', 'Serge', TypePersonnel.DIRECTEUR),
    ('PER-PMN-02', 'KABONGO', 'David', TypePersonnel.GARDIEN),
    ('PER-PMN-03', 'NGOY', 'Christian', TypePersonnel.GARDIEN),
    ('PER-PMN-04', 'KALONJI', 'Helene', TypePersonnel.MEDECIN),
    ('PER-PMN-05', 'MBALA', 'Pierre', TypePersonnel.AGENT_SECURITE),
    ('PER-PMN-06', 'KABANGE', 'Sophie', TypePersonnel.INFIRMIER),
    ('PER-PMN-07', 'TSHISEKEDI', 'Michel', TypePersonnel.AGENT_ADMINISTRATIF),
    ('PER-PMN-08', 'MUJINGA', 'Albert', TypePersonnel.PSYCHOLOGUE),
    ('PER-PMN-09', 'TSAVA', 'Jeanne', TypePersonnel.AGENT_SECURITE),
    ('PER-PMN-10', 'KANDOLO', 'Elie', TypePersonnel.GARDIEN),
    ('PER-PMN-11', 'KABASELE', 'Marc', TypePersonnel.GARDIEN),
    ('PER-PMN-12', 'MWAMBA', 'Chantal', TypePersonnel.NETTOYEUR),
    ('PER-PMN-13', 'TSHIMANGA', 'Dieudonne', TypePersonnel.CUISINIER),
    ('PER-PMN-14', 'KABUYA', 'Olivier', TypePersonnel.AGENT_SECURITE),
    ('PER-PMN-15', 'LUNGA', 'Patricia', TypePersonnel.AGENT_ADMINISTRATIF),
    ('PER-PMN-16', 'MUTEBA', 'Francois', TypePersonnel.GARDIEN),
    ('PER-PMN-17', 'KAZADI', 'Benjamin', TypePersonnel.GARDIEN),
]


class Command(BaseCommand):
    help = 'Cree 5 visiteurs, 10 visites, 6 personnels (Makala) et 17 (Ndolo)'

    def handle(self, *args, **options):
        c001 = CentrePenitencier.objects.filter(code='C001').first()
        pmn = CentrePenitencier.objects.filter(code='PMN').first()
        if not c001 or not pmn:
            self.stderr.write('Centres C001 et PMN requis.')
            return

        visiteurs = []
        for row in VISITEURS:
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
            visiteurs.append(obj)
            self.stdout.write(('OK' if created else 'SKIP') + ' visiteur ' + row['nom'])

        created_p = 0
        for matricule, nom, prenom, typ in PERSONNEL_C001 + PERSONNEL_PMN:
            centre = c001 if matricule.startswith('PER-C001') else pmn
            _, was = Personnel.objects.get_or_create(
                matricule=matricule,
                defaults={
                    'nom': nom,
                    'prenom': prenom,
                    'type_personnel': typ,
                    'statut': StatutPersonnel.ACTIF,
                    'date_embauche': date(2021, 3, 1),
                    'centre': centre,
                    'telephone': '0812%04d' % (hash(matricule) % 9000 + 1000),
                    'heures_travail_semaine': 40,
                },
            )
            if was:
                created_p += 1
        self.stdout.write('Personnel cree: %s' % created_p)

        detenus_c001 = list(Detenu.objects.filter(centre=c001, statut='INCARCERE')[:6])
        detenus_pmn = list(Detenu.objects.filter(centre=pmn, statut='INCARCERE')[:5])
        if len(detenus_c001) < 2 or not detenus_pmn:
            self.stderr.write('Pas assez de detenus incarcérés.')
            return

        today = timezone.localdate()
        now = timezone.now()
        pairs = [
            (detenus_c001[0], visiteurs[0], StatutVisite.PROGRAMMEE, today, time(9, 0)),
            (detenus_c001[1], visiteurs[1], StatutVisite.EN_COURS, today, time(10, 30)),
            (detenus_c001[2], visiteurs[2], StatutVisite.TERMINEE, today, time(8, 0)),
            (detenus_c001[3], visiteurs[0], StatutVisite.PROGRAMMEE, today, time(14, 0)),
            (detenus_c001[4], visiteurs[3], StatutVisite.ANNULEE, today, time(11, 0)),
            (detenus_pmn[0], visiteurs[1], StatutVisite.PROGRAMMEE, today, time(9, 30)),
            (detenus_pmn[1], visiteurs[4], StatutVisite.EN_COURS, today, time(13, 0)),
            (detenus_pmn[2], visiteurs[2], StatutVisite.TERMINEE, today, time(8, 30)),
            (detenus_c001[0], visiteurs[4], StatutVisite.PROGRAMMEE, today - timedelta(days=2), time(15, 0)),
            (detenus_pmn[0], visiteurs[3], StatutVisite.TERMINEE, today - timedelta(days=1), time(16, 0)),
        ]

        created_v = 0
        for detenu, visiteur, statut, jour, heure in pairs:
            dt = timezone.make_aware(datetime.combine(jour, heure))
            exists = Visite.objects.filter(detenu=detenu, visiteur=visiteur, date_visite=dt).exists()
            if exists:
                continue
            Visite.objects.create(
                detenu=detenu,
                visiteur=visiteur,
                date_visite=dt,
                duree_minutes=30,
                statut=statut,
                objets_apportes='Vivres et vetements',
                observations='Donnees de demonstration',
            )
            created_v += 1

        celine = visiteurs[0]
        visite_ref = (
            Visite.objects.filter(visiteur=celine)
            .select_related('detenu')
            .order_by('pk')
            .first()
        )
        detenu_ref = visite_ref.detenu if visite_ref else detenus_c001[0]
        extra_celine = [
            (StatutVisite.TERMINEE, today - timedelta(days=21), time(10, 0), 'Colis alimentaire', 'Visite familiale mensuelle'),
            (StatutVisite.TERMINEE, today - timedelta(days=7), time(11, 30), 'Vetements propres', 'Suivi regulier'),
            (StatutVisite.PROGRAMMEE, today + timedelta(days=7), time(9, 0), 'Vivres', 'Prochaine visite planifiee'),
        ]
        for statut, jour, heure, objets, obs in extra_celine:
            dt = timezone.make_aware(datetime.combine(jour, heure))
            exists = Visite.objects.filter(detenu=detenu_ref, visiteur=celine, date_visite=dt).exists()
            if exists:
                continue
            Visite.objects.create(
                detenu=detenu_ref,
                visiteur=celine,
                date_visite=dt,
                duree_minutes=30,
                statut=statut,
                objets_apportes=objets,
                observations=obs,
            )
            created_v += 1
        self.stdout.write(self.style.SUCCESS(
            'Visiteurs: %s | Visites creees: %s | Personnel total: %s'
            % (Visiteur.objects.count(), created_v, Personnel.objects.count())
        ))
