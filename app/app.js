/* ── Planificador de newsletters · García de Pou ───────────────────────────
   La página se reescribe a sí misma: al guardar, documento(ESTADO) devuelve
   el documento completo con los datos incrustados y se publica como nueva
   versión. Por eso todas las funciones son declaraciones de primer nivel:
   codigoFuente() las serializa con toString().
   ──────────────────────────────────────────────────────────────────────── */

const ESTADOS = [
  ['idea',          'Idea'],
  ['propuesta',     'Propuesta'],
  ['en-aprobacion', 'En aprobación'],
  ['aprobada',      'Aprobada'],
  ['en-diseno',     'En diseño'],
  ['montada',       'Montada'],
  ['enviada',       'Enviada'],
];
const MESES = ['','Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto',
               'Septiembre','Octubre','Noviembre','Diciembre'];
const DIAS = ['Domingo','Lunes','Martes','Miércoles','Jueves','Viernes','Sábado'];

let FILTROS = { mes: 'todos', estado: 'todos', texto: '', razon: true };
let SUCIO = false;
let SOLO_LECTURA = false;
let PUEDE_DESCARGAR = false;
let ANTERIOR = null;      // instantánea para deshacer, un nivel
let MOVIENDO = null;      // {id, destino, antes} mientras se arrastra
let SCROLL = null;        // temporizador del scroll automático al llegar al borde

