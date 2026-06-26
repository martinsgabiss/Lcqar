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

