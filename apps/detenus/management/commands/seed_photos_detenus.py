import json
from datetime import date
from io import BytesIO
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import Image

from apps.detenus.models import Detenu

UA = 'Mozilla/5.0 (compatible; e-Detenu-demo/1.0)'
API = 'https://this-person-does-not-exist.com'


def download(url):
    request = Request(url, headers={'User-Agent': UA, 'Referer': API + '/'})
    with urlopen(request, timeout=30) as response:
        data = response.read()
        content_type = response.headers.get('Content-Type', 'image/jpeg')
    if not data or 'image' not in content_type:
        raise URLError('not an image')
    return data


def fetch_african_portrait(sexe, age):
    gender = 'female' if sexe == 'F' else 'male'
    age = max(21, min(55, age or 30))
    api_url = '%s/new?gender=%s&age=%s&etnic=black' % (API, gender, age)
    request = Request(api_url, headers={'User-Agent': UA, 'Referer': API + '/'})
    with urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode('utf-8'))
    src = payload.get('src') or ''
    name = payload.get('name') or ''
    if src.startswith('/'):
        img_url = API + src
    elif name:
        img_url = API + '/img/' + name
    else:
        raise URLError('no image in response')
    return download(img_url)


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


def age_detenu(detenu):
    born = detenu.date_naissance
    if not born:
        return 30
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


class Command(BaseCommand):
    help = (
        'Assigne des portraits africains IA (this-person-does-not-exist.com, personnes fictives) '
        'aux detenus.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Remplacer les photos existantes')

    def handle(self, *args, **options):
        force = options['force']
        detenus = list(Detenu.objects.order_by('matricule'))
        if not detenus:
            self.stderr.write('Aucun detenu.')
            return

        assigned = 0
        skipped = 0
        errors = 0

        for detenu in detenus:
            if detenu.photo_face and not force:
                skipped += 1
                continue

            data = None
            last_error = None
            for _attempt in range(3):
                try:
                    data = fetch_african_portrait(detenu.sexe, age_detenu(detenu))
                    break
                except Exception as exc:
                    last_error = exc
            if not data:
                errors += 1
                self.stderr.write('SKIP %s : %s' % (detenu.matricule, last_error))
                continue

            jpeg = to_passport_jpeg(data)
            detenu.photo_face.save(
                '%s_face.jpg' % detenu.matricule.lower(),
                ContentFile(jpeg),
                save=False,
            )
            detenu.photo_profil.save(
                '%s_profil.jpg' % detenu.matricule.lower(),
                ContentFile(jpeg),
                save=False,
            )
            detenu.save(update_fields=['photo_face', 'photo_profil'])
            assigned += 1
            self.stdout.write('OK %s %s' % (detenu.matricule, detenu.nom_complet))

        self.stdout.write(self.style.SUCCESS(
            'Photos africaines assignees: %s | deja presentes: %s | erreurs: %s'
            % (assigned, skipped, errors)
        ))
