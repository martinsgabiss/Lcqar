#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 29 13:41:27 2026

@author: bruno
"""

#arquivo com codigos feitos, mas nao utilizados

#%% -------------- não usei mais - Criar gráfico COM TODAS AS REGIÕES

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

# Somar TOTAL por região e mês
dfRegiao = (
    dfOnibusUF
    .groupby(["REGIÃO", "ANO_MÊS"])["TOTAL"]
    .sum()
    .reset_index()
) 

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



# # COM REGRESSÃO E TAXA COMPOSTA MÉDIA

# RegrAnual = []

# for muni in dfOEA["MUNICIPIO"].unique():

#     dados = (
#         dfOEA[
#             dfOEA["MUNICIPIO"] == muni
#         ]
#         .sort_values("ANO")
#     )

#     x = dados["ANO"]
#     y = dados["ACUMULADO"]

#     regressao = linregress(x, y)

#     valor_inicial = y.iloc[0]
#     valor_final = y.iloc[-1]

#     anos = x.iloc[-1] - x.iloc[0]

#     if valor_inicial > 0 and anos > 0:

#         crescimento_anual = (
#             (
#                 valor_final / valor_inicial
#             ) ** (1 / anos) - 1
#         ) * 100

#     else:

#         crescimento_anual = np.nan

#     RegrAnual.append({

#         "Municipio": muni,

#         "UF": dados["UF"].iloc[0],

#         "Tendência (Ônibus/Ano)": regressao.slope,

#         "Crescimento Médio Anual (%)": crescimento_anual,

#         #"R²": regressao.rvalue**2
#     })

# dfTrendAnual = pd.DataFrame(RegrAnual)

#testar por estado com somatorio agrupado tbm

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