function esc(s) {
  return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function nuevoId() {
  return 'e' + Math.random().toString(36).slice(2, 9);
}

function fechaLarga(iso) {
  const p = iso.split('-');
  const d = new Date(+p[0], +p[1] - 1, +p[2]);
  return DIAS[d.getDay()];
}

function ordenar() {
  ESTADO.envios.sort(function (a, b) { return a.fecha < b.fecha ? -1 : a.fecha > b.fecha ? 1 : 0; });
}

function hayFiltro() {
  return FILTROS.mes !== 'todos' || FILTROS.estado !== 'todos' || FILTROS.texto.trim() !== '';
}

function instantanea() {
  ANTERIOR = JSON.parse(JSON.stringify(ESTADO.envios));
}

function deshacer() {
  if (!ANTERIOR) return;
  ESTADO.envios = ANTERIOR;
  ANTERIOR = null;
  marcarSucio(true);
  pintar();
  document.getElementById('avisos').innerHTML = '';
}

function indiceDe(id) {
  for (let i = 0; i < ESTADO.envios.length; i++) {
    if (ESTADO.envios[i].id === id) return i;
  }
  return -1;
}

function reasignarHuecos() {
  // Las fechas son huecos fijos del calendario: se vuelven a repartir en orden.
  const huecos = ESTADO.envios.map(function (e) { return e.fecha; }).sort();
  ESTADO.envios.forEach(function (e, i) { e.fecha = huecos[i]; });
}

function mover(id, destino) {
  // destino = índice donde debe quedar el envío, en la lista completa ya ordenada
  ordenar();
  const desde = indiceDe(id);
  if (desde === -1) return 0;
  let hasta = Math.max(0, Math.min(ESTADO.envios.length - 1, destino));
  if (hasta === desde) return 0;
  instantanea();
  const e = ESTADO.envios.splice(desde, 1)[0];
  ESTADO.envios.splice(hasta, 0, e);
  reasignarHuecos();
  return Math.abs(hasta - desde);
}

function tras(saltos, id) {
  if (!saltos) return;
  marcarSucio(true);
  pintar();
  const e = ESTADO.envios[indiceDe(id)];
  const p = e.fecha.split('-');
  const n = Math.abs(saltos);
  aviso('«' + e.tema.slice(0, 48) + '» pasa al ' + (+p[2]) + ' de ' + MESES[+p[1]].toLowerCase()
        + '. Se han recolocado ' + n + (n === 1 ? ' envío más.' : ' envíos más.'),
        'ok', { texto: 'Deshacer', fn: deshacer });
  const fila = document.querySelector('tr[data-id="' + id + '"]');
  if (fila) {
    fila.classList.add('pl-recien');
    fila.scrollIntoView({ block: 'center', behavior: 'smooth' });
  }
}

function moverUno(id, delta) {
  if (SOLO_LECTURA) return;
  ordenar();
  const saltos = mover(id, indiceDe(id) + delta);
  tras(saltos, id);
}

function filtrados() {
  const t = FILTROS.texto.trim().toLowerCase();
  return ESTADO.envios.filter(function (e) {
    if (FILTROS.mes !== 'todos' && e.fecha.slice(5, 7) !== FILTROS.mes) return false;
    if (FILTROS.estado !== 'todos' && e.estado !== FILTROS.estado) return false;
    if (t && (e.tema + ' ' + (e.url || '') + ' ' + (e.razon || '')).toLowerCase().indexOf(t) === -1) return false;
    return true;
  });
}

function opcionesEstado(sel) {
  return ESTADOS.map(function (x) {
    return '<option value="' + x[0] + '"' + (x[0] === sel ? ' selected' : '') + '>' + x[1] + '</option>';
  }).join('');
}

function pintarKpis() {
  const n = ESTADO.envios.length;
  const propia = ESTADO.envios.filter(function (e) { return e.propia; }).length;
  const conUrl = ESTADO.envios.filter(function (e) { return e.url; }).length;
  const porEstado = {};
  ESTADO.envios.forEach(function (e) { porEstado[e.estado] = (porEstado[e.estado] || 0) + 1; });
  const avance = ESTADO.envios.filter(function (e) {
    return ['aprobada', 'en-diseno', 'montada', 'enviada'].indexOf(e.estado) > -1;
  }).length;
  const kpis = [
    [n, 'envíos en el plan'],
    [n ? Math.round(propia / n * 100) + '%' : '—', 'papel y cartón propio'],
    [conUrl + ' / ' + n, 'con URL de referencia'],
    [avance + ' / ' + n, 'aprobados o más'],
  ];
  document.getElementById('kpis').innerHTML = kpis.map(function (k) {
    return '<div class="pl-kpi"><b>' + k[0] + '</b><span>' + k[1] + '</span></div>';
  }).join('');
}

function pintar() {
  ordenar();
  pintarKpis();
  const filtrado = hayFiltro();
  const lista = filtrados();
  const cont = document.getElementById('tabla');
  if (!lista.length) {
    cont.innerHTML = '<p class="pl-vacio">Ningún envío coincide con el filtro.</p>';
    return;
  }
  let html = '', mesPrevio = null;
  lista.forEach(function (e) {
    const mes = e.fecha.slice(0, 7);
    if (mes !== mesPrevio) {
      if (mesPrevio !== null) html += '</tbody></table></section>';
      const nMes = lista.filter(function (x) { return x.fecha.slice(0, 7) === mes; }).length;
      html += '<section class="pl-mes"><div class="pl-mes-head">'
        + '<h2 class="pl-mes-t">' + MESES[+mes.slice(5, 7)] + ' <em>' + mes.slice(0, 4) + '</em></h2>'
        + '<span class="pl-mes-n">' + nMes + (nMes === 1 ? ' envío' : ' envíos') + '</span></div>'
        + '<table class="pl-t"><thead><tr>'
        + '<th class="c-g"><span class="pl-oculto">Mover</span></th>'
        + '<th class="c-f">Fecha</th><th class="c-t">Tema</th><th class="c-u">URL</th>'
        + '<th class="c-e">Estado</th><th class="c-x"></th></tr></thead><tbody>';
      mesPrevio = mes;
    }
    const mover_ok = !SOLO_LECTURA && !filtrado;
    html += '<tr data-id="' + e.id + '">'
      + '<td class="c-g"><button class="pl-asa"' + (mover_ok ? '' : ' disabled')
      + ' aria-label="Mover el envío del ' + esc(e.fecha)
      + '. Alt y flecha arriba o abajo para cambiarlo de hueco."'
      + ' title="' + (mover_ok ? 'Arrastrar para cambiar de hueco · Alt+↑ / Alt+↓'
                               : 'Quita el filtro para poder mover envíos') + '">'
      + '<span aria-hidden="true">⠿</span></button></td>'
      + '<td class="c-f"><input type="date" data-campo="fecha" value="' + esc(e.fecha) + '" aria-label="Fecha del envío">'
      + '<em>' + fechaLarga(e.fecha) + ' · 15:00</em></td>'
      + '<td class="c-t"><div class="pl-edit" contenteditable="plaintext-only" data-campo="tema" '
      + 'role="textbox" aria-label="Tema">' + esc(e.tema) + '</div>'
      + (e.razon && FILTROS.razon ? '<span class="pl-razon">' + esc(e.razon) + '</span>' : '')
      + (e.propia ? '' : '<span class="pl-tag">no es fabricación propia</span>')
      + '</td>'
      + '<td class="c-u"><input type="text" data-campo="url" value="' + esc(e.url || '') + '" '
      + 'placeholder="Sin URL — pegar aquí" aria-label="URL de categoría">'
      + (e.url ? '<a class="pl-abrir" href="' + esc(e.url) + '" target="_blank" rel="noopener">abrir ↗</a>' : '')
      + '</td>'
      + '<td class="c-e" data-estado="' + e.estado + '"><select data-campo="estado" '
      + 'aria-label="Estado">' + opcionesEstado(e.estado) + '</select></td>'
      + '<td class="c-x"><button class="pl-borrar" data-accion="borrar" title="Quitar este envío" '
      + 'aria-label="Quitar el envío del ' + esc(e.fecha) + '">×</button></td>'
      + '</tr>';
  });
  html += '</tbody></table></section>';
  cont.innerHTML = html;
}

function marcarSucio(si) {
  SUCIO = si;
  const b = document.getElementById('btn-guardar');
  const s = document.getElementById('sucio');
  if (SOLO_LECTURA) {
    s.textContent = 'Solo lectura \u00b7 los cambios no se guardan';
    s.className = 'pl-sucio pl-sucio--ro';
    return;
  }
  s.textContent = si ? 'Cambios sin guardar' : 'Todo guardado';
  s.className = 'pl-sucio' + (si ? ' pl-sucio--si' : '');
  b.disabled = !si;
}

function buscaEnvio(id) {
  return ESTADO.envios.filter(function (e) { return e.id === id; })[0];
}

function alEditar(ev) {
  const campo = ev.target.getAttribute && ev.target.getAttribute('data-campo');
  if (!campo) return;
  const fila = ev.target.closest('tr');
  if (!fila) return;
  const e = buscaEnvio(fila.getAttribute('data-id'));
  if (!e) return;
  if (campo === 'tema') {
    e.tema = ev.target.textContent.replace(/\s+/g, ' ').trim();
  } else if (campo === 'url') {
    e.url = ev.target.value.trim() || null;
  } else if (campo === 'fecha') {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(ev.target.value)) return;
    e.fecha = ev.target.value;
    marcarSucio(true);
    pintar();
    return;
  } else if (campo === 'estado') {
    e.estado = ev.target.value;
    marcarSucio(true);
    pintar();
    return;
  }
  marcarSucio(true);
}

