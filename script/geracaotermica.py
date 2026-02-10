# -*- coding: utf-8 -*-
"""
Foram elaborados fatores de desagregação temporal diário, semanal, mensal e
horário, a partir da normalização anual da geração elétrica, preservando a
massa anual e refletindo o perfil operacional das usinas termelétricas. Além 
disso plots para avaliar a sazonalidade e comportamento dessa geração
 
"""

#Importando os pacotes

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import glob
import os

#%% Leitura dos csv e somatória por hora

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

#all_df['nom_tipousina'].unique()

# Filtrando para térmica
all_termica = all_df [all_df['nom_tipousina'] == 'TÉRMICA']

# Gerando uma cópia segura
all_termica = all_termica.copy()

# Tendo certeza que é o formato datetime
all_termica['din_instante'] = pd.to_datetime(all_termica['din_instante'])

# Colocando como índice
all_termica = all_termica.set_index('din_instante')

#print(all_termica.head())
#print(all_termica.columns)

# Tirando colunas não úteis
all_termica = all_termica.drop(columns=['id_subsistema', 'nom_subsistema', 
                                        'id_estado', 'id_ons'])
#all_termica['val_geracao'].dtype

# Somando a cada dia, por hora em comum de geração
geracao_termica_horaria = (
    all_termica
    .resample('H')[['val_geracao']]
    .sum()
)


#%% Plotagem sazonalidade 

fig, ax = plt.subplots(figsize=(14, 5))

ax.plot(
    geracao_termica_horaria.index,
    geracao_termica_horaria['val_geracao'],
    linewidth=0.6
)

# ---- EIXO X ----
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

ax.xaxis.set_minor_locator(mdates.MonthLocator())

# ---- GRID ----
ax.grid(True, which='major', axis='x', linewidth=0.8, alpha=0.9)
ax.grid(True, which='minor', axis='x', linewidth=0.4, linestyle='--', alpha=0.6)
ax.grid(True, which='major', axis='y', linewidth=0.4, alpha=0.7)

# ---- LIMITES (remove espaços) ----
ax.set_xlim(
    geracao_termica_horaria.index.min(),
    geracao_termica_horaria.index.max()
)

ax.margins(x=0)

# ---- LABELS ----
ax.set_xlabel('Ano')
ax.set_ylabel('Geração [MW]', labelpad=15)
ax.set_title('Geração horária - Usinas termelétricas (2017–2024)')

fig.subplots_adjust(left=0.12)

#plt.tight_layout()
plt.show()

#%% Fatores de desagregação temporal 

geracao_termica_horaria['ano'] = geracao_termica_horaria.index.year
geracao_termica_horaria['mes'] = geracao_termica_horaria.index.month
geracao_termica_horaria['hora'] = geracao_termica_horaria.index.hour
geracao_termica_horaria['data'] = geracao_termica_horaria.index.date
geracao_termica_horaria['semana'] = geracao_termica_horaria.index.isocalendar().week

# Soma anual da geração
geracao_anual = (
    geracao_termica_horaria
    .groupby('ano')['val_geracao']
    .sum()
    .rename('geracao_total_ano')
)



#%% Fator desagregação horário

geracao_termica_horaria['geracao_total_ano'] = (
    geracao_termica_horaria['ano']
    .map(geracao_anual)
)

geracao_termica_horaria['fator_horario'] = (
    geracao_termica_horaria['val_geracao'] / geracao_termica_horaria['geracao_total_ano']
)

#check - tem que dar 1
geracao_termica_horaria.groupby('ano')['fator_horario'].sum()

#%% Fator de desagregação diário

geracao_termica_diaria = (
    geracao_termica_horaria
    .groupby(['ano', 'data'], as_index=False)['val_geracao']
    .sum()
)

geracao_termica_diaria = geracao_termica_diaria.merge(geracao_anual, on='ano')

geracao_termica_diaria['fator_diario'] = (
    geracao_termica_diaria['val_geracao'] / geracao_termica_diaria['geracao_total_ano']
)

#check - tem que dar 1
geracao_termica_diaria.groupby('ano')['fator_diario'].sum()

# ----------- a média dos fatores

media_hora = all_termica.groupby(all_termica.index.hour)['val_geracao'].mean()

df_media_hora = media_hora.to_frame()

media_dfactor = (
    geracao_termica_horaria
    .groupby(geracao_termica_horaria.index.hour)['fator_horario']
    .mean()
)

df_media_hora['dfactor'] = media_dfactor
#media_h = grp_hora.mean()




