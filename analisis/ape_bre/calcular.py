"""APE anual regional/sectorial y MAPE espacial; solo bibliotecas estándar."""
import csv
import json
import math
import sqlite3
from collections import defaultdict
from pathlib import Path
from statistics import mean

ROOT = Path('/srv/compartido/inbox/datos_modelos_MERLIN_EDM_prot_3/data')
OUT = Path(__file__).resolve().parent
SECTORS = {'R': 'Residencial', 'C': 'Comercial', 'P': 'Público', 'I': 'Industrial', 'T': 'Transporte'}
aliases = json.loads((ROOT / 'raw/reg_alias.json').read_text())
hist = defaultdict(lambda: defaultdict(float))
with (ROOT / 'raw/wp2_elec_input_sector_shares_raw.csv').open(encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        hist[(row['región'], int(row['año']))][row['sector']] += float(row['valor'])

def reference(region, year):
    if (region, year) in hist:
        return {s: hist[region, year][s] for s in SECTORS.values()}, 'BRE disponible'
    years = sorted(y for r, y in hist if r == region)
    assert years
    result = {}
    for sector in SECTORS.values():
        values = [hist[region, y][sector] for y in years]
        if len(years) == 1:
            prediction = values[0]
        else:
            # Recta de mínimos cuadrados equivalente a np.polyfit(x, y, 1).
            mx, my = mean(years), mean(values)
            slope = sum((x-mx)*(v-my) for x, v in zip(years, values)) / sum((x-mx)**2 for x in years)
            prediction = my + slope * (year-mx)
        result[sector] = max(0.0, prediction)
    return result, 'BRE extrapolado linealmente; no observado'

p = ROOT / 'rec_2024_2025/results/capas_regionales/wp2_output_demanda_electrica_regional.gpkg'
connection = sqlite3.connect(f'file:{p}?mode=ro', uri=True)
connection.row_factory = sqlite3.Row
rows = connection.execute('SELECT * FROM wp2_output_demanda_electrica_regional ORDER BY año, cod_region').fetchall()
assert len(rows) == 32
assert len({(r['año'], r['cod_region']) for r in rows}) == 32
detail = []
for row in rows:
    ref, kind = reference(aliases[row['region']], row['año'])
    for code, sector in [('total', 'Total'), *SECTORS.items()]:
        predicted = row[f'demanda_{code}_GWh']
        target = sum(ref.values()) if code == 'total' else ref[sector]
        assert math.isfinite(predicted) and math.isfinite(target)
        ape = 100 * abs(predicted-target) / abs(target) if target != 0 else None
        detail.append(dict(año=row['año'], cod_region=row['cod_region'], region=row['region'], sector=sector,
                           modelo_GWh=predicted, referencia_GWh=target, tipo_referencia=kind, APE_pct=ape))
summary = []
for year in [2024, 2025]:
    for sector in ['Total', *SECTORS.values()]:
        selected = [d for d in detail if d['año'] == year and d['sector'] == sector]
        assert len(selected) == 16
        valid = [d['APE_pct'] for d in selected if d['APE_pct'] is not None]
        summary.append(dict(año=year, sector=sector, MAPE_pct=mean(valid) if len(valid) == 16 else None,
                            regiones=16, regiones_APE_definido=len(valid), tipo_referencia=selected[0]['tipo_referencia']))
for filename, data in [('ape_region_sector.csv', detail), ('mape_16_regiones.csv', summary)]:
    with (OUT / filename).open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(data[0]))
        writer.writeheader()
        writer.writerows(data)
lines = ['# APE anual y MAPE entre regiones', '',
         'Fuente: GeoPackage regional de resultados 2024–2025 y data/raw/wp2_elec_input_sector_shares_raw.csv.',
         'Unidades: GWh. Cruce mediante data/raw/reg_alias.json.', '',
         '2024: referencia BRE disponible. 2025: extrapolación lineal por región y sector de todos los años disponibles, con valores negativos truncados a cero, reproduciendo capa_regional.ipynb. Los sectores ausentes en años históricos se completan con cero, igual que en el notebook.', '',
         'APE = 100 × |modelo − referencia| / |referencia|. MAPE: media aritmética de los APE de las 16 regiones, sin ponderación energética, por año y sector. Total usa demanda_total_GWh y la suma de los cinco sectores del BRE; no se obtiene promediando los APE sectoriales.', '',
         'Si una referencia es cero, APE queda indefinido y no se publica un MAPE de 16 regiones para ese grupo. No se reemplaza por cero ni se excluye silenciosamente.', '',
         'Estas comparaciones miden consistencia anual con las referencias que el flujo utiliza para escalar las predicciones; no son una validación independiente ni un MAPE horario. Para 2025 no constituyen error contra un BRE observado.', '']
for year in [2024, 2025]:
    lines += [f'## {year}', '', '| Región | Total | Residencial | Comercial | Público | Industrial | Transporte |', '|---|---:|---:|---:|---:|---:|---:|']
    for row in [r for r in rows if r['año'] == year]:
        ds = [d for d in detail if d['año'] == year and d['cod_region'] == row['cod_region']]
        lines.append('| ' + row['region'] + ' | ' + ' | '.join('Indefinido' if d['APE_pct'] is None else f"{d['APE_pct']:.2f}%" for d in ds) + ' |')
    ss = [s for s in summary if s['año'] == year]
    lines += ['| **MAPE 16 regiones** | ' + ' | '.join('Indefinido' if s['MAPE_pct'] is None else f"**{s['MAPE_pct']:.2f}%**" for s in ss) + ' |', '']
(OUT / 'resultados.md').write_text('\n'.join(lines), encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2))
print('Referencias cero:', sum(d['APE_pct'] is None for d in detail))
print('Verificado: 32 pares región/año, 192 APE y 12 grupos MAPE.')
