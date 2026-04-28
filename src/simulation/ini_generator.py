import os
from collections import defaultdict

def generate_ini_files(coordenadas, comunicacion, tipo_nodos, tam_mina, sf, cr, freq):
    project_root = os.path.dirname(os.getcwd())
    simulations_dir = os.path.join(project_root, "simulations")
    os.makedirs(simulations_dir, exist_ok=True)
    
    freq_hz  = freq * 1_000_000
    freq_mhz = f"{freq}MHz"

    width_mine  = tam_mina['max_X'].iloc[0]
    height_mine = tam_mina['max_Y'].iloc[0]

    nodos_inicio = coordenadas["Nodo"].values
    nodos_final  = tipo_nodos["Nodo"].values

    valores_coincidentes = list(set(nodos_inicio) & set(nodos_final))
    if 0 not in valores_coincidentes:
        valores_coincidentes.insert(0, 0)

    diccionario = {nodo: idx for idx, nodo in enumerate(valores_coincidentes)}

    # --- Generar coordenadas.ini ---
    coord_path = os.path.join(simulations_dir, "coordenadas.ini")
    with open(coord_path, 'w', encoding='utf-8') as file:
        file.write("# Archivo generado automaticamente - Coordenadas\n\n")

        file.write("*.gateway.mobility.typename = \"StationaryMobility\"\n")
        file.write("*.gateway.mobility.initialX = 250m\n")
        file.write("*.gateway.mobility.initialY = 150m\n")
        file.write("*.gateway.mobility.initialZ = 0m\n")
        file.write("*.gateway.mobility.initFromDisplayString = false\n\n")

        file.write("*.networkServer.mobility.typename = \"StationaryMobility\"\n")
        file.write("*.networkServer.mobility.initialX = 400m\n")
        file.write("*.networkServer.mobility.initialY = 50m\n")
        file.write("*.networkServer.mobility.initialZ = 0m\n")
        file.write("*.networkServer.mobility.initFromDisplayString = false\n\n")

        for item in coordenadas["Nodo"]:
            if item in valores_coincidentes:
                host_index = diccionario[item]
                cX      = round(coordenadas.loc[coordenadas["Nodo"] == item, "cX"].iloc[0], 2)
                cY_orig = round(coordenadas.loc[coordenadas["Nodo"] == item, "cY"].iloc[0], 2)
                #cY      = round((cY_orig * -1) + height_mine, 2)
                cY = round(height_mine - cY_orig, 2)

                file.write(f'*.host[{host_index}].mobility.initialX = {cX}m\n')
                file.write(f'*.host[{host_index}].mobility.initialY = {cY}m\n')
                file.write(f'*.host[{host_index}].mobility.initialZ = 0m\n\n')

        file.write(f'*.numHost = {len(valores_coincidentes)}\n')
        file.write(f'*.width = {width_mine}m\n')
        file.write(f'*.height = {height_mine}m\n')

    # --- Leer nextHopId DIRECTAMENTE del Excel ---
    # Cada fila dice: este nodo envia sus paquetes hacia este destino.
    # Ese destino ES el nextHopId. Si el destino es el gateway (idx=0), ponemos -1.
    gateway_idx = diccionario.get(0, 0)

    next_hop = {}   # idx_nodo -> idx_next_hop (-1 si es el gateway)
    for _, row in comunicacion.iterrows():
        origen_raw  = row['Nodo origen']
        destino_raw = row['Nodo destino']
        origen  = diccionario.get(origen_raw)
        destino = diccionario.get(destino_raw)
        if origen is None or destino is None:
            continue
        # Si el destino es el gateway, el nodo va directo (-1)
        next_hop[origen] = -1 if destino == gateway_idx else destino

    # --- Construir destinos bidireccionales por nodo (para destNodeIds) ---
    destinos_por_nodo = defaultdict(list)
    for _, row in comunicacion.iterrows():
        origen_raw  = row['Nodo origen']
        destino_raw = row['Nodo destino']
        origen  = diccionario.get(origen_raw)
        destino = diccionario.get(destino_raw)
        if origen is None or destino is None:
            continue
        destinos_por_nodo[origen].append(destino)
        destinos_por_nodo[destino].append(origen)

    # Eliminar duplicados manteniendo orden
    for nodo in destinos_por_nodo:
        seen = set()
        destinos_por_nodo[nodo] = [x for x in destinos_por_nodo[nodo]
                                    if not (x in seen or seen.add(x))]

    # --- Imprimir rutas para verificacion ---
    print("\n=== RUTAS (desde Comunicacion.xlsx) ===")
    for nodo_idx in sorted(next_hop.keys()):
        hop = next_hop[nodo_idx]
        hop_str = "GW" if hop == -1 else str(hop)
        print(f"  host[{nodo_idx}] -> nextHop={hop_str}")

    # --- Generar conexion.ini ---
    conexion_path = os.path.join(simulations_dir, "conexion.ini")
    with open(conexion_path, 'w', encoding='utf-8') as file:
        file.write("# Archivo generado automaticamente - Configuracion LoRa App\n\n")
        file.write("*.host[*].numApps = 1\n")
        file.write("*.host[*].app[0].typename = \"SimpleLoRaApp\"\n")
        file.write("*.host[*].app[0].dataSize = 10B\n")
        file.write("*.host[*].app[0].initialLoRaTP = 14dBm\n")
        file.write(f"*.host[*].app[0].initialLoRaCF = {freq_mhz}\n")
        file.write("*.host[*].app[0].initialLoRaBW = 125kHz\n")
        file.write(f"*.host[*].app[0].initialLoRaSF = {sf}\n")
        file.write(f"*.host[*].app[0].initialLoRaCR = {cr}\n")
        file.write("*.host[*].app[0].initialUseHeader = true\n")
        file.write("*.host[*].app[0].evaluateADRinNode = false\n")
        file.write("*.host[*].app[0].destNodeIds = \"-1\"\n")
        file.write("*.host[*].app[0].nextHopId = -1\n\n")

        for nodo_idx, destinos in sorted(destinos_por_nodo.items()):
            dest_str = " ".join(str(d) for d in destinos)
            hop      = next_hop.get(nodo_idx, -1)
            hop_str  = "GW" if hop == -1 else str(hop)

            file.write(f"# Nodo {nodo_idx} | vecinos: {dest_str} | nextHop: {hop_str}\n")
            file.write(f"*.host[{nodo_idx}].app[0].destNodeIds = \"{dest_str}\"\n")
            file.write(f"*.host[{nodo_idx}].app[0].srcNodeId = {nodo_idx}\n")
            file.write(f"*.host[{nodo_idx}].app[0].nextHopId = {hop}\n")
            file.write(f"*.host[{nodo_idx}].app[0].timeToFirstPacket = exponential(5s)\n")
            file.write(f"*.host[{nodo_idx}].app[0].timeToNextPacket = exponential(10s)\n\n")
            
    # --- frecuencia.ini---
    freq_path = os.path.join(simulations_dir, "frecuencia.ini")
    with open(freq_path, 'w', encoding='utf-8') as file:
        file.write("# Archivo generado automaticamente - Frecuencia\n\n")
        file.write(f"*.radioMedium.pathLoss.frequency = {freq_hz}\n")

    print(f"\nArchivos INI generados exitosamente en: {simulations_dir}")
    return diccionario