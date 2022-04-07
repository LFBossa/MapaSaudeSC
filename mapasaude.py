import streamlit as st
import pandas as pd
import numpy as np
import json
import folium
from folium.plugins import FastMarkerCluster
from streamlit_folium import folium_static
import requests

# descomentar para versão online
BASE_URL = "https://raw.githubusercontent.com/LFBossa/MapaSaudeSC/main/"
#BASE_URL = "./"


@st.cache
def get_estabelecimentos():
    ST = pd.read_pickle(BASE_URL + "parsed-data/estabelecimentos.pd.pkl")
    ST.set_index("CNES", inplace=True)
    ST["label"] = ST["NOME FANTASIA"]
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


tipo_unidade = ESTABELECIMENTOS.tipo_unidade.unique()
tipo_unidade_selectbox = st.sidebar.multiselect(
    "Escolha o tipo de unidade", tipo_unidade)

#all_options = st.sidebar.checkbox("Selecionar todas")

# if all_options:
#    tipo_unidade_selectbox = tipo_unidade


def retrieve_data(line):
    return line["lat"], line["lon"], line["label"]


def ping_points():
    callback = """\
    function (row) {
        var marker;
        marker = L.marker(new L.LatLng(row[0], row[1]));
        marker.bindPopup(`<b>${row[2]}</b>`)
        return marker;
    };
    """
    m = folium.Map([-27.048549, -50.4133549], zoom_start=7.4,tiles="Stamen Toner")
    for x in tipo_unidade_selectbox:
        subconjunto = ESTABELECIMENTOS.query(f"tipo_unidade == '{x}'")
        dados = subconjunto.apply(retrieve_data, axis=1)
        FastMarkerCluster(dados, callback=callback,
                          name=x).add_to(m)
    return m


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
    name="Random",
    data=filtrados_doenca,
    columns=["IBGE", "incidência"],
    key_on="feature.properties.id",
    fill_color="PRGn",
    fill_opacity=0.5,
    line_opacity=0.1,
    highlight=True,
    legend_name=f"{doenca_selecionada} (casos/mil hab.)"
)



mapinha.add_to(m)

folium.GeoJson(GEOJSON,
    control=False,
    style_function=lambda x: {'fillOpacity': 0.0, 'stroke': False},
    popup=folium.GeoJsonPopup(fields=["name","incidência"])
).add_to(m)

folium.LayerControl().add_to(m)

folium_static(m,  width=800, height=500)