function alPulsar(ev) {
  const b = ev.target.closest('button[data-accion]');
  if (!b) return;
  const fila = b.closest('tr');
  const id = fila.getAttribute('data-id');
  const e = buscaEnvio(id);
  if (b.getAttribute('data-accion') === 'borrar') {
    if (!confirm('¿Quitar el envío «' + e.tema.slice(0, 60) + '»?')) return;
    instantanea();
    ESTADO.envios = ESTADO.envios.filter(function (x) { return x.id !== id; });
    marcarSucio(true);
    pintar();
    aviso('Quitado «' + e.tema.slice(0, 48) + '».', 'warn', { texto: 'Deshacer', fn: deshacer });
  }
}

function limpiaSeleccion() {
  const sel = window.getSelection ? window.getSelection() : null;
  if (sel && sel.removeAllRanges) { try { sel.removeAllRanges(); } catch (err) {} }
}

function limpiaMarcas() {
  const t = document.getElementById('tabla');
  ['pl-arrastrando', 'pl-antes', 'pl-despues'].forEach(function (c) {
    t.querySelectorAll('.' + c).forEach(function (el) { el.classList.remove(c); });
  });
}

/* Mover envíos con eventos de puntero, no con HTML5 drag-and-drop: así funciona
   igual con ratón y con dedo, y no se pelea con los campos editables de la fila. */

