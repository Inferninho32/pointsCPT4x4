from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

APP_TITLE = "CPT 4x4"
DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_FILE = DATA_DIR / "resultados_cpt4x4.json"

NOMES_CLASSES = [
    "Unlimited Petrol",
    "Unlimited Diesel",
    "X-Treme",
    "Promocao",
    "SSV",
]

NOMES_PROVAS = [
    "Valongo",
    "Cinfaes",
    "Macao",
    "Braganca",
    "Santa Maria da Feira",
    "Lordelo",
]

PONTUACOES = {
    1: 25,
    2: 20,
    3: 17,
    4: 14,
    5: 12,
    6: 10,
    7: 8,
    8: 6,
    9: 4,
    10: 2,
}


def pontos_etapa(posicao: int) -> int:
    return PONTUACOES.get(int(posicao), 1)


def dados_iniciais() -> dict[str, Any]:
    return {
        "classes": {classe: {} for classe in NOMES_CLASSES}
    }


def carregar_dados() -> dict[str, Any]:
    DATA_DIR.mkdir(exist_ok=True)
    if not DATA_FILE.exists():
        dados = dados_iniciais()
        guardar_dados(dados)
        return dados

    try:
        with DATA_FILE.open("r", encoding="utf-8") as f:
            dados = json.load(f)
    except (json.JSONDecodeError, OSError):
        dados = dados_iniciais()

    dados.setdefault("classes", {})
    for classe in NOMES_CLASSES:
        dados["classes"].setdefault(classe, {})
    return dados


def guardar_dados(dados: dict[str, Any]) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def normalizar_nome(nome: str) -> str:
    return nome.strip().replace(" ", "_")


def obter_equipas(dados: dict[str, Any], classe: str) -> dict[str, list[dict[str, Any]]]:
    return dados.setdefault("classes", {}).setdefault(classe, {})


def adicionar_resultado(
    dados: dict[str, Any],
    classe: str,
    prova: str,
    equipa: str,
    pos_etapa_1: int,
    pos_etapa_2: int,
) -> tuple[int, int]:
    equipa = normalizar_nome(equipa)
    if not equipa:
        raise ValueError("Introduza o nome da equipa.")
    if pos_etapa_1 <= 0 or pos_etapa_2 <= 0:
        raise ValueError("As posições têm de ser maiores que zero.")

    pts1 = pontos_etapa(pos_etapa_1)
    pts2 = pontos_etapa(pos_etapa_2)

    equipas = obter_equipas(dados, classe)
    equipas.setdefault(equipa, [])
    equipas[equipa].append({
        "prova": prova,
        "etapa": 1,
        "posicao": int(pos_etapa_1),
        "pontos": int(pts1),
    })
    equipas[equipa].append({
        "prova": prova,
        "etapa": 2,
        "posicao": int(pos_etapa_2),
        "pontos": int(pts2),
    })
    guardar_dados(dados)
    return pts1, pts2


def apagar_equipa(dados: dict[str, Any], classe: str, equipa: str) -> None:
    equipas = obter_equipas(dados, classe)
    if equipa in equipas:
        del equipas[equipa]
        guardar_dados(dados)


def apagar_classe(dados: dict[str, Any], classe: str) -> None:
    dados["classes"][classe] = {}
    guardar_dados(dados)


def apagar_etapa(dados: dict[str, Any], classe: str, equipa: str, indice: int) -> None:
    equipas = obter_equipas(dados, classe)
    etapas = equipas.get(equipa, [])
    if 0 <= indice < len(etapas):
        etapas.pop(indice)
        guardar_dados(dados)


def piores_etapas(etapas: list[dict[str, Any]], quantidade: int = 2) -> list[dict[str, Any]]:
    if quantidade <= 0 or len(etapas) < quantidade:
        return []
    return sorted(etapas, key=lambda e: int(e.get("pontos", 0)))[:quantidade]


