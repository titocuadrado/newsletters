/* ── Motor de planificación automática ────────────────────────────────────
   Mismo criterio que scripts/proponer_temas.py, portado al navegador para que
   el botón "Planificar trimestre" no dependa de ningún servidor.

   Las ideas salen del calendario comercial (DATOS.ocasiones), no del histórico:
   qué compra el hostelero en cada momento del año, con la fecha ya adelantada
   al momento de la compra. Las URL salen de DATOS.urls, que son enlaces que ya
   se han usado de verdad en newsletters anteriores: nunca se inventa una.
   ──────────────────────────────────────────────────────────────────────── */

const CUOTA_PROPIA = 0.75;
const FECHA_MIGRACION = '2025-10-01';   // el sitio cambió de estructura de URL
const SEGMENTOS_RAROS = ['kerstmis', 'tafel-en-accessoires', 'bar-en-buffet', 'voorgerechten',
                         'disposable-products', 'wegwerpartikelen'];
const PARAMS_FILTRO = ['gpou_', 'product_list_dir', 'q='];

function dosDigitos(n) {
  return (n < 10 ? '0' : '') + n;
}

function aIso(d) {
  return d.getFullYear() + '-' + dosDigitos(d.getMonth() + 1) + '-' + dosDigitos(d.getDate());
}

function deIso(iso) {
  const p = iso.split('-');
  return new Date(+p[0], +p[1] - 1, +p[2]);
}

function huecosEntre(desde, hasta) {
  // Martes y jueves, que es la cadencia fija de envío
  const out = [];
  const d = deIso(desde);
  const fin = deIso(hasta);
  while (d <= fin) {
    const dia = d.getDay();          // 0 domingo … 2 martes … 4 jueves
    if (dia === 2 || dia === 4) out.push(aIso(d));
    d.setDate(d.getDate() + 1);
  }
  return out;
}

