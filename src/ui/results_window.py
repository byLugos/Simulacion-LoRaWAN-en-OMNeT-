import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from processing.pathloss_analysis import process_radio_metrics

# === PALETA PERSONALIZADA (AZUL Y NARANJA) ===
BG      = '#FFFFFF'
BG2     = '#F5F5F5'
FG      = '#212121'
GRID    = '#E0E0E0'
BORDER  = '#CCCCCC'

# Colores principales para los modelos
COLORES = {
    'TrueRays': '#1F77B4',   # Un azul sólido y elegante
    'Multimodel': '#FF7F0E'  # Un naranja vibrante que contrasta
}

def _extraer_der(csv_path):
    df = pd.read_csv(csv_path, low_memory=False)

    run_modelo = {}
    for _, row in df[df['type'] == 'runattr'].iterrows():
        if row['attrname'] == 'iterationvars':
            val = str(row['attrvalue'])
            run_modelo[row['run']] = 'TrueRays' if 'TrueRays' in val else 'Multimodel'

    scalars = df[df['type'] == 'scalar'].copy()
    scalars['modelo'] = scalars['run'].map(run_modelo)

    der_data = {}
    for modelo in ['TrueRays', 'Multimodel']:
        sub    = scalars[scalars['modelo'] == modelo]
        ns_der = sub[sub['name'] == 'LoRa_NS_DER']['value']
        gw_der = sub[sub['name'] == 'LoRa_GW_DER']['value']

        der_data[modelo] = {
            'ns': float(ns_der.values[0]) if len(ns_der) else 0.0,
            'gw': float(gw_der.values[0]) if len(gw_der) else 0.0,
        }

    return der_data

def show_results(csv_path, coordenadas, comunicacion, diccionario, tam_mina):

    df_rssi, df_snir, df_rssi_pares = process_radio_metrics(
        csv_path, coordenadas, comunicacion, diccionario, tam_mina
    )
    der_data = _extraer_der(csv_path)

    if df_rssi.empty and df_snir.empty and not der_data:
        print("Sin datos suficientes para graficar.")
        return

    sns.set_theme(style="whitegrid", font_scale=0.95)

    fig, axes = plt.subplots(1, 3, figsize=(16, 6))
    fig.patch.set_facecolor(BG)
    fig.suptitle('Métricas de Enlace LoRa — Simulación en Túnel de Mina', 
                 fontsize=15, fontweight='bold', color=FG, y=0.98)

    ax_rssi, ax_snir, ax_der = axes

    for ax in axes:
        ax.set_facecolor(BG)
        ax.tick_params(colors=FG, labelsize=9)
        ax.xaxis.label.set_color(FG)
        ax.yaxis.label.set_color(FG)
        ax.title.set_color(FG)
        ax.grid(color=GRID, linestyle='-', linewidth=0.7, alpha=0.8)
        for spine in ax.spines.values():
            spine.set_edgecolor(BORDER)

    # ── 1. RSSI vs Distancia (Scatter con líneas de tendencia) ──────────
    if not df_rssi.empty:
        for modelo, sub in df_rssi.groupby('Modelo'):
            color_m = COLORES.get(modelo, '#333333')
            ax_rssi.scatter(sub['distancia'], sub['value'], 
                            color=color_m, alpha=0.4, s=18, label=f'Datos {modelo}')
            
            if len(sub) > 3:
                z  = np.polyfit(sub['distancia'], sub['value'], 1)
                xs = np.linspace(sub['distancia'].min(), sub['distancia'].max(), 100)
                ax_rssi.plot(xs, np.poly1d(z)(xs), 
                             color=color_m, linewidth=2.5, 
                             linestyle='-', label=f'Tendencia {modelo}')

    ax_rssi.set_title('RSSI vs Distancia', fontsize=12, fontweight='semibold')
    ax_rssi.set_xlabel('Distancia (m)')
    ax_rssi.set_ylabel('RSSI (dBm)')
    ax_rssi.legend(fontsize=8.5, frameon=True, facecolor='white', framealpha=0.8)

    # ── 2. SNIR Boxplot (Distribución con colores) ─────────────────────
    if not df_snir.empty:
        modelos_s = df_snir['Modelo'].unique()
        data_plot = [df_snir[df_snir['Modelo'] == m]['value'].values for m in modelos_s]
        
        bp = ax_snir.boxplot(data_plot, labels=modelos_s, patch_artist=True,
                             medianprops=dict(color='white', linewidth=2))
        
        for patch, m in zip(bp['boxes'], modelos_s):
            patch.set_facecolor(COLORES.get(m, '#999999'))
            patch.set_alpha(0.8)
            patch.set_edgecolor('#444444')

    ax_snir.set_title('SNIR en NetworkServer', fontsize=12, fontweight='semibold')
    ax_snir.set_ylabel('SNIR (dB)')

    # ── 3. DER (Barras comparativas) ──────────────────────────────────
    modelos_d = [m for m in ['TrueRays', 'Multimodel'] if m in der_data]

    if modelos_d:
        x     = np.arange(len(modelos_d))
        ancho = 0.35

        ns_vals = [der_data[m]['ns'] for m in modelos_d]
        gw_vals = [der_data[m]['gw'] for m in modelos_d]

        # Barras de Network Server (Sólidas)
        ax_der.bar(x - ancho/2, ns_vals, ancho, 
                   color=[COLORES[m] for m in modelos_d], 
                   alpha=0.9, label='DER NetworkServer', edgecolor='white', linewidth=1)
        
        # Barras de Gateway (Hachuradas o más claras para diferenciar)
        ax_der.bar(x + ancho/2, gw_vals, ancho, 
                   color=[COLORES[m] for m in modelos_d], 
                   alpha=0.35, label='DER Gateway', edgecolor='black', linewidth=0.8, hatch='//')

        ax_der.set_xticks(x)
        ax_der.set_xticklabels(modelos_d, fontweight='bold')
        ax_der.set_ylim(0, 1.15)
        ax_der.set_title('DER — Eficiencia de Recepción', fontsize=12, fontweight='semibold')
        ax_der.set_ylabel('Ratio (0 a 1)')
        ax_der.legend(fontsize=8.5, loc='upper right')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig('link_metrics_color.png', dpi=120, bbox_inches='tight', facecolor=BG)
    plt.show()
    print("Gráfica a color guardada en link_metrics_color.png")