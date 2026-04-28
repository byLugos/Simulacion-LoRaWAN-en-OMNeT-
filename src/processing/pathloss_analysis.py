import pandas as pd
import numpy as np
import re


def process_radio_metrics(csv_path, coordenadas, comunicacion, diccionario, tam_mina=None):
    """
    Extrae RSSI y SNIR del CSV de OMNeT++.

    Fuentes:
      - RSSI agregado : todos los escalares 'unit=dBm' — todos los pares TX-RX.
      - RSSI por par  : solo los pares configurados en comunicacion (conexion.ini).
      - SNIR          : vector 'Vector of SNIR per node' del NetworkServer (lineal → dB).

    Retorna:
      df_rssi      : [Modelo, value (dBm), distancia (m)] — todos los pares
      df_snir      : [Modelo, value (dB)]
      df_rssi_pares: [Modelo, par, distancia (m), value (dBm)] — solo pares configurados
    """
    try:
        df = pd.read_csv(csv_path, low_memory=False)
    except Exception as e:
        print(f"Error al leer el CSV: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    # ── Mapear run → modelo ──────────────────────────────────────────────────
    run_modelo = {}
    for _, row in df[df['type'] == 'runattr'].iterrows():
        if row['attrname'] == 'iterationvars':
            val = str(row['attrvalue'])
            run_modelo[row['run']] = 'TrueRays' if 'TrueRays' in val else 'Multimodel'

    scalars = df[df['type'] == 'scalar'].copy()
    scalars['modelo'] = scalars['run'].map(run_modelo)
    vectors = df[df['type'] == 'vector'].copy()
    vectors['modelo'] = vectors['run'].map(run_modelo)

    # ── Calcular coordenadas simuladas de cada nodo ──────────────────────────
    # ini_generator invierte Y: cY_sim = -cY_excel + height_mine
    # height_mine viene de tam_mina['max_Y'], no del máximo de coordenadas
    try:
        height_mine = float(tam_mina['max_Y'].iloc[0]) if tam_mina is not None else 494.0
    except Exception:
        height_mine = 494.0

    coord_sim = {}   # idx_nodo → (x_sim, y_sim)
    for _, row in coordenadas.iterrows():
        nodo = row['Nodo']
        idx  = diccionario.get(nodo)
        if idx is None:
            continue
        coord_sim[idx] = (float(row['cX']), float(-row['cY'] + height_mine))

    # ── Construir tabla de pares configurados con sus coordenadas ────────────
    pares_config = {}   # (tx_x, tx_y, rx_x, rx_y) → etiqueta del par
    for _, row in comunicacion.iterrows():
        idx_o = diccionario.get(row['Nodo origen'])
        idx_d = diccionario.get(row['Nodo destino'])
        if idx_o is None or idx_d is None:
            continue
        if idx_o not in coord_sim or idx_d not in coord_sim:
            continue
        tx = coord_sim[idx_o]
        rx = coord_sim[idx_d]
        etiqueta = f"N{row['Nodo origen']}\u2192N{row['Nodo destino']}"
        pares_config[(round(tx[0],0), round(tx[1],0),
                      round(rx[0],0), round(rx[1],0))] = etiqueta

    # ── RSSI — todos los pares ───────────────────────────────────────────────
    rssi_rows = scalars[scalars['name'].str.contains('unit=dBm', na=False)].copy()
    coord_re  = re.compile(r'from \(([^)]+)\) to \(([^)]+)\)')
    rssi_list       = []
    rssi_pares_list = []

    for _, row in rssi_rows.iterrows():
        try:
            m = coord_re.search(str(row['name']))
            if not m:
                continue
            c_tx = [float(x) for x in m.group(1).split(',')]
            c_rx = [float(x) for x in m.group(2).split(',')]
            dist  = np.sqrt((c_tx[0]-c_rx[0])**2 + (c_tx[1]-c_rx[1])**2)
            valor = float(row['value'])
            modelo = row['modelo']

            # Registro agregado (todos los pares)
            rssi_list.append({
                'Modelo':    modelo,
                'value':     valor,
                'distancia': dist
            })

            # Registro por par configurado
            key = (round(c_tx[0],0), round(c_tx[1],0),
                   round(c_rx[0],0), round(c_rx[1],0))
            if key in pares_config:
                rssi_pares_list.append({
                    'Modelo':    modelo,
                    'par':       pares_config[key],
                    'distancia': round(dist, 1),
                    'value':     valor
                })
        except Exception:
            continue

    df_rssi       = pd.DataFrame(rssi_list)
    df_rssi_pares = pd.DataFrame(rssi_pares_list)

    # ── SNIR ─────────────────────────────────────────────────────────────────
    snir_vecs = vectors[
        (vectors['name'] == 'Vector of SNIR per node') &
        (vectors['module'].str.contains('networkServer', na=False))
    ]
    snir_list = []
    for _, row in snir_vecs.iterrows():
        try:
            vals = [float(v) for v in str(row['vecvalue']).split()
                    if v and v != 'nan']
            for v in vals:
                if v > 0:
                    snir_list.append({'Modelo': row['modelo'],
                                      'value':  10 * np.log10(v)})
        except Exception:
            continue
    df_snir = pd.DataFrame(snir_list)

    # ── Resumen por consola ───────────────────────────────────────────────────
    _print_summary(df_rssi, df_rssi_pares, df_snir, scalars, run_modelo)

    return df_rssi, df_snir, df_rssi_pares


def _print_summary(df_rssi, df_rssi_pares, df_snir, scalars, run_modelo):
    SEP  = "=" * 62
    SEP2 = "-" * 62

    print(f"\n{SEP}")
    print("  METRICAS DE ENLACE LoRa — RESUMEN")
    print(SEP)

    # RSSI agregado
    print("\n  RSSI (dBm) — todos los pares TX-RX")
    print(SEP2)
    if not df_rssi.empty:
        resumen = df_rssi.groupby('Modelo')['value'].agg(
            N='count', Media='mean', Minimo='min', Maximo='max', Std='std'
        ).round(2)
        print(resumen.to_string())
        print()
        for modelo, sub in df_rssi.groupby('Modelo'):
            n_bajo  = (sub['value'] < -60).sum()
            n_medio = ((sub['value'] >= -90) & (sub['value'] < -60)).sum()
            n_muy   = (sub['value'] < -100).sum()
            print(f"  [{modelo}]  >-60dBm: {len(sub)-n_bajo}   "
                  f"-60 a -90dBm: {n_medio-n_muy if n_medio > n_muy else 0}   "
                  f"<-90dBm: {n_bajo}")
    else:
        print("  Sin datos de RSSI.")   

    # RSSI por par configurado
    print(f"\n{SEP2}")
    print("  RSSI (dBm) — solo pares configurados en conexion.ini")
    print(SEP2)
    if not df_rssi_pares.empty:
        resumen_p = df_rssi_pares.groupby(['Modelo','par','distancia'])['value'].mean().round(2)
        for modelo in ['TrueRays', 'Multimodel']:
            print(f"\n  [{modelo}]")
            sub = df_rssi_pares[df_rssi_pares['Modelo'] == modelo]
            tabla = sub.groupby(['par','distancia'])['value'].agg(
                Media='mean', Min='min', Max='max'
            ).round(2).sort_values('distancia')
            for (par, dist), vals in tabla.iterrows():
                print(f"    {par:<14}  {dist:>6.1f}m  "
                      f"media={vals['Media']:>7.2f} dBm  "
                      f"[{vals['Min']:.2f}, {vals['Max']:.2f}]")
    else:
        print("  No se encontraron pares configurados en el CSV.")

    # SNIR
    print(f"\n{SEP2}")
    print("  SNIR (dB) — relacion senal-ruido-interferencia en NS")
    print(SEP2)
    if not df_snir.empty:
        resumen = df_snir.groupby('Modelo')['value'].agg(
            N='count', Media='mean', Minimo='min', Maximo='max', Std='std'
        ).round(2)
        print(resumen.to_string())
        print()
        for modelo, sub in df_snir.groupby('Modelo'):
            print(f"  [{modelo}]  min={sub['value'].min():.2f} dB  "
                  f"max={sub['value'].max():.2f} dB  "
                  f"bajo 0dB: {(sub['value'] < 0).sum()}/{len(sub)}")
    else:
        print("  Sin datos de SNIR.")

    # DER
    print(f"\n{SEP2}")
    print("  DER — Data Extraction Rate")
    print(SEP2)
    print(f"  {'Modelo':<14}  {'GW':>6}  {'NS':>6}  {'Perdida GW->NS':>14}")
    print(f"  {'-'*46}")
    for modelo in ['TrueRays', 'Multimodel']:
        sub    = scalars[scalars['run'].map(run_modelo) == modelo]
        gw_row = sub[sub['name'] == 'LoRa_GW_DER']['value']
        ns_row = sub[sub['name'] == 'LoRa_NS_DER']['value']
        gw = float(gw_row.values[0]) if len(gw_row) else 0.0
        ns = float(ns_row.values[0]) if len(ns_row) else 0.0
        print(f"  {modelo:<14}  {gw:>6.3f}  {ns:>6.3f}  {gw-ns:>14.3f}")

    print(f"\n{SEP}\n")