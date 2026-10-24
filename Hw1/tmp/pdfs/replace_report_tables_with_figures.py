from pathlib import Path
import hashlib
import json
import re
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / 'HW1_results_113062273'
REPORT = ROOT / 'HW1_final_report_minimal_113062273.md'
AUDIT = ROOT / 'tmp/pdfs/chart_revision'
AUDIT.mkdir(parents=True, exist_ok=True)

protected = [ROOT / 'tracks.csv', ROOT / 'HW1_pre_report_113062273.pdf',
             ROOT / 'HW1_ai_use_113062273.md', ROOT / 'HW1_code_113062273.ipynb']
protected += list(RESULTS.glob('*.csv'))
before = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
          for p in protected}
(AUDIT / 'unchanged_numeric_inputs.json').write_text(json.dumps(before, indent=2), encoding='utf-8')
original = REPORT.read_text(encoding='utf-8')
if not (AUDIT / 'report_before.md').exists():
    (AUDIT / 'report_before.md').write_text(original, encoding='utf-8')

plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 9,
    'axes.titlesize': 10, 'axes.labelsize': 9, 'legend.fontsize': 8,
    'xtick.labelsize': 8, 'ytick.labelsize': 8,
    'axes.spines.top': False, 'axes.spines.right': False,
    'savefig.dpi': 300, 'axes.linewidth': .7,
})
BLUE, ORANGE, TEAL, PURPLE = '#2563eb', '#d97706', '#0f766e', '#7c3aed'
manifest = {}


def save(fig, name, sources, panels):
    fig.savefig(RESULTS / (name + '.png'), dpi=300, facecolor='white')
    plt.close(fig)
    manifest[name] = {'sources': sources, 'plotted_values': panels}


selection = pd.read_csv(RESULTS / 'kmeans_selection.csv')
if 'k' not in selection.columns:
    selection = selection.rename(columns={selection.columns[0]: 'k'})
fig, axes = plt.subplots(1, 2, figsize=(7.4, 2.6), layout='constrained')
k = selection.k.to_numpy()
for ax, column, title, color in zip(axes, ['inertia', 'silhouette'],
        ['(a) Inertia: all 88,858 tracks', '(b) Silhouette: fixed 2,000-track sample'], [BLUE, TEAL]):
    values = selection[column].to_numpy()
    ax.plot(k, values, marker='o', markersize=4, linewidth=1.5, color=color)
    ax.axvline(2, color=PURPLE, linestyle='--', linewidth=.9, alpha=.8)
    ax.set(title=title, xlabel='Number of clusters k', ylabel=column.capitalize(), xticks=k)
    ax.grid(axis='y', alpha=.2)
    if column == 'inertia':
        ax.ticklabel_format(axis='y', style='plain')
        ax.set_ylim(values.min() - 80000, values.max() + 65000)
        for i, offset in [(0, (6, 10)), (-1, (-6, -12))]:
            ax.annotate(f'{values[i]:,.1f}', (k[i], values[i]), xytext=offset,
                        textcoords='offset points', ha='left' if i == 0 else 'right', fontsize=8)
    else:
        ax.set_ylim(.15, .29)
        below = {3, 5, 8, 10}
        for x, y in zip(k, values):
            ax.annotate(f'{y:.4f}', (x, y), xytext=(0, -14 if x in below else 8),
                        textcoords='offset points', ha='center', fontsize=7.5)
save(fig, 'report_k_selection', ['kmeans_selection.csv'],
     {'k': k.tolist(), 'inertia': selection.inertia.tolist(), 'silhouette': selection.silhouette.tolist()})

summary = pd.read_csv(RESULTS / 'q4_summary.csv').set_index('setting')
alpha_ticks = [1e-6, 1e-3, 1, 1e3, 1e6]


def alpha_axis(ax):
    ax.set_xscale('log')
    ax.set_xticks(alpha_ticks)
    ax.set_xlabel(r'Regularization strength $\alpha$')
    ax.grid(axis='y', alpha=.2)


def error_panel(ax, path, s, panel_title):
    ax.plot(path.index, path.test_rmse, color=BLUE, linewidth=1.5,
            marker='o', markersize=2.7, label='Ridge test RMSE')
    ax.axhline(s.OLS_test_rmse, color='#64748b', linestyle=':', linewidth=1.2, label='Same-input OLS test')
    alpha = float(s.alpha_selected_on_validation)
    ax.axvline(alpha, color=PURPLE, linestyle='--', linewidth=1, label='Validation-selected alpha')
    ax.scatter([alpha], [s.Ridge_test_rmse], color=PURPLE, s=26, zorder=4)
    ax.set(title=panel_title, ylabel='Energy RMSE')
    alpha_axis(ax)
    ax.legend(loc='upper left', frameon=False, fontsize=7.1)
    ax.margins(y=.18)


