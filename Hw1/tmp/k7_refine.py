import json
from pathlib import Path

notebook = json.loads(Path('HW1_code_113062273.ipynb').read_text(encoding='utf-8'))
ns = {'__name__': '__main__'}
setup = ''.join(notebook['cells'][2]['source']).replace("OUT = Path('HW1_results_113062273')", "OUT = Path('tmp/k7_refine')").replace('OUT.mkdir(exist_ok=True)', 'OUT.mkdir(parents=True, exist_ok=True)')
exec(setup, ns)
ns['display'] = lambda *args, **kwargs: None
ns['table'] = lambda name, frame, show=True: frame
for index in [3, 5, 6]:
    exec(''.join(notebook['cells'][index]['source']), ns)
clean, audio = ns['clean'], ns['AUDIO']
assert len(clean) == 88858
z = ns['StandardScaler']().fit_transform(clean[audio])
km = ns['KMeans'](n_clusters=7, n_init=10, random_state=ns['SEED'], algorithm='lloyd').fit(z)
profiles = clean[audio].assign(cluster=km.labels_).groupby('cluster').mean()
profiles.insert(0, 'tracks', ns['pd'].Series(km.labels_).value_counts().sort_index())
profiles.to_csv(ns['OUT'] / 'k7_cluster_profiles.csv', encoding='utf-8-sig')
metrics = ns['pd'].read_csv('HW1_results_113062273/kmeans_selection.csv').set_index('k')
ns['np'].testing.assert_allclose(km.inertia_, metrics.loc[7, 'inertia'], rtol=1e-10)
sample = ns['rng'].choice(len(clean), size=2000, replace=False)
sil = ns['silhouette_score'](z[sample], km.labels_[sample])
ns['np'].testing.assert_allclose(sil, metrics.loc[7, 'silhouette'], rtol=1e-10)
print('K7 PROFILES\n' + profiles.round(4).to_string())
print('Inertia reduction vs k2:', (1 - metrics.loc[7, 'inertia'] / metrics.loc[2, 'inertia']) * 100)
print('Silhouette reduction vs k2:', (1 - metrics.loc[7, 'silhouette'] / metrics.loc[2, 'silhouette']) * 100)
print('K2 silhouette higher vs k7:', (metrics.loc[2, 'silhouette'] / metrics.loc[7, 'silhouette'] - 1) * 100)
plt = ns['plt']
fig, axes = plt.subplots(1, 2, figsize=(9, 3.2), layout='constrained')
for ax, column, color in zip(axes, ['inertia', 'silhouette'], ['#2563eb', '#0f766e']):
    ax.plot(metrics.index, metrics[column], 'o-', color=color)
    ax.axvline(7, linestyle='--', color='#7c3aed', label='Selected k = 7')
    ax.set(xlabel='Number of clusters k', ylabel=column.capitalize(), xticks=metrics.index)
    ax.grid(axis='y', alpha=.2)
    ax.legend(frameon=False)
axes[0].set_title('All 88,858 tracks')
axes[1].set_title('Same fixed 2,000-track sample')
fig.savefig(ns['OUT'] / 'k7_selection.png', dpi=200)
plt.close(fig)

ns['BEST_K'] = 7
ns['cluster_labels'] = km.labels_
ns['sil_idx'] = sample
def save_table(name, frame, show=True):
    frame.to_csv(ns['OUT'] / (name + '.csv'), encoding='utf-8-sig')
    return frame
ns['table'] = save_table
exec(''.join(notebook['cells'][16]['source']), ns)
print('K7 STABILITY\n' + ns['pd'].read_csv(ns['OUT'] / 'cluster_stability.csv').to_string(index=False))
pca = ns['PCA'](svd_solver='full').fit(z)
pcs = pca.transform(z)
centroids = ns['pd'].DataFrame(pcs[:, :2], columns=['PC1', 'PC2']).assign(cluster=km.labels_).groupby('cluster').mean()
centroids.to_csv(ns['OUT'] / 'k7_pca_centroids.csv', encoding='utf-8-sig')
print('K7 PC CENTROIDS\n' + centroids.round(4).to_string())
colors = ['#2563eb', '#d97706', '#059669', '#7c3aed', '#db2777', '#0891b2', '#64748b']
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9,
    'axes.titlesize': 10, 'axes.labelsize': 9, 'legend.fontsize': 8})
fig, ax = plt.subplots(figsize=(7.4, 2.7), layout='constrained')
for cluster, color in enumerate(colors):
    ids = sample[km.labels_[sample] == cluster]
    ax.scatter(pcs[ids, 0], pcs[ids, 1], s=8, alpha=.55, color=color, label=f'Cluster {cluster}')
ax.set(xlabel=f'PC1 ({pca.explained_variance_ratio_[0]:.2%})',
       ylabel=f'PC2 ({pca.explained_variance_ratio_[1]:.2%})',
       title='Same fixed 2,000-track sample; k = 7 fitted in all 9 features')
ax.legend(ncol=4, loc='upper center', bbox_to_anchor=(.5, 1.02), frameon=False, markerscale=1.5)
ax.grid(alpha=.15)
fig.savefig(ns['OUT'] / 'k7_pca.png', dpi=300)
plt.close(fig)

fig, axes = plt.subplots(1, 2, figsize=(7.4, 2.6), layout='constrained')
for ax, column, title, color in zip(axes, ['inertia', 'silhouette'],
    ['(a) Inertia: all 88,858 tracks', '(b) Silhouette: fixed 2,000-track sample'], ['#2563eb', '#0f766e']):
    values = metrics[column]
    ax.plot(metrics.index, values, 'o-', color=color, linewidth=1.5, markersize=4)
    ax.axvline(7, color='#7c3aed', linestyle='--', linewidth=.9)
    ax.set(title=title, xlabel='Number of clusters k', ylabel=column.capitalize(), xticks=metrics.index)
    ax.grid(axis='y', alpha=.2)
    if column == 'silhouette':
        ax.set_ylim(.15, .29)
        for k, value in values.items():
            ax.annotate(f'{value:.4f}', (k, value), xytext=(0, -14 if k in [3,5,8,10] else 8),
                        textcoords='offset points', ha='center', fontsize=7.5)
fig.savefig(ns['OUT'] / 'k7_selection.png', dpi=300)
plt.close(fig)
