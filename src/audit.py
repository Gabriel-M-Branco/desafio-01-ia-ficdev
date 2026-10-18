"""
Módulo de Auditoria, Rastreabilidade, LGPD e Avaliação de Qualidade (RF11, RF12, RF13)
"""

import json
import uuid
import hashlib
import re
import unicodedata
import os
from datetime import datetime as _datetime
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

from src import resolver_caminho, caminho_relativo


class AuditLogger:
    """
    Registrador de auditoria estruturada e rastreabilidade completa (RF11).
    Registra vínculos e hashes e sanitiza segredos conhecidos. Não autentica pessoas
    nem garante anonimização integral ou inviolabilidade dos arquivos locais.
    """

    def __init__(self, log_dir: str = "resultados/logs"):
        self.log_dir = resolver_caminho(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.trail_file = self.log_dir / "audit_trail.jsonl"

    @staticmethod
    def sanitizar(valor):
        """Remove segredos em profundidade, preservando métricas de tokens."""
        metricas = {"max_tokens", "total_tokens", "prompt_tokens", "completion_tokens"}
        if isinstance(valor, dict):
            return {k: ("[REDACTED]" if str(k).lower() not in metricas and
                re.search(r"(^|_)(api_key|key|chave|token|secret|secreta|password|pwd|authorization|auth)($|_)", str(k), re.I)
                else AuditLogger.sanitizar(v)) for k, v in valor.items()}
        if isinstance(valor, (list, tuple)):
            return [AuditLogger.sanitizar(v) for v in valor]
        if isinstance(valor, str):
            for nome, segredo in os.environ.items():
                if len(segredo) > 4 and any(t in nome.upper() for t in ("TOKEN", "KEY", "PASSWORD", "SECRET")):
                    valor = valor.replace(segredo, "[REDACTED]")
            return re.sub(r"Bearer\s+\S+|(?:sk-or-v1-|hf_)[A-Za-z0-9_-]+", "[REDACTED]", valor, flags=re.I)
        return valor

    def registrar_execucao(
        self,
        modalidade: str,
        arquivo_origem: str,
        provedor: str,
        modelo: str,
        versao_prompt: str,
        parametros: Dict[str, Any],
        resultado: Dict[str, Any],
        duracao_segundos: float,
        decisao_humana: Optional[Dict[str, Any]] = None,
        erros: Optional[List[str]] = None,
    ) -> str:
        """
        Salva um evento no log de auditoria sem expor senhas/chaves de API (RF11).
        """
        exec_id = f"EXEC_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

        # Sanitiza parâmetros removendo possíveis chaves de API
        params_limpos = self.sanitizar(parametros or {})
        resultado = self.sanitizar(resultado)

        registro = {
            "id_execucao": exec_id,
            "timestamp": datetime.now().isoformat(),
            "modalidade": modalidade,  # texto, audio, visao, imagem
            "arquivo_origem": caminho_relativo(arquivo_origem),
            "provedor": provedor,
            "modelo": modelo,
            "versao_prompt": versao_prompt,
            "parametros": params_limpos,
            "duracao_segundos": duracao_segundos,
            "erros": erros or [],
            "resultado_resumo": {
                "sucesso": (resultado.get("sucesso", True) is not False) and not erros,
                "campos_extraidos": len(resultado.get("extracao", {})) if isinstance(resultado, dict) else 0,
            },
            "decisao_humana": decisao_humana or {
                "status": "pendente_revisao",
                "operador": "aguardando_validacao",
                "justificativa": "Aguardando deliberação de servidor responsável no painel web.",
            },
        }

        registro = self.sanitizar(registro)
        # Grava no log cumulativo JSON Lines
        with open(self.trail_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(registro, ensure_ascii=False) + "\n")

        # Grava arquivo individual detalhado para o caso
        individual_file = self.log_dir / f"{exec_id}.json"
        with open(individual_file, "w", encoding="utf-8") as f:
            json.dump({**registro, "detalhes_completos": resultado}, f, ensure_ascii=False, indent=2)

        return exec_id

    @staticmethod
    def hash_texto(texto: str) -> str:
        return hashlib.sha256(texto.encode("utf-8")).hexdigest()

    def obter_aprovacao_texto(self, exec_id: str, texto: str, modalidade_esperada="texto"):
        """Lê a aprovação persistida; não aceita flags enviadas pelo cliente."""
        if not exec_id or not re.fullmatch(r"[A-Za-z0-9_-]+", exec_id):
            return None
        try:
            dado = json.loads((self.log_dir / f"{exec_id}.json").read_text(encoding="utf-8"))
            decisao = dado.get("decisao_humana", {})
            if (dado.get("modalidade") == modalidade_esperada
                    and decisao.get("status") == "APROVADO" and decisao.get("id_aprovacao")
                    and dado.get("texto_final") == texto
                    and decisao.get("hash_texto_aprovado") == self.hash_texto(texto)):
                return decisao
        except (OSError, ValueError, AttributeError, TypeError):
            pass
        return None

    def atualizar_decisao_humana(self, exec_id: str, decisao: str, justificativa: str, operador: str = "Servidor Público", texto_final: Optional[str] = None) -> bool:
        """
        Atualiza o status de Human-in-the-Loop de uma execução (RF13).
        decisao: 'APROVADO', 'REJEITADO', 'CORRIGIDO'
        """
        if (not re.fullmatch(r"[A-Za-z0-9_-]+", exec_id) or decisao not in {"APROVADO", "CORRIGIDO", "REJEITADO"}
                or not justificativa.strip() or not operador.strip()
                or (decisao == "APROVADO" and (not isinstance(texto_final, str) or not texto_final.strip()))):
            return False
        if texto_final is not None and self.sanitizar(texto_final) != texto_final:
            return False  # Não persistir um segredo como texto institucional aprovado.
        operador, justificativa = self.sanitizar(operador), self.sanitizar(justificativa)
        individual_file = self.log_dir / f"{exec_id}.json"
        if not individual_file.exists():
            return False

        with open(individual_file, "r", encoding="utf-8") as f:
            dado = json.load(f)

        dado.setdefault("historico_decisoes", []).append(dado.get("decisao_humana", {}).copy())
        dado["decisao_humana"] = {
            "status": decisao,
            "operador": operador,
            "justificativa": justificativa,
            "data_decisao": datetime.now().isoformat(),
        }
        if texto_final is not None:
            dado["texto_final"] = texto_final
        if decisao == "APROVADO":
            dado["decisao_humana"].update(
                id_aprovacao=uuid.uuid4().hex, hash_texto_aprovado=self.hash_texto(texto_final))

        with open(individual_file, "w", encoding="utf-8") as f:
            json.dump(dado, f, ensure_ascii=False, indent=2)

        return True

    def listar_execucoes(self) -> List[Dict[str, Any]]:
        """Lê todas as execuções registradas no arquivo de trilha."""
        if not self.trail_file.exists():
            return []
        execucoes = []
        with open(self.trail_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        execucoes.append(json.loads(line))
                    except Exception:
                        pass
        return execucoes

    def resumo_revisoes(self):
        """Decisões atuais dos casos, excluindo TTS e eventos auxiliares do denominador."""
        contagens = {k: 0 for k in ("APROVADO", "CORRIGIDO", "REJEITADO", "pendente_revisao")}
        for evento in self.listar_execucoes():
            if evento.get("modalidade") not in {"texto", "audio", "visao", "imagem"}:
                continue
            try:
                dado = json.loads((self.log_dir / (evento["id_execucao"] + ".json")).read_text(encoding="utf-8"))
                status = dado.get("decisao_humana", {}).get("status", "pendente_revisao")
            except (OSError, ValueError):
                status = "pendente_revisao"
            contagens[status if status in contagens else "pendente_revisao"] += 1
        decididos = sum(contagens[k] for k in ("APROVADO", "CORRIGIDO", "REJEITADO"))
        return {"contagens": contagens, "casos_decididos": decididos,
                "taxa_aprovacao_percentual": round(100 * contagens["APROVADO"] / decididos, 1) if decididos else None,
                "criterio": "Aprovados / (aprovados + corrigidos + rejeitados); pendentes e TTS excluídos. Revisões RF10 isoladas não entram nesta trilha."}


class LGPDManager:
    """
    Gestão de Conformidade com a Lei Geral de Proteção de Dados (RF12).
    Classificação, finalidade, análise de riscos e minimização de dados enviados a provedores.
    """

    TABELA_CAMPOS_LGPD = {
        "solicitante": {
            "natureza": "Dado Pessoal",
            "finalidade": "Identificação do requerente no processo escolar de matrícula.",
            "necessidade": "Essencial para emissão de certidões e histórico acadêmico.",
            "risco": "Médio (identificação individual direta).",
            "minimizar_no_prompt": False,
        },
        "cpf": {
            "natureza": "Dado pessoal de identificação; risco operacional alto",
            "finalidade": "Unicidade cadastral junto ao MEC e órgãos estaduais de educação.",
            "necessidade": "Identificador presente no caso fictício; não comprova obrigação legal de coleta. Preferir conferência local.",
            "risco": "Alto (risco de fraude em caso de vazamento externo).",
            "minimizar_no_prompt": True,
        },
        "rg": {
            "natureza": "Dado Pessoal",
            "finalidade": "Validação de documento físico na secretaria da escola.",
            "necessidade": "Complementar à verificação do CPF.",
            "risco": "Médio.",
            "minimizar_no_prompt": True,
        },
        "data_nascimento": {
            "natureza": "Dado Pessoal (Menor de Idade se < 18 anos)",
            "finalidade": "Verificação de idade mínima legal e necessidade de assistência parental.",
            "necessidade": "Essencial para cumprimento das diretrizes educacionais.",
            "risco": "Alto (Artigo 14 da LGPD - Proteção especial a crianças e adolescentes).",
            "minimizar_no_prompt": False,
        },
        "nome_mae": {
            "natureza": "Dado Pessoal / Filiação",
            "finalidade": "Diferenciação de homônimos e representação legal de menor.",
            "necessidade": "Essencial para documentação escolar oficial.",
            "risco": "Médio.",
            "minimizar_no_prompt": False,
        },
        "email": {
            "natureza": "Dado de Contato",
            "finalidade": "Envio do comprovante oficial de matrícula e orientações da secretaria.",
            "necessidade": "Canal oficial direto de comunicação com o estudante.",
            "risco": "Baixo/Médio.",
            "minimizar_no_prompt": False,
        },
    }

    # Campos adicionais também podem identificar uma pessoa quando combinados.
    # Estas flags documentam a política proposta; não afirmam anonimização automática.
    for _campo in ("protocolo", "data", "orgao_expedidor", "naturalidade", "uf", "nome_pai",
                   "curso", "eixo_tecnologico", "carga_horaria", "turno", "inicio_curso", "telefone",
                   "assunto", "pedido", "categoria", "nivel_confianca", "campos_ausentes", "necessidade_revisao"):
        TABELA_CAMPOS_LGPD.setdefault(_campo, {
            "natureza": "Dado pessoal ou contextual quando vinculado a pessoa identificável",
            "finalidade": "Triagem, conferência e resposta à solicitação fictícia",
            "necessidade": "Avaliar caso a caso; não usar a presença no schema como autorização de coleta",
            "risco": "Identificação por associação, exposição ou decisão baseada em informação incorreta",
            "minimizar_no_prompt": True})

    @staticmethod
    def mascarar_dado_sensivel(valor: str, tipo: str) -> str:
        """Aplica pseudonimização/máscara para exibição segura em telas públicas ou logs."""
        if not valor or valor.lower() in ["não localizado", "nao localizado"]:
            return valor
        if tipo == "cpf" and len(valor) >= 11:
            v_clean = "".join(c for c in valor if c.isdigit())
            if len(v_clean) == 11:
                return f"***.{v_clean[3:6]}.***-**"
            return f"***.{valor[4:7]}.***-**"
        if tipo == "email" and "@" in valor:
            partes = valor.split("@")
            return f"{partes[0][0]}***@{partes[1]}"
        return valor

    @classmethod
    def gerar_relatorio_conformidade(cls) -> Dict[str, Any]:
        """Gera a matriz formal de adequação à LGPD exigida no RF12."""
        return {
            "titulo": "Relatório de Conformidade com a LGPD (Lei nº 13.709/2018)",
            "orgao": "Governo do Estado de Mato Grosso - SECITECI/MT",
            "principios_atendidos": [
                {"principio": "Finalidade", "status": "Delimitada no protótipo", "evidencia": "Triagem e minuta de casos fictícios. Uma implantação real exige avaliação própria de finalidade/necessidade."},
                {"principio": "Necessidade/Minimização", "status": "PARCIAL", "evidencia": "OCR/STT podem permanecer locais. Texto fictício integral é enviado ao LLM; pseudonimização prévia não implementada."},
                {"principio": "Segurança", "status": "PARCIAL", "evidencia": "Sanitização e controles locais testados; autenticação do grupo ausente. Não constitui certificação de segurança."},
                {"principio": "Transparência", "status": "PARCIAL", "evidencia": "IA identificada e novos registros rastreáveis; evidências históricas incompletas exigem seleção e ressalvas."},
            ],
            "matriz_de_dados": cls.TABELA_CAMPOS_LGPD,
            "declaracao_dados_ficticios": "Uso autorizado exclusivamente com dados FICTÍCIOS. O sistema não consegue comprovar automaticamente que um texto livre não identifica pessoa real.",
        }


class QualityEvaluator:
    """
    Protocolo de Avaliação de Qualidade e Revisão Humana (RF13).
    Calcula fidelidade, completude, gravidade de erros e taxas de aprovação.
    """

    ROTULOS_CAMPOS = {
        "protocolo": "Número de Protocolo",
        "data": "Data da Solicitação",
        "solicitante": "Nome do Requerente / Solicitante",
        "cpf": "Cadastro de Pessoa Física (CPF)",
        "rg": "Registro Geral (RG)",
        "orgao_expedidor": "Órgão Expedidor do RG",
        "data_nascimento": "Data de Nascimento",
        "naturalidade": "Naturalidade / Cidade",
        "uf": "Unidade Federativa (UF)",
        "nome_mae": "Nome da Mãe (Filiação)",
        "nome_pai": "Nome do Pai (Filiação)",
        "curso": "Curso Técnico Pretendido",
        "eixo_tecnologico": "Eixo Tecnológico",
        "carga_horaria": "Carga Horária do Curso",
        "turno": "Turno Solicitado",
        "inicio_curso": "Previsão de Início das Aulas",
        "email": "E-mail de Contato",
        "telefone": "Telefone / Celular",
        "assunto": "Assunto da Manifestação",
        "pedido": "Teor do Pedido Formal",
        "categoria": "Categoria do Atendimento",
    }

    REGRAS_FORMATO_PADRAO = {
        "protocolo": {
            "padrao": r"^\d{4}[-/]\d{5,7}$",
            "esperado": "AAAA-XXXXXX (ex: 2026-000142)",
        },
        "data": {
            "padrao": r"^\d{2}/\d{2}/\d{4}$",
            "esperado": "DD/MM/AAAA",
        },
        "solicitante": {
            "padrao": r"^[A-Za-zÀ-ÿ'\s]{3,}\s+[A-Za-zÀ-ÿ'\s]{2,}$",
            "esperado": "Nome Completo (Mínimo 2 palavras)",
        },
        "cpf": {
            "padrao": r"^(\d{3}\.\d{3}\.\d{3}-\d{2}|\d{11})$",
            "esperado": "000.000.000-00 ou 11 dígitos",
        },
        "rg": {
            "padrao": r"^[0-9A-Za-z.\-\s/]{5,20}$",
            "esperado": "0000000-0 ou dígitos oficiais",
        },
        "orgao_expedidor": {
            "esperado": "Sigla oficial ou 'não localizado'",
        },
        "data_nascimento": {
            "padrao": r"^\d{2}/\d{2}/\d{4}$",
            "esperado": "DD/MM/AAAA",
        },
        "naturalidade": {
            "esperado": "Município / Cidade oficial",
        },
        "uf": {
            "padrao": r"^[A-Za-z]{2}$",
            "esperado": "Sigla da UF (2 letras) ou 'não localizado'",
        },
        "nome_mae": {
            "padrao": r"^[A-Za-zÀ-ÿ'\s]{3,}\s+[A-Za-zÀ-ÿ'\s]{2,}$",
            "esperado": "Nome Completo da Mãe",
        },
        "nome_pai": {
            "esperado": "Nome do Pai ou 'não localizado'",
        },
        "curso": {
            "esperado": "Denominação Institucional do Curso",
        },
        "eixo_tecnologico": {
            "esperado": "Eixo Institucional Oficial (MEC)",
        },
        "carga_horaria": {
            "esperado": "Carga Horária (ex: 1200 horas)",
        },
        "turno": {
            "esperado": "Turno (matutino, vespertino ou noturno)",
        },
        "inicio_curso": {
            "padrao": r"^\d{2}/\d{2}/\d{4}$",
            "esperado": "DD/MM/AAAA",
        },
        "email": {
            "padrao": r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$",
            "esperado": "nome@dominio.ext",
        },
        "telefone": {
            "esperado": "DDD + Telefone ou 'não localizado'",
        },
        "assunto": {
            "esperado": "Tema resumido da manifestação",
        },
        "pedido": {
            "esperado": "Teor da solicitação expressa",
        },
        "categoria": {
            "esperado": "Categoria institucional",
        },
    }

    @classmethod
    def avaliar_conformidade_regras(cls, extracao, regras_customizadas=None):
        """Formato e presença, sem alegar fidelidade ao documento original."""
        regras = cls.REGRAS_FORMATO_PADRAO if regras_customizadas is None else regras_customizadas
        detalhes = []
        erros = []
        conformes = 0
        for campo, regra in regras.items():
            valor = str(extracao.get(campo, "")).strip()
            ausente = not valor or valor.casefold() in {"não localizado", "nao localizado"}
            padrao = regra.get("padrao")
            valido = not ausente and (not padrao or re.fullmatch(padrao, valor) is not None)
            if valido and campo in {"data", "data_nascimento", "inicio_curso"}:
                try:
                    _datetime.strptime(valor, "%d/%m/%Y")
                except ValueError:
                    valido = False
            conformes += int(valido)
            detalhe = {"campo": campo, "rotulo": cls.ROTULOS_CAMPOS.get(campo, campo),
                "esperado": regra.get("esperado", "Formato a conferir"),
                "obtido": valor or "não localizado", "eh_pendencia": ausente,
                "status": "PENDENCIA" if ausente else "FORMATO_CONFORME" if valido else "DIVERGENTE",
                "gravidade": "Alta" if not valido else "Nenhuma",
                "acao_recomendada": "Confirmar na fonte; formato não comprova fidelidade."}
            detalhes.append(detalhe)
            if not valido:
                erros.append(detalhe)
        return {"total_campos_analisados": len(detalhes), "total_acertos": conformes,
            "total_pendencias": sum(d["eh_pendencia"] for d in detalhes),
            "taxa_conformidade_percentual": round(conformes/max(1,len(detalhes))*100,1),
            "comparativo_campos": detalhes, "erros_encontrados": erros,
            "status_qualidade": "Formato conforme; fidelidade não avaliada" if not erros else "Requer revisão",
            "tipo_avaliacao": "formato"}

    @staticmethod
    def _normalizar_valor_comparacao(valor):
        texto = "" if valor is None else str(valor)
        texto = unicodedata.normalize("NFKD", unicodedata.normalize("NFKC", texto).casefold())
        texto = "".join(c for c in texto if not unicodedata.combining(c)
                        and unicodedata.category(c) != "Cf")
        texto = " ".join(texto.split())
        # Equivalências apenas do marcador de ausência, não de valores reais.
        if not texto or re.fullmatch(r"nao[\s_\-\u2010-\u2015]*localizad[oa]\s*[.!;:]?", texto):
            return "nao localizado"
        return texto

    @classmethod
    def _normalizar_campo_comparacao(cls, campo, valor):
        texto = cls._normalizar_valor_comparacao(valor)
        # Apenas apresentação do mesmo identificador; não inferir dígitos/UF/DDI.
        if campo in {"cpf", "rg", "telefone"} and re.fullmatch(r"[\d.()\s+\-x]+", texto):
            limpo = re.sub(r"[.()\s+\-]", "", texto)
            if campo != "cpf" or len(limpo) == 11 and limpo.isdigit():
                return limpo
        if campo == "protocolo" and re.fullmatch(r"\d{4}[-/]\d{5,7}", texto):
            return texto.replace("/", "-")
        return texto

    @classmethod
    def avaliar_extracao(cls, extracao, gabarito):
        """Ausência na fonte é pendência; não vira acerto nem divergência falsa."""
        esperados = gabarito.get("campos_esperados", {})
        comparativo = []
        for campo, esperado in esperados.items():
            obtido = extracao.get(campo, "não localizado")
            referencia = cls._normalizar_campo_comparacao(campo, esperado)
            extraido = cls._normalizar_campo_comparacao(campo, obtido)
            ausente_fonte = referencia == "nao localizado"
            ausente_extraido = extraido == "nao localizado"
            ambos_ausentes = ausente_fonte and ausente_extraido
            correto = not ausente_fonte and not ausente_extraido and referencia == extraido
            pendente = ausente_extraido
            status = "PENDENCIA" if pendente else "CORRETO" if correto else "DIVERGENTE"
            comparativo.append({"campo": campo, "rotulo": cls.ROTULOS_CAMPOS.get(campo, campo),
                "esperado": esperado, "obtido": obtido, "eh_pendencia": pendente,
                "ausente_na_fonte": ausente_fonte,
                "avaliavel_fidelidade": not ambos_ausentes,
                "status": status,
                "gravidade": "Nenhuma" if correto else "Informativa" if ambos_ausentes else "Alta",
                "acao_recomendada": "Dado ausente na fonte; aguardar informação e revisão humana." if ambos_ausentes
                    else "Conferir na fonte e registrar revisão humana."})
        acertos = sum(d["status"] == "CORRETO" for d in comparativo)
        avaliaveis = sum(d["avaliavel_fidelidade"] for d in comparativo)
        disponiveis = [d for d in comparativo if not d["ausente_na_fonte"]]
        extraidos_disponiveis = sum(not d["eh_pendencia"] for d in disponiveis)
        pendencias = sum(d["eh_pendencia"] for d in comparativo)
        erros = [d for d in comparativo if d["status"] == "DIVERGENTE"]
        omissoes = [d for d in disponiveis if d["eh_pendencia"]]
        return {"total_campos_analisados": len(comparativo), "total_acertos": acertos,
            "total_campos_avaliaveis": avaliaveis,
            "total_campos_disponiveis_fonte": len(disponiveis),
            "total_ausentes_na_fonte": sum(d["ausente_na_fonte"] for d in comparativo),
            "total_pendencias": pendencias, "total_omissoes_extracao": len(omissoes),
            "taxa_fidelidade_percentual": round(acertos/avaliaveis*100, 1) if avaliaveis else None,
            "taxa_completude_percentual": round(extraidos_disponiveis/len(disponiveis)*100, 1) if disponiveis else None,
            "criterio_metricas": "Fidelidade exclui apenas ausências coincidentes; completude considera dados disponíveis na fonte. Ausências não contam como acertos.",
            "comparativo_campos": comparativo, "erros_encontrados": erros,
            "omissoes_extracao": omissoes,
            "status_qualidade": "Requer revisão" if erros or omissoes else "Dados conferidos; pendências na fonte" if pendencias
                else "Conferido com referência" if avaliaveis else "Sem dados avaliáveis",
            "tipo_avaliacao": "fidelidade", "conformidade_formato": cls.avaliar_conformidade_regras(extracao)}
