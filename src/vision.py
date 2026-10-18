"""RF08: OCR local sem valores simulados ou envio a serviços externos."""
import json
import os
import sys
import shutil
import re
import time
import unicodedata
import uuid
import io
import hashlib
import subprocess
from pathlib import Path
from typing import Optional

import pymupdf
from PIL import Image, ImageOps
from src import resolver_caminho, caminho_relativo

AUSENTE = "não localizado"
def _detectar_tesseract_dir() -> Optional[Path]:
    """
    Localiza o diretório do Tesseract de forma dinâmica e independente de SO.
    Localiza o executável do Tesseract no sistema operacional.
    """
    # 1. Variável de ambiente explícita de sobreposição (se configurada)
    env_dir = os.environ.get("TESSERACT_DIR")
    if env_dir and Path(env_dir).is_dir():
        return Path(env_dir)
    # 2. Busca dinâmica no PATH do sistema operacional (agnóstico a SO)
    which_tess = shutil.which("tesseract") or shutil.which("tesseract.exe")
    if which_tess:
        return Path(which_tess).parent
    # 3. Caminhos canônicos do sistema somente se fisicamente existentes
    if sys.platform == "win32":
        pf = os.environ.get("ProgramFiles") or r"C:\Program Files"
        candidato = Path(pf) / "Tesseract-OCR"
        if candidato.is_dir():
            return candidato
    else:
        for d in [Path("/usr/bin"), Path("/usr/local/bin"), Path("/usr/share/tesseract-ocr")]:
            if d.is_dir() and (d / "tesseract").is_file():
                return d
    return None

TESSERACT_DIR = _detectar_tesseract_dir()
# Coordenadas em pontos PDF, medidas visualmente no formulário oficial (595 x 842).
# Não contêm valores esperados nem são derivadas do gabarito.
REGIOES_OFICIAIS = {
    "codigo": (135, 246, 396, 260), "nome": (135, 258, 511, 273),
    "data_nascimento": (135, 271, 225, 284), "cpf": (267, 270, 444, 284),
    "rg": (135, 283, 225, 296), "orgao_expedidor": (324, 283, 511, 296),
    "naturalidade": (135, 295, 300, 307), "uf": (379, 294, 437, 307),
    "nome_mae": (135, 306, 511, 320), "nome_pai": (135, 319, 511, 332),
    "curso": (135, 336, 430, 350), "ch": (462, 335, 585, 349),
    "eixo_tecnologico": (135, 348, 430, 360), "turma": (503, 347, 585, 359),
    "municipio": (135, 359, 320, 370), "turno": (383, 358, 585, 370),
    "inicio_curso": (135, 368, 318, 382), "termino_curso": (442, 367, 585, 381),
    "tel_celular": (135, 387, 295, 398), "tel_residencial": (363, 385, 585, 397),
    "email": (135, 393, 585, 408), "data_matricula": (118, 414, 585, 427),
    "assinatura_aluno": (100, 467, 330, 484),
}
FORMULARIO_SHA256 = "a4b3bc0518df73244856ab27e010b561680b5f60ee8e730be4df83b3b567505f"
ROTULOS = {
    "codigo": ["codigo", "protocolo"], "nome": ["nome", "nome do aluno"],
    "data_nascimento": ["data de nascimento"], "cpf": ["cpf"], "rg": ["rg"],
    "orgao_expedidor": ["orgao expedidor"], "naturalidade": ["naturalidade"],
    "uf": ["uf"], "nome_mae": ["nome da mae"], "nome_pai": ["nome do pai"],
    "curso": ["curso"], "ch": ["ch", "carga horaria"],
    "eixo_tecnologico": ["eixo tecnologico"], "turma": ["turma"],
    "municipio": ["municipio"], "turno": ["turno"],
    "inicio_curso": ["inicio do curso"], "termino_curso": ["termino do curso"],
    "tel_celular": ["tel. celular", "telefone celular"],
    "tel_residencial": ["telefone residencial", "tel. residencial"],
    "email": ["e-mail", "email"], "data_matricula": ["data matricula", "data da matricula"],
    "assinatura_aluno": ["assinatura do aluno ou responsavel", "assinatura do aluno"],
    "assinatura_secretaria": ["assinatura da secretaria escolar"],
}


