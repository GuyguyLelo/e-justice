from datetime import date, timedelta

from django.core.management.base import BaseCommand

from apps.comptes.models import Utilisateur
from apps.detenus.models import CentrePenitencier, Detenu, StatutDetenu, TypePeine


DETENUS_TEST = [
    {
        'matricule': 'M0101', 'nom': 'MBALA', 'prenom': 'Jean-Pierre', 'sexe': 'M',
        'date_naissance': date(1988, 3, 12), 'lieu_naissance': 'Kinshasa',
        'profession': 'Commerçant', 'cellule': 'A-12',
        'motif': 'Vol aggravé', 'tribunal': 'TGI Kinshasa/Gombe',
        'regime': TypePeine.CONDAMNE, 'statut': StatutDetenu.INCARCERE,
        'peine': 36, 'jours_incarc': 420, 'centre_code': 'C001',
    },
    {
        'matricule': 'M0102', 'nom': 'KABANGE', 'prenom': 'Marie', 'sexe': 'F',
        'date_naissance': date(1992, 7, 4), 'lieu_naissance': 'Lubumbashi',
        'profession': 'Couturière', 'cellule': 'F-03',
        'motif': 'Escroquerie', 'tribunal': 'TGI Lubumbashi',
        'regime': TypePeine.PREVENTIF, 'statut': StatutDetenu.INCARCERE,
        'peine': None, 'jours_incarc': 80, 'centre_code': 'C001',
    },
    {
        'matricule': 'M0103', 'nom': 'ILUNGA', 'prenom': 'Patrick', 'sexe': 'M',
        'date_naissance': date(1985, 11, 21), 'lieu_naissance': 'Mbuji-Mayi',
        'profession': 'Chauffeur', 'cellule': 'B-07',
        'motif': 'Coups et blessures volontaires', 'tribunal': 'TGI Mbuji-Mayi',
        'regime': TypePeine.CONDAMNE, 'statut': StatutDetenu.INCARCERE,
        'peine': 24, 'jours_incarc': 200, 'centre_code': 'C001',
    },
    {
        'matricule': 'M0104', 'nom': 'NSIMBA', 'prenom': 'Grace', 'sexe': 'F',
        'date_naissance': date(1996, 1, 18), 'lieu_naissance': 'Matadi',
        'profession': 'Étudiante', 'cellule': 'F-08',
        'motif': 'Recel', 'tribunal': 'TGI Matadi',
        'regime': TypePeine.PREVENTIF, 'statut': StatutDetenu.INCARCERE,
        'peine': None, 'jours_incarc': 45, 'centre_code': 'C001',
    },
    {
        'matricule': 'M0105', 'nom': 'MUAMBA', 'prenom': 'Dieudonné', 'sexe': 'M',
        'date_naissance': date(1979, 5, 9), 'lieu_naissance': 'Kananga',
        'profession': 'Agriculteur', 'cellule': 'C-02',
        'motif': 'Trafic de stupéfiants', 'tribunal': 'TGI Kananga',
        'regime': TypePeine.CONDAMNE, 'statut': StatutDetenu.INCARCERE,
        'peine': 60, 'jours_incarc': 900, 'centre_code': 'C001',
    },
    {
        'matricule': 'M0106', 'nom': 'LUMBU', 'prenom': 'Alain', 'sexe': 'M',
        'date_naissance': date(1990, 9, 30), 'lieu_naissance': 'Kisangani',
        'profession': 'Mécanicien', 'cellule': 'A-18',
        'motif': 'Vol à main armée', 'tribunal': 'TGI Kisangani',
        'regime': TypePeine.CONDAMNE, 'statut': StatutDetenu.INCARCERE,
        'peine': 84, 'jours_incarc': 310, 'centre_code': 'C001',
    },
    {
        'matricule': 'M0107', 'nom': 'MWAMBA', 'prenom': 'Sophie', 'sexe': 'F',
        'date_naissance': date(1994, 12, 2), 'lieu_naissance': 'Goma',
        'profession': 'Commerçante', 'cellule': 'F-01',
        'motif': 'Faux et usage de faux', 'tribunal': 'TGI Goma',
        'regime': TypePeine.CONDAMNE, 'statut': StatutDetenu.LIBERE,
        'peine': 12, 'jours_incarc': 400, 'centre_code': 'C001',
        'liberation': date(2025, 11, 2),
    },
    {
        'matricule': 'M0108', 'nom': 'KASONGO', 'prenom': 'Emmanuel', 'sexe': 'M',
        'date_naissance': date(1982, 4, 14), 'lieu_naissance': 'Kolwezi',
        'profession': 'Mineur', 'cellule': 'D-11',
        'motif': 'Association de malfaiteurs', 'tribunal': 'TGI Kolwezi',
        'regime': TypePeine.CONDAMNE, 'statut': StatutDetenu.TRANSFERE,
        'peine': 48, 'jours_incarc': 150, 'centre_code': 'C001',
    },
    {
        'matricule': 'M0109', 'nom': 'KABASELE', 'prenom': 'David', 'sexe': 'M',
        'date_naissance': date(1998, 8, 8), 'lieu_naissance': 'Kinshasa',
        'profession': 'Étudiant', 'cellule': 'B-21',
        'motif': 'Outrage et rébellion', 'tribunal': 'TGI Kinshasa/Kalamu',
        'regime': TypePeine.PREVENTIF, 'statut': StatutDetenu.INCARCERE,
        'peine': None, 'jours_incarc': 22, 'centre_code': 'C001',
    },
    {
        'matricule': 'M0110', 'nom': 'MUKENDI', 'prenom': 'Joseph', 'sexe': 'M',
        'date_naissance': date(1975, 2, 27), 'lieu_naissance': 'Kananga',
        'profession': 'Fonctionnaire', 'cellule': 'PM-04',
        'motif': "Desertion et vol d'armes", 'tribunal': 'CM Kinshasa',
        'regime': TypePeine.CONDAMNE, 'statut': StatutDetenu.INCARCERE,
        'peine': 120, 'jours_incarc': 640, 'centre_code': 'PMN',
    },
    {
        'matricule': 'M0111', 'nom': 'KABONGO', 'prenom': 'Serge', 'sexe': 'M',
        'date_naissance': date(1987, 6, 16), 'lieu_naissance': 'Kinshasa',
        'profession': 'Militaire', 'cellule': 'PM-09',
        'motif': 'Insubordination grave', 'tribunal': 'CM Kinshasa',
        'regime': TypePeine.PREVENTIF, 'statut': StatutDetenu.INCARCERE,
        'peine': None, 'jours_incarc': 110, 'centre_code': 'PMN',
    },
    {
        'matricule': 'M0112', 'nom': 'NGOY', 'prenom': 'Christian', 'sexe': 'M',
        'date_naissance': date(1991, 10, 5), 'lieu_naissance': 'Lubumbashi',
        'profession': 'Électricien', 'cellule': 'PM-15',
        'motif': 'Extorsion', 'tribunal': 'TGI Kinshasa/Ndjili',
        'regime': TypePeine.CONDAMNE, 'statut': StatutDetenu.INCARCERE,
        'peine': 18, 'jours_incarc': 95, 'centre_code': 'PMN',
    },
    {
        'matricule': 'M0113', 'nom': 'KALALA', 'prenom': 'Hélène', 'sexe': 'F',
        'date_naissance': date(1989, 3, 3), 'lieu_naissance': 'Bukavu',
        'profession': 'Infirmière', 'cellule': 'PM-F2',
        'motif': 'Corruption', 'tribunal': 'TGI Bukavu',
        'regime': TypePeine.CONDAMNE, 'statut': StatutDetenu.INCARCERE,
        'peine': 30, 'jours_incarc': 180, 'centre_code': 'PMN',
    },
    {
        'matricule': 'M0114', 'nom': 'TSHIMANGA', 'prenom': 'Michel', 'sexe': 'M',
        'date_naissance': date(1984, 12, 25), 'lieu_naissance': 'Tshikapa',
        'profession': 'Commerçant', 'cellule': 'PM-22',
        'motif': 'Homicide involontaire', 'tribunal': 'TGI Tshikapa',
        'regime': TypePeine.CONDAMNE, 'statut': StatutDetenu.INCARCERE,
        'peine': 72, 'jours_incarc': 500, 'centre_code': 'PMN',
    },
]