function marcaDestino() {
  limpiaMarcas();
  if (!MOVIENDO) return;
  const orig = document.querySelector('tr[data-id="' + MOVIENDO.id + '"]');
  if (orig) orig.classList.add('pl-arrastrando');
  if (!MOVIENDO.destino) return;
  const fila = document.querySelector('tr[data-id="' + MOVIENDO.destino + '"]');
  if (fila) fila.classList.add(MOVIENDO.antes ? 'pl-antes' : 'pl-despues');
}

function autoScroll(y) {
  // Con 104 filas hay que poder arrastrar más allá de lo que se ve.
  const margen = 90;
  const paso = y < margen ? -14 : (y > window.innerHeight - margen ? 14 : 0);
  if (!paso) {
    if (SCROLL) { clearInterval(SCROLL); SCROLL = null; }
    return;
  }
  if (SCROLL) return;
  SCROLL = setInterval(function () {
    window.scrollBy({ top: paso, behavior: 'instant' });
  }, 16);
}

function alPunteroAbajo(ev) {
  const asa = ev.target.closest('.pl-asa');
  if (!asa || asa.disabled) return;
  if (SOLO_LECTURA || hayFiltro()) return;
  ev.preventDefault();
  const fila = asa.closest('tr');
  MOVIENDO = { id: fila.getAttribute('data-id'), destino: null, antes: true };
  document.body.classList.add('pl-moviendo');
  limpiaSeleccion();
  try { asa.setPointerCapture(ev.pointerId); } catch (err) {}
  asa.addEventListener('pointermove', alPunteroMueve);
  asa.addEventListener('pointerup', alPunteroArriba);
  asa.addEventListener('pointercancel', alPunteroFin);
  marcaDestino();
}

function alPunteroMueve(ev) {
  if (!MOVIENDO) return;
  ev.preventDefault();
  limpiaSeleccion();
  autoScroll(ev.clientY);
  const el = document.elementFromPoint(ev.clientX, ev.clientY);
  const fila = el && el.closest ? el.closest('tr[data-id]') : null;
  if (!fila || fila.getAttribute('data-id') === MOVIENDO.id) {
    MOVIENDO.destino = null;
  } else {
    const caja = fila.getBoundingClientRect();
    MOVIENDO.antes = (ev.clientY - caja.top) < caja.height / 2;
    MOVIENDO.destino = fila.getAttribute('data-id');
  }
  marcaDestino();
}

function alPunteroArriba(ev) {
  if (!MOVIENDO) return;
  const m = MOVIENDO;
  alPunteroFin(ev);
  if (!m.destino) return;
  ordenar();
  const iOrigen = indiceDe(m.id);
  let iDestino = indiceDe(m.destino);
  if (!m.antes) iDestino = iDestino + 1;
  if (iOrigen < iDestino) iDestino = iDestino - 1;
  tras(mover(m.id, iDestino), m.id);
}

function alPunteroFin(ev) {
  const asa = ev && ev.currentTarget;
  if (asa && asa.removeEventListener) {
    asa.removeEventListener('pointermove', alPunteroMueve);
    asa.removeEventListener('pointerup', alPunteroArriba);
    asa.removeEventListener('pointercancel', alPunteroFin);
  }
  if (SCROLL) { clearInterval(SCROLL); SCROLL = null; }
  document.body.classList.remove('pl-moviendo');
  limpiaSeleccion();
  limpiaMarcas();
  MOVIENDO = null;
}

