from requests import options
import streamlit as st
import pandas as pd
import numpy as np
from matplotlib import legend, pyplot as plt
from datetime import datetime as dt
import matplotlib.dates as mdates
from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource, HoverTool
import json
import folium
from folium.plugins import FastMarkerCluster
from streamlit_folium import folium_static

# descomentar para versão online
#BASE_URL = "https://raw.githubusercontent.com/LFBossa/MapaSaudeSC/main/"
BASE_URL = "./"

st.set_page_config(  # layout="wide",
    page_title="Mapa da Saúde SC",
    page_icon="🧊")

# Incidências

@st.cache
def get_dados():
    doenças = pd.read_csv(BASE_URL + "parsed-data/saude-series.csv")
    população = pd.read_csv(BASE_URL + "parsed-data/populacao.csv")
    regioes = pd.read_csv(BASE_URL + "data/geoloc/regioes-saude.csv",
                          dtype={"REGIAO": "category", "municipio": "str"})
    regioes.set_index("CODIBGE", inplace=True)
    população["região"] = população.COD_IBGE.apply(
        lambda x: regioes.loc[x, "REGIAO"])
    população.set_index("COD_IBGE", inplace=True)

    def get_pop(ibge, year):
        if year == 2022:
            year -= 1
        return população.loc[ibge, str(year)]

    def get_pop_df(row):
        return get_pop(row["Ibge"], row["ano"])

    doenças["população"] = doenças.apply(get_pop_df, axis=1)
    doenças["região"] = doenças.Ibge.apply(lambda x: regioes.loc[x, "REGIAO"])

    return doenças, população, regioes


def pop_regiao(regiao, year):
    if year == 2022:
        year -= 1
    elif year == 2013:
        year += 1
    return população_das_regiões.loc[regiao, str(year)]


def pop_estado(ano):
    if ano == 2022:
        ano -= 1
    elif ano == 2013:
        ano += 1
    return população[str(ano)].sum()

# MAPA
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
    doencas = pd.read_csv(BASE_URL + "parsed-data/doencas2.csv")
    return doencas


@st.cache
def get_populacao():
    populi = pd.read_csv(BASE_URL + "parsed-data/populacao.csv")
    populi.set_index("COD_IBGE", inplace=True)
    return populi


@st.cache
def get_incidencia(doenca, ano):
    populacao = get_populacao()
    doencas = get_doencas()
    serie = doencas.query(f"ano == {ano}").set_index("Ibge")[doenca]
    a = serie.div(populacao[f"{ano}"])*1000
    df = pd.DataFrame({"IBGE": a.index.values, "incidência": a.values})
    return df


st.sidebar.write("# Abas")
MAIN_SWITCH = st.sidebar.radio("Escolha o tipo de visualização", ["Mapa", "Série"])
st.sidebar.write("## Filtros")