class Command(BaseCommand):
    help = 'Intègre 14 détenus de test (matricules M0101 à M0114)'

    def handle(self, *args, **options):
        centres = {c.code: c for c in CentrePenitencier.objects.all()}
        if 'C001' not in centres or 'PMN' not in centres:
            self.stderr.write('Centres C001 et/ou PMN introuvables.')
            return

        created_by = (
            Utilisateur.objects.filter(username='admin1').first()
            or Utilisateur.objects.filter(is_superuser=True).first()
        )
        today = date.today()
        created = 0
        skipped = 0

        for row in DETENUS_TEST:
            centre = centres[row['centre_code']]
            incarceration = today - timedelta(days=row['jours_incarc'])
            arrestation = incarceration - timedelta(days=3)
            liberation_prevue = None
            if row['peine']:
                liberation_prevue = incarceration + timedelta(days=row['peine'] * 30)

            defaults = {
                'nom': row['nom'],
                'prenom': row['prenom'],
                'sexe': row['sexe'],
                'date_naissance': row['date_naissance'],
                'lieu_naissance': row['lieu_naissance'],
                'nationalite': 'Congolaise',
                'profession': row['profession'],
                'adresse': f"Commune test, {row['lieu_naissance']}",
                'centre': centre,
                'date_arrestation': arrestation,
                'date_incarceration': incarceration,
                'motif_incarceration': row['motif'],
                'tribunal': row['tribunal'],
                'numero_dossier': f"RP/{row['matricule']}/2024",
                'avocat': 'Me. KABUYA Paul',
                'cellule': row['cellule'],
                'regime': row['regime'],
                'statut': row['statut'],
                'duree_peine_mois': row['peine'],
                'date_liberation_prevue': liberation_prevue,
                'date_liberation_effective': row.get('liberation'),
                'couleur_yeux': 'MARRON',
                'couleur_cheveux': 'NOIR',
                'type_cheveux': 'CREPU',
                'couleur_peau': 'NOIR',
                'created_by': created_by,
            }
            _, was_created = Detenu.objects.get_or_create(
                matricule=row['matricule'],
                defaults=defaults,
            )
            if was_created:
                created += 1
                self.stdout.write(f'OK {row["matricule"]} {row["nom"]} {row["prenom"]} ({centre.code})')
            else:
                skipped += 1
                self.stdout.write(f'- déjà présent : {row["matricule"]}')

        for centre in centres.values():
            n = Detenu.objects.filter(centre=centre, statut=StatutDetenu.INCARCERE).count()
            centre.capacite_actuelle = n
            centre.save(update_fields=['capacite_actuelle'])

        self.stdout.write(self.style.SUCCESS(
            f'{created} détenu(s) créé(s), {skipped} déjà en base. Total : {Detenu.objects.count()}'
        ))
