#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  2 09:02:57 2026

@author: bruno
"""

#%% Pacotes 

import pandas as pd
import glob
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import numpy as np
import seaborn as sns
#%%
#Caminho e leitura do arquivo
dfmun = pd.read_csv('/home/bruno/Gabriela/Lcqar/outputs/Frota Elétricos/Onibus Convencionais/dfFrotaMun.csv')

# Selecionando colunas necessárias
dfOnibusMun = dfmun[['UF','MUNICIPIO','MICRO-ONIBUS','ONIBUS','ANO_MÊS']]

# Adicionando coluna Soma 
dfOnibusMun['TOTAL'] = dfOnibusMun['MICRO-ONIBUS'] + dfOnibusMun['ONIBUS']

dfOnibusMun = dfOnibusMun.sort_values(["UF", "ANO_MÊS"])

dfCaminhoesMun = dfmun[['UF','MUNICIPIO','CAMINHAO','CAMINHAO TRATOR','ANO_MÊS']]

# Adicionando coluna Soma 
dfCaminhoesMun['TOTAL'] = dfCaminhoesMun['CAMINHAO'] + dfCaminhoesMun['CAMINHAO TRATOR']


#%% FROTA POR UF

# Fazendo a efetiva soma da coluna SOMA que junta Onibus com Micro-onibus
dfOnibusUF= (
    dfOnibusMun.groupby(["UF", "ANO_MÊS"])["TOTAL"]
    .sum()
    .reset_index()
)

# Transformando em datetime
dfOnibusUF["ANO_MÊS"] = pd.to_datetime(dfOnibusUF["ANO_MÊS"].astype(str))

# Criar coluna Ano
dfOnibusUF["ANO"] = dfOnibusUF["ANO_MÊS"].dt.year

# Garantir ordem 
dfOnibusUF = dfOnibusUF.sort_values(["UF", "ANO_MÊS"])


#%%
# Verificando pro brasil 
dfUF_Ano = (
    dfOnibusUF
    .groupby(["UF", "ANO"])["TOTAL"]
    .last()
    .reset_index()
)

# Depois: soma das UFs no Brasil
dfBrasil = (
    dfUF_Ano
    .groupby("ANO")["TOTAL"]
    .sum()
    .reset_index()
)


frota_2030 = frota_2025 * 1.056
frota_2035 = frota_2025 * 1.129



#print(dfBrasil)
#%% Plot

fig, ax = plt.subplots(figsize=(10,6))

ax.plot(
    dfBrasil["ANO"],
    dfBrasil["TOTAL"],
    marker="o"
)

ax.set_xlabel("Ano")
ax.set_ylabel("N° Ônibus")
ax.set_title("Frota de Ônibus Convencional - Brasil")

ax.grid(True)

plt.show()

