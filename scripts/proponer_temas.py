#!/usr/bin/env python3
"""
Propone los temas de newsletter de un periodo: fecha, tema y URL.

La fuente de ideas es el CALENDARIO COMERCIAL (scripts/calendario_comercial.py), no el
historico. El historico se usa para dos cosas y solo dos:
  1. sacar la URL de categoria, de entre los enlaces que ya se han usado de verdad
  2. avisar si un tema muy parecido salio hace poco

No propone envios extraordinarios: nada de catalogos, tarifas, felicitaciones ni
encuestas. Solo temas de producto que pueden generar venta en esa epoca del año.

Uso:  python3 scripts/proponer_temas.py --desde 2027-01-01 --hasta 2027-12-31
      python3 scripts/proponer_temas.py --desde 2027-01-01 --hasta 2027-03-31 --csv
"""
import json, argparse, re, unicodedata, sys, os
from datetime import date, timedelta
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calendario_comercial import como_diccionarios

DIAS_ENVIO = (1, 3)          # martes y jueves
HORA = '15:00'
CUOTA_PROPIA = 0.75          # los temas de papel y carton propio deben dominar
MESES_DESCANSO = 10          # meses antes de volver a proponer la misma ocasion
NOMBRE_DIA = ['lunes','martes','miercoles','jueves','viernes','sabado','domingo']
MES_CORTO = ['','ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic']

# Segmentos de ruta en otro idioma que aparecen dentro de /es/ por los rewrites de Magento.
# Se penalizan al elegir URL: funcionan, pero son inconsistentes.
SEGMENTOS_RAROS = ('kerstmis', 'tafel-en-accessoires', 'bar-en-buffet', 'voorgerechten',
                   'disposable-products', 'wegwerpartikelen')

# El sitio cambio de estructura de URL con la migracion. En el historico conviven dos
# generaciones: /es/un-solo-uso/servilletas.html (2022) y
# /es/un-solo-uso/servilletas-de-papel/... (2025-2026). Las antiguas pueden estar muertas,
# asi que solo se proponen si no hay ninguna reciente, y entonces se marcan para revisar.
FECHA_MIGRACION = '2025-10-01'

# Parametros de filtro: son vistas filtradas de la categoria, no la categoria.
PARAMS_FILTRO = ('gpou_', 'product_list_dir', 'q=')

def sinacentos(s):
    s = unicodedata.normalize('NFD', str(s).lower())
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn')

def huecos(desde, hasta):
    out, d = [], desde
    while d <= hasta:
        if d.weekday() in DIAS_ENVIO:
            out.append(d)
        d += timedelta(days=1)
    return out

def indice_urls(envios):
    """Todas las URL usadas de verdad, con la fecha de la ultima vez."""
    urls = {}
    for e in envios:
        for u in e.get('enlaces', []):
            if u not in urls or e['fecha'] > urls[u]:
                urls[u] = e['fecha']
    return urls

def elige_url(claves, urls):
    """Busca entre las URL reales la mejor para estas claves. Nunca inventa una.

    Devuelve (url, calidad) donde calidad es:
      'exacta'   - la clave es la categoria final de la ruta y el enlace es post-migracion
      'proxima'  - coincide, pero es una subcategoria o una vista filtrada
      'antigua'  - solo existe con la estructura de URL anterior a la migracion: revisar
    """
    def limpia(u):
        return u.split('?')[0] if any(p in u for p in PARAMS_FILTRO) else u

    for clave in claves:                                  # las claves van por prioridad
        cands = [u for u in urls if clave in u]
        if not cands:
            continue
        recientes = [u for u in cands if urls[u] >= FECHA_MIGRACION]
        pool, antigua = (recientes, False) if recientes else (cands, True)

        def coste(u):
            ruta = u.split('?')[0]
            final = ruta.rsplit('/', 1)[-1].removesuffix('.html')
            return (
                final != clave,                           # la clave ES la categoria final
                any(s in u for s in SEGMENTOS_RAROS),     # penaliza rutas mezcladas
                any(p in u for p in PARAMS_FILTRO),       # penaliza vistas filtradas
                ruta.count('/'),                          # prefiere categoria a subcategoria
                len(u),
            )
        mejor = sorted(pool, key=coste)[0]
        ruta = mejor.split('?')[0]
        exacta = ruta.rsplit('/', 1)[-1].removesuffix('.html') == clave
        calidad = 'antigua' if antigua else ('exacta' if exacta else 'proxima')
        return limpia(mejor), calidad
    return None, None

