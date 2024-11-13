import requests
import pandas as pd
import yfinance as yf
import numpy as np
import plotly.express as px
import json
import math
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from datetime import date

#LIBRERIAS

#################################################################################################################################################################################################################################################################################################################################################################################################################################

dia_final = date.today().strftime('%Y-%m-%d')

# SP 100 OEF
def realizar_calculos():
 
    json_url = 'https://www.blackrock.com/mx/intermediarios/productos/239723/ishares-sp-100-etf/1501904811835.ajax?tab=all&fileType=json'

    response = requests.get(json_url)

    
    if response.status_code == 200:
        data = response.content.decode('utf-8-sig')
        json_data = json.loads(data)

        holdings_data = json_data.get('aaData', [])
        df = pd.DataFrame(holdings_data)

       
        first_column = df.iloc[:, 0].tolist()

        
        tickers_df = pd.DataFrame(first_column, columns=['Ticker'])
        tickers_df.to_csv('tickers.csv', index=False)

        st.write("Tickers extraídos y guardados en tickers.csv")
    else:
        st.write("No se pudo descargar los datos JSON.")
        return None, None, None, None, None

    
    tickers_to_exclude = ['USD', 'ESM4', 'BRKB', 'MSFUT', 'XTSLA', 'ESU4', 'MARGIN_USD']

    
    tickers = [ticker for ticker in first_column if ticker not in tickers_to_exclude]
    etf_ticker = 'OEF'
    tickers.append(etf_ticker)

    inicio = '2024-01-01'
    final = dia_final
    etf = 'OEF'

    # Descargar datos de precios ajustados
    def descargar_datos(tickers, inicio, final):
        datos = yf.download(tickers, inicio, final)['Adj Close']
        return datos

    precios = descargar_datos(tickers, inicio, final)
    precios_etf = descargar_datos([etf], inicio, final)

    # Calcular retornos diarios
    retorno_diarios = precios.pct_change(1)
    retorno_diarios_etf = precios_etf.pct_change(1)

    # Calcular retornos anuales
    retornos_anuales = retorno_diarios.mean() * 252
    retorno_anual_etf = retorno_diarios_etf.mean() * 252

    # Ajustar retornos anuales en relación con el retorno del ETF
    retorno_anual_etf_valor = retorno_anual_etf.item()
    retornos_anuales_ajustados = retornos_anuales - retorno_anual_etf_valor

    # Calcular riesgo anual
    riesgo_anual = retorno_diarios.std() * math.sqrt(252)

    # Ordenar los retornos anuales ajustados
    retorno_anual_ordenado = retornos_anuales_ajustados.sort_values(ascending=False)

    # Crear un DataFrame con los datos ajustados
    datos2 = pd.DataFrame()
    datos2['Retorno Anual Ajustado'] = retornos_anuales_ajustados
    datos2['Riesgo Anual Esperado'] = riesgo_anual
    datos2['Tickers'] = datos2.index
    datos2['Ratio'] = datos2['Retorno Anual Ajustado'] / datos2['Riesgo Anual Esperado']

    # Ordenar por el ratio
    datos2.sort_values(by='Ratio', axis=0, ascending=False, inplace=False)

    # Calcular Beta
    datos = pd.DataFrame(precios)
    retornos_diarios = datos.pct_change()
    covarianza = retornos_diarios.cov()
    varianza = np.var(retornos_diarios[etf])
    betas = []
    for t in tickers:
        beta_accion = covarianza.loc[t, etf] / varianza
        betas.append(beta_accion)

    tabla = pd.DataFrame({'Ticker': tickers, 'Beta': betas})
    tabla = tabla.round(2)

    # Graficar Retorno Ajustado vs Riesgo
    fig1 = px.scatter(
        datos2,
        x='Riesgo Anual Esperado',
        y='Retorno Anual Ajustado',
        text='Tickers',
        title='Retorno Anual Ajustado vs Riesgo Anual Esperado vs ETF'
    )

    # Añadir una línea horizontal punteada en el punto (0,0)
    fig1.add_shape(
        type="line",
        x0=0, y0=0, x1=0.6, y1=0,
        line=dict(color="Crimson", width=2, dash="dot")
    )

    # Actualizar etiquetas y estilo
    fig1.update_traces(marker=dict(color='DarkBlue', size=10), textposition='bottom center')
    fig1.update_layout(
        xaxis_title='Riesgo Anual Esperado',
        yaxis_title='Retorno Anual Ajustado',
        height=600,
        width=900
    )

    # Graficar los retornos anuales ajustados
    fig2 = go.Figure(data=[
        go.Bar(x=retorno_anual_ordenado.index, y=retorno_anual_ordenado)
    ])

    # Añadir etiquetas y título
    fig2.update_layout(
        title='Retornos Anualizados Ajustados del Portafolio vs ETF',
        xaxis_title='Ticker',
        yaxis_title='Retornos Anualizados Ajustados',
        xaxis_tickangle=-90,
         height=600,
        width=900
    )

   
    data = pd.DataFrame({'Ticker': tickers, 'Beta': betas, 'Retorno Anual': retorno_anual_ordenado})
    data = data.dropna().round({'Beta': 2, 'Retorno Anual': 2})

    # Crear la gráfica entre Retornos Anuales Ajustados vs Beta con nombres de los tickers y puntos más grandes
    fig3 = px.scatter(data, x='Beta', y='Retorno Anual', text='Ticker',
                      labels={'x': 'Beta', 'y': 'Retorno Anual'},
                      title='Relación entre Retornos Anuales Ajustados y Beta',width=900, height=600)

    fig3.update_traces(marker=dict(size=10), textposition='top center')

    # Añadir una línea punteada vertical en Beta 1
    fig3.add_trace(go.Scatter(x=[1, 1], y=[data['Retorno Anual'].min(), data['Retorno Anual'].max()],
                              mode='lines',
                              line=dict(dash='dash', color='red'),
                              showlegend=False))
    
    precios_acumulados = (1 + retorno_diarios).cumprod() - 1

    # Graficar los retornos acumulados
    fig4 = px.line(precios_acumulados, title='Retornos Acumulados')
    fig4.update_layout(
        xaxis_title='Fecha',
        yaxis_title='Retornos Acumulados',
        height=600,
        width=900
    )

    return fig1, fig2, fig3, fig4

#################################################################################################################################################################################################################################################################################################################################################################################################################################

# TECNOLOGIA - IYW
def realizar_calculos1():
    # Paso 1: Scrape los tickers de la página de BlackRock
    json_url_tech = 'https://www.blackrock.com/mx/intermediarios/productos/239522/ishares-us-technology-etf/1501904811835.ajax?tab=all&fileType=json'

    response_tech = requests.get(json_url_tech)

    # Verificar si la solicitud fue exitosa
    if response_tech.status_code == 200:
        data_tech = response_tech.content.decode('utf-8-sig')
        json_data_tech = json.loads(data_tech)

        holdings_data_tech = json_data_tech.get('aaData', [])
        df_tech = pd.DataFrame(holdings_data_tech)

        # Extraer la primera columna (asumiendo que contiene los tickers)
        first_column_tech = df_tech.iloc[:, 0].tolist()

        # Guardar los tickers en un archivo CSV
        tickers_df_tech = pd.DataFrame(first_column_tech, columns=['Ticker'])
        tickers_df_tech.to_csv('tickers_tech.csv', index=False)

        st.write("Tickers extraídos y guardados en tickers_tech.csv")
    else:
        st.write("No se pudo descargar los datos JSON.")
        return None, None, None, None, None

    # Lista de tickers a excluir
    tickers_to_exclude_tech = ['USD', 'ESM4', 'BRKB', 'MSFUT', 'XTSLA', 'ESU4', 'MARGIN_USD', 'IXTU4','WFFUT', 'XASU4']

    # Filtrar los tickers excluyendo los no válidos
    tickers_tech = [ticker for ticker in first_column_tech if ticker not in tickers_to_exclude_tech]
    etf_ticker_tech = 'IYW'
    tickers_tech.append(etf_ticker_tech)

    inicio_tech = '2024-01-01'
    final_tech = dia_final
    etf_tech = 'IYW'

    # Descargar datos de precios ajustados
    def descargar_datos_tech(tickers_tech, inicio_tech, final_tech):
        datos_tech = yf.download(tickers_tech, inicio_tech, final_tech)['Adj Close']
        return datos_tech

    precios_tech = descargar_datos_tech(tickers_tech, inicio_tech, final_tech)
    precios_etf_tech = descargar_datos_tech([etf_tech], inicio_tech, final_tech)

    # Calcular retornos diarios
    retorno_diarios_tech = precios_tech.pct_change(1)
    retorno_diarios_etf_tech = precios_etf_tech.pct_change(1)

    # Calcular retornos anuales
    retornos_anuales_tech = retorno_diarios_tech.mean() * 252
    retorno_anual_etf_tech = retorno_diarios_etf_tech.mean() * 252

    # Ajustar retornos anuales en relación con el retorno del ETF
    retorno_anual_etf_valor_tech = retorno_anual_etf_tech.item()
    retornos_anuales_ajustados_tech = retornos_anuales_tech - retorno_anual_etf_valor_tech

    # Calcular riesgo anual
    riesgo_anual_tech = retorno_diarios_tech.std() * math.sqrt(252)

    # Ordenar los retornos anuales ajustados
    retorno_anual_ordenado_tech = retornos_anuales_ajustados_tech.sort_values(ascending=False)

    # Crear un DataFrame con los datos ajustados
    datos2_tech = pd.DataFrame()
    datos2_tech['Retorno Anual Ajustado'] = retornos_anuales_ajustados_tech
    datos2_tech['Riesgo Anual Esperado'] = riesgo_anual_tech
    datos2_tech['Tickers'] = datos2_tech.index
    datos2_tech['Ratio'] = datos2_tech['Retorno Anual Ajustado'] / datos2_tech['Riesgo Anual Esperado']

    # Ordenar por el ratio
    datos2_tech.sort_values(by='Ratio', axis=0, ascending=False, inplace=False)

    # Calcular Beta
    datos_tech = pd.DataFrame(precios_tech)
    retornos_diarios_tech = datos_tech.pct_change()
    covarianza_tech = retornos_diarios_tech.cov()
    varianza_tech = np.var(retornos_diarios_tech[etf_tech])
    betas_tech = []
    for t in tickers_tech:
        beta_accion_tech = covarianza_tech.loc[t, etf_tech] / varianza_tech
        betas_tech.append(beta_accion_tech)

    tabla_tech = pd.DataFrame({'Ticker': tickers_tech, 'Beta': betas_tech})
    tabla_tech = tabla_tech.round(2)
   
    # Graficar Retorno Ajustado vs Riesgo
    fig5 = px.scatter(
        datos2_tech,
        x='Riesgo Anual Esperado',
        y='Retorno Anual Ajustado',
        text='Tickers',
        title='Retorno Anual Ajustado vs Riesgo Anual Esperado vs ETF'
    )

    # Añadir una línea horizontal punteada en el punto (0,0)
    fig5.add_shape(
        type="line",
        x0=0, y0=0, x1=0.6, y1=0,
        line=dict(color="Crimson", width=2, dash="dot")
    )

    # Actualizar etiquetas y estilo
    fig5.update_traces(marker=dict(color='DarkBlue', size=10), textposition='bottom center')
    fig5.update_layout(
        xaxis_title='Riesgo Anual Esperado',
        yaxis_title='Retorno Anual Ajustado',
        height=600,
        width=900
    )

    # Graficar los retornos anuales ajustados
    fig6 = go.Figure(data=[
        go.Bar(x=retorno_anual_ordenado_tech.index, y=retorno_anual_ordenado_tech)
    ])

    # Añadir etiquetas y título
    fig6.update_layout(
        title='Retornos Anualizados Ajustados del Portafolio vs ETF',
        xaxis_title='Ticker',
        yaxis_title='Retornos Anualizados Ajustados',
        xaxis_tickangle=-90,
         height=600,
        width=900
    )

   
    data_tech = pd.DataFrame({'Ticker': tickers_tech, 'Beta': betas_tech, 'Retorno Anual': retorno_anual_ordenado_tech})
    data_tech = data_tech.dropna().round({'Beta': 2, 'Retorno Anual': 2})

    # Crear la gráfica entre Retornos Anuales Ajustados vs Beta con nombres de los tickers y puntos más grandes
    fig7 = px.scatter(data_tech, x='Beta', y='Retorno Anual', text='Ticker',
                      labels={'x': 'Beta', 'y': 'Retorno Anual'},
                      title='Relación entre Retornos Anuales Ajustados y Beta',width=900, height=600)

    fig7.update_traces(marker=dict(size=10), textposition='top center')

    # Añadir una línea punteada vertical en Beta 1
    fig7.add_trace(go.Scatter(x=[1, 1], y=[data_tech['Retorno Anual'].min(), data_tech['Retorno Anual'].max()],
                              mode='lines',
                              line=dict(dash='dash', color='red'),
                              showlegend=False))
    
    precios_acumulados_tech = (1 + retorno_diarios_tech).cumprod() - 1

    # Graficar los retornos acumulados
    fig8 = px.line(precios_acumulados_tech, title='Retornos Acumulados')
    fig8.update_layout(
        xaxis_title='Fecha',
        yaxis_title='Retornos Acumulados',
        height=600,
        width=900
    )

    return fig5, fig6, fig7, fig8

