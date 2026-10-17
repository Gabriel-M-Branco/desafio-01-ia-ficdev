"""
Modulo de Geracao de Documentos Oficiais em PDF (RF09)
Produz a minuta de resposta formal em documento PDF timbrado do Governo do Estado de Mato Grosso.
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Union
import pymupdf

from src import BASE_DIR, resolver_caminho, caminho_relativo


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
        (45, 115),
        f"COMUNICADO OFICIAL DE ATENDIMENTO Nº {protocolo}/SECITECI/ETEC",
        fontsize=10,
        fontname="helv",
        color=(0/255, 74/255, 143/255),
    )
    page.insert_text(
        (420, 115),
        f"Cuiaba-MT, {data_registro}",
        fontsize=9,
        fontname="helv",
        color=(70/255, 80/255, 95/255),
    )

    # 5. Quadro Resumo do Requerente
    page.draw_rect(pymupdf.Rect(45, 128, 550, 175), color=(220/255, 225/255, 235/255), fill=(248/255, 250/255, 252/255))
    page.insert_text((55, 144), f"Interessado: {solicitante}", fontsize=9, fontname="helv", color=(15/255, 23/255, 42/255))
    page.insert_text((55, 158), f"Protocolo: {protocolo}  |  Canal: Atendimento Oficial  |  Categoria: {dados_extracao.get('categoria', 'Atendimento')}", fontsize=8, fontname="helv", color=(70/255, 80/255, 95/255))

    # 6. Corpo da Minuta
    # Limpa quebras escapadas caso existam
    texto_formatado = texto_minuta.replace("\\n", "\n").strip()
    rect_corpo = pymupdf.Rect(45, 190, 550, 680)
    page.insert_textbox(
        rect_corpo,
        texto_formatado,
        fontsize=9.5,
        fontname="helv",
        color=(15/255, 23/255, 42/255),
        align=pymupdf.TEXT_ALIGN_LEFT,
    )

    # 7. Espaco para Assinatura do Servidor Responsavel
    page.draw_line(pymupdf.Point(170, 755), pymupdf.Point(425, 755), color=(150/255, 150/255, 150/255), width=1)
    page.insert_text(
        (220, 768),
        "Servidor(a) Publico(a) Responsavel",
        fontsize=8.5,
        fontname="helv",
        color=(30/255, 41/255, 59/255),
    )
    page.insert_text(
        (185, 780),
        "Secretaria de Atendimento e Registros Escolares - SECITECI/MT",
        fontsize=7.5,
        fontname="helv",
        color=(100/255, 116/255, 139/255),
    )

    # 8. Rodape com Tarja de Validacao e Auditoria
    page.draw_rect(pymupdf.Rect(0, 810, 595, 842), color=None, fill=(15/255, 37/255, 64/255))
    page.insert_text(
        (45, 825),
        "DOCUMENTO OFICIAL - GOVERNO DO ESTADO DE MATO GROSSO",
        fontsize=8,
        fontname="helv",
        color=(255/255, 255/255, 255/255),
    )
    exec_txt = f"ID: {identificador_execucao}" if identificador_execucao else f"Emissao: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
    page.insert_text(
        (45, 836),
        f"Autenticidade e Protecao de Dados | {exec_txt}",
        fontsize=7,
        fontname="helv",
        color=(160/255, 196/255, 226/255),
    )

    doc.save(str(saida_path))
    doc.close()
    return caminho_relativo(saida_path)