function alTeclaAsa(ev) {
  const asa = ev.target.closest('.pl-asa');
  if (!asa) return;
  const id = asa.closest('tr').getAttribute('data-id');
  if (ev.key === 'ArrowUp' && ev.altKey) { ev.preventDefault(); moverUno(id, -1); reenfocar(id); }
  if (ev.key === 'ArrowDown' && ev.altKey) { ev.preventDefault(); moverUno(id, 1); reenfocar(id); }
}

function reenfocar(id) {
  const asa = document.querySelector('tr[data-id="' + id + '"] .pl-asa');
  if (asa) asa.focus();
}

function nuevoEnvio() {
  const ult = ESTADO.envios.length ? ESTADO.envios[ESTADO.envios.length - 1].fecha : ESTADO.periodo[0];
  const p = ult.split('-');
  const d = new Date(+p[0], +p[1] - 1, +p[2]);
  d.setDate(d.getDate() + 2);
  const iso = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-'
    + String(d.getDate()).padStart(2, '0');
  ESTADO.envios.push({ id: nuevoId(), fecha: iso, tema: 'Nuevo tema', url: null,
                       estado: 'idea', propia: true, razon: '', cliente: '' });
  FILTROS.mes = 'todos';
  document.getElementById('f-mes').value = 'todos';
  marcarSucio(true);
  pintar();
  const filas = document.querySelectorAll('#tabla tr');
  const ultima = filas[filas.length - 1];
  if (ultima) {
    ultima.scrollIntoView({ block: 'center', behavior: 'smooth' });
    const ed = ultima.querySelector('[data-campo="tema"]');
    if (ed) ed.focus();
  }
}

function aviso(texto, tipo, accion) {
  const c = document.getElementById('avisos');
  const clase = tipo === 'error' ? 'gdp-alert--error' : tipo === 'ok' ? 'gdp-alert--success'
    : tipo === 'warn' ? 'gdp-alert--warning' : 'gdp-alert--info';
  c.innerHTML = '<div class="gdp-alert ' + clase + '" role="status">'
    + '<div class="gdp-alert-icon"></div><div class="gdp-alert-content">'
    + '<p class="gdp-alert-msg">' + esc(texto)
    + (accion ? ' <button class="btn btn-outline-blue btn-sm" id="btn-accion">'
                + esc(accion.texto) + '</button>' : '')
    + '</p></div></div>';
  if (accion) document.getElementById('btn-accion').onclick = accion.fn;
  c.scrollIntoView({ block: 'nearest' });
}

function desactivar(id, motivo) {
  const b = document.getElementById(id);
  if (!b) return;
  b.classList.add('pl-off');
  b.setAttribute('aria-disabled', 'true');
  b.setAttribute('title', motivo);
  b.setAttribute('data-motivo', motivo);
  b.disabled = false;
}

function apagado(b) {
  if (!b || !b.classList.contains('pl-off')) return false;
  aviso(b.getAttribute('data-motivo'), 'warn');
  return true;
}

function modoLectura() {
  SOLO_LECTURA = true;
  desactivar('btn-guardar', 'Esta vista es de solo lectura: el plan no se puede modificar desde aquí.');
  const p = document.getElementById('pie-guardar');
  if (p) {
    p.innerHTML = '<strong>Esta vista es de solo lectura.</strong> Puedes tocar todo lo que ves '
      + '\u2014 escribir sobre un tema, cambiar fechas, estados y URL, filtrar y buscar \u2014 '
      + 'pero los cambios se quedan en tu pantalla y no modifican el plan.';
  }
  marcarSucio(SUCIO);
  pintar();   // repinta para que las asas de mover queden deshabilitadas de verdad
}

