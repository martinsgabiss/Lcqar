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

# ---------IMPORTANDO PACOTES

import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.colors import SymLogNorm #Escala log
import contextily as ctx
from pyproj import Transformer
import os
import glob 
import geopandas as gpd
from shapely import contains_xy

import pyproj
import pandas as pd

#%% ---------- CAMINHOS

baseDir = "/home/bruno/Gabriela/Lcqar"

# Caminho base dados entrada
inDir = os.path.join(baseDir, "inputs", "IndustrialInventory")

# Caminho para salvar os plots 
# -> BR por poluente
outDir = os.path.join(baseDir, "figuras", "Inventario")
os.makedirs(outDir, exist_ok=True)

# -> Por estado e indústrias (por poluente)
outUfDir = os.path.join(outDir, "Estados")
os.makedirs(outUfDir, exist_ok=True)

# Arquivos específicos
arqIndustriais = os.path.join(inDir, "emission_total_light_v2.csv")
shapeEstados = os.path.join(inDir, "BR_UF_2024", "BR_UF_2024.shp")

#%% FUNÇÕES PARA TRAZER/LOCALIZAR/INSERIR LAT LON

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

#%% DOMÍNIO BR - EMISSÃO POR POLUENTE

# Listar os arquivos .nc
arquivos_nc = sorted(glob.glob(os.path.join(inDir,'*.nc')))

# Abrir todos os arquivos como um único dataset (data cube) com xarray
try:
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

