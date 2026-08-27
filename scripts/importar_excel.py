#!/usr/bin/env python3
"""
Importa el Planning_NL_*.xlsx historico a los ficheros de datos del planificador.

Genera:
  data/historico.json  - un registro por envio realizado o planificado, con fecha ISO
  data/temas.json      - banco de temas deduplicado, clasificado y con estadisticas de uso

Uso:  python3 scripts/importar_excel.py <fichero.xlsx> [--anyo-inicial 2024]
"""
import openpyxl, re, json, sys, unicodedata, argparse
from datetime import date
from collections import defaultdict

MESES = {'enero':1,'febrero':2,'marzo':3,'abril':4,'mayo':5,'junio':6,'julio':7,'agosto':8,
         'septiembre':9,'setiembre':9,'octubre':10,'noviembre':11,'diciembre':12,
         'ene':1,'feb':2,'mar':3,'abr':4,'may':5,'jun':6,'jul':7,'ago':8,'sep':9,'oct':10,
         'nov':11,'dic':12}
# Incluye variantes reales encontradas en el Excel: "Juves", "Miercoles", abreviaturas
DIAS = {'lunes':0,'martes':1,'miercoles':2,'jueves':3,'viernes':4,'sabado':5,'domingo':6,
        'juves':3,'lun':0,'mar':1,'mie':2,'jue':3,'vie':4}

def sinacentos(s):
    s = unicodedata.normalize('NFD', str(s).lower())
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn')

def slug(s):
    s = re.sub(r'[^a-z0-9]+', '-', sinacentos(s)).strip('-')
    return s[:60]

def parse_fecha(txt):
    """'Martes 18 junio' / 'Mar 6 oct' / 'jueves 10 de julio' -> (dow, dia, mes)"""
    t = re.sub(r'\s+', ' ', sinacentos(txt)).strip().replace(' de ', ' ')
    m = re.match(r'^([a-z]+)\.?\s+(\d{1,2})\s+([a-z]+)', t)
    if not m:
        return None
    dow, dia, mes = DIAS.get(m.group(1)), int(m.group(2)), MESES.get(m.group(3))
    return None if mes is None else (dow, dia, mes)

