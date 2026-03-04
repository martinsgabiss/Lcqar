#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 27 17:19:09 2026

==Explorando o netCDF do Inventário Industrial==

Neste script serão desenvolvidos gráficos que demonstram a emissão
por poluente no domínio do Brasil do Inventário Industrial e análise 
de uma série temporal

Dimensions:  (TSTEP: 25, - 25 passos de tempo - 00h às 24h
              VAR: 54, - 54 variáveis (espécies químicas)
              DATE-TIME: 2, - [DATA, HORA]
              LAY: 40, - 40 camadas verticais
              ROW: 406, - grade Y - domínio pixel
              COL: 379 - grade X - domínio pixel
              )

@author: bruno
"""

import xarray as xr
#import netCDF4 as nc
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.colors import SymLogNorm #Escala log
#import pandas as pd
import contextily as ctx
#import geopandas as gpd
from pyproj import Transformer

import pyproj

#%% PARA TRAZER/LOCALIZAR/INSERIR LAT LON

def ioapiCoords(ds): #criar as coordenadas X e Y reais da grade
    # Latlon
    lonI = ds.XORIG
    latI = ds.YORIG
    
    # Cell spacing 
    xcell = ds.XCELL
    ycell = ds.YCELL
    ncols = ds.NCOLS
    nrows = ds.NROWS
    
    lon = np.arange(lonI,(lonI+ncols*xcell),xcell)
    lat = np.arange(latI,(latI+nrows*ycell),ycell)
    
    xv, yv = np.meshgrid(lon,lat)
    return xv,yv,lon,lat

def eqmerc2latlon(ds,xv,yv):

    mapstr = '+proj=merc +a=%s +b=%s +lat_ts=0 +lon_0=%s' % (
              6370000, 6370000, ds.XCENT)
    #p = pyproj.Proj("+proj=merc +lon_0="+str(ds.P_GAM)+" +k=1 +x_0=0 +y_0=0 +a=6370000 +b=6370000 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs")
    p = pyproj.Proj(mapstr)
    xlon, ylat = p(xv, yv, inverse=True)
    
    return xlon,ylat

#%% EXPLORANDO O NETCDF

#Caminho para o arquivo .nc
netCDFpath = '/home/bruno/Gabriela/Lcqar/inputs/IndustrialInventory/IND2CMAQ_2023_03_01_0000_to_2023_03_02_0000.nc'

# Abrindo o arquivo
ds= xr.open_dataset(netCDFpath)

print(ds) # Informações do netcdf ex.: dimensões

#list(ds.data_vars) # Acessar o nome das espécies químicas

# Coordenadas projetadas
xv, yv, lon, lat = ioapiCoords(ds)

# Converter para lat/lon
xlon, ylat = eqmerc2latlon(ds, xv, yv)

PMC_total = ds['PMC'][:]
PMC_total = np.nansum(np.nansum(PMC_total,axis=0),axis=0)

# Somou todas as horas e as camadas, ignorou os nan's 

print(PMC_total.data)

# # ========== Plotando com escala linear ============
# plt.figure(figsize=(8,6))
# PMC_total.plot(cmap='jet_r')
# #plt.imshow(PMC_total, cmap='jet_r')
# #plt.colorbar(label='PMC')
# plt.title('PMC')
# plt.show()

# ========== Plotando com ESCALA LOG ===============

# Pega o colormap jet original
jet = plt.cm.get_cmap('jet', 256)

# Converte para array de cores
colors = jet(np.linspace(0, 1, 256))

# Define a primeira cor como branca
colors[0] = [1, 1, 1, 1]  # RGBA branco

# Cria novo colormap
jet_white = ListedColormap(colors)

# Converter lat/lon → Web Mercator
transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)

x_merc, y_merc = transformer.transform(xlon, ylat)

# Conferindo lat lon
# print('Lon min/max:', np.nanmin(x_merc), np.nanmax(x_merc))
# print('Lat min/max:', np.nanmin(ylat), np.nanmax(ylat))

PMC_masked = np.ma.masked_where(PMC_total <= 0, PMC_total) #mascarar zeros

cmap = jet_white.copy()
cmap.set_bad(alpha=0)

# Ploting
fig, ax = plt.subplots(figsize=(8,6))

pcm = ax.pcolor(
    x_merc, y_merc, PMC_masked,
    norm=SymLogNorm(
        linthresh=1e-3,
        linscale=1,
        vmin=np.nanmin(PMC_masked),
        vmax=np.nanmax(PMC_masked)
    ),
    cmap=cmap
)

plt.colorbar(pcm, ax=ax, label='PMC')

ax.set_xlim(np.nanmin(x_merc), np.nanmax(x_merc))
ax.set_ylim(np.nanmin(y_merc), np.nanmax(y_merc))

# Mapa de fundo
ctx.add_basemap(ax, 
                source=ctx.providers.CartoDB.Positron,
                crs="EPSG:3857")
#ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron)

plt.title("PMC Total - escala log")
plt.xlabel(" ")
plt.ylabel(" ")
plt.show()


# =========== Total emitido por especie ============= N FUNCIONOU

# Total emitido ETOH 
# etoh_total = ds['ETOH'].sum(dim=['TSTEP','LAY','ROW','COL'])
# print(etoh_total.values)

totais = (
    ds
    .drop_vars('TFLAG')   # remove TFLAG
    .sum(dim=['TSTEP','LAY','ROW','COL'])
)

#print(totais)
for var in totais.data_vars:
    print(var, float(totais[var].values))



