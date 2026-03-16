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
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.colors import SymLogNorm #Escala log
#import pandas as pd
import contextily as ctx
from pyproj import Transformer
import os
import glob 
import geopandas as gpd
#from shapely.geometry import Point #serve para criar geometrias espaciais
from shapely import contains_xy
import csv

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

#%% VISUALIZANDO NO DOMÍNIO BR - EMISSÃO POR POLUENTE

#Caminho para os arquivos netCDF
allArch = '/home/bruno/Gabriela/Lcqar/inputs/IndustrialInventory'

# Listar os arquivos .nc
arquivos_nc = sorted(glob.glob(os.path.join(allArch,'*.nc')))

# Abrir todos os arquivos como um único dataset (data cube) com xarray
try:
    #ds = xr.open_mfdataset(arquivos_nc, combine="by_coords")
    ds= xr.open_mfdataset(
        arquivos_nc, 
        combine="nested",
        concat_dim="TSTEP",
        chunks={}
        )
except ImportError as e:
    print("Erro ao abrir com xarray: ", e)

print(ds) # Informações do netcdf ex.: dimensões

# Coordenadas projetadas - chamando a função
xv, yv, lon, lat = ioapiCoords(ds)

# Converter para lat/lon - chamando a função - é EPS4326 - sistema em graus
xlon, ylat = eqmerc2latlon(ds, xv, yv)

# ========== Plotando com ESCALA LOG ===============

# Pega o colormap jet original
jet = plt.cm.get_cmap('jet', 256)

# Converte para array de cores
colors = jet(np.linspace(0, 1, 256))

# Define a primeira cor como branca
colors[0] = [1, 1, 1, 1]  # RGBA branco

# Cria novo colormap
jet_white = ListedColormap(colors)

# Converter lat/lon → Web Mercator - sistema em m
transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)

x_merc, y_merc = transformer.transform(xlon, ylat)

# Conferindo lat lon
# print('Lon min/max:', np.nanmin(x_merc), np.nanmax(x_merc))
# print('Lat min/max:', np.nanmin(ylat), np.nanmax(ylat))

cmap = jet_white.copy()
cmap.set_bad(alpha=0)

# Lista de variáveis do dataset
variaveis = [
    var for var in ds.data_vars
    if ds[var].ndim >= 3 and 'ROW' in ds[var].dims and 'COL' in ds[var].dims
]

# # Definindo o caminho para salvar o nome das especies químicas
# especies= "/home/bruno/Gabriela/Lcqar/outputs"
# os.makedirs(especies, exist_ok=True)

# caminho = os.path.join(especies, "variaveis.csv")

# # Salvando como csv
# with open(caminho, 'w', newline='') as f:
#     writer = csv.writer(f)
#     for item in variaveis:
#         writer.writerow([item])

# Definindo caminho para salvar os plots
pasta = "/home/bruno/Gabriela/Lcqar/figuras/Inventario"
os.makedirs(pasta, exist_ok=True)

# Looping para acessar cada variável e plotar
for var in variaveis:
    print("Processando:", var)
    
    dado = ds[var].sum(dim=['TSTEP', 'LAY'], skipna=True).compute()
    
    # Mascarar zeros
    dado_masked = dado.where(dado > 0)
    
    # Criar figura
    fig, ax = plt.subplots(figsize=(8,6))
    
    pcm = ax.pcolormesh( #pcolor
        x_merc, y_merc, dado_masked,
        norm=SymLogNorm(
            linthresh=1e-3,
            linscale=1,
            vmin=np.nanmin(dado_masked),
            vmax=np.nanmax(dado_masked)
        ),
        cmap=cmap
    )
    
    plt.colorbar(pcm, ax=ax, label=var)
    
    ax.set_xlim(np.nanmin(x_merc), np.nanmax(x_merc))
    ax.set_ylim(np.nanmin(y_merc), np.nanmax(y_merc))
    
    ctx.add_basemap(ax,
                    source=ctx.providers.CartoDB.Positron,
                    crs="EPSG:3857")
    
    plt.title(f"{var} - Total (log)")
    plt.tight_layout()
    #plt.show()
    
    caminho_arquivo = os.path.join(pasta, f"{var}.png")
    plt.savefig(caminho_arquivo, dpi=300, bbox_inches="tight")
    
    plt.close(fig)

    del dado
    del dado_masked
   
#%% VISUALIZANDO POR ESTADO PMC, NO2 E ALD2

# Definindo caminho para o arquivo .shp
estados = gpd.read_file("/home/bruno/Gabriela/Lcqar/inputs/IndustrialInventory/BR_UF_2024/BR_UF_2024.shp")

# Definindo o CRS - Coordinate Reference System 
estados = estados.to_crs("EPSG:4326")

# Definindo as especies que quero analisar
especies = ["PMC", "NO2", "ALD2"]

# Caminho para salvar os plots por Estado
pastaUF = "/home/bruno/Gabriela/Lcqar/figuras/Inventario/Estados"
os.makedirs(pasta, exist_ok=True)


#for idx, estado in estados.head(1).iterrows():
# Looping para analisar Estado por Estado
for idx, estado in estados.iterrows():
    
    estado_nome = estado["NM_UF"]
    print("Processando:", estado_nome)
    
    poligono = estado.geometry
    
    minx, miny, maxx, maxy = estado.geometry.bounds
    
    minx_m, miny_m = transformer.transform(minx, miny)
    maxx_m, maxy_m = transformer.transform(maxx, maxy)
    
    # máscara espacial do estado
    mask_estado = contains_xy(poligono, xlon, ylat)
   
    for var in especies:
        print("Processando:", var)
        
        dado_estado = ds[var].sum(dim=['TSTEP', 'LAY'], skipna=True).compute()
        
        dado_estado = dado_estado.where(mask_estado)
        # Mascarar zeros
        dado_masked_uf = dado_estado.where(dado_estado > 0)
        
        # Criar figura
        fig, ax = plt.subplots(figsize=(8,6))
        
        pcm = ax.pcolormesh( #pcolor
            x_merc, y_merc, dado_masked_uf,
            norm=SymLogNorm(
                linthresh=1e-3,
                linscale=1,
                vmin=np.nanmin(dado_masked_uf),
                vmax=np.nanmax(dado_masked_uf)
            ),
            cmap=cmap,
            alpha=0.8 #transparência pixels
        )
        
        plt.colorbar(pcm, ax=ax, label=var)
        
        ax.set_xlim(minx_m, maxx_m)
        ax.set_ylim(miny_m, maxy_m)
        
        
        # primeiro: satélite
        ctx.add_basemap(
            ax,
            source=ctx.providers.Esri.WorldImagery,
            crs="EPSG:3857"
        )
        
        # segundo: labels (cidades, fronteiras, etc)
        ctx.add_basemap(
            ax,
            source=ctx.providers.CartoDB.PositronOnlyLabels,
            crs="EPSG:3857"
        )
        
        gpd.GeoSeries([estado.geometry], crs="EPSG:4326").to_crs("EPSG:3857").boundary.plot(
            ax=ax,
            edgecolor="black", 
            linewidth=0.6, #espessura linha
            zorder=5 # Garante que fique acima de todas as camadas
            )    
        
        plt.title(f"{var} - Total (log)")
        plt.tight_layout()
        #plt.show()
        
        caminho_arquivo = os.path.join(pastaUF, f"{var} - {estado_nome}.png")
        plt.savefig(caminho_arquivo, dpi=300, bbox_inches="tight")
        
        plt.close(fig)
    
        del dado_estado
        del dado_masked_uf


#%% RASCUNHO

