# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import pandas as pd
import os 
import pandas as pd
from difflib import get_close_matches
#%%
pasta = r"C:\IND_Inventory\Marcos\relatorio"

#%% Nesta parte faz a estimativa de altura e diâmetro da chamine 
# de todos os processos das industrias, sem separação do que é de combustao
# ou do processo de produção especificamente

# Concatenação dos relatorios parana de 2023,2024 e 2025
relatorio_PR = pd.concat(pd.read_excel(os.path.join(pasta, f) , skiprows = 1)
    for f in os.listdir(pasta)
    if f.endswith((".xls", ".xlsx")))

# Extrair dados de chamine
padrao = (
r"^Chaminé\s+\d+\s+-\s+"
    r"altura\s+\d+,\d+m\s+/\s+"
    r"diâmetro\s+\d+,\d+m$"
)

# Selecionar as linhas que seguem o padrao
relatorio_filtrado = relatorio_PR[
    relatorio_PR["Descrição Ponto de Emissão"].str.match(padrao, na=False)
].copy()

# extrair altura e diâmetro
relatorio_filtrado[["altura_m", "diametro_m"]] = (
    relatorio_filtrado["Descrição Ponto de Emissão"]
    .str.extract(
        r"altura\s+(\d+,\d+)m\s+/\s+diâmetro\s+(\d+,\d+)m"
    )
)

# Converter para float (trocar vírgula por ponto)
relatorio_filtrado["altura_m"] = (
    relatorio_filtrado["altura_m"]
    .str.replace(",", ".", regex=False)
    .astype(float)
)
relatorio_filtrado["diametro_m"] = (
    relatorio_filtrado["diametro_m"]
    .str.replace(",", ".", regex=False)
    .astype(float)
)

# Fazendo classifcações
atividadeEspecifica = relatorio_filtrado.groupby(['Atividade','Atividade Específica'])[['altura_m','diametro_m']].median()
atividadeEspecifica = atividadeEspecifica.reset_index()
atividadeGeral = relatorio_filtrado.groupby(['Atividade'])[['altura_m','diametro_m']].median()

# atividadeEspecifica.to_excel('/home/marcos/Downloads/atividadeespecifica.xlsx', index=True)
# atividadeGeral.to_excel('/home/marcos/Downloads/atividade.xlsx', index=True)

#%% Nesta parte faz-se uma classifcação geral de qual área esta o CNPJ de acordo
# Com a descrição de atividades.

# Arquivo pre-processado anteriormente para estrair a area de mercado e ativi
# vidade principal de cada CNPJ analisado
classificacaoCNPJ = pd.read_csv(r"C:\IND_Inventory\Marcos\cnpj_classificados_cnpja.csv")

# 2. Criar um dicionário de mapeamento: Descrição Específica -> Atividade Principal
mapa_referencia = dict(zip(atividadeEspecifica['Atividade Específica'], 
                           atividadeEspecifica['Atividade']))

lista_especificas = atividadeEspecifica['Atividade Específica'].tolist()

# 3. Suas 547 descrições únicas
suas_atividades = classificacaoCNPJ['Descricao_Atividade'].unique()

# Função que relaciona a descrição da atividade com a area de atuação (Automático)
def encontrar_melhor_categoria(descricao):
    # Tenta encontrar um match exato primeiro
    if descricao in mapa_referencia:
        return mapa_referencia[descricao]
    
    # Se não houver match exato, busca a descrição mais parecida no a.csv
    match_proximo = get_close_matches(descricao, lista_especificas, n=1, cutoff=0.3)
    
    if match_proximo:
        return mapa_referencia[match_proximo[0]]
    
    return "Industrias diversas" # Categoria padrão se nada for encontrado

# 4. Criar a nova classificação (previo)
df_final = pd.DataFrame({'Descricao_Atividade': suas_atividades})
df_final['Atividade_Mapeada'] = df_final['Descricao_Atividade'].apply(encontrar_melhor_categoria)

############ CORREÇÃO MANUAL DA CLASSIFCAÇÃO

# df_final corrigido
Classificacao = pd.read_csv(r"C:\IND_Inventory\Marcos\df_corrigido.csv")

# Fazer classificação de área geral do CNPJ
classificacaoCNPJ = classificacaoCNPJ.merge(Classificacao[
    ['Descricao_Atividade','Atividade_Mapeada']],
    on='Descricao_Atividade', how='left')

# Fazer a classificação do CNPJ com dados de altura e diametro de chamine
classificacaoCNPJGERAL = classificacaoCNPJ.merge(
    atividadeGeral,left_on='Atividade_Mapeada',
    right_index=True,how='left')

#%% Nesta parte é feito a estimativa de altura e diametro da chamine para fontes
# de combustao