# Looping para acessar cada variável e plotar
for var in variaveis:
    print("Processando:", var)
    
    dado = ds[var].sum(dim=['TSTEP', 'LAY'], skipna=True).compute()
    
    # Mascarar zeros
    dado_masked = dado.where(dado > 0)
    
    # Criar figura
    fig, ax = plt.subplots(figsize=(8,6))
    
    pcm = ax.pcolormesh( 
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
    
    caminho_arquivo = os.path.join(outDir, f"{var}.png")
    plt.savefig(caminho_arquivo, dpi=300, bbox_inches="tight")
    
    plt.close(fig)

    del dado
    del dado_masked
   
#%% VISUALIZANDO POR ESTADO PMC, NO2 E ALD2

# Shapefile dos estados
estados = gpd.read_file(shapeEstados)
estados = estados.to_crs("EPSG:4326")

# Especies que quero analisar
especies = ["PMC", "NO2", "ALD2"]

# Lendo o csv
df_ind = pd.read_csv(arqIndustriais)

#df_ind.columns
# Remove duplicatas
df_ind_unique = df_ind.drop_duplicates(subset=["Longitude","Latitude"])

# Converter para GeoDataFrame
gdf_ind = gpd.GeoDataFrame(
    df_ind_unique,
    geometry=gpd.points_from_xy(df_ind_unique["Longitude"], df_ind_unique["Latitude"]),
    crs="EPSG:4326"
)

#print("Total de registros:", len(df_ind_unique))
cmap = plt.cm.inferno

for idx, estado in estados.head(1).iterrows():
    
# Looping para analisar Estado por Estado
#for idx, estado in estados.iterrows():

    estado_nome = estado["NM_UF"]

    print("Processando:", estado_nome)
    
    poligono = estado.geometry #extrai a geometria de cada estado(polígono)

    # Corrige geometria
    poligono = poligono.buffer(0)
    
    # Se for MultiPolygon, pega só o maior (continente)
    if poligono.geom_type == "MultiPolygon":
        poligono = max(poligono.geoms, key=lambda g: g.area)
    
    # Limites do estado para metros (3857) 
    geom_estado_merc = gpd.GeoSeries([poligono], crs="EPSG:4326").to_crs("EPSG:3857")
    
    #Define limites para o mapa
    minx_m, miny_m, maxx_m, maxy_m = geom_estado_merc.total_bounds
   
    # Pontos das indústrias dentro do estado
    gdf_estado = gdf_ind[gdf_ind.geometry.within(poligono)]
    
    # Converter indústrias para metros
    if len(gdf_estado) > 0:
        gdf_estado_merc = gdf_estado.to_crs("EPSG:3857")
    
    for var in especies:
        print("Processando:", var)
        
        poligono_merc = geom_estado_merc.iloc[0]      
        
        dado_total = ds[var].sum(dim=['TSTEP', 'LAY'], skipna=True).compute()
        
        # Os pontos estão dentro do retângulo - + rápido computacionalmente
        cond = (
           (x_merc >= minx_m) & (x_merc <= maxx_m) &
           (y_merc >= miny_m) & (y_merc <= maxy_m)
        )
        
        # Verifica se cada ponto está dentro do polígono
        #mask_estado = contains_xy(poligono, xlon, ylat)
        mask_estado = contains_xy(poligono_merc, x_merc, y_merc)

        # Junta o retângulo com o polígono
        mask_final = cond & mask_estado

        # Aplica o mask_final 
        dado_plot = dado_total.where(mask_final)
        dado_plot = dado_plot.where(dado_plot > 0)
     
        # Criar figura
        fig, ax = plt.subplots(figsize=(8,6))
        
        ax.set_xlim(minx_m, maxx_m)
        ax.set_ylim(miny_m, maxy_m)
    
        # ctx.add_basemap(
        #     ax,
        # source=ctx.providers.CartoDB.Positron,
        # crs="EPSG:3857",
        # alpha=0.5,
        # zorder=1
        # )
        
        pcm = ax.pcolormesh(
            x_merc, y_merc, dado_plot,
            norm=SymLogNorm(
                linthresh=1e-3,
                linscale=1,
                vmin=np.nanpercentile(dado_plot.values, 5),
                vmax=np.nanpercentile(dado_plot.values, 95)
            ),
            cmap=cmap,
            alpha=1, #transparência pixels
            zorder=1,
            shading='auto')
        
        #plt.colorbar(pcm, ax=ax, label=var)
        cbar = plt.colorbar(pcm, ax=ax)
        cbar.set_label(f"{var} (concentração)")
        
        NÃO DEU CERTO DA EESCALA
        cbar.set_ticks([1e-3, 1e-2, 1e-1, 1, 10, 100, 1000])
        # vmin = np.nanpercentile(dado_plot.values, 5)
        # vmax = np.nanpercentile(dado_plot.values, 95)
        
        # # segurança
        # if vmin <= 0 or np.isnan(vmin):
        #     vmin = 1e-3
        # if vmax <= vmin:
        #     vmax = vmin * 10
        
        # ticks = np.logspace(
        #     np.floor(np.log10(vmin)),
        #     np.ceil(np.log10(vmax)),
        #     5
        # )
        
        # cbar.set_ticks(ticks)
        # cbar.ax.set_yticklabels([f"{t:.0e}" for t in ticks])


        gpd.GeoSeries([estado.geometry], crs="EPSG:4326").to_crs("EPSG:3857").boundary.plot(
            ax=ax,
            edgecolor="black", 
            linewidth=0.6, #espessura linha
            zorder=2 
            )    
        
        # pontos das indústrias
        if len(gdf_estado) > 0:
            gdf_estado_merc.plot(
                ax=ax,
                color="white",
                markersize=7,
                edgecolor="black",
                linewidth=0.5,
                alpha=0.9,
                zorder=3,
                label="Indústrias"
                )
        
        #plt.title(f"{var} - Total (log)\n {estado_nome}")
        fig.suptitle(
        f"{var} - Total (log)\n{estado_nome}",
        fontsize=10,
        fontweight="bold",
        y=0.98
        )
        
        #ax.legend(loc="upper right")
        #ax.legend(loc="upper left", bbox_to_anchor=(1, 1))
        ax.legend(loc="lower left")
        
        #plt.tight_layout()
        #plt.tight_layout(rect=[0, 0, 1, 0.95])
        plt.tight_layout(rect=[0, 0, 0.9, 0.93])
        
        #plt.show()
        ax.set_axis_off()
        
        caminho_arquivo = os.path.join(outUfDir, f"{var} - {estado_nome}.png")
        plt.savefig(caminho_arquivo, dpi=300, bbox_inches="tight")
        
        plt.close(fig)
    
        #del dado_estado
        del dado_total
        #del dado_masked_uf
        del dado_plot

print(estados.crs)
print(gdf_ind.crs)
print(x_merc.min(), x_merc.max())
print(xlon.min(), xlon.max())