#################################################################################################################################################################################################################################################################################################################################################################################################################################

# SEMICONDUCTORES - SOXX
def realizar_calculos2():
    # Paso 1: Scrape los tickers de la página de BlackRock
    json_url_semiconductores = 'https://www.blackrock.com/mx/intermediarios/productos/239705/ishares-phlx-semiconductor-etf/1501904811835.ajax?tab=all&fileType=json'

    response_semiconductores = requests.get(json_url_semiconductores)

    # Verificar si la solicitud fue exitosa
    if response_semiconductores.status_code == 200:
        data_semiconductores = response_semiconductores.content.decode('utf-8-sig')
        json_data_semiconductores = json.loads(data_semiconductores)

        holdings_data_semiconductores = json_data_semiconductores.get('aaData', [])
        df_semiconductores = pd.DataFrame(holdings_data_semiconductores)

        # Extraer la primera columna (asumiendo que contiene los tickers)
        first_column_semiconductores = df_semiconductores.iloc[:, 0].tolist()

        # Guardar los tickers en un archivo CSV
        tickers_df_semiconductores = pd.DataFrame(first_column_semiconductores, columns=['Ticker'])
        tickers_df_semiconductores.to_csv('tickers_semiconductores.csv', index=False)

        st.write("Tickers extraídos y guardados en tickers_semiconductores.csv")
    else:
        st.write("No se pudo descargar los datos JSON.")
        return None, None, None, None, None

    # Lista de tickers a excluir
    tickers_to_exclude_semiconductores = ['USD', 'ESM4', 'BRKB', 'MSFUT', 'XTSLA', 'ESU4', 'MARGIN_USD', 'IXTU4','WFFUT', 'XASU4', 'RTYU4']

    # Filtrar los tickers excluyendo los no válidos
    tickers_semiconductores = [ticker for ticker in first_column_semiconductores if ticker not in tickers_to_exclude_semiconductores]
    etf_ticker_semiconductores = 'SOXX'
    tickers_semiconductores.append(etf_ticker_semiconductores)

    inicio_semiconductores = '2024-01-01'
    final_semiconductores = dia_final
    etf_semiconductores = 'SOXX'

    # Descargar datos de precios ajustados
    def descargar_datos_semiconductores(tickers_semiconductores, inicio_semiconductores, final_semiconductores):
        datos_semiconductores = yf.download(tickers_semiconductores, inicio_semiconductores, final_semiconductores)['Adj Close']
        return datos_semiconductores

    precios_semiconductores = descargar_datos_semiconductores(tickers_semiconductores, inicio_semiconductores, final_semiconductores)
    precios_etf_semiconductores = descargar_datos_semiconductores([etf_semiconductores], inicio_semiconductores, final_semiconductores)

    # Calcular retornos diarios
    retorno_diarios_semiconductores = precios_semiconductores.pct_change(1)
    retorno_diarios_etf_semiconductores = precios_etf_semiconductores.pct_change(1)

    # Calcular retornos anuales
    retornos_anuales_semiconductores = retorno_diarios_semiconductores.mean() * 252
    retorno_anual_etf_semiconductores = retorno_diarios_etf_semiconductores.mean() * 252

    # Ajustar retornos anuales en relación con el retorno del ETF
    retorno_anual_etf_valor_semiconductores = retorno_anual_etf_semiconductores.item()
    retornos_anuales_ajustados_semiconductores = retornos_anuales_semiconductores - retorno_anual_etf_valor_semiconductores

    # Calcular riesgo anual
    riesgo_anual_semiconductores = retorno_diarios_semiconductores.std() * math.sqrt(252)

    # Ordenar los retornos anuales ajustados
    retorno_anual_ordenado_semiconductores = retornos_anuales_ajustados_semiconductores.sort_values(ascending=False)

    # Crear un DataFrame con los datos ajustados
    datos2_semiconductores = pd.DataFrame()
    datos2_semiconductores['Retorno Anual Ajustado'] = retornos_anuales_ajustados_semiconductores
    datos2_semiconductores['Riesgo Anual Esperado'] = riesgo_anual_semiconductores
    datos2_semiconductores['Tickers'] = datos2_semiconductores.index
    datos2_semiconductores['Ratio'] = datos2_semiconductores['Retorno Anual Ajustado'] / datos2_semiconductores['Riesgo Anual Esperado']

    # Ordenar por el ratio
    datos2_semiconductores.sort_values(by='Ratio', axis=0, ascending=False, inplace=False)

    # Calcular Beta
    datos_semiconductores = pd.DataFrame(precios_semiconductores)
    retornos_diarios_semiconductores = datos_semiconductores.pct_change()
    covarianza_semiconductores = retornos_diarios_semiconductores.cov()
    varianza_semiconductores = np.var(retornos_diarios_semiconductores[etf_semiconductores])
    betas_semiconductores = []
    for t in tickers_semiconductores:
        beta_accion_semiconductores = covarianza_semiconductores.loc[t, etf_semiconductores] / varianza_semiconductores
        betas_semiconductores.append(beta_accion_semiconductores)

    tabla_semiconductores = pd.DataFrame({'Ticker': tickers_semiconductores, 'Beta': betas_semiconductores})
    tabla_semiconductores = tabla_semiconductores.round(2)
   
    # Graficar Retorno Ajustado vs Riesgo
    fig9 = px.scatter(
        datos2_semiconductores,
        x='Riesgo Anual Esperado',
        y='Retorno Anual Ajustado',
        text='Tickers',
        title='Retorno Anual Ajustado vs Riesgo Anual Esperado vs ETF'
    )

    # Añadir una línea horizontal punteada en el punto (0,0)
    fig9.add_shape(
        type="line",
        x0=0, y0=0, x1=0.6, y1=0,
        line=dict(color="Crimson", width=2, dash="dot")
    )

    # Actualizar etiquetas y estilo
    fig9.update_traces(marker=dict(color='DarkBlue', size=10), textposition='bottom center')
    fig9.update_layout(
        xaxis_title='Riesgo Anual Esperado',
        yaxis_title='Retorno Anual Ajustado',
        height=600,
        width=900
    )

    # Graficar los retornos anuales ajustados
    fig10 = go.Figure(data=[
        go.Bar(x=retorno_anual_ordenado_semiconductores.index, y=retorno_anual_ordenado_semiconductores)
    ])

    # Añadir etiquetas y título
    fig10.update_layout(
        title='Retornos Anualizados Ajustados del Portafolio vs ETF',
        xaxis_title='Ticker',
        yaxis_title='Retornos Anualizados Ajustados',
        xaxis_tickangle=-90,
         height=600,
        width=900
    )

   
    data_semiconductores = pd.DataFrame({'Ticker': tickers_semiconductores, 'Beta': betas_semiconductores, 'Retorno Anual': retorno_anual_ordenado_semiconductores})
    data_semiconductores = data_semiconductores.dropna().round({'Beta': 2, 'Retorno Anual': 2})

    # Crear la gráfica entre Retornos Anuales Ajustados vs Beta con nombres de los tickers y puntos más grandes
    fig11 = px.scatter(data_semiconductores, x='Beta', y='Retorno Anual', text='Ticker',
                      labels={'x': 'Beta', 'y': 'Retorno Anual'},
                      title='Relación entre Retornos Anuales Ajustados y Beta',width=900, height=600)

    fig11.update_traces(marker=dict(size=10), textposition='top center')

    # Añadir una línea punteada vertical en Beta 1
    fig11.add_trace(go.Scatter(x=[1, 1], y=[data_semiconductores['Retorno Anual'].min(), data_semiconductores['Retorno Anual'].max()],
                              mode='lines',
                              line=dict(dash='dash', color='red'),
                              showlegend=False))
    
    precios_acumulados_semiconductores = (1 + retorno_diarios_semiconductores).cumprod() - 1

    # Graficar los retornos acumulados
    fig12 = px.line(precios_acumulados_semiconductores, title='Retornos Acumulados')
    fig12.update_layout(
        xaxis_title='Fecha',
        yaxis_title='Retornos Acumulados',
        height=600,
        width=900
    )
    
    return fig9, fig10, fig11, fig12

#################################################################################################################################################################################################################################################################################################################################################################################################################################