# CSV com as emissoes industriais
emissoes_industriais = pd.read_csv(r"C:\IND_Inventory\Inputs\emission_total_light.csv")

# FOrmatar cnpj
emissoes_industriais['CPF_CNPJ_NUM'] = (
    emissoes_industriais['CPF_CNPJ']
    .str.replace(r'\D', '', regex=True)
    .astype('Int64')
)


####### ETAPA 1 - sELECIONAR AS FONTES NO RELATORIO PR E TRATAR
relatorio_combustao = relatorio_PR[relatorio_PR[
    'Origem Emissão'].str.startswith('Combustão', na=False)]
relatorio_combustao['Taxa ton/ano'] = relatorio_combustao[
    'Taxa ton/ano'].str.replace(',', '.', regex=False).astype(float)
# Selecionar as linhas que seguem o padrao
relatorio_combustao = relatorio_combustao[
    relatorio_combustao["Descrição Ponto de Emissão"].str.match(padrao, na=False)
].copy()

# extrair altura e diâmetro
relatorio_combustao[["altura_m", "diametro_m"]] = (
    relatorio_combustao["Descrição Ponto de Emissão"]
    .str.extract(
        r"altura\s+(\d+,\d+)m\s+/\s+diâmetro\s+(\d+,\d+)m"
    )
)

####### ETAPA 2 - DETERMINAR A CLASSIFICAÇÃO DAS FONTES


# Converter para float (trocar vírgula por ponto)
relatorio_combustao["altura_m"] = (
    relatorio_combustao["altura_m"]
    .str.replace(",", ".", regex=False)
    .astype(float)
)
relatorio_combustao["diametro_m"] = (
    relatorio_combustao["diametro_m"]
    .str.replace(",", ".", regex=False)
    .astype(float)
)

# Anlise do CO por conter maior grupo amostral
relatorio_combustao_CO = relatorio_combustao[
    relatorio_combustao['Parâmetro'] == 'CO']

# Achar os valores de classifcações
p50 = relatorio_combustao_CO['Taxa ton/ano'].quantile(0.50)
p75 = relatorio_combustao_CO['Taxa ton/ano'].quantile(0.75)
p25 = relatorio_combustao_CO['Taxa ton/ano'].quantile(0.25)

# 25 % -
fontes_25 = relatorio_combustao_CO[
    relatorio_combustao_CO['Taxa ton/ano'] <= p25]
atividadeGeral_25 = fontes_25.groupby(['Atividade'])[
    ['altura_m','diametro_m']].median()

# Fazer a classificação do CNPJ com dados de altura e diametro de chamine
classificacaoCNPJ_25 = classificacaoCNPJ.merge(
    atividadeGeral_25,left_on='Atividade_Mapeada',
    right_index=True,how='left')

emissoes_industriais_25 = emissoes_industriais[
    emissoes_industriais['CO'] <= p25]


emissoes_industriais_25 = emissoes_industriais_25.merge(
    classificacaoCNPJ_25[['CNPJ','altura_m','diametro_m']],
    left_on='CPF_CNPJ_NUM',
    right_on='CNPJ',
    how='left'
)

# 25% - 50%
fontes_50 = relatorio_combustao_CO[
    (relatorio_combustao_CO['Taxa ton/ano'] > p25) &
    (relatorio_combustao_CO['Taxa ton/ano'] <= p50)]

atividadeGeral_50 = fontes_50.groupby(['Atividade'])[
    ['altura_m','diametro_m']].median()

classificacaoCNPJ_50 = classificacaoCNPJ.merge(
    atividadeGeral_50,
    left_on='Atividade_Mapeada',
    right_index=True,
    how='left')

emissoes_industriais_50 = emissoes_industriais[
    (emissoes_industriais['CO'] > p25) &
    (emissoes_industriais['CO'] <= p50)]

emissoes_industriais_50 = emissoes_industriais_50.merge(
    classificacaoCNPJ_50[['CNPJ','altura_m','diametro_m']],
    left_on='CPF_CNPJ_NUM',
    right_on='CNPJ',
    how='left')

# 50% - 75%
fontes_75 = relatorio_combustao_CO[
    (relatorio_combustao_CO['Taxa ton/ano'] > p50) &
    (relatorio_combustao_CO['Taxa ton/ano'] <= p75)]

atividadeGeral_75 = fontes_75.groupby(['Atividade'])[
    ['altura_m','diametro_m']].median()

classificacaoCNPJ_75 = classificacaoCNPJ.merge(
    atividadeGeral_75,
    left_on='Atividade_Mapeada',
    right_index=True,
    how='left')

emissoes_industriais_75 = emissoes_industriais[
    (emissoes_industriais['CO'] > p50) &
    (emissoes_industriais['CO'] <= p75)]