for setting, name in [('full_original', 'report_q4_full'), ('small_polynomial', 'report_q4_small')]:
    path = pd.read_csv(RESULTS / f'q4_{setting}_path.csv').set_index('alpha')
    s = summary.loc[setting]
    assert len(path) == 25 and np.allclose(path.index, np.logspace(-6, 6, 25))
    assert float(path.validation_rmse.idxmin()) == float(s.alpha_selected_on_validation)
    assert abs(path.loc[s.alpha_selected_on_validation, 'test_rmse'] - s.Ridge_test_rmse) < 1e-12
    small = setting == 'small_polynomial'
    fig, axes = plt.subplots(1, 3 if small else 2,
        figsize=(8.0, 2.75) if small else (7.4, 2.6), layout='constrained')
    columns = ['loudness^2', 'loudness^3', 'instrumentalness loudness^2'] if small else ['instrumentalness', 'valence', 'loudness']
    labels = [r'$L^2$', r'$L^3$', r'$L^2I$'] if small else columns
    for column, label, color in zip(columns, labels, [BLUE, ORANGE, TEAL]):
        axes[0].plot(path.index, path[column], label=label, color=color, linewidth=1.5)
    axes[0].axhline(0, color='#94a3b8', linewidth=.7)
    axes[0].set(title='(a) Standardized-basis coefficients' if small else '(a) Standardized-input coefficients', ylabel='Coefficient')
    alpha_axis(axes[0])
    axes[0].legend(loc='upper right' if small else 'center left', frameon=False)
    if small:
        axes[1].plot(path.index, path.coefficient_l2, color=TEAL, linewidth=1.5)
        axes[1].set_yscale('log')
        axes[1].set(title='(b) All 19 coefficients', ylabel='Coefficient L2 norm')
        alpha_axis(axes[1])
    error_panel(axes[-1], path, s, '(c) Held-out error' if small else '(b) Held-out error')
    save(fig, name, [f'q4_{setting}_path.csv', 'q4_summary.csv'],
         {'alpha': path.index.tolist(), 'coefficients': {c: path[c].tolist() for c in columns},
          'test_rmse': path.test_rmse.tolist(), 'OLS_test_rmse': float(s.OLS_test_rmse),
          'validation_selected_alpha': float(s.alpha_selected_on_validation),
          **({'coefficient_l2': path.coefficient_l2.tolist()} if small else {})})

replacements = [
    (r'^\| k \| Inertia \| Silhouette \|\n(?:\|[^\n]*\|\n)+',
     '![選擇 k 的指標](HW1_results_113062273/report_k_selection.png)\n\n圖 1：不同 k 的 inertia 與 silhouette；虛線標示選擇的 k = 2。\n'),
    (r'^\| Alpha \| instrumentalness 係數[^\n]*\n(?:\|[^\n]*\|\n)+',
     '![完整資料的正則化結果](HW1_results_113062273/report_q4_full.png)\n\n圖 2：完整資料的三欄係數與 test RMSE；虛線標示依 validation 選出的 alpha。\n'),
    (r'^\| Alpha \| L² 係數[^\n]*\n(?:\|[^\n]*\|\n)+',
     '![小樣本多項式的正則化結果](HW1_results_113062273/report_q4_small.png)\n\n圖 3：80 首、多項式設定的代表基底係數、全部係數 L2 長度與 test RMSE。\n'),
]
report = original
for pattern, replacement in replacements:
    report, count = re.subn(pattern, replacement, report, flags=re.M)
    assert count == 1 or (count == 0 and replacement.splitlines()[0] in report), (pattern, count)
report = report.replace('下表係數對應標準化原始輸入', '圖 2 的係數對應標準化原始輸入')
report = report.replace('下表係數對應再次標準化的基底', '圖 3 的係數對應再次標準化的基底')
assert report.count('![') == 3
REPORT.write_text(report, encoding='utf-8')
for relative, expected in before.items():
    assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected, relative
(AUDIT / 'plot_data_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print('Replaced three tables with source-derived figures; all source CSVs, notebook, pre-report, dataset and AI-use log unchanged.')
