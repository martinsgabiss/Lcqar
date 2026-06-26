#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 11 12:13:51 2026

@author: bruno
"""
#%% Pacotes

import pandas as pd
import glob
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# from scipy.stats import linregress
import numpy as np
import seaborn as sns

from scipy.optimize import curve_fit
from sklearn.metrics import r2_score


#%% Pastas e caminhos

# Caminhos para salvar Outputs
pastaOutputsConvencional = "/home/bruno/Gabriela/Lcqar/outputs/Frota Elétricos/Onibus Convencionais"

# cria a pasta caso não exista
os.makedirs(pastaOutputsConvencional, exist_ok=True)

# Caminhos para figuras
pastaFigurasConvencional = '/home/bruno/Gabriela/Lcqar/figuras/Onibus Eletricos/Onibus Convencionais'

# cria a pasta caso não exista
os.makedirs(pastaFigurasConvencional, exist_ok=True)


#%% Manipulando os arquivos excel

# 1. Defina o caminho da pasta onde estão os arquivos
pastaTipoFrota = '/home/bruno/Gabriela/Lcqar/inputs/FrotaOnibusEletricosBR/2.FrotaPorMunicipio'


def carregar_arquivos_frota(pasta, header=0):

    # 2. Glob para listar todos os arquivos .xlsx
    arquivos_xls = glob.glob(
        os.path.join(pasta, "**", "*.xls"),
        recursive=True
    )
    
    arquivos_xlsx = glob.glob(
        os.path.join(pasta, "**", "*.xlsx"),
        recursive=True
    )

    arquivos = arquivos_xls + arquivos_xlsx
    
    print(f'Total de arquivos encontrados: {len(arquivos)}')
    
    # 3. Crie uma lista vazia para armazenar os DataFrames
    lista = []
    
    # 4. Loop para ler cada arquivo
    for arquivo in arquivos:

        ano_mes = os.path.basename(os.path.dirname(arquivo))
        
        # ignora arquivos fora de pastas YYYY-MM
        if '-' not in ano_mes:
            continue
           
        df = pd.read_excel(arquivo, header=2)
 
            # limpa nomes de colunas
        df.columns = df.columns.str.strip()
        df = df.loc[:, ~df.columns.duplicated()]
            
       
        df['ANO_MÊS'] = ano_mes
        
        lista.append(df)

    # 5. Concatenar todos os DataFrames em um único
    df_final = pd.concat(lista, ignore_index=True)
    
    return df_final

# #Conferindo se tem nan
# print(df_final['ano_mes'].unique())
# df_final.sample(10)

dfFrotaMun = carregar_arquivos_frota(pastaTipoFrota)

dfFrotaMun.to_csv(f"{pastaOutputsConvencional}/dfFrotaMun.csv",
    index=False
    # encoding="utf-8-sig"
)

#print(dfFrotaMun.columns)

# Selecionando colunas necessárias
dfOnibusMun = dfFrotaMun[['UF','MUNICIPIO','MICRO-ONIBUS','ONIBUS','ANO_MÊS']]

# Adicionando coluna Soma 
dfOnibusMun['TOTAL'] = dfOnibusMun['MICRO-ONIBUS'] + dfOnibusMun['ONIBUS']

dfOnibusMun = dfOnibusMun.sort_values(["UF", "ANO_MÊS"])

print(sorted(dfOnibusMun['ANO_MÊS'].unique().tolist()))

# df = pd.read_excel(
#     "/home/bruno/Gabriela/Lcqar/inputs/FrotaOnibusEletricosBR/2.FrotaPorMunicipio/2015/2015-12/2015-12.xls")

# FROTA POR UF

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

# Criar coluna e respectivo calculo entre linhas por UF
# Aqui é quanto a frota variou em relação ao mês anterior.
dfOnibusUF["VARIAÇÂO (%)"] = (dfOnibusUF.groupby("UF")["TOTAL"]
    .pct_change() * 100)


# verificando pro brasil 
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


# Crescimento percentual anual
dfBrasil["VARIAÇÃO (%)"] = (
    dfBrasil["TOTAL"]
    .pct_change() * 100
)

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
#%% -------------- FROTA ONIBUS CONVENCIONAL POR ANO E UF
# dfFrotaConvencionalY = (dfOnibusUF.groupby(
#     ["UF", "ANO"])["TOTAL"].
#     sum().
#     reset_index()
#     )

dfFrotaConvencionalY = (
    dfOnibusUF
    .groupby(["UF", "ANO"])["TOTAL"]
    .last()
    .reset_index())

dfFrotaConvencionalY["VARIAÇÂO (%)"] = (dfFrotaConvencionalY
                                        .groupby("UF")["TOTAL"]
    .pct_change() * 100)

# salva o csv dentro dela
dfFrotaConvencionalY.to_csv(
    f"{pastaOutputsConvencional}/Onibus_convencional_UF_anual%.csv",
    index=False
)

# Loop pelos estados
for uf in dfFrotaConvencionalY["UF"].unique():

    # Cria uma pasta para o estado
    pastaUF = f"{pastaOutputsConvencional}/{uf}"

    os.makedirs(pastaUF, exist_ok=True)

    # Filtra os dados do estado
    df_estado = dfFrotaConvencionalY[
        dfFrotaConvencionalY["UF"] == uf
    ]

    # Salva o csv dentro da pasta do estado
    df_estado.to_csv(
        f"{pastaUF}/Onibus_convencional%_{uf}.csv",index=False
    )
        
#%% -------------- Criar gráfico POR ESTADO

cores_40 = sns.color_palette("tab20", 20) + sns.color_palette("tab20b", 20)

fig, ax = plt.subplots(figsize=(12,6))

for i,estado in enumerate(dfOnibusUF["UF"].unique()):

    dados_estadolog = dfOnibusUF[dfOnibusUF["UF"] == estado]

    ax.plot(
        dados_estadolog["ANO_MÊS"],
        dados_estadolog["TOTAL"],
        label=estado,
        color=cores_40[i % len(cores_40)]
    )

    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.set_minor_locator(mdates.MonthLocator())
    
    ax.set_yscale("log")
    
   # plt.legend()
    plt.legend(
        loc='center left',
        bbox_to_anchor=(1.02, 0.5),
        ncol=1,
        fontsize=9,
        frameon=False
    )
    
    plt.xlabel("Ano")
    plt.ylabel("N° Ônibus")
    plt.title("Frota de Ônibus - UF")
    
    #plt.show()
    
    # salva figura
    fig.savefig(os.path.join(
        pastaFigurasConvencional,
     "frota_onibus_convencional_porUF.png"),
    dpi=300,
    bbox_inches="tight"
)

#%% Estimativa BR

dfPop = pd.read_excel('/home/bruno/Gabriela/Lcqar/inputs/FrotaOnibusEletricosBR/ProjeçãoCrescimentoPopulacionalIBGE.xlsx')

# ---------------- JUNTAR FROTA + POPULAÇÃO

dfProj = pd.merge(
    dfBrasil,
    dfPop[["ANO", "POP_T"]],
    on="ANO",
    how="inner"
)

#---------------- CALCULAR ÔNIBUS POR HABITANTE

dfProj["ONIBUS_HAB"] = (
    dfProj["TOTAL"] / dfProj["POP_T"]
)

# ---------------- MAIOR TAXA HISTÓRICA
#localiza qual o valor maior dentre os disponíveis
taxa_max = dfProj["ONIBUS_HAB"].max()

# ---------------- DEFINIR LIMITE PLAUSÍVEL

# margem de 20% acima da maior taxa histórica
taxa_limite = taxa_max * 1.20


# ---------------- POPULAÇÃO FUTURA (2044)

pop_2044 = (
    dfPop[dfPop["ANO"] == 2044]["POP_T"]
    .iloc[0]
)

# ---------------- CALCULAR K

K = pop_2044 * taxa_limite

# ---------------- PREPARAR DADOS

x = dfProj["ANO"].values

y = dfProj["TOTAL"].values

x0t = x.min()

def projecao_frota_total():
    
    
    #---------------- FUNÇÃO LOGÍSTICA
    
    def logistico(x, K, r, A):
    
        return K / (
            1 + A * np.exp(
                -r * (x - x0t)
            )
        )
    
    # ---------------- AJUSTE DA CURVA
    
    param_log_total, _ = curve_fit(
    
        logistico,
    
        x,
        y,
    
        # chute inicial
        p0=[K, 0.03, 10],
    
        # limites dos parâmetros
        bounds=(
            [K * 0.95, 0.0001, 0],
            [K * 1.05, 1, 1000]
        ),
        #tentativas até desistir
        maxfev=20000
    )
    
    # ---------------- RESULTADOS DO AJUSTE
    
    K_fit, r_fit, A_fit = param_log_total
    
    print("\nPARÂMETROS AJUSTADOS")
    print("--------------------")
    print("K =", round(K_fit))
    print("r =", r_fit)
    print("A =", A_fit)
    
    # ---------------- AJUSTE NOS DADOS HISTÓRICOS
    
    y_log = logistico(
        x,
        *param_log_total
    )
    
    r2_log = r2_score(
        y,
        y_log
    )
    
    print("\nR² Logístico:", round(r2_log, 4))
    
    #---------------- PROJEÇÃO FUTURA
    
    anos_futuros = np.arange(
        x.min(),
        2045
    )
    
    proj_log = logistico(
        anos_futuros,
        *param_log_total
    )
    
    #---------------- VALORES ESPECÍFICOS
    
    frota_2033 = logistico(
        2033,
        *param_log_total
    )
    
    frota_2044 = logistico(
        2044,
        *param_log_total
    )
    
    print("\nPROJEÇÕES")
    print("----------")
    print("2033:", round(frota_2033))
    print("2044:", round(frota_2044))
    return anos_futuros, proj_log

#projecao_frota_total= anos_futuros,proj_log
anos_futuros, proj_log= projecao_frota_total()

# ---------------- GRÁFICO

fig, ax = plt.subplots(
    figsize=(12,6)
)

# histórico
ax.scatter(
    x,
    y,
    label="Dados reais"
)

# curva logística
ax.plot(
    anos_futuros,
    proj_log,
    linewidth=2,
    label="Regressão logística"
)

# linhas verticais
ax.axvline(
    2033,
    linestyle="--"
)

ax.axvline(
    2044,
    linestyle="--"
)

ax.set_xlabel("Ano")

ax.set_ylabel("Frota de ônibus")

ax.set_title(
    "Projeção da Frota Convencional"
)

ax.legend()

ax.grid(True)

plt.show()