# --- Clasificacion por familia de catalogo (reglas sobre el texto del tema) ---
FAMILIAS = [
    ('institucional', ['catalogo','cataleg','tarifa','felicitacion','encuesta','web print',
                       'historia portadas','nuestras colecciones','normativa','blog']),
    ('cotillon',      ['navidad','cotillon','kerstmis','christmas','fin de ano','san valentin',
                       'lotes','bolsas para regalos','papel y bolsitas regalo','botellas navidad',
                       'bolsitas regalo','regalo']),
    ('take-away',     ['take away','take-away','delivery','hamburguesa','burger','hot dog','kebab',
                       'wrap','crepe','sushi','bagel','poke','taco','street food','cubos para pollo',
                       'cubos pollo','ensaladera','barquilla','barquita','maletas de transporte',
                       'bandejas trasporte','bandejas transporte','grab','fritos','palomitas',
                       'cucurucho','papelina','pizza','panini','sandwich','bocadillo','grill & go',
                       'roast and go','conchas','portavasos']),
    ('un-solo-uso',   ['servilleta','mantel','mantelin','tete','camino de mesa','bolsa','vaso',
                       'pajita','paletina','envase','recipiente','tarrina','blonda','posavaso',
                       'bandeja','papel antigrasa','antigrasas','pasteleria','aluminio','film',
                       'cubierto','plato','bol ','boles','cucharilla','pincho','toallita','papelina',
                       'contenedores lacados','sobres adhesivos','aros de horneado','molde',
                       'like linen','like-linen','airlaid','spunbond','spundbond','double point',
                       'just in time','canguro','kangaroo','dry cotton','thepack','bionic','wood',
                       'paper cutlery','parole','times','pfas','feel green','areca','just paper',
                       'fitipaldi','leaf','papel encerado','cera vegetal','papel con aluminio',
                       'compostable','papel de horno','estuches para cubiertos']),
    ('bar-buffet',    ['bufet','buffet','presentacion bufet','presentador','display','chafing',
                       'dispensador','cubitera','champanera','jarra','termo','barman','coctel',
                       'exprimidor','ramequin','mini recipiente','aperitivo','bambu','tabla de madera',
                       'tablas de madera','botellero','estanteria botellas','american style',
                       'artinox','waki','cristaleria','vasos cristal','crockery','loza']),
    ('mesa-accesorios',['cuberteria','cubiertos inox','porcelana','melamina','policarbonato',
                       'stoneware','akala','asamiware','enamelware','vajilla','copa','vasos reutilizables',
                       'reuse it','vasos irrompibles','cesta','servilletero','lampara','vela',
                       'mobiliario','mesa plegable','silla','taburete','trona','set lounge',
                       'oslo','essenza','dakota','olivia','siena','atlanta','coral','lyon','sevilla',
                       'spiga','marlene','provenza','vintage','supratek','supra-tek','chicago']),
    ('utensilios-cocina',['bateria','cuchillo','cubeta','gn','contenedor','isotermic','bolsa termica',
                       'rack','carro','tabla de corte','bascula','termometro','maquinaria','termosellar',
                       'termosellable','mesas de trabajo','pala']),
    ('limpieza-higiene',['celulosa','papel higienico','secamanos','bobina','matatrapos','bayeta',
                       'pano','bolsas de basura','papelera','contenedor de reciclaje','guante',
                       'vestuario','delantal','gorro','jabon','carro de limpieza','microkleen',
                       'perfokleen','flushable','roll it','cubos pedal']),
    ('habitaciones',  ['amenitie','amenities','gel','champu','acogida','dental','afeitado','costurero',
                       'zapatilla','toalla','percha','reposamaletas','spa','allure','aloe vera',
                       'azur','therapy','touch of charm']),
    ('rotulacion',    ['portamenu','pizarra','bloc de comanda','senalizacion','etiqueta','catenaria',
                       'porta cuenta','pulsera','papel termico','tpv']),
]

MARCAS = ['THEPACK','BIONIC','FEEL GREEN','PFAS FREE','PAROLE','TIMES','WOOD','DRY COTTON',
          'Like-Linen','Airlaid','Spunbond','Double Point','Just in Time','Kangaroo','ERIK',
          'Ipanema','Jazz','Keiko','Safari','Akala','Artinox','Enamelware','Asamiware','Crockery',
          'American Style','Waki Glass','Wasara','Fitipaldi','Leaf','Areca','Vintage','Kintsu',
          'Supratek','Arrow','Paper Cutlery','Just Paper','Reuse it','Grill & Go','Roast and Go',
          'Ovensafe','CUBE','Set Lounge','Flurry','Grafitti','Microkleen','Perfokleen',
          'Atlanta','Coral','Dakota','Essenza','Linea','Lyon','Marlene','Olivia','Oslo',
          'Provenza','Sevilla','Siena','Spiga','Allure','Aloe Vera','Azur','Therapy',
          'Touch of Charm','Chicago Lava Stone']

def familia_de(tema):
    t = sinacentos(tema)
    for fam, claves in FAMILIAS:
        if any(k in t for k in claves):
            return fam
    return 'sin-clasificar'

def marcas_de(tema):
    t = sinacentos(tema)
    return [m for m in MARCAS if sinacentos(m) in t]

def paginas_de(texto):
    """Extrae referencias a paginas de catalogo: 'pag 24', '(157, 158)', '32-41', '798'"""
    t = texto
    pags = set()
    for m in re.finditer(r'p[ag]{1,3}\.?\s*([\d\s,\-y]+)', t, re.I):
        for n in re.findall(r'\d{1,3}', m.group(1)):
            pags.add(int(n))
    for m in re.finditer(r'\((\d{1,3}(?:\s*[-,]\s*\d{1,3})*)\)', t):
        for n in re.findall(r'\d{1,3}', m.group(1)):
            pags.add(int(n))
    return sorted(pags)

