# -*- coding: utf-8 -*-
"""
Created on Fri Feb 13 10:52:42 2026

@author: Leonardo.Hoinaski
"""
import numpy as np
import geopandas as gpd
import pyproj
import netCDF4 as nc
from shapely.geometry import Polygon
from pyproj import Proj



def grid_from_metcro3d(metcro3d):
    ds = nc.Dataset(metcro3d)
    grid={}

    grid["nrows"]=ds.dimensions["ROW"].size
    grid["ncols"]=ds.dimensions["COL"].size

    grid["xorig"]=ds.XORIG
    grid["yorig"]=ds.YORIG
    grid["dx"]=ds.XCELL
    grid["dy"]=ds.YCELL

    grid["proj"]=ds.GDTYP
    grid["p_alp"]=ds.P_ALP
    grid["p_bet"]=ds.P_BET
    grid["p_gam"]=ds.P_GAM
    grid["xcent"]=ds.XCENT
    grid["ycent"]=ds.YCENT

    return grid

def ioapiCoords(ds):
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

def domain_from_metcro3d(metcro3d):
    ds = nc.Dataset(metcro3d)
    xv,yv,lon,lat=ioapiCoords(ds)
    xlon,ylat = eqmerc2latlon(ds,xv,yv)
    
    xmin = xlon.min()
    ymin = ylat.min()
    xmax = xlon.max()
    ymax = ylat.max()
    
    
    poly = Polygon([
        (xmin,ymin),
        (xmax,ymin),
        (xmax,ymax),
        (xmin,ymax),
        (xmin,ymin)
    ])

    domain = gpd.GeoDataFrame(
        {"domain":["MCIP_domain"]},
        geometry=[poly],
        crs='4326'
    )

    return domain



def build_proj(grid):

    if grid["proj"]==2:   # Lambert
        proj=Proj(proj="lcc",
                  lat_1=grid["p_alp"],
                  lat_2=grid["p_bet"],
                  lat_0=grid["ycent"],
                  lon_0=grid["p_gam"])

    elif grid["proj"]==7: # Mercator
        proj=Proj(proj="merc",
                  lat_ts=grid["p_alp"],
                  lon_0=grid["p_gam"])

    elif grid["proj"]==5: # Polar
        proj=Proj(proj="stere",
                  lat_ts=grid["p_alp"],
                  lon_0=grid["p_gam"])

    elif grid["proj"]==1: # LatLon
        proj=None

    else:
        raise ValueError("Unsupported projection")

    return proj

