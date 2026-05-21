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

from scipy.stats import linregress
import numpy as np

#%% Manipulando os arquivos excel

# 1. Defina o caminho da pasta onde estão os arquivos
#pastaFuel = '/home/bruno/Gabriela/Lcqar/inputs/FrotaOnibusEletricosBR/4.FrotaPorMunicipioECombustivel'
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

#print(dfFrotaMun.columns)

# Selecionando colunas necessárias
dfOnibusMun = dfFrotaMun[['UF','MUNICIPIO','MICRO-ONIBUS','ONIBUS','ANO_MÊS']]

# Adicionando coluna Soma 
dfOnibusMun['TOTAL'] = dfOnibusMun['MICRO-ONIBUS'] + dfOnibusMun['ONIBUS']

# Fazendo a efetiva soma da coluna SOMA que junta Onibus com Micro-onibus
dfOnibusUF= (
    dfOnibusMun.groupby(["UF", "ANO_MÊS"])["TOTAL"]
    .sum()
    .reset_index()
)

# Transformando em datetime
dfOnibusUF["ANO_MÊS"] = pd.to_datetime(dfOnibusUF["ANO_MÊS"].astype(str))

# Dicionário completo das regiões
regioes = {

    # Norte
    "AC": "Norte",
    "AP": "Norte",
    "AM": "Norte",
    "PA": "Norte",
    "RO": "Norte",
    "RR": "Norte",
    "TO": "Norte",

    # Nordeste
    "AL": "Nordeste",
    "BA": "Nordeste",
    "CE": "Nordeste",
    "MA": "Nordeste",
    "PB": "Nordeste",
    "PE": "Nordeste",
    "PI": "Nordeste",
    "RN": "Nordeste",
    "SE": "Nordeste",

    # Centro-Oeste
    "DF": "Centro-Oeste",
    "GO": "Centro-Oeste",
    "MT": "Centro-Oeste",
    "MS": "Centro-Oeste",

    # Sudeste
    "ES": "Sudeste",
    "MG": "Sudeste",
    "RJ": "Sudeste",
    "SP": "Sudeste",

    # Sul
    "PR": "Sul",
    "RS": "Sul",
    "SC": "Sul"
}

# Criar coluna de região e preencher com respectiva região
dfOnibusUF["REGIÃO"] = dfOnibusUF["UF"].map(regioes)

# Criar coluna Ano
dfOnibusUF["ANO"] = dfOnibusUF["ANO_MÊS"].dt.year

# Garantir ordem 
dfOnibusUF = dfOnibusUF.sort_values(["UF", "ANO_MÊS"])

# Criar coluna e respectivo calculo entre linhas por UF
# Aqui é quanto a frota variou em relação ao mês anterior.
dfOnibusUF["VARIAÇÂO (%)"] = (dfOnibusUF.groupby("UF")["TOTAL"]
    .pct_change() * 100)


#%% -------------- Criar gráfico COM TODAS AS REGIÕES

# Somar TOTAL por região e mês
dfRegiao = (
    dfOnibusUF
    .groupby(["REGIÃO", "ANO_MÊS"])["TOTAL"]
    .sum()
    .reset_index()
) 

fig, ax = plt.subplots(figsize=(14,7))

# Plotar cada região
for regiao in dfRegiao["REGIÃO"].unique():

    dados = dfRegiao[dfRegiao["REGIÃO"] == regiao]

    ax.plot(dados["ANO_MÊS"],dados["TOTAL"],label=regiao)
    
    # Configuração do eixo X
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(
        mdates.DateFormatter('%Y'))
    
    # Marquinhas mensais
    ax.xaxis.set_minor_locator(mdates.MonthLocator())
    #ax.set_yscale("log")
    # Ajustes visuais
    plt.xlabel("Ano")
    plt.ylabel("Total de Ônibus")
    plt.title("Frota de Ônibus por Região do Brasil")
    
    plt.legend(title="Região")
    
    plt.grid(True)
    
    plt.show()
# Teste com log

fig, ax = plt.subplots(figsize=(14,7))
for regiao in dfRegiao["REGIÃO"].unique():

    dadoslog = dfRegiao[dfRegiao["REGIÃO"] == regiao]

    ax.plot(dadoslog["ANO_MÊS"],dadoslog["TOTAL"],label=regiao)
    
    # Configuração do eixo X
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(
        mdates.DateFormatter('%Y'))
    
    # Marquinhas mensais
    ax.xaxis.set_minor_locator(mdates.MonthLocator())
    ax.set_yscale("log")
    # Ajustes visuais
    plt.xlabel("Ano")
    plt.ylabel("Total de Ônibus")
    plt.title("Frota de Ônibus por Região do Brasil")
    
    plt.legend(title="Região")
    
    plt.grid(True)
    
    plt.show()


#%% -------------- Criar gráfico POR ESTADO

fig, ax = plt.subplots(figsize=(12,6))

for estado in dfOnibusUF["UF"].unique():

    dados_estado = dfOnibusUF[dfOnibusUF["UF"] == estado]

    ax.plot(
        dados_estado["ANO_MÊS"],
        dados_estado["TOTAL"],
        label=estado
    )

    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.set_minor_locator(mdates.MonthLocator())
    
    #ax.set_yscale("log")
    
    plt.legend()
    plt.xlabel("Ano")
    plt.ylabel("Total")
    plt.title("Frota de Ônibus por Estado")
    
    plt.show()

