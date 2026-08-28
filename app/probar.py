from playwright.sync_api import sync_playwright
import sys, os, json

SP = os.path.dirname(os.path.abspath(__file__))
frag = open(f'{SP}/planificador.html').read()
# El host de Artifact envuelve el fragmento en un esqueleto: lo replicamos.
open(f'{SP}/v1.html','w').write(
    '<!doctype html><html lang="es"><head><meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width,initial-scale=1">'
    '<style>*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}</style>'
    '</head><body>' + frag + '</body></html>')

fallos = []
def check(cond, msg):
    print(('  OK   ' if cond else '  FALLO') + '  ' + msg)
    if not cond: fallos.append(msg)

with sync_playwright() as pw:
    nav = pw.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
                             args=['--no-sandbox'])
    STUB = '''
      window.__publicado = null;
      window.__descargas = [];
      window.claude = { use: async function(n){
        if (n === 'artifact') return Object.freeze({ publish: async function(html){
          window.__publicado = html; return { version: 'v-test' }; } });
        if (n === 'downloads') return Object.freeze({ save: async function(r){
          window.__descargas.push(r.filename); return { status: 'saved' }; } });
        return null; } };
    '''
    pag = nav.new_page(viewport={'width': 1500, 'height': 1000})
    pag.add_init_script(STUB)
    errores = []
    pag.on('pageerror', lambda e: errores.append(str(e)))
    pag.on('console', lambda m: errores.append('console.' + m.type + ': ' + m.text)
           if m.type == 'error' and 'fonts.g' not in m.text and 'ERR_CONNECTION' not in m.text
           else None)

    print('\n=== VERSION 1 (fragmento, como lo publica la herramienta) ===')
    pag.goto(f'file://{SP}/v1.html')
    pag.wait_for_selector('#tabla tr', timeout=15000)
    check(not errores, f'sin errores de JS  {errores[:3]}')
    filas = pag.eval_on_selector_all('#tabla tbody tr', 'els => els.length')
    check(filas == 104, f'104 filas renderizadas (hay {filas})')
    meses = pag.eval_on_selector_all('.pl-mes', 'els => els.length')
    check(meses == 12, f'12 secciones de mes (hay {meses})')
    kpi = pag.eval_on_selector_all('.pl-kpi b', 'els => els.map(e=>e.textContent)')
    check(kpi[0] == '104' and kpi[1] == '94%', f'KPIs correctos: {kpi}')
    check(pag.eval_on_selector('#btn-guardar', 'b => b.disabled') is True,
          'Guardar arranca deshabilitado (nada sucio)')

    print('\n--- editar el tema de la primera fila ---')
    ed = pag.query_selector('#tabla tbody tr [data-campo="tema"]')
    ed.click()
    pag.keyboard.press('Control+a')
    pag.keyboard.type('PRUEBA tema editado')
    pag.wait_for_timeout(200)
    nuevo = pag.evaluate('ESTADO.envios.find(e=>e.tema.indexOf("PRUEBA")===0) ? '
                         'ESTADO.envios.find(e=>e.tema.indexOf("PRUEBA")===0).tema : null')
    check(nuevo == 'PRUEBA tema editado', f'el tema llega a ESTADO: {nuevo!r}')
    check(pag.eval_on_selector('#sucio', 'e => e.textContent') == 'Cambios sin guardar',
          'el indicador pasa a "Cambios sin guardar"')
    check(pag.eval_on_selector('#btn-guardar', 'b => b.disabled') is False,
          'Guardar se habilita')

    print('\n--- cambiar estado y fecha ---')
    pag.select_option('#tabla tbody tr:first-child select[data-campo="estado"]', 'aprobada')
    pag.wait_for_timeout(200)
    check(pag.evaluate('ESTADO.envios[0].estado') == 'aprobada', 'el estado llega a ESTADO')
    check(pag.eval_on_selector('#tabla tbody tr:first-child td.c-e',
                               'e => e.getAttribute("data-estado")') == 'aprobada',
          'la celda se recolorea')

    print('\n--- pegar una URL en un envio que no la tenia ---')
    sinurl = pag.evaluate('ESTADO.envios.findIndex(e => !e.url)')
    check(sinurl > -1, f'hay envíos sin URL (índice {sinurl})')
    pag.evaluate('''() => {
      const id = ESTADO.envios.find(e => !e.url).id;
      const inp = document.querySelector('tr[data-id="'+id+'"] input[data-campo="url"]');
      inp.value = 'https://www.garciadepou.com/es/un-solo-uso/posavasos.html';
      inp.dispatchEvent(new Event('input', {bubbles:true}));
    }''')
    pag.wait_for_timeout(150)
    check(pag.evaluate('ESTADO.envios.filter(e=>e.url && e.url.indexOf("posavasos")>-1).length') == 1,
          'la URL pegada llega a ESTADO')

    print('\n--- filtros ---')
    pag.select_option('#f-mes', '10')
    pag.wait_for_timeout(200)
    oct_ = pag.eval_on_selector_all('#tabla tbody tr', 'els => els.length')
    esperado = pag.evaluate('ESTADO.envios.filter(e => e.fecha.slice(5,7)==="10").length')
    check(oct_ == esperado, f'el filtro de octubre deja los {esperado} de octubre (hay {oct_})')
    pag.select_option('#f-mes', 'todos')
    pag.fill('#f-texto', 'navidad')
    pag.wait_for_timeout(250)
    nav_ = pag.eval_on_selector_all('#tabla tbody tr', 'els => els.length')
    check(nav_ > 0 and nav_ < 104, f'el buscador filtra ({nav_} filas con "navidad")')
    pag.fill('#f-texto', '')
    pag.wait_for_timeout(200)

    print('\n--- añadir y borrar ---')
    pag.click('#btn-nuevo')
    pag.wait_for_timeout(300)
    check(pag.evaluate('ESTADO.envios.length') == 105, 'añadir envío deja 105')
    pag.evaluate('''() => {
      const id = ESTADO.envios[ESTADO.envios.length-1].id;
      window.confirm = () => true;
      document.querySelector('tr[data-id="'+id+'"] button[data-accion="borrar"]').click();
    }''')
    pag.wait_for_timeout(300)
    check(pag.evaluate('ESTADO.envios.length') == 104, 'borrar vuelve a 104')

    print('\n--- exportaciones ---')
    ncsv = pag.evaluate('csv().split("\\r\\n").length')
    check(ncsv == 105, f'CSV con cabecera + 104 filas (hay {ncsv})')
    nb = pag.evaluate('brief().length')
    check(nb > 5000, f'el brief tiene contenido ({nb} caracteres)')

    print('\n--- descarga del CSV ---')
    pag.click('#btn-csv')
    pag.wait_for_timeout(400)
    check(pag.evaluate('window.__descargas') == ['newsletters-2027.csv'],
          f'pide guardar el CSV: {pag.evaluate("window.__descargas")}')

    print('\n--- guardar (publish) ---')
    check(pag.eval_on_selector('#sucio', 'e => e.textContent') == 'Cambios sin guardar',
          'sigue marcado como sucio antes de guardar')
    pag.click('#btn-guardar')
    pag.wait_for_timeout(600)
    pub = pag.evaluate('window.__publicado')
    check(bool(pub) and pub.startswith('<!doctype html>'),
          'guardar publica un documento completo')
    check(pag.evaluate('ESTADO.rev') == 2, f'la revisión sube a 2 (es {pag.evaluate("ESTADO.rev")})')

    print('\n=== RECONSTRUCCION: la pagina se reescribe a si misma ===')
    v2 = pag.evaluate('window.__publicado || documento(ESTADO)')
    check(v2.startswith('<!doctype html>'), 'el documento empieza por el doctype')
    check('</html>' in v2, 'el documento se cierra')
    open(f'{SP}/v2.html','w').write(v2)
    print(f'  v2: {len(v2)} bytes')

    pag.screenshot(path=f'{SP}/captura-v1.png', full_page=False)

    print('\n=== VERSION 2 (documento generado al guardar) ===')
    pag2 = nav.new_page(viewport={'width': 1500, 'height': 1000})
    pag2.add_init_script(STUB)
    err2 = []
    pag2.on('pageerror', lambda e: err2.append(str(e)))
    pag2.on('console', lambda m: err2.append('console.' + m.type + ': ' + m.text)
            if m.type == 'error' and 'fonts.g' not in m.text and 'ERR_CONNECTION' not in m.text
            else None)
    pag2.goto(f'file://{SP}/v2.html')
    pag2.wait_for_selector('#tabla tr', timeout=15000)
    check(not err2, f'sin errores de JS en v2  {err2[:3]}')
    filas2 = pag2.eval_on_selector_all('#tabla tbody tr', 'els => els.length')
    check(filas2 == 104, f'v2 renderiza 104 filas (hay {filas2})')
    check(pag2.evaluate('ESTADO.envios[0].estado') == 'aprobada',
          'v2 conserva el estado editado')
    check(pag2.evaluate('ESTADO.envios.filter(e=>e.tema.indexOf("PRUEBA")===0).length') == 1,
          'v2 conserva el tema editado')
    check(pag2.evaluate('ESTADO.envios.filter(e=>e.url && e.url.indexOf("posavasos")>-1).length') == 1,
          'v2 conserva la URL pegada')
    check(pag2.evaluate('typeof documento === "function"'),
          'v2 sigue sabiendo reconstruirse (tercera generación)')
    v3 = pag2.evaluate('documento(ESTADO)')
    check(v3.startswith('<!doctype html>') and len(v3) > 50000,
          f'v3 se genera correctamente ({len(v3)} bytes)')
    check(pag2.eval_on_selector('#sucio', 'e => e.textContent') == 'Todo guardado',
          'v2 arranca limpio')
    check(pag2.evaluate('ESTADO.rev') == 2, 'v2 conserva la revisión guardada')

    print('\n--- vista de solo lectura (publish rechaza not_writer) ---')
    pagRO = nav.new_page()
    pagRO.add_init_script('''
      window.claude = { use: async function(n){
        if (n === 'artifact') return Object.freeze({ publish: async function(){
          const e = new Error('read only'); e.code = 'not_writer'; throw e; } });
        if (n === 'downloads') return Object.freeze({ save: async function(){
          return {status:'saved'}; } });
        return null; } };
    ''')
    pagRO.goto(f'file://{SP}/v2.html')
    pagRO.wait_for_selector('#tabla tr', timeout=15000)
    pagRO.eval_on_selector('#tabla tbody tr [data-campo=\"tema\"]',
                           'e => { e.textContent = \"editado por un invitado\"; '
                           'e.dispatchEvent(new Event(\"input\", {bubbles:true})); }')
    pagRO.wait_for_timeout(200)
    pagRO.click('#btn-guardar')
    pagRO.wait_for_timeout(600)
    check('solo lectura' in pagRO.eval_on_selector('#avisos', 'e => e.textContent').lower(),
          'avisa de que la vista es de solo lectura')
    check(pagRO.eval_on_selector('#btn-guardar', 'b => b.disabled') is True,
          'deshabilita Guardar tras el rechazo')
    check(pagRO.evaluate('ESTADO.rev') == 2, 'no deja la revisión descuadrada tras el fallo')
    pag2.screenshot(path=f'{SP}/captura-v2.png', full_page=False)

    print('\n=== SIN window.claude (vista sin capacidades) ===')
    pag3 = nav.new_page()
    err3 = []
    pag3.on('pageerror', lambda e: err3.append(str(e)))
    pag3.goto(f'file://{SP}/v2.html')
    pag3.wait_for_selector('#tabla tr', timeout=15000)
    pag3.wait_for_timeout(600)
    check(not err3, f'no revienta sin window.claude  {err3[:2]}')
    check(pag3.eval_on_selector('#sucio', 'e => e.textContent').startswith('Solo lectura'),
          'pasa a modo solo lectura')
    check(pag3.eval_on_selector('#btn-guardar', 'b => b.style.display') == 'none',
          'esconde el botón de Guardar')
    check('solo lectura' in pag3.eval_on_selector('#pie-guardar', 'e => e.textContent').lower(),
          'el pie explica que los cambios no se guardan')
    check(pag3.eval_on_selector_all('#tabla tbody tr', 'els => els.length') == 104,
          'la copia congelada sigue mostrando los 104 envíos')
    pag3.eval_on_selector('#tabla tbody tr [data-campo=\"tema\"]',
                          'e => { e.textContent = \"un invitado escribiendo\"; '
                          'e.dispatchEvent(new Event(\"input\", {bubbles:true})); }')
    pag3.wait_for_timeout(200)
    check(pag3.eval_on_selector('#sucio', 'e => e.textContent').startswith('Solo lectura'),
          'sigue diciendo solo lectura aunque el invitado escriba')
    check(pag3.eval_on_selector('#btn-csv', 'b => b.style.display') == 'none',
          'oculta los botones de descarga')
    nav.close()

print('\n' + '='*60)
print(f'{len(fallos)} fallos' if fallos else 'TODO CORRECTO')
sys.exit(1 if fallos else 0)