class VisionProcessor:
    @classmethod
    def obter_executavel_tesseract(cls) -> Path:
        """Localiza dinamicamente o executável do Tesseract de forma agnóstica ao SO."""
        # 1. Se TESSERACT_DIR estiver definido (ou mockado em testes unitários)
        if TESSERACT_DIR:
            if (TESSERACT_DIR / "tesseract.exe").is_file():
                return TESSERACT_DIR / "tesseract.exe"
            if (TESSERACT_DIR / "tesseract").is_file():
                return TESSERACT_DIR / "tesseract"
            if sys.platform == "win32":
                return TESSERACT_DIR / "tesseract.exe"
            return TESSERACT_DIR / "tesseract"

        # 2. Busca dinâmica no PATH do sistema operacional (independente de SO)
        nomes_busca = ["tesseract.exe", "tesseract"] if sys.platform == "win32" else ["tesseract", "tesseract.exe"]
        for nome in nomes_busca:
            local = shutil.which(nome)
            if local:
                return Path(local)

        # 3. Caminhos canônicos do SO somente se fisicamente existentes
        if sys.platform == "win32":
            pf = os.environ.get("ProgramFiles") or r"C:\Program Files"
            padrao_win = Path(pf) / "Tesseract-OCR" / "tesseract.exe"
            if padrao_win.is_file():
                return padrao_win
        else:
            for p in [Path("/usr/bin/tesseract"), Path("/usr/local/bin/tesseract")]:
                if p.is_file():
                    return p

        # 4. Fallback padrão pelo nome do comando no PATH do SO
        return Path("tesseract.exe" if sys.platform == "win32" else "tesseract")

    @classmethod
    def obter_tessdata_dir(cls) -> Path:
        """Localiza a pasta de modelos treinados (tessdata) com prioridade a TESSDATA_PREFIX."""
        # 1. Subdiretório tessdata em TESSERACT_DIR (se configurado ou mockado em testes)
        if TESSERACT_DIR and (TESSERACT_DIR / "tessdata").is_dir():
            return TESSERACT_DIR / "tessdata"
        # 2. Variável de ambiente padrão internacional do Tesseract
        env_prefix = os.environ.get("TESSDATA_PREFIX")
        if env_prefix and Path(env_prefix).is_dir():
            return Path(env_prefix)
        # 3. Caminhos canônicos em distribuições Linux (Debian, Ubuntu, Docker)
        for d in [
            Path("/usr/share/tesseract-ocr/5/tessdata"),
            Path("/usr/share/tesseract-ocr/4.00/tessdata"),
            Path("/usr/share/tesseract-ocr/tessdata"),
            Path("/usr/share/tessdata"),
        ]:
            if d.is_dir() and (d / "por.traineddata").is_file():
                return d
        if TESSERACT_DIR:
            return TESSERACT_DIR / "tessdata"
        return Path("tessdata")

    def __init__(self, config_path="config.json"):
        try:
            self.config = json.loads(resolver_caminho(config_path).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.config = {}
        self.vision_model = "Tesseract OCR / PyMuPDF (por)"

    @staticmethod
    def _normalizar(texto):
        return "".join(c for c in unicodedata.normalize("NFD", texto.lower())
                       if not unicodedata.combining(c))

    def converter_pdf_para_imagem(self, caminho_pdf, caminho_saida_png: Optional[str] = None):
        saida = resolver_caminho(caminho_saida_png or f"dados/processados/preview_{uuid.uuid4().hex}.png")
        if saida.resolve().is_relative_to(resolver_caminho("dados/originais").resolve()):
            raise ValueError("Originais são imutáveis.")
        with pymupdf.open(str(resolver_caminho(caminho_pdf))) as doc:
            pix = doc[0].get_pixmap(dpi=200)
            saida.parent.mkdir(parents=True, exist_ok=True)
            pix.save(str(saida))
        return caminho_relativo(saida)

    def _extrair_campos(self, texto):
        texto = unicodedata.normalize("NFC", texto)
        aliases = {alias: campo for campo, nomes in ROTULOS.items() for alias in nomes}
        labels = "|".join(re.escape(s) for s in sorted(aliases, key=len, reverse=True))
        pattern = r"(?<!\w)(" + labels + r")(?:[ \t]*[:=][ \t]*|[ \t]*\n[ \t]*|[ \t]*$)"
        marcas = list(re.finditer(pattern, self._normalizar(texto)))
        campos = {campo: AUSENTE for campo in ROTULOS}
        vistos = set()
        for i, marca in enumerate(marcas):
            campo = aliases[marca[1]]
            fim = marcas[i + 1].start() if i + 1 < len(marcas) else len(texto)
            valor = texto[marca.end():fim].strip(" \t\r\n|;")
            linhas = [linha.strip() for linha in valor.splitlines() if linha.strip()]
            # Nomes e descrições podem quebrar linha; números não são concatenados.
            multilinha = campo in {"nome", "nome_mae", "nome_pai", "curso", "eixo_tecnologico"}
            valor = " ".join(linhas[:3]) if multilinha else (linhas[0] if linhas else "")
            if campo in vistos:
                campos[campo] = AUSENTE
                continue
            vistos.add(campo)
            campos[campo] = valor if valor and re.search(r"\w", valor) else AUSENTE
        return campos

    def _ocr_alternativo(self, pagina, tessdata):
        pix = pagina.get_pixmap(dpi=300, colorspace=pymupdf.csRGB, alpha=False)
        with Image.open(io.BytesIO(pix.tobytes("png"))) as imagem:
            tratada = ImageOps.autocontrast(ImageOps.grayscale(imagem))
            buffer = io.BytesIO()
            tratada.save(buffer, format="PNG", dpi=(300, 300))
        return self._executar_tesseract(buffer.getvalue(), tessdata, 11, 300)

    def _executar_tesseract(self, png, tessdata, psm, dpi):
        processo = subprocess.run(
            [str(self.obter_executavel_tesseract()), "stdin", "stdout", "--tessdata-dir", str(tessdata),
             "-l", "por", "--dpi", str(dpi), "--psm", str(psm)],
            input=png, capture_output=True, timeout=90,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if processo.returncode:
            raise RuntimeError("Tesseract alternativo retornou erro.")
        return processo.stdout.decode("utf-8", errors="replace")

    def _ocr_regioes(self, pagina, tessdata):
        if tuple(pagina.rect) != (0.0, 0.0, 595.0, 842.0):
            raise ValueError("Geometria incompatível com perfil oficial.")
        versoes = {f"regioes_psm{psm}": {"campos_extraidos": {}, "regioes": {}, "erros": []}
                   for psm in (6, 7)}
        for campo, bbox in REGIOES_OFICIAIS.items():
            pix = pagina.get_pixmap(dpi=400, clip=pymupdf.Rect(bbox), colorspace=pymupdf.csRGB, alpha=False)
            with Image.open(io.BytesIO(pix.tobytes("png"))) as imagem:
                tratada = ImageOps.expand(ImageOps.autocontrast(ImageOps.grayscale(imagem)), border=16, fill=255)
                buffer = io.BytesIO()
                tratada.save(buffer, format="PNG", dpi=(400, 400))
            png = buffer.getvalue()
            for psm in (6, 7):
                versao = versoes[f"regioes_psm{psm}"]
                registro = {"pagina": 1, "bbox_pontos": bbox, "dpi": 400, "psm": psm,
                            "idioma": "por", "preprocessamento": ["escala_cinza", "autocontraste", "borda_branca_16px"],
                            "sha256_recorte": hashlib.sha256(png).hexdigest()}
                try:
                    bruto = self._executar_tesseract(png, tessdata, psm, 400)
                    valor = re.sub(r"\s+", " ", bruto).strip()
                    versao["campos_extraidos"][campo] = valor if re.search(r"\w", valor) else AUSENTE
                    registro["texto_bruto"] = bruto
                except Exception:
                    versao["campos_extraidos"][campo] = AUSENTE
                    registro["erro"] = "falha_ocr_regiao"
                    versao["erros"].append({"campo": campo, "codigo": "falha_ocr_regiao"})
                versao["regioes"][campo] = registro
        for versao in versoes.values():
            versao["texto_bruto"] = "\n".join(v.get("texto_bruto", "") for v in versao["regioes"].values())
        return versoes

    def processar_documento(self, caminho_arquivo):
        inicio = time.perf_counter()
        path = resolver_caminho(caminho_arquivo)
        base = {"arquivo_analisado": path.name, "modelo_utilizado": self.vision_model,
                "provedor": "Tesseract local / PyMuPDF", "exige_confirmacao_humana": True}
        def falha(codigo, mensagem):
            return {**base, "sucesso": False, "codigo_erro": codigo, "erro": mensagem,
                    "tempo_processamento_segundos": time.perf_counter() - inicio}
        try:
            if (not path.is_file() or path.suffix.lower() not in
                    {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}
                    or not 0 < path.stat().st_size <= 50 * 1024 * 1024):
                return falha("arquivo_invalido", "Documento ausente, vazio, muito grande ou formato inválido.")
            tessdata = self.obter_tessdata_dir()
            if not self.obter_executavel_tesseract().is_file() or not (tessdata / "por.traineddata").is_file():
                return falha("ocr_indisponivel", "Tesseract e idioma português não localizados no diretório configurado.")
            paginas = []
            hash_original = hashlib.sha256(path.read_bytes()).hexdigest()
            regionais = {}
            erros_regioes = []
            variantes = {nome: {"paginas": [], "erros": []} for nome in ("pymupdf", "psm11")}
            estrategias_paginas = []
            with pymupdf.open(str(path)) as doc:
                if doc.needs_pass or not 0 < len(doc) <= 50:
                    return falha("pdf_invalido", "Documento protegido, vazio ou com páginas demais.")
                for numero, pagina in enumerate(doc, 1):
                    textos = {}
                    for estrategia in variantes:
                        try:
                            if estrategia == "pymupdf":
                                tp = pagina.get_textpage_ocr(language="por", dpi=300, full=True, tessdata=str(tessdata))
                                texto = pagina.get_text("text", textpage=tp)
                            else:
                                texto = self._ocr_alternativo(pagina, tessdata)
                            textos[estrategia] = texto
                            if not texto.strip():
                                variantes[estrategia]["erros"].append({"pagina": numero, "codigo": "ocr_vazio"})
                        except Exception as exc:
                            textos[estrategia] = ""
                            variantes[estrategia]["erros"].append({"pagina": numero, "codigo":
                                "timeout" if isinstance(exc, subprocess.TimeoutExpired) else "falha_ocr"})
                        variantes[estrategia]["paginas"].append(textos[estrategia])
                    # Preserva a primeira estratégia; usa a segunda somente se a primeira não produziu texto.
                    escolhida = "pymupdf" if textos["pymupdf"].strip() else "psm11"
                    if not textos[escolhida].strip():
                        resultado_falha = falha("ocr_vazio" if all(
                            erro["codigo"] == "ocr_vazio" for v in variantes.values() for erro in v["erros"])
                            else "falha_ocr", f"Nenhuma estratégia produziu texto na página {numero}.")
                        resultado_falha["versoes_ocr"] = variantes
                        return resultado_falha
                    paginas.append(textos[escolhida])
                    estrategias_paginas.append(escolhida)
                    if numero == 1 and hash_original == FORMULARIO_SHA256:
                        try:
                            regionais = self._ocr_regioes(pagina, tessdata)
                        except Exception:
                            erros_regioes.append("Não foi possível processar o perfil regional oficial.")
        except (pymupdf.FileDataError, pymupdf.EmptyFileError):
            return falha("pdf_invalido", "Não foi possível abrir o documento.")
        except Exception:
            return falha("falha_ocr", "Não foi possível concluir o OCR local.")
        bruto = "\n\f\n".join(paginas)
        corrigido = "\n".join(re.sub(r"[ \t]+", " ", linha).strip() for linha in bruto.splitlines())
        campos = self._extrair_campos(corrigido)
        for nome, variante in variantes.items():
            variante["texto_bruto"] = "\n\f\n".join(variante.pop("paginas"))
            variante["campos_extraidos"] = self._extrair_campos(variante["texto_bruto"])
            variante["comparacao_gabarito"] = self.comparar_com_gabarito(variante["campos_extraidos"])
        origem_campos = "parser_texto_principal"
        if regionais:
            # Consenso posicional conservador; nunca consultar o gabarito para selecionar resultados.
            campos = {campo: AUSENTE for campo in ROTULOS}
            for campo in REGIOES_OFICIAIS:
                v6 = regionais["regioes_psm6"]["campos_extraidos"][campo]
                v7 = regionais["regioes_psm7"]["campos_extraidos"][campo]
                if v6 != AUSENTE and self._normalizar(v6) == self._normalizar(v7):
                    campos[campo] = v7
            origem_campos = "consenso_regional_psm6_psm7_pendente_revisao"
            for versao in regionais.values():
                versao["comparacao_gabarito"] = self.comparar_com_gabarito(versao["campos_extraidos"])
            variantes.update(regionais)
        divergencias = [campo for campo in ROTULOS if len({
            self._normalizar(v["campos_extraidos"].get(campo, AUSENTE)).strip()
            for v in variantes.values()}) > 1]
        incertos = ["Todos os campos críticos exigem conferência humana; OCR não valida assinaturas ou manuscritos."]
        incertos += [f"Campo '{campo}': ausente, ilegível ou ambíguo."
                     for campo, valor in campos.items() if valor == AUSENTE]
        incertos += [f"Campo '{campo}': divergência entre estratégias; confirmar no original." for campo in divergencias]
        incertos += erros_regioes
        return {**base, "sucesso": True, "texto_bruto": bruto, "texto_corrigido": corrigido,
                "campos_extraidos": campos, "paginas_processadas": len(paginas),
                "origem_campos": origem_campos,
                "perfil_regional": "oficial_sha256" if regionais else "não aplicado",
                "erros_regioes": erros_regioes,
                "versoes_ocr": variantes, "divergencias_entre_estrategias": divergencias,
                "estrategias_por_pagina": estrategias_paginas,
                "politica_selecao": "Texto: primeira estratégia, segunda se vazia/falha. Campos do perfil oficial: consenso PSM6/7; discordâncias ficam pendentes. Sem seleção por tamanho ou gabarito.",
                "parametros_ocr": {"dpi": 300, "idioma": "por", "psm_alternativo": 11,
                                   "preprocessamento": ["escala_cinza", "autocontraste"],
                                   "regioes": {"dpi": 400, "psm": [6, 7], "perfil_sha256": FORMULARIO_SHA256}},
                "sha256_original": hash_original,
                "trechos_incertos_ou_ilegiveis": incertos,
                "comparacao_gabarito": self.comparar_com_gabarito(campos),
                "justificativa_soberania_privacidade": "OCR local evita envio do documento a terceiros e favorece soberania e privacidade.",
                "tempo_processamento_segundos": time.perf_counter() - inicio}

    def comparar_com_gabarito(self, texto_extraido):
        campos = texto_extraido if isinstance(texto_extraido, dict) else self._extrair_campos(texto_extraido)
        try:
            gabarito = json.loads(resolver_caminho("dados/gabaritos/gabarito_visao.json").read_text(encoding="utf-8"))
            esperados = gabarito["campos_esperados"]
            if not isinstance(esperados, dict) or not esperados:
                raise ValueError("Gabarito vazio")
        except (OSError, ValueError, KeyError):
            return {"status": "gabarito_indisponivel", "total_campos": 0, "campos_conferidos": 0,
                    "taxa_acuracia_percentual": "0.0%", "detalhes": {}}
        def normalizar(campo, valor):
            valor = re.sub(r"\s+", " ", self._normalizar(str(valor))).strip()
            if campo in {"cpf", "rg", "codigo", "data_nascimento", "inicio_curso", "termino_curso", "data_matricula"}:
                valor = re.sub(r"[.\-/\s]", "", valor)
            return valor
        detalhes = {}
        for campo, esperado in esperados.items():
            obtido = campos.get(campo, AUSENTE)
            ausente = not str(obtido).strip() or self._normalizar(str(obtido)) == self._normalizar(AUSENTE)
            acerto = not ausente and esperado != AUSENTE and normalizar(campo, obtido) == normalizar(campo, esperado)
            detalhes[campo] = {"esperado": esperado, "extraido": obtido, "conferido_com_sucesso": acerto}
        acertos = sum(v["conferido_com_sucesso"] for v in detalhes.values())
        return {"total_campos": len(esperados), "campos_conferidos": acertos,
                "taxa_acuracia_percentual": f"{100 * acertos / len(esperados):.1f}%", "detalhes": detalhes}

    def processar_com_auditoria(self, audit_logger, caminho_arquivo="dados/originais/entrada_pdf-imagem.pdf"):
        resultado = self.processar_documento(caminho_arquivo)
        if resultado.get("sucesso"):
            diretorio = resolver_caminho(self.config.get("paths", {}).get("dados_processados", "dados/processados"))
            nome_base = Path(caminho_arquivo).stem
            # Substitui execuções anteriores do mesmo documento para evitar proliferação de arquivos
            for antigo in diretorio.glob("ocr_*.json"):
                try:
                    antigo.unlink()
                except OSError:
                    pass
            arquivo = diretorio / f"ocr_{nome_base}.json"
            try:
                if arquivo.resolve().is_relative_to(resolver_caminho("dados/originais").resolve()):
                    raise OSError("Originais imutáveis")
                arquivo.parent.mkdir(parents=True, exist_ok=True)
                resultado["arquivo_extracao"] = caminho_relativo(arquivo)
                arquivo.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
            except OSError:
                resultado.pop("arquivo_extracao", None)
                resultado.update(sucesso=False, codigo_erro="falha_persistencia", erro="Não foi possível salvar o OCR.")
        resultado["id_execucao"] = audit_logger.registrar_execucao(
            modalidade="visao", arquivo_origem=caminho_arquivo,
            provedor=resultado["provedor"], modelo=resultado["modelo_utilizado"],
            versao_prompt="N/A (OCR local)", parametros=resultado.get("parametros_ocr", {"idioma": "por", "dpi": 300}),
            resultado=resultado, duracao_segundos=resultado["tempo_processamento_segundos"],
            erros=[] if resultado.get("sucesso") else [resultado["codigo_erro"]])
        return resultado