def parecido(a, b):
    """Solapamiento de palabras significativas entre dos temas."""
    STOP = set('de la el los las para con en un una del al y o e su sus que se lo por'
               ' mas mas antes ahora todo toda todos todas'.split())
    pa = {w for w in re.findall(r'[a-z]{4,}', sinacentos(a)) if w not in STOP}
    pb = {w for w in re.findall(r'[a-z]{4,}', sinacentos(b)) if w not in STOP}
    if not pa or not pb:
        return 0.0
    return len(pa & pb) / min(len(pa), len(pb))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--desde', required=True)
    ap.add_argument('--hasta', required=True)
    ap.add_argument('--salida')
    ap.add_argument('--csv', action='store_true', help='saca tambien un CSV de tres columnas')
    args = ap.parse_args()
    desde, hasta = date.fromisoformat(args.desde), date.fromisoformat(args.hasta)

    ocasiones = como_diccionarios()
    hist = [e for e in json.load(open('data/historico.json'))['envios']
            if not e.get('revision_previa')]
    urls = indice_urls(hist)

    # Envios recientes, para avisar de solapamiento
    limite = (desde - timedelta(days=int(MESES_DESCANSO * 30.4))).isoformat()
    recientes = [e for e in hist if e['fecha'] >= limite]

    por_mes = defaultdict(list)
    for i, o in enumerate(ocasiones):
        for m in o['meses']:
            por_mes[m].append(i)

    fechas = huecos(desde, hasta)
    usados, plan = set(), []

    def candidatos(mes):
        """Ocasiones del mes, sin usar, propias primero."""
        libres = [i for i in por_mes.get(mes, []) if i not in usados]
        return sorted(libres, key=lambda i: (not ocasiones[i]['propia'], i))

    def cuota_actual():
        if not plan:
            return 1.0
        return sum(1 for p in plan if p['fabricacion_propia']) / len(plan)

    for f in fechas:
        cands = candidatos(f.month)
        # Meses vecinos si el mes se queda corto de ideas
        if not cands:
            for vecino in (f.month - 1, f.month + 1):
                vecino = 12 if vecino == 0 else 1 if vecino == 13 else vecino
                cands = candidatos(vecino)
                if cands:
                    break
        if not cands:
            plan.append({'fecha': f.isoformat(), 'hora': HORA, 'dia': NOMBRE_DIA[f.weekday()],
                         'tema': '(sin propuesta — amplíe el calendario comercial)',
                         'url': None, 'url_calidad': None, 'razon': None, 'cliente': None,
                         'fabricacion_propia': False, 'aviso': 'sin candidatos para este mes'})
            continue

        # Si la cuota de fabricacion propia va baja, se fuerza una propia
        if cuota_actual() < CUOTA_PROPIA:
            propias = [i for i in cands if ocasiones[i]['propia']]
            cands = propias or cands

        idx = cands[0]
        usados.add(idx)
        o = ocasiones[idx]

        aviso = None
        for e in recientes:
            if parecido(o['tema'], e['asunto']) >= 0.6:
                aviso = f'parecido a «{e["asunto"][:60]}» del {e["fecha"]}'
                break

        url, calidad = elige_url(o['claves'], urls)
        plan.append({
            'fecha': f.isoformat(), 'hora': HORA, 'dia': NOMBRE_DIA[f.weekday()],
            'tema': o['tema'],
            'url': url, 'url_calidad': calidad,
            'razon': o['razon'], 'cliente': o['cliente'],
            'fabricacion_propia': o['propia'], 'aviso': aviso,
        })

    salida = args.salida or f'data/temas-{desde.year}.json'
    json.dump({'periodo': [args.desde, args.hasta], 'generado_por': 'proponer_temas.py',
               'envios': plan}, open(salida, 'w'), ensure_ascii=False, indent=1)

    ancho = max(len(p['tema']) for p in plan)
    print(f'{len(plan)} envíos entre {desde} y {hasta}  ->  {salida}\n')
    mes_previo = None
    for p in plan:
        a, m, d = p['fecha'].split('-')
        if m != mes_previo:
            print()
            mes_previo = m
        fecha = f'{p["dia"][:3]} {int(d):>2} {MES_CORTO[int(m)]} {a}'
        url = p['url'] or '—  (sin enlace en el histórico)'
        marca = {'proxima': '  ~', 'antigua': '  ⚠ URL anterior a la migración'}.get(
            p.get('url_calidad'), '')
        print(f'{fecha:<16} {p["tema"]:<{ancho}}  {url}{marca}')
        if p['aviso']:
            print(f'{"":<16} ⚑ {p["aviso"]}')

    print()
    cal = Counter(p.get('url_calidad') for p in plan)
    print(f'con URL del histórico ..... {sum(1 for p in plan if p["url"])}/{len(plan)}'
          f'   (exacta {cal["exacta"]} · próxima {cal["proxima"]} · antigua {cal["antigua"]})')
    print(f'sin enlace ................ {cal[None]}  <- aquí ayudaría el catálogo')
    print(f'papel y cartón propio ..... {sum(1 for p in plan if p["fabricacion_propia"])}/{len(plan)}'
          f'  ({cuota_actual()*100:.0f}%)')
    print(f'avisos de solapamiento .... {sum(1 for p in plan if p["aviso"])}')
    print(f'sin propuesta ............. {sum(1 for p in plan if p["url"] is None and not p["razon"])}')

    if args.csv:
        import csv
        ruta = salida.replace('.json', '.csv')
        with open(ruta, 'w', newline='') as fh:
            w = csv.writer(fh)
            w.writerow(['Fecha', 'Hora', 'Tema', 'URL'])
            for p in plan:
                w.writerow([p['fecha'], p['hora'], p['tema'], p['url'] or ''])
        print(f'\nCSV -> {ruta}')

if __name__ == '__main__':
    main()