# RUSSELL 1000 - IWF
def realizar_calculos3():
    # Paso 1: Scrape los tickers de la página de BlackRock
    json_url_russell = 'https://www.blackrock.com/mx/intermediarios/productos/239706/ishares-russell-1000-growth-etf/1501904811835.ajax?tab=all&fileType=json'

    response_russell = requests.get(json_url_russell)

    # Verificar si la solicitud fue exitosa
    if response_russell.status_code == 200:
        data_russell = response_russell.content.decode('utf-8-sig')
        json_data_russell = json.loads(data_russell)

        holdings_data_russell = json_data_russell.get('aaData', [])
        df_russell = pd.DataFrame(holdings_data_russell)

        # Extraer la primera columna (asumiendo que contiene los tickers)
        first_column_russell = df_russell.iloc[:, 0].tolist()

        # Guardar los tickers en un archivo CSV
        tickers_df_russell = pd.DataFrame(first_column_russell, columns=['Ticker'])
        tickers_df_russell.to_csv('tickers_russell.csv', index=False)

        st.write("Tickers extraídos y guardados en tickers_russell.csv")
    else:
        st.write("No se pudo descargar los datos JSON.")
        return None, None, None, None, None

    # Lista de tickers a excluir
    tickers_to_exclude_russell = ['USD', 'ESM4', 'BRKB', 'MSFUT', 'XTSLA', 'ESU4', 'MARGIN_USD', 'IXTU4','WFFUT', 'XASU4', 'RTYU4']

    # Filtrar los tickers excluyendo los no válidos
    tickers_russell = [ticker for ticker in first_column_russell if ticker not in tickers_to_exclude_russell]
    etf_ticker_russell = 'IWF'
    tickers_russell.append(etf_ticker_russell)

    inicio_russell = '2024-01-01'
    final_russell = dia_final
    etf_russell = 'IWF'

    # Descargar datos de precios ajustados
    def descargar_datos_russell(tickers_russell, inicio_russell, final_russell):
        datos_russell = yf.download(tickers_russell, inicio_russell, final_russell)['Adj Close']
        return datos_russell

    precios_russell = descargar_datos_russell(tickers_russell, inicio_russell, final_russell)
    precios_etf_russell = descargar_datos_russell([etf_russell], inicio_russell, final_russell)

    # Calcular retornos diarios
    retorno_diarios_russell = precios_russell.pct_change(1)
    retorno_diarios_etf_russell = precios_etf_russell.pct_change(1)

    # Calcular retornos anuales
    retornos_anuales_russell = retorno_diarios_russell.mean() * 252
    retorno_anual_etf_russell = retorno_diarios_etf_russell.mean() * 252

    # Ajustar retornos anuales en relación con el retorno del ETF
    retorno_anual_etf_valor_russell = retorno_anual_etf_russell.item()
    retornos_anuales_ajustados_russell = retornos_anuales_russell - retorno_anual_etf_valor_russell

    # Calcular riesgo anual
    riesgo_anual_russell = retorno_diarios_russell.std() * math.sqrt(252)

    # Ordenar los retornos anuales ajustados
    retorno_anual_ordenado_russell = retornos_anuales_ajustados_russell.sort_values(ascending=False)

    # Crear un DataFrame con los datos ajustados
    datos2_russell = pd.DataFrame()
    datos2_russell['Retorno Anual Ajustado'] = retornos_anuales_ajustados_russell
    datos2_russell['Riesgo Anual Esperado'] = riesgo_anual_russell
    datos2_russell['Tickers'] = datos2_russell.index
    datos2_russell['Ratio'] = datos2_russell['Retorno Anual Ajustado'] / datos2_russell['Riesgo Anual Esperado']

    # Ordenar por el ratio
    datos2_russell.sort_values(by='Ratio', axis=0, ascending=False, inplace=False)

    # Calcular Beta
    datos_russell = pd.DataFrame(precios_russell)
    retornos_diarios_russell = datos_russell.pct_change()
    covarianza_russell = retornos_diarios_russell.cov()
    varianza_russell = np.var(retornos_diarios_russell[etf_russell])
    betas_russell = []
    for t in tickers_russell:
        beta_accion_russell = covarianza_russell.loc[t, etf_russell] / varianza_russell
        betas_russell.append(beta_accion_russell)

    tabla_russell = pd.DataFrame({'Ticker': tickers_russell, 'Beta': betas_russell})
    tabla_russell = tabla_russell.round(2)
   
    # Graficar Retorno Ajustado vs Riesgo
    fig13 = px.scatter(
        datos2_russell,
        x='Riesgo Anual Esperado',
        y='Retorno Anual Ajustado',
        text='Tickers',
        title='Retorno Anual Ajustado vs Riesgo Anual Esperado vs ETF'
    )

    # Añadir una línea horizontal punteada en el punto (0,0)
    fig13.add_shape(
        type="line",
        x0=0, y0=0, x1=0.6, y1=0,
        line=dict(color="Crimson", width=2, dash="dot")
    )

    # Actualizar etiquetas y estilo
    fig13.update_traces(marker=dict(color='DarkBlue', size=10), textposition='bottom center')
    fig13.update_layout(
        xaxis_title='Riesgo Anual Esperado',
        yaxis_title='Retorno Anual Ajustado',
        height=600,
        width=900
    )

    # Graficar los retornos anuales ajustados
    fig14 = go.Figure(data=[
        go.Bar(x=retorno_anual_ordenado_russell.index, y=retorno_anual_ordenado_russell)
    ])

    # Añadir etiquetas y título
    fig14.update_layout(
        title='Retornos Anualizados Ajustados del Portafolio vs ETF',
        xaxis_title='Ticker',
        yaxis_title='Retornos Anualizados Ajustados',
        xaxis_tickangle=-90,
         height=600,
        width=900
    )

   
    data_russell = pd.DataFrame({'Ticker': tickers_russell, 'Beta': betas_russell, 'Retorno Anual': retorno_anual_ordenado_russell})
    data_russell = data_russell.dropna().round({'Beta': 2, 'Retorno Anual': 2})

    # Crear la gráfica entre Retornos Anuales Ajustados vs Beta con nombres de los tickers y puntos más grandes
    fig15 = px.scatter(data_russell, x='Beta', y='Retorno Anual', text='Ticker',
                      labels={'x': 'Beta', 'y': 'Retorno Anual'},
                      title='Relación entre Retornos Anuales Ajustados y Beta',width=900, height=600)

    fig15.update_traces(marker=dict(size=10), textposition='top center')

    # Añadir una línea punteada vertical en Beta 1
    fig15.add_trace(go.Scatter(x=[1, 1], y=[data_russell['Retorno Anual'].min(), data_russell['Retorno Anual'].max()],
                              mode='lines',
                              line=dict(dash='dash', color='red'),
                              showlegend=False))
    
    precios_acumulados_russell = (1 + retorno_diarios_russell).cumprod() - 1

    # Graficar los retornos acumulados
    fig16 = px.line(precios_acumulados_russell, title='Retornos Acumulados')
    fig16.update_layout(
        xaxis_title='Fecha',
        yaxis_title='Retornos Acumulados',
        height=600,
        width=900
    )
    
    return fig13, fig14, fig15, fig16

#################################################################################################################################################################################################################################################################################################################################################################################################################################

# INSURANCE - IAK
def realizar_calculos4():
    # Paso 1: Scrape los tickers de la página de BlackRock
    json_url_insurance = 'https://www.blackrock.com/mx/intermediarios/productos/239515/ishares-us-insurance-etf/1501904811835.ajax?tab=all&fileType=json'

    response_insurance = requests.get(json_url_insurance)

    # Verificar si la solicitud fue exitosa
    if response_insurance.status_code == 200:
        data_insurance = response_insurance.content.decode('utf-8-sig')
        json_data_insurance = json.loads(data_insurance)

        holdings_data_insurance = json_data_insurance.get('aaData', [])
        df_insurance = pd.DataFrame(holdings_data_insurance)

        # Extraer la primera columna (asumiendo que contiene los tickers)
        first_column_insurance = df_insurance.iloc[:, 0].tolist()

        # Guardar los tickers en un archivo CSV
        tickers_df_insurance = pd.DataFrame(first_column_insurance, columns=['Ticker'])
        tickers_df_insurance.to_csv('tickers_insurance.csv', index=False)

        st.write("Tickers extraídos y guardados en tickers_insurance.csv")
    else:
        st.write("No se pudo descargar los datos JSON.")
        return None, None, None, None, None

    # Lista de tickers a excluir
    tickers_to_exclude_insurance = ['USD', 'ESM4', 'BRKB', 'MSFUT', 'XTSLA', 'ESU4', 'MARGIN_USD', 'IXTU4','WFFUT', 'XASU4', 'RTYU4']

    # Filtrar los tickers excluyendo los no válidos
    tickers_insurance = [ticker for ticker in first_column_insurance if ticker not in tickers_to_exclude_insurance]
    etf_ticker_insurance = 'IAK'
    tickers_insurance.append(etf_ticker_insurance)

    inicio_insurance = '2024-01-01'
    final_insurance = dia_final
    etf_insurance = 'IAK'

    # Descargar datos de precios ajustados
    def descargar_datos_insurance(tickers_insurance, inicio_insurance, final_insurance):
        datos_insurance = yf.download(tickers_insurance, inicio_insurance, final_insurance)['Adj Close']
        return datos_insurance

    precios_insurance = descargar_datos_insurance(tickers_insurance, inicio_insurance, final_insurance)
    precios_etf_insurance = descargar_datos_insurance([etf_insurance], inicio_insurance, final_insurance)

    # Calcular retornos diarios
    retorno_diarios_insurance = precios_insurance.pct_change(1)
    retorno_diarios_etf_insurance = precios_etf_insurance.pct_change(1)

    # Calcular retornos anuales
    retornos_anuales_insurance = retorno_diarios_insurance.mean() * 252
    retorno_anual_etf_insurance = retorno_diarios_etf_insurance.mean() * 252

    # Ajustar retornos anuales en relación con el retorno del ETF
    retorno_anual_etf_valor_insurance = retorno_anual_etf_insurance.item()
    retornos_anuales_ajustados_insurance = retornos_anuales_insurance - retorno_anual_etf_valor_insurance

    # Calcular riesgo anual
    riesgo_anual_insurance = retorno_diarios_insurance.std() * math.sqrt(252)

    # Ordenar los retornos anuales ajustados
    retorno_anual_ordenado_insurance = retornos_anuales_ajustados_insurance.sort_values(ascending=False)

    # Crear un DataFrame con los datos ajustados
    datos2_insurance = pd.DataFrame()
    datos2_insurance['Retorno Anual Ajustado'] = retornos_anuales_ajustados_insurance
    datos2_insurance['Riesgo Anual Esperado'] = riesgo_anual_insurance
    datos2_insurance['Tickers'] = datos2_insurance.index
    datos2_insurance['Ratio'] = datos2_insurance['Retorno Anual Ajustado'] / datos2_insurance['Riesgo Anual Esperado']

    # Ordenar por el ratio
    datos2_insurance.sort_values(by='Ratio', axis=0, ascending=False, inplace=False)

    # Calcular Beta
    datos_insurance = pd.DataFrame(precios_insurance)
    retornos_diarios_insurance = datos_insurance.pct_change()
    covarianza_insurance = retornos_diarios_insurance.cov()
    varianza_insurance = np.var(retornos_diarios_insurance[etf_insurance])
    betas_insurance = []
    for t in tickers_insurance:
        beta_accion_insurance = covarianza_insurance.loc[t, etf_insurance] / varianza_insurance
        betas_insurance.append(beta_accion_insurance)

    tabla_insurance = pd.DataFrame({'Ticker': tickers_insurance, 'Beta': betas_insurance})
    tabla_insurance = tabla_insurance.round(2)
   
    # Graficar Retorno Ajustado vs Riesgo
    fig17 = px.scatter(
        datos2_insurance,
        x='Riesgo Anual Esperado',
        y='Retorno Anual Ajustado',
        text='Tickers',
        title='Retorno Anual Ajustado vs Riesgo Anual Esperado vs ETF'
    )

    # Añadir una línea horizontal punteada en el punto (0,0)
    fig17.add_shape(
        type="line",
        x0=0, y0=0, x1=0.6, y1=0,
        line=dict(color="Crimson", width=2, dash="dot")
    )

    # Actualizar etiquetas y estilo
    fig17.update_traces(marker=dict(color='DarkBlue', size=10), textposition='bottom center')
    fig17.update_layout(
        xaxis_title='Riesgo Anual Esperado',
        yaxis_title='Retorno Anual Ajustado',
        height=600,
        width=900
    )

    # Graficar los retornos anuales ajustados
    fig18 = go.Figure(data=[
        go.Bar(x=retorno_anual_ordenado_insurance.index, y=retorno_anual_ordenado_insurance)
    ])

    # Añadir etiquetas y título
    fig18.update_layout(
        title='Retornos Anualizados Ajustados del Portafolio vs ETF',
        xaxis_title='Ticker',
        yaxis_title='Retornos Anualizados Ajustados',
        xaxis_tickangle=-90,
         height=600,
        width=900
    )

   
    data_insurance = pd.DataFrame({'Ticker': tickers_insurance, 'Beta': betas_insurance, 'Retorno Anual': retorno_anual_ordenado_insurance})
    data_insurance = data_insurance.dropna().round({'Beta': 2, 'Retorno Anual': 2})

    # Crear la gráfica entre Retornos Anuales Ajustados vs Beta con nombres de los tickers y puntos más grandes
    fig19 = px.scatter(data_insurance, x='Beta', y='Retorno Anual', text='Ticker',
                      labels={'x': 'Beta', 'y': 'Retorno Anual'},
                      title='Relación entre Retornos Anuales Ajustados y Beta',width=900, height=600)

    fig19.update_traces(marker=dict(size=10), textposition='top center')

    # Añadir una línea punteada vertical en Beta 1
    fig19.add_trace(go.Scatter(x=[1, 1], y=[data_insurance['Retorno Anual'].min(), data_insurance['Retorno Anual'].max()],
                              mode='lines',
                              line=dict(dash='dash', color='red'),
                              showlegend=False))
    
    precios_acumulados_insurance = (1 + retorno_diarios_insurance).cumprod() - 1

    # Graficar los retornos acumulados
    fig20 = px.line(precios_acumulados_insurance, title='Retornos Acumulados')
    fig20.update_layout(
        xaxis_title='Fecha',
        yaxis_title='Retornos Acumulados',
        height=600,
        width=900
    )
    
    return fig17, fig18, fig19, fig20

