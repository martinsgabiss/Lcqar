#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

"""

import geopandas as gpd
import pandas as pd
import numpy as np
#from netCDFcreator import createNETCDFtemporal
#from temporalDisagregation import temporalDisagVehicular
import numpy.matlib
from shapely.geometry import Polygon, Point
from gridding import griddingMCIP, populatingGridTemp3D
from IND_speciate import IndSpeciate
from prepGrid import ioapiCoords, eqmerc2latlon
#import datetime
import netCDF4 as nc
import math
import matplotlib.pyplot as plt
import datetime

#%% MCIPDomain
def MCIPDomain(GRIDDOT2D):   
    print('Extracting MCIP GRIDDOT2D coordinates')
    
    #dataVar = list(ds.variables.keys())
    x = np.unique(GRIDDOT2D['LOND'][:])
    y = np.unique(GRIDDOT2D['LATD'][:])
    #-------------------- Reading industrial emissions-----------------------------   
    # Creating domain window
    domain = Polygon(zip([np.min(x),np.min(x),np.max(x),np.max(x)],
                         [np.min(y),np.max(y),np.max(y),np.min(y)])) 
    domain = gpd.GeoDataFrame(index=[0],geometry=[domain])
    domain.crs = "EPSG:4326"
    #Reading
    return domain,x,y

#%%

def frp_to_temperature(FRP_W, Af_m2, eps=1, Tbg_K=300.0):
    """Convert FRP (W) to effective fire temperature (K) assuming greybody.
    FRP ≈ σ ε Af (T^4 - Tbg^4)
    """
    sigma = 5.670374419e-8  # W m^-2 K^-4
    return ((FRP_W / (sigma * eps * Af_m2)) + (273+600)**4) ** 0.25

def frp_to_velocity(FRP, Af_m2, Tamb, Tfir):
    
    cp = 1670 # Ws/kg°C
    pa = 1.293 # air pressure in kg/m³
    
    e_0 = cp*pa*(Tfir-Tamb)
    
    return FRP/(Af_m2*e_0)

def convective_velocity_scale(H, T, q, zi, rho=1.225):
    """
    Compute AERMOD convective velocity scale (w*).

    Parameters
    ----------
    H   : surface sensible heat flux (W/m²)
    T   : air temperature (K) #MCIP
    q   : specific humidity (kg/kg) #MCIP
    zi  : mixing height (m) #MCIP
    rho : air density (kg/m³) #MCIP

    Returns
    -------
    w_star : convective velocity scale (m/s)
    """
    g = 9.8          # gravity (m/s²)
    cp = 1004.0      # specific heat of air (J/kg/K)

    # Virtual temperature
    Tv = T * (1 + 0.61 * q)

    # Virtual heat flux (w'θ'v)
    w_theta_v = H / (rho * cp)

    # AERMOD convective velocity
    w_star = (g * w_theta_v * zi / Tv) ** (1/3)

    return w_star

def frp_to_sensible_flux(frp_mw, area_m2, chi=0.35, beta=0.5):
    """
    Convert FRP (MW) to estimated surface sensible heat flux (W/m^2).

    Parameters
    ----------
    frp_mw : float
        Fire Radiative Power in megawatts (MW).
    area_m2 : float
        Area over which the heat is distributed (m^2).
    chi : float, optional
        Radiative fraction (FRP / total heat), typical range ~0.2-0.5. Default 0.35.
    beta : float, optional
        Fraction of non-radiative heat that becomes sensible. Default 0.5.

    Returns
    -------
    H : float
        Estimated surface sensible heat flux in W/m^2.
    Q_sensible : float
        Sensible heat power in W (absolute).
    Q_total : float
        Total heat release rate in W.
    """
    # conversions
    frp_w = frp_mw * 1e6  # MW -> W

    # total heat release rate (W)
    Q_total = frp_w / chi

    # non-radiative fraction (W)
    Q_nonrad = Q_total - frp_w

    # sensible heat (W)
    Q_sensible = beta * Q_nonrad

    # sensible flux (W/m^2)
    H = Q_sensible / area_m2

    return H


#%%
def emissFire(rootPath,domain):
    
    df = pd.read_csv(r"C:\IND_Inventory\FINN\FINNv2.5.1_modvrs_base_FRP_202310_c20240521.txt\FINNv2.5.1_modvrs_base_FRP_202310_c20240521.txt",
                     sep=',')
    
    df[['BMASS', 'coluna_apagar']] = df['BMASS'].str.extract(r'(\S+)\s+(\S+)')
    
    cols = ['PM10','NMHC','NO2','NO','NH3','BC','OC','TPC','TPM','PM25','SO2',
            'NOXasNO','H2','NMOC','CH4','CO','CO2','FRP']

    novo_frp = df['coluna_apagar']

    for i in range(len(cols) - 1):
        df[cols[i]] = df[cols[i + 1]]
    
    df['FRP'] = novo_frp
    
    df = df.drop(columns=['coluna_apagar'])
    
    df = df.astype(float)
    
    shp = gpd.read_file("C:\IND_Inventory\Inputs\shapefiles\GEOFT_PAIS\GEOFT_PAIS.shp")
    
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df['LONGI'], df['LATI']),
        crs="EPSG:4674"   # WGS84: longitude/latitude
    )
    
    gdf = gdf.clip(shp)
    
    lista_temperatura = []
    lista_velocidade = []

    for frp, area in zip(gdf['FRP'], gdf['AREA']):
        temp = frp_to_temperature(float(frp)*10**6, float(area))
        lista_temperatura.append(temp)
        
        H = frp_to_sensible_flux(float(frp), float(area))
        lista_velocidade.append(convective_velocity_scale(H, 300, 0, 1000))
    
    gdf['DIAMETRO'] = ((gdf['AREA']*4)/math.pi)**(1/2)
    
    gdf_2 = gdf[gdf['FRP']>0]

    fig, ax = plt.subplots(figsize=(8, 8))

    gdf_2.plot(
        column="FRP",
        ax=ax,
        legend=True,
        cmap="turbo",          # colormap contínuo
        vmin=gdf["FRP"].min(), # valor mínimo
        vmax=gdf["FRP"].max(), # valor máximo
        markersize=15*gdf["DIAMETRO"]/gdf["DIAMETRO"].max()
    )
    
    plt.show()
    
    dataEmissIND=1
    centerIND=1 
    emisPar=1
    
    return dataEmissIND, centerIND, emisPar

#%% emissReader
def emissReader(rootPath,domain,ano):
    
    try:
        datetime.date(ano,2,29)
        convTonAno2gs = 1e6/(366*24*3600) # Conversion from ton/year to g/s
    except ValueError:
        convTonAno2gs = 1e6/(365*24*3600) # Conversion from ton/year to g/s
    
    print(convTonAno2gs)

    print('Reading indutrial emissions from ' + rootPath+'/Inputs/emission_total_light.csv')
    dfind = pd.read_csv(rootPath+'/Inputs/emission_total_light.csv')
    
    # Converting to geodataframe
    ind = gpd.GeoDataFrame(
        dfind, geometry=gpd.points_from_xy(dfind.Longitude, dfind.Latitude))
    ind.crs = "EPSG:4326" # Setting EPSG
    #ind = ind[ind['Type']=='POINT'].copy()
    
    ind = ind[ind['ANO']==ano]
    
    # Cliping industries inside domain
    pip_mask = ind.within(domain.iloc[0,0])
    ind = ind.loc[pip_mask]
    ind=ind.reset_index(drop=True)
    
    # Selecting ID industry
    dataAssociation = ind[['SETOR','SNAP','Technology','Abatement','Fuel']]

    # Selecting data from industrial inventory - emissions in ton/year
    # Measured data
    dataEmissIND = ind[['PM10','SOx','CH4','NMVOC','CO','NOx','PM25','NH3']].copy() 
    
    # Converting from ton/year to g/s
    dataEmissIND=dataEmissIND*convTonAno2gs
    
    # Getting emissions centroid
    centerIND = ind.geometry.centroid
    centerIND.to_crs("EPSG:4326")
    
    df_association = pd.read_csv(rootPath+'/IndustrialSpeciation/InventorySpeciate_association.csv')
    df_association['SNAP'] = np.where(
        pd.to_numeric(df_association['SNAP'], errors='coerce').notna(),
        pd.to_numeric(df_association['SNAP'], errors='coerce').astype('Int64').astype(str),
        df_association['SNAP'].astype(str)
    )

    cols = ['SETOR','SNAP', 'Technology', 'Abatement', 'Fuel']

    dataAssociation_2 = dataAssociation
    dataAssociation_2['SNAP'] = np.where(
        pd.to_numeric(dataAssociation_2['SNAP'], errors='coerce').notna(),
        pd.to_numeric(dataAssociation_2['SNAP'], errors='coerce').astype('Int64').astype(str),
        dataAssociation_2['SNAP'].astype(str)
    )

    for c in cols:
        dataAssociation_2[c] = dataAssociation_2[c].astype(str).str.strip()
        df_association[c] = df_association[c].astype(str).str.strip()

    df_temp = dataAssociation_2.merge(
        df_association[['SETOR','SNAP', 'Technology', 'Abatement', 'Fuel', 'Temperatura']],
        on=['SETOR','SNAP', 'Technology', 'Abatement', 'Fuel'],
        how='left'
    )

    df_temp.to_csv(rootPath+'/Outputs/BR_12km/df_profiles_temp.csv')


    ind['Temperatura'] = df_temp['Temperatura'].astype(float)
    print(ind['Temperatura'][0])

    emisPar = ind[['altura_m', 'Temperatura', 'diametro_m','Velocidade']].copy()
    isna = emisPar.altura_m.isna()
    emisPar.altura_m[isna] = 50.0
    isna = emisPar.Temperatura.isna()
    emisPar.Temperatura[isna] = 300.0
    isna = emisPar.diametro_m.isna()
    emisPar.diametro_m[isna] = 1.0
    emisPar['velocidade_ms'] = 10.0
    
    emisPar.rename(columns={
        'altura_m': 'Hs',
        'diametro_m': 'Ds',
        'Temperatura': 'Ts',
        'Velocidade': 'Vs'
    }, inplace=True)
    
    return dataEmissIND, centerIND, emisPar, dataAssociation

'''
def emissReader_old(rootPath,domain):
    convKg2g = 1000 # Conversion from kg/s to g/s
    print('Reading indutrial emissions from ' + rootPath+'/Inputs/BR_Ind.xlsx')
    dfind = pd.read_excel(rootPath+'/Inputs/BR_Ind.xlsx')
    
    # Converting to geodataframe
    ind = gpd.GeoDataFrame(
        dfind, geometry=gpd.points_from_xy(dfind.Long, dfind.Lat))
    ind.crs = "EPSG:4326" # Setting EPSG
    #ind = ind[ind['Type']=='POINT'].copy()
    
    # Cliping industries inside domain
    pip_mask = ind.within(domain.iloc[0,0])
    ind = ind.loc[pip_mask]
    ind=ind.reset_index(drop=True)
    
    # Selecting ID industry
    dataTemp = ind['ID'] # FIXME

    # Selecting data from industrial inventory - emissions in kg/s
    # Measured data
    dataEmissIND = ind[['PMemis', 
                        'COemis', 
                        'NOxemis',
                        'SOxemis',
                        'VOCemis']].copy() 
    
    # Converting from kg/s to g/s
    dataEmissIND=dataEmissIND*convKg2g
    
    # Estimated data
    dataEmissINDestmeas = ind[['PMestmeas', 
                        'COestmeas', 
                        'NOxestmeas',
                        'SOxestmeas',
                        'VOCestmeas']].copy()
    
    # Converting from kg/s to g/s
    dataEmissINDestmeas=dataEmissINDestmeas*convKg2g 

    # Substituting nan by estimated data
    isna = dataEmissIND.isna()
    dataEmissIND[isna] = dataEmissINDestmeas[isna]
    dataEmissIND['ID'] = ind['ID']
    
    # Getting emissions centroid
    centerIND = ind.geometry.centroid
    centerIND.to_crs("EPSG:4326")
    
    emisPar = ind[['Hs', 'Ts', 'Ds', 'Vs']].copy()
    isna = emisPar.Hs.isna()
    emisPar.Hs[isna] = 50.0
    isna = emisPar.Ts.isna()
    emisPar.Ts[isna] = 30.0
    emisPar.Ts = emisPar.Ts+273
    isna = emisPar.Ds.isna()
    emisPar.Ds[isna] = 1.0
    isna = emisPar.Vs.isna()
    emisPar.Vs[isna] = 5.0
    emisPar.Hs[ind['Type']!='POINT'] = 1
    emisPar.Vs[ind['Type']!='POINT'] = 0.1

    
    return dataEmissIND, centerIND, emisPar, dataTemp #FIXME
'''
#%% temporalDesag

def hour_to_gwc(point,shp_lon):
    
    gdf_ponto = gpd.GeoDataFrame(
        geometry=[point],
        crs="EPSG:4326"
    )
    
    gdf_zonas = shp_lon.to_crs(gdf_ponto.crs)
    
    join = gpd.sjoin(
        gdf_ponto,
        gdf_zonas,
        how="left",
        predicate="within"
    )
    
    zone = join.loc[0, "zone"]
    
    return(int(zone))

def temporalDesag(dataAssociation,centerIND,date,rootPath):
    
    year = int(date.split('-')[0])
    month = int(date.split('-')[1])
    day = int(date.split('-')[2])
    
    data = datetime.datetime(year, month, day)
    data_antes = data - datetime.timedelta(days=1)
    
    weekday = (data.weekday()) % 7
    weekday_antes = (data_antes.weekday()) % 7
    
    month_antes = data_antes.month
    
    shp_lon = gpd.read_file(rootPath+'/Inputs/shapefiles/time_zones/ne_10m_time_zones.shp')
    
    tempPath = rootPath + '/IndustrialTemporal'
    
    temporal_disag = pd.DataFrame(
                    np.zeros((dataAssociation.shape[0], 25)),
                    columns=[f'{i}' for i in range(25)]
                )
    
    df_association = pd.read_csv(rootPath+'/IndustrialSpeciation/InventorySpeciate_association.csv')
    df_association['SNAP'] = np.where(
        pd.to_numeric(df_association['SNAP'], errors='coerce').notna(),
        pd.to_numeric(df_association['SNAP'], errors='coerce').astype('Int64').astype(str),
        df_association['SNAP'].astype(str)
    )
    
    cols = ['SETOR','SNAP', 'Technology', 'Abatement', 'Fuel']
    
    dataAssociation_2 = dataAssociation
    dataAssociation_2['SNAP'] = np.where(
        pd.to_numeric(dataAssociation_2['SNAP'], errors='coerce').notna(),
        pd.to_numeric(dataAssociation_2['SNAP'], errors='coerce').astype('Int64').astype(str),
        dataAssociation_2['SNAP'].astype(str)
    )
    
    for c in cols:
        dataAssociation_2[c] = dataAssociation_2[c].astype(str).str.strip()
        df_association[c] = df_association[c].astype(str).str.strip()    

    df_profiles = dataAssociation_2.merge(
        df_association[['SETOR','SNAP', 'Technology', 'Abatement', 'Fuel', 'NFR']],
        on=['SETOR','SNAP', 'Technology', 'Abatement', 'Fuel'],
        how='left'
    )
    
    df_profiles.to_csv(rootPath+'/Outputs/BR_12km/df_profiles_NFR.csv')

    for i in range(dataAssociation.shape[0]):
        
        h_to_gwc = hour_to_gwc(centerIND[i],shp_lon)
        
        h_min = 24+h_to_gwc
        h_max = h_min+25
        
        id_temp = str(df_profiles['NFR'][i])
        
        try:
            df_weekly = pd.read_csv(tempPath+'/'+id_temp+'_weekly.csv')
            df_hourly = pd.read_csv(tempPath+'/'+id_temp+'_hourly.csv')
            df_monthly = pd.read_csv(tempPath+'/'+id_temp+'_monthly.csv')
        except:
            df_weekly = pd.read_csv(tempPath+'/1.A.1.a_weekly.csv')
            df_hourly = pd.read_csv(tempPath+'/1.A.1.a_hourly.csv')
            df_monthly = pd.read_csv(tempPath+'/1.A.1.a_monthly.csv')
        
        fatores_antes = 7*df_weekly['factor'][weekday_antes]*12*df_monthly['factor'][month_antes-1]*24*df_hourly['factor'].values
        fatores = 7*df_weekly['factor'][weekday]*12*df_monthly['factor'][month-1]*24*df_hourly['factor'].values
        
        temporal_indices = list(fatores_antes)+list(fatores)
        temporal_indices1 = temporal_indices[h_min:h_max]
        
        temporal_disag.loc[i] = temporal_indices1
    
    temporal_disag.to_csv(rootPath+'/Outputs/BR_12km/df_temporal.csv')
    
    return temporal_disag

#%% gridSpec
def gridSpecMCIP (rootPath,outPath,date,
                  mcipMETCRO3Dpath,mcipMETCRO2Dpath,
                  mcipGRIDCRO2DPath,mcipGRIDDOT2DPath):
    
    print('Calling gridSpecMCIP')
    METCRO3D = nc.Dataset(mcipMETCRO3Dpath)
    METCRO2D = nc.Dataset(mcipMETCRO2Dpath)
    GRIDCRO2D = nc.Dataset(mcipGRIDCRO2DPath)
    GRIDDOT2D = nc.Dataset(mcipGRIDDOT2DPath)
    
    ano = int(date.split("-")[0])
    
    domain,x,y = MCIPDomain(GRIDDOT2D)
    
    dataEmissIND, centerIND, emisPar, dataAssociation = emissReader(rootPath,domain,ano) #FIXME
    
    temporal_disag = temporalDesag(dataAssociation,centerIND,date,rootPath)
    
    #Loop over each cel in x direction
    polygons=[]
    for ii in range(1,x.shape[0]):
        #Loop over each cel in y direction
        for jj in range(1,y.shape[0]):
            #roadClip=[]
            lat_point_list = [y[jj-1], y[jj], y[jj], y[jj-1]]
            lon_point_list = [x[ii-1], x[ii-1], x[ii], x[ii]]
            cel = Polygon(zip(lon_point_list, lat_point_list))
            polygons.append(cel)

    # Creating basegridfile
    baseGrid = gpd.GeoDataFrame({'geometry':polygons})
    baseGrid.to_csv(outPath+'/baseGrid'+'.csv')
    baseGrid.crs = "EPSG:4326" 
    print('baseGrid.csv was created at ' + outPath ) 
    
    #xv,yv,xX,yY = griddingMCIP(GRIDCRO2D,GRIDDOT2D)
    xv,yv,xX,yY = ioapiCoords(GRIDCRO2D)
    
    print('Grid')
    print(xv.max())
    print(yv.max())
    print(xX.max())
    print(yY.max())

    xlon,ylat = eqmerc2latlon(GRIDCRO2D,xv,yv)

    # Calling speciation function
    print('Speciating emissions')

    temporal_disag = temporalDesag(dataAssociation,centerIND,date,rootPath)

    dataEmissX,colunasX = IndSpeciate(rootPath,dataEmissIND,dataAssociation)
    
    dataTempo = populatingGridTemp3D(dataEmissX,centerIND,emisPar,xlon,ylat,
                                     temporal_disag,METCRO3D,METCRO2D,GRIDCRO2D) #FIXME
    
    return dataTempo,colunasX