if MAIN_SWITCH == "Série":
    
    doenças, população, regioes = get_dados()

    população_das_regiões = população.groupby("região").sum()


    doenca_select = st.sidebar.selectbox(
        label="Selecione a doença", options=doenças.columns[1:13])

    municipio_select = st.sidebar.selectbox(label="Selecione o município",
                                            options=regioes.index, format_func=lambda x: regioes.loc[x, "municipio"].title())

    cidade_label = regioes.loc[municipio_select, "municipio"].title()
    codibge = municipio_select
    regiao = regioes.loc[int(codibge), "REGIAO"]
    doença = doenca_select
    pvt_doença_região = pd.pivot_table(
        doenças[["referencia", "região", doença]], index="referencia", columns="região", aggfunc=sum)[(doença, regiao)]
    população_região = [pop_regiao(regiao, ano)
                        for ano in (pvt_doença_região.index.values // 100)]
    pvt_doença_estado = pd.pivot_table(
        doenças[["referencia", doença]], index="referencia",  aggfunc=sum)[doença]
    população_estado = [pop_estado(ano) for ano in (
        pvt_doença_estado.index.values // 100)]


    sr_doença_cidade = doenças.query(
        f"Ibge == {codibge}").set_index("referencia")[doença]
    sr_população_cidade = doenças.query(
        f"Ibge == {codibge}").set_index("referencia")["população"]

    dadddos = pd.concat([sr_doença_cidade/sr_população_cidade*1000,
                        pvt_doença_região/população_região*1000,
                        pvt_doença_estado/população_estado*1000], axis=1).sort_index().reset_index()
    datas = [dt.strptime(str(x), "%Y%m") for x in dadddos["referencia"].values]
    dadddos["referencia"] = datas
    dadddos.set_index("referencia", inplace=True)
    dadddos.columns = [cidade_label, regiao, "SC"]

    source = ColumnDataSource(dadddos)
    TOOLTIPS = HoverTool(
        tooltips=[
            ("data", "@referencia{%F}"),
            ("cidade", f"@{{{cidade_label}}}"),
            ("região", f"@{{{regiao}}}"),
            ("estado", f"@{{SC}}"),
        ],
        formatters={
            '@referencia': 'datetime',  # use 'datetime' formatter for '@date' field
        },)

    p = figure(title=f"Índice de {doença} para cada mil habitantes em {cidade_label}",
            x_axis_type='datetime')
    p.line(x="referencia", y=cidade_label, source=source,
        line_color="red", legend_label=cidade_label, line_width=2)
    p.line(x="referencia", y=regiao, source=source,
        legend_label=regiao, alpha=0.7)
    p.line(x="referencia", y="SC", source=source,
        legend_label="SC", alpha=0.6, line_dash="dashed",line_color="black")
    p.add_tools(TOOLTIPS)
    p.legend.location = 'top_left'

    f"""# Incidência de casos
Comparando o número de atendimento de casos de {doença} em {cidade_label} com dados regionais e estaduais.
    """
    st.bokeh_chart(p, use_container_width=True)
else:
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
        m = folium.Map([-27.2958165,-50.5933218], zoom_start=7.4,tiles="Stamen Toner")
        for x in tipo_unidade_selectbox:
            subconjunto = ESTABELECIMENTOS.query(f"tipo_unidade == '{x}'")
            dados = subconjunto.apply(retrieve_data, axis=1)
            FastMarkerCluster(dados, callback=callback,
                            name=x).add_to(m)
        return m

    doenca_selecionada = st.sidebar.selectbox(
        "Selecione a doença", DOENCAS.columns[2:])
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


    f"""# Mapa da Saúde SC

Mapa comparativo do total de casos de  {doenca_selecionada} no ano de {ano_selecionado}.
    """
    mapinha.add_to(m)

    folium.GeoJson(GEOJSON,
        control=False,
        style_function=lambda x: {'fillOpacity': 0.0, 'stroke': False},
        popup=folium.GeoJsonPopup(fields=["name","incidência"])
    ).add_to(m)

    folium.LayerControl().add_to(m)

    folium_static(m,  width=800, height=500)

"""
Esse applicativo contém dados obtivos pelo Sistema de informação em Saúde para a Atenção Básica 
[SISAB](https://sisab.saude.gov.br/paginas/acessoRestrito/relatorio/federal/saude/RelSauProducao.xhtml), sobre atendimentos individuais para 
as doenças listadas. 

Dados de população obtidos do sistema [SIDRA](https://sidra.ibge.gov.br/tabela/6579) do IBGE.

Geocodificação de endereços e fronteiras de cidades foi feita usando a API [CEP aberto](https://www.cepaberto.com/) e [Nominatim](https://nominatim.org/).
"""

"""> Criado por  [Bossa](https://github.com/LFBossa) do [LABMAC](http://labmac.mat.blumenau.ufsc.br/)
> para o *Projeto Qualificação Profissional e de Gestores de Santa Catarina em [DCNT](https://dcnt.paginas.ufsc.br/)* """