import streamlit as st
from xml.etree import ElementTree as ET
import tempfile

def remover_links_google_earth(root):
    for parent in root.iter():
        for elem in list(parent):
            if elem.tag.endswith('link'):
                rel = elem.attrib.get("rel")
                href = elem.attrib.get("href", "")
                if rel == "app" and "google.com/earth" in href:
                    parent.remove(elem)

def organizar_placemarks_por_pasta(conteudo_kml, sigla, subgrupo_inicial, sequencia_inicial=1, pasta_contador_inicial=1):
    try:
        tree = ET.ElementTree(ET.fromstring(conteudo_kml))
        root = tree.getroot()
        ns = {"kml": "http://www.opengis.net/kml/2.2"}
        ET.register_namespace('', ns["kml"])

        folders = root.findall(".//kml:Folder/kml:Folder", ns)
        sequencia_global = sequencia_inicial
        rota_contador = 1

        # Define o subgrupo e seus limites
        limite_subgrupo = 16 if subgrupo_inicial == 1 else 15
        subgrupo = subgrupo_inicial
        subgrupo_base = subgrupo_inicial

        for i, folder in enumerate(folders):
            # pasta_contador avança como antes
            pasta_contador = pasta_contador_inicial + (i // 16)

            placemarks = folder.findall(".//kml:Placemark", ns)

            for contagem_local, placemark in enumerate(placemarks, start=1):
                novo_nome = f"ROTA-{rota_contador}_CTO-{contagem_local}"
                descricao_texto = f"{sigla}-{sequencia_global:04d} (1/{pasta_contador}/{subgrupo}) CTO-{contagem_local}"
                sequencia_global += 1

                nome = placemark.find("kml:name", ns)
                if nome is None:
                    nome = ET.SubElement(placemark, f"{{{ns['kml']}}}name")
                nome.text = novo_nome

                descricao = placemark.find("kml:description", ns)
                if descricao is None:
                    descricao = ET.SubElement(placemark, f"{{{ns['kml']}}}description")
                descricao.text = descricao_texto

            rota_contador += 1

            # lógica de rotação de subgrupo manual
            subgrupo += 1
            if subgrupo > subgrupo_base + limite_subgrupo - 1:
                subgrupo = subgrupo_base

        remover_links_google_earth(root)

        with tempfile.NamedTemporaryFile(delete=False, suffix="_organizado.kml") as temp:
            tree.write(temp.name, encoding="utf-8", xml_declaration=True)
            with open(temp.name, "rb") as f:
                novo_conteudo = f.read()

        return novo_conteudo

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
        return None

# Interface Streamlit
st.title("Organizador de Placemarks - KML")
st.markdown("Organize os placemarks por subpastas e defina o valor inicial do **SUBGRUPO (PON INICIAL)**.")

# Inputs
sigla = st.text_input("Digite a sigla para os Placemarks:", "").strip().upper()
pon_inicial = st.selectbox("Selecione a PON INICIAL (Subgrupo inicial):", options=[0, 1])
arquivo_kml = st.file_uploader("Envie o arquivo KML", type=["kml"])

# Configuração Manual com session_state
if "config_manual" not in st.session_state:
    st.session_state.config_manual = False

st.session_state.config_manual = st.checkbox("Configuração Manual", value=st.session_state.config_manual)

if st.session_state.config_manual:
    sequencia_global_manual = st.number_input("Valor inicial para SEQUÊNCIA GLOBAL:", min_value=1, value=1, step=1)
    pasta_contador_manual = st.number_input("Valor inicial para PASTA CONTADOR:", min_value=1, value=1, step=1)
    subgrupo_manual = st.number_input("Valor inicial para SUBGRUPO (PON):", min_value=0, value=pon_inicial, step=1)
else:
    sequencia_global_manual = 1
    pasta_contador_manual = 1
    subgrupo_manual = pon_inicial

# Botão de processamento
processar = st.button("Organizar KML")

if processar:
    if not arquivo_kml:
        st.warning("Por favor, envie um arquivo KML.")
    elif not sigla:
        st.warning("Por favor, insira a sigla para os placemarks.")
    else:
        conteudo_kml = arquivo_kml.read()
        novo_arquivo = organizar_placemarks_por_pasta(
            conteudo_kml,
            sigla,
            subgrupo_inicial=subgrupo_manual,
            sequencia_inicial=sequencia_global_manual,
            pasta_contador_inicial=pasta_contador_manual
        )

        if novo_arquivo:
            st.success("Arquivo processado com sucesso!")
            st.download_button(
                label="Baixar KML Organizado",
                data=novo_arquivo,
                file_name=arquivo_kml.name.replace(".kml", "_organizado.kml"),
                mime="application/vnd.google-earth.kml+xml"
            )
