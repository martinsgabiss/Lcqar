# -*- coding: utf-8 -*-
"""
Foram elaborados fatores de desagregação temporal diário, semanal, mensal e
horário, a partir da normalização anual da geração elétrica, preservando a
massa anual e refletindo o perfil operacional das usinas termelétricas. Além 
de plots para avaliar a sazonalidade e comportamento dessa geração.
 
"""

#Importando os pacotes

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import glob
import os

#%% Leitura dos csv e somatória por hora

# Caminho para os arquivos CSV
path = '/home/bruno/Gabriela/Lcqar/inputs/dadostermeletricas'

files = glob.glob(os.path.join(path, "*.csv"))

# Lista para armazenar os DataFrames
df_list = []

for file in files:
    df = pd.read_csv(file, sep=";")
    df_list.append(df)

# Concatena todos os DataFrames em um só
all_df = pd.concat(df_list, ignore_index=True)

#all_df['nom_tipousina'].unique() #me fala os valores unicos da coluna

# Filtrando para térmica
all_termica = all_df [all_df['nom_tipousina'] == 'TÉRMICA']

# Gerando uma cópia segura
all_termica = all_termica.copy()

# Tendo certeza que é o formato datetime
all_termica['din_instante'] = pd.to_datetime(all_termica['din_instante'])

# Colocando como índice
all_termica = all_termica.set_index('din_instante')

#print(all_termica.head()) #mostra a estrutura do dataframe, priemiras linhas
#print(all_termica.columns) #nome das colunas

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

fig_path = "/home/bruno/Gabriela/Lcqar/figuras"

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
plt.savefig(os.path.join(fig_path,'Geração horária (2017-2024).png'),dpi=300)
plt.show()

#%% FATORES DE DESAGREGAÇÃO TEMPORAL - "geracao da linha pela anual"

geracao_termica_horaria['ano'] = geracao_termica_horaria.index.year
geracao_termica_horaria['mes'] = geracao_termica_horaria.index.month
geracao_termica_horaria['hora'] = geracao_termica_horaria.index.hour
geracao_termica_horaria['data'] = geracao_termica_horaria.index.date
geracao_termica_horaria['semana'] = geracao_termica_horaria.index.isocalendar().week

# Soma anual da geração de energia
geracao_anual = (
    geracao_termica_horaria
    .groupby('ano')['val_geracao']
    .sum()
    .rename('geracao_total_ano')
) 
#acho que dava para fazer com o RESAMPLE

#%% Fator desagregação - POR HORA

geracao_termica_horaria['geracao_total_ano'] = (
    geracao_termica_horaria['ano']
    .map(geracao_anual) #.map() localiza e associa valores
)

# O FATOR:
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
# O .merge() faz o join com entre dois dataframes

# O FATOR:
geracao_termica_diaria['fator_diario'] = (
    geracao_termica_diaria['val_geracao'] / geracao_termica_diaria['geracao_total_ano']
)

#check - tem que dar 1
geracao_termica_diaria.groupby('ano')['fator_diario'].sum()

#%% Fator de desagregação semanal 

# geracao_termica_semanal = (
#     geracao_termica_horaria
#     .groupby(['ano', 'semana'], as_index=False)['val_geracao']
#     .sum()
# )

# geracao_termica_semanal = geracao_termica_semanal.merge(geracao_anual, on='ano')

# geracao_termica_semanal['fator_semanal'] = (
#     geracao_termica_semanal['val_geracao'] / geracao_termica_semanal['geracao_total_ano']
# )

# #check - tem que dar 1
# print(geracao_termica_semanal.groupby('ano')['fator_semanal'].sum())

#%% Fator de desagregação mensal

geracao_termica_mensal = (
    geracao_termica_horaria
    .groupby(['ano', 'mes'], as_index=False)['val_geracao']
    .sum()
)

geracao_termica_mensal = geracao_termica_mensal.merge(geracao_anual, on='ano')

# O FATOR:
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

# # =========================
# # FATOR SEMANAL
# # =========================
# geracao_termica_semanal.to_csv(
#     os.path.join(output_path, 'fator_desagregacao_semanal_completo.csv'),
#     index=False
# )

# =========================
# FATOR MENSAL
# =========================
geracao_termica_mensal.to_csv(
    os.path.join(output_path, 'fator_desagregacao_mensal_completo.csv'),
    index=False
)