async function guardar() {
  if (apagado(document.getElementById('btn-guardar'))) return;
  if (SOLO_LECTURA) return;
  const api = window.claude && window.claude.use ? await window.claude.use('artifact') : null;
  if (!api) {
    modoLectura();
    aviso('Esta vista no puede guardar. Puedes editar y exportar, pero los cambios no se conservan.', 'warn');
    return;
  }
  const btn = document.getElementById('btn-guardar');
  btn.disabled = true;
  btn.textContent = 'Guardando…';
  ESTADO.rev = (ESTADO.rev || 0) + 1;
  ESTADO.guardado = new Date().toISOString();
  try { sessionStorage.setItem('gdp-plan-borrador', JSON.stringify(ESTADO)); } catch (err) {}
  try {
    await api.publish(documento(ESTADO));
    // La vista se recarga con la versión nueva.
  } catch (err) {
    ESTADO.rev = ESTADO.rev - 1;
    btn.textContent = 'Guardar';
    const c = err && err.code;
    if (c === 'conflict') {
      aviso('Alguien ha guardado antes que tú. La página se está recargando con su versión.', 'warn');
      return;
    }
    if (['not_writer', 'not_granted', 'not_declared', 'consent_required',
         'capability_disabled', 'capability_removed'].indexOf(c) > -1) {
      modoLectura();
      aviso('Esta vista es de solo lectura: puedes editar y exportar, pero no guardar.', 'warn');
      return;
    }
    btn.disabled = false;
    if (c === 'too_large') { aviso('El plan es demasiado grande para guardarlo.', 'error'); return; }
    if (c === 'rate_limited') { aviso('Demasiados guardados seguidos. Espera unos segundos.', 'warn'); return; }
    aviso('No se ha podido guardar. Vuelve a intentarlo.', 'error');
  }
}

