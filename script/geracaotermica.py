# -*- coding: utf-8 -*-
"""
Editor Spyder

Este é um arquivo de script temporário.
"""

#Importando os pacotes

import pandas as pd
import matplotlib.pyplot as plt
import glob
import os

#%% Filtrando

# Caminho para os arquivos CSV
path = '/home/bruno/Gabriela/dados'
files = glob.glob(os.path.join(path, "*.csv"))

# Lista para armazenar os DataFrames
df_list = []

for file in files:
    df = pd.read_csv(file, sep=";")
    df_list.append(df)

# Concatena todos os DataFrames em um só
all_df = pd.concat(df_list, ignore_index=True)

all_df['nom_tipousina'].unique()

all_termica = all_df [all_df['nom_tipousina'] == 'TÉRMICA']

#print(all_termica.head())
#print(all_termica.columns)

all_termica['din_instante'].dtype
all_termica = all_termica.copy()
all_termica['din_instante'] = pd.to_datetime(all_termica['din_instante'])
all_termica = all_termica.set_index('din_instante')

#print(all_termica.head())
#print(all_termica.columns)

all_termica = all_termica.drop(columns=['id_subsistema', 'nom_subsistema', 
                                        'id_estado', 'id_ons'])


#contagem_mensal = all_termica.resample('M').count()

#sazonal_horaria = all_termica.groupby(all_termica.index.hour).mean()

# gráfico teste 1
#all_termica.iloc[:, -1].plot(figsize=(12,4))

# grafico teste 2

# plt.figure(figsize=(14, 5))

# plt.plot(all_termica.index, all_termica['val_geracao'],
#          linewidth=0.6,
#          alpha=0.85)

# plt.show()

#grafico teste3

import matplotlib.dates as mdates

fig, ax = plt.subplots(figsize=(14, 5))

ax.plot(all_termica.index, all_termica['val_geracao'],
        linewidth=0.6,
        alpha=0.9)

# Ticks principais = ANO
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

# Ticks secundários = MÊS
ax.xaxis.set_minor_locator(mdates.MonthLocator())

# Grid
ax.grid(True, which='major', linewidth=0.8, alpha=0.7)
ax.grid(True, which='minor', linewidth=0.3, alpha=0.3)

plt.show()

#gŕafico teste 4

#df_mensal = all_termica['val_geracao'].resample('M').mean()

#fig, ax = plt.subplots(figsize=(14, 5))

#ax.plot(df_mensal.index, df_mensal,
#        linewidth=2)

#ax.xaxis.set_major_locator(mdates.YearLocator())
#ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

#ax.xaxis.set_minor_locator(mdates.MonthLocator())
#ax.grid(True, which='both', alpha=0.4)

#ax.set_xlabel('Ano')
#ax.set_ylabel('Geração média mensal (MW)')
#ax.set_title('Geração média mensal por usina – ONS')

#plt.show()