#%% PLOTS USANDO OS VALORES MÉDIOS DE GERAÇÃO DE ENERGIA

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

plt.savefig(os.path.join(fig_path,'Analise Horaria pela Geracao.png'),dpi=300)

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

plt.savefig(os.path.join(fig_path,'Analise Dias da Semana pela Geracao.png'),dpi=300)

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

plt.savefig(os.path.join(fig_path,'Analise Mensal pela Geracao.png'),dpi=300)

plt.show()


#%% TESTANDO com escala log

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

#%% Perfil horário relativo - PLOT

df_hora = geracao_termica_horaria.copy() #mudei aqui o nome para conseguir comparar melhor com o código do gabriel

# Agrupa calculando média, percentil 5 e percentil 95
df_hora_agrupado = df_hora.groupby('hora')['fator_horario'].agg(
    fator_horario='mean',
    p05=lambda x: x.quantile(0.05),
    p95=lambda x: x.quantile(0.95)
).reset_index()

# Calcula o relativo baseado na média
df_hora_agrupado['fator_horario_relativo'] = df_hora_agrupado['fator_horario'] / df_hora_agrupado['fator_horario'].sum()

# Configuração do gráfico
plt.plot(df_hora_agrupado['hora'], df_hora_agrupado['fator_horario_relativo'], 
         label='Média Relativa', color='blue', lw=2)

plt.xlabel('Hora do Dia')
plt.ylabel('Fator Relativo')
plt.title('Variação Horária Relativa')
plt.xticks(range(0, 24))
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(fig_path,'Perfil Horário do fator relativo.png'),dpi=300)
plt.show()

df_hora_agrupado['fator_horario_relativo'].sum()

# GRÁFICO COM A VARIAÇÃO DOS ANOS - PERFIL HORÁRIO

# Extrair ano
#df_hora['ano'] = df_hora['hora'].dt.year

plt.figure(figsize=(12, 6))

# Plotar linhas finas para cada ano
for ano in sorted(df_hora['ano'].unique()):
    df_ano = df_hora[df_hora['ano'] == ano]
    # Agrupa por hora para aquele ano específico
    agrupado_ano = df_ano.groupby('hora')['fator_horario'].mean().reset_index()
    # Normaliza pela soma do próprio ano para ver o formato do perfil
    relativo_ano = agrupado_ano['fator_horario'] / agrupado_ano['fator_horario'].sum()
    
    plt.plot(agrupado_ano['hora'], relativo_ano, color='gray', lw=0.5, alpha=0.5)

# Plotar a média geral (que você já calculou) em destaque
plt.plot(df_hora_agrupado['hora'], df_hora_agrupado['fator_horario_relativo'], 
         label='Média Geral (2017-2024)', color='blue', lw=3)

plt.title('Variação Horária: Linhas Anuais vs Média Geral')
plt.xlabel('Hora do Dia')
plt.ylabel('Fator Relativo')
plt.xticks(range(0, 24))
plt.legend()
plt.grid(True, linestyle='--', alpha=0.3)
plt.savefig(os.path.join(fig_path,'Perfil Horário Interanual do fator relativo.png'),dpi=300)
plt.show()

#%% Perfil DIAS DA SEMANA - fator relativo - PLOT

# 1. Extrair o dia da semana (0=Segunda, 6=Domingo)
df_hora['dia_semana_num'] = df_hora.index.dayofweek
# Mapeamento para nomes em português
dias_nomes = {0: 'Seg', 1: 'Ter', 2: 'Qua', 3: 'Qui', 4: 'Sex', 5: 'Sab', 6: 'Dom'}

# 2. Agrupamento por dia da semana
df_semana_agrupado = df_hora.groupby('dia_semana_num')['fator_horario'].agg(
    fator_medio='mean',
    p05=lambda x: x.quantile(0.05),
    p95=lambda x: x.quantile(0.95)
).reset_index()

# 3. Normalização Consistente
# Dividimos pela soma das médias para que a linha azul (média) some 1
total_referencia = df_semana_agrupado['fator_medio'].sum()

df_semana_agrupado['rel_medio'] = df_semana_agrupado['fator_medio'] / total_referencia

print(df_semana_agrupado['rel_medio'].sum())


# 4. Gráfico
plt.figure(figsize=(10, 5))

plt.plot(df_semana_agrupado['dia_semana_num'], df_semana_agrupado['rel_medio'], 
         label='Média Diária', color='blue', lw=3, marker='o')


