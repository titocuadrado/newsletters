#!/usr/bin/env python3
"""
Propone el planning de newsletters de un periodo: genera las fechas y asigna un tema
a cada hueco a partir del banco construido con el historico.

REGLA DE NEGOCIO QUE MANDA (Marketing, ago-2026)
------------------------------------------------
Se prioriza el producto de un solo uso de PAPEL Y CARTON porque es de fabricacion
propia. El resto del catalogo es distribucion y solo entra si el producto es
atractivo, novedoso o de una calidad que merezca destacarse.

Traducido a reglas:
  * al menos CUOTA_PROPIA de los envios de producto son de fabricacion propia
  * un tema de distribucion solo se propone si es "destacable": novedad, o nunca
    enviado, o marcado a mano como destacable en el banco
  * los envios institucionales (catalogo, tarifas, felicitacion) van a sus fechas
    y no cuentan para la cuota

Orden de asignacion de cada hueco:
  1. Fijo institucional  - lanzamiento de catalogo o tarifa en su fecha habitual
  2. Ancla estacional    - que se envio esa misma semana ISO en anyos anteriores
  3. Cuota de propia     - si vamos por debajo, se fuerza un tema de fabricacion propia
  4. Estreno             - tema del banco que nunca ha salido
  5. Rotacion            - el tema disponible mas antiguo

Filtros que se aplican siempre:
  * descanso: no repetir un tema enviado en los ultimos MESES_DESCANSO meses
  * ventana estacional: Navidad solo en oct-dic, granizados solo en abr-sep, etc.

Uso:  python3 scripts/proponer_plan.py --desde 2027-01-01 --hasta 2027-03-31
"""
import json, argparse, unicodedata, re, os
from datetime import date, timedelta
from collections import Counter

MESES_DESCANSO = 12
CUOTA_PROPIA   = 0.65        # minimo de envios de producto que deben ser fabricacion propia
DIAS_ENVIO     = (1, 3)      # martes y jueves
HORA           = '15:00'
NOMBRE_DIA = ['lunes','martes','miercoles','jueves','viernes','sabado','domingo']

# Festivos en los que historicamente SI se ha enviado: se avisa, no se bloquea.
FESTIVOS_AVISO = {(1,1),(1,6),(5,1),(8,15),(11,1),(12,6),(12,8),(12,25),(12,26)}

# Ventanas estacionales: meses en los que un tema tiene sentido.
VENTANAS_FAMILIA = {'cotillon': (10, 11, 12)}
VENTANAS_CLAVE = [
    (('navidad','cotillon','kerstmis','christmas','fin de ano','felicitacion','lotes',
      'regalo','botellas navidad','finger food','conjuntos decorados'), (10, 11, 12)),
    (('san valentin',),                                                  (1, 2)),
    (('castana','churro','sopa','crema','bebidas calientes','vasos cafe',
      'chocolate caliente','matatrapos'),                          (10,11,12,1,2,3)),
    (('granizado','batido','smoothie','helado','terraza','bebidas frias','flurry',
      'refrescante','zumo','gazpacho'),                            (4,5,6,7,8,9)),
    (('catalogo navidad','cataleg navidad','catalogo cotillon'),          (7, 8, 9)),
]

# Envios institucionales con fecha habitual, deducida del historico 2022-2026.
# (mes, semana_del_mes, asunto, tipo) — semana 1 = primera semana del mes, -1 = ultima
FIJOS = [
    (1,  4, 'Lanzamiento del catálogo del año',        'lanzamiento-catalogo'),
    (2,  1, 'Actualización de tarifas',                'tarifa'),
    (7,  3, 'Catálogo de Navidad — mayoristas',        'lanzamiento-catalogo'),
    (9,  3, 'Catálogo de Navidad — Horeca',            'lanzamiento-catalogo'),
    (10, 3, 'Catálogo de novedades',                   'lanzamiento-catalogo'),
    (11, 4, 'Actualización de tarifas',                'tarifa'),
    (12,-1, 'Felicitación de Navidad',                 'institucional'),
]

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