#################################################################################################################################################################################################################################################################################################################################################################################################################################

# ENERGY - IYE
def realizar_calculos5():
    # Paso 1: Scrape los tickers de la página de BlackRock
    json_url_energy = 'https://www.blackrock.com/mx/intermediarios/productos/239507/ishares-us-energy-etf/1501904811835.ajax?tab=all&fileType=json'

    response_energy = requests.get(json_url_energy)

    # Verificar si la solicitud fue exitosa
    if response_energy.status_code == 200:
        data_energy = response_energy.content.decode('utf-8-sig')
        json_data_energy = json.loads(data_energy)

        holdings_data_energy = json_data_energy.get('aaData', [])
        df_energy = pd.DataFrame(holdings_data_energy)

        # Extraer la primera columna (asumiendo que contiene los tickers)
        first_column_energy = df_energy.iloc[:, 0].tolist()

        # Guardar los tickers en un archivo CSV
        tickers_df_energy = pd.DataFrame(first_column_energy, columns=['Ticker'])
        tickers_df_energy.to_csv('tickers_energy.csv', index=False)

        st.write("Tickers extraídos y guardados en tickers_energy.csv")
    else:
        st.write("No se pudo descargar los datos JSON.")
        return None, None, None, None, None

    # Lista de tickers a excluir
    tickers_to_exclude_energy = ['USD', 'ESM4', 'BRKB', 'MSFUT', 'XTSLA', 'ESU4', 'MARGIN_USD', 'IXTU4','WFFUT', 'XASU4', 'RTYU4']

    # Filtrar los tickers excluyendo los no válidos
    tickers_energy = [ticker for ticker in first_column_energy if ticker not in tickers_to_exclude_energy]
    etf_ticker_energy = 'IYE'
    tickers_energy.append(etf_ticker_energy)

    inicio_energy = '2024-01-01'
    final_energy = dia_final
    etf_energy = 'IYE'

    # Descargar datos de precios ajustados
    def descargar_datos_energy(tickers_energy, inicio_energy, final_energy):
        datos_energy = yf.download(tickers_energy, inicio_energy, final_energy)['Adj Close']
        return datos_energy

    precios_energy = descargar_datos_energy(tickers_energy, inicio_energy, final_energy)
    precios_etf_energy = descargar_datos_energy([etf_energy], inicio_energy, final_energy)

    # Calcular retornos diarios
    retorno_diarios_energy = precios_energy.pct_change(1)
    retorno_diarios_etf_energy = precios_etf_energy.pct_change(1)

    # Calcular retornos anuales
    retornos_anuales_energy = retorno_diarios_energy.mean() * 252
    retorno_anual_etf_energy = retorno_diarios_etf_energy.mean() * 252

    # Ajustar retornos anuales en relación con el retorno del ETF
    retorno_anual_etf_valor_energy = retorno_anual_etf_energy.item()
    retornos_anuales_ajustados_energy = retornos_anuales_energy - retorno_anual_etf_valor_energy

    # Calcular riesgo anual
    riesgo_anual_energy = retorno_diarios_energy.std() * math.sqrt(252)

    # Ordenar los retornos anuales ajustados
    retorno_anual_ordenado_energy = retornos_anuales_ajustados_energy.sort_values(ascending=False)

    # Crear un DataFrame con los datos ajustados
    datos2_energy = pd.DataFrame()
    datos2_energy['Retorno Anual Ajustado'] = retornos_anuales_ajustados_energy
    datos2_energy['Riesgo Anual Esperado'] = riesgo_anual_energy
    datos2_energy['Tickers'] = datos2_energy.index
    datos2_energy['Ratio'] = datos2_energy['Retorno Anual Ajustado'] / datos2_energy['Riesgo Anual Esperado']

    # Ordenar por el ratio
    datos2_energy.sort_values(by='Ratio', axis=0, ascending=False, inplace=False)

    # Calcular Beta
    datos_energy = pd.DataFrame(precios_energy)
    retornos_diarios_energy = datos_energy.pct_change()
    covarianza_energy = retornos_diarios_energy.cov()
    varianza_energy = np.var(retornos_diarios_energy[etf_energy])
    betas_energy = []
    for t in tickers_energy:
        beta_accion_energy = covarianza_energy.loc[t, etf_energy] / varianza_energy
        betas_energy.append(beta_accion_energy)

    tabla_energy = pd.DataFrame({'Ticker': tickers_energy, 'Beta': betas_energy})
    tabla_energy = tabla_energy.round(2)
   
    # Graficar Retorno Ajustado vs Riesgo
    fig21 = px.scatter(
        datos2_energy,
        x='Riesgo Anual Esperado',
        y='Retorno Anual Ajustado',
        text='Tickers',
        title='Retorno Anual Ajustado vs Riesgo Anual Esperado vs ETF'
    )

    # Añadir una línea horizontal punteada en el punto (0,0)
    fig21.add_shape(
        type="line",
        x0=0, y0=0, x1=0.6, y1=0,
        line=dict(color="Crimson", width=2, dash="dot")
    )

    # Actualizar etiquetas y estilo
    fig21.update_traces(marker=dict(color='DarkBlue', size=10), textposition='bottom center')
    fig21.update_layout(
        xaxis_title='Riesgo Anual Esperado',
        yaxis_title='Retorno Anual Ajustado',
        height=600,
        width=900
    )

    # Graficar los retornos anuales ajustados
    fig22 = go.Figure(data=[
        go.Bar(x=retorno_anual_ordenado_energy.index, y=retorno_anual_ordenado_energy)
    ])

    # Añadir etiquetas y título
    fig22.update_layout(
        title='Retornos Anualizados Ajustados del Portafolio vs ETF',
        xaxis_title='Ticker',
        yaxis_title='Retornos Anualizados Ajustados',
        xaxis_tickangle=-90,
         height=600,
        width=900
    )

   
    data_energy = pd.DataFrame({'Ticker': tickers_energy, 'Beta': betas_energy, 'Retorno Anual': retorno_anual_ordenado_energy})
    data_energy = data_energy.dropna().round({'Beta': 2, 'Retorno Anual': 2})

    # Crear la gráfica entre Retornos Anuales Ajustados vs Beta con nombres de los tickers y puntos más grandes
    fig23 = px.scatter(data_energy, x='Beta', y='Retorno Anual', text='Ticker',
                      labels={'x': 'Beta', 'y': 'Retorno Anual'},
                      title='Relación entre Retornos Anuales Ajustados y Beta',width=900, height=600)

    fig23.update_traces(marker=dict(size=10), textposition='top center')

    # Añadir una línea punteada vertical en Beta 1
    fig23.add_trace(go.Scatter(x=[1, 1], y=[data_energy['Retorno Anual'].min(), data_energy['Retorno Anual'].max()],
                              mode='lines',
                              line=dict(dash='dash', color='red'),
                              showlegend=False))
    
    precios_acumulados_energy = (1 + retorno_diarios_energy).cumprod() - 1

    # Graficar los retornos acumulados
    fig24 = px.line(precios_acumulados_energy, title='Retornos Acumulados')
    fig24.update_layout(
        xaxis_title='Fecha',
        yaxis_title='Retornos Acumulados',
        height=600,
        width=900
    )
    
    return fig21, fig22, fig23, fig24

#################################################################################################################################################################################################################################################################################################################################################################################################################################