#%% Fator de desagregação semanal 

geracao_termica_semanal = (
    geracao_termica_horaria
    .groupby(['ano', 'semana'], as_index=False)['val_geracao']
    .sum()
)

geracao_termica_semanal = geracao_termica_semanal.merge(geracao_anual, on='ano')

geracao_termica_semanal['fator_semanal'] = (
    geracao_termica_semanal['val_geracao'] / geracao_termica_semanal['geracao_total_ano']
)

#check - tem que dar 1
print(geracao_termica_semanal.groupby('ano')['fator_semanal'].sum())

#%% Fator de desagregação mensal

geracao_termica_mensal = (
    geracao_termica_horaria
    .groupby(['ano', 'mes'], as_index=False)['val_geracao']
    .sum()
)

geracao_termica_mensal = geracao_termica_mensal.merge(geracao_anual, on='ano')

geracao_termica_mensal['fator_mensal'] = (
    geracao_termica_mensal['val_geracao'] / geracao_termica_mensal['geracao_total_ano']
)

#check - tem que dar 1
print(geracao_termica_mensal.groupby('ano')['fator_mensal'].sum())

#%% EXPORTAÇÃO COMPLETA DOS FATORES (todas as colunas)

# pasta de saída
output_path = '/home/bruno/Gabriela/Lcqar/outputs'
os.makedirs(output_path, exist_ok=True)

# =========================
# FATOR HORÁRIO
# =========================
geracao_termica_horaria.to_csv(
    os.path.join(output_path, 'fator_desagregacao_horario_completo.csv'),
    index=False
)

# =========================
# FATOR DIÁRIO
# =========================
geracao_termica_diaria.to_csv(
    os.path.join(output_path, 'fator_desagregacao_diario_completo.csv'),
    index=False
)

# =========================
# FATOR SEMANAL
# =========================
geracao_termica_semanal.to_csv(
    os.path.join(output_path, 'fator_desagregacao_semanal_completo.csv'),
    index=False
)

# =========================
# FATOR MENSAL
# =========================
geracao_termica_mensal.to_csv(
    os.path.join(output_path, 'fator_desagregacao_mensal_completo.csv'),
    index=False
)

#%% 
# -----------Plot média hora------------

grp_hora = all_termica.groupby(all_termica.index.hour)['val_geracao']

media_h = grp_hora.mean()
min_h   = grp_hora.min()
max_h   = grp_hora.max()

fig, ax = plt.subplots(figsize=(10, 4))

ax.plot(media_h.index, media_h.values, label='Média', linewidth=2)
ax.fill_between(
    media_h.index,
    min_h.values,
    max_h.values,
    alpha=0.3,
    label='Mín–Máx'
)

# ---- LIMITES (remove espaços) ----
ax.set_xlim(0, 23)

ax.set_title('Horas')
ax.set_ylabel('Geração [MW]')
ax.set_xticks(range(0, 24))
ax.legend()
ax.grid(alpha=0.3)

plt.show()

# ---------- Plot dias da semana -------------
grp_sem = all_termica.groupby(all_termica.index.dayofweek)['val_geracao']

media_s = grp_sem.mean()
min_s   = grp_sem.min()
max_s   = grp_sem.max()

dias = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']

fig, ax = plt.subplots(figsize=(8, 4))

ax.plot(dias, media_s.values,label='Média', linewidth=2)
ax.fill_between(
    dias,
    min_s.values,
    max_s.values,
    alpha=0.3,
    label='Mín–Máx'
)

# ---- LIMITES (remove espaços) ----
ax.set_xlim('Seg', 'Dom')

ax.set_ylabel('Geração [MW]')
ax.set_title('Dias da semana')
ax.legend()
ax.grid(True, which='both', alpha=0.3)

plt.show()

# ----------- Plot mensal --------------

grp_mes = all_termica.groupby(all_termica.index.month)['val_geracao']

media_m = grp_mes.mean()
min_m   = grp_mes.min()
max_m   = grp_mes.max()

meses = ['Jan','Fev','Mar','Abr','Mai','Jun',
         'Jul','Ago','Set','Out','Nov','Dez']

fig, ax = plt.subplots(figsize=(9, 4))

ax.plot(meses, media_m.values, label='Média', linewidth=2)
ax.fill_between(
    meses,
    min_m.values,
    max_m.values,
    alpha=0.3,
    label='Mín–Máx' #legenda
)

# ---- LIMITES (remove espaços) ----
ax.set_xlim('Jan', 'Dez') #retira a margem

