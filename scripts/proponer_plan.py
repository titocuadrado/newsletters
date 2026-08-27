#!/usr/bin/env python3
"""
Propone el planning de un trimestre: genera las fechas y asigna un tema a cada hueco.

Reglas de asignacion, en este orden:
  1. Ancla estacional  - que se envio en esa misma semana del anyo en anyos anteriores
  2. Descanso          - no repetir un tema enviado en los ultimos MESES_DESCANSO meses
  3. Estrenos          - reservar huecos para temas del banco nunca enviados
  4. Equilibrio        - reservar huecos para las familias infrarrepresentadas
  5. Fijos             - lanzamientos de catalogo y tarifas en su fecha habitual

Uso:  python3 scripts/proponer_plan.py --desde 2027-01-01 --hasta 2027-03-31
"""
import json, argparse, unicodedata, re
from datetime import date, timedelta
from collections import Counter, defaultdict

MESES_DESCANSO = 12          # meses minimos antes de repetir un tema
CUOTA_ESTRENOS = 0.30        # 30% de los huecos para temas nunca enviados
DIAS_ENVIO = (1, 3)          # martes y jueves
HORA = '15:00'
FAMILIAS_INFRA = ('limpieza-higiene', 'habitaciones', 'utensilios-cocina', 'rotulacion')

# Ventanas estacionales: meses en los que un tema TIENE sentido.
# Sin esto el ancla estacional arrastra temas de Navidad a la primera semana de enero.
VENTANAS_FAMILIA = {'cotillon': (10, 11, 12)}
VENTANAS_CLAVE = [
    (('navidad','cotillon','kerstmis','christmas','fin de ano','felicitacion',
      'lotes','regalo','botellas navidad'), (10, 11, 12)),
    (('san valentin',),                       (1, 2)),
    (('castana','churro','sopa','crema','bebidas calientes','vasos cafe',
      'chocolate caliente'),                  (10, 11, 12, 1, 2, 3)),
    (('granizado','batido','helado','terraza','bebidas frias','flurry',
      'refrescante','polo'),                  (4, 5, 6, 7, 8, 9)),
    (('catalogo navidad','cataleg navidad'),  (7, 8, 9)),
]
NOMBRE_DIA = ['lunes','martes','miercoles','jueves','viernes','sabado','domingo']

# Festivos en los que historicamente SI se ha enviado -> no se bloquean, solo se avisan
FESTIVOS_AVISO = {(1,1),(1,6),(4,2),(5,1),(8,15),(11,1),(12,6),(12,8),(12,25),(12,26)}

def sinacentos(s):
    s = unicodedata.normalize('NFD', str(s).lower())
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn')

def huecos(desde, hasta):
    """Todas las fechas de envio del periodo."""
    out, d = [], desde
    while d <= hasta:
        if d.weekday() in DIAS_ENVIO:
            out.append(d)
        d += timedelta(days=1)
    return out

def cargar():
    temas = json.load(open('data/temas.json'))['temas']
    envios = json.load(open('data/historico.json'))['envios']
    return temas, envios