# HEALTHCARE - IYH
def realizar_calculos6():
    # Paso 1: Scrape los tickers de la página de BlackRock
    json_url_healthcare = 'https://www.blackrock.com/mx/intermediarios/productos/239511/ishares-us-healthcare-etf/1501904811835.ajax?tab=all&fileType=json'

    response_healthcare = requests.get(json_url_healthcare)

    # Verificar si la solicitud fue exitosa
    if response_healthcare.status_code == 200:
        data_healthcare = response_healthcare.content.decode('utf-8-sig')
        json_data_healthcare = json.loads(data_healthcare)

        holdings_data_healthcare = json_data_healthcare.get('aaData', [])
        df_healthcare = pd.DataFrame(holdings_data_healthcare)

        # Extraer la primera columna (asumiendo que contiene los tickers)
        first_column_healthcare = df_healthcare.iloc[:, 0].tolist()

        # Guardar los tickers en un archivo CSV
        tickers_df_healthcare = pd.DataFrame(first_column_healthcare, columns=['Ticker'])
        tickers_df_healthcare.to_csv('tickers_healthcare.csv', index=False)

        st.write("Tickers extraídos y guardados en tickers_healthcare.csv")
    else:
        st.write("No se pudo descargar los datos JSON.")
        return None, None, None, None, None

    # Lista de tickers a excluir
    tickers_to_exclude_healthcare = ['USD', 'ESM4', 'BRKB', 'MSFUT', 'XTSLA', 'ESU4', 'MARGIN_USD', 'IXTU4', 'WFFUT', 'XASU4', 'RTYU4']

    # Filtrar los tickers excluyendo los no válidos
    tickers_healthcare = [ticker for ticker in first_column_healthcare if ticker not in tickers_to_exclude_healthcare]
    etf_ticker_healthcare = 'IYH'
    tickers_healthcare.append(etf_ticker_healthcare)

    inicio_healthcare = '2024-01-01'
    final_healthcare = dia_final
    etf_healthcare = 'IYH'

    # Descargar datos de precios ajustados
    def descargar_datos_healthcare(tickers_healthcare, inicio_healthcare, final_healthcare):
        datos_healthcare = yf.download(tickers_healthcare, inicio_healthcare, final_healthcare)['Adj Close']
        return datos_healthcare

    precios_healthcare = descargar_datos_healthcare(tickers_healthcare, inicio_healthcare, final_healthcare)
    precios_etf_healthcare = descargar_datos_healthcare([etf_healthcare], inicio_healthcare, final_healthcare)

    # Calcular retornos diarios
    retorno_diarios_healthcare = precios_healthcare.pct_change(1)
    retorno_diarios_etf_healthcare = precios_etf_healthcare.pct_change(1)

    # Calcular retornos anuales
    retornos_anuales_healthcare = retorno_diarios_healthcare.mean() * 252
    retorno_anual_etf_healthcare = retorno_diarios_etf_healthcare.mean() * 252

    # Ajustar retornos anuales en relación con el retorno del ETF
    retorno_anual_etf_valor_healthcare = retorno_anual_etf_healthcare.item()
    retornos_anuales_ajustados_healthcare = retornos_anuales_healthcare - retorno_anual_etf_valor_healthcare

    # Calcular riesgo anual
    riesgo_anual_healthcare = retorno_diarios_healthcare.std() * math.sqrt(252)

    # Ordenar los retornos anuales ajustados
    retorno_anual_ordenado_healthcare = retornos_anuales_ajustados_healthcare.sort_values(ascending=False)

    # Crear un DataFrame con los datos ajustados
    datos2_healthcare = pd.DataFrame()
    datos2_healthcare['Retorno Anual Ajustado'] = retornos_anuales_ajustados_healthcare
    datos2_healthcare['Riesgo Anual Esperado'] = riesgo_anual_healthcare
    datos2_healthcare['Tickers'] = datos2_healthcare.index
    datos2_healthcare['Ratio'] = datos2_healthcare['Retorno Anual Ajustado'] / datos2_healthcare['Riesgo Anual Esperado']

    # Ordenar por el ratio
    datos2_healthcare.sort_values(by='Ratio', axis=0, ascending=False, inplace=False)

    # Calcular Beta
    datos_healthcare = pd.DataFrame(precios_healthcare)
    retornos_diarios_healthcare = datos_healthcare.pct_change()
    covarianza_healthcare = retornos_diarios_healthcare.cov()
    varianza_healthcare = np.var(retornos_diarios_healthcare[etf_healthcare])
    betas_healthcare = []
    for t in tickers_healthcare:
        beta_accion_healthcare = covarianza_healthcare.loc[t, etf_healthcare] / varianza_healthcare
        betas_healthcare.append(beta_accion_healthcare)

    tabla_healthcare = pd.DataFrame({'Ticker': tickers_healthcare, 'Beta': betas_healthcare})
    tabla_healthcare = tabla_healthcare.round(2)
   
    # Graficar Retorno Ajustado vs Riesgo
    fig25 = px.scatter(
        datos2_healthcare,
        x='Riesgo Anual Esperado',
        y='Retorno Anual Ajustado',
        text='Tickers',
        title='Retorno Anual Ajustado vs Riesgo Anual Esperado vs ETF'
    )

    # Añadir una línea horizontal punteada en el punto (0,0)
    fig25.add_shape(
        type="line",
        x0=0, y0=0, x1=0.6, y1=0,
        line=dict(color="Crimson", width=2, dash="dot")
    )

    # Actualizar etiquetas y estilo
    fig25.update_traces(marker=dict(color='DarkBlue', size=10), textposition='bottom center')
    fig25.update_layout(
        xaxis_title='Riesgo Anual Esperado',
        yaxis_title='Retorno Anual Ajustado',
        height=600,
        width=900
    )

    # Graficar los retornos anuales ajustados
    fig26 = go.Figure(data=[
        go.Bar(x=retorno_anual_ordenado_healthcare.index, y=retorno_anual_ordenado_healthcare)
    ])

    # Añadir etiquetas y título
    fig26.update_layout(
        title='Retornos Anualizados Ajustados del Portafolio vs ETF',
        xaxis_title='Ticker',
        yaxis_title='Retornos Anualizados Ajustados',
        xaxis_tickangle=-90,
         height=600,
        width=900
    )

   
    data_healthcare = pd.DataFrame({'Ticker': tickers_healthcare, 'Beta': betas_healthcare, 'Retorno Anual': retorno_anual_ordenado_healthcare})
    data_healthcare = data_healthcare.dropna().round({'Beta': 2, 'Retorno Anual': 2})

    # Crear la gráfica entre Retornos Anuales Ajustados vs Beta con nombres de los tickers y puntos más grandes
    fig27 = px.scatter(data_healthcare, x='Beta', y='Retorno Anual', text='Ticker',
                      labels={'x': 'Beta', 'y': 'Retorno Anual'},
                      title='Relación entre Retornos Anuales Ajustados y Beta',width=900, height=600)

    fig27.update_traces(marker=dict(size=10), textposition='top center')

    # Añadir una línea punteada vertical en Beta 1
    fig27.add_trace(go.Scatter(x=[1, 1], y=[data_healthcare['Retorno Anual'].min(), data_healthcare['Retorno Anual'].max()],
                              mode='lines',
                              line=dict(dash='dash', color='red'),
                              showlegend=False))
    
    precios_acumulados_healthcare = (1 + retorno_diarios_healthcare).cumprod() - 1

    # Graficar los retornos acumulados
    fig28 = px.line(precios_acumulados_healthcare, title='Retornos Acumulados')
    fig28.update_layout(
        xaxis_title='Fecha',
        yaxis_title='Retornos Acumulados',
        height=600,
        width=900
    )
    
    return fig25, fig26, fig27, fig28

#################################################################################################################################################################################################################################################################################################################################################################################################################################

# GROWTH - IVW
def realizar_calculos7():
    # Paso 1: Scrape los tickers de la página de BlackRock
    json_url_growth = 'https://www.blackrock.com/mx/intermediarios/productos/239725/ishares-sp-500-growth-etf/1501904811835.ajax?tab=all&fileType=json'

    response_growth = requests.get(json_url_growth)

    # Verificar si la solicitud fue exitosa
    if response_growth.status_code == 200:
        data_growth = response_growth.content.decode('utf-8-sig')
        json_data_growth = json.loads(data_growth)

        holdings_data_growth = json_data_growth.get('aaData', [])
        df_growth = pd.DataFrame(holdings_data_growth)

        # Extraer la primera columna (asumiendo que contiene los tickers)
        first_column_growth = df_growth.iloc[:, 0].tolist()

        # Guardar los tickers en un archivo CSV
        tickers_df_growth = pd.DataFrame(first_column_growth, columns=['Ticker'])
        tickers_df_growth.to_csv('tickers_growth.csv', index=False)

        st.write("Tickers extraídos y guardados en tickers_growth.csv")
    else:
        st.write("No se pudo descargar los datos JSON.")
        return None, None, None, None, None

    # Lista de tickers a excluir
    tickers_to_exclude_growth = ['USD', 'ESM4', 'BRKB', 'MSFUT', 'XTSLA', 'ESU4', 'MARGIN_USD', 'IXTU4', 'WFFUT', 'XASU4', 'RTYU4']

    # Filtrar los tickers excluyendo los no válidos
    tickers_growth = [ticker for ticker in first_column_growth if ticker not in tickers_to_exclude_growth]
    etf_ticker_growth = 'IVW'
    tickers_growth.append(etf_ticker_growth)

    inicio_growth = '2024-01-01'
    final_growth = dia_final
    etf_growth = 'IVW'

    # Descargar datos de precios ajustados
    def descargar_datos_growth(tickers_growth, inicio_growth, final_growth):
        datos_growth = yf.download(tickers_growth, inicio_growth, final_growth)['Adj Close']
        return datos_growth

    precios_growth = descargar_datos_growth(tickers_growth, inicio_growth, final_growth)
    precios_etf_growth = descargar_datos_growth([etf_growth], inicio_growth, final_growth)

    # Calcular retornos diarios
    retorno_diarios_growth = precios_growth.pct_change(1)
    retorno_diarios_etf_growth = precios_etf_growth.pct_change(1)

    # Calcular retornos anuales
    retornos_anuales_growth = retorno_diarios_growth.mean() * 252
    retorno_anual_etf_growth = retorno_diarios_etf_growth.mean() * 252

    # Ajustar retornos anuales en relación con el retorno del ETF
    retorno_anual_etf_valor_growth = retorno_anual_etf_growth.item()
    retornos_anuales_ajustados_growth = retornos_anuales_growth - retorno_anual_etf_valor_growth

    # Calcular riesgo anual
    riesgo_anual_growth = retorno_diarios_growth.std() * math.sqrt(252)

    # Ordenar los retornos anuales ajustados
    retorno_anual_ordenado_growth = retornos_anuales_ajustados_growth.sort_values(ascending=False)

    # Crear un DataFrame con los datos ajustados
    datos2_growth = pd.DataFrame()
    datos2_growth['Retorno Anual Ajustado'] = retornos_anuales_ajustados_growth
    datos2_growth['Riesgo Anual Esperado'] = riesgo_anual_growth
    datos2_growth['Tickers'] = datos2_growth.index
    datos2_growth['Ratio'] = datos2_growth['Retorno Anual Ajustado'] / datos2_growth['Riesgo Anual Esperado']

    # Ordenar por el ratio
    datos2_growth.sort_values(by='Ratio', axis=0, ascending=False, inplace=False)

    # Calcular Beta
    datos_growth = pd.DataFrame(precios_growth)
    retornos_diarios_growth = datos_growth.pct_change()
    covarianza_growth = retornos_diarios_growth.cov()
    varianza_growth = np.var(retornos_diarios_growth[etf_growth])
    betas_growth = []
    for t in tickers_growth:
        beta_accion_growth = covarianza_growth.loc[t, etf_growth] / varianza_growth
        betas_growth.append(beta_accion_growth)

    tabla_growth = pd.DataFrame({'Ticker': tickers_growth, 'Beta': betas_growth})
    tabla_growth = tabla_growth.round(2)
   
    # Graficar Retorno Ajustado vs Riesgo
    fig29 = px.scatter(
        datos2_growth,
        x='Riesgo Anual Esperado',
        y='Retorno Anual Ajustado',
        text='Tickers',
        title='Retorno Anual Ajustado vs Riesgo Anual Esperado vs ETF'
    )

    # Añadir una línea horizontal punteada en el punto (0,0)
    fig29.add_shape(
        type="line",
        x0=0, y0=0, x1=0.6, y1=0,
        line=dict(color="Crimson", width=2, dash="dot")
    )

    # Actualizar etiquetas y estilo
    fig29.update_traces(marker=dict(color='DarkBlue', size=10), textposition='bottom center')
    fig29.update_layout(
        xaxis_title='Riesgo Anual Esperado',
        yaxis_title='Retorno Anual Ajustado',
        height=600,
        width=900
    )

    # Graficar los retornos anuales ajustados
    fig30 = go.Figure(data=[
        go.Bar(x=retorno_anual_ordenado_growth.index, y=retorno_anual_ordenado_growth)
    ])

    # Añadir etiquetas y título
    fig30.update_layout(
        title='Retornos Anualizados Ajustados del Portafolio vs ETF',
        xaxis_title='Ticker',
        yaxis_title='Retornos Anualizados Ajustados',
        xaxis_tickangle=-90,
         height=600,
        width=900
    )

   
    data_growth = pd.DataFrame({'Ticker': tickers_growth, 'Beta': betas_growth, 'Retorno Anual': retorno_anual_ordenado_growth})
    data_growth = data_growth.dropna().round({'Beta': 2, 'Retorno Anual': 2})

    # Crear la gráfica entre Retornos Anuales Ajustados vs Beta con nombres de los tickers y puntos más grandes
    fig31 = px.scatter(data_growth, x='Beta', y='Retorno Anual', text='Ticker',
                      labels={'x': 'Beta', 'y': 'Retorno Anual'},
                      title='Relación entre Retornos Anuales Ajustados y Beta',width=900, height=600)

    fig31.update_traces(marker=dict(size=10), textposition='top center')

    # Añadir una línea punteada vertical en Beta 1
    fig31.add_trace(go.Scatter(x=[1, 1], y=[data_growth['Retorno Anual'].min(), data_growth['Retorno Anual'].max()],
                              mode='lines',
                              line=dict(dash='dash', color='red'),
                              showlegend=False))
    
    precios_acumulados_growth = (1 + retorno_diarios_growth).cumprod() - 1

    # Graficar los retornos acumulados
    fig32 = px.line(precios_acumulados_growth, title='Retornos Acumulados')
    fig32.update_layout(
        xaxis_title='Fecha',
        yaxis_title='Retornos Acumulados',
        height=600,
        width=900
    )
    
    return fig29, fig30, fig31, fig32

#################################################################################################################################################################################################################################################################################################################################################################################################################################