def construir_classificacao(dados: dict[str, Any], classe: str, tirar_2_piores: bool) -> pd.DataFrame:
    linhas: list[dict[str, Any]] = []
    equipas = obter_equipas(dados, classe)

    for equipa, etapas in equipas.items():
        pontos = [int(e.get("pontos", 0)) for e in etapas]
        removidas = piores_etapas(etapas, 2) if tirar_2_piores else []
        pontos_removidos = [int(e.get("pontos", 0)) for e in removidas]
        total_bruto = sum(pontos)
        total_final = total_bruto - sum(pontos_removidos)

        linhas.append({
            "Equipa": equipa,
            "Pontos": total_final,
            "Total bruto": total_bruto,
            "N.º etapas": len(etapas),
            "Etapas": ", ".join(str(p) for p in pontos) if pontos else "—",
            "Removidos": ", ".join(str(p) for p in pontos_removidos) if pontos_removidos else "—",
        })

    df = pd.DataFrame(linhas)
    if df.empty:
        return pd.DataFrame(columns=["Pos.", "Equipa", "Pontos", "Total bruto", "N.º etapas", "Etapas", "Removidos"])

    df = df.sort_values(["Pontos", "Total bruto", "Equipa"], ascending=[False, False, True]).reset_index(drop=True)
    df.insert(0, "Pos.", range(1, len(df) + 1))
    return df


def construir_detalhes(dados: dict[str, Any], classe: str, equipa: str) -> pd.DataFrame:
    etapas = obter_equipas(dados, classe).get(equipa, [])
    linhas = []
    for i, etapa in enumerate(etapas, start=1):
        linhas.append({
            "N.º": i,
            "Prova": etapa.get("prova", "—"),
            "Etapa": etapa.get("etapa", "—"),
            "Posição": etapa.get("posicao", "—"),
            "Pontos": etapa.get("pontos", 0),
        })
    return pd.DataFrame(linhas)


def admin_visivel() -> bool:
    """
    O painel de admin só aparece quando o link tiver ?admin=1.

    Exemplo:
    http://localhost:8501/?admin=1
    """
    try:
        return st.query_params.get("admin") == "1"
    except Exception:
        return False


def obter_password_admin() -> str:
    """
    Usa a password dos Secrets quando existir.
    Se não houver secrets.toml no computador, usa 'admin' por defeito.
    """
    try:
        return st.secrets.get("ADMIN_PASSWORD", "admin")
    except Exception:
        return "admin"


def password_admin_ok() -> bool:
    if not admin_visivel():
        return False

    password_configurada = obter_password_admin()

    with st.sidebar.expander("Admin", expanded=False):
        password = st.text_input("Palavra-passe", type="password")

        if password == password_configurada:
            st.session_state["admin_ok"] = True
            st.success("Modo admin ativo.")
        elif password:
            st.error("Palavra-passe errada.")

    return bool(st.session_state.get("admin_ok", False))


def secao_publica(dados: dict[str, Any]) -> None:
    st.subheader("Classificação")
    col1, col2 = st.columns([1, 1])
    with col1:
        classe = st.selectbox("Classe", NOMES_CLASSES, key="classe_publica")
    with col2:
        modo = st.radio("Modo", ["Geral", "Tirar 2 piores etapas"], horizontal=True)

    tirar_2 = modo == "Tirar 2 piores etapas"
    df = construir_classificacao(dados, classe, tirar_2)

    total_equipas = len(obter_equipas(dados, classe))
    lider = "—" if df.empty else f"{df.iloc[0]['Equipa']} ({df.iloc[0]['Pontos']} pts)"

    m1, m2, m3 = st.columns(3)
    m1.metric("Classe", classe)
    m2.metric("Equipas", total_equipas)
    m3.metric("Líder", lider)

    st.dataframe(df, hide_index=True, use_container_width=True)

    equipas = list(obter_equipas(dados, classe).keys())
    if equipas:
        with st.expander("Ver etapas detalhadas por equipa"):
            equipa = st.selectbox("Equipa", equipas)
            detalhes = construir_detalhes(dados, classe, equipa)
            st.dataframe(detalhes, hide_index=True, use_container_width=True)

    with st.expander("Pontuações por posição"):
        tabela = pd.DataFrame(
            [{"Posição": f"{pos}.º", "Pontos": pontos_etapa(pos)} for pos in range(1, 11)]
            + [{"Posição": "11.º ou pior", "Pontos": 1}]
        )
        st.dataframe(tabela, hide_index=True, use_container_width=True)


