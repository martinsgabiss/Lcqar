#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 15 17:09:28 2026

@author: bruno
"""

#%% IMPORTANTO OS PACOTES

#import os
import pandas as pd
import matplotlib.pyplot as plt 
import matplotlib.dates as mdates
import seaborn as sns
from scipy.stats import linregress
import numpy as np

#%% -------- MANIPULANDO OS ARQUIVOS

#Caminho e leitura do arquivo
dfOnibusE = pd.read_csv('/home/bruno/Gabriela/Lcqar/inputs/FrotaOnibusEletricosBR/VendaOnibusEletricos.csv')

# Transformando em datetime
dfOnibusE["ANO_MÊS"] = pd.to_datetime(dfOnibusE["ANO_MÊS"].astype(str))


# Garantir ordem 
dfOnibusE = dfOnibusE.sort_values(["MUNICIPIO", "ANO_MÊS"])

# Soma acumulada por município
dfOnibusE ["SOMA ACUMULADA"] = (
    dfOnibusE.groupby("MUNICIPIO")["VENDA"]
    .cumsum())

#print(dfOnibusE["MUNICIPIO"].unique())

# Limpando os nomes que estavam com espaçamento indevido
dfOnibusE["MUNICIPIO"] = ( dfOnibusE["MUNICIPIO"]
    .str.strip()
    .str.upper())


#%% ----------- PLOT POR MUNICÍPIO COM FROTA ELÉTRICA

fig, ax = plt.subplots(figsize=(22,10))

# Gera uma lista com 40 cores distintas usando a paleta tab20 e suas variantes
cores_40 = sns.color_palette("tab20", 20) + sns.color_palette("tab20b", 20)

for i, m in enumerate(dfOnibusE["MUNICIPIO"].unique()):

    dadosMunicipios = dfOnibusE[
        dfOnibusE["MUNICIPIO"] == m
    ]

    ax.plot(
        dadosMunicipios["ANO_MÊS"],
        dadosMunicipios["SOMA ACUMULADA"],
        label=m,
        color=cores_40[i % len(cores_40)]
    )

ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

ax.set_yscale("log")

plt.xlabel("Ano")
plt.ylabel("Total")
plt.title("Frota de Ônibus Elétricos por Município")

plt.subplots_adjust(right=0.8)

plt.legend(
    loc='center left',
    bbox_to_anchor=(1.02, 0.5),
    ncol=1,
    fontsize=6,
    frameon=False
)

plt.show()

#%%------------ TENDÊNCIA FROTA ELÉTRICOS MENSAL

# COM REGRESSÃO E TAXA COMPOSTA MÉDIA
RegrMunE = []

for muni in dfOnibusE["MUNICIPIO"].unique():

    eletr_mun = (
        dfOnibusE[
            dfOnibusE["MUNICIPIO"] == muni
        ]
        .sort_values("ANO_MÊS")
    )

    serie = eletr_mun["SOMA ACUMULADA"].dropna()

    #x = range(len(serie))
    x = (
    eletr_mun["ANO_MÊS"].dt.year * 12
    + eletr_mun["ANO_MÊS"].dt.month
)
    y = serie.values

    regressao = linregress(x, y)

    valor_inicial = y[0]
    valor_final = y[-1]
    
 # quantidade de meses do período
    meses = x.iloc[-1] - x.iloc[0]

    # crescimento percentual médio mensal
    if valor_inicial > 0 and meses > 0:

        crescimento_mensal = (
            (
                valor_final / valor_inicial
            ) ** (1 / meses) - 1
        ) * 100

    else:

        crescimento_mensal = np.nan

    uf = eletr_mun["UF"].iloc[0]
    
    # RegrMunE.append({
    #     "Municipio": muni,
    #     "UF": uf,
    #     "Tendência (Ônibus/Mês)": regressao.slope,
    #     "Tendência (% Mês)": slope_percentual,
    #     "R2": regressao.rvalue**2
    # })

    RegrMunE.append({
        "Municipio": muni,
        "UF": uf,
        "Tendência (Ônibus/Mês)": regressao.slope,
        "Crescimento Médio Mensal (%)": crescimento_mensal,
        #"R²": regressao.rvalue**2
    })
#qual a tendência média de crescimento ao longo do período observado daquele município”.
#crescimento médio de ônibus por mês real.
dfTrendEMun = pd.DataFrame(RegrMunE)

#%%  ---------- TENDÊNCIA ANUAL FROTA ELÉTRICOS

dfOnibusE["ANO"] = dfOnibusE["ANO_MÊS"].dt.year

dfOEA = (
    dfOnibusE
    .groupby(["MUNICIPIO", "UF", "ANO"])["VENDA"]
    .sum()
    .reset_index()
)

dfOEA = dfOEA.sort_values(
    ["MUNICIPIO", "ANO"]
)

dfOEA["ACUMULADO"] = (
    dfOEA.groupby("MUNICIPIO")["VENDA"]
    .cumsum()
)

dfOEA["CRESCIMENTO (%) - ANO"] = (
    dfOEA.groupby("MUNICIPIO")["ACUMULADO"]
    .pct_change() * 100
)

# COM REGRESSÃO E TAXA COMPOSTA MÉDIA

RegrAnual = []

for muni in dfOEA["MUNICIPIO"].unique():

    dados = (
        dfOEA[
            dfOEA["MUNICIPIO"] == muni
        ]
        .sort_values("ANO")
    )

    x = dados["ANO"]
    y = dados["ACUMULADO"]

    regressao = linregress(x, y)

    valor_inicial = y.iloc[0]
    valor_final = y.iloc[-1]

    anos = x.iloc[-1] - x.iloc[0]

    if valor_inicial > 0 and anos > 0:

        crescimento_anual = (
            (
                valor_final / valor_inicial
            ) ** (1 / anos) - 1
        ) * 100

    else:

        crescimento_anual = np.nan

    RegrAnual.append({

        "Municipio": muni,

        "UF": dados["UF"].iloc[0],

        "Tendência (Ônibus/Ano)": regressao.slope,

        "Crescimento Médio Anual (%)": crescimento_anual,

        #"R²": regressao.rvalue**2
    })

dfTrendAnual = pd.DataFrame(RegrAnual)

#testar por estado com somatorio agrupado tbm