# SP500 - IVV
def realizar_calculos8():
    # Paso 1: Scrape los tickers de la página de BlackRock
    json_url_core = 'https://www.blackrock.com/mx/intermediarios/productos/239726/ishares-core-sp-500-etf/1501904811835.ajax?tab=all&fileType=json'

    response_core = requests.get(json_url_core)

    # Verificar si la solicitud fue exitosa
    if response_core.status_code == 200:
        data_core = response_core.content.decode('utf-8-sig')
        json_data_core = json.loads(data_core)

        holdings_data_core = json_data_core.get('aaData', [])
        df_core = pd.DataFrame(holdings_data_core)

        # Extraer la primera columna (asumiendo que contiene los tickers)
        first_column_core = df_core.iloc[:, 0].tolist()

        # Guardar los tickers en un archivo CSV
        tickers_df_core = pd.DataFrame(first_column_core, columns=['Ticker'])
        tickers_df_core.to_csv('tickers_core.csv', index=False)

        st.write("Tickers extraídos y guardados en tickers_core.csv")
    else:
        st.write("No se pudo descargar los datos JSON.")
        return None, None, None, None, None

    # Lista de tickers a excluir
    tickers_to_exclude_core = ['USD', 'ESM4', 'BRKB', 'MSFUT', 'XTSLA', 'ESU4', 'MARGIN_USD', 'IXTU4', 'WFFUT', 'XASU4', 'RTYU4']

    # Filtrar los tickers excluyendo los no válidos
    tickers_core = [ticker for ticker in first_column_core if ticker not in tickers_to_exclude_core]
    etf_ticker_core = 'IVV'
    tickers_core.append(etf_ticker_core)

    inicio_core = '2024-01-01'
    final_core = dia_final
    etf_core = 'IVV'

    # Descargar datos de precios ajustados
    def descargar_datos_core(tickers_core, inicio_core, final_core):
        datos_core = yf.download(tickers_core, inicio_core, final_core)['Adj Close']
        return datos_core

    precios_core = descargar_datos_core(tickers_core, inicio_core, final_core)
    precios_etf_core = descargar_datos_core([etf_core], inicio_core, final_core)

    # Calcular retornos diarios
    retorno_diarios_core = precios_core.pct_change(1)
    retorno_diarios_etf_core = precios_etf_core.pct_change(1)

    # Calcular retornos anuales
    retornos_anuales_core = retorno_diarios_core.mean() * 252
    retorno_anual_etf_core = retorno_diarios_etf_core.mean() * 252

    # Ajustar retornos anuales en relación con el retorno del ETF
    retorno_anual_etf_valor_core = retorno_anual_etf_core.item()
    retornos_anuales_ajustados_core = retornos_anuales_core - retorno_anual_etf_valor_core

    # Calcular riesgo anual
    riesgo_anual_core = retorno_diarios_core.std() * math.sqrt(252)

    # Ordenar los retornos anuales ajustados
    retorno_anual_ordenado_core = retornos_anuales_ajustados_core.sort_values(ascending=False)

    # Crear un DataFrame con los datos ajustados
    datos2_core = pd.DataFrame()
    datos2_core['Retorno Anual Ajustado'] = retornos_anuales_ajustados_core
    datos2_core['Riesgo Anual Esperado'] = riesgo_anual_core
    datos2_core['Tickers'] = datos2_core.index
    datos2_core['Ratio'] = datos2_core['Retorno Anual Ajustado'] / datos2_core['Riesgo Anual Esperado']

    # Ordenar por el ratio
    datos2_core.sort_values(by='Ratio', axis=0, ascending=False, inplace=False)

    # Calcular Beta
    datos_core = pd.DataFrame(precios_core)
    retornos_diarios_core = datos_core.pct_change()
    covarianza_core = retornos_diarios_core.cov()
    varianza_core = np.var(retornos_diarios_core[etf_core])
    betas_core = []
    for t in tickers_core:
        beta_accion_core = covarianza_core.loc[t, etf_core] / varianza_core
        betas_core.append(beta_accion_core)

    tabla_core = pd.DataFrame({'Ticker': tickers_core, 'Beta': betas_core})
    tabla_core = tabla_core.round(2)
   
    # Graficar Retorno Ajustado vs Riesgo
    fig33 = px.scatter(
        datos2_core,
        x='Riesgo Anual Esperado',
        y='Retorno Anual Ajustado',
        text='Tickers',
        title='Retorno Anual Ajustado vs Riesgo Anual Esperado vs ETF'
    )

    # Añadir una línea horizontal punteada en el punto (0,0)
    fig33.add_shape(
        type="line",
        x0=0, y0=0, x1=0.6, y1=0,
        line=dict(color="Crimson", width=2, dash="dot")
    )

    # Actualizar etiquetas y estilo
    fig33.update_traces(marker=dict(color='DarkBlue', size=10), textposition='bottom center')
    fig33.update_layout(
        xaxis_title='Riesgo Anual Esperado',
        yaxis_title='Retorno Anual Ajustado',
        height=600,
        width=900
    )

    # Graficar los retornos anuales ajustados
    fig34 = go.Figure(data=[
        go.Bar(x=retorno_anual_ordenado_core.index, y=retorno_anual_ordenado_core)
    ])

    # Añadir etiquetas y título
    fig34.update_layout(
        title='Retornos Anualizados Ajustados del Portafolio vs ETF',
        xaxis_title='Ticker',
        yaxis_title='Retornos Anualizados Ajustados',
        xaxis_tickangle=-90,
         height=600,
        width=900
    )

   
    data_core = pd.DataFrame({'Ticker': tickers_core, 'Beta': betas_core, 'Retorno Anual': retorno_anual_ordenado_core})
    data_core = data_core.dropna().round({'Beta': 2, 'Retorno Anual': 2})

    # Crear la gráfica entre Retornos Anuales Ajustados vs Beta con nombres de los tickers y puntos más grandes
    fig35 = px.scatter(data_core, x='Beta', y='Retorno Anual', text='Ticker',
                      labels={'x': 'Beta', 'y': 'Retorno Anual'},
                      title='Relación entre Retornos Anuales Ajustados y Beta', width=900, height=600)

    fig35.update_traces(marker=dict(size=10), textposition='top center')

    # Añadir una línea punteada vertical en Beta 1
    fig35.add_trace(go.Scatter(x=[1, 1], y=[data_core['Retorno Anual'].min(), data_core['Retorno Anual'].max()],
                              mode='lines',
                              line=dict(dash='dash', color='red'),
                              showlegend=False))
    
    precios_acumulados_core = (1 + retorno_diarios_core).cumprod() - 1

    # Graficar los retornos acumulados
    fig36 = px.line(precios_acumulados_core, title='Retornos Acumulados')
    fig36.update_layout(
        xaxis_title='Fecha',
        yaxis_title='Retornos Acumulados',
        height=600,
        width=900
    )
    
    return fig33, fig34, fig35, fig36










































##############################################################################################################################################################################################################################################################################################################################################################################################################################

# Configurar Streamlit
st.title("Smart Beta App")
st.caption("By Fernando Guzman")

# Crear una pestaña para S&P 100
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs(["S&P 100", "Technology", "Semiconductors", "Russell 1000", "Insurance", "Energy", "Healthcare", "Growth", "S&P 500"])

with tab1:
    st.header("S&P 100")
    st.write("The index measures the performance of the large-capitalization sector of the U.S. equity market. The fund generally will invest at least 80% of its assets in the component securities of its index and in investments that have economic characteristics that are substantially identical to the component securities of its index and may invest up to 20% of its assets in certain futures, options and swap contracts, cash and cash equivalents.")
    
    # Paso 1: Scrape los datos de los componentes de la página de BlackRock
    json_url = 'https://www.blackrock.com/mx/intermediarios/productos/239723/ishares-sp-100-etf/1501904811835.ajax?tab=all&fileType=json'

    response = requests.get(json_url)

    # Verificar si la solicitud fue exitosa
    if response.status_code == 200:
        data = response.content.decode('utf-8-sig')
        json_data = json.loads(data)
        
        holdings_data = json_data.get('aaData', [])
        df = pd.DataFrame(holdings_data)

        # Asumiendo que la primera columna contiene los tickers y la sexta columna los pesos en formato {display: x%, raw: y}
        tickers = df.iloc[:, 0].tolist()
        weights = df.iloc[:, 5].apply(lambda x: float(x['display'].rstrip('%'))).tolist()  # Extraer el valor de 'display' y convertir a float
        
        # Crear un DataFrame con los tickers y sus pesos
        data = {'Ticker': tickers, 'Peso (%)': weights}
        df_weights = pd.DataFrame(data)
        
        # Limitar el número de componentes a mostrar
        limit = 20
        df_weights = df_weights.sort_values('Peso (%)', ascending=False)
        top_weights = df_weights[:limit]
        other_weights = df_weights[limit:]
        others_sum = other_weights['Peso (%)'].sum()
        
        # Añadir la categoría 'Otros' para los componentes restantes
        top_weights = pd.concat([top_weights, pd.DataFrame({'Ticker': ['Otros'], 'Peso (%)': [others_sum]})], ignore_index=True)
        
        # Crear el gráfico de pastel usando Plotly
        fig5 = px.pie(top_weights, values='Peso (%)', names='Ticker')
        
        # Mostrar el gráfico
        st.plotly_chart(fig5)
    else:
        print("No se pudo descargar los datos JSON.")
    
    if st.button("Realizar Cálculo - S&P 100"):
        fig1, fig2, fig3, fig4 = realizar_calculos()
        
        if fig1 and fig2 and fig3 and fig4 is not None:
            # Mostrar gráficos y datos
            st.plotly_chart(fig1)
            st.plotly_chart(fig2)
            st.plotly_chart(fig3)
            st.plotly_chart(fig4)
        else:
            st.write("Ocurrió un error al realizar los cálculos.")
            
with tab2:
    st.header("IYW Technology")
    st.write("The iShares U.S. Technology ETF (IYW) aims to track the Dow Jones U.S. Technology Capped Index, offering exposure to U.S. technology companies. It includes major firms like Apple, Microsoft, and Alphabet, providing broad exposure to the tech sector with a diversified portfolio of large-cap stocks. With an expense ratio of 0.39%, the ETF is relatively cost-effective. Historically, it has performed well, though the sector's volatility means future performance may vary. IYW is highly liquid, ensuring easy trading, but it offers a low dividend yield as it focuses on growth-oriented companies. Investors should be aware of the market, sector, and concentration risks inherent in a tech-focused fund. Managed by BlackRock, IYW is suitable for those seeking targeted tech exposure and willing to accept the associated risks as part of a diversified portfolio.")
    
    # Paso 1: Scrape los datos de los componentes de la página de BlackRock
    json_url = 'https://www.blackrock.com/mx/intermediarios/productos/239522/ishares-us-technology-etf/1501904811835.ajax?tab=all&fileType=json'

    response = requests.get(json_url)

    # Verificar si la solicitud fue exitosa
    if response.status_code == 200:
        data = response.content.decode('utf-8-sig')
        json_data = json.loads(data)
        
        holdings_data = json_data.get('aaData', [])
        df = pd.DataFrame(holdings_data)

        # Asumiendo que la primera columna contiene los tickers y la sexta columna los pesos en formato {display: x%, raw: y}
        tickers = df.iloc[:, 0].tolist()
        weights = df.iloc[:, 5].apply(lambda x: float(x['display'].rstrip('%'))).tolist()  # Extraer el valor de 'display' y convertir a float
        
        # Crear un DataFrame con los tickers y sus pesos
        data1 = {'Ticker': tickers, 'Peso (%)': weights}
        df_weights = pd.DataFrame(data1)
        
        # Limitar el número de componentes a mostrar
        limit = 20
        df_weights = df_weights.sort_values('Peso (%)', ascending=False)
        top_weights = df_weights[:limit]
        other_weights = df_weights[limit:]
        others_sum = other_weights['Peso (%)'].sum()
        
        # Añadir la categoría 'Otros' para los componentes restantes
        top_weights = pd.concat([top_weights, pd.DataFrame({'Ticker': ['Otros'], 'Peso (%)': [others_sum]})], ignore_index=True)
        
        # Crear el gráfico de pastel usando Plotly
        fig5 = px.pie(top_weights, values='Peso (%)', names='Ticker')
        
        # Mostrar el gráfico
        st.plotly_chart(fig5)
    else:
        print("No se pudo descargar los datos JSON.")
    
    if st.button("Realizar Cálculo - Technology"):
        fig5, fig6, fig7, fig8 = realizar_calculos1()
        
        if fig5 and fig6 and fig7 and fig8 is not None:
            # Mostrar gráficos y datos
            st.plotly_chart(fig5)
            st.plotly_chart(fig6)
            st.plotly_chart(fig7)
            st.plotly_chart(fig8)
        else:
            st.write("Ocurrió un error al realizar los cálculos.")
            
