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

def organizar_placemarks_por_pasta(conteudo_kml, sigla, pon_inicial, manual=False, seq_inicial=1, pasta_inicial=1, subgrupo_inicial=None):
    try:
        tree = ET.ElementTree(ET.fromstring(conteudo_kml))
        root = tree.getroot()
        ns = {"kml": "http://www.opengis.net/kml/2.2"}
        ET.register_namespace('', ns["kml"])

        folders = root.findall(".//kml:Folder/kml:Folder", ns)

        sequencia_global = seq_inicial if manual else 1
        pasta_contador = pasta_inicial if manual else 1
        subgrupo = subgrupo_inicial if manual else pon_inicial
        pon_base = pon_inicial
        rota_contador = 1

        for folder in folders:
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

            # Incrementar subgrupo e reiniciar conforme PON base
            subgrupo += 1
            if (pon_base == 0 and subgrupo > 15) or (pon_base == 1 and subgrupo > 16):
                subgrupo = pon_base
                pasta_contador += 1  # Incrementa pasta_contador ao reiniciar subgrupo

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

sigla = st.text_input("Digite a sigla para os Placemarks:", "").strip().upper()
pon_inicial = st.selectbox("Selecione a PON INICIAL (Subgrupo reinício):", options=[0, 1])

manual = st.checkbox("Configuração Manual")
if manual:
    st.markdown("### Configurações Avançadas")
    seq_inicial = st.number_input("Valor inicial para SEQUÊNCIA GLOBAL:", min_value=1, value=1)
    pasta_inicial = st.number_input("Valor inicial para PASTA CONTADOR:", min_value=1, value=1)
    max_subgrupo = 16 if pon_inicial == 1 else 15
    subgrupo_inicial = st.number_input(
        "Valor inicial para SUBGRUPO (PON):",
        min_value=0, max_value=max_subgrupo, value=pon_inicial
    )
else:
    seq_inicial = 1
    pasta_inicial = 1
    subgrupo_inicial = pon_inicial

arquivo_kml = st.file_uploader("Envie o arquivo KML", type=["kml"])
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
            pon_inicial,
            manual=manual,
            seq_inicial=seq_inicial,
            pasta_inicial=pasta_inicial,
            subgrupo_inicial=subgrupo_inicial
        )

        if novo_arquivo:
            st.success("Arquivo processado com sucesso!")
            st.download_button(
                label="📥 Baixar KML Organizado",
                data=novo_arquivo,
                file_name=arquivo_kml.name.replace(".kml", "_organizado.kml"),
                mime="application/vnd.google-earth.kml+xml"
            )