def meses_desde(iso, ref):
    f = date.fromisoformat(iso)
    return (ref.year - f.year) * 12 + (ref.month - f.month)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--desde', required=True)
    ap.add_argument('--hasta', required=True)
    ap.add_argument('--salida', default=None)
    args = ap.parse_args()
    desde, hasta = date.fromisoformat(args.desde), date.fromisoformat(args.hasta)

    temas, envios = cargar()
    por_id = {t['id']: t for t in temas}

    # Indice: semana ISO -> temas usados en esa semana en anyos anteriores
    por_semana = defaultdict(list)
    for e in envios:
        f = date.fromisoformat(e['fecha'])
        por_semana[f.isocalendar()[1]].append(e)

    # Disponibilidad
    def descansado(t):
        return t['ultimo_envio'] is None or meses_desde(t['ultimo_envio'], desde) >= MESES_DESCANSO

    def en_ventana(t, f):
        """El tema encaja en el mes de esta fecha."""
        v = VENTANAS_FAMILIA.get(t['familia'])
        if v and f.month not in v:
            return False
        n = sinacentos(t['nombre'])
        for claves, meses in VENTANAS_CLAVE:
            if any(k in n for k in claves) and f.month not in meses:
                return False
        return True

    def libre(t, f):
        return t['id'] not in usados and descansado(t) and en_ventana(t, f)

    estrenos = [t for t in temas if t['veces_enviado'] == 0]
    infra    = [t for t in temas if t['familia'] in FAMILIAS_INFRA]

    fechas = huecos(desde, hasta)
    n_estrenos = round(len(fechas) * CUOTA_ESTRENOS)

    plan, usados = [], set()

    def elige_estacional(f):
        """Tema usado en esta semana ISO en anyos anteriores y ya descansado."""
        sem = f.isocalendar()[1]
        candidatos = []
        for offset in (0, -1, 1):                      # semana exacta, luego vecinas
            for e in por_semana.get(sem + offset, []):
                base = re.sub(r'^(repetida|repetir|resend)\s*:?\s*', '', sinacentos(e['tema'])).strip()
                k = re.sub(r'[^a-z0-9]+', '-', base).strip('-')[:60]
                t = por_id.get(k)
                if t and libre(t, f):
                    candidatos.append((abs(offset), t))
        candidatos.sort(key=lambda c: (c[0], c[1]['ultimo_envio'] or ''))
        return candidatos[0][1] if candidatos else None

    def elige_de(lista, f):
        for t in lista:
            if libre(t, f):
                return t
        return None

    for i, f in enumerate(fechas):
        motivo, tema = None, None
        # 1 de cada 3 huecos se reserva a estreno / familia infrarrepresentada
        if i % 3 == 2 and len([p for p in plan if p['motivo'].startswith('estreno')]) < n_estrenos:
            tema = elige_de(infra, f)
            motivo = 'estreno · familia infrarrepresentada' if tema else None
            if not tema:
                tema = elige_de(estrenos, f)
                motivo = 'estreno · tema del banco nunca enviado' if tema else None
        if not tema:
            tema = elige_estacional(f)
            motivo = 'ancla estacional · misma semana en anyos anteriores' if tema else None
        if not tema:
            tema = elige_de(sorted(temas, key=lambda t: (t['ultimo_envio'] or '')), f)
            motivo = 'rotacion · el tema mas antiguo disponible' if tema else None

        if tema:
            usados.add(tema['id'])
        plan.append({
            'fecha': f.isoformat(), 'hora': HORA, 'dia': NOMBRE_DIA[f.weekday()],
            'semana_iso': f.isocalendar()[1],
            'tema_id': tema['id'] if tema else None,
            'asunto': tema['nombre'] if tema else '(sin propuesta)',
            'familia': tema['familia'] if tema else None,
            'paginas_catalogo': tema['paginas_catalogo'] if tema else [],
            'url_es': tema['url_es'] if tema else None,
            'ultimo_envio': tema['ultimo_envio'] if tema else None,
            'motivo': motivo or 'sin candidato',
            'estado': 'propuesta',
            'aviso_festivo': (f.month, f.day) in FESTIVOS_AVISO,
        })

    salida = args.salida or f'data/plan-{desde.year}-Q{(desde.month-1)//3+1}.json'
    json.dump({'periodo': [args.desde, args.hasta], 'generado_por': 'proponer_plan.py',
               'envios': plan}, open(salida, 'w'), ensure_ascii=False, indent=1)

    print(f'{len(plan)} huecos entre {desde} y {hasta}  ->  {salida}\n')
    print(f'{"FECHA":<12}{"DIA":<10}{"ASUNTO":<58}{"FAM":<18}ULT.ENVIO')
    print('-'*116)
    for p in plan:
        u = p['ultimo_envio'] or '—'
        av = ' ⚑' if p['aviso_festivo'] else ''
        print(f'{p["fecha"]:<12}{p["dia"]:<10}{p["asunto"][:56]:<58}{(p["familia"] or "—"):<18}{u}{av}')
    print()
    print('motivos:')
    for m, c in Counter(p['motivo'] for p in plan).most_common():
        print(f'   {c:3d}  {m}')
    print(f'\nsin URL todavia: {sum(1 for p in plan if not p["url_es"])}/{len(plan)}')
    print(f'avisos de festivo: {sum(1 for p in plan if p["aviso_festivo"])}')

if __name__ == '__main__':
    main()