with tab3:
    st.header("SOXX Semiconductors")
    st.write("The iShares Semiconductor ETF (SOXX) aims to track the ICE Semiconductor Index, providing exposure to U.S. companies primarily engaged in the design, distribution, manufacture, and sale of semiconductors. The ETF includes major semiconductor firms such as NVIDIA, Intel, and Texas Instruments, offering a diversified portfolio within the semiconductor industry. With an expense ratio of 0.35%, SOXX is cost-effective for investors. Historically, the ETF has shown strong performance, reflecting the growth and innovation within the semiconductor sector, though it can be volatile. SOXX is highly liquid, facilitating easy trading, but it has a relatively low dividend yield as it focuses on growth-oriented companies. Investors should be aware of the market, sector, and concentration risks associated with a semiconductor-focused fund. Managed by BlackRock, SOXX is suitable for those seeking targeted exposure to the semiconductor industry and willing to accept the associated risks as part of a diversified portfolio.")
    
    # Paso 1: Scrape los datos de los componentes de la página de BlackRock
    json_url = 'https://www.blackrock.com/mx/intermediarios/productos/239705/ishares-phlx-semiconductor-etf/1501904811835.ajax?tab=all&fileType=json'

    response = requests.get(json_url)

    # Verificar si la solicitud fue exitosa
    if response.status_code == 200:
        data = response.content.decode('utf-8-sig')
        json_data = json.loads(data)
        
        holdings_data = json_data.get('aaData', [])
        df = pd.DataFrame(holdings_data)

        # Asumiendo que la primera columna contiene los tickers y la sexta columna los pesos en formato {display: x%, raw: y}
        tickers = df.iloc[:, 0].tolist()
        weights = df.iloc[:, 5].apply(lambda x: float(x['display'].rstrip('%'))).tolist()  # Extraer el valor de 'display' y convertir a float
        
        # Crear un DataFrame con los tickers y sus pesos
        data1 = {'Ticker': tickers, 'Peso (%)': weights}
        df_weights = pd.DataFrame(data1)
        
        # Limitar el número de componentes a mostrar
        limit = 20
        df_weights = df_weights.sort_values('Peso (%)', ascending=False)
        top_weights = df_weights[:limit]
        other_weights = df_weights[limit:]
        others_sum = other_weights['Peso (%)'].sum()
        
        # Añadir la categoría 'Otros' para los componentes restantes
        top_weights = pd.concat([top_weights, pd.DataFrame({'Ticker': ['Otros'], 'Peso (%)': [others_sum]})], ignore_index=True)
        
        # Crear el gráfico de pastel usando Plotly
        fig5 = px.pie(top_weights, values='Peso (%)', names='Ticker')
        
        # Mostrar el gráfico
        st.plotly_chart(fig5)
    else:
        print("No se pudo descargar los datos JSON.")
    
    if st.button("Realizar Cálculo - Semiconductors"):
        fig9, fig10, fig11, fig12 = realizar_calculos2()
        
        if fig9 and fig10 and fig11 and fig12 is not None:
            # Mostrar gráficos y datos
            st.plotly_chart(fig9)
            st.plotly_chart(fig10)
            st.plotly_chart(fig11)
            st.plotly_chart(fig12)
        else:
            st.write("Ocurrió un error al realizar los cálculos.")

with tab4:
    st.header("Russell 1000")
    st.write("The iShares Russell 1000 Growth ETF (IWF) aims to track the Russell 1000 Growth Index, providing exposure to large- and mid-cap U.S. companies with growth characteristics. The ETF includes major growth-oriented firms such as Apple, Microsoft, and Amazon, offering a diversified portfolio across various sectors. With an expense ratio of 0.19%, IWF is relatively cost-effective. Historically, it has performed well, capturing the growth potential of leading companies, though growth stocks can be more volatile compared to value stocks. IWF is highly liquid, ensuring easy trading, but it has a relatively low dividend yield as it focuses on companies that reinvest earnings for growth. Investors should be aware of the market and growth-specific risks associated with this ETF. Managed by BlackRock, IWF is suitable for those seeking targeted exposure to U.S. growth stocks and willing to accept the associated risks as part of a diversified portfolio.")
    
    # Paso 1: Scrape los datos de los componentes de la página de BlackRock
    json_url = 'https://www.blackrock.com/mx/intermediarios/productos/239706/ishares-russell-1000-growth-etf/1501904811835.ajax?tab=all&fileType=json'

    response = requests.get(json_url)

    # Verificar si la solicitud fue exitosa
    if response.status_code == 200:
        data = response.content.decode('utf-8-sig')
        json_data = json.loads(data)
        
        holdings_data = json_data.get('aaData', [])
        df = pd.DataFrame(holdings_data)

        # Asumiendo que la primera columna contiene los tickers y la sexta columna los pesos en formato {display: x%, raw: y}
        tickers = df.iloc[:, 0].tolist()
        weights = df.iloc[:, 5].apply(lambda x: float(x['display'].rstrip('%'))).tolist()  # Extraer el valor de 'display' y convertir a float
        
        # Crear un DataFrame con los tickers y sus pesos
        data1 = {'Ticker': tickers, 'Peso (%)': weights}
        df_weights = pd.DataFrame(data1)
        
        # Limitar el número de componentes a mostrar
        limit = 20
        df_weights = df_weights.sort_values('Peso (%)', ascending=False)
        top_weights = df_weights[:limit]
        other_weights = df_weights[limit:]
        others_sum = other_weights['Peso (%)'].sum()
        
        # Añadir la categoría 'Otros' para los componentes restantes
        top_weights = pd.concat([top_weights, pd.DataFrame({'Ticker': ['Otros'], 'Peso (%)': [others_sum]})], ignore_index=True)
        
        # Crear el gráfico de pastel usando Plotly
        fig5 = px.pie(top_weights, values='Peso (%)', names='Ticker')
        
        # Mostrar el gráfico
        st.plotly_chart(fig5)
    else:
        print("No se pudo descargar los datos JSON.")
    
    if st.button("Realizar Cálculo - Russell 1000"):
        fig13, fig14, fig15, fig16 = realizar_calculos3()
        
        if fig13 and fig14 and fig15 and fig16 is not None:
            # Mostrar gráficos y datos
            st.plotly_chart(fig13)
            st.plotly_chart(fig14)
            st.plotly_chart(fig15)
            st.plotly_chart(fig16)
        else:
            st.write("Ocurrió un error al realizar los cálculos.")

with tab5:
    st.header("Insurance")
    st.write("The iShares U.S. Insurance ETF (IAK) aims to track the Dow Jones U.S. Select Insurance Index, providing exposure to U.S. insurance companies across various segments, including life, property and casualty, and full-line insurers. The ETF includes major insurance firms such as MetLife, Chubb, and Prudential, offering a diversified portfolio within the insurance industry. With an expense ratio of 0.39%, IAK is relatively cost-effective. Historically, the ETF has delivered solid performance, reflecting the stability and growth potential of the insurance sector, though it may be impacted by industry-specific risks and economic conditions. IAK is highly liquid, facilitating easy trading, and typically offers a moderate dividend yield, as many insurance companies pay regular dividends. Investors should be aware of the market and sector-specific risks associated with this ETF. Managed by BlackRock, IAK is suitable for those seeking targeted exposure to the U.S. insurance industry and willing to accept the associated risks as part of a diversified portfolio.")
    
    # Paso 1: Scrape los datos de los componentes de la página de BlackRock
    json_url = 'https://www.blackrock.com/mx/intermediarios/productos/239515/ishares-us-insurance-etf/1501904811835.ajax?tab=all&fileType=json'

    response = requests.get(json_url)

    # Verificar si la solicitud fue exitosa
    if response.status_code == 200:
        data = response.content.decode('utf-8-sig')
        json_data = json.loads(data)
        
        holdings_data = json_data.get('aaData', [])
        df = pd.DataFrame(holdings_data)

        # Asumiendo que la primera columna contiene los tickers y la sexta columna los pesos en formato {display: x%, raw: y}
        tickers = df.iloc[:, 0].tolist()
        weights = df.iloc[:, 5].apply(lambda x: float(x['display'].rstrip('%'))).tolist()  # Extraer el valor de 'display' y convertir a float
        
        # Crear un DataFrame con los tickers y sus pesos
        data1 = {'Ticker': tickers, 'Peso (%)': weights}
        df_weights = pd.DataFrame(data1)
        
        # Limitar el número de componentes a mostrar
        limit = 20
        df_weights = df_weights.sort_values('Peso (%)', ascending=False)
        top_weights = df_weights[:limit]
        other_weights = df_weights[limit:]
        others_sum = other_weights['Peso (%)'].sum()
        
        # Añadir la categoría 'Otros' para los componentes restantes
        top_weights = pd.concat([top_weights, pd.DataFrame({'Ticker': ['Otros'], 'Peso (%)': [others_sum]})], ignore_index=True)
        
        # Crear el gráfico de pastel usando Plotly
        fig5 = px.pie(top_weights, values='Peso (%)', names='Ticker')
        
        # Mostrar el gráfico
        st.plotly_chart(fig5)
    else:
        print("No se pudo descargar los datos JSON.")
    
    if st.button("Realizar Cálculo - Insurance"):
        fig17, fig18, fig19, fig20 = realizar_calculos4()
        
        if fig17 and fig18 and fig19 and fig20 is not None:
            # Mostrar gráficos y datos
            st.plotly_chart(fig17)
            st.plotly_chart(fig18)
            st.plotly_chart(fig19)
            st.plotly_chart(fig20)
        else:
            st.write("Ocurrió un error al realizar los cálculos.")
            