def meses_desde(iso, ref):
    f = date.fromisoformat(iso)
    return (ref.year - f.year) * 12 + (ref.month - f.month)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--desde', required=True)
    ap.add_argument('--hasta', required=True)
    ap.add_argument('--salida')
    ap.add_argument('--cuota-propia', type=float, default=CUOTA_PROPIA)
    args = ap.parse_args()
    desde, hasta = date.fromisoformat(args.desde), date.fromisoformat(args.hasta)
    cuota = args.cuota_propia

    temas  = json.load(open('data/temas.json'))['temas']
    hist   = [e for e in json.load(open('data/historico.json'))['envios']
              if not e.get('revision_previa')]

    # Indice de anclas estacionales: semana ISO -> ids de tema usados esa semana
    def id_de(nombre):
        base = re.sub(r'^(repetida|repetir|resend)\s*:?\s*', '', sinacentos(nombre)).strip()
        base = re.sub(r'\(rep[^)]*\)|\(repetida\)', '', base).strip()
        return re.sub(r'[^a-z0-9]+', '-', base).strip('-')[:60]
    por_id = {t['id']: t for t in temas}
    por_semana = {}
    for e in hist:
        s = date.fromisoformat(e['fecha']).isocalendar()[1]
        por_semana.setdefault(s, []).append(id_de(e['asunto']))

    usados = set()
    plan   = []

    def descansado(t):
        return t['ultimo_envio'] is None or meses_desde(t['ultimo_envio'], desde) >= MESES_DESCANSO

    def en_ventana(t, f):
        if f.month not in VENTANAS_FAMILIA.get(t['familia'], range(1, 13)):
            return False
        n = sinacentos(t['nombre'] + ' ' + t.get('productos', ''))
        for claves, meses in VENTANAS_CLAVE:
            if any(k in n for k in claves) and f.month not in meses:
                return False
        return True

    def destacable(t):
        """Un tema de distribucion solo entra si merece destacarse."""
        if t.get('destacable'):
            return True
        if t['veces_enviado'] == 0:
            return True
        return t['tipo'] in ('novedad', 'producto-con-blog', 'video')

    def admisible(t, f):
        if t['id'] in usados or not descansado(t) or not en_ventana(t, f):
            return False
        if t['fabricacion'] == 'institucional':
            return False
        if t['fabricacion'] == 'distribucion' and not destacable(t):
            return False
        return True

    def cuenta_propia():
        prod = [p for p in plan if p['cuenta_cuota']]
        if not prod:
            return 1.0
        return sum(1 for p in prod if p['fabricacion'] == 'propia') / len(prod)

    def fijo_de(f):
        """Devuelve el envio institucional que toca en esta fecha, si toca."""
        del_mes = [d for d in huecos(date(f.year, f.month, 1),
                                    date(f.year, f.month, 28) + timedelta(days=4))
                   if d.month == f.month]
        for mes, sem, asunto, tipo in FIJOS:
            if mes != f.month:
                continue
            objetivo = del_mes[-1] if sem == -1 else del_mes[min(sem - 1, len(del_mes) - 1)]
            if objetivo == f:
                return asunto, tipo
        return None

    def elige_ancla(f):
        sem = f.isocalendar()[1]
        cands = []
        for off in (0, -1, 1):
            for tid in por_semana.get(sem + off, []):
                t = por_id.get(tid)
                if t and admisible(t, f):
                    cands.append((abs(off), t))
        cands.sort(key=lambda c: (c[0], c[1]['ultimo_envio'] or ''))
        return cands[0][1] if cands else None

    def elige(lista, f):
        for t in lista:
            if admisible(t, f):
                return t
        return None

    propia_antigua = sorted([t for t in temas if t['fabricacion'] == 'propia'],
                            key=lambda t: (t['ultimo_envio'] or ''))
    estrenos       = [t for t in temas if t['veces_enviado'] == 0]
    estrenos_propia= [t for t in estrenos if t['fabricacion'] == 'propia']
    todos_antiguos = sorted(temas, key=lambda t: (t['ultimo_envio'] or ''))

    for f in huecos(desde, hasta):
        fijo = fijo_de(f)
        if fijo:
            asunto, tipo = fijo
            plan.append({'fecha': f.isoformat(), 'hora': HORA, 'dia': NOMBRE_DIA[f.weekday()],
                         'semana_iso': f.isocalendar()[1], 'tema_id': None, 'asunto': asunto,
                         'familia': 'institucional', 'fabricacion': 'institucional', 'tipo': tipo,
                         'productos': '', 'paginas_catalogo': [], 'enlaces': [], 'blog': '',
                         'ultimo_envio': None, 'motivo': 'fijo institucional · fecha habitual',
                         'estado': 'propuesta', 'cuenta_cuota': False,
                         'aviso_festivo': (f.month, f.day) in FESTIVOS_AVISO})
            continue

        tema, motivo = None, None
        if cuenta_propia() < cuota:
            tema = elige(propia_antigua, f) or elige(estrenos_propia, f)
            motivo = 'cuota · fabricación propia por debajo del mínimo' if tema else None
        if not tema:
            tema = elige_ancla(f)
            motivo = 'ancla estacional · misma semana en años anteriores' if tema else None
        if not tema:
            tema = elige(estrenos_propia, f) or elige(estrenos, f)
            motivo = 'estreno · tema del banco nunca enviado' if tema else None
        if not tema:
            tema = elige(todos_antiguos, f)
            motivo = 'rotación · el tema disponible más antiguo' if tema else None

        if tema:
            usados.add(tema['id'])
        plan.append({
            'fecha': f.isoformat(), 'hora': HORA, 'dia': NOMBRE_DIA[f.weekday()],
            'semana_iso': f.isocalendar()[1],
            'tema_id': tema['id'] if tema else None,
            'asunto': tema['nombre'] if tema else '(sin propuesta)',
            'familia': tema['familia'] if tema else None,
            'fabricacion': tema['fabricacion'] if tema else None,
            'tipo': tema['tipo'] if tema else None,
            'productos': tema.get('productos', '') if tema else '',
            'paginas_catalogo': tema['paginas_catalogo'] if tema else [],
            'enlaces': tema['enlaces'] if tema else [],
            'blog': tema.get('blog', '') if tema else '',
            'ultimo_envio': tema['ultimo_envio'] if tema else None,
            'motivo': motivo or 'sin candidato disponible',
            'estado': 'propuesta', 'cuenta_cuota': True,
            'aviso_festivo': (f.month, f.day) in FESTIVOS_AVISO,
        })

    salida = args.salida or f'data/plan-{desde.year}-Q{(desde.month-1)//3+1}.json'
    json.dump({'periodo': [args.desde, args.hasta], 'cuota_propia': cuota,
               'generado_por': 'proponer_plan.py', 'envios': plan},
              open(salida, 'w'), ensure_ascii=False, indent=1)

    print(f'{len(plan)} huecos entre {desde} y {hasta}  ->  {salida}\n')
    print(f'{"FECHA":<12}{"DIA":<9}{"ASUNTO":<54}{"FABRIC.":<15}{"ULT.ENVIO":<12}MOTIVO')
    print('-' * 132)
    for p in plan:
        print(f'{p["fecha"]:<12}{p["dia"]:<9}{p["asunto"][:52]:<54}'
              f'{(p["fabricacion"] or "—"):<15}{(p["ultimo_envio"] or "—"):<12}'
              f'{p["motivo"].split(" · ")[0]}{" ⚑" if p["aviso_festivo"] else ""}')
    prod = [p for p in plan if p['cuenta_cuota']]
    print('\nmezcla de los envios de producto:')
    for f, c in Counter(p['fabricacion'] for p in prod).most_common():
        print(f'   {c:3d}  {c/len(prod)*100:5.1f}%  {f}')
    print(f'\ninstitucionales fijos: {len(plan) - len(prod)}')
    print('motivos:')
    for m, c in Counter(p['motivo'] for p in plan).most_common():
        print(f'   {c:3d}  {m}')
    print(f'\ncon enlaces heredados del banco: {sum(1 for p in plan if p["enlaces"])}/{len(plan)}')

if __name__ == '__main__':
    main()