#teste log - Devo ajustar legenda e cores!

fig, ax = plt.subplots(figsize=(12,6))

for estado in dfOnibusUF["UF"].unique():

    dados_estadolog = dfOnibusUF[dfOnibusUF["UF"] == estado]

    ax.plot(
        dados_estadolog["ANO_MÊS"],
        dados_estadolog["TOTAL"],
        label=estado
    )

    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.set_minor_locator(mdates.MonthLocator())
    
    ax.set_yscale("log")
    
    plt.legend()
    plt.xlabel("Ano")
    plt.ylabel("Total")
    plt.title("Frota de Ônibus por Estado")
    
    plt.show()

#%% ---------- Criar gráfico POR REGIÃO

for r in dfOnibusUF["REGIÃO"].unique():

    fig, ax = plt.subplots(figsize=(12,6))

    dadosR = dfOnibusUF[
        dfOnibusUF["REGIÃO"] == regiao
    ]

    for estado in dadosR["UF"].unique():

        dadosUF = dadosR[
            dadosR["UF"] == estado
        ]

        ax.plot(
            dadosUF["ANO_MÊS"],
            dadosUF["TOTAL"],
            label=estado
        )
        #ax.set_yscale("log")
        
        ax.set_title(f"Total de Ônibus - {regiao}")
    
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(
            mdates.DateFormatter('%Y')
        )
        ax.xaxis.set_minor_locator(
            mdates.MonthLocator()
        )
    
        ax.legend()
    
        plt.show()

#%% ---------- Tendência por UF

# Regressão Linear Tendência UF
Regr = []

for est in dfOnibusUF["UF"].unique():
    
    dadosEst = (
        dfOnibusUF[
            dfOnibusUF["UF"] == est
        ]
        .sort_values("ANO_MÊS")
    )
    # Série temporal do estado
    serie = dadosEst['TOTAL'].dropna()
    # Tempo em formato numérico
    x = range(len(serie))

    # Valores da série
    y = serie.values

    # Regressão linear
    regressao = linregress(x, y) #crescimento médio mensal 

    valor_inicial = y[0] #o primeiro mês de dado, no caso jan2021

    valor_final = y[-1]
    
    meses = len(y) - 1
    
    if valor_inicial > 0 and meses > 0:
    
        crescimento_mensal = (
            (
                valor_final / valor_inicial
            ) ** (1 / meses) - 1
        ) * 100
    
    else:
    
        crescimento_mensal = np.nan
    
    # slope_percentual = (
    #     regressao.slope / valor_inicial
    # ) * 100

    Regr.append({"UF": est,
        "Tendência (Onibus/Mês)": regressao.slope, #intensidade
        "Crescimento (% Mês)": crescimento_mensal,
        #"Pvalor": regressao.pvalue, #tendência significativa? 
        #"R2": regressao.rvalue**2 #confiabilidade
        })
   
# Criar DataFrame final
dfTrendRL = pd.DataFrame(Regr)

# --------- VARIAÇÃO ANUAL UF

dfTrendAUF = (
    dfOnibusUF
    .sort_values("ANO_MÊS")
    .groupby(["UF", "ANO"])["TOTAL"]
    .first()
    .reset_index()
)

dfTrendAUF["CRESCIMENTO (%)"] = (
    dfTrendAUF
    .groupby("UF")["TOTAL"]
    .pct_change() * 100
)

#%% ------- Tendência por município FROTA ONIBUS

# Transformando em datetime a coluna ANO_MES
dfOnibusMun["ANO_MÊS"] = pd.to_datetime(dfOnibusMun["ANO_MÊS"].astype(str))

RegrMun = []

for mun in dfOnibusMun["MUNICIPIO"].unique():

    dados_mun = (
        dfOnibusMun[
            dfOnibusMun["MUNICIPIO"] == mun
        ]
        .sort_values("ANO_MÊS")
    )

    serie = dados_mun["TOTAL"].dropna()

    x = range(len(serie))
    y = serie.values

    regressao = linregress(x, y)

    valor_inicial = y[0]

    valor_final = y[-1]
    
    meses = len(y) - 1
    
    if valor_inicial > 0 and meses > 0:
    
        crescimento_mensal = (
            (
                valor_final / valor_inicial
            ) ** (1 / meses) - 1
        ) * 100
    
    else:
    
        crescimento_mensal = np.nan

    # slope_percentual = (
    #     regressao.slope / valor_inicial
    # ) * 100
    
    uf = dados_mun["UF"].iloc[0]
    
    RegrMun.append({
        "Municipio": mun,
        "UF": uf,
        "Tendência (Ônibus/Mês)": regressao.slope,
        "Crescimento Mensal Médio (%)": crescimento_mensal,
        "R2": regressao.rvalue**2
    })

dfTrendMunicipio = pd.DataFrame(RegrMun)

# TESTE VERIFICAÇÃO SE A SERIE ESTÁ ACUMULANDO - MUNICIPIO ESPECÍFICO
# Escolher município
municipio = "ACRELANDIA"

# Filtrar município e ordenar pela data
serie_mun = (
    dfOnibusMun[dfOnibusMun["MUNICIPIO"] == municipio]
    .sort_values("ANO_MÊS")
)

print(serie_mun)

