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
    id_aprobada = pag.evaluate('ESTADO.envios[0].id')
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

    print('\n--- mover envios (las fechas son huecos fijos) ---')
    huecos_antes = pag.evaluate('ESTADO.envios.map(e => e.fecha).join("|")')
    orden_antes  = pag.evaluate('ESTADO.envios.map(e => e.id).join("|")')
    check(pag.eval_on_selector_all('#tabla .pl-asa', 'els => els.length') == 104,
          'cada fila tiene su asa de arrastre')

    # Alt+flecha abajo desde el asa: baja un hueco
    prim = pag.evaluate('ESTADO.envios[0].id')
    pag.eval_on_selector('tr[data-id=\"' + prim + '\"] .pl-asa', 'b => b.focus()')
    pag.keyboard.press('Alt+ArrowDown')
    pag.wait_for_timeout(400)
    check(pag.evaluate(f'ESTADO.envios[1].id') == prim,
          'Alt+flecha abajo mueve el envío un hueco')
    check(pag.evaluate('ESTADO.envios.map(e => e.fecha).join("|")') == huecos_antes,
          'los huecos del calendario no cambian: solo se reparten distinto')
    check('Deshacer' in pag.eval_on_selector('#avisos', 'e => e.textContent'),
          'ofrece deshacer el movimiento')
    check('recolocado' in pag.eval_on_selector('#avisos', 'e => e.textContent'),
          'dice cuántos envíos se han recolocado')
    pag.eval_on_selector('#btn-accion', 'b => b.click()')
    pag.wait_for_timeout(300)
    check(pag.evaluate('ESTADO.envios.map(e => e.id).join("|")') == orden_antes,
          'deshacer devuelve el orden anterior')

    # Se mueve con eventos de puntero, así que el ratón real sirve para probarlo.
    def arrastrar(id_desde, id_hasta, mitad_superior=True):
        # Las dos filas tienen que caber en pantalla: el ratón no puede salir del viewport.
        pag.evaluate(
            "([a, b]) => {"
            " const ra = document.querySelector('tr[data-id=\"'+a+'\"]').getBoundingClientRect();"
            " const rb = document.querySelector('tr[data-id=\"'+b+'\"]').getBoundingClientRect();"
            " const centro = (Math.min(ra.top, rb.top) + Math.max(ra.bottom, rb.bottom)) / 2;"
            " window.scrollBy({top: centro - innerHeight / 2, behavior: 'instant'}); }",
            [id_desde, id_hasta])
        pag.wait_for_timeout(150)
        a = pag.query_selector('tr[data-id="' + id_desde + '"] .pl-asa').bounding_box()
        assert 0 < a['y'] < 950, f'el asa quedó fuera de pantalla: {a}'
        pag.mouse.move(a['x'] + a['width'] / 2, a['y'] + a['height'] / 2)
        pag.mouse.down()
        b = pag.query_selector('tr[data-id="' + id_hasta + '"] td.c-t').bounding_box()
        y = b['y'] + (b['height'] * (0.2 if mitad_superior else 0.8))
        pag.mouse.move(b['x'] + 30, y, steps=8)
        pag.wait_for_timeout(150)

    check(pag.eval_on_selector_all('#tabla tr.pl-antes, #tabla tr.pl-despues',
                                   'els => els.length') == 0,
          'sin arrastre en curso no hay marca de destino')

    # Arrastre corto y visible: el 6.o envio pasa delante del 2.o
    pag.evaluate('window.scrollTo(0, 0)')
    pag.wait_for_timeout(150)
    id_org = pag.evaluate('ESTADO.envios[5].id')
    id_dst = pag.evaluate('ESTADO.envios[1].id')
    arrastrar(id_org, id_dst, True)
    check(pag.eval_on_selector_all('#tabla tr.pl-antes', 'els => els.length') == 1,
          'durante el arrastre se marca dónde va a caer')
    check(pag.eval_on_selector_all('#tabla tr.pl-arrastrando', 'els => els.length') == 1,
          'y la fila que se mueve se atenúa')
    pag.mouse.up()
    pag.wait_for_timeout(400)
    idx = pag.evaluate('ESTADO.envios.findIndex(e => e.id === "' + id_org + '")')
    check(idx == 1, f'el envío cae justo antes del destino (índice {idx}, esperado 1)')
    check(pag.eval_on_selector_all(
              '#tabla tr.pl-antes, #tabla tr.pl-despues, #tabla tr.pl-arrastrando',
              'els => els.length') == 0,
          'al soltar se limpian las marcas de arrastre')
    check(pag.evaluate('document.body.classList.contains("pl-moviendo")') is False,
          'y el cursor de arrastre se retira')
    check(pag.evaluate('window.getSelection().toString().length') == 0,
          'el arrastre no deja media página seleccionada')
    check(pag.evaluate('ESTADO.envios.map(e => e.fecha).join("|")') == huecos_antes,
          'tras el arrastre los huecos del calendario siguen siendo los mismos')
    check(pag.evaluate('ESTADO.envios.length') == 104, 'no se pierde ni se duplica ningún envío')
    check(len(set(pag.evaluate('ESTADO.envios.map(e => e.fecha)'))) == 104,
          'no hay dos envíos en la misma fecha')

    # Soltar en la mitad inferior mete DETRAS del destino
    id_org2 = pag.evaluate('ESTADO.envios[0].id')
    id_dst2 = pag.evaluate('ESTADO.envios[4].id')
    arrastrar(id_org2, id_dst2, False)
    check(pag.eval_on_selector_all('#tabla tr.pl-despues', 'els => els.length') == 1,
          'soltando por la mitad inferior, la marca va al otro lado')
    pag.mouse.up()
    pag.wait_for_timeout(400)
    check(pag.evaluate('ESTADO.envios.findIndex(e => e.id === "' + id_org2 + '")') == 4,
          'y el envío queda detrás del destino')

    print('\n--- scroll automatico al arrastrar hacia el borde ---')
    pag.evaluate("window.scrollTo({top: 1400, behavior: 'instant'})")
    pag.wait_for_timeout(250)
    y0 = pag.evaluate('window.scrollY')
    check(y0 > 200, f'la página está desplazada para la prueba (scrollY={y0})')
    BUSCA_MEDIO = ("(() => { const fs = Array.from(document.querySelectorAll('#tabla tbody tr'));"
                   " const f = fs.find(x => { const r = x.getBoundingClientRect();"
                   " return r.top > 300 && r.top < 600; });"
                   " return f ? f.getAttribute('data-id') : null; })()")
    medio = pag.evaluate(BUSCA_MEDIO)
    check(medio is not None, 'hay una fila a media pantalla para agarrar')
    a = pag.query_selector('tr[data-id="' + medio + '"] .pl-asa').bounding_box()
    pag.mouse.move(a['x'] + a['width'] / 2, a['y'] + a['height'] / 2)
    pag.mouse.down()
    pag.mouse.move(a['x'] + 30, 30, steps=6)      # hasta el borde superior
    pag.wait_for_timeout(700)
    y1 = pag.evaluate('window.scrollY')
    check(y1 < y0 - 50, f'arrastrar al borde superior desplaza la página ({y0} -> {y1})')
    pag.mouse.up()
    pag.wait_for_timeout(300)
    check(pag.evaluate('SCROLL') is None, 'al soltar se detiene el desplazamiento')
    check(pag.evaluate('MOVIENDO') is None, 'y se olvida el envío que se movía')
    pag.evaluate('window.scrollTo(0, 0)')
    pag.wait_for_timeout(150)

    print('\n--- con filtro puesto no se puede arrastrar ---')
    pag.select_option('#f-mes', '05')
    pag.wait_for_timeout(300)
    check(pag.eval_on_selector('#tabla .pl-asa', 'b => b.disabled') is True,
          'con filtro, las asas quedan deshabilitadas')
    check('filtro' in pag.eval_on_selector('#tabla .pl-asa', 'b => b.title').lower(),
          'y explican por qué')
    pag.select_option('#f-mes', 'todos')
    pag.wait_for_timeout(300)
    check(pag.eval_on_selector('#tabla .pl-asa', 'b => b.disabled') is False,
          'al quitar el filtro se vuelven a habilitar')

    print('\n--- deshacer un borrado ---')
    n0 = pag.evaluate('ESTADO.envios.length')
    pag.evaluate('''() => {
      window.confirm = () => true;
      document.querySelector('#tabla tbody tr button[data-accion="borrar"]').click();
    }''')
    pag.wait_for_timeout(300)
    check(pag.evaluate('ESTADO.envios.length') == n0 - 1, 'borrar quita el envío')
    pag.eval_on_selector('#btn-accion', 'b => b.click()')
    pag.wait_for_timeout(300)
    check(pag.evaluate('ESTADO.envios.length') == n0, 'deshacer recupera el envío borrado')

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
    check(pag2.evaluate('ESTADO.envios.find(e => e.id === "' + id_aprobada + '").estado')
          == 'aprobada', 'v2 conserva el estado editado')
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
    check(pagRO.eval_on_selector('#btn-guardar', 'b => b.classList.contains("pl-off")'),
          'tras el rechazo, Guardar queda apagado pero visible')
    check('solo lectura' in pagRO.eval_on_selector('#avisos', 'e => e.textContent').lower(),
          'avisa de que la vista es de solo lectura')

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
    check(pag3.eval_on_selector('#btn-guardar', 'b => b.classList.contains("pl-off")'),
          'el botón de Guardar se ve pero queda apagado')
    check(pag3.eval_on_selector('#btn-csv', 'b => b.classList.contains("pl-off")')
          and pag3.eval_on_selector('#btn-brief', 'b => b.classList.contains("pl-off")'),
          'Exportar CSV y Brief de diseño se ven pero quedan apagados')
    for bid in ('btn-csv', 'btn-brief', 'btn-guardar'):
        vis = pag3.eval_on_selector('#' + bid,
              'b => { const r = b.getBoundingClientRect(); return r.width > 0 && r.height > 0; }')
        check(vis, f'#{bid} sigue visible en la vista compartida')
    pag3.eval_on_selector('#btn-csv', 'b => b.click()')
    pag3.wait_for_timeout(300)
    txt = pag3.eval_on_selector('#avisos', 'e => e.textContent')
    check('no están disponibles' in txt and 'CSV' in txt,
          f'al pulsar Exportar CSV explica por qué no funciona')
    pag3.eval_on_selector('#btn-brief', 'b => b.click()')
    pag3.wait_for_timeout(300)
    check('brief' in pag3.eval_on_selector('#avisos', 'e => e.textContent').lower(),
          'al pulsar Brief de diseño explica por qué no funciona')
    pag3.eval_on_selector('#btn-guardar', 'b => b.click()')
    pag3.wait_for_timeout(300)
    check('solo lectura' in pag3.eval_on_selector('#avisos', 'e => e.textContent').lower(),
          'al pulsar Guardar explica que la vista es de solo lectura')
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
    check(pag3.eval_on_selector('#tabla .pl-asa', 'b => b.disabled') is True,
          'en solo lectura no se pueden mover envíos')
    check(pag3.evaluate('ESTADO.rev') == 2,
          'nada de lo pulsado en la vista compartida cambia el plan')
    nav.close()

print('\n' + '='*60)
print(f'{len(fallos)} fallos' if fallos else 'TODO CORRECTO')
sys.exit(1 if fallos else 0)
