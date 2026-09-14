"""Reconstrucción regional anual condicionada al BRE, con evidencia reproducible.

No reentrena el modelo ni utiliza las observaciones horarias de demanda.
Los outputs pesados se guardan en data/ (ignorado por Git).
"""
import argparse
import calendar
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

os.environ.setdefault('CUDA_VISIBLE_DEVICES', '-1')
os.environ.setdefault('TF_ENABLE_ONEDNN_OPTS', '0')
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
SECTORS = {'R': 'Residencial', 'C': 'Comercial', 'P': 'Público',
           'I': 'Industrial', 'T': 'Transporte'}
TEMP_COLS = ['temperatura'] + [f'temp_t - {i}' for i in range(1, 8)]
A = float(np.exp(-1.1315))
B = 0.8988
KPI_SOURCE = ('https://github.com/FCR-CSET-Merlin/merlin-index/blob/'
              'a9b855f60c4ad207d7c2544a07e4f43d25356209/'
              '05-roadmap/01-antecedentes/Resultados_Excel_CORFO.md')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def prepare_reference(bre, aliases, year):
    """Exige referencia observada, completa, única y positiva; no imputa ceros."""
    require(len(aliases) == 16 and len(set(aliases.values())) == 16,
            'Se requieren alias únicos para 16 regiones')
    data = bre.loc[bre['año'].eq(year)].copy()
    require(not data.empty, f'BRE {year} ausente: no se extrapola')
    require(not data.duplicated(['región', 'sector']).any(), 'BRE duplicado')
    required = pd.MultiIndex.from_product(
        [sorted(aliases.values()), list(SECTORS.values())], names=['región', 'sector'])
    observed = pd.MultiIndex.from_frame(data[['región', 'sector']])
    require(set(observed) == set(required),
            f'Cobertura BRE inválida; faltantes: {list(required.difference(observed))}')
    require(np.isfinite(data['valor']).all() and data['valor'].gt(0).all(),
            'BRE contiene valores no finitos, negativos o cero; APE no definido')
    wide = data.pivot(index='región', columns='sector', values='valor')
    wide['Total'] = wide[list(SECTORS.values())].sum(axis=1)
    wide['region_comuna_share'] = wide['Total'] / wide['Total'].sum()
    for code, sector in SECTORS.items():
        wide[f'share_{code}'] = wide[sector] / wide['Total']
    return wide


def check_weather(weather, aliases, year):
    expected = pd.date_range(f'{year}-01-01', f'{year+1}-01-01', freq='h', inclusive='left')
    require(set(weather['region']) == set(aliases), 'Clima sin las 16 regiones esperadas')
    require(not weather.duplicated(['region', 'fecha_hora']).any(), 'Clima duplicado')
    require(np.isfinite(weather[TEMP_COLS].to_numpy()).all(), 'Clima/rezagos no finitos')
    for name, group in weather.groupby('region'):
        actual = pd.DatetimeIndex(group['fecha_hora'].sort_values())
        require(actual.equals(expected), f'Cobertura horaria incompleta: {name}')
    return len(expected)


def check_lags(weather, raw):
    require(not raw.duplicated(['region', 'fecha_hora']).any(), 'Clima original duplicado')
    original = raw.set_index(['region', 'fecha_hora'])['temperatura']
    for lag, col in enumerate(TEMP_COLS):
        keys = pd.MultiIndex.from_arrays(
            [weather['region'], weather['fecha_hora'] - pd.Timedelta(hours=lag)])
        expected = original.reindex(keys).to_numpy()
        require(np.isfinite(expected).all(), f'Falta historia climática para {col}')
        require(np.allclose(expected, weather[col].to_numpy(), rtol=0, atol=1e-6),
                f'Rezago no causal o discordante: {col}')


