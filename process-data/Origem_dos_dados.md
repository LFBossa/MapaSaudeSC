# De onde vem os dados

## Dados de estabelecimentos: 

- Baseado em [Getting_CNES_Data](https://github.com/AlertaDengue/PySUS/raw/master/pysus/Notebooks/Getting_CNES_Data.ipynb)
- Criei o arquivo [GettingST_PySUS](GettingST_PySUS.ipynb)
- Segunda fonte de dados [CNES](https://cnes.datasus.gov.br/pages/downloads/arquivosBaseDados.jsp)

## Dados de CEP: 

- Usando a API do [CEP Aberto](https://www.cepaberto.com/)
- Criei o arquivo [CEP_API](CEP_API.ipynb)

## Tipo de estabelecimento

- [Consulta Tipo Estabelecimento](https://cnes2.datasus.gov.br/Mod_Ind_Unidade.asp)

## Fronteiras das Cidades

- Usando a API [Nominatim](https://nominatim.openstreetmap.org)
- Criei o arquivo [Fronteiras](Fronteiras.ipynb)
- Simplifiquei as fronteiras usando o [mapshaper](https://mapshaper.org/)