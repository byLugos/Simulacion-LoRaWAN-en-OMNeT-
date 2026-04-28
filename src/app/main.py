from processing.excel_loader import load_excel_data
from simulation.ini_generator import generate_ini_files
from simulation.omnet_runner import run_simulation
from simulation.scavetool_runner import extract_results
from ui.multihop_summary import show_multihop_summary
from ui.results_window import show_results
from ui.file_loader import load_input_files, select_lora_params


def main():
    #-------------------------------
    # Cargar archivos desde interfaz UNA SOLA VEZ
    #-------------------------------
    excel_path, image_info = load_input_files()

    #-------------------------------
    # Leer Excel para obtener dimensiones
    #-------------------------------
    coordenadas, comunicacion, tipo_nodos, tam_mina = load_excel_data(excel_path)

    #-------------------------------
    # Generar .ini con parámetros
    #-------------------------------
    sf, cr, freq = select_lora_params()

    #-------------------------------
    # Generar archivos .ini
    #-------------------------------
    diccionario = generate_ini_files(coordenadas, comunicacion, tipo_nodos, tam_mina, sf, cr, freq)

    #-------------------------------
    # Ejecutar simulación OMNeT++
    #-------------------------------
    run_simulation()

    #-------------------------------
    # Extraer resultados con scavetool
    #-------------------------------
    csv_path = extract_results()

    #-------------------------------
    # Mostrar resumen de multihop
    #-------------------------------
    show_multihop_summary(csv_path, comunicacion, diccionario)

    #-------------------------------
    # Mostrar ventana de resultados
    #-------------------------------
    show_results(csv_path, coordenadas, comunicacion, diccionario, tam_mina)


if __name__ == "__main__":
    main()