ax.set_ylabel('Geração [MW]')
ax.set_title('Mês')
ax.legend()
ax.grid(alpha=0.3)

plt.show()


#%%com escala log

#----horaria log
grp_hora = all_termica.groupby(all_termica.index.hour)['val_geracao']

media_h = grp_hora.mean()
min_h   = grp_hora.min()
max_h   = grp_hora.max()

eps = 1e-3  # valor mínimo para escala log

media_h = media_h.clip(lower=eps)
min_h   = min_h.clip(lower=eps)
max_h   = max_h.clip(lower=eps)

fig, ax = plt.subplots(figsize=(10, 4))

ax.plot(media_h.index, media_h.values, linewidth=2, label='Média')
ax.fill_between(
    media_h.index,
    min_h.values,
    max_h.values,
    alpha=0.3,
    label='Mín–Máx'
)

ax.set_yscale('log')
ax.set_xlabel('Hora do dia')
ax.set_ylabel('Geração')
ax.set_xticks(range(24))
ax.legend()
ax.grid(True, which='both', alpha=0.3)

plt.show()

#----------mensal log

grp_mes = all_termica.groupby(all_termica.index.month)['val_geracao']

media_m = grp_mes.mean()
min_m   = grp_mes.min()
max_m   = grp_mes.max()

eps = 1e-3  # valor mínimo para escala log

media_m = media_m.clip(lower=eps)
min_m   = min_m.clip(lower=eps)
max_m   = max_m.clip(lower=eps)

meses = ['Jan','Fev','Mar','Abr','Mai','Jun',
         'Jul','Ago','Set','Out','Nov','Dez']

fig, ax = plt.subplots(figsize=(9, 4))

ax.plot(meses, media_m.values, marker='o', linewidth=2)
ax.fill_between(
    meses,
    min_m.values,
    max_m.values,
    alpha=0.3
)

ax.set_yscale('log')

ax.set_ylabel('Geração')
ax.set_title('Sazonalidade mensal')
ax.grid(alpha=0.3)

plt.show()

# ------ dias da semana
grp_sem = all_termica.groupby(all_termica.index.dayofweek)['val_geracao']

media_s = grp_sem.mean()
min_s   = grp_sem.min()
max_s   = grp_sem.max()

eps = 1e-3

media_s = media_s.clip(lower=eps)
min_s   = min_s.clip(lower=eps)
max_s   = max_s.clip(lower=eps)

dias = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']

fig, ax = plt.subplots(figsize=(8, 4))

ax.plot(dias, media_s.values, marker='o', linewidth=2)
ax.fill_between(
    dias,
    min_s.values,
    max_s.values,
    alpha=0.3
)

ax.set_yscale('log')
ax.set_ylabel('Geração')
ax.set_title('Sazonalidade semanal')
ax.legend()
ax.grid(True, which='both', alpha=0.3)

plt.show()

#%%
#os 3 juntos

# fig, axs = plt.subplots(3, 1, figsize=(11, 10), sharey=False)

# # ----------------------
# # 1) HORÁRIA
# # ----------------------
# axs[0].plot(
#     media_h.index,
#     media_h.values,
#     linewidth=2
# )
# axs[0].fill_between(
#     media_h.index,
#     min_h.values,
#     max_h.values,
#     alpha=0.3
# )
# axs[0].set_title('Horas')
# axs[0].set_xlabel('Hora do dia')
# axs[0].set_ylabel('Geração')
# axs[0].set_xticks(range(24))
# axs[0].grid(alpha=0.3)

# # ----------------------
# # 2) SEMANAL
# # ----------------------
# dias = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']

# axs[1].plot(
#     dias,
#     media_s.values,
#     linewidth=2
# )
# axs[1].fill_between(
#     dias,
#     min_s.values,
#     max_s.values,
#     alpha=0.3
# )
# axs[1].set_title('Dias da semana')
# axs[1].set_ylabel('Geração')
# axs[1].grid(alpha=0.3)

# # ----------------------
# # 3) MENSAL
# # ----------------------
# meses = ['Jan','Fev','Mar','Abr','Mai','Jun',
#          'Jul','Ago','Set','Out','Nov','Dez']

# axs[2].plot(
#     meses,
#     media_m.values,
#     linewidth=2
# )
# axs[2].fill_between(
#     meses,
#     min_m.values,
#     max_m.values,
#     alpha=0.3
# )
# axs[2].set_title('Mês')
# axs[2].set_ylabel('Geração')
# axs[2].grid(alpha=0.3)

# plt.tight_layout()
# plt.show()
