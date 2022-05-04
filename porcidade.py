import streamlit as st
import pandas as pd
import numpy as np
import json
import folium
from folium.plugins import FastMarkerCluster, MarkerCluster
from streamlit_folium import folium_static
import requests

# descomentar para versão online
BASE_URL = "https://raw.githubusercontent.com/LFBossa/MapaSaudeSC/main/"
#BASE_URL = "./"

st.set_page_config(#layout="wide",
    page_title="Mapa da Saúde SC",
    page_icon="🧊")


@st.cache
def get_estabelecimentos():
    ST = pd.read_pickle(BASE_URL + "parsed-data/estabelecimentos.pd.pkl")
    ST.set_index("CNES", inplace=True)
    ST["label"] = ST["NOME FANTASIA"]
    geocodes = pd.read_pickle(BASE_URL + "parsed-data/geocodes.pd.pkl")
    ST.update(geocodes)
    ST["endereco"] = ST.apply(lambda x: f"{x.LOGRADOURO} {x.NUMERO}, {x.BAIRRO}", axis=1)
    return ST


@st.cache(allow_output_mutation=True)
def get_geojson():
    PATH = BASE_URL + "data/geoloc/boundaries-simplified.json"
    try:
        with open(PATH) as fp:
            geojson = json.load(fp)
    except:
        contents = requests.get(PATH).text
        geojson = json.loads(contents)
    return geojson


@st.cache
def get_doencas():
    doencas = pd.read_csv(BASE_URL + "parsed-data/doencas.csv")
    return doencas
@st.cache
def get_populacao():
    populi = pd.read_csv(BASE_URL + "parsed-data/populacao.csv")
    populi.set_index("COD_IBGE",inplace=True)
    return populi
 
@st.cache
def get_incidencia(doenca, ano):
    populacao = get_populacao()
    doencas = get_doencas()
    serie =  doencas.query(f"ano == {ano}").set_index("Ibge")[doenca]
    a = serie.div(populacao[f"{ano}"])*1000
    df =  pd.DataFrame({"IBGE": a.index.values, "incidência": a.values})

    return df

DOENCAS = get_doencas()
POPULACAO = get_populacao()
ESTABELECIMENTOS = get_estabelecimentos()

st.sidebar.write("""# Filtros
## Estabelecimentos de saúde
""")

municipios_list = ESTABELECIMENTOS.MUNICIPIO.unique()
municipios_list.sort()
municipio_selecionado = st.sidebar.selectbox(
    "Escolha a cidade", municipios_list)
 


def retrieve_data(line):
    return line["lat"], line["lon"], line["label"], line["tipo_unidade"], line["endereco"]


def ping_points():
    callback = """\
    function (row) {
        var marker;
        marker = L.marker(new L.LatLng(row[0], row[1]));
        marker.bindPopup(`<p><b>${row[2]}</b><br><i>${row[3]}</i></p><p>${row[4]}</p>`)
        return marker;
    };
    """
    m = folium.Map([-27.2958165,-50.5933218], zoom_start=7.4,tiles="OpenStreetMap") 
    subconjunto = ESTABELECIMENTOS.query(f"MUNICIPIO == '{municipio_selecionado}'")
    dados = subconjunto.apply(retrieve_data, axis=1)
    FastMarkerCluster(dados, callback=callback,
                    name=municipio_selecionado).add_to(m)
    #MarkerCluster(subconjunto[["lat","lon"]].values).add_to(m)
    return m


st.sidebar.write("""## Doença/ano
""")
doenca_selecionada = st.sidebar.selectbox(
    "Selecione a doença", ["Hipertensão", "Diabetes", "Obesidade", "Tabagismo"])
ano_selecionado = st.sidebar.slider(
    "Selecione o ano de interesse", min_value=2014, max_value=2021)

m = ping_points()

filtrados_doenca = get_incidencia(doenca_selecionada, ano_selecionado)


GEOJSON = get_geojson()

for i, x in enumerate(GEOJSON["features"]):
    try: 
        objeto = x["properties"] 
        idx = objeto["id"]
        indice = filtrados_doenca.query(f"IBGE == {idx}")["incidência"].values[0]
        objeto.update({"incidência": "{:0.3f}".format(indice).replace(".",",")})
        #objeto = GEOJSON["features"][i]["properties"]
        #objeto["incidência"] =  indice
    except KeyError:
        pass
        #print(idx)


mapinha = folium.Choropleth(
    geo_data=GEOJSON,
    name=doenca_selecionada,
    data=filtrados_doenca,
    columns=["IBGE", "incidência"],
    key_on="feature.properties.id",
    bins=7,
    fill_color="OrRd",
    fill_opacity=0.5,
    line_opacity=0.1,
    highlight=True,
    legend_name=f"{doenca_selecionada} (casos/mil hab.)"
)


"""# Mapa da Saúde SC


"""
mapinha.add_to(m)

folium.GeoJson(GEOJSON,
    control=False,
    style_function=lambda x: {'fillOpacity': 0.0, 'stroke': False},
    popup=folium.GeoJsonPopup(fields=["name","incidência"])
).add_to(m)

folium.LayerControl().add_to(m)

folium_static(m,  width=800, height=500)


subconjunto = ESTABELECIMENTOS.query(f"MUNICIPIO == '{municipio_selecionado}'").copy()
subconjunto.rename({'MUNICIPIO': municipio_selecionado}, axis=1, inplace=True)

st.write(subconjunto.groupby("tipo_unidade").count()[municipio_selecionado])
"""
O mapa acima contém dados obtivos pelo Sistema de informação em Saúde para a Atenção Básica 
[SISAB](https://sisab.saude.gov.br/paginas/acessoRestrito/relatorio/federal/saude/RelSauProducao.xhtml), sobre atendimentos individuais para 
hipertensão arterial, hiabetes, obesidade e tabagismo. 

Dados de população obtidos do sistema [SIDRA](https://sidra.ibge.gov.br/tabela/6579) do IBGE.

Geocodificação de endereços e fronteiras de cidades foi feita usando a API [CEP aberto](https://www.cepaberto.com/) e [Nominatim](https://nominatim.org/).
"""

"""> Criado por  [Bossa](https://github.com/LFBossa) do [LABMAC](http://labmac.mat.blumenau.ufsc.br/)
> para o *Projeto Qualificação Profissional e de Gestores de Santa Catarina em [DCNT](https://dcnt.paginas.ufsc.br/)* """