# -*- coding: utf-8 -*-
"""
Created on Wed Mar 20 15:11:15 2024

@author: EricTien
modified from Ashesh Chattopadhyay https://github.com/ashesh6810/Generative_Models_SGS/blob/main/beta_conv_vae.py

"""

import numpy as np
import torch
print(torch.__version__)
import glob
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
#from torchinfo import summary
import sys
from datetime import date,timedelta
import netCDF4 as nc
from saveNCfile import savenc
import xarray as xr
import rioxarray as rxr
from GFS_data_check import check_GFS_validility

def load_train_data(daystart,dayend,pathgfs,pathdaymet):
    day=daystart
    gfsall,daymetall=[],[]
    while day<dayend:
        for times in range(1,5):
            hour=times*6
            if hour<10:
                hourstr='06'
            else:
                hourstr=str(hour)
            gfstemp=xr.open_dataset(pathgfs+'/data/'+str(day.year)+'/gfs.0p25.'+day.strftime('%Y%m%d')+'00.f0'+hourstr+'.grib2')
            if times==1:
                gfsdaily=gfstemp
            else:
                gfsdaily=gfsdaily+gfstemp
        gfsall.append(gfsdaily.to_array()[0])
        day=day+timedelta(1)
    day=daystart
    daymet=xr.open_dataset(pathdaymet+'/daymet_v4_daily_na_prcp_'+str(day.year)+'.nc')
    # clip for around west US
    dayofyearstart=(daystart-date(daystart.year,1,1)).days+1
    dayofyearend=(dayend-date(daystart.year,1,1)).days+1
    daymetall=daymet.prcp[dayofyearstart-1:dayofyearend-1,((daymet.y>-1500000)&(daymet.y<1500000)),((daymet.x>-2000000)&(daymet.x<-500000))]
    
    p_input=np.array(gfsall)
    p_label=np.array(daymetall)
    
    p_input_torch=torch.from_numpy(p_input).float()
    p_label_torch=torch.from_numpy(p_label).float()
    p_input_torch=torch.unsqueeze(p_input_torch,1)
    p_label_torch=torch.unsqueeze(p_label_torch,1)
    return p_input_torch , p_label_torch

def load_train_data_PRISM(daystart,dayend,pathgfs,pathPRISM):
    day=daystart
    gfsall,PRISMall=[],[]
    validdatelist=[]
    fhourlist=list(range(6,241,6))
    for hour in range(252,385,12):
        fhourlist.append(hour)
    fhourlist=np.array(fhourlist)
    while day<dayend:
        gfsdaily=[]
        files=glob.glob('data/'+str(day.year)+'/gfs.0p25.'+day.strftime('%Y%m%d')+'00*.grib2')
        if len(files)!=len(fhourlist):
            day=day+timedelta(1)
            continue
        else:
            validdatelist.append(day)
            
        for lforecast in [1,3,5,7,10,16]:
            gfs=[]
            if lforecast==1:
                fhour=fhourlist[0:4]
            elif lforecast==3:
                fhour=fhourlist[4:12]
            elif lforecast==5:
                fhour=fhourlist[12:20]
            elif lforecast==7:
                fhour=fhourlist[20:28]
            elif lforecast==10:
                fhour=fhourlist[28:40]
            elif lforecast==16:
                fhour=fhourlist[40:52]
            for times in fhour:
                if times<10:
                    hourstr='00'+str(times)
                elif times<100:
                    hourstr='0'+str(times)
                else:
                    hourstr=str(hour)
                gfstemp=xr.open_dataset(pathgfs+'/data/'+str(day.year)+'/gfs.0p25.'+day.strftime('%Y%m%d')+'00.f'+hourstr+'.grib2')
                if type(gfs)==list:
                    gfs=gfstemp
                else:
                    gfs=gfs+gfstemp
            gfsdaily.append(gfs.to_array()[0])
        gfsdaily=np.array(gfsdaily)
        gfsall.append(gfsdaily)
        day=day+timedelta(1)
    for day in validdatelist:
        PRISMdaily=[]
        for length in [1,3,5,7,10,16]:
            PRISM=[]
            for d in range(length):
                PRISMtemp=rxr.open_rasterio(pathPRISM+'/PRISM_ppt_stable_4kmD2_'+(day+timedelta(d)).strftime('%Y%m%d')+'_bil.bil')[0]
                PRISMtemp=PRISMtemp.where(PRISMtemp>=0)
                # clip for around west US
                PRISMtemp=PRISMtemp[PRISMtemp.y>30,PRISMtemp.x<-105]
                if type(PRISM)==list:
                    PRISM=PRISMtemp
                else:
                    PRISM=PRISM+PRISMtemp
            PRISMdaily.append(PRISM.values)
        PRISMdaily=np.array(PRISMdaily)
        PRISMall.append(PRISMdaily)
    
    p_input=np.array(gfsall)
    p_label=np.array(PRISMall)
    
    p_input_torch=torch.from_numpy(p_input).float()
    p_label_torch=torch.from_numpy(p_label).float()
    return p_input_torch , p_label_torch

#%% testing
'''
pathgfs='C:/UCLA/research/medium range'
pathPRISM='C:/UCLA/research/PRISM daily'
a,b=load_train_data_PRISM(date(2015,1,15),date(2015,3,31),pathgfs,pathPRISM)'''