import subprocess
import os
import glob

def extract_results():
    scavetool_path = r"C:\omnetpp-6.0.3-windows-x86_64\omnetpp-6.0.3\bin\opp_scavetool.exe"
    simulations_dir = "C:/OmnetDos/test_omnet/simulations/results"
    output_file = "C:/OmnetDos/test_omnet/src/data/results.csv"

    # Buscamos todos los archivos .sca y .vec
    result_files = glob.glob(os.path.join(simulations_dir, "*.sca")) + \
                   glob.glob(os.path.join(simulations_dir, "*.vec"))

    if not result_files:
        print("No se encontraron archivos de resultados en simulations/results")
        return None

    # Simplificamos el filtro para evitar errores de sintaxis
    # Esto traerá todas las métricas y nosotros las filtramos en Python
    scavetool_command = [
        scavetool_path,
        "export",
        "-o", output_file,
        *result_files
    ]

    try:
        print("Exportando resultados con scavetool...")
        subprocess.run(scavetool_command, check=True)
        print(f"Resultados exportados a {output_file}")
        return output_file
    except subprocess.CalledProcessError as e:
        print(f"Error al extraer resultados: {e}")
        return None