# Notas internas: fragmentos en catalan o anotaciones de proceso dentro del tema
MARCAS_PROCESO = ['(feta)','feta)','repetida','repetir','rep )','rep)','(rep','no stock',
                  'resend','dos parts','nomes els de dalt','hi ha','esmenta','per exemple',
                  'una mica de tot','les diferents linies','per tornar','aquests de cara',
                  'nous colors','nous dissenys','no hay materia prima','emili','laia','aurelie']

def limpia_tema(tema):
    """Separa el tema publicable de la nota interna de proceso."""
    urls = re.findall(r'https?://\S+', tema)
    t = re.sub(r'https?://\S+', '', tema).strip()
    notas = [m for m in MARCAS_PROCESO if m in sinacentos(t)]
    limpio = re.sub(r'\s{2,}', ' ', t).strip(' .·-+')
    return limpio, notas, urls

def tipo_de(tema, notas):
    t = sinacentos(tema)
    if any(k in t for k in ['catalogo','cataleg']):        return 'lanzamiento-catalogo'
    if 'tarifa' in t:                                       return 'tarifa'
    if 'felicitacion' in t:                                 return 'institucional'
    if any(k in t for k in ['encuesta','web print','historia portadas']): return 'institucional'
    if 'blog' in t:                                          return 'contenido-blog'
    if 'video' in t:                                         return 'video'
    if 'new' in t.split() or t.startswith('nuev') or 'nuevas' in t or 'nuevos' in t: return 'novedad'
    if any(k in notas for k in ['repetida','repetir','(rep','rep)','rep )']): return 'repeticion'
    return 'producto'

