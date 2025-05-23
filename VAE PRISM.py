# -*- coding: utf-8 -*-
"""
Created on Wed Mar 20 11:16:42 2024

@author: EricTien
modified from Ashesh Chattopadhyay https://github.com/ashesh6810/Generative_Models_SGS/blob/main/beta_conv_vae.py
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision
from torchvision import datasets, transforms
from torchvision.utils import save_image
import matplotlib.pyplot as plt
import numpy as np
import netCDF4 as nc
from datetime import date,timedelta

import os
os.chdir(r'C:/UCLA/research/medium range')
#from data_loader_new import load_test_data
from data_loader_new import load_train_data_PRISM
"""
Determine if any GPUs are available
"""
##### prepare test data ###################################################
'''
FF=nc.Dataset('/glade/scratch/asheshc/theory-interp/QG/larger_domain_QG/Dry'+str(9)+'/U_output.nc')
GG=nc.Dataset('/glade/scratch/asheshc/theory-interp/QG/larger_domain_QG/Dry'+str(9)+'/V_output.nc')
lat=np.asarray(FF['lat'])
lon=np.asarray(FF['lon'])

lead = 1

psi_test_input_Tr_torch, psi_test_label_Tr_torch  = load_test_data(FF,GG,lead)

psi_test_label_Tr_unnormalized = psi_test_label_Tr_torch.detach().cpu().numpy()


dim_lon = int(142)
new_lat = lat[74:216]

M_test_level1 = torch.mean(torch.flatten(psi_test_input_Tr_torch[:,0,:,:]))
STD_test_level1 = torch.std(torch.flatten(psi_test_input_Tr_torch[:,0,:,:]))

M_test_level2 = torch.mean(torch.flatten(psi_test_input_Tr_torch[:,1,:,:]))
STD_test_level2 = torch.std(torch.flatten(psi_test_input_Tr_torch[:,1,:,:]))


M_test_level3 = torch.mean(torch.flatten(psi_test_input_Tr_torch[:,2,:,:]))
STD_test_level3 = torch.std(torch.flatten(psi_test_input_Tr_torch[:,2,:,:]))

M_test_level4 = torch.mean(torch.flatten(psi_test_input_Tr_torch[:,3,:,:]))
STD_test_level4 = torch.std(torch.flatten(psi_test_input_Tr_torch[:,3,:,:]))


psi_test_input_Tr_torch_norm_level1 = ((psi_test_input_Tr_torch[:,0,None,:,:]-M_test_level1)/STD_test_level1)
psi_test_input_Tr_torch_norm_level2 = ((psi_test_input_Tr_torch[:,1,None,:,:]-M_test_level2)/STD_test_level2)
psi_test_input_Tr_torch_norm_level3 = ((psi_test_input_Tr_torch[:,2,None,:,:]-M_test_level3)/STD_test_level3)
psi_test_input_Tr_torch_norm_level4 = ((psi_test_input_Tr_torch[:,3,None,:,:]-M_test_level4)/STD_test_level4)



psi_test_input_Tr_torch  = torch.cat((psi_test_input_Tr_torch_norm_level1,psi_test_input_Tr_torch_norm_level2,psi_test_input_Tr_torch_norm_level3,psi_test_input_Tr_torch_norm_level4),1)



psi_test_label_Tr_torch_norm_level1 = (psi_test_label_Tr_torch[:,0,None,:,:]-M_test_level1)/STD_test_level1
psi_test_label_Tr_torch_norm_level2 = (psi_test_label_Tr_torch[:,1,None,:,:]-M_test_level2)/STD_test_level2
psi_test_label_Tr_torch_norm_level3 = (psi_test_label_Tr_torch[:,2,None,:,:]-M_test_level3)/STD_test_level3
psi_test_label_Tr_torch_norm_level4 = (psi_test_label_Tr_torch[:,3,None,:,:]-M_test_level4)/STD_test_level4



psi_test_label_Tr_torch = torch.cat((psi_test_label_Tr_torch_norm_level1,psi_test_label_Tr_torch_norm_level2,psi_test_label_Tr_torch_norm_level3,psi_test_label_Tr_torch_norm_level4),1)

print('shape of normalized input test',psi_test_input_Tr_torch.shape)
print('shape of normalized label test',psi_test_label_Tr_torch.shape)
'''
################### Load training data files ########################################
'''fileList_train_U=[]
fileList_train_V=[]
mylist = [1,2,3,4,5,6,7,8,10]
for k in mylist:
  fileList_train_U.append ('/glade/scratch/asheshc/theory-interp/QG/larger_domain_QG/Dry'+str(k)+'/U_output.nc')
  fileList_train_V.append ('/glade/scratch/asheshc/theory-interp/QG/larger_domain_QG/Dry'+str(k)+'/V_output.nc')
'''
pathgfs='C:/UCLA/research/medium range'
pathPRISM='C:/UCLA/research/PRISM daily'
startdaylist,enddaylist=[],[]
for years in range(2017,2022):
    startdaylist.append(date(years,1,1))
    enddaylist.append(date(years+1,1,1))

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

dimxin=89
dimyin=89
dimxout=478
dimyout=480
num_filters=32

class VAE(nn.Module):
    def __init__(self, imgChannels=1, out_channels=1, featureDim=num_filters*dimxin*dimyin, zDim=128):
        super(VAE, self).__init__()

        # Initializing the 2 convolutional layers and 2 full-connected layers for the encoder
        self.encConv1 = (nn.Conv2d(imgChannels, num_filters, kernel_size=5, stride=1, padding='same'))
        self.encConv2 = (nn.Conv2d(num_filters, num_filters, kernel_size=5, stride=1, padding='same'))
        self.encFC1 = nn.Linear(featureDim, zDim)
        self.encFC2 = nn.Linear(featureDim, zDim)

        # Initializing the fully-connected layer and 2 convolutional layers for decoder
        self.decFC1 = nn.Linear(zDim, num_filters*dimxout*dimyout)
        self.decConv1 = (nn.Conv2d(num_filters, num_filters, kernel_size=5, stride=1, padding='same' ))
        self.decConv2 = (nn.Conv2d(num_filters, out_channels, kernel_size=5, stride=1, padding='same' ))
        

    def encoder(self, x):

        # Input is fed into 2 convolutional layers sequentially
        # The output feature map are fed into 2 fully-connected layers to predict mean (mu) and variance (logVar)
        # Mu and logVar are used for generating middle representation z and KL divergence loss
        x = F.relu(self.encConv1(x))
        x = F.relu(self.encConv2(x))
        #print(x.shape)
        x = x.view(-1, num_filters*dimxin*dimyin)
        mu = self.encFC1(x)
        logVar = self.encFC2(x)
        return mu, logVar

    def reparameterize(self, mu, logVar):

        #Reparameterization takes in the input mu and logVar and sample the mu + std * eps
        std = torch.exp(logVar/2)
        eps = torch.randn_like(std)
        return mu + std * eps

    def decoder(self, z):

        # z is fed back into a fully-connected layers and then into two transpose convolutional layers
        # The generated output is the same size of the original input
        x = F.relu(self.decFC1(z))
        #print(x.shape)
        x = x.view(-1, num_filters, dimxout, dimyout)
        x = F.relu(self.decConv1(x))
        x = (self.decConv2(x))
        return x

    def forward(self, x):

        # The entire pipeline of the VAE: encoder -> reparameterization -> decoder
        # output, mu, and logVar are returned for loss computation
        mu, logVar = self.encoder(x)
        z = self.reparameterize(mu, logVar)
        out = self.decoder(z)
        return out, mu, logVar

batch_size = 2
learning_rate = 1e-4
beta=5.0
num_epochs=200
trainN=700
net = VAE()
net.cuda()
optimizer = torch.optim.Adam(net.parameters(), lr=learning_rate)
mse_loss = nn.MSELoss()

#%%

losslist=[]
for epoch in range(0, num_epochs):  # loop over the dataset multiple times

    running_loss = 0.0
    for (loop1,loop2) in zip(startdaylist,enddaylist):
     print('Training loop start day',loop1)
     print('Training loop end day',loop2)


     p_train_input_torch , p_train_label_torch = load_train_data_PRISM(loop1, loop2, pathgfs, pathPRISM)


###### normalize each batch ##########

     M_train_level1 = torch.mean(torch.flatten(p_train_input_torch[:,0,:,:]))
     STD_train_level1 = torch.std(torch.flatten(p_train_input_torch[:,0,:,:]))
     M_train_level2 = torch.mean(torch.flatten(p_train_input_torch[:,1,:,:]))
     STD_train_level2 = torch.std(torch.flatten(p_train_input_torch[:,1,:,:]))
     M_train_level3 = torch.mean(torch.flatten(p_train_input_torch[:,2,:,:]))
     STD_train_level3 = torch.std(torch.flatten(p_train_input_torch[:,2,:,:]))
     M_train_level4 = torch.mean(torch.flatten(p_train_input_torch[:,3,:,:]))
     STD_train_level4 = torch.std(torch.flatten(p_train_input_torch[:,3,:,:]))
     M_train_level5 = torch.mean(torch.flatten(p_train_input_torch[:,4,:,:]))
     STD_train_level5 = torch.std(torch.flatten(p_train_input_torch[:,4,:,:]))
     M_train_level6 = torch.mean(torch.flatten(p_train_input_torch[:,5,:,:]))
     STD_train_level6 = torch.std(torch.flatten(p_train_input_torch[:,5,:,:]))

     p_train_input_torch_norm_level1 = ((p_train_input_torch[:,0,:,:]-M_train_level1)/STD_train_level1).unsqueeze(1)
     p_train_input_torch_norm_level2 = ((p_train_input_torch[:,1,:,:]-M_train_level2)/STD_train_level2).unsqueeze(1)
     p_train_input_torch_norm_level3 = ((p_train_input_torch[:,2,:,:]-M_train_level3)/STD_train_level3).unsqueeze(1)
     p_train_input_torch_norm_level4 = ((p_train_input_torch[:,3,:,:]-M_train_level4)/STD_train_level4).unsqueeze(1)
     p_train_input_torch_norm_level5 = ((p_train_input_torch[:,4,:,:]-M_train_level5)/STD_train_level5).unsqueeze(1)
     p_train_input_torch_norm_level6 = ((p_train_input_torch[:,5,:,:]-M_train_level6)/STD_train_level6).unsqueeze(1)

     p_train_input_torch = torch.cat((p_train_input_torch_norm_level1,p_train_input_torch_norm_level2,p_train_input_torch_norm_level3,
                                      p_train_input_torch_norm_level4,p_train_input_torch_norm_level5,p_train_input_torch_norm_level6))

     p_train_label_torch_norm_level1 = ((p_train_label_torch[:,0,:,:]-M_train_level1)/STD_train_level1).unsqueeze(1)
     p_train_label_torch_norm_level2 = ((p_train_label_torch[:,1,:,:]-M_train_level2)/STD_train_level2).unsqueeze(1)
     p_train_label_torch_norm_level3 = ((p_train_label_torch[:,2,:,:]-M_train_level3)/STD_train_level3).unsqueeze(1)
     p_train_label_torch_norm_level4 = ((p_train_label_torch[:,3,:,:]-M_train_level4)/STD_train_level4).unsqueeze(1)
     p_train_label_torch_norm_level5 = ((p_train_label_torch[:,4,:,:]-M_train_level5)/STD_train_level5).unsqueeze(1)
     p_train_label_torch_norm_level6 = ((p_train_label_torch[:,5,:,:]-M_train_level6)/STD_train_level6).unsqueeze(1)
     
     p_train_label_torch = torch.cat((p_train_label_torch_norm_level1,p_train_label_torch_norm_level2,p_train_label_torch_norm_level3, 
                                      p_train_label_torch_norm_level4,p_train_label_torch_norm_level5,p_train_label_torch_norm_level6))

     for step in range(0,360,batch_size):
        # get the inputs; data is a list of [inputs, labels]
        indices = np.random.permutation(np.arange(start=step, stop=step+batch_size))
        input_batch, label_batch = p_train_input_torch[indices,:,:,:], p_train_label_torch[indices,:,:,:]
        #print('shape of input', input_batch.shape)
        #print('shape of output', label_batch.shape)

        # zero the parameter gradients
        optimizer.zero_grad()

        # forward + backward + optimize
#        output,_,_,_,_,_,_ = net(input_batch.cuda())
        output, mu, logVar = net(input_batch.cuda())
        mask=torch.isnan(label_batch)
        output[mask]=0
        label_batch[mask]=0
        kl_divergence = 0.5 * torch.sum(-1 - logVar + mu.pow(2) + logVar.exp())
        loss = mse_loss(output,label_batch.cuda()) + beta*kl_divergence 
        loss.backward()
        optimizer.step()
        if step % 60 == 0:    # print every 2000 mini-batches
            print('[%d, %5d] loss: %.3f' %
                  (epoch + 1, step + 1, loss))
            losslist.append(loss)
        
print('Finished Training')


torch.save(net.state_dict(), 'VAE 1 day PRISM.pt')

print('BNN Model Saved')



