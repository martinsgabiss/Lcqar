#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 28 16:33:06 2022

Created on Fri Jul 22 13:32:45 2022
https://www.cmascenter.org/cmaq/science_documentation/pdf/ch09.pdf
https://www.sciencedirect.com/science/article/pii/S0269749111002387#bib18
https://www.sciencedirect.com/science/article/pii/S1352231014008188#bib14
https://acp.copernicus.org/articles/18/14695/2018/

@author: leohoinaski
"""
#import netCDF4 as nc
import numpy as np
#import matplotlib.pyplot as plt
from scipy.stats import norm
from gridPlumeRise import BRIGGSplumeRise

def pressure2alt (P0,P,T):
    P0 = np.array(P0)
    P = np.array(P)
    Temp = np.array(T[1::])
    #https://physics.stackexchange.com/questions/333475/how-to-calculate-altitude-from-current-temperature-and-pressure
    # Estimating altitude 
    alt = (((P0/P)**(1/5.257) -1)*(Temp))/(0.0065)
    
    return alt
                         

def verticalProfile(dTdZ, altSigmas,Hef,HT):
    A = 15 #https://www.cmascenter.org/cmaq/science_documentation/pdf/ch09.pdf
    B = 117
    sgz0 = A*np.exp(-B*dTdZ)
    if sgz0 < 3:
        sgz0 = 3
    altSigmas0 = np.append(2,altSigmas)
    factor= np.diff(norm.cdf(altSigmas0, Hef+HT, sgz0))
    factor = np.absolute(factor)# FIXME
    if np.sum(factor)>0:# FIXME
        factor = factor/sum(factor)# FIXME
    else:
        factor[0] = 1
    return factor,sgz0
    

def ptVerticalProfile(P,T,Uas,HT,Ts,Vs,Ds,Hs): 
   
    P0 = 101325
    
    altSigmas = pressure2alt(P0,P,T)
   
    dTdZ = np.diff(T)/np.diff(np.append(2,altSigmas))
    if (Hs+HT)>altSigmas[0]:
        dTdZ = dTdZ[np.where((Hs+HT)>altSigmas)[-1][-1]]
        Tas = T[np.where((Hs+HT)>altSigmas)[-1][-1]]
    else:
        dTdZ = dTdZ[0]
        Tas = T[0]
    
    Hef = BRIGGSplumeRise(Ts,Vs,Ds,Hs,Tas,Uas,dTdZ)
    
    factor,sgz0 = verticalProfile(dTdZ, altSigmas,Hef,HT)
    
    return factor