function costeUrl(u, clave) {
  const ruta = u.split('?')[0];
  const ultimo = ruta.split('/').pop().replace(/\.html$/, '');
  return [
    ultimo === clave ? 0 : 1,                                        // la clave ES la categoría
    SEGMENTOS_RAROS.some(function (s) { return u.indexOf(s) > -1; }) ? 1 : 0,
    PARAMS_FILTRO.some(function (p) { return u.indexOf(p) > -1; }) ? 1 : 0,
    (ruta.match(/\//g) || []).length,                                // categoría antes que subcategoría
    u.length,
  ];
}

function comparaCoste(a, b) {
  for (let i = 0; i < a.length; i++) {
    if (a[i] !== b[i]) return a[i] - b[i];
  }
  return 0;
}

function eligeUrl(claves) {
  // Devuelve {url, calidad} o {url: null}. Nunca inventa una URL.
  for (let i = 0; i < claves.length; i++) {
    const clave = claves[i];
    const cands = DATOS.urls.filter(function (x) { return x.u.indexOf(clave) > -1; });
    if (!cands.length) continue;
    const recientes = cands.filter(function (x) { return x.v >= FECHA_MIGRACION; });
    const pool = recientes.length ? recientes : cands;
    const antigua = recientes.length === 0;
    pool.sort(function (a, b) {
      return comparaCoste(costeUrl(a.u, clave), costeUrl(b.u, clave));
    });
    let mejor = pool[0].u;
    if (PARAMS_FILTRO.some(function (p) { return mejor.indexOf(p) > -1; })) {
      mejor = mejor.split('?')[0];
    }
    const ruta = mejor.split('?')[0];
    const exacta = ruta.split('/').pop().replace(/\.html$/, '') === clave;
    return { url: mejor, calidad: antigua ? 'antigua' : (exacta ? 'exacta' : 'proxima') };
  }
  return { url: null, calidad: null };
}

function planificar(desde, hasta) {
  const fechas = huecosEntre(desde, hasta);
  const porMes = {};
  DATOS.ocasiones.forEach(function (o, i) {
    o.meses.forEach(function (m) {
      if (!porMes[m]) porMes[m] = [];
      porMes[m].push(i);
    });
  });

  const usados = {};
  const plan = [];

  function cuotaPropia() {
    if (!plan.length) return 1;
    let n = 0;
    plan.forEach(function (p) { if (p.propia) n++; });
    return n / plan.length;
  }

  function candidatos(mes) {
    const libres = (porMes[mes] || []).filter(function (i) { return !usados[i]; });
    // Fabricación propia primero: es la regla de negocio que manda
    libres.sort(function (a, b) {
      const pa = DATOS.ocasiones[a].propia ? 0 : 1;
      const pb = DATOS.ocasiones[b].propia ? 0 : 1;
      return pa !== pb ? pa - pb : a - b;
    });
    return libres;
  }

  fechas.forEach(function (f) {
    const mes = +f.slice(5, 7);
    let cands = candidatos(mes);
    if (!cands.length) {
      // Si el mes se queda sin ideas, se tira de los meses vecinos
      const vecinos = [mes === 1 ? 12 : mes - 1, mes === 12 ? 1 : mes + 1];
      for (let v = 0; v < vecinos.length && !cands.length; v++) {
        cands = candidatos(vecinos[v]);
      }
    }
    if (!cands.length) {
      plan.push({ fecha: f, tema: '(sin propuesta — amplíe el calendario comercial)',
                  url: null, propia: false, razon: '', cliente: '' });
      return;
    }
    if (cuotaPropia() < CUOTA_PROPIA) {
      const propias = cands.filter(function (i) { return DATOS.ocasiones[i].propia; });
      if (propias.length) cands = propias;
    }
    const idx = cands[0];
    usados[idx] = true;
    const o = DATOS.ocasiones[idx];
    const u = eligeUrl(o.claves);
    plan.push({ fecha: f, tema: o.tema, url: u.url, url_calidad: u.calidad,
                propia: o.propia, razon: o.razon, cliente: o.cliente });
  });

  return plan;
}

function trimestreDe(anyo, q) {
  const m0 = (q - 1) * 3 + 1;
  const m1 = m0 + 2;
  const ultimo = new Date(anyo, m1, 0).getDate();
  return [anyo + '-' + dosDigitos(m0) + '-01', anyo + '-' + dosDigitos(m1) + '-' + ultimo];
}

function proximoTrimestre() {
  // El siguiente al último envío que ya hay en el plan, o al de hoy si está vacío
  let ref = new Date();
  if (ESTADO.envios.length) {
    const ult = deIso(ESTADO.envios[ESTADO.envios.length - 1].fecha);
    if (ult > ref) ref = ult;
  }
  let q = Math.floor(ref.getMonth() / 3) + 2;
  let anyo = ref.getFullYear();
  if (q > 4) { q = 1; anyo = anyo + 1; }
  return { anyo: anyo, q: q };
}

function parecidoEnPlan(tema, fuera) {
  // Avisa si el tema propuesto se parece a otro que ya está en el plan
  const STOP = ('de la el los las para con en un una del al y o e su sus que se lo por mas '
                + 'todo toda todos todas').split(' ');
  function palabras(t) {
    const s = t.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
    const out = {};
    (s.match(/[a-z]{4,}/g) || []).forEach(function (w) {
      if (STOP.indexOf(w) === -1) out[w] = true;
    });
    return Object.keys(out);
  }
  const pa = palabras(tema);
  if (!pa.length) return null;
  for (let i = 0; i < ESTADO.envios.length; i++) {
    const e = ESTADO.envios[i];
    if (e.fecha >= fuera[0] && e.fecha <= fuera[1]) continue;
    const pb = palabras(e.tema);
    if (!pb.length) continue;
    let comunes = 0;
    pa.forEach(function (w) { if (pb.indexOf(w) > -1) comunes++; });
    if (comunes / Math.min(pa.length, pb.length) >= 0.6) return e;
  }
  return null;
}

function abrePlanificador() {
  const caja = document.getElementById('planificar');
  if (caja.hasAttribute('hidden')) {
    const p = proximoTrimestre();
    document.getElementById('p-anyo').value = String(p.anyo);
    document.getElementById('p-trim').value = String(p.q);
    caja.removeAttribute('hidden');
    document.getElementById('p-trim').focus();
    pintaResumenPrevio();
  } else {
    caja.setAttribute('hidden', '');
  }
}

function pintaResumenPrevio() {
  const anyo = +document.getElementById('p-anyo').value;
  const q = +document.getElementById('p-trim').value;
  const r = trimestreDe(anyo, q);
  const huecos = huecosEntre(r[0], r[1]).length;
  const ocupados = ESTADO.envios.filter(function (e) {
    return e.fecha >= r[0] && e.fecha <= r[1];
  }).length;
  document.getElementById('p-previo').textContent =
    huecos + ' martes y jueves entre el 1 de ' + MESES[+r[0].slice(5, 7)].toLowerCase()
    + ' y el ' + (+r[1].slice(8, 10)) + ' de ' + MESES[+r[1].slice(5, 7)].toLowerCase()
    + (ocupados ? '. Ya hay ' + ocupados + (ocupados === 1 ? ' envío' : ' envíos')
                  + ' en esas fechas, que se sustituirán.' : '. No hay nada planificado ahí.');
}

function planificarTrimestre() {
  if (SOLO_LECTURA) return;
  const anyo = +document.getElementById('p-anyo').value;
  const q = +document.getElementById('p-trim').value;
  const r = trimestreDe(anyo, q);
  const previos = ESTADO.envios.filter(function (e) {
    return e.fecha >= r[0] && e.fecha <= r[1];
  });
  if (previos.length && !confirm('Se van a sustituir ' + previos.length
      + ' envíos ya planificados entre el ' + r[0] + ' y el ' + r[1] + '. ¿Seguir?')) return;

  instantanea();
  const nuevos = planificar(r[0], r[1]);
  let repetidos = 0;
  const resto = ESTADO.envios.filter(function (e) {
    return e.fecha < r[0] || e.fecha > r[1];
  });
  const anyadidos = nuevos.map(function (n, i) {
    const rep = parecidoEnPlan(n.tema, r);
    if (rep) repetidos++;
    return {
      id: 'p' + anyo + q + dosDigitos(i + 1) + Math.random().toString(36).slice(2, 5),
      fecha: n.fecha, tema: n.tema, url: n.url, estado: 'propuesta',
      propia: n.propia, razon: n.razon, cliente: n.cliente,
      aviso: rep ? 'se parece a «' + rep.tema.slice(0, 50) + '» del ' + rep.fecha : null,
    };
  });
  ESTADO.envios = resto.concat(anyadidos);

  document.getElementById('planificar').setAttribute('hidden', '');
  FILTROS.mes = 'todos';
  FILTROS.estado = 'todos';
  FILTROS.texto = '';
  document.getElementById('f-mes').value = 'todos';
  document.getElementById('f-estado').value = 'todos';
  document.getElementById('f-texto').value = '';
  marcarSucio(true);
  pintar();

  const conUrl = anyadidos.filter(function (e) { return e.url; }).length;
  const propias = anyadidos.filter(function (e) { return e.propia; }).length;
  aviso('Q' + q + ' de ' + anyo + ' planificado: ' + anyadidos.length + ' envíos, '
        + conUrl + ' con URL y ' + Math.round(propias / anyadidos.length * 100)
        + '% de papel y cartón propio.'
        + (repetidos ? ' ' + repetidos + (repetidos === 1 ? ' tema se parece' : ' temas se parecen')
                       + ' a otros del plan: están marcados.' : ''),
        'ok', { texto: 'Deshacer', fn: deshacer });

  const primera = document.querySelector('tr[data-id="' + anyadidos[0].id + '"]');
  if (primera) primera.scrollIntoView({ block: 'center', behavior: 'smooth' });
}