with tab6:
    st.header("Energy")
    st.write("The iShares U.S. Energy ETF (IYE) aims to track the Dow Jones U.S. Oil & Gas Index, providing exposure to U.S. companies engaged in the exploration, production, and distribution of oil and gas. The ETF includes major energy firms such as ExxonMobil, Chevron, and ConocoPhillips, offering a diversified portfolio within the energy sector. With an expense ratio of 0.39%, IYE is relatively cost-effective. Historically, the ETF's performance has been closely tied to the volatility of the oil and gas markets, reflecting both the growth and risks inherent in the energy sector. IYE is highly liquid, ensuring easy trading, and typically offers a higher dividend yield compared to other sectors, as many energy companies pay substantial dividends. Investors should be aware of the market, sector-specific, and geopolitical risks associated with this ETF. Managed by BlackRock, IYE is suitable for those seeking targeted exposure to the U.S. energy sector and willing to accept the associated risks as part of a diversified portfolio.")
    
    # Paso 1: Scrape los datos de los componentes de la página de BlackRock
    json_url = 'https://www.blackrock.com/mx/intermediarios/productos/239507/ishares-us-energy-etf/1501904811835.ajax?tab=all&fileType=json'

    response = requests.get(json_url)

    # Verificar si la solicitud fue exitosa
    if response.status_code == 200:
        data = response.content.decode('utf-8-sig')
        json_data = json.loads(data)
        
        holdings_data = json_data.get('aaData', [])
        df = pd.DataFrame(holdings_data)

        # Asumiendo que la primera columna contiene los tickers y la sexta columna los pesos en formato {display: x%, raw: y}
        tickers = df.iloc[:, 0].tolist()
        weights = df.iloc[:, 5].apply(lambda x: float(x['display'].rstrip('%'))).tolist()  # Extraer el valor de 'display' y convertir a float
        
        # Crear un DataFrame con los tickers y sus pesos
        data1 = {'Ticker': tickers, 'Peso (%)': weights}
        df_weights = pd.DataFrame(data1)
        
        # Limitar el número de componentes a mostrar
        limit = 20
        df_weights = df_weights.sort_values('Peso (%)', ascending=False)
        top_weights = df_weights[:limit]
        other_weights = df_weights[limit:]
        others_sum = other_weights['Peso (%)'].sum()
        
        # Añadir la categoría 'Otros' para los componentes restantes
        top_weights = pd.concat([top_weights, pd.DataFrame({'Ticker': ['Otros'], 'Peso (%)': [others_sum]})], ignore_index=True)
        
        # Crear el gráfico de pastel usando Plotly
        fig5 = px.pie(top_weights, values='Peso (%)', names='Ticker')
        
        # Mostrar el gráfico
        st.plotly_chart(fig5)
    else:
        print("No se pudo descargar los datos JSON.")
    
    if st.button("Realizar Cálculo - Energy"):
        fig21, fig22, fig23, fig24 = realizar_calculos5()
        
        if fig21 and fig22 and fig23 and fig24 is not None:
            # Mostrar gráficos y datos
            st.plotly_chart(fig21)
            st.plotly_chart(fig22)
            st.plotly_chart(fig23)
            st.plotly_chart(fig24)
        else:
            st.write("Ocurrió un error al realizar los cálculos.")

with tab7:
    st.header("Healthcare")
    st.write("The iShares Global Healthcare ETF (IXJ) aims to track the S&P Global 1200 Health Care Sector Index, providing exposure to global companies in the healthcare sector, including pharmaceuticals, biotechnology, medical devices, and healthcare providers. The ETF includes major healthcare firms such as Johnson & Johnson, Pfizer, and Roche, offering a diversified portfolio across various healthcare industries. With an expense ratio of 0.40%, IXJ is relatively cost-effective for investors. Historically, it has performed well, reflecting the stable growth and innovation within the healthcare sector, though it may be influenced by regulatory changes and healthcare reforms. IXJ is highly liquid, ensuring easy trading, and typically offers a moderate dividend yield as many healthcare companies pay regular dividends. Investors should be aware of market, sector-specific, and global risks associated with this ETF. Managed by BlackRock, IXJ is suitable for those seeking broad exposure to the global healthcare sector and willing to accept the associated risks as part of a diversified portfolio.")
    
    # Paso 1: Scrape los datos de los componentes de la página de BlackRock
    json_url = 'https://www.blackrock.com/mx/intermediarios/productos/239511/ishares-us-healthcare-etf/1501904811835.ajax?tab=all&fileType=json'

    response = requests.get(json_url)

    # Verificar si la solicitud fue exitosa
    if response.status_code == 200:
        data = response.content.decode('utf-8-sig')
        json_data = json.loads(data)
        
        holdings_data = json_data.get('aaData', [])
        df = pd.DataFrame(holdings_data)

        # Asumiendo que la primera columna contiene los tickers y la sexta columna los pesos en formato {display: x%, raw: y}
        tickers = df.iloc[:, 0].tolist()
        weights = df.iloc[:, 5].apply(lambda x: float(x['display'].rstrip('%'))).tolist()  # Extraer el valor de 'display' y convertir a float
        
        # Crear un DataFrame con los tickers y sus pesos
        data1 = {'Ticker': tickers, 'Peso (%)': weights}
        df_weights = pd.DataFrame(data1)
        
        # Limitar el número de componentes a mostrar
        limit = 20
        df_weights = df_weights.sort_values('Peso (%)', ascending=False)
        top_weights = df_weights[:limit]
        other_weights = df_weights[limit:]
        others_sum = other_weights['Peso (%)'].sum()
        
        # Añadir la categoría 'Otros' para los componentes restantes
        top_weights = pd.concat([top_weights, pd.DataFrame({'Ticker': ['Otros'], 'Peso (%)': [others_sum]})], ignore_index=True)
        
        # Crear el gráfico de pastel usando Plotly
        fig5 = px.pie(top_weights, values='Peso (%)', names='Ticker')
        
        # Mostrar el gráfico
        st.plotly_chart(fig5)
    else:
        print("No se pudo descargar los datos JSON.")
    
    if st.button("Realizar Cálculo - Healthcare"):
        fig25, fig26, fig27, fig28 = realizar_calculos6()
        
        if fig25 and fig26 and fig27 and fig28 is not None:
            # Mostrar gráficos y datos
            st.plotly_chart(fig25)
            st.plotly_chart(fig26)
            st.plotly_chart(fig27)
            st.plotly_chart(fig28)
        else:
            st.write("Ocurrió un error al realizar los cálculos.")
            

with tab8:
    st.header("S&P Growth 500")
    st.write("The iShares S&P 500 Growth ETF (IVW) aims to track the S&P 500 Growth Index, providing exposure to large-cap U.S. companies that exhibit growth characteristics. The ETF includes major growth-oriented firms such as Apple, Microsoft, and Amazon, offering a diversified portfolio across various sectors. With an expense ratio of 0.18%, IVW is cost-effective for investors. Historically, it has performed well, capturing the growth potential of leading companies, though growth stocks can be more volatile compared to value stocks. IVW is highly liquid, ensuring easy trading, but it has a relatively low dividend yield as it focuses on companies that reinvest earnings for growth. Investors should be aware of the market and growth-specific risks associated with this ETF. Managed by BlackRock, IVW is suitable for those seeking targeted exposure to U.S. growth stocks and willing to accept the associated risks as part of a diversified portfolio.")
    
    # Paso 1: Scrape los datos de los componentes de la página de BlackRock
    json_url = 'https://www.blackrock.com/mx/intermediarios/productos/239725/ishares-sp-500-growth-etf/1501904811835.ajax?tab=all&fileType=json'

    response = requests.get(json_url)

    # Verificar si la solicitud fue exitosa
    if response.status_code == 200:
        data = response.content.decode('utf-8-sig')
        json_data = json.loads(data)
        
        holdings_data = json_data.get('aaData', [])
        df = pd.DataFrame(holdings_data)

        # Asumiendo que la primera columna contiene los tickers y la sexta columna los pesos en formato {display: x%, raw: y}
        tickers = df.iloc[:, 0].tolist()
        weights = df.iloc[:, 5].apply(lambda x: float(x['display'].rstrip('%'))).tolist()  # Extraer el valor de 'display' y convertir a float
        
        # Crear un DataFrame con los tickers y sus pesos
        data1 = {'Ticker': tickers, 'Peso (%)': weights}
        df_weights = pd.DataFrame(data1)
        
        # Limitar el número de componentes a mostrar
        limit = 20
        df_weights = df_weights.sort_values('Peso (%)', ascending=False)
        top_weights = df_weights[:limit]
        other_weights = df_weights[limit:]
        others_sum = other_weights['Peso (%)'].sum()
        
        # Añadir la categoría 'Otros' para los componentes restantes
        top_weights = pd.concat([top_weights, pd.DataFrame({'Ticker': ['Otros'], 'Peso (%)': [others_sum]})], ignore_index=True)
        
        # Crear el gráfico de pastel usando Plotly
        fig5 = px.pie(top_weights, values='Peso (%)', names='Ticker')
        
        # Mostrar el gráfico
        st.plotly_chart(fig5)
    else:
        print("No se pudo descargar los datos JSON.")
    
    if st.button("Realizar Cálculo - Growth"):
        fig29, fig30, fig31, fig32 = realizar_calculos7()
        
        if fig29 and fig30 and fig31 and fig32 is not None:
            # Mostrar gráficos y datos
            st.plotly_chart(fig29)
            st.plotly_chart(fig30)
            st.plotly_chart(fig31)
            st.plotly_chart(fig32)
        else:
            st.write("Ocurrió un error al realizar los cálculos.")
                                                                
with tab9:
    st.header("S&P IVV 500")
    st.write("The iShares Core S&P 500 ETF (IVV) aims to track the S&P 500 Index, providing exposure to 500 of the largest publicly traded companies in the U.S. The ETF includes major firms such as Apple, Microsoft, and Amazon, offering a diversified portfolio across various sectors, representing the overall U.S. economy. With an expense ratio of 0.03%, IVV is extremely cost-effective for investors. Historically, it has performed well, reflecting the growth and stability of the U.S. stock market, though it is still subject to market volatility. IVV is highly liquid, ensuring easy trading, and typically offers a moderate dividend yield, as many of its underlying companies pay regular dividends. Investors should be aware of the market risks associated with this ETF. Managed by BlackRock, IVV is suitable for those seeking broad exposure to the U.S. stock market and willing to accept the associated risks as part of a diversified portfolio.")
    
    # Paso 1: Scrape los datos de los componentes de la página de BlackRock
    json_url = 'https://www.blackrock.com/mx/intermediarios/productos/239726/ishares-core-sp-500-etf/1501904811835.ajax?tab=all&fileType=json'

    response = requests.get(json_url)

    # Verificar si la solicitud fue exitosa
    if response.status_code == 200:
        data = response.content.decode('utf-8-sig')
        json_data = json.loads(data)
        
        holdings_data = json_data.get('aaData', [])
        df = pd.DataFrame(holdings_data)

        # Asumiendo que la primera columna contiene los tickers y la sexta columna los pesos en formato {display: x%, raw: y}
        tickers = df.iloc[:, 0].tolist()
        weights = df.iloc[:, 5].apply(lambda x: float(x['display'].rstrip('%'))).tolist()  # Extraer el valor de 'display' y convertir a float
        
        # Crear un DataFrame con los tickers y sus pesos
        data1 = {'Ticker': tickers, 'Peso (%)': weights}
        df_weights = pd.DataFrame(data1)
        
        # Limitar el número de componentes a mostrar
        limit = 20
        df_weights = df_weights.sort_values('Peso (%)', ascending=False)
        top_weights = df_weights[:limit]
        other_weights = df_weights[limit:]
        others_sum = other_weights['Peso (%)'].sum()
        
        # Añadir la categoría 'Otros' para los componentes restantes
        top_weights = pd.concat([top_weights, pd.DataFrame({'Ticker': ['Otros'], 'Peso (%)': [others_sum]})], ignore_index=True)
        
        # Crear el gráfico de pastel usando Plotly
        fig5 = px.pie(top_weights, values='Peso (%)', names='Ticker')
        
        # Mostrar el gráfico
        st.plotly_chart(fig5)
    else:
        print("No se pudo descargar los datos JSON.")
    
    if st.button("Realizar Cálculo - SP 500"):
        fig33, fig34, fig35, fig36 = realizar_calculos8()
        
        if fig33 and fig34 and fig35 and fig36 is not None:
            # Mostrar gráficos y datos
            st.plotly_chart(fig33)
            st.plotly_chart(fig34)
            st.plotly_chart(fig35)
            st.plotly_chart(fig36)
        else:
            st.write("Ocurrió un error al realizar los cálculos.")