# Ajustar os nomes no eixo X
plt.xticks(ticks=range(7), labels=[dias_nomes[i] for i in range(7)])

plt.title('Perfil Semanal de Variação Relativa 2017-2024')
plt.xlabel('Dia da Semana')
plt.ylabel('Fator Relativo')
plt.grid(True, axis='y', linestyle=':', alpha=0.7)
plt.legend()
plt.tight_layout()

plt.savefig(os.path.join(fig_path,'Perfil dos dias da semana do fator relativo.png'),dpi=300)
plt.show()

# GRÁFICO COM A VARIAÇÃO DOS ANOS - PERFIL DIAS DA SEMANA

plt.figure(figsize=(10, 5))

for ano in sorted(df_hora['ano'].unique()):
    df_ano = df_hora[df_hora['ano'] == ano]
    agrupado_ano = df_ano.groupby('dia_semana_num')['fator_horario'].mean().reset_index()
    # Normaliza pela soma do ano
    total_ano = agrupado_ano['fator_horario'].sum()
    
    plt.plot(agrupado_ano['dia_semana_num'], agrupado_ano['fator_horario'] / total_ano, 
             color='gray', lw=0.5, alpha=0.5)

plt.plot(df_semana_agrupado['dia_semana_num'], df_semana_agrupado['rel_medio'], 
         label='Média Semanal Geral', color='blue', lw=3, marker='o')

plt.xticks(ticks=range(7), labels=[dias_nomes[i] for i in range(7)])
plt.title('Perfil Semanal: Variação entre Anos (2017-2024)')
plt.legend()
plt.savefig(os.path.join(fig_path,'Perfil dos dias da semana interanual do fator relativo.png'),dpi=300)
plt.show()

#%% Perfil mensal do fator relativo - PLOT

# 1. Extrair o mês (1 a 12)
#df_hora['mes'] = df_hora['hora'].dt.month

# 2. Agrupamento Mensal
df_mensal_agrupado = df_hora.groupby('mes')['fator_horario'].agg(
    fator_medio='mean',
    p05=lambda x: x.quantile(0.05),
    p95=lambda x: x.quantile(0.95)
).reset_index()

# 3. Normalização Técnica (Denominador Único)
# Isso garante que a hierarquia Vermelho > Azul > Verde seja respeitada
total_referencia = df_mensal_agrupado['fator_medio'].sum()

df_mensal_agrupado['rel_medio'] = df_mensal_agrupado['fator_medio'] / total_referencia

# 4. Gráfico
plt.figure(figsize=(12, 6))

# Linhas de tendência
plt.plot(df_mensal_agrupado['mes'], df_mensal_agrupado['rel_medio'], 
         label='Média Mensal', color='blue', lw=3, marker='s')

# Ajustes de Eixo e Legenda
plt.title('Sazonalidade Mensal Relativa 2017-2024', fontsize=14)
plt.xlabel('Mês do Ano')
plt.ylabel('Fator Relativo')
plt.xticks(range(1, 13)) # Garante que apareçam os 12 meses
plt.grid(True, linestyle=':', alpha=0.6)
plt.legend(loc='upper right')
plt.tight_layout()

plt.savefig(os.path.join(fig_path,'Perfil mensal do fator relativo.png'),dpi=300)
plt.show()

# GRÁFICO COM A VARIAÇÃO DOS ANOS - PERFIL mensal
plt.figure(figsize=(12, 6))

for ano in sorted(df_hora['ano'].unique()):
    df_ano = df_hora[df_hora['ano'] == ano]
    agrupado_ano = df_ano.groupby('mes')['fator_horario'].mean().reset_index()
    total_ano = agrupado_ano['fator_horario'].sum()
    
    plt.plot(agrupado_ano['mes'], agrupado_ano['fator_horario'] / total_ano, 
             color='gray', lw=0.5, alpha=0.5)

plt.plot(df_mensal_agrupado['mes'], df_mensal_agrupado['rel_medio'], 
         label='Média Mensal Geral', color='blue', lw=3, marker='s')

plt.title('Sazonalidade Mensal: Variação entre Anos (2017-2024)')
plt.xticks(range(1, 13))
plt.legend()

plt.savefig(os.path.join(fig_path,'Perfil mensal interanual do fator relativo.png'),dpi=300)
plt.show()
