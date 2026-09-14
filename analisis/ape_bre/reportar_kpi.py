"""Regenera evidencia numérica HC2 para electricidad Chile 2024 (sin dependencias)."""
import csv
import hashlib
import json
import math
import runpy
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

BASE = Path(__file__).resolve().parents[2]
REPORT = BASE / 'corfo-report'
PACKAGE = 'CORFO-MERLIN-EDM-CHILE-BRE2024'
STANDARD_COMMIT = 'a9b855f60c4ad207d7c2544a07e4f43d25356209'
SOURCE = f'https://github.com/FCR-CSET-Merlin/merlin-index/blob/{STANDARD_COMMIT}/05-roadmap/01-antecedentes/Resultados_Excel_CORFO.md'
state = runpy.run_path(str(Path(__file__).with_name('calcular.py')))
detail = [r for r in state['detail'] if r['año'] == 2024]
summary = [r for r in state['summary'] if r['año'] == 2024 and r['sector'] != 'Total']
assert len(detail) == 96 and len(summary) == 5
assert len({(r['cod_region'], r['sector']) for r in detail}) == 96
kpis = []
for row in summary:
    values = [r for r in detail if r['sector'] == row['sector']]
    assert len(values) == 16 and len({r['cod_region'] for r in values}) == 16
    for r in values:
        assert r['referencia_GWh'] > 0
        assert math.isclose(r['APE_pct'], 100 * abs(r['modelo_GWh'] - r['referencia_GWh']) / r['referencia_GWh'], abs_tol=1e-10)
    assert math.isclose(row['MAPE_pct'], mean(r['APE_pct'] for r in values), abs_tol=1e-10)
    kpis.append(dict(id_evidencia=PACKAGE, compromiso='HC2', indicador='2 - precisión',
                     pais='Chile', energia='Electricidad', año=2024, sector=row['sector'],
                     regiones=16, MAPE_pct=row['MAPE_pct'], umbral_pct=35,
                     criterio='MAPE < 35%', cumple_umbral=row['MAPE_pct'] < 35,
                     alcance='Consistencia anual regional; no acredita HC2 global',
                     evidencia='ape_bre/ape_region_sector_bre_2024.csv', fuente_meta=SOURCE))
passed = sum(r['cumple_umbral'] for r in kpis)
def write_csv(path, rows):
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n"); w.writeheader(); w.writerows(rows)
write_csv(REPORT / 'validation/kpi_validation.csv', kpis)
write_csv(REPORT / 'results/tables/kpi_summary.csv', [dict(
    id_evidencia=PACKAGE, compromiso='HC2', indicador='2 - precisión', pais='Chile', energia='Electricidad',
    año=2024, sectores_evaluados=5, sectores_bajo_umbral=passed, porcentaje=100*passed/5,
    mayoria_numerica=passed > 5/2, cumplimiento_global='No acreditado por este paquete',
    evidencia='../../validation/kpi_validation.csv')])
lines = ['# Evidencia numérica del umbral HC2 — Chile, electricidad 2024', '',
         f'ID de evidencia: `{PACKAGE}`. Fuente del compromiso: [HC2, indicador 2]({SOURCE}).', '',
         'Meta: MAPE estrictamente inferior a 35 % en la mayoría de los sectores. Se interpreta mayoría como más de la mitad de los cinco sectores; el total agregado no es un sexto sector.', '',
         '| Sector | MAPE entre 16 regiones | MAPE < 35 % |', '|---|---:|---|']
for r in kpis:
    lines.append(f"| {r['sector']} | {r['MAPE_pct']:.5f} % | {'Sí' if r['cumple_umbral'] else 'No'} |")
lines += ['', f'**Resultado: {passed}/5 sectores ({100*passed/5:.0f} %) cumplen el umbral numérico en este caso.** La decisión usa valores sin redondear.', '',
          'Estado: evidencia reproducible de consistencia anual, pendiente de aceptación como validación del KPI. El BRE 2024 interviene en el escalamiento del modelo; por tanto no es un comparador independiente. La meta no especifica que este MAPE espacial anual sea la agregación formal aceptada. La aceptación de la métrica, su frontera y su uso como evidencia de precisión requiere revisión del proyecto.', '',
          'No se acredita HC2 completo: este paquete no demuestra demanda térmica, ejecución en Alemania ni cobertura validada de todos los modelos país–sector. Tampoco acredita R1–R7, HC1 o HC3. El diagnóstico para Alemania es factibilidad, no ejecución validada. 2025 se excluye del KPI porque su referencia es extrapolada.', '',
          'Transporte no cumple el umbral en 2024. Los casos Atacama y Coquimbo se conservan íntegros; no se descartan ni se sustituye el indicador por otra métrica para obtener cumplimiento.', '',
          '- [Datos KPI por sector](kpi_validation.csv).',
          '- [APE y referencias por región](ape_bre/ape_region_sector_bre_2024.csv).',
          '- [Ficha de evidencia y brechas](ficha_evidencia_edm_2024.md).', '']
(REPORT / 'validation/cumplimiento_kpi.md').write_text('\n'.join(lines), encoding='utf-8')
def digest(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''): h.update(block)
    return h.hexdigest()
inputs = [state['ROOT'] / 'raw/wp2_elec_input_sector_shares_raw.csv',
          state['ROOT'] / 'raw/reg_alias.json',
          state['ROOT'] / 'rec_2024_2025/results/capas_regionales/wp2_output_demanda_electrica_regional.gpkg']
outputs = list((REPORT/'validation/ape_bre').glob('*.csv')) + [REPORT/'validation/kpi_validation.csv', REPORT/'results/tables/kpi_summary.csv']
scripts = [Path(__file__).resolve(), Path(__file__).with_name('calcular.py').resolve()]
manifest = dict(id_evidencia=PACKAGE, generado_utc=datetime.now(timezone.utc).isoformat(),
                commit_base=subprocess.check_output(['git','rev-parse','HEAD'],cwd=BASE,text=True).strip(),
                nota_version='Commit base del cálculo; los hashes identifican los scripts ejecutados. No es el commit del entrenamiento ni de la inferencia originales.',
                fuente_compromiso=SOURCE, comando='python analisis/ape_bre/reportar_kpi.py',
                inputs=[dict(path=str(p), sha256=digest(p), bytes=p.stat().st_size) for p in inputs],
                scripts=[dict(path=str(p.relative_to(BASE)), sha256=digest(p)) for p in scripts],
                outputs=[dict(path=str(p.relative_to(BASE)), sha256=digest(p)) for p in outputs],
                verificaciones=['96 pares región-categoría únicos en 2024', '16 regiones por sector',
                                'Referencias positivas', 'APE recalculados', 'MAPE media sin ponderación',
                                'Umbral estricto sin redondeo; total excluido del conteo'])
(REPORT/'validation/manifiesto_edm_2024.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
print(f'HC2 local: {passed}/5 sectores bajo 35%; HC2 global no acreditado.')
