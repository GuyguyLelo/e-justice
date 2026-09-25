from io import BytesIO
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import Image

from apps.visites.models import Visiteur

UA = 'Mozilla/5.0 (compatible; e-Detenu-demo/1.0; +https://unsplash.com)'

# Portraits d'adultes, licence Unsplash (https://unsplash.com/license).
PHOTOS_FEMMES = [
    'https://images.unsplash.com/photo-1531123897727-8f129e1688ce?auto=format&fit=crop&w=600&h=600&q=80',
    'https://images.unsplash.com/photo-1589156280159-27698a70f29e?auto=format&fit=crop&w=600&h=600&q=80',
    'https://images.unsplash.com/photo-1488426862026-3ee34a7d66df?auto=format&fit=crop&w=600&h=600&q=80',
    'https://images.unsplash.com/photo-1524504388940-b1c1722653e1?auto=format&fit=crop&w=600&h=600&q=80',
]
PHOTOS_HOMMES = [
    'https://images.unsplash.com/photo-1531384441138-2736e62e0919?auto=format&fit=crop&w=600&h=600&q=80',
]

PRENOMS_FEMININS = {
    'celine', 'céline', 'esther', 'ange', 'marie', 'grace', 'grâce',
    'sophie', 'helene', 'hélène', 'jeanne', 'chantal', 'patricia',
    'aline', 'nathalie', 'josiane', 'odette', 'therese', 'thérèse',
    'fatou', 'amina', 'sarah', 'rachel', 'deborah', 'déborah',
}


def download(url):
    request = Request(url, headers={'User-Agent': UA, 'Accept': 'image/*'})
    with urlopen(request, timeout=20) as response:
        data = response.read()
        content_type = response.headers.get('Content-Type', 'image/jpeg')
    if not data or 'image' not in content_type:
        raise URLError('not an image')
    return data


def to_passport_jpeg(data):
    image = Image.open(BytesIO(data)).convert('RGB')
    width, height = image.size
    side = min(width, height)
    left = (width - side) // 2
    top = max(0, (height - side) // 6)
    image = image.crop((left, top, left + side, top + side))
    image = image.resize((400, 400), Image.Resampling.LANCZOS)
    buffer = BytesIO()
    image.save(buffer, format='JPEG', quality=90, subsampling=0)
    return buffer.getvalue()


def sexe_visiteur(visiteur):
    prenom = (visiteur.prenom or '').strip().lower()
    return 'F' if prenom in PRENOMS_FEMININS else 'M'


class Command(BaseCommand):
    help = (
        'Assigne des portraits africains libres (Unsplash) aux visiteurs.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Remplacer les photos existantes')

    def handle(self, *args, **options):
        force = options['force']
        visiteurs = list(Visiteur.objects.order_by('nom', 'prenom'))
        if not visiteurs:
            self.stderr.write('Aucun visiteur.')
            return

        assigned = 0
        skipped = 0
        errors = 0
        idx_f = 0
        idx_h = 0

        for visiteur in visiteurs:
            if visiteur.photo and not force:
                skipped += 1
                continue

            sexe = sexe_visiteur(visiteur)
            if sexe == 'F':
                url = PHOTOS_FEMMES[idx_f % len(PHOTOS_FEMMES)]
                idx_f += 1
            else:
                url = PHOTOS_HOMMES[idx_h % len(PHOTOS_HOMMES)]
                idx_h += 1

            try:
                jpeg = to_passport_jpeg(download(url))
            except Exception as exc:
                fallback = PHOTOS_FEMMES[0] if sexe == 'F' else PHOTOS_HOMMES[0]
                try:
                    jpeg = to_passport_jpeg(download(fallback))
                except Exception:
                    errors += 1
                    self.stderr.write('SKIP %s : %s' % (visiteur.nom_complet, exc))
                    continue

            slug = ('%s_%s' % (visiteur.nom, visiteur.prenom)).lower().replace(' ', '_')
            visiteur.photo.save('%s.jpg' % slug, ContentFile(jpeg), save=True)
            assigned += 1
            self.stdout.write('OK %s' % visiteur.nom_complet)

        self.stdout.write(self.style.SUCCESS(
            'Photos visiteurs assignees: %s | deja presentes: %s | erreurs: %s'
            % (assigned, skipped, errors)
        ))
