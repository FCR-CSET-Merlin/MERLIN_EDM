"""Controles de cobertura, causalidad y definición de métricas del piloto."""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'prototipo_3/src'))
from reconstruct_regional import SECTORS, TEMP_COLS, check_lags, check_weather, evaluate, prepare_reference


class RegionalPilotTests(unittest.TestCase):
    def setUp(self):
        self.aliases = {f'Region {i}': f'R{i}' for i in range(16)}
        self.bre = pd.DataFrame([
            {'año': 2023, 'región': alias, 'sector': sector, 'valor': 100.0}
            for alias in self.aliases.values() for sector in SECTORS.values()])

    def test_bre_missing_duplicate_and_zero_are_rejected(self):
        zero = self.bre.copy(); zero.loc[0, 'valor'] = 0
        for invalid in [self.bre.iloc[1:], pd.concat([self.bre, self.bre.iloc[:1]]), zero]:
            with self.subTest(rows=len(invalid)), self.assertRaises(ValueError):
                prepare_reference(invalid, self.aliases, 2023)
        with self.assertRaises(ValueError):
            prepare_reference(self.bre, self.aliases, 2022)

    def test_metrics_are_mean_of_regional_apes_and_strict_threshold(self):
        # Solo una región tiene error residencial de 160%; MAPE = 10%,
        # independientemente de que su tamaño energético sea mayor.
        self.bre.loc[self.bre['región'].eq('R0'), 'valor'] = 1000
        ref = prepare_reference(self.bre, self.aliases, 2023)
        rows = []
        for region, alias in self.aliases.items():
            row = dict(region=region, region_bne=alias, demanda_total_GWh=ref.loc[alias, 'Total'])
            for code, sector in SECTORS.items():
                row[f'demanda_{code}_GWh'] = ref.loc[alias, sector]
            row['demanda_T_GWh'] *= 1.35  # Exactamente 35% NO cumple.
            if alias == 'R0':
                row['demanda_R_GWh'] *= 2.6
            rows.append(row)
        detail, summary, kpi = evaluate(pd.DataFrame(rows), ref, 2023)
        self.assertEqual(len(detail), 96)
        self.assertAlmostEqual(summary.set_index('sector').loc['Residencial','MAPE_pct'], 10)
        self.assertFalse(kpi.set_index('sector').loc['Transporte','cumple_umbral'])
        self.assertEqual(len(kpi), 5)
        self.assertNotIn('Total', set(kpi.sector))

    def test_causal_lags_use_previous_year(self):
        times = pd.date_range('2022-12-31 17:00', periods=9, freq='h')
        raw = pd.DataFrame({'fecha_hora': times, 'region':'X', 'temperatura': np.arange(9.)})
        weather = raw.iloc[7:].copy()
        for lag, col in enumerate(TEMP_COLS):
            weather[col] = np.arange(7.,9.) - lag
        check_lags(weather, raw)
        weather.iloc[0, weather.columns.get_loc('temp_t - 1')] = 8  # Circular, incorrecto.
        with self.assertRaises(ValueError):
            check_lags(weather, raw)

    def test_hourly_coverage_rejects_gap_duplicate_and_missing_region(self):
        frame = pd.DataFrame([(region,t) for region in self.aliases
                              for t in pd.date_range('2023-01-01','2023-12-31 23:00',freq='h')],
                             columns=['region','fecha_hora'])
        frame[TEMP_COLS] = 15.0
        self.assertEqual(check_weather(frame, self.aliases, 2023), 8760)
        for invalid in [frame.iloc[1:], pd.concat([frame,frame.iloc[:1]]),
                        frame.loc[frame.region.ne('Region 0')]]:
            with self.subTest(rows=len(invalid)), self.assertRaises(ValueError):
                check_weather(invalid, self.aliases, 2023)


if __name__ == '__main__':
    unittest.main()
