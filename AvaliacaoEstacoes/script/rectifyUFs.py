#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  9 10:35:20 2026

@author: Gabriela
"""

#%%

import pandas as pd
import os
from collections import defaultdict
# from datetime import datetime, timedelta
import re
import numpy as np
#from pathlib import Path
# import glob
# import csv

#%% Função para Organizar arquivos UFs

# definir path
path = "/home/bruno/Gabriela/Lcqar/AvaliacaoEstacoes"

def create_QAQCMMA_VALOR(df,pol):

    if 'VALOR_ORIGINAL' in df.columns:
        df = df.drop(columns='VALOR_ORIGINAL')

    df = df.rename(columns={'VALOR':'VALOR_ORIGINAL'})

    flags_invalidos = ['?E','!', 'IF', 'IO', 'IC', 'I%', 'IL', 'IE', 'IS', 'IU', 'IM', 'IP', 'ID', 'IT', 'IR', 
                       'Fora da Faixa de Medição', 'Disabilitada Temporariamente', 'Inválido', 
                       'Insuficientes', 'Inexistente']

    df['QAQC_INTERNO'] = ~df['QAQC_INTERNO'].isin(flags_invalidos)
    
    DEFAULT_RANGE_LIMITS = {
        "O3": (0, 500),
        "CO": (0, 50),
        "NO2": (0, 1000),
        "NOX": (0, 2000),
        "SO2": (0, 1000),
        "MP25": (0, 1000),
        "MP10": (0, 2000),
    }

    df['QAQC_MMA'] = df['QAQC_INTERNO']

    if pol in list(DEFAULT_RANGE_LIMITS.keys()):
        lim_min = DEFAULT_RANGE_LIMITS[pol][0]
        lim_max = DEFAULT_RANGE_LIMITS[pol][1]
    else:
        lim_min = 0
        lim_max = np.inf
    
    df['VALOR'] = df['VALOR_ORIGINAL']

    df['VALOR'] = pd.to_numeric(df['VALOR'], errors='coerce')
    
    #Se QAQC_MMA está True e o VALOR é nulo, muito baixo ou muito alto, então mude QAQC_MMA para False
    df.loc[df['QAQC_MMA'] & (df['VALOR'].isna() | (df['VALOR'] <= lim_min) | (df['VALOR'] >= lim_max)), 'QAQC_MMA'] = False
    
    df.loc[df['VALOR'] == 985, 'VALOR'] = np.nan
    
    # Nas linhas onde QAQC_MMA é False, coloque NaN em VALOR.
    df.loc[~df['QAQC_MMA'], 'VALOR'] = np.nan
    
    df = df[['DATETIME', 'ANO', 'MES', 'DIA', 'HORA', 'VALOR', 'VALOR_ORIGINAL', 'UNIDADE', 'QAQC_INTERNO', 'QAQC_MMA']]

    return df

#Função para Bahia

def rectify_BA(path):
    
    pathBA = path+ "/outputs/BA"
    #path+'/output_by_station_pollutant/'
    
    #abrindo uma lista
    dict_pols_stat = defaultdict(list)
    
    #a todos os arquivos encontrados no path
    files = os.listdir(pathBA)
    
    lista=[]
    
    i = 0
    
    for item in files:
        print(i)
        i = i + 1
                   
        if 'csv' in item:

            if os.path.getsize(pathBA + '/' + item) > 0:  # só tenta ler se não for vazio
                #os.path.getsize(pathBA+item) >
                try:
                    df = pd.read_csv(pathBA + '/' + item)
                    #pd.read_csv(pathBA+item)
                    
                    #Divide a string onde encontra _ 
                    # assume que existe padrão no nome do arquivo por isso -4 (codigo poluente)
                    pol = item.split('_')[-4]
                    
                    pol = tabela_pols.loc[tabela_pols['COD_POLUENTE'] == int(pol), 'NOME_PASTA'].values[0]
                    
                    estacao = ''.join(item.split('_')[1:-4])
                    
                    df['DATETIME'] = pd.to_datetime(df["DATETIME"])
                    
                    df.index = df['DATETIME']

                    df = df.rename(columns={'CONC':'VALOR','QAQC':'QAQC_INTERNO'})
                    
                    #guarda no dicionário
                    dict_pols_stat[estacao+'_'+pol].append(df)
                    
                except pd.errors.EmptyDataError:
                    print(f"Arquivo vazio ou inválido: {pathBA+item}")
                    df = pd.DataFrame()  # cria DF vazio
            else:
                print(f"Arquivo vazio: {pathBA+item}")
                df = pd.DataFrame()
    
    dict_formatado = {}
    
    #percorre cada chave
    for chave in dict_pols_stat.keys():
        
        #coloca nessa lista
        lista_dfs = dict_pols_stat[chave]
        
        #junta tudo, todos os dias juntos
        df = pd.concat(lista_dfs, ignore_index=True)

        df["DATETIME"] = pd.to_datetime(df["DATETIME"])

        df = df.set_index("DATETIME")

        df = df.sort_index()
        
        lista_horas = pd.date_range(
            start=df.index.min(), 
            end=df.index.max(), 
            freq='h').strftime('%Y-%m-%d %H:%M:%S').tolist()
        
        if len(lista_horas) != len(df):
            #força o DataFrame a ter todas as horas
            df = df.reindex(pd.DatetimeIndex(lista_horas))
        
        df.insert(0, 'DATETIME', df.index)
        df.insert(1, 'ANO', df.index.year)
        df.insert(2, 'MES', df.index.month)
        df.insert(3, 'DIA', df.index.day)
        df.insert(4, 'HORA', df.index.hour)
        
        #unidade
        if chave.split('_')[-1] == 'CO':
            df['UNIDADE'] = 'ppm'
        else:
            df['UNIDADE'] = 'ug/m³'
        
        # um dataframe por estação e poluente
        dict_formatado[chave] = df
        
    primeiros_valores = {}
    
    #salva os primeiros valores validos
    for chave, df in dict_formatado.items():
        
        if ~df['VALOR'].isna().all() and (df['VALOR'] > 0).any(): 
            
            linha_valida = df[df["VALOR"].notna() & (df["VALOR"] > 0)].iloc[0]
            primeiros_valores[chave] = linha_valida["DATETIME"]
    
    codigo_estacao_BA = {}
    
    #confere as datas e atualiza se for uma data menor?
    for chave in primeiros_valores.keys():
        
        station = chave.split('_')[0]
        data = primeiros_valores[chave]
        
        if station in codigo_estacao_BA:
            if data <= codigo_estacao_BA[station]:
                codigo_estacao_BA[station] = data
        else:
            codigo_estacao_BA[station] = data
            
    #organiza
    sorted_items = sorted(
        codigo_estacao_BA.items(),
        key=lambda x: (x[1], x[0])
    )
    
    codigo_estacao_BA = {}
    
    for i, (nome, ts) in enumerate(sorted_items, start=1):
        codigo = f"BA{i:04d}"
        codigo_estacao_BA[nome] = codigo
    
    # codigo_estacao_BA = {
    # "AREIASII" : "BA0001",
    # "BOTELHO" : "BA0002",
    # "CABOTO" : "BA0003",
    # "CAMARA" : "BA0004",
    # "COBRE" : "BA0005",
    # "CONCORDIA" : "BA0006",
    # "ESCOLA": "BA0007",
    # "FUTURAMAI" : "BA0008",
    # "GAMBOA" : "BA0009",
    # "GRAVATA" : "BA0010",
    # "LAMARAO" : "BA0011",
    # "LEANDRINHO" : "BA0012",
    # "MACHADINHO" : "BA0013",
    # "MALEMBA" : "BA0014"}
 ############################ 
    
    codigo_estacao_BA = {
    "AREIASII" : "BA0012",
    "BOTELHO" : "BA0010",
    "CABOTO" : "BA0013",
    "CAMARA" : "BA0001",
    "COBRE" : "BA0002",
    "CONCORDIA" : "BA0007",
    "ESCOLA": "BA0006",
    "FUTURAMAI" : "BA0009",
    "GAMBOA" : "BA0014",
    "GRAVATA" : "BA0003",
    "LAMARAO" : "BA0004",
    "LEANDRINHO" : "BA0008",
    "MACHADINHO" : "BA0005",
    "MALEMBA" : "BA0011"}
    
    print("\n=== codigo_estacao_BA gerado automaticamente ===")
    for k, v in codigo_estacao_BA.items():
        print(k, ":", v)

######################
      
    for chave, df in dict_formatado.items():
        
        estacao = codigo_estacao_BA[chave.split('_')[0]]
        
        cod_pol = tabela_pols.loc[tabela_pols['POLUENTE'] == chave.split('_')[-1], 'COD_POLUENTE'].values[0]
        
        nome_pasta = tabela_pols.loc[tabela_pols['COD_POLUENTE'] == int(cod_pol), 'NOME_PASTA'].values[0]

        df = create_QAQCMMA_VALOR(df,nome_pasta)
        
        # #mudei aquiiiiiii
        # df.to_csv( "/home/bruno/Gabriela/Lcqar/AvaliacaoEstacoes/outputs/Resultados Brutos/BA/" +nome_pasta+'/'+estacao+'ND'+str(int(cod_pol)).zfill(3)+'.csv',index=False,
        #           exist_ok=True)

        pasta_saida = (
    "/home/bruno/Gabriela/Lcqar/AvaliacaoEstacoes/outputs/Resultados Brutos/BA/"
    + nome_pasta
        )
        
        os.makedirs(pasta_saida, exist_ok=True)
        
        df.to_csv(
            pasta_saida + '/' +
            estacao + 'ND' +
            str(int(cod_pol)).zfill(3) +
            '.csv',
            index=False
        )

            #"/home/bruno/Gabriela/Lcqar/AvaliacaoEstacoes/outputs"
            #'/home/nobre/Notebooks/RQAR_2025_book/data/MQAr/'
    df_ids = pd.DataFrame({
    'ID_OEMA': codigo_estacao_BA.keys(),
    'ID_MMA':list(codigo_estacao_BA.values())})

    return df_ids


# Função para Maranhão

def rectify_MA(path):
    
    #path = path+'/output_by_station_pollutant/'
    pathMA = path+ "/outputs/MA"
    
    dict_pols_stat = defaultdict(list)
    
    files = os.listdir(pathMA)
    
    lista=[]
    
    lista_pols = ['MP25','MP10','CO','O3','NO2','SO2','PTS']
    
    lista_regex = ['OUT','CO','NO2','O3IQAR','UVIQAR','MP25',
                   'COIQAR','IQAR','MP10IQAR','MP25IQAR','O3',
                   'MP10','SO2','NO2IQAR','PTS','UV','IN']
    
    lista_negada = "|".join(lista_regex)
    
    padrao = rf"^[A-Z]{{2}}_(.*?)(?=_(?:\d|{lista_negada}))"
    
    for item in files:
        
        if 'csv' in item:
            
            pol = item.split('_')[-2]
            
            if pol in lista_pols:
                #erro aqui, teste
                estacao = re.search(padrao, item)
                
                if estacao is None:
                    print("\nERRO REGEX:")
                    print(item)
                    continue
                # if estacao is None:
                #     print(item)
                
                lista.append(estacao.group(1).replace("_", " "))
                
                #df = pd.read_csv(pathMA+item)
                df = pd.read_csv(os.path.join(pathMA, item))
                
                pol = tabela_pols.loc[tabela_pols['POLUENTE'] == pol, 'NOME_PASTA'].values[0]
                
                estacao = estacao.group(1).replace("_", " ")
                
                df['DATETIME'] = pd.to_datetime(df["DATETIME"])
                
                df.index = df['DATETIME']
                
                df = df.rename(columns={'CONC':'VALOR'})
                
                df = df.drop(columns=["COD"])
                
                dict_pols_stat[estacao+'_'+pol].append(df)
    
    dict_formatado = {}
    
    for chave in dict_pols_stat.keys():
        
        lista_dfs = dict_pols_stat[chave]
        
        df = pd.concat(lista_dfs, ignore_index=True)
        
        print("\n================")
        print(chave)
        
        print("Menor data:", df["DATETIME"].min())
        print("Maior data:", df["DATETIME"].max())
                
        df["DATETIME"] = pd.to_datetime(df["DATETIME"])

        df = df.set_index("DATETIME")

        df = df.sort_index()
        
        lista_horas = pd.date_range(
            start=df.index.min(), 
            end=df.index.max(), 
            freq='h').strftime('%Y-%m-%d %H:%M:%S').tolist()
        
        if len(lista_horas) != len(df):
            df = df.reindex(pd.DatetimeIndex(lista_horas))
        
        df.insert(0, 'DATETIME', df.index)
        df.insert(1, 'ANO', df.index.year)
        df.insert(2, 'MES', df.index.month)
        df.insert(3, 'DIA', df.index.day)
        df.insert(4, 'HORA', df.index.hour)
        
        if chave.split('_')[-1] == 'CO':
            df['UNIDADE'] = 'ppm'
        else:
            df['UNIDADE'] = 'ug/m³'
        
        df['QAQC_INTERNO'] = None
        
        dict_formatado[chave] = df
        
    primeiros_valores = {}

    for chave, df in dict_formatado.items():
        
        if ~df['VALOR'].isna().all() and (df['VALOR'] > 0).any(): 
            
            linha_valida = df[df["VALOR"].notna() & (df["VALOR"] > 0)].iloc[0]
            primeiros_valores[chave] = linha_valida["DATETIME"]
    
    codigo_estacao_MA = {}
    
    for chave in primeiros_valores.keys():
        
        station = chave.split('_')[0]
        data = primeiros_valores[chave]
        
        if station in codigo_estacao_MA:
            if data <= codigo_estacao_MA[station]:
                codigo_estacao_MA[station] = data
        else:
            codigo_estacao_MA[station] = data
    
    sorted_items = sorted(
        codigo_estacao_MA.items(),
        key=lambda x: (x[1], x[0])
    )
    
    codigo_estacao_MA = {}
    for i, (nome, ts) in enumerate(sorted_items, start=1):
        codigo = f"MA{i:04d}"
        codigo_estacao_MA[nome] = codigo
    
    #AJUSTAR AQUI
    
    codigo_estacao_MA = {
        'BR135 Pedrinhas': 'MA0003',
        'Coqueiro': 'MA0004',
        'Santa Bárbara': 'MA0001',
        'Vila Maranhão': 'MA0006',
        'Vila Sarney': 'MA0005',
        'Anjo da Guarda': 'MA0002'}
        
    for chave, df in dict_formatado.items():
        
        estacao = codigo_estacao_MA[chave.split('_')[0]]
        
        cod_pol = tabela_pols.loc[tabela_pols['POLUENTE'] == chave.split('_')[-1], 'COD_POLUENTE'].values[0]
        
        nome_pasta = tabela_pols.loc[tabela_pols['COD_POLUENTE'] == int(cod_pol), 'NOME_PASTA'].values[0]

        df = create_QAQCMMA_VALOR(df,nome_pasta)
        
        #df.to_csv('/home/nobre/Notebooks/RQAR_2025_book/data/MQAr/'+nome_pasta+'/'+estacao+'RA'+str(int(cod_pol)).zfill(3)+'.csv',index=False)
        
        pasta_saida = (
    "/home/bruno/Gabriela/Lcqar/AvaliacaoEstacoes/outputs/Resultados Brutos/MA/"
    + nome_pasta
        )
        
        os.makedirs(pasta_saida, exist_ok=True)
        
        df.to_csv(
            pasta_saida + '/' +
            estacao + 'ND' +
            str(int(cod_pol)).zfill(3) +
            '.csv',
            index=False
        )


    df_ids = pd.DataFrame({
    'ID_OEMA': codigo_estacao_MA.keys(),
    'ID_MMA':list(codigo_estacao_MA.values())})
    
    return df_ids


#%% MAIN
funcoes = {
    # 'MG': rectify_MG, 
    # 'ES': rectify_ES,
    # 'SP': rectify_SP,
    # 'RJ': rectify_RJ,
     
    # 'SC': rectify_SC,
    # 'RS': rectify_RS,
    # 'PR': rectify_PR,
    
    'MA': rectify_MA,
    'BA': rectify_BA,
    # 'PE': rectify_PE,
    # 'CE': rectify_CE,
    # 'PB': rectify_PB,
    
    # 'MT': rectify_MT,
    # 'DF': rectify_DF,
    # 'MS': rectify_MS,
    
    # 'RR': rectify_RR,
    # 'AC': rectify_AC,   
}

#lista_estados = ['DF','ES','MA','MG','MS','PE','PR','RS','SC','SP','BA']
lista_estados = ['MA','BA']

# que dicionário é esse?                                        
tabela_pols = pd.read_csv('/home/bruno/Gabriela/Lcqar/AvaliacaoEstacoes/input/CODIGO_POLUENTES.csv')
#('/home/nobre/Notebooks/RQAR_2025_book/data/dicionarios/CODIGO_POLUENTES.csv')

for estado in lista_estados:
    path = "/home/bruno/Gabriela/Lcqar/AvaliacaoEstacoes" 
    #'/data/DADOS_BRUTOS/' + estado + '/'

    df_ids = funcoes[estado](path)
    
    
# import os

# print(os.getcwd())
# print(path)
# print(os.path.exists(path))