def evaluate(annual, reference, year):
    detail = []
    for row in annual.to_dict('records'):
        for code, sector in [('total', 'Total'), *SECTORS.items()]:
            pred = row[f'demanda_{code}_GWh']
            ref = float(reference.loc[row['region_bne'], sector])
            detail.append(dict(año=year, region=row['region'], region_bne=row['region_bne'],
                               sector=sector, modelo_GWh=pred, BRE_GWh=ref,
                               APE_pct=100 * abs(pred-ref) / abs(ref)))
    detail = pd.DataFrame(detail)
    require(len(detail) == 96 and not detail.duplicated(['region', 'sector']).any(),
            'Evaluación requiere 96 pares únicos')
    summary = detail.groupby('sector', sort=False).agg(
        MAPE_pct=('APE_pct', 'mean'), regiones=('region', 'nunique')).reset_index()
    require(summary['regiones'].eq(16).all(), 'No se permite MAPE con menos de 16 regiones')
    summary.insert(0, 'año', year)
    kpi = summary.loc[summary['sector'].ne('Total')].copy()
    kpi['umbral_pct'] = 35
    kpi['cumple_umbral'] = kpi['MAPE_pct'] < 35
    kpi['compromiso'] = 'HC2-2'
    kpi['pais'] = 'Chile'
    kpi['energia'] = 'Electricidad'
    kpi['alcance'] = 'Consistencia anual BRE; no acredita HC2 global'
    kpi['fuente_meta'] = KPI_SOURCE
    return detail, summary, kpi


