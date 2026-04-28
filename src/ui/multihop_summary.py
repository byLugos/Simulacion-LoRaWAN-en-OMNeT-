import pandas as pd
import matplotlib.pyplot as plt
import math

# === PALETA CLARA ===
BG       = '#FFFFFF'
BG2      = '#F5F5F5'
FG       = '#000000'
BORDE    = '#B0B0B0'


def _safe_int(v):
    """Convierte a int de forma segura, devuelve 0 si es NaN o None."""
    try:
        if v is None:
            return 0
        if isinstance(v, float) and math.isnan(v):
            return 0
        return int(v)
    except Exception:
        return 0


def show_multihop_summary(csv_path, comunicacion, diccionario):

    df = pd.read_csv(csv_path, low_memory=False)

    run_modelo = {}
    for _, row in df[df['type'] == 'runattr'].iterrows():
        if row['attrname'] == 'iterationvars':
            val = str(row['attrvalue'])
            run_modelo[row['run']] = 'TrueRays' if 'TrueRays' in val else 'Multimodel'

    scalars = df[df['type'] == 'scalar'].copy()
    scalars['modelo'] = scalars['run'].map(run_modelo)

    gateway_idx = diccionario.get(0, 0)
    next_hop = {}
    for _, row in comunicacion.iterrows():
        origen  = diccionario.get(row['Nodo origen'])
        destino = diccionario.get(row['Nodo destino'])
        if origen is None or destino is None:
            continue
        next_hop[origen] = -1 if destino == gateway_idx else destino

    def contar_saltos(nodo):
        saltos, cursor, vistos = 0, nodo, set()
        while True:
            sig = next_hop.get(cursor)
            saltos += 1
            if sig is None or sig == -1:
                return saltos + 1
            if sig in vistos:
                return saltos
            vistos.add(cursor)
            cursor = sig

    saltos_por_nodo = {n: contar_saltos(n) for n in next_hop}

    ns = scalars[scalars['name'].str.contains('numReceivedFromNode', na=False)].copy()

    tabla_data = []
    for _, row in ns.sort_values(['modelo', 'name']).iterrows():
        try:
            node_id = int(row['name'].split()[-1]) - 1
            saltos  = saltos_por_nodo.get(node_id, 1)
            tabla_data.append({
                'Nodo':     node_id,
                'Saltos':   saltos,
                'Pkts':     int(row['value']),
                'Multihop': 'SI' if saltos >= 3 else 'No',
                'Modelo':   row['modelo']
            })
        except Exception:
            continue

    if not tabla_data:
        print("Sin datos de multihop para mostrar.")
        return

    rec_df = pd.DataFrame(tabla_data)

    kpis = {}
    for modelo in ['TrueRays', 'Multimodel']:
        sub       = rec_df[rec_df['Modelo'] == modelo]
        total_row = scalars[(scalars['modelo'] == modelo) &
                            (scalars['name'] == 'totalReceivedPackets')]['value']
        total     = int(total_row.values[0]) if len(total_row) else sub['Pkts'].sum()
        mh        = sub[sub['Saltos'] >= 3]['Pkts'].sum()
        der_row   = scalars[(scalars['modelo'] == modelo) &
                            (scalars['name'] == 'LoRa_NS_DER')]['value']
        der = float(der_row.values[0]) if len(der_row) else 0
        kpis[modelo] = {
            'total': total, 'mh': mh,
            'pct':   mh / total * 100 if total else 0,
            'der':   der
        }

    # === FIGURA ===
    fig, axes = plt.subplots(1, 3, figsize=(14, 5),
                             gridspec_kw={'width_ratios': [1, 1, 2]})
    fig.patch.set_facecolor(BG)
    fig.suptitle('Confirmacion de Multihop LoRa — Tunel de Mina',
                 fontsize=14, fontweight='bold', color=FG, y=0.97)

    # === KPIs ===
    for ax, modelo in zip(axes[:2], ['TrueRays', 'Multimodel']):
        ax.set_facecolor(BG2)
        ax.axis('off')
        ax.text(0.5, 0.82, modelo,
                transform=ax.transAxes,
                ha='center', fontsize=12, fontweight='bold', color=FG)
        ax.text(0.5, 0.52, f"{kpis[modelo]['pct']:.0f}%",
                transform=ax.transAxes,
                ha='center', fontsize=32, fontweight='bold', color=FG)
        ax.text(0.5, 0.30, 'paquetes via multihop',
                transform=ax.transAxes,
                ha='center', fontsize=9, color="#555555")
        ax.text(0.5, 0.12,
                f"{kpis[modelo]['mh']} de {kpis[modelo]['total']} pkts"
                f"   DER = {kpis[modelo]['der']:.3f}",
                transform=ax.transAxes,
                ha='center', fontsize=8, color="#555555")

    # === TABLA ===
    ax_t = axes[2]
    ax_t.axis('off')
    ax_t.set_facecolor(BG)

    pivot = rec_df.pivot_table(
        index=['Nodo', 'Saltos', 'Multihop'],
        columns='Modelo', values='Pkts', aggfunc='sum'
    ).reset_index().sort_values('Nodo')

    col_labels = ['Nodo', 'Saltos', 'Multihop', 'Pkts TR', 'Pkts MM']
    rows = []
    for _, r in pivot.iterrows():
        rows.append([
            _safe_int(r['Nodo']),
            _safe_int(r['Saltos']),
            r['Multihop'],
            _safe_int(r.get('TrueRays')),
            _safe_int(r.get('Multimodel')),
        ])

    tabla = ax_t.table(cellText=rows, colLabels=col_labels,
                       loc='center', cellLoc='center')
    tabla.auto_set_font_size(False)
    tabla.set_fontsize(8)
    tabla.scale(1, 1.4)

    for (ri, ci), cell in tabla.get_celld().items():
        cell.set_edgecolor(BORDE)
        if ri == 0:
            cell.set_facecolor(BG2)
            cell.set_text_props(color=FG, fontweight='bold')
        else:
            cell.set_facecolor('#FFFFFF')
            cell.set_text_props(color=FG)

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    plt.savefig('multihop_summary.png', dpi=110, bbox_inches='tight',
                facecolor=BG)
    plt.show()