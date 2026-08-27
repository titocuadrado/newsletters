# Planificador de newsletters — García de Pou

Planifica las newsletters de García de Pou (martes y jueves, 15:00, cuatro idiomas)
a partir del histórico de envíos, en lugar de a mano sobre un Excel.

**Estado: propuesta.** Lo que hay aquí es el importador de los Excel históricos, el
banco de temas que sale de ellos y el motor de propuesta de temas por trimestre.
La interfaz del planificador es la fase 1 y todavía no está construida.

Propuesta completa, con el diagnóstico y las fases: [`docs/propuesta.html`](docs/propuesta.html).

## Datos

| Fichero | Qué es |
|---|---|
| `data/origen-*.xlsx` | Los cuatro Excel originales, tal cual. Solo como fuente. |
| `data/historico.json` | 499 envíos fechados (2022-02-03 → 2026-12-22), normalizados. |
| `data/temas.json` | Banco de 720 temas únicos con familia, origen de fabricación, marcas, páginas, enlaces y uso. |
| `data/plan-2027-Q1.json` | Propuesta generada para el Q1 de 2027. Ejemplo de salida. |

Los cuatro ficheros de origen vienen en dos formatos distintos:

- **Formato rico** (`Planning_Newsletters_V18`, 2022–2024) — `DIA | TEMA | PRODUCTOS |
  BLOG | ENLACES (hasta 5) | DISCLAIMERS`. El TEMA es un gancho editorial separado del
  producto, y los DISCLAIMERS son avisos de feria por mercado.
- **Formato simple** (`Planning_NL_*`, 2024–2026) — `fecha | tema | alternativa | estado`,
  con el asunto, las páginas de catálogo y las notas internas dentro de la misma celda.

El importador lee los dos y fusiona. Cuando dos ficheros planifican la misma fecha con
temas distintos (109 casos), gana el fichero más nuevo y el anterior queda marcado como
`revision_previa`, sin contar como envío.

## Scripts

```bash
pip install openpyxl

# Reimportar. Los ficheros se pasan de MAS ANTIGUO a MAS NUEVO.
PYTHONPATH=scripts python3 scripts/importar_excel.py \
  data/origen-Planning_Newsletters_V18.xlsx \
  data/origen-Planning_NL_primaveraestiu.xlsx \
  data/origen-Planning_NL_2025.xlsx \
  data/origen-Planning_NL_2026.xlsx

# Proponer el planning de un trimestre -> data/plan-<año>-Q<n>.json
python3 scripts/proponer_plan.py --desde 2027-01-01 --hasta 2027-03-31
```

### La regla de negocio que manda

En las newsletters se prioriza el producto de **un solo uso de papel y cartón**, porque es
de fabricación propia (Ordis). El resto del catálogo es distribución y solo entra si el
producto es atractivo, novedoso o de una calidad que merezca destacarse.

`scripts/clasificar.py` clasifica cada tema en `propia`, `distribucion`, `institucional`
o `por-confirmar`. La frontera pendiente de decidir son los **envases de cartón** (cajas
THEPACK, barquillas, bandejas, tarrinas, ensaladeras, cucuruchos) y los **vasos de
cartón**: 114 envíos y 292 temas dependen de esa respuesta.

### Cómo propone los temas

`proponer_plan.py` genera los huecos de martes y jueves del periodo y asigna un tema
a cada uno, en este orden:

1. **Fijo institucional** — lanzamiento de catálogo o tarifa en su fecha habitual (`FIJOS`).
2. **Cuota de fabricación propia** — si el plan va por debajo de `CUOTA_PROPIA` (65%),
   fuerza un tema de papel y cartón propio.
3. **Ancla estacional** — qué se envió esa misma semana ISO en años anteriores.
4. **Estreno** — tema del banco que nunca ha salido, priorizando fabricación propia.
5. **Rotación** — si no hay candidato, el tema disponible más antiguo.

Filtros que se aplican siempre:

- **Descanso** — no repite un tema enviado en los últimos 12 meses (`MESES_DESCANSO`).
- **Ventana estacional** — un tema de Navidad no puede caer en enero, ni uno de
  granizados en diciembre (`VENTANAS_FAMILIA`, `VENTANAS_CLAVE`).
- **Destacable** — un tema de distribución solo se propone si es novedad, nunca ha
  salido, o está marcado a mano como destacable.

Los festivos se marcan como aviso, no como bloqueo: en el histórico hay envíos el
15 de agosto, el 24 y el 31 de diciembre.

## Pendiente

- **Respuesta sobre los envases y vasos de cartón** — bloquea la clasificación.
- Depurar el banco: fundir duplicados, separar el tema editorial del nombre interno y
  sacar de producto lo que no lo es (`Presentació Suite Majoristes` y similares).
- Recuperar los cuatro campos del formato rico: productos, blog, varios enlaces y
  disclaimer por mercado.
- Recuperar la numeración de campaña, que se quedó en el 807.
- Interfaz del planificador, vista de aprobación y brief de diseño en Gmail.
- Conector de Mailchimp para traer aperturas y clics al banco.
