#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  2 10:22:00 2026

@author: bruno
"""

#%%
import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

import matplotlib.pyplot as plt




df= pd.read_csv("https://arquivos.lcqar.ufsc.br/data/databases/stations/Monitoramento_QAr_BR.csv")

# URL DO NO2 1H
url_pagina = "https://arquivos.lcqar.ufsc.br/data/databases/stations/MQAr_averages/1/NO2/"

response = requests.get(url_pagina)
soup = BeautifulSoup(response.text, "html.parser")

links_csv = []

for link in soup.find_all("a"):
    href = link.get("href")

    if href and href.endswith(".csv"):
        links_csv.append(urljoin(url_pagina, href))

#print(links_csv)

#dfT= pd.read_csv("https://arquivos.lcqar.ufsc.br/data/databases/stations/MQAr_averages/1/NO2/")

lista_df = []

for url in links_csv:
    df = pd.read_csv(url)
    lista_df.append(df)

df_final = pd.concat(lista_df, ignore_index=True)

#df2023= df_final['ANO']
df2023NO2 = df_final.loc[df_final['ANO'] == 2023]

#media_maio = df.loc[df['Mes'] == 5, 'Valor'].mean()

dfNO2 = df2023NO2.loc[df2023NO2['MES']== 1, 'VALOR'].mean()

print(dfNO2)


media_mes = (
    df2023NO2
    .groupby('MES')['VALOR']
    .mean()
)

print(media_mes)

# # Conferência
# df2023NO2.groupby('MES')['VALOR'].agg(
#     ['count', 'mean', 'min', 'max']
# )



media_mes.boxplot(column='VALOR')
plt.show()



#df2023NO2 = df_final.loc[df_final['ANO'] == 2023]

plt.figure(figsize=(10, 6))
media_mes.boxplot(column='VALOR', by='MES')

plt.title('Distribuição mensal de NO₂ em 2023')
plt.suptitle('')  # remove o título automático do pandas
plt.xlabel('Mês')
plt.ylabel('VALOR')
plt.show()


plt.figure(figsize=(10,6))
df2023NO2.boxplot(column='VALOR', by='MES')

plt.title('Distribuição mensal de NO₂ em 2023')
plt.suptitle('')
plt.xlabel('Mês')
plt.ylabel('VALOR')
plt.show()

