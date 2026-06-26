#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 26 15:42:43 2026

Objetivo desse script é filtrar os resultados do rectifyUFs até 2025
(para o caso de ter baixado para 2026) e então agrupar com o
histórico que está no https://arquivos.lcqar.ufsc.br/data/databases/stations/MQAr/

@author: gabriela
"""

# Pacotes
from pathlib import Path
import pandas as pd
import requests
from bs4 import BeautifulSoup
import os

#%% Fazendo o filtro para 2025

basePath = Path("/home/bruno/Gabriela/Lcqar/AvaliacaoEstacoes/outputs/Resultados Brutos/")

dataInicio = "2025-01-01"
dataFim = "2026-01-01"

data_inicio = pd.to_datetime
data_fim = pd.to_datetime

for ufPath in basePath.iterdir():
    if ufPath.is_dir():
        print(ufPath)
    
    for poluentePath in ufPath.iterdir():
        if poluentePath.is_dir():
            print(poluentePath)
            
        for file in poluentePath.glob("*csv"):
            print(f"Lendo: {file}")
            
            df = pd.read_csv(file)
    # garante que existe coluna de data (ajuste o nome se necessário)
            if "DATETIME" in df.columns:
                df["DATETIME"] = pd.to_datetime(df["DATETIME"])

                # aplica filtro de data
                df_filtrado = df[
                    (df["DATETIME"] >= dataInicio) &
                    (df["DATETIME"] < dataFim)
                ]

                # df_filtrado = df[
                #     (df["DATETIME"] >= "2023-01-01") &
                #     (df["DATETIME"] < "2024-01-01")
                # ]

                # aqui você pode salvar ou processar
                df_filtrado.to_csv(file, index=False)
                print(f"Atualizado: {file}")

#%% Juntar os arquivos antigos (histórico) com o de 2025

base_url = "https://arquivos.lcqar.ufsc.br/data/databases/stations/MQAr/"

poluentes = [
    "CO",
    "NO2",
    "PTS",
    "O3",
    "MP10",
    "MP25",
    "SO2"
]

estacoes = {
    "CO": ['BA0001ND007',
           'BA0002ND007',
           'BA0003ND007',
           'BA0004ND007',
           'BA0005ND007',
           'BA0006ND007',
           'BA0007ND007',
           'BA0008ND007',
           'BA0009ND007',
           'BA0010ND007',
           'BA0011ND007',
           'BA0012ND007',
           'BA0013ND007',
           'BA0014ND007',
           'MA0001RA007',
           'MA0002RA007',
           'MA0003RA007',
           'MA0004RA007',
           'MA0005RA007',
           'MA0006RA007'  
           ],
    "NO2": ['BA0001ND007',
           'BA0002ND007',
           'BA0003ND007',
           'BA0004ND007',
           'BA0005ND007',
           'BA0006ND007',
           'BA0007ND007',
           'BA0008ND007',
           'BA0009ND007',
           'BA0010ND007',
           'BA0011ND007',
           'BA0012ND007',
           'BA0013ND007',
           'BA0014ND007',
           'MA0001RA007',
           'MA0002RA007',
           'MA0003RA007',
           'MA0004RA007',
           'MA0005RA007',
           'MA0006RA007'  
           ],
    "PM10": ['BA0001ND007',
           'BA0002ND007',
           'BA0003ND007',
           'BA0004ND007',
           'BA0005ND007',
           'BA0006ND007',
           'BA0007ND007',
           'BA0008ND007',
           'BA0009ND007',
           'BA0010ND007',
           'BA0011ND007',
           'BA0012ND007',
           'BA0013ND007',
           'BA0014ND007',
           'MA0001RA007',
           'MA0002RA007',
           'MA0003RA007',
           'MA0004RA007',
           'MA0005RA007',
           'MA0006RA007'  
           ],
    "O3": ['BA0001ND007',
           'BA0002ND007',
           'BA0003ND007',
           'BA0004ND007',
           'BA0005ND007',
           'BA0006ND007',
           'BA0007ND007',
           'BA0008ND007',
           'BA0009ND007',
           'BA0010ND007',
           'BA0011ND007',
           'BA0012ND007',
           'BA0013ND007',
           'BA0014ND007',
           'MA0001RA007',
           'MA0002RA007',
           'MA0003RA007',
           'MA0004RA007',
           'MA0005RA007',
           'MA0006RA007'  
           ]
}

# arquivos_por_poluente = {}

# for pol in poluentes:

#     url = base_url + pol + "/"

#     html = requests.get(url).text
#     soup = BeautifulSoup(html, "html.parser")

#     arquivos = []

#     for link in soup.find_all("a"):
#         href = link.get("href")

#         if href.endswith(".csv"):
#             arquivos.append(href)

#     arquivos_por_poluente[pol] = arquivos
# print(arquivos_por_poluente["CO"])


base_url = "https://arquivos.lcqar.ufsc.br/data/databases/stations/MQAr/"

for poluente, lista_estacoes in estacoes.items():

    pasta = f"Historico/{poluente}"
    os.makedirs(pasta, exist_ok=True)

    print(f"\nBaixando {poluente}")

    for estacao in lista_estacoes:

        url = f"{base_url}{poluente}/{estacao}.csv"

        try:
            r = requests.get(url, timeout=20)

            if r.status_code == 200:

                with open(os.path.join(pasta, f"{estacao}.csv"), "wb") as f:
                    f.write(r.content)

                print(f"✓ {estacao}")

            else:
                print(f"✗ {estacao} (HTTP {r.status_code})")

        except Exception as e:
            print(f"Erro em {estacao}: {e}")