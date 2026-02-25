#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 20 11:16:05 2026

@author: gabriela
"""
#%% 

#importing

import pandas as pd
from speciate_to_cmaq import SpeciateToCMAQ as Speciator

df = pd.read_csv("/home/bruno/Downloads/emission_total_light_v2.csv")
dfprofile =pd.read_csv("/home/bruno/Downloads/InventorySpeciate_association.xlsx - Association_v2 (1).csv")

# Init object
my_speciator = Speciator()

# ======================
# PM
# ======================

lista_pm = []

for valor in dfprofile['PROFILE_PM'].dropna().unique(): #le cada linha da coluna 'PROFILE_PM'
    
    valor = str(valor).strip() #Transforma em string
    codigos = [v.strip() for v in valor.split(';')]
    
    pm_factors = my_speciator.generate_fractions(codigos)
    
    # 🔥 adiciona profile como coluna
    pm_factors['profile_codigo'] = valor
    
    lista_pm.append(pm_factors) #colocando o resultado dos fatores numa lista

pm_all = pd.concat(lista_pm, ignore_index=True) #junta tudo

# 🔥 transforma em índice
pm_all = pm_all.set_index('profile_codigo')


pm_wide = pm_all.pivot_table( #cria uma versão "larga", onde as "Species", viram colunas
    index='profile_codigo',
    columns='Species',
    values='Fraction',
    fill_value=0
).reset_index()

#pm_all.index.nunique()

# ======================
# GAS
# ======================

lista_gas = []

for valor in dfprofile['PROFILE_GAS'].dropna().unique():
    
    valor = str(valor).strip()
    codigos = [v.strip() for v in valor.split(';')]
    
    gas_factors = my_speciator.generate_fractions(codigos,
                                                      gas_tog_to_voc=True)
    #resultados_gas[idx] = gas_factors
    
    gas_factors['profile_codigo'] = valor
    
    lista_gas.append(gas_factors)
    

gas_all = pd.concat(lista_gas, ignore_index=True)

gas_wide = gas_all.pivot_table(
    index='profile_codigo',
    columns='Species',
    values='Fraction',
    fill_value=0
).reset_index()







# Generate fractions for PM profiles
# EXEMPLO pm_factors = my_speciator.generate_fractions(['8996VBS', '8995VBS'])
pm_factors = my_speciator.generate_fractions('91138')

#pm_factors['Fraction'].sum()

# Generate fractions for VOC profiles
gas_factors = my_speciator.generate_fractions(
    '6324',
    gas_tog_to_voc=True     # If your emission inventory output is VOC (no TOG)
) # o resultado vem em mol por algo

# PM Emission example
pm_heavy_duty_vehicles = 12060 # g/pixel/h

# Speciating
my_speciated_pm_emission = pm_factors * pm_heavy_duty_vehicles
my_speciated_pm_emission

# VOC Emission example
voc_heavy_duty_vehicles = 21351 # g/pixel/h

# Speciating
my_speciated_pm_emission = gas_factors * voc_heavy_duty_vehicles
 

