"""
Prisons principales de la RDC (réseau national).

Coordonnées : sources publiques (Wikipedia, OSM, chef-lieu de ville
lorsque l'emprise exacte n'est pas publiée). Valeurs indicatives.
"""

from datetime import date

PRISON = 'PRISON'
CAMP = 'CENTRE_DE_DETENTION'


def _p(code, nom, ville, province, lat, lng, adresse, capacite, ouvert,
       type_centre=PRISON):
    return {
        'code': code,
        'nom': nom,
        'ville': ville,
        'province': province,
        'latitude': lat,
        'longitude': lng,
        'adresse': adresse,
        'capacite_max': capacite,
        'date_ouverture': ouvert,
        'type_centre': type_centre,
        'statut': True,
    }


# Principal network of central / provincial prisons (not every territorial lock-up).
PRISONS_RDC = [
    _p('C001', 'PRISON CENTRALE DE MAKALA', 'Kinshasa', 'Kinshasa',
       -4.3625000, 15.2858333,
       'Communes de Makala et Selembao, Kinshasa',
       1500, date(1957, 1, 1)),
    _p('PMN', 'PRISON MILITAIRE DE NDOLO', 'Kinshasa', 'Kinshasa',
       -4.3263889, 15.3275000,
       'Avenue Kabasele Tshiamala Joseph, commune de Barumbu, Kinshasa',
       1500, date(1960, 6, 30)),
    _p('PLZU', 'CAMP DE DETENTION DE LUZUMU', 'Kasangulu', 'Kongo-Central',
       -4.5830000, 15.1650000,
       'Kasangulu, Kongo-Central',
       400, date(2019, 1, 1), CAMP),
    _p('PMAT', 'PRISON CENTRALE DE MATADI', 'Matadi', 'Kongo-Central',
       -5.8270000, 13.4630000, 'Matadi, Kongo-Central', 400, date(1960, 6, 30)),
    _p('PBOM', 'PRISON CENTRALE DE BOMA', 'Boma', 'Kongo-Central',
       -5.8510000, 13.0540000, 'Boma, Kongo-Central', 250, date(1960, 6, 30)),
    _p('PKIK', 'PRISON CENTRALE DE KIKWIT', 'Kikwit', 'Kwilu',
       -5.0410000, 18.8160000, 'Kikwit, Kwilu', 350, date(1960, 6, 30)),
    _p('PBAN', 'PRISON CENTRALE DE BANDUNDU', 'Bandundu', 'Kwilu',
       -3.3170000, 17.3810000, 'Bandundu, Kwilu', 300, date(1960, 6, 30)),
    _p('PKGE', 'PRISON CENTRALE DE KENGE', 'Kenge', 'Kwango',
       -4.8430000, 16.8990000, 'Kenge, Kwango', 250, date(1960, 6, 30)),
    _p('PMBD', 'PRISON CENTRALE DE MBANDAKA', 'Mbandaka', 'Équateur',
       0.0490000, 18.2600000, 'Mbandaka, Équateur', 400, date(1960, 6, 30)),
    _p('PBOE', 'PRISON CENTRALE DE BOENDE', 'Boende', 'Tshuapa',
       -0.2810000, 20.8760000, 'Boende, Tshuapa', 200, date(1960, 6, 30)),
    _p('PANG', 'PRISON D\'ANGENGA', 'Bumba', 'Mongala',
       2.1820000, 22.4700000, 'Angenga, territoire de Bumba, Mongala', 500, date(1960, 6, 30)),
    _p('PLIS', 'PRISON CENTRALE DE LISALA', 'Lisala', 'Mongala',
       2.1510000, 21.5170000, 'Lisala, Mongala', 250, date(1960, 6, 30)),
    _p('PGBD', 'PRISON CENTRALE DE GBADOLITE', 'Gbadolite', 'Nord-Ubangi',
       4.2830000, 21.0170000, 'Gbadolite, Nord-Ubangi', 250, date(1960, 6, 30)),
    _p('PGEM', 'PRISON CENTRALE DE GEMENA', 'Gemena', 'Sud-Ubangi',
       3.2570000, 19.7720000, 'Gemena, Sud-Ubangi', 250, date(1960, 6, 30)),
    _p('PKIS', 'PRISON CENTRALE DE KISANGANI', 'Kisangani', 'Tshopo',
       0.5160000, 25.2060000, 'Kisangani, Tshopo', 600, date(1960, 6, 30)),
    _p('POSI', 'PRISON D\'OSIO', 'Kisangani', 'Tshopo',
       0.5800000, 25.1500000, 'Osio, périphérie de Kisangani, Tshopo', 400, date(1960, 6, 30)),
    _p('PISI', 'PRISON CENTRALE D\'ISIRO', 'Isiro', 'Haut-Uele',
       2.7730000, 27.6160000, 'Isiro, Haut-Uele', 250, date(1960, 6, 30)),
    _p('PBTA', 'PRISON CENTRALE DE BUTA', 'Buta', 'Bas-Uele',
       2.8000000, 24.7300000, 'Buta, Bas-Uele', 200, date(1960, 6, 30)),
    _p('PKIN', 'PRISON CENTRALE DE KINDU', 'Kindu', 'Maniema',
       -2.9500000, 25.9220000, 'Kindu, Maniema', 350, date(1960, 6, 30)),
    _p('PMUN', 'PRISON CENTRALE DE MUNZENZE', 'Goma', 'Nord-Kivu',
       -1.6694444, 29.2322222, 'Goma, Nord-Kivu', 700, date(1953, 1, 1)),
    _p('PBEN', 'PRISON URBAINE DE BENI', 'Beni', 'Nord-Kivu',
       0.4910000, 29.4730000, 'Beni, Nord-Kivu', 300, date(1960, 6, 30)),
    _p('PBUT', 'PRISON URBAINE DE BUTEMBO', 'Butembo', 'Nord-Kivu',
       0.1280000, 29.2910000, 'Butembo, Nord-Kivu', 300, date(1960, 6, 30)),
    _p('PBUK', 'PRISON CENTRALE DE BUKAVU', 'Bukavu', 'Sud-Kivu',
       -2.5080000, 28.8610000, 'Bukavu, Sud-Kivu', 600, date(1960, 6, 30)),
    _p('PUVI', 'PRISON URBAINE D\'UVIRA', 'Uvira', 'Sud-Kivu',
       -3.3950000, 29.1380000, 'Uvira, Sud-Kivu', 250, date(1960, 6, 30)),
    _p('PBUN', 'PRISON CENTRALE DE BUNIA', 'Bunia', 'Ituri',
       1.5600000, 30.2520000, 'Bunia, Ituri', 400, date(1960, 6, 30)),
    _p('PKAL', 'PRISON CENTRALE DE KALEMIE', 'Kalemie', 'Tanganyika',
       -5.9350000, 29.1950000, 'Kalemie, Tanganyika', 350, date(1960, 6, 30)),
    _p('PKAS', 'PRISON DE KASAPA', 'Lubumbashi', 'Haut-Katanga',
       -11.6400000, 27.4790000, 'Quartier Kasapa, Lubumbashi, Haut-Katanga', 900, date(1960, 6, 30)),
    _p('PBUL', 'PRISON DE BULUWO', 'Likasi', 'Haut-Katanga',
       -10.9830000, 26.7330000, 'Likasi, Haut-Katanga', 400, date(1960, 6, 30)),
    _p('PKOL', 'PRISON CENTRALE DE KOLWEZI', 'Kolwezi', 'Lualaba',
       -10.7160000, 25.4670000, 'Kolwezi, Lualaba', 350, date(1960, 6, 30)),
    _p('PKAM', 'PRISON CENTRALE DE KAMINA', 'Kamina', 'Haut-Lomami',
       -8.7390000, 24.9980000, 'Kamina, Haut-Lomami', 250, date(1960, 6, 30)),
    _p('PKAN', 'PRISON CENTRALE DE KANANGA', 'Kananga', 'Kasaï-Central',
       -5.8960000, 22.4170000, 'Kananga, Kasaï-Central', 500, date(1960, 6, 30)),
    _p('PMBJ', 'PRISON CENTRALE DE MBUJI-MAYI', 'Mbuji-Mayi', 'Kasaï-Oriental',
       -6.1360000, 23.5900000, 'Mbuji-Mayi, Kasaï-Oriental', 500, date(1960, 6, 30)),
    _p('PTSD', 'PRISON CENTRALE DE TSHIKAPA', 'Tshikapa', 'Kasaï',
       -6.4160000, 20.8000000, 'Tshikapa, Kasaï', 300, date(1960, 6, 30)),
    _p('PMWD', 'PRISON CENTRALE DE MWENE-DITU', 'Mwene-Ditu', 'Lomami',
       -7.0010000, 23.4530000, 'Mwene-Ditu, Lomami', 250, date(1960, 6, 30)),
    _p('PLOD', 'PRISON CENTRALE DE LODJA', 'Lodja', 'Sankuru',
       -3.5210000, 23.6000000, 'Lodja, Sankuru', 200, date(1960, 6, 30)),
]
