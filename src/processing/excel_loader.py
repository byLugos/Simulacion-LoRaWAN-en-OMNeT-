import pandas as pd


def load_excel_data(path):

    coordenadas = pd.read_excel(path, sheet_name="Coordenadas")
    comunicacion = pd.read_excel(path, sheet_name="Comunicacion")
    tipo_nodos = pd.read_excel(path, sheet_name="Tipo_nodos")
    tam_mina = pd.read_excel(path, sheet_name="Tamaño_mina")

    return coordenadas, comunicacion, tipo_nodos, tam_mina
