#!/usr/bin/env python3
"""
Empaqueta lo que el planificador necesita para planificar dentro del navegador:
las ocasiones comerciales y el índice de URL reales del histórico.

El botón "Planificar trimestre" no llama a ningún servidor: el motor va dentro de
la página, y estos son sus datos.
"""
import json, os
from collections import Counter

ocas = json.load(open('data/calendario-comercial.json'))['ocasiones']
hist = [e for e in json.load(open('data/historico.json'))['envios']
        if not e.get('revision_previa')]

# URL -> última vez que se usó de verdad en una newsletter
urls = {}
for e in hist:
    for u in e.get('enlaces', []):
        if u not in urls or e['fecha'] > urls[u]:
            urls[u] = e['fecha']

datos = {
    'ocasiones': [{'tema': o['tema'], 'meses': o['meses'], 'razon': o['razon'],
                   'cliente': o['cliente'], 'claves': o['claves'], 'propia': o['propia']}
                  for o in ocas],
    'urls': [{'u': u, 'v': v} for u, v in sorted(urls.items())],
}
json.dump(datos, open('data/planificador-datos.json', 'w'), ensure_ascii=False,
          separators=(',', ':'))

print(f'ocasiones ........ {len(datos["ocasiones"])}')
print(f'  fabricación propia {sum(1 for o in datos["ocasiones"] if o["propia"])}')
por_mes = Counter()
for o in datos['ocasiones']:
    for m in o['meses']:
        por_mes[m] += 1
print('  por mes .........', {m: por_mes[m] for m in range(1, 13)})
print(f'urls del histórico  {len(datos["urls"])}')
print(f'  posteriores a la migración {sum(1 for x in datos["urls"] if x["v"] >= "2025-10-01")}')
print(f'tamaño ........... {os.path.getsize("data/planificador-datos.json") / 1024:.0f} KB')