TEMPORADAS = {12:'invierno',1:'invierno',2:'invierno',3:'primavera',4:'primavera',5:'primavera',
              6:'verano',7:'verano',8:'verano',9:'otono',10:'otono',11:'otono'}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('xlsx')
    ap.add_argument('--anyo-inicial', type=int, default=2024)
    args = ap.parse_args()

    wb = openpyxl.load_workbook(args.xlsx, data_only=True)
    envios, ideas, avisos = [], [], []

    for ws in wb.worksheets:
        anyo, mes_previo = args.anyo_inicial, None
        for i, r in enumerate(ws.iter_rows(values_only=True), start=1):
            cells = ['' if c is None else str(c).strip() for c in r] + [''] * 4
            fecha_raw, c1, c2, c3 = cells[0], cells[1], cells[2], cells[3]
            if not c1:
                continue
            if 'PLANNING' in c1.upper() and not fecha_raw:
                continue

            # El resto de columnas son alternativas o estado, segun la hoja
            resto = ' '.join(x for x in (c2, c3) if x)
            tema, notas, urls = limpia_tema(c1)
            _, notas2, urls2 = limpia_tema(resto)
            urls += urls2
            notas = sorted(set(notas + notas2))
            alternativa = re.sub(r'https?://\S+', '', resto).strip() if resto else ''

            reg = {
                'tema': tema,
                'familia': familia_de(c1 + ' ' + resto),
                'marcas': marcas_de(c1 + ' ' + resto),
                'paginas_catalogo': paginas_de(c1 + ' ' + resto),
                'urls': sorted(set(urls)),
                'notas_internas': notas,
                'alternativa': alternativa,
                'origen': f'{ws.title}!{i}',
            }
            reg['tipo'] = tipo_de(c1, notas)

            p = parse_fecha(fecha_raw) if fecha_raw else None
            if p:
                dow, dia, mes = p
                if mes_previo is not None and mes < mes_previo:
                    anyo += 1
                mes_previo = mes
                try:
                    f = date(anyo, mes, dia)
                except ValueError:
                    avisos.append(f'{ws.title}!{i}: fecha invalida "{fecha_raw}"')
                    ideas.append(reg); continue
                if dow is not None and f.weekday() != dow:
                    avisos.append(f'{ws.title}!{i}: "{fecha_raw}" no cae en el dia declarado ({f})')
                reg.update(fecha=f.isoformat(), hora='15:00',
                           dia_semana=['lunes','martes','miercoles','jueves','viernes','sabado','domingo'][f.weekday()],
                           temporada=TEMPORADAS[mes], mes=mes, anyo=f.year)
                envios.append(reg)
            else:
                ideas.append(reg)

    envios.sort(key=lambda e: e['fecha'])

    # --- Banco de temas: deduplica por slug del tema limpio ---
    banco = {}
    for reg in envios + ideas:
        if not reg['tema']:
            continue
        # normaliza para agrupar repeticiones ("Repetida X", "REPETIR: X", "X (rep)")
        base = re.sub(r'^(repetida|repetir|resend)\s*:?\s*', '', sinacentos(reg['tema'])).strip()
        base = re.sub(r'\(rep[^)]*\)', '', base).strip()
        k = slug(base)
        if not k:
            continue
        t = banco.setdefault(k, {
            'id': k, 'nombre': reg['tema'], 'familia': reg['familia'], 'marcas': [],
            'paginas_catalogo': [], 'url_es': None, 'tipo': reg['tipo'],
            'envios': [], 'meses_usados': [], 'notas_internas': [],
        })
        t['marcas'] = sorted(set(t['marcas']) | set(reg['marcas']))
        t['paginas_catalogo'] = sorted(set(t['paginas_catalogo']) | set(reg['paginas_catalogo']))
        t['notas_internas'] = sorted(set(t['notas_internas']) | set(reg['notas_internas']))
        if reg['urls'] and not t['url_es']:
            t['url_es'] = reg['urls'][0]
        if reg.get('fecha'):
            t['envios'].append(reg['fecha'])
            t['meses_usados'].append(reg['mes'])
        if t['familia'] == 'sin-clasificar' and reg['familia'] != 'sin-clasificar':
            t['familia'] = reg['familia']

    for t in banco.values():
        t['envios'].sort()
        t['veces_enviado'] = len(t['envios'])
        t['ultimo_envio'] = t['envios'][-1] if t['envios'] else None
        ms = t['meses_usados']
        t['temporadas'] = sorted({TEMPORADAS[m] for m in ms}) if ms else []
        del t['meses_usados']

    temas = sorted(banco.values(), key=lambda t: (-t['veces_enviado'], t['id']))

    json.dump({'generado_desde': args.xlsx, 'envios': envios},
              open('data/historico.json', 'w'), ensure_ascii=False, indent=1)
    json.dump({'temas': temas}, open('data/temas.json', 'w'), ensure_ascii=False, indent=1)

    print(f'envios con fecha .......... {len(envios)}  ({envios[0]["fecha"]} -> {envios[-1]["fecha"]})')
    print(f'ideas sin fecha ........... {len(ideas)}')
    print(f'temas unicos en el banco .. {len(temas)}')
    print(f'temas con URL ............. {sum(1 for t in temas if t["url_es"])}')
    print(f'sin clasificar ............ {sum(1 for t in temas if t["familia"]=="sin-clasificar")}')
    print(f'avisos .................... {len(avisos)}')
    for a in avisos[:10]:
        print('   !', a)
    from collections import Counter
    print('\npor familia:')
    for f, c in Counter(t['familia'] for t in temas).most_common():
        print(f'   {c:4d}  {f}')
    print('\nmas repetidos:')
    for t in temas[:12]:
        print(f'   {t["veces_enviado"]}x  {t["nombre"][:62]}')

if __name__ == '__main__':
    main()
