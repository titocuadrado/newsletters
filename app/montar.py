#!/usr/bin/env python3
"""Ensambla el planificador: CSS de marca + CSS propio + cuerpo + datos + app.js."""
import json, os
SP    = os.path.dirname(os.path.abspath(__file__))
RAIZ  = os.path.dirname(SP) if os.path.basename(SP) == 'app' else '/home/user/newsletters'
MARCA = os.path.join(RAIZ, 'app', 'marca')
DATOS = os.path.join(RAIZ, 'data', 'temas-2027.json')

css  = open(f'{MARCA}/gdp-brand.css').read() + '\n' + open(f'{SP}/app.css').read()
logo = open(f'{MARCA}/logo-gdp.svg').read().strip().replace(
    '<svg ', '<svg class="pl-logo" role="img" aria-label="García de Pou" ', 1)
app  = open(f'{SP}/app.js').read()
cuerpo = open(f'{SP}/cuerpo.html').read().replace('__LOGO__', logo)

plan = json.load(open(DATOS))
envios = [{
    'id': 'e%03d' % i, 'fecha': p['fecha'], 'tema': p['tema'], 'url': p['url'],
    'estado': 'propuesta', 'propia': bool(p['fabricacion_propia']),
    'razon': p['razon'] or '', 'cliente': p['cliente'] or '',
} for i, p in enumerate(plan['envios'], 1)]
estado = {'titulo': 'Plan 2027', 'periodo': plan['periodo'], 'rev': 1,
          'guardado': None, 'envios': envios}

doc = ('<title>Planificador de Newsletters</title>\n'
       '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
       '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
       '<link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;'
       '0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;0,9..40,800;0,9..40,900;1,9..40,300&'
       'family=Caveat:wght@400;500;600&display=swap" rel="stylesheet">\n'
       '<div id="app"></div>\n'
       '<script>\n'
       'const CSS = ' + json.dumps(css) + ';\n'
       'const CUERPO = ' + json.dumps(cuerpo) + ';\n'
       'let ESTADO = ' + json.dumps(estado, ensure_ascii=False) + ';\n\n'
       + app + '\n</script>\n')

cuerpo_script = doc[doc.index('<script>'):doc.rindex('</script>')]
assert '</script' not in cuerpo_script.replace('<\\/script', ''), 'cierre prematuro de script'
open(f'{SP}/planificador.html', 'w').write(doc)
print(f'planificador.html  {len(doc)} bytes  ·  {len(envios)} envíos')
