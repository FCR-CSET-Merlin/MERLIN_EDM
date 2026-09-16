"""Exporta tablas anuales livianas desde la capa regional de resultados.

Las series Parquet se copian separadamente y no se versionan por su tamaño.
"""
import argparse
import csv
import sqlite3
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = Path('/srv/compartido/inbox/datos_modelos_MERLIN_EDM_prot_3/data/rec_2024_2025/results/capas_regionales/wp2_output_demanda_electrica_regional.gpkg')
FIELDS = ['año', 'cod_region', 'region', 'demanda_total_GWh', 'demanda_R_GWh',
          'demanda_C_GWh', 'demanda_P_GWh', 'demanda_I_GWh', 'demanda_T_GWh']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=DEFAULT_SOURCE)
    parser.add_argument('--output', type=Path, default=REPO/'corfo-report/results/tables')
    parser.add_argument('--years', nargs='+', type=int, default=[2024, 2025])
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(args.source)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        'select año, cod_region, region, demanda_total_GWh, demanda_R_GWh, '
        'demanda_C_GWh, demanda_P_GWh, demanda_I_GWh, demanda_T_GWh '
        'from wp2_output_demanda_electrica_regional order by año, cod_region'
    ).fetchall()
    for year in args.years:
        selected = [dict(row) for row in rows if row['año'] == year]
        if len(selected) != 16:
            raise ValueError(f'{year}: se esperaban 16 regiones, se encontraron {len(selected)}')
        with (args.output/f'demanda_regional_sectorial_{year}.csv').open(
                'w', encoding='utf-8-sig', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator='\n')
            writer.writeheader()
            writer.writerows(selected)
        print(f'Exportado: {args.output/f"demanda_regional_sectorial_{year}.csv"}')


if __name__ == '__main__':
    main()
