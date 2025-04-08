import streamlit as st
from xml.etree import ElementTree as ET
import tempfile
import os

def remover_links_google_earth(root):
    """Remove elementos <link> com referência ao Google Earth."""
    for parent in root.iter():
        for elem in list(parent):
            if elem.tag.endswith('link'):
                rel = elem.attrib.get("rel")
                href = elem.attrib.get("href", "")
                if rel == "app" and "google.com/earth" in href:
                    parent.remove(elem)

def organizar_placemarks_por_pasta(conteudo_kml, sigla, pon_inicial):
    """Organiza os placemarks por subpastas internas e ajusta nome e descrição."""
    try:
        tree = ET.ElementTree(ET.fromstring(conteudo_kml))
        root = tree.getroot()
        ns = {"kml": "http://www.opengis.net/kml/2.2"}
        ET.register_namespace('', ns["kml"])

        folders = root.findall(".//kml:Folder/kml:Folder", ns)
        sequencia_global = 1
        pasta_contador = 1
        rota_contador = 1
        subgrupo = pon_inicial  # Subgrupo começa com valor definido pelo usuário

        for i, folder in enumerate(folders):
            if i > 0 and i % 16 == 0:
                pasta_contador += 1

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
            subgrupo += 1

        # Remove os links do Google Earth
        remover_links_google_earth(root)

        # Salvar o novo conteúdo em memória
        with tempfile.NamedTemporaryFile(delete=False, suffix="_organizado.kml") as temp:
            tree.write(temp.name, encoding="utf-8", xml_declaration=True)
            with open(temp.name, "rb") as f:
                novo_conteudo = f.read()

        return novo_conteudo

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
        return None

# Interface Streamlit
st.title("Organizador de Placemarks KML")
st.markdown("Organize os placemarks por subpastas e defina o valor inicial do **SUBGRUPO (PON INICIAL)**.")

sigla = st.text_input("Digite a sigla para os Placemarks:", "").strip().upper()
pon_inicial = st.selectbox("Selecione a PON INICIAL (Subgrupo inicial):", options=[0, 1])

arquivo_kml = st.file_uploader("Envie o arquivo KML", type=["kml"])

if st.button("Organizar KML") and arquivo_kml and sigla:
    conteudo_kml = arquivo_kml.read()
    novo_arquivo = organizar_placemarks_por_pasta(conteudo_kml, sigla, pon_inicial)

    if novo_arquivo:
        st.success("Arquivo processado com sucesso!")
        st.download_button(
            label="Baixar KML Organizado",
            data=novo_arquivo,
            file_name=arquivo_kml.name.replace(".kml", "_organizado.kml"),
            mime="application/vnd.google-earth.kml+xml"
        )
else:
    if not arquivo_kml and st.button("Organizar KML"):
        st.warning("Por favor, envie um arquivo KML.")
    elif not sigla and st.button("Organizar KML"):
        st.warning("Por favor, insira a sigla para os placemarks.")
