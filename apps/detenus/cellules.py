from collections import Counter, OrderedDict

from .models import Cellule, Detenu, StatutDetenu, TypePopulationCellule


def choix_cellules(centre=None, sexe=None, extra=None):
    """Liste déroulante des cellules d'un centre, groupées par pavillon."""
    choices = [('', '— Choisir une cellule —')]
    if not centre:
        if extra:
            choices.append(('Autre', [(extra, extra)]))
        return choices

    qs = Cellule.objects.filter(centre=centre, actif=True).order_by('pavillon', 'code')
    if sexe == 'F':
        qs = qs.filter(type_population=TypePopulationCellule.FEMMES)
    elif sexe == 'M':
        qs = qs.filter(type_population=TypePopulationCellule.HOMMES)

    occupes = Counter(
        Detenu.objects.filter(centre=centre, statut=StatutDetenu.INCARCERE)
        .exclude(cellule='')
        .values_list('cellule', flat=True)
    )

    groupes = OrderedDict()
    codes = set()
    for cell in qs:
        codes.add(cell.code)
        n = occupes.get(cell.code, 0)
        label = '%s (%s/%s)' % (cell.code, n, cell.capacite)
        groupes.setdefault(cell.libelle_pavillon, []).append((cell.code, label))

    choices.extend(groupes.items())
    if extra and extra not in codes:
        choices.append(('Autre', [(extra, extra)]))
    return choices


def cellules_json(centre, sexe=None):
    groups = []
    for groupe, options in choix_cellules(centre, sexe)[1:]:
        if groupe == 'Autre':
            continue
        groups.append({
            'pavillon': groupe,
            'cellules': [{'code': code, 'label': label} for code, label in options],
        })
    return groups