emissoes_industriais_75 = emissoes_industriais_75.merge(
    classificacaoCNPJ_75[['CNPJ','altura_m','diametro_m']],
    left_on='CPF_CNPJ_NUM',
    right_on='CNPJ',
    how='left')

# 75 % +
fontes_100 = relatorio_combustao_CO[
    relatorio_combustao_CO['Taxa ton/ano'] > p75]

atividadeGeral_100 = fontes_100.groupby(['Atividade'])[
    ['altura_m','diametro_m']].median()

classificacaoCNPJ_100 = classificacaoCNPJ.merge(
    atividadeGeral_100,
    left_on='Atividade_Mapeada',
    right_index=True,
    how='left')

emissoes_industriais_100 = emissoes_industriais[
    emissoes_industriais['CO'] > p75]

emissoes_industriais_100 = emissoes_industriais_100.merge(
    classificacaoCNPJ_100[['CNPJ','altura_m','diametro_m']],
    left_on='CPF_CNPJ_NUM',
    right_on='CNPJ',
    how='left')


emissoes_industriais_final = pd.concat([
    emissoes_industriais_25,
    emissoes_industriais_50,
    emissoes_industriais_75,
    emissoes_industriais_100
], ignore_index=True)

emissoes_industriais_final_valor = emissoes_industriais_final[
    ~emissoes_industriais_final['altura_m'].isna()
]

emissoes_nan = emissoes_industriais_final[
    emissoes_industriais_final['altura_m'].isna()]

emissoes_fora = emissoes_industriais[
    ~emissoes_industriais.index.isin(emissoes_industriais_final.index)]

emissoes_para_classificar = pd.concat(
    [emissoes_nan, emissoes_fora],ignore_index=False)


emissoes_para_classificar = emissoes_para_classificar.drop(
    columns=['altura_m','diametro_m','CPF_CNPJ_NUM'])

#emissoes_para_classificar = emissoes_para_classificar['CNPJ'].astype(int)
emissoes_class_geral = emissoes_para_classificar.merge(
    classificacaoCNPJGERAL[['CNPJ','altura_m','diametro_m']],
    on='CNPJ',how='left')


emissoes_industriais_total = pd.concat(
    [emissoes_industriais_final_valor, emissoes_class_geral],
    ignore_index=True)


emissoes_industriais_total = emissoes_industriais_total.drop(
    columns=['CPF_CNPJ_NUM','CNPJ'],
    errors='ignore')

medias_setor = (
    emissoes_industriais_total
    .groupby('SETOR')[['altura_m', 'diametro_m']]
    .mean()
    .reset_index()
)

# Média Industria Química
media_quimica = medias_setor[
    medias_setor['SETOR'].str.contains('Indústria Química', na=False)
][['altura_m', 'diametro_m']].mean()

# Média Combustão Ferro e Aço
media_ferro = medias_setor.loc[
    medias_setor['SETOR'] == 'Combustão na Indústria de Ferro e Aço',
    ['altura_m', 'diametro_m']
].iloc[0]

# Média Produção: alumínio + ferro e aço
media_producao = medias_setor[
    medias_setor['SETOR'].isin(['Produção de alumínio', 'Produção de ferro e aço'])
][['altura_m', 'diametro_m']].mean()

mask_quimica = (
    medias_setor['SETOR'].str.contains('Indústria Química', na=False)
    & medias_setor['altura_m'].isna()
)
medias_setor.loc[mask_quimica, ['altura_m', 'diametro_m']] = media_quimica.values

mask_auto = medias_setor['SETOR'].str.contains(
    'veículos automotores', na=False
)
medias_setor.loc[mask_auto, ['altura_m', 'diametro_m']] = media_ferro.values

mask_producao = (
    medias_setor['SETOR'].str.contains('Produção', na=False)
    & medias_setor['altura_m'].isna()
)
medias_setor.loc[mask_producao, ['altura_m', 'diametro_m']] = media_producao.values

# Renomeia colunas para não confundir
medias_aux = medias_setor.rename(
    columns={
        'altura_m': 'altura_media',
        'diametro_m': 'diametro_medio'
    }
)

# Faz o merge pelo SETOR
df = emissoes_industriais_total.merge(
    medias_aux,
    on='SETOR',
    how='left'
)

# Preenche os NaN com as médias do setor
df['altura_m'] = df['altura_m'].fillna(df['altura_media'])
df['diametro_m'] = df['diametro_m'].fillna(df['diametro_medio'])

# Remove colunas auxiliares
emissoes_industriais_total = df.drop(columns=['altura_media', 'diametro_medio'])

emissoes_industriais_total.to_csv(
    r"C:\IND_Inventory\Marcos\emission_total_light.csv",
    index=False)


