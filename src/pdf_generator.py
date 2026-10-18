"""
Modulo de Geracao de Documentos Oficiais em PDF (RF09)
Produz a minuta de resposta formal em documento PDF timbrado do Governo do Estado de Mato Grosso.
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Union
import pymupdf

from src import BASE_DIR, resolver_caminho, caminho_relativo
import re


def normalizar_caracteres_pdf(texto: str) -> str:
    """
    Substitui travessões, aspas curvas e caracteres tipográficos do Unicode
    por seus equivalentes padrão, evitando pontos de interrogação '?' no PDF.
    Também garante o nome oficial correto do órgão.
    """
    if not isinstance(texto, str):
        return ""
    substituicoes = {
        "\u2014": " - ",  # em-dash (travessão que causava o ?)
        "\u2013": "-",    # en-dash (meia-risca)
        "\u2012": "-",
        "\u2015": " - ",
        "\u2018": "'",    # aspa curva esquerda
        "\u2019": "'",    # aspa curva direita
        "\u201c": '"',    # aspas duplas curvas
        "\u201d": '"',
        "\u2026": "...",  # reticências
        "\u2022": "-",    # marcador bullet
        "\u00a0": " ",    # espaço inquebrável
    }
    for k, v in substituicoes.items():
        texto = texto.replace(k, v)
    # Corrige alucinação de 'EDUCAÇÃO' para 'CIÊNCIA' em SECITECI
    texto = re.sub(
        r"SECRETARIA\s+DE\s+ESTADO\s+DE\s+EDUCA[CÇ][AÃ]O[,\s]+TECNOLOGIA\s+E\s+INOVA[CÇ][AÃ]O",
        "SECRETARIA DE ESTADO DE CIÊNCIA, TECNOLOGIA E INOVAÇÃO",
        texto,
        flags=re.IGNORECASE,
    )
    return texto


def limpar_repeticoes_cabecalho_rodape(texto: str) -> str:
    """
    Remove linhas que repetem desnecessariamente o cabeçalho timbrado do GOV.MT,
    o número de protocolo ou a assinatura institucional que já constam na moldura
    oficial do documento, deixando apenas o teor substancial da comunicação.
    """
    if not isinstance(texto, str):
        return ""
    linhas = texto.replace("\r\n", "\n").split("\n")
    linhas_filtradas = []
    ignorar_cabecalho = True

    padroes_cabecalho_repetido = [
        r"^governo\s+do\s+estado\s+de\s+mato\s+grosso",
        r"^secretaria\s+de\s+estado\s+de\s+(?:ci[eê]ncia|educa[cç][aã]o)",
        r"^escola\s+t[eé]cnica\s+estadual",
        r"^comunicado\s+oficial\s+de\s+atendimento",
        r"^protocolo:\s*[\d\w-]+\s*\|\s*data:",
        r"^data:\s*[\d/]+",
    ]

    padroes_rodape_repetido = [
        r"^coordena[cç][aã]o\s+de\s+atendimento",
        r"^escola\s+t[eé]cnica\s+estadual\s+de\s+cuiab[aá]",
        r"^seciteci\s*-\s*governo\s+de\s+mato\s+grosso",
        r"^secretaria\s+de\s+atendimento\s+e\s+registros",
        r"^servidor\(a\)\s+p[uú]blico\(a\)\s+respons[aá]vel",
    ]

    for linha in linhas:
        l_strip = linha.strip()
        l_lower = l_strip.lower()
        if ignorar_cabecalho:
            if not l_strip:
                continue
            if any(re.search(p, l_lower) for p in padroes_cabecalho_repetido):
                continue
            # Ao encontrar o início da mensagem (vocativo ou corpo)
            ignorar_cabecalho = False
            linhas_filtradas.append(linha)
        else:
            if any(re.search(p, l_lower) for p in padroes_rodape_repetido):
                continue
            linhas_filtradas.append(linha)

    resultado = "\n".join(linhas_filtradas).strip()
    return resultado if resultado else texto.strip()


def gerar_minuta_pdf(
    dados_extracao: Dict[str, Any],
    texto_minuta: str,
    caminho_saida_pdf: Union[str, Path],
    brasao_path: Optional[Union[str, Path]] = None,
    identificador_execucao: Optional[str] = None,
) -> str:
    """
    Gera um documento PDF oficial em formato A4 timbrado com brasao,
    identificacao do orgao, corpo da minuta e campo para assinatura formal.
    Todos os caminhos sao resolvidos dinamicamente de forma relativa a raiz do projeto.
    """
    saida_path = resolver_caminho(caminho_saida_pdf)
    saida_path.parent.mkdir(parents=True, exist_ok=True)

    caminho_brasao = resolver_caminho(brasao_path or "dados/originais/brasao.png")

    # Cria documento A4 (595.3 x 841.9 pontos)
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)

    # 1. Faixa Tricolor Superior Oficial (Azul, Verde, Amarelo)
    page.draw_rect(pymupdf.Rect(0, 0, 198, 6), color=None, fill=(0/255, 74/255, 143/255))
    page.draw_rect(pymupdf.Rect(198, 0, 396, 6), color=None, fill=(0/255, 139/255, 71/255))
    page.draw_rect(pymupdf.Rect(396, 0, 595, 6), color=None, fill=(247/255, 181/255, 0/255))

    # 2. Insercao do Brasao de Mato Grosso
    if caminho_brasao.exists():
        try:
            page.insert_image(pymupdf.Rect(45, 30, 95, 80), filename=str(caminho_brasao))
        except Exception:
            pass

    # 3. Cabecalho Textual Institucional
    page.insert_text(
        (108, 45),
        "GOVERNO DO ESTADO DE MATO GROSSO",
        fontsize=11,
        fontname="helv",
        color=(0/255, 74/255, 143/255),
    )
    page.insert_text(
        (108, 60),
        "SECRETARIA DE ESTADO DE CIENCIA, TECNOLOGIA E INOVACAO - SECITECI/MT",
        fontsize=9,
        fontname="helv",
        color=(30/255, 41/255, 59/255),
    )
    page.insert_text(
        (108, 73),
        "ESCOLA TECNICA ESTADUAL DE CUIABA - UNIDADE INTEGRADA",
        fontsize=8,
        fontname="helv",
        color=(100/255, 116/255, 139/255),
    )

    # Linha separadora institucional
    page.draw_line(pymupdf.Point(45, 92), pymupdf.Point(550, 92), color=(200/255, 205/255, 215/255), width=1)

    # 4. Dados de Identificacao do Ato e Protocolo
    protocolo = dados_extracao.get("protocolo", "2026-000142")
    solicitante = dados_extracao.get("solicitante", "Interessado")
    data_registro = dados_extracao.get("data", datetime.now().strftime("%d/%m/%Y"))

    page.insert_text(
        (45, 114),
        f"COMUNICADO OFICIAL DE ATENDIMENTO Nº {protocolo}/SECITECI/ETEC",
        fontsize=10,
        fontname="helv",
        color=(0/255, 74/255, 143/255),
    )
    page.insert_text(
        (420, 114),
        f"Cuiaba-MT, {data_registro}",
        fontsize=9,
        fontname="helv",
        color=(70/255, 80/255, 95/255),
    )

    # 5. Identificacao do Requerente e Categoria (sem caixa pesada, visual limpo)
    page.insert_text((45, 134), f"Interessado: {solicitante}", fontsize=9, fontname="helv", color=(15/255, 23/255, 42/255))
    page.insert_text((45, 148), f"Protocolo: {protocolo}  |  Canal: Atendimento Oficial  |  Categoria: {dados_extracao.get('categoria', 'Atendimento')}", fontsize=8, fontname="helv", color=(70/255, 80/255, 95/255))
    page.draw_line(pymupdf.Point(45, 160), pymupdf.Point(550, 160), color=(225/255, 230/255, 238/255), width=0.8)

    def desenhar_faixa_topo(pg):
        pg.draw_rect(pymupdf.Rect(0, 0, 198, 6), color=None, fill=(0/255, 74/255, 143/255))
        pg.draw_rect(pymupdf.Rect(198, 0, 396, 6), color=None, fill=(0/255, 139/255, 71/255))
        pg.draw_rect(pymupdf.Rect(396, 0, 595, 6), color=None, fill=(247/255, 181/255, 0/255))

    def desenhar_rodape(pg, pnum):
        pg.draw_rect(pymupdf.Rect(0, 810, 595, 842), color=None, fill=(15/255, 37/255, 64/255))
        pg.insert_text(
            (45, 825),
            "DOCUMENTO OFICIAL - GOVERNO DO ESTADO DE MATO GROSSO",
            fontsize=8,
            fontname="helv",
            color=(255/255, 255/255, 255/255),
        )
        exec_txt = f"ID: {identificador_execucao}" if identificador_execucao else f"Emissao: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        pg.insert_text(
            (45, 836),
            f"Autenticidade e Protecao de Dados | {exec_txt}  •  Pagina {pnum}",
            fontsize=7,
            fontname="helv",
            color=(160/255, 196/255, 226/255),
        )

    # 6. Corpo da Minuta com Fluxo Contínuo Dinâmico (Limpando cabeçalhos/rodapés repetidos)
    texto_limpo = limpar_repeticoes_cabecalho_rodape(texto_minuta)
    texto_formatado = normalizar_caracteres_pdf(texto_limpo.replace("\\n", "\n").strip())

    # Testa se cabe na primeira página inteira
    rect_corpo_p1 = pymupdf.Rect(45, 175, 550, 725)
    coube_direto = False
    for fsize in [9.5, 9.0, 8.5, 8.0]:
        rc = page.insert_textbox(rect_corpo_p1, texto_formatado, fontsize=fsize, fontname="helv", align=pymupdf.TEXT_ALIGN_LEFT)
        if rc >= 0:
            coube_direto = True
            break

    if not coube_direto:
        # Se excedeu o espaço de uma página só, recria com fluxo contínuo multipágina linha a linha
        doc.close()
        doc = pymupdf.open()
        page = doc.new_page(width=595, height=842)
        desenhar_faixa_topo(page)

        # Repete cabeçalho institucional na página 1
        if caminho_brasao.exists():
            try:
                page.insert_image(pymupdf.Rect(45, 30, 95, 80), filename=str(caminho_brasao))
            except Exception:
                pass
        page.insert_text((108, 45), "GOVERNO DO ESTADO DE MATO GROSSO", fontsize=11, fontname="helv", color=(0/255, 74/255, 143/255))
        page.insert_text((108, 60), "SECRETARIA DE ESTADO DE CIENCIA, TECNOLOGIA E INOVACAO - SECITECI/MT", fontsize=9, fontname="helv", color=(30/255, 41/255, 59/255))
        page.insert_text((108, 73), "ESCOLA TECNICA ESTADUAL DE CUIABA - UNIDADE INTEGRADA", fontsize=8, fontname="helv", color=(100/255, 116/255, 139/255))
        page.draw_line(pymupdf.Point(45, 92), pymupdf.Point(550, 92), color=(200/255, 205/255, 215/255), width=1)
        page.insert_text((45, 114), f"COMUNICADO OFICIAL DE ATENDIMENTO Nº {protocolo}/SECITECI/ETEC", fontsize=10, fontname="helv", color=(0/255, 74/255, 143/255))
        page.insert_text((420, 114), f"Cuiaba-MT, {data_registro}", fontsize=9, fontname="helv", color=(70/255, 80/255, 95/255))
        page.insert_text((45, 134), f"Interessado: {solicitante}", fontsize=9, fontname="helv", color=(15/255, 23/255, 42/255))
        page.insert_text((45, 148), f"Protocolo: {protocolo}  |  Canal: Atendimento Oficial  |  Categoria: {dados_extracao.get('categoria', 'Atendimento')}", fontsize=8, fontname="helv", color=(70/255, 80/255, 95/255))
        page.draw_line(pymupdf.Point(45, 160), pymupdf.Point(550, 160), color=(225/255, 230/255, 238/255), width=0.8)

        y = 175.0
        linhas = texto_formatado.split("\n")
        for linha in linhas:
            if not linha.strip():
                y += 6.0
                continue
            altura_estimada = 14.0
            if len(linha) > 95:
                altura_estimada = 26.0
            if len(linha) > 190:
                altura_estimada = 38.0
            
            # Se for estourar o limite da página, finaliza e cria nova página
            if y + altura_estimada > 720:
                desenhar_rodape(page, len(doc))
                page = doc.new_page(width=595, height=842)
                desenhar_faixa_topo(page)
                page.insert_text((45, 30), f"SECITECI/MT - ETEC Cuiaba  |  Comunicado Nº {protocolo} (Continuacao)", fontsize=8, fontname="helv", color=(100/255, 116/255, 139/255))
                page.draw_line(pymupdf.Point(45, 38), pymupdf.Point(550, 38), color=(200/255, 205/255, 215/255), width=0.5)
                y = 55.0

            r_lin = pymupdf.Rect(45, y, 550, y + altura_estimada + 10)
            rc_lin = page.insert_textbox(r_lin, linha, fontsize=8.5, fontname="helv")
            usado = (altura_estimada + 10) - rc_lin if rc_lin >= 0 else altura_estimada
            y += usado + 2.0

        # Espaço para assinatura
        if y + 65 > 790:
            desenhar_rodape(page, len(doc))
            page = doc.new_page(width=595, height=842)
            desenhar_faixa_topo(page)
            y = 60.0

        page.draw_line(pymupdf.Point(170, y + 25), pymupdf.Point(425, y + 25), color=(150/255, 150/255, 150/255), width=1)
        page.insert_text((220, y + 38), "Servidor(a) Publico(a) Responsavel", fontsize=8.5, fontname="helv", color=(30/255, 41/255, 59/255))
        page.insert_text((185, y + 49), "Secretaria de Atendimento e Registros Escolares - SECITECI/MT", fontsize=7.5, fontname="helv", color=(100/255, 116/255, 139/255))
        desenhar_rodape(page, len(doc))

    else:
        # Coube na página 1: desenha a assinatura e o rodapé da página única
        page.draw_line(pymupdf.Point(170, 755), pymupdf.Point(425, 755), color=(150/255, 150/255, 150/255), width=1)
        page.insert_text((220, 768), "Servidor(a) Publico(a) Responsavel", fontsize=8.5, fontname="helv", color=(30/255, 41/255, 59/255))
        page.insert_text((185, 780), "Secretaria de Atendimento e Registros Escolares - SECITECI/MT", fontsize=7.5, fontname="helv", color=(100/255, 116/255, 139/255))
        desenhar_rodape(page, 1)

    doc.save(str(saida_path))
    doc.close()
    return caminho_relativo(saida_path)
