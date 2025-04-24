# -*- coding: utf-8 -*-
"""
Created on Wed Apr 10 18:04:17 2024

@author: erict
"""

import os,glob
os.chdir(r'C:/UCLA/research/medium range')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.dates import DateFormatter
from matplotlib.colors import ListedColormap
from netCDF4 import Dataset
import numpy as np
import pandas as pd
import xarray as xr
import rioxarray as rxr
import geopandas as gpd
import fiona
import scipy
from datetime import date, timedelta


#%%
'''fhourlist=list(range(6,241,6))
for hour in range(252,385,12):
    fhourlist.append(hour)

for year in range(2015,2024):
    valid=True
    if year==2015:
        startdate=date(year,1,15)
    else:
        startdate=date(year,1,1)
    day=startdate
    while day < date(year+1,1,1):
        files=glob.glob('data/'+str(year)+'/gfs.0p25.'+day.strftime('%Y%m%d')+'00*.grib2')
        if len(files)!=len(fhourlist):
            valid=False
            print(day.strftime('%Y%m%d')+' data corrupted.')
        day=day+timedelta(days=1)
    if valid==True:
        print(str(year)+' data ok.')'''

def check_GFS_validility(year):
    fhourlist=list(range(6,241,6))
    for hour in range(252,385,12):
        fhourlist.append(hour)
    valid,datelist=[],[]
    if year==2015:
        startdate=date(year,1,15)
    else:
        startdate=date(year,1,1)
    day=startdate
    while day < date(year+1,1,1):
        files=glob.glob('data/'+str(year)+'/gfs.0p25.'+day.strftime('%Y%m%d')+'00*.grib2')
        if len(files)!=len(fhourlist):
            valid.append(False)
        else:
            valid.append(True)
        datelist.append(day)
        day=day+timedelta(days=1)
    valid=pd.Series(valid,index=datelist)
    return valid

def GFS_valid_data_date(datestart,dateend):
    return 0