# Planificador de newsletters — García de Pou

Planifica las newsletters de García de Pou (martes y jueves, 15:00, cuatro idiomas)
a partir del histórico de envíos, en lugar de a mano sobre un Excel.

**Estado: propuesta.** Lo que hay aquí es el importador del Excel histórico, el banco
de temas que sale de él y un primer motor de propuesta de temas por trimestre.
La interfaz del planificador es la fase 1 y todavía no está construida.

Propuesta completa, con el diagnóstico y las fases: [`docs/propuesta.html`](docs/propuesta.html).

## Datos

| Fichero | Qué es |
|---|---|
| `data/origen-Planning_NL_2026.xlsx` | El Excel original, tal cual. Solo como fuente. |
| `data/historico.json` | 292 envíos fechados (2024-05-02 → 2026-12-22), normalizados. |
| `data/temas.json` | Banco de 327 temas únicos con familia, marcas, páginas, URL y uso. |
| `data/plan-2027-Q1.json` | Propuesta generada para el Q1 de 2027. Ejemplo de salida. |

## Scripts

```bash
pip install openpyxl

# Reimportar el Excel -> data/historico.json + data/temas.json
python3 scripts/importar_excel.py data/origen-Planning_NL_2026.xlsx

# Proponer el planning de un trimestre -> data/plan-<año>-Q<n>.json
python3 scripts/proponer_plan.py --desde 2027-01-01 --hasta 2027-03-31
```

### Cómo propone los temas

`proponer_plan.py` genera los huecos de martes y jueves del periodo y asigna un tema
a cada uno, en este orden de prioridad:

1. **Ancla estacional** — qué se envió esa misma semana ISO en años anteriores.
2. **Descanso** — no repite un tema enviado en los últimos 12 meses (`MESES_DESCANSO`).
3. **Ventana estacional** — un tema de Navidad no puede caer en enero, ni uno de
   granizados en diciembre (`VENTANAS_FAMILIA`, `VENTANAS_CLAVE`).
4. **Estrenos** — uno de cada tres huecos se reserva a familias infrarrepresentadas
   (limpieza, habitaciones, utensilios, rotulación) o a temas nunca enviados.
5. **Rotación** — si no hay candidato, el tema disponible más antiguo.

Los festivos se marcan como aviso, no como bloqueo: en el histórico hay envíos el
15 de agosto, el 24 y el 31 de diciembre.

## Pendiente

- Consolidar duplicados del banco (el Excel arrastra el mismo tema con nombres distintos).
- Separar el nombre interno del tema del asunto que ve el cliente.
- Índice de URL del sitio en es/en/fr/pt — hace falta el `sitemap.xml`.
- Interfaz del planificador, vista de aprobación y brief de diseño.