function csv() {
  const filas = [['Fecha', 'Hora', 'Dia', 'Tema', 'URL', 'Estado']];
  ESTADO.envios.forEach(function (e) {
    filas.push([e.fecha, '15:00', fechaLarga(e.fecha), e.tema, e.url || '', e.estado]);
  });
  return filas.map(function (f) {
    return f.map(function (c) { return '"' + String(c).replace(/"/g, '""') + '"'; }).join(',');
  }).join('\r\n');
}

function brief() {
  let t = 'BRIEF DE DISEÑO · NEWSLETTERS ' + ESTADO.periodo[0].slice(0, 4) + '\n';
  t += 'García de Pou · Marketing\n';
  t += 'Envíos: martes y jueves a las 15:00 · 4 idiomas (ES, EN, FR, PT)\n';
  t += '='.repeat(78) + '\n\n';
  let mesPrevio = null;
  ESTADO.envios.forEach(function (e) {
    const mes = e.fecha.slice(0, 7);
    if (mes !== mesPrevio) {
      t += '\n' + MESES[+mes.slice(5, 7)].toUpperCase() + ' ' + mes.slice(0, 4) + '\n';
      t += '-'.repeat(78) + '\n';
      mesPrevio = mes;
    }
    const p = e.fecha.split('-');
    t += '\n' + p[2] + '/' + p[1] + '  ' + fechaLarga(e.fecha) + '\n';
    t += '  Tema:   ' + e.tema + '\n';
    t += '  URL:    ' + (e.url || '(pendiente)') + '\n';
    t += '  Estado: ' + e.estado + '\n';
    if (e.razon) t += '  Por qué: ' + e.razon + '\n';
    if (e.cliente) t += '  Cliente: ' + e.cliente + '\n';
  });
  t += '\n\n' + '='.repeat(78) + '\n';
  t += 'Los enlaces son de referencia, para saber qué producto entra en cada envío.\n';
  t += 'Los definitivos por idioma, con marcas de seguimiento, se ponen en Mailchimp.\n';
  return t;
}

async function descargar(nombre, datos, alternativa) {
  const api = window.claude && window.claude.use ? await window.claude.use('downloads') : null;
  if (!api) { aviso('Las descargas no están disponibles en esta vista.', 'warn'); return; }
  try {
    await api.save({ filename: nombre, data: datos });
    aviso('Descargado: ' + nombre, 'ok');
  } catch (err) {
    const c = err && err.code;
    if (c === 'declined') return;
    if (c === 'extension_not_enabled' && alternativa) { return descargar(alternativa, datos, null); }
    if (c === 'rate_limited') { aviso('Ya hay una descarga en curso. Espera un momento.', 'warn'); return; }
    aviso('No se ha podido descargar el fichero.', 'error');
  }
}

function recuperarBorrador() {
  let guardado = null;
  try { guardado = sessionStorage.getItem('gdp-plan-borrador'); } catch (err) { return; }
  if (!guardado) return;
  try { sessionStorage.removeItem('gdp-plan-borrador'); } catch (err) {}
  let prev;
  try { prev = JSON.parse(guardado); } catch (err) { return; }
  if (!prev || !prev.envios) return;
  if (JSON.stringify(prev.envios) === JSON.stringify(ESTADO.envios)) return;
  const c = document.getElementById('avisos');
  c.innerHTML = '<div class="gdp-alert gdp-alert--warning" role="status">'
    + '<div class="gdp-alert-icon"></div><div class="gdp-alert-content">'
    + '<strong class="gdp-alert-title">Hay cambios de un guardado que no llegó a completarse</strong>'
    + '<p class="gdp-alert-msg">Puedes recuperarlos o quedarte con la versión guardada.'
    + ' <button class="btn btn-outline-blue btn-sm" id="btn-recuperar">Recuperar</button>'
    + ' <button class="btn btn-outline-blue btn-sm" id="btn-descartar">Descartar</button></p>'
    + '</div></div>';
  document.getElementById('btn-recuperar').onclick = function () {
    ESTADO.envios = prev.envios;
    c.innerHTML = '';
    marcarSucio(true);
    pintar();
  };
  document.getElementById('btn-descartar').onclick = function () { c.innerHTML = ''; };
}

async function probarCapacidades() {
  const hayApi = !!(window.claude && window.claude.use);
  const art = hayApi ? await window.claude.use('artifact') : null;
  if (!art) modoLectura();
  const dl = hayApi ? await window.claude.use('downloads') : null;
  PUEDE_DESCARGAR = !!dl;
  if (!dl) {
    desactivar('btn-csv', 'Las descargas no están disponibles en la vista compartida. '
      + 'En la versión de trabajo este botón baja el plan completo en CSV.');
    desactivar('btn-brief', 'Las descargas no están disponibles en la vista compartida. '
      + 'En la versión de trabajo este botón genera el brief para el departamento de diseño.');
  }
}

function arrancar() {
  if (!document.getElementById('css-planificador')) {
    const st = document.createElement('style');
    st.id = 'css-planificador';
    st.textContent = CSS;
    document.head.appendChild(st);
  }
  const app = document.getElementById('app');
  app.innerHTML = CUERPO;

  const fm = document.getElementById('f-mes');
  fm.innerHTML = '<option value="todos">Todos los meses</option>'
    + MESES.slice(1).map(function (m, i) {
        return '<option value="' + String(i + 1).padStart(2, '0') + '">' + m + '</option>';
      }).join('');
  document.getElementById('f-estado').innerHTML = '<option value="todos">Todos los estados</option>'
    + ESTADOS.map(function (x) { return '<option value="' + x[0] + '">' + x[1] + '</option>'; }).join('');

  fm.onchange = function () { FILTROS.mes = this.value; pintar(); };
  document.getElementById('f-estado').onchange = function () { FILTROS.estado = this.value; pintar(); };
  document.getElementById('f-texto').oninput = function () { FILTROS.texto = this.value; pintar(); };
  document.getElementById('f-razon').onchange = function () { FILTROS.razon = this.checked; pintar(); };
  document.getElementById('btn-nuevo').onclick = nuevoEnvio;
  document.getElementById('btn-guardar').onclick = guardar;
  document.getElementById('btn-csv').onclick = function () {
    if (apagado(this)) return;
    descargar('newsletters-' + ESTADO.periodo[0].slice(0, 4) + '.csv', csv(),
              'newsletters-' + ESTADO.periodo[0].slice(0, 4) + '.txt');
  };
  document.getElementById('btn-brief').onclick = function () {
    if (apagado(this)) return;
    descargar('brief-diseno-' + ESTADO.periodo[0].slice(0, 4) + '.txt', brief(), null);
  };

  const tabla = document.getElementById('tabla');
  tabla.addEventListener('input', alEditar);
  tabla.addEventListener('change', alEditar);
  tabla.addEventListener('click', alPulsar);
  tabla.addEventListener('pointerdown', alPunteroAbajo);
  tabla.addEventListener('keydown', alTeclaAsa);

  window.addEventListener('beforeunload', function (ev) {
    if (SUCIO && !SOLO_LECTURA) { ev.preventDefault(); ev.returnValue = ''; }
  });

  pintar();
  marcarSucio(false);
  recuperarBorrador();
  probarCapacidades();
}

function codigoFuente(estado) {
  const fuentes = [
    'const CSS = ' + JSON.stringify(CSS) + ';',
    'const CUERPO = ' + JSON.stringify(CUERPO) + ';',
    'let ESTADO = ' + JSON.stringify(estado) + ';',
    'const ESTADOS = ' + JSON.stringify(ESTADOS) + ';',
    'const MESES = ' + JSON.stringify(MESES) + ';',
    'const DIAS = ' + JSON.stringify(DIAS) + ';',
    'let FILTROS = { mes: "todos", estado: "todos", texto: "", razon: true };',
    'let SUCIO = false;',
    'let SOLO_LECTURA = false;',
    'let PUEDE_DESCARGAR = false;',
    'let ANTERIOR = null;',
    'let MOVIENDO = null;',
    'let SCROLL = null;',
    esc.toString(), nuevoId.toString(), fechaLarga.toString(), ordenar.toString(),
    hayFiltro.toString(), instantanea.toString(), deshacer.toString(), indiceDe.toString(),
    reasignarHuecos.toString(), mover.toString(), tras.toString(), moverUno.toString(),
    limpiaSeleccion.toString(), limpiaMarcas.toString(), marcaDestino.toString(),
    autoScroll.toString(), alPunteroAbajo.toString(), alPunteroMueve.toString(), alPunteroArriba.toString(),
    alPunteroFin.toString(), alTeclaAsa.toString(), reenfocar.toString(),
    filtrados.toString(), opcionesEstado.toString(), pintarKpis.toString(),
    pintar.toString(), marcarSucio.toString(), buscaEnvio.toString(), alEditar.toString(),
    alPulsar.toString(), nuevoEnvio.toString(), aviso.toString(), desactivar.toString(),
    apagado.toString(), modoLectura.toString(),
    guardar.toString(), csv.toString(), brief.toString(), descargar.toString(),
    recuperarBorrador.toString(), probarCapacidades.toString(), arrancar.toString(),
    codigoFuente.toString(), documento.toString(),
    'arrancar();',
  ];
  return fuentes.join('\n\n');
}

function documento(estado) {
  const codigo = codigoFuente(estado).replace(/<\/script/gi, '<\\/script');
  return '<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n'
    + '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
    + '<title>Planificador de Newsletters</title>\n'
    + '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    + '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    + '<link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;'
    + '0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;0,9..40,800;0,9..40,900;1,9..40,300&'
    + 'family=Caveat:wght@400;500;600&display=swap" rel="stylesheet">\n'
    + '<style id="css-planificador">' + CSS + '</style>\n</head>\n<body>\n<div id="app"></div>\n'
    + '<scr' + 'ipt>\n' + codigo + '\n</scr' + 'ipt>\n</body>\n</html>';
}

arrancar();
