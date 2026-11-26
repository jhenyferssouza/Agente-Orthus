from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import streamlit as st


HORIZONTES = np.arange(1, 7)


st.set_page_config(
    page_title="Alerta de Transbordamento",
    page_icon="🌊",
    layout="wide",
)


@st.cache_resource
def carregar_modelo():
    caminhos = (
        Path("services/agente_previsao/models/baseline_ridge.pkl"),
        Path("baseline_ridge.pkl"),
    )

    for caminho in caminhos:
        if caminho.exists():
            try:
                modelo = joblib.load(caminho)
                return modelo, "Scikit-Learn (RidgeCV .pkl)"
            except Exception as exc:
                return None, f"Erro ao carregar .pkl: {exc}"

    return None, "Baseline de Regras Determinísticas"


def coletar_entradas():
    st.sidebar.header("Parâmetros de Entrada")

    st.sidebar.subheader("Estado Atual da Estação")
    cota_critica = st.sidebar.number_input(
        "Cota Crítica / Emergência (m)",
        min_value=1.0,
        max_value=10.0,
        value=3.80,
        step=0.10,
    )
    nivel_atual = st.sidebar.number_input(
        "Nível Atual Medido (m)",
        min_value=0.0,
        max_value=10.0,
        value=3.40,
        step=0.05,
    )
    taxa_variacao = st.sidebar.slider(
        "Velocidade de Subida / Taxa (m/h)",
        min_value=-0.50,
        max_value=1.00,
        value=0.15,
        step=0.01,
    )

    st.sidebar.subheader("Previsão de Chuva (Próximas 1h - 6h)")
    chuva_horaria = np.array(
        [
            st.sidebar.number_input("Chuva 1ª hora (mm)", 0.0, 100.0, 10.0),
            st.sidebar.number_input("Chuva 2ª hora (mm)", 0.0, 100.0, 15.0),
            st.sidebar.number_input("Chuva 3ª hora (mm)", 0.0, 100.0, 25.0),
            st.sidebar.number_input("Chuva 4ª hora (mm)", 0.0, 100.0, 10.0),
            st.sidebar.number_input("Chuva 5ª hora (mm)", 0.0, 100.0, 5.0),
            st.sidebar.number_input("Chuva 6ª hora (mm)", 0.0, 100.0, 0.0),
        ]
    )
    chuva_acumulada = np.cumsum(chuva_horaria)

    st.sidebar.subheader("Configuração de Incerteza")
    margem_erro_pct = (
        st.sidebar.slider(
            "Margem de Incerteza Estimada (±%)",
            min_value=1,
            max_value=20,
            value=7,
        )
        / 100.0
    )

    return (
        cota_critica,
        nivel_atual,
        taxa_variacao,
        chuva_acumulada,
        margem_erro_pct,
    )


def executar_inferencia(modelo, nivel_atual, taxa_variacao, chuva_acumulada):
    if modelo is not None:
        features = np.column_stack(
            (np.full(6, taxa_variacao), chuva_acumulada)
        )
        try:
            deltas = modelo.predict(features)
            return np.round(nivel_atual + deltas, 2)
        except Exception:
            features_alternativas = np.column_stack(
                (np.full(6, taxa_variacao), np.full(6, nivel_atual))
            )
            try:
                deltas = modelo.predict(features_alternativas)
                return np.round(nivel_atual + deltas, 2)
            except Exception:
                pass

    niveis = (
        nivel_atual
        + (taxa_variacao * HORIZONTES)
        + (chuva_acumulada * 0.015)
    )
    return np.round(niveis, 2)


def calcular_status(niveis_previstos, limite_superior, cota_critica):
    ultrapassou = np.where(limite_superior >= cota_critica)[0]
    if len(ultrapassou) > 0:
        tempo = int(HORIZONTES[ultrapassou[0]])
        return (
            tempo,
            "ALERTA VERMELHO - EMERGÊNCIA DE TRANSBORDAMENTO",
            "error",
        )

    if any(niveis_previstos >= cota_critica * 0.85):
        return (
            None,
            "ALERTA AMARELO - ATENÇÃO (NÍVEL ELEVADO)",
            "warning",
        )

    return None, "STATUS VERDE - NÍVEL ESTÁVEL", "info"


def exibir_alerta(status_alerta, cor_alerta, tempo_ate_cota, cota_critica):
    if cor_alerta == "error":
        st.error(
            f"🚨 **{status_alerta}** | Cota crítica de {cota_critica:.2f}m "
            f"poderá ser atingida em aproximadamente "
            f"**{tempo_ate_cota} hora(s)**!"
        )
    elif cor_alerta == "warning":
        st.warning(
            f"⚠️ **{status_alerta}** | "
            "Nível projetado atinge a zona de atenção nas próximas 6 horas."
        )
    else:
        st.success(
            f"✅ **{status_alerta}** | "
            "O nível do rio permanece dentro dos limites de segurança."
        )


