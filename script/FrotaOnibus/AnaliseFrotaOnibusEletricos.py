#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 15 17:09:28 2026

@author: bruno
"""

#%% IMPORTANTO OS PACOTES

import os
import pandas as pd
import matplotlib.pyplot as plt 
import matplotlib.dates as mdates
import seaborn as sns
#from scipy.stats import linregress
import numpy as np
from scipy.optimize import curve_fit
from sklearn.metrics import r2_score


#%%

# Caminhos para salvar Outputs
pastaOutputsEletricos = "/home/bruno/Gabriela/Lcqar/outputs/Frota Elétricos/Onibus Eletricos"

# cria a pasta caso não exista
os.makedirs(pastaOutputsEletricos, exist_ok=True)

#%% -------- MANIPULANDO OS ARQUIVOS

#Caminho e leitura do arquivo
dfOnibusE = pd.read_csv('/home/bruno/Gabriela/Lcqar/inputs/FrotaOnibusEletricosBR/VendaOnibusEletricosABVE.csv')

#Caminho e leitura arquivo ICCT para crescimento anual
dfICCTOnibusE = pd.read_csv('/home/bruno/Gabriela/Lcqar/inputs/FrotaOnibusEletricosBR/ICCTVendasOE.csv')

# Limpeza PRIMEIRO
dfOnibusE["MUNICIPIO"] = (
    dfOnibusE["MUNICIPIO"]
    .str.strip()
    .str.upper()
)

# Datetime
dfOnibusE["ANO_MÊS"] = pd.to_datetime(dfOnibusE["ANO_MÊS"])

dfOnibusE["ANO"] = dfOnibusE["ANO_MÊS"].dt.year

# Ordenação
dfOnibusE = dfOnibusE.sort_values(
    ["MUNICIPIO", "ANO_MÊS"]
).reset_index(drop=True)

# Soma acumulada
dfOnibusE["SOMA ACUMULADA"] = (
    dfOnibusE.groupby("MUNICIPIO")["VENDA"]
    .cumsum()
)





# Soma acumulada ICCT
dfICCTOnibusE["VENDA ACUMULADA"] = (
    dfICCTOnibusE["VENDAS ONIBUS (ICCT)"]
    .cumsum()
)

# TAXA CRESCIMENTO BR DADOS ICCT
dfICCTOnibusE["CRESCIMENTO (%) - ANO"] = (
    dfICCTOnibusE["VENDA ACUMULADA"]
    .pct_change() * 100
)

# salva o csv dentro dela
dfICCTOnibusE.to_csv(
    f"{pastaOutputsEletricos}/Onibus_BR_anual%ICCT.csv",
    index=False
)

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

#%%  ---------- TENDÊNCIA ANUAL FROTA ELÉTRICOS

dfOnibusE["ANO"] = dfOnibusE["ANO_MÊS"].dt.year

dfOEA = (
    dfOnibusE
    .groupby(["MUNICIPIO", "UF", "ANO"])["VENDA"]
    .sum()
    .reset_index()
)

# anos = range(
#     dfOEA["ANO"].min(),
#     dfOEA["ANO"].max() + 1
# )

# municipios = dfOEA["MUNICIPIO"].unique()

# index_completo = pd.MultiIndex.from_product(
#     [municipios, anos],
#     names=["MUNICIPIO", "ANO"]
# )
# dfOEA = (
#     dfOEA
#     .set_index(["MUNICIPIO", "ANO"])
#     .reindex(index_completo)
#     .reset_index()
# )


# dfOEA["VENDA"] = dfOEA["VENDA"].fillna(0)

# # Recolocar UF
# dfOEA["UF"] = (
#     dfOEA.groupby("MUNICIPIO")["UF"]
#     .ffill()
#     .bfill()
# )

dfOEA = dfOEA.sort_values(
    ["MUNICIPIO", "ANO"]
)

dfOEA["ACUMULADO"] = (
    dfOEA.groupby("MUNICIPIO")["VENDA"]
    .cumsum()
)

# dfOEA["CRESCIMENTO (%) - ANO"] = (
#     dfOEA.groupby("MUNICIPIO")["ACUMULADO"]
#     .pct_change() * 100
# )

# Loop pelos municípios
for cid in dfOEA["MUNICIPIO"].unique():
    
    # Filtra município
    df_mun = dfOEA[
        dfOEA["MUNICIPIO"] == cid
    ]
    
    # Pega a UF do município
    uf = df_mun["UF"].iloc[0]
    
    # Cria uma pasta para o estado
    pastaUF = f"{pastaOutputsEletricos}/{uf}"

    os.makedirs(pastaUF, exist_ok=True)

    # # Filtra os dados do estado
    # df_estado = dfFrotaConvencionalY[
    #     dfFrotaConvencionalY["UF"] == uf
    # ]
    # Salva o csv dentro da pasta do estado
    df_mun.to_csv(
        f"{pastaUF}/Onibus_eletricos%_{cid}.csv",index=False
    )

# 

dfBrasil = (
    dfOnibusE
    .groupby([ "ANO"])["VENDA"]
    .sum()
    .reset_index()
)

dfBrasil["VENDA ACUMULADA"] = (
    dfBrasil["VENDA"]
    .cumsum()
)

#[]	acessar/selecionar
#()	executar/chamar

dfBrasil["CRESCIMENTO (%) - ANO"] = (
    dfBrasil["VENDA ACUMULADA"]
    .pct_change() * 100
)

df_mun.to_csv(
     f"{pastaUF}/Onibus_eletricos%_{cid}.csv",index=False
 )

# salva o csv dentro dela
dfBrasil.to_csv(
    f"{pastaOutputsEletricos}/Onibus_BR_anual%.csv",
    index=False
)

# Estimativa 2033 e 2044
import sys

sys.path.append(
    "/home/bruno/Gabriela/Lcqar/script/FrotaOnibus"
)
from AnaliseFrotaOnibus import projecao_frota_total


anos_futuros, proj_log = projecao_frota_total()

# import AnaliseFrotaOnibus

# print(dir(AnaliseFrotaOnibus))
# # ---------------- CALCULAR K
Kel = 1397863

# ---------------- PREPARAR DADOS

xe = dfBrasil["ANO"].values

ye = dfBrasil["VENDA ACUMULADA"].values

x0 = xe.min()
#---------------- FUNÇÃO LOGÍSTICA

def logistico(xe, Kel, r, A):

    return Kel / (
        1 + A * np.exp(
            -r * (xe - x0)
        )
    )

# ---------------- AJUSTE DA CURVA

param_log_eletr, _ = curve_fit(

    logistico,

    xe,
    ye,

    # chute inicial
    p0=[Kel, 0.03, 10],
    
    bounds=(
        [Kel * 0.90, 0.001, 0],
        [Kel * 1.10, 5, 100000]
),
    # limites dos parâmetros
    # bounds=(
    #     [K * 0.95, 0.0001, 0],
    #     [K * 1.05, 1, 1000]
    # ),
    #tentativas até desistir
    maxfev=20000
)

# ---------------- RESULTADOS DO AJUSTE

K_fit, r_fit, A_fit = param_log_eletr

print("\nPARÂMETROS AJUSTADOS")
print("--------------------")
print("K =", round(K_fit))
print("r =", r_fit)
print("A =", A_fit)

# ---------------- AJUSTE NOS DADOS HISTÓRICOS

y_logEle = logistico(
    xe,
    *param_log_eletr
)

r2_logEle = r2_score(
    ye,
    y_logEle
)

print("\nR² Logístico:", round(r2_logEle, 4))

#---------------- PROJEÇÃO FUTURA

anos_futuros_ele = np.arange(
    xe.min(),
    2045
)

proj_log_ele = logistico(
    anos_futuros_ele,
    *param_log_eletr
)

#---------------- VALORES ESPECÍFICOS

frota_2033_ele = logistico(
    2033,
    *param_log_eletr
)

frota_2044_ele = logistico(
    2044,
    *param_log_eletr
)

print("\nPROJEÇÕES")
print("----------")
print("2033:", round(frota_2033_ele))
print("2044:", round(frota_2044_ele))

# ---------------- GRÁFICO

# fig, ax = plt.subplots(
#     figsize=(12,6)
# )

# # histórico
# ax.scatter(
#     xe,
#     ye,
#     label="Dados reais"
# )

# # curva logística
# ax.plot(
#     anos_futuros_ele,
#     proj_log_ele,
#     linewidth=2,
#     label="Regressão logística"
# )

# # linhas verticais
# ax.axvline(
#     2033,
#     linestyle="--"
# )

# ax.axvline(
#     2044,
#     linestyle="--"
# )

# ax.set_xlabel("Ano")

# ax.set_ylabel("Frota de ônibus")

# ax.set_title(
#     "Projeção da Frota Convencional"
# )

# ax.legend()

# ax.grid(True)

# plt.show()


fig, ax = plt.subplots(
    figsize=(12,6)
)

# ---------------- ELÉTRICOS HISTÓRICOS

ax.scatter(
    xe,
    ye,
    label="Elétricos - Histórico"
)

# ---------------- ELÉTRICOS PROJETADOS

ax.plot(
    anos_futuros_ele,
    proj_log_ele,
    linewidth=2,
    label="Elétricos - Logístico"
)

# ---------------- FROTA TOTAL PROJETADA

ax.plot(
    anos_futuros,
    proj_log,
    linewidth=2,
    linestyle="--",
    label="Frota Total Projetada"
)

# ---------------- LINHAS VERTICAIS

ax.axvline(
    2033,
    linestyle=":"
)

ax.axvline(
    2044,
    linestyle=":"
)

# ---------------- LABELS

ax.set_xlabel("Ano")

ax.set_ylabel("Frota de ônibus")

ax.set_title(
    "Projeção da Frota Elétrica"
)

ax.legend()

ax.grid(True)

plt.show()



# -------------TENDENCIA POR UF ANO

# ÚLTIMO ACUMULADO DE CADA MUNICÍPIO NO ANO
dfMunicipioAno = (
    dfOnibusE
    .sort_values("ANO_MÊS")
    .groupby(["UF", "MUNICIPIO", "ANO"])["SOMA ACUMULADA"]
    .last()
    .reset_index()
)

# SOMA DOS MUNICÍPIOS POR UF NO ANO
dfUF = (
    dfMunicipioAno
    .groupby(["UF", "ANO"])["SOMA ACUMULADA"]
    .sum()
    .reset_index(name="TOTAL_UF")
)

# VARIAÇÃO ANUAL
dfUF["VARIAÇÃO (%)"] = (
    dfUF
    .groupby("UF")["TOTAL_UF"]
    .pct_change() * 100
)


dfFrotaEletricosUFY = (
    dfOnibusE
    .groupby(["UF", "ANO_MÊS"])["SOMA ACUMULADA"]
    .last()
    .reset_index())

dfFrotaEletricosUFY["VARIAÇÂO (%)"] = (dfFrotaEletricosUFY
                                        .groupby("UF")["TOTAL"]
    .pct_change() * 100)