def fingerprint(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return dict(path=str(path.resolve()), sha256=h.hexdigest(), bytes=path.stat().st_size)


def save_figures(annual, detail, summary, validation, figures, year):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size': 9})
    fig, ax = plt.subplots(figsize=(9, 5))
    sectors = summary.loc[summary.sector.ne('Total')]
    ax.barh(sectors.sector, sectors.MAPE_pct, color='#187b8c')
    ax.axvline(35, color='#b54136', linestyle='--', label='HC2: MAPE < 35 %')
    for i, value in enumerate(sectors.MAPE_pct):
        ax.text(value + 0.3, i, f'{value:.2f} %', va='center')
    ax.set_xlim(0, max(40, sectors.MAPE_pct.max()*1.25))
    ax.set_xlabel('MAPE entre 16 regiones (%)')
    ax.set_title(f'Chile {year} · Consistencia anual con BRE de entrada')
    ax.legend(); fig.tight_layout()
    fig.savefig(validation/'mape_sectorial.png', dpi=160); plt.close(fig)
    matrix = detail.pivot(index='region', columns='sector', values='APE_pct')
    matrix = matrix[['Total', *SECTORS.values()]]
    fig, ax = plt.subplots(figsize=(13, 8))
    heat = ax.imshow(matrix.to_numpy(), aspect='auto', cmap='YlOrRd')
    ax.set_yticks(range(len(matrix)), matrix.index, fontsize=8)
    ax.set_xticks(range(len(matrix.columns)), matrix.columns)
    for r in range(len(matrix)):
        for c in range(len(matrix.columns)):
            value = matrix.iloc[r, c]
            color = 'white' if value > matrix.max().max()*0.65 else 'black'
            ax.text(c, r, f'{value:.2f}', ha='center', va='center', color=color, fontsize=8)
    fig.colorbar(heat, ax=ax, label='APE (%)')
    ax.set_title(f'APE regional y sectorial · BRE {year}')
    fig.tight_layout(); fig.savefig(validation/'ape_region_sector.png', dpi=160); plt.close(fig)
    ordered = annual.sort_values('demanda_total_GWh')
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.barh(ordered.region, ordered.demanda_total_GWh, color='#187b8c')
    ax.set_xlabel('Demanda total modelada (GWh/año)')
    ax.set_title(f'Reconstrucción regional {year} condicionada al BRE')
    fig.tight_layout(); fig.savefig(figures/f'demanda_regional_{year}.png', dpi=160); plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--year', type=int, default=2023)
    parser.add_argument('--artifact-root', type=Path,
                        default=Path('/srv/compartido/inbox/datos_modelos_MERLIN_EDM_prot_3'))
    parser.add_argument('--report-root', type=Path, default=REPO/'corfo-report')
    parser.add_argument('--timeseries-dir', type=Path)
    parser.add_argument('--overwrite', action='store_true', help='Regenerar salidas de este caso')
    args = parser.parse_args()
    year, root = args.year, args.artifact_root
    validation = args.report_root/'validation'/f'bre_{year}'
    tables, figures = args.report_root/'results/tables', args.report_root/'results/figures'
    hourly_dir = args.timeseries_dir or REPO/'prototipo_3/data/rec_historica'/str(year)
    hourly_path = hourly_dir/f'demanda_regional_{year}_horaria.parquet'
    annual_path = tables/f'demanda_regional_sectorial_{year}.csv'
    require(args.overwrite or not any(p.exists() for p in [validation, hourly_path, annual_path]),
            'Caso existente: utilizar --overwrite para regenerarlo explícitamente')
    paths = dict(model=root/'models/ds_comunal/best_merlin_mlp_global.keras',
                 scaler=root/'models/scaler_temp_global.pkl',
                 columns=root/'data/rec_2024_2025/columns.txt',
                 bre=root/'data/raw/wp2_elec_input_sector_shares_raw.csv',
                 aliases=root/'data/raw/reg_alias.json',
                 climate=root/'data/interim/temperatura_regional_lagged.parquet',
                 raw_climate=root/'data/interim/temperatura_regional_horaria.parquet')
    for path in paths.values():
        require(path.is_file(), f'Falta insumo: {path}')
    aliases = json.loads(paths['aliases'].read_text())
    reference = prepare_reference(pd.read_csv(paths['bre']), aliases, year)
    # Leer solo el período objetivo; los rezagos vienen de la historia continua.
    weather = pd.read_parquet(paths['climate'], filters=[
        ('fecha_hora', '>=', pd.Timestamp(year, 1, 1)),
        ('fecha_hora', '<', pd.Timestamp(year+1, 1, 1))])
    weather = weather.sort_values(['region', 'fecha_hora']).reset_index(drop=True)
    hours = check_weather(weather, aliases, year)
    raw = pd.read_parquet(paths['raw_climate'], filters=[
        ('fecha_hora', '>=', pd.Timestamp(year, 1, 1)-pd.Timedelta(hours=7)),
        ('fecha_hora', '<', pd.Timestamp(year+1, 1, 1))])
    check_lags(weather, raw)
    print(f'QA entradas: {len(weather)} horas-región; BRE 80 pares; rezagos causales verificados.', flush=True)

    import joblib
    import tensorflow as tf
    from forecast_edm.time_features import build_calendar_features
    from forecast_edm.scaling_engine import calculate_scaling_parameters
    from forecast_edm.inference import predict_and_disaggregate
    tf.config.threading.set_inter_op_parallelism_threads(2)
    tf.config.threading.set_intra_op_parallelism_threads(2)
    tf.keras.utils.set_random_seed(2023)
    tf.config.experimental.enable_op_determinism()
    model = tf.keras.models.load_model(paths['model'], compile=False)
    scaler = joblib.load(paths['scaler'])
    features = paths['columns'].read_text().splitlines()
    require(len(features) == len(set(features)) == 24 and model.input_shape[-1] == 24,
            'Contrato del modelo distinto de 24 entradas')
    require(scaler.n_features_in_ == 8, 'Scaler no tiene ocho entradas')
    require(list(scaler.feature_names_in_) == TEMP_COLS, 'Orden climático incompatible')
    blocks = []
    for region, group in weather.groupby('region', sort=True):
        group = build_calendar_features(group, country='CL', subdiv=aliases[region])
        group['region_bne'] = aliases[region]
        blocks.append(group)
    master = pd.concat(blocks, ignore_index=True)
    master[TEMP_COLS] = scaler.transform(master[TEMP_COLS])
    fraction_outside = float(((master[TEMP_COLS] < 0) | (master[TEMP_COLS] > 1)).to_numpy().mean())
    master['año'] = year
    master['is_comuna'] = 0
    for col in ['region_comuna_share', *[f'share_{s}' for s in SECTORS]]:
        master[col] = master['region_bne'].map(reference[col])
    for alias in reference.index:
        row = reference.loc[alias]
        params = calculate_scaling_parameters(
            row['Total']*1000, {s: row[label]*1000 for s, label in SECTORS.items()}, year, A, B)
        for name, value in params.items():
            master.loc[master['region_bne'].eq(alias), name] = value
    require(set(features).issubset(master.columns), 'Faltan features exigidos por el modelo')
    require(np.isfinite(master[features].to_numpy()).all(), 'Entradas de red no finitas')
    require(np.allclose(master[[f'share_{s}' for s in SECTORS]].sum(axis=1), 1), 'Shares no suman 1')
    metadata = master.drop(columns=features).copy()
    prediction = predict_and_disaggregate(model, master[features], metadata,
                                          features, sectores=list(SECTORS))
    cols = ['demanda_total_pred'] + [f'demanda_pred_{s}' for s in SECTORS]
    require(np.isfinite(prediction[cols].to_numpy()).all(), 'Predicciones no finitas')
    require(prediction[cols].ge(0).all().all(), 'Predicciones negativas después de clipping')
    annual = prediction.groupby(['año', 'region', 'region_bne'])[cols].sum().reset_index()
    annual[cols] = annual[cols] / 1000
    annual = annual.rename(columns={'demanda_total_pred': 'demanda_total_GWh',
                                   **{f'demanda_pred_{s}': f'demanda_{s}_GWh' for s in SECTORS}})
    detail, summary, kpi = evaluate(annual, reference, year)
    for directory in [validation, tables, figures, hourly_dir]:
        directory.mkdir(parents=True, exist_ok=True)
    hourly = prediction[['fecha_hora', 'año', 'region', 'region_bne', *cols]].rename(
        columns={'fecha_hora': 'timestamp', 'demanda_total_pred': 'demanda_total_MWh',
                 **{f'demanda_pred_{s}': f'demanda_{s}_MWh' for s in SECTORS}})
    hourly.to_parquet(hourly_path, index=False)
    for data, path in [(annual, annual_path), (detail, validation/'ape_region_sector.csv'),
                       (summary, validation/'mape_sectorial.csv'), (kpi, validation/'kpi_validation.csv')]:
        data.to_csv(path, index=False, encoding='utf-8-sig', lineterminator='\n')
    save_figures(annual, detail, summary, validation, figures, year)
    passed = int(kpi.cumple_umbral.sum())
    total_mape = float(summary.loc[summary.sector.eq('Total'), 'MAPE_pct'].iloc[0])
    lines = [f'# Piloto regional {year} — inferencia y comparación BRE', '',
             f'ID: `CORFO-MERLIN-EDM-CHILE-BRE{year}`. Estado: inferencia ejecutada; consistencia anual reproducible, pendiente de aceptación como validación formal.', '',
             f'16 regiones, {hours} horas por región, {len(hourly):,} filas horarias, 96 APE y seis MAPE. No se reentrenaron los pesos. MAPE del total: **{total_mape:.5f} %**.', '',
             '| Categoría | MAPE (%) | Regiones | Umbral HC2 <35 % |', '|---|---:|---:|---|']
    for row in summary.to_dict('records'):
        status = 'No se cuenta como sector' if row['sector'] == 'Total' else ('Sí' if row['MAPE_pct'] < 35 else 'No')
        lines.append(f"| {row['sector']} | {row['MAPE_pct']:.5f} | 16 | {status} |")
    lines += ['', f'**{passed}/5 sectores ({passed*20} %) bajo el umbral numérico.** Se usa el valor sin redondear y el total no cuenta como sexto sector. [Fuente HC2]('+KPI_SOURCE+').', '',
              '## Método y límites', '',
              'Reconstrucción condicionada al BRE observado del mismo año: shares, mu y sigma utilizan el balance con el que se compara. APE = 100 × |predicción − BRE| / |BRE|; MAPE es la media sin ponderación de los 16 APE. La condición numérica local no acredita HC2 completo, validación independiente, demanda térmica ni Alemania.', '',
              'Se reutilizan modelo global, scaler y orden de 24 entradas. Calendario CL con subdivisión regional sobre timestamps sin zona explícita; no se cambia la convención temporal. Los siete rezagos físicos se contrastan contra las horas previas reales, incluido diciembre del año anterior. A diferencia del inicio circular de np.roll del notebook 2024–2025, el piloto no conecta el final del año con enero.', '',
              f'Escalamiento: mu = energía BRE en MWh / {hours}; sigma = exp(-1.1315) × mu^0.8988, también para escenarios sin sector. Se conserva la resta de escenarios y clipping de inference.py. No se impone cierre sectorial ni anual a posteriori. Fracción de entradas climáticas escaladas fuera de [0,1]: {fraction_outside:.6%}; no se recortan ni se reajusta el scaler.', '',
              'Los metadatos globales inspeccionados corresponden a entrenamiento 2018–2019, validación 2020 y prueba 2021. No certifican la historia completa de los pesos. Esta ejecución registra sus hashes y el código actual; el commit del entrenamiento original sigue sin establecerse.', '',
              '## Resultados por región', '',
              '| Región | Total | Residencial | Comercial | Público | Industrial | Transporte |',
              '|---|---:|---:|---:|---:|---:|---:|']
    pivot = detail.pivot(index='region', columns='sector', values='APE_pct')
    for region, row in pivot.iterrows():
        lines.append('| '+region+' | '+' | '.join(f'{row[s]:.2f} %' for s in ['Total', *SECTORS.values()])+' |')
    lines += ['', '![MAPE sectorial](mape_sectorial.png)', '', '![APE regional y sectorial](ape_region_sector.png)', '',
              '## Reproducción y archivos', '',
              'Desde la raíz, en el entorno merlin_edm:', '', '```bash',
              f'python prototipo_3/src/reconstruct_regional.py --year {year}', '```', '',
              'Para repetir un caso ya existente añadir `--overwrite`. Raíces configurables mediante `--artifact-root`, `--report-root` y `--timeseries-dir`. Se requiere acceso a los artefactos externos. Las versiones, hashes y verificaciones están en el manifiesto.', '',
              '- [APE y valores de referencia](ape_region_sector.csv).',
              '- [MAPE por categoría](mape_sectorial.csv).', '- [KPI por sector](kpi_validation.csv).',
              f'- [Totales simulados en GWh](../../results/tables/demanda_regional_sectorial_{year}.csv).',
              f'- [Figura de demanda simulada](../../results/figures/demanda_regional_{year}.png).',
              '- [Manifiesto de ejecución](manifiesto.json).',
              f'- Serie horaria pesada: `{hourly_path}` (fuera del control de Git).', '']
    (validation/'README.md').write_text('\n'.join(lines), encoding='utf-8')
    package_names = ['tensorflow', 'keras', 'numpy', 'pandas', 'pyarrow', 'scikit-learn',
                     'joblib', 'holidays', 'matplotlib']
    versions = {p: importlib.metadata.version(p) for p in package_names}
    scripts = [Path(__file__), *[Path(__file__).parent/'forecast_edm'/name
               for name in ['inference.py', 'scaling_engine.py', 'time_features.py']]]
    outputs = [*validation.glob('*.csv'), *validation.glob('*.png'), validation/'README.md',
               annual_path, figures/f'demanda_regional_{year}.png', hourly_path]
    manifest = dict(id=f'CORFO-MERLIN-EDM-CHILE-BRE{year}', year=year,
                    generated_utc=datetime.now(timezone.utc).isoformat(),
                    commit_base=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip(),
                    branch=subprocess.check_output(['git', 'branch', '--show-current'], cwd=REPO, text=True).strip(),
                    note='Hashes de scripts identifican el código ejecutado; no se infiere el commit del entrenamiento.',
                    python=sys.version, executable=sys.executable, versions=versions,
                    args={k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
                    features=features, A=A, B=B, hours_per_region=hours, hourly_rows=len(hourly),
                    regions=16, sectors=5, input_climate_fraction_outside_0_1=fraction_outside,
                    deterministic_ops=True, cpu_threads=2, random_seed=2023,
                    inputs={k: fingerprint(p) for k, p in paths.items()},
                    scripts=[fingerprint(p) for p in scripts], outputs=[fingerprint(p) for p in outputs],
                    checks=['BRE: 80 referencias únicas positivas', 'Clima: 16 años-región completos',
                            'Rezagos t-1 a t-7 coinciden con historia física', '24 features; scaler de 8 variables',
                            'Shares suman uno', 'Predicciones finitas y no negativas',
                            '96 APE; MAPE de 16 regiones; KPI estricto sin Total'])
    (validation/'manifiesto.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    print(summary.to_string(index=False))
    print(f'KPI local {passed}/5. Informe: {validation / "README.md"}')


if __name__ == '__main__':
    main()
