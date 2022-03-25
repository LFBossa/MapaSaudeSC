#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd


# In[2]:


caminho = "data/"


# In[3]:


ceps = pd.read_csv(caminho + "CEPdatabase.csv")
ceps.set_index("cep", inplace=True) # index numérico


# In[4]:


regioes = pd.read_csv(caminho + "regioes-saude.csv")
regioes.set_index("CODIBGE", inplace=True) # index numérico


# In[5]:


tipo_unidade = pd.read_csv(caminho + "tipo_unidade.csv")
tipo_unidade.set_index("cod", inplace=True)


# In[6]:


ST = pd.read_csv(caminho + "STSC202202.csv", low_memory=False)


# In[8]:


estabelecimentos = pd.read_csv(caminho + "estabelecimentos-420000-202202.csv")
estabelecimentos.set_index("CNES",inplace=True)

