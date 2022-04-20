from requests import options
import streamlit as st
import pandas as pd
import numpy as np
from matplotlib import legend, pyplot as plt
from datetime import datetime as dt
import matplotlib.dates as mdates
from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource, HoverTool

# descomentar para versão online
#BASE_URL = "https://raw.githubusercontent.com/LFBossa/MapaSaudeSC/main/"
BASE_URL = "./"

st.set_page_config(  # layout="wide",
    page_title="Mapa da Saúde SC",
    page_icon="🧊")


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
        elif year == 2013:
            year += 1
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
       legend_label="SC", alpha=0.5, line_dash="dashed")
p.add_tools(TOOLTIPS)
p.legend.location = 'top_left'
st.bokeh_chart(p, use_container_width=True)
#fig, ax = plt.subplots(figsize=(10,5))
# dadddos.plot(ax=ax)
#ax.set_title(f"Índice de {dd} para cada mil habitantes em {cdd}")
# st.pyplot(fig)