def exibir_metricas(
    nivel_atual,
    taxa_variacao,
    chuva_acumulada,
    niveis_previstos,
    tempo_ate_cota,
):
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Nível Atual",
            f"{nivel_atual:.2f} m",
            delta=f"{taxa_variacao:+.2f} m/h",
        )
    with col2:
        nivel_max = np.max(niveis_previstos)
        st.metric(
            "Nível Máximo Previsto (6h)",
            f"{nivel_max:.2f} m",
            delta=f"{nivel_max - nivel_atual:+.2f} m",
        )
    with col3:
        tempo = (
            f"{tempo_ate_cota} hora(s)"
            if tempo_ate_cota
            else "Sem Risco (6h)"
        )
        st.metric("Tempo até Cota Crítica", tempo)
    with col4:
        st.metric(
            "Fatores Principais",
            f"Chuva 6h: {chuva_acumulada[-1]:.0f} mm",
            delta=f"Subida: {taxa_variacao:+.2f} m/h",
        )


def exibir_grafico_e_tabela(
    cota_critica,
    chuva_acumulada,
    niveis_previstos,
    limite_inferior,
    limite_superior,
    probabilidades,
):
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.subheader("📈 Projeção do Nível da Água (1h a 6h)")
        df_grafico = pd.DataFrame(
            {
                "Hora": [f"+{hora}h" for hora in HORIZONTES],
                "Nível Previsto (m)": niveis_previstos,
                "Limite Inferior (m)": limite_inferior,
                "Limite Superior (m)": limite_superior,
                "Cota Crítica (m)": np.full(6, cota_critica),
            }
        ).set_index("Hora")
        st.line_chart(
            df_grafico[
                [
                    "Nível Previsto (m)",
                    "Cota Crítica (m)",
                    "Limite Superior (m)",
                    "Limite Inferior (m)",
                ]
            ]
        )

    with col_right:
        st.subheader("Tabela de Inferência Detalhada")
        df_tabela = pd.DataFrame(
            {
                "Horizonte": [
                    f"+{hora} hora(s)" for hora in HORIZONTES
                ],
                "Chuva Acum. (mm)": chuva_acumulada,
                "Previsto (m)": niveis_previstos,
                "Incerteza (±)": [
                    f"[{inferior:.2f}m - {superior:.2f}m]"
                    for inferior, superior in zip(
                        limite_inferior,
                        limite_superior,
                    )
                ],
                "Risco (%)": [f"{risco:.1f}%" for risco in probabilidades],
            }
        )
        st.dataframe(df_tabela, use_container_width=True, hide_index=True)


def exibir_explicabilidade(
    taxa_variacao,
    margem_erro_pct,
    chuva_acumulada,
    limite_inferior,
    limite_superior,
    cota_critica,
):
    with st.expander(
        "Entenda os Fatores desta Previsão"
    ):
        st.markdown(
            f"""
* **Fatores Principais de Entrada**:
  1. **Velocidade de subida atual**:
     O rio está evoluindo a **`{taxa_variacao:+.2f} m/h`**.
  2. **Previsão de precipitação**:
     Acúmulo total previsto de **`{chuva_acumulada[-1]:.1f} mm`**
     para as próximas 6h.
* **Margem de Incerteza Estimada (±{margem_erro_pct * 100:.1f}%)**:
  - No horizonte de 6 horas, o nível estimado estará entre
    **`{limite_inferior[-1]:.2f}m`** e
    **`{limite_superior[-1]:.2f}m`**.
* **Cota Crítica Alvo**: **`{cota_critica:.2f} m`**.
"""
        )


def main():
    modelo, metodo_nome = carregar_modelo()
    (
        cota_critica,
        nivel_atual,
        taxa_variacao,
        chuva_acumulada,
        margem_erro_pct,
    ) = coletar_entradas()

    st.title("Protótipo: Teste de Inferência do Agente de Previsão")
    st.caption(f"**Método de Inferência Ativo:** {metodo_nome}")
    st.markdown("---")

    niveis_previstos = executar_inferencia(
        modelo,
        nivel_atual,
        taxa_variacao,
        chuva_acumulada,
    )
    limite_inferior = np.round(
        niveis_previstos * (1 - margem_erro_pct),
        2,
    )
    limite_superior = np.round(
        niveis_previstos * (1 + margem_erro_pct),
        2,
    )
    probabilidades = np.where(
        limite_superior >= cota_critica,
        np.clip(
            np.round((limite_superior / cota_critica) * 100, 1),
            0,
            100,
        ),
        np.clip(
            np.round((niveis_previstos / cota_critica) * 100, 1),
            0,
            99,
        ),
    )

    tempo_ate_cota, status_alerta, cor_alerta = calcular_status(
        niveis_previstos,
        limite_superior,
        cota_critica,
    )
    exibir_alerta(
        status_alerta,
        cor_alerta,
        tempo_ate_cota,
        cota_critica,
    )
    exibir_metricas(
        nivel_atual,
        taxa_variacao,
        chuva_acumulada,
        niveis_previstos,
        tempo_ate_cota,
    )
    st.markdown("---")
    exibir_grafico_e_tabela(
        cota_critica,
        chuva_acumulada,
        niveis_previstos,
        limite_inferior,
        limite_superior,
        probabilidades,
    )
    exibir_explicabilidade(
        taxa_variacao,
        margem_erro_pct,
        chuva_acumulada,
        limite_inferior,
        limite_superior,
        cota_critica,
    )


if __name__ == "__main__":
    main()
