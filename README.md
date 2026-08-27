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
| `data/calendario-comercial.json` | 111 ocasiones comerciales HORECA: qué compra el hostelero y cuándo. |
| `data/temas-2027.json` / `.csv` | Los 104 temas propuestos para 2027, con fecha y URL. |

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

# Proponer los temas de un periodo -> data/temas-<año>.json (+ .csv con --csv)
python3 scripts/proponer_temas.py --desde 2027-01-01 --hasta 2027-12-31 --csv
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

La fuente de ideas es **`scripts/calendario_comercial.py`**, no el histórico. Son 111
ocasiones comerciales HORECA, cada una con:

- el **tema** tal como iría en la newsletter
- los **meses en los que toca enviar**, ya descontada la antelación de compra
- la **razón comercial**: por qué vende en esa fecha
- el **cliente** al que le vende
- las **claves** para localizar la URL de categoría
- si es **papel y cartón de fabricación propia**

La idea central es la **antelación de compra**: el hostelero cierra la mantelería de
Navidad en octubre, equipa la terraza en marzo y encarga la caja del roscón en
noviembre. El calendario envía en el momento de la compra, no del consumo.

`proponer_temas.py` reparte esas ocasiones sobre los martes y jueves del periodo,
prioriza fabricación propia hasta `CUOTA_PROPIA` (75%), y tira de meses vecinos si un
mes se queda corto de ideas. **No propone envíos extraordinarios**: nada de catálogos,
tarifas, felicitaciones ni encuestas.

El histórico se usa solo para dos cosas:

1. **Sacar la URL** de entre los 225 enlaces que ya se han usado de verdad — nunca se
   inventa una. El sitio cambió de estructura con la migración, así que se prefieren los
   enlaces posteriores a `FECHA_MIGRACION` y los anteriores se marcan para revisar.
2. **Avisar de solapamiento** si un tema muy parecido salió en los últimos 10 meses.

## Pendiente

- **Catálogo de producto** — 6 temas de 2027 no tienen enlace porque son categorías que
  nunca se han enlazado en una newsletter (posavasos, personalizados, Airlaid). El
  catálogo cerraría ese hueco y permitiría bajar de categoría a referencia concreta.
- Ampliar el calendario comercial: febrero y agosto son los meses con menos ocasiones.
- Interfaz del planificador, vista de aprobación y brief de diseño en Gmail.
- Conector de Mailchimp para traer aperturas y clics, y saber qué temas funcionan.