def secao_admin(dados: dict[str, Any]) -> None:
    st.divider()
    st.subheader("Painel de administração")

    tab_add, tab_apagar, tab_dados = st.tabs(["Adicionar resultado", "Apagar", "Dados"])

    with tab_add:
        with st.form("form_adicionar_resultado", clear_on_submit=True):
            classe = st.selectbox("Classe", NOMES_CLASSES, key="admin_classe_add")
            prova = st.selectbox("Prova", NOMES_PROVAS)
            equipa = st.text_input("Nome da equipa")
            c1, c2 = st.columns(2)
            with c1:
                pos1 = st.number_input("Posição etapa 1", min_value=1, step=1, value=1)
            with c2:
                pos2 = st.number_input("Posição etapa 2", min_value=1, step=1, value=1)
            st.caption(f"Pontos: etapa 1 = {pontos_etapa(pos1)}, etapa 2 = {pontos_etapa(pos2)}, total = {pontos_etapa(pos1) + pontos_etapa(pos2)}")
            submitted = st.form_submit_button("Adicionar resultado")

        if submitted:
            try:
                pts1, pts2 = adicionar_resultado(dados, classe, prova, equipa, int(pos1), int(pos2))
                st.success(f"Resultado adicionado: {normalizar_nome(equipa)} recebeu {pts1} + {pts2} pontos.")
                st.rerun()
            except ValueError as erro:
                st.error(str(erro))

    with tab_apagar:
        classe = st.selectbox("Classe", NOMES_CLASSES, key="admin_classe_apagar")
        equipas = list(obter_equipas(dados, classe).keys())
        if not equipas:
            st.info("Esta classe ainda não tem equipas.")
        else:
            equipa = st.selectbox("Equipa", equipas, key="admin_equipa_apagar")
            detalhes = construir_detalhes(dados, classe, equipa)
            st.dataframe(detalhes, hide_index=True, use_container_width=True)

            col1, col2, col3 = st.columns(3)
            with col1:
                if len(detalhes) > 0:
                    indice = st.number_input("N.º da etapa a apagar", min_value=1, max_value=len(detalhes), value=1, step=1)
                    if st.button("Apagar etapa selecionada"):
                        apagar_etapa(dados, classe, equipa, int(indice) - 1)
                        st.success("Etapa apagada.")
                        st.rerun()
            with col2:
                if st.button("Apagar equipa"):
                    apagar_equipa(dados, classe, equipa)
                    st.success("Equipa apagada.")
                    st.rerun()
            with col3:
                if st.button("Apagar classe inteira"):
                    apagar_classe(dados, classe)
                    st.success("Classe apagada.")
                    st.rerun()

    with tab_dados:
        st.caption("Exporta ou importa os resultados em JSON.")
        st.download_button(
            "Descarregar resultados",
            data=json.dumps(dados, ensure_ascii=False, indent=2).encode("utf-8"),
            file_name="resultados_cpt4x4.json",
            mime="application/json",
        )
        upload = st.file_uploader("Importar resultados JSON", type="json")
        if upload is not None:
            try:
                novos_dados = json.loads(upload.read().decode("utf-8"))
                guardar_dados(novos_dados)
                st.success("Resultados importados.")
                st.rerun()
            except Exception as erro:
                st.error(f"Não foi possível importar o ficheiro: {erro}")


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="🏁", layout="wide")
    st.title("🏁 CPT 4x4")
    st.caption("Classificações, provas e resultados por etapas")

    dados = carregar_dados()
    secao_publica(dados)

    if password_admin_ok():
        secao_admin(dados)

    st.caption("Regra: cada etapa conta como um resultado. No modo 'Tirar 2 piores etapas', são removidas as duas etapas com menor pontuação de cada equipa.")


if __name__ == "__main__":
    main()
