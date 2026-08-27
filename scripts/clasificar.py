#!/usr/bin/env python3
"""
Clasifica un tema por origen de fabricacion.

Regla de negocio (Marketing, ago-2026): en las newsletters se prioriza el producto
de UN SOLO USO DE PAPEL Y CARTON, porque es de fabricacion propia (Ordis). El resto
del catalogo es distribucion y solo entra si el producto es atractivo, novedoso o de
una calidad que merezca destacarse.

Tres valores:
  propia         - papel y carton de fabricacion propia -> prioridad alta
  distribucion   - no lo fabricamos -> solo si es destacable
  por-confirmar  - la frontera no esta clara y la tiene que decidir Marketing
"""
import unicodedata, re

def sinacentos(s):
    s = unicodedata.normalize('NFD', str(s).lower())
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn')

# ── Fabricacion propia: papeleria de mesa, bolsas de papel y envoltorios ─────
PROPIA = [
    # Servilletas y calidades de fabricacion propia
    'servilleta','canguro','kangaroo','just in time','mini servis','double point',
    'airlaid','like linen','like-linen','spunbond','spundbond','dry cotton',
    # Manteleria
    'mantel','mantelin','camino de mesa','tete','tu y yo','conjuntos decorados',
    # Disenyos y colecciones de manteleria / papeleria
    'ipanema','jazz','keiko','safari','parole','times','fitipaldi','tundra','madras',
    'vertex','arrow','grafitti','graffiti','eden','maui','modernismo','rhombus',
    'argyle','chevron','mist','dune','slim','ciudades','linea reciclada',
    # Bolsas de papel
    'bolsa sos','bolsas sos','bolsa de papel','bolsas de papel','bolsas kraft','bolsa kraft',
    'bolsas planas','bolsas boutique','bolsas con asas','bolsas sin asas','bolsas base ancha',
    'bolsas para pan','bolsas para croissant','bolsas para patatas','bolsas abiertas',
    'bolsas para regalos','bolsitas regalo','bolsas cotillon','bolsas de cotillon',
    'bolsas take away','bolsas aluminio parole','bolsas cubiertos','bolsas just in time',
    'papelinas','papelina','papel y bolsitas',
    # Envoltorios y papel tecnico
    'papel antigrasa','antigrasas','papel encerado','cera vegetal','just paper','leaf',
    'envoltorio','papel de horno','papel para envolver','papel de regalo',
    # Blondas, posavasos, cucuruchos
    'blonda','erik','posavaso','cucurucho',
    # Papeleria de pasteleria
    'capsula','moldes de papel','discos','bandejas carton','bandeja carton',
]

# ── Distribucion: lo que no sale de la fabrica ──────────────────────────────
DISTRIBUCION = [
    # Mesa durable
    'vajilla','melamina','porcelana','stoneware','akala','asamiware','enamelware',
    'artinox','crockery','loza','cuberteria','cubiertos inox','cubierto inox','inox',
    'oslo','essenza','dakota','olivia','siena','atlanta','spiga','marlene','provenza',
    'lyon','sevilla','coral',
    # Cristal y vasos reutilizables
    'waki','cristaleria','vasos cristal','copa','vasos irrompibles','vasos reutilizables',
    'reuse it','policarbonato',
    # Materiales naturales importados
    'madera','bambu','wood','areca','hoja de palma','tabla de bambu','tablas de madera',
    # Materiales alternativos importados
    'bionic','cana de azucar','bagazo','wasara',
    # Amenities
    'amenitie','amenities','champu','acogida','percha','reposamaletas','spa',
    'allure','aloe vera','azur','therapy','touch of charm',
    # Limpieza e higiene
    'bayeta','papelera','cubos pedal','guante','delantal','gorro','jabon','microkleen',
    'perfokleen','flushable','roll it','bolsas de basura','secamanos','papel higienico',
    # Utensilios y maquinaria
    'cuchillo','cubeta','carro','bascula','termometro','maquinaria','termosellar',
    'termosellable','mesas de trabajo','rack','tabla de corte','bateria',
    # Bar, buffet y mobiliario
    'mobiliario','silla','mesa plegable','taburete','trona','lampara','vela','set lounge',
    'supratek','supra-tek','chafing','dispensador','cubitera','champanera','jarra','termo',
    'display','presentador','cesta','servilletero','ramequin','botellero','estanteria',
    'mini recipiente','chicago','american style','sillas de madera','sillas poliester',
    # Rotulacion
    'portamenu','pizarra','bloc de comanda','catenaria','pulsera','papel termico',
    # Otros
    'aluminio parole','film','toallita','pajita','paletina','agitador','encuesta',
]

# ── Frontera por confirmar con Marketing ────────────────────────────────────
POR_CONFIRMAR = [
    'vaso','vasos','tarrina','envase','envases','recipiente','recipientes','caja','cajas',
    'thepack','barquilla','barquita','cajetilla','bandeja','bandejas','concha','conchas',
    'cubo','cubos','ensaladera','bol','boles','aluminio','estuche','sobres adhesivos',
    'aros de horneado','portavasos','pala','palas','separadores','maletas',
]

INSTITUCIONAL = ['catalogo','cataleg','tarifa','felicitacion','web print','historia portadas',
                 'nuestras colecciones','normativa','blog','video']

def fabricacion(nombre, familia=None):
    n = sinacentos(nombre)
    if any(k in n for k in INSTITUCIONAL):
        return 'institucional'
    # El match mas especifico gana: se compara por longitud de la clave encontrada
    mejor, valor = 0, None
    for k in PROPIA:
        if k in n and len(k) > mejor:
            mejor, valor = len(k), 'propia'
    for k in DISTRIBUCION:
        if k in n and len(k) > mejor:
            mejor, valor = len(k), 'distribucion'
    if valor:
        return valor
    for k in POR_CONFIRMAR:
        if re.search(rf'\b{re.escape(k)}', n):
            return 'por-confirmar'
    return 'por-confirmar'
