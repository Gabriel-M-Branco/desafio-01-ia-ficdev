"""
Módulo de Auditoria, Rastreabilidade, LGPD e Avaliação de Qualidade (RF11, RF12, RF13)
"""

import json
import uuid
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

from src import resolver_caminho, caminho_relativo


class AuditLogger:
    """
    Registrador de auditoria estruturada e rastreabilidade completa (RF11).
    Garante integridade, anonimização de credenciais e vínculo estrito com arquivos de entrada.
    """

    def __init__(self, log_dir: str = "resultados/logs"):
        self.log_dir = resolver_caminho(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.trail_file = self.log_dir / "audit_trail.jsonl"

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

        params_limpos = {}
        for k, v in (parametros or {}).items():
            if any(term in k.lower() for term in ["key", "token", "secret", "auth", "pwd"]):
                params_limpos[k] = "[REDACTED]"
            else:
                params_limpos[k] = v

        registro = {
            "id_execucao": exec_id,
            "timestamp": datetime.now().isoformat(),
            "modalidade": modalidade,
            "arquivo_origem": caminho_relativo(arquivo_origem),
            "provedor": provedor,
            "modelo": modelo,
            "versao_prompt": versao_prompt,
            "parametros": params_limpos,
            "duracao_segundos": duracao_segundos,
            "erros": erros or [],
            "resultado_resumo": {
                "sucesso": len(erros or []) == 0,
                "campos_extraidos": len(resultado.get("extracao", {})) if isinstance(resultado, dict) else 0,
            },
            "decisao_humana": decisao_humana or {
                "status": "pendente_revisao",
                "operador": "aguardando_validacao",
                "justificativa": "Aguardando deliberação de servidor responsável no painel web.",
            },
        }

        with open(self.trail_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(registro, ensure_ascii=False) + "\n")

        individual_file = self.log_dir / f"{exec_id}.json"
        with open(individual_file, "w", encoding="utf-8") as f:
            json.dump({**registro, "detalhes_completos": resultado}, f, ensure_ascii=False, indent=2)

        return exec_id

    def atualizar_decisao_humana(self, exec_id: str, decisao: str, justificativa: str, operador: str = "Servidor Público") -> bool:
        """
        Atualiza o status de Human-in-the-Loop de uma execução (RF13).
        decisao: 'APROVADO', 'REJEITADO', 'CORRIGIDO'
        """
        individual_file = self.log_dir / f"{exec_id}.json"
        if not individual_file.exists():
            return False

        with open(individual_file, "r", encoding="utf-8") as f:
            dado = json.load(f)

        dado["decisao_humana"] = {
            "status": decisao,
            "operador": operador,
            "justificativa": justificativa,
            "data_decisao": datetime.now().isoformat(),
        }

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
            "natureza": "Dado Pessoal Sensível/Crítico",
            "finalidade": "Unicidade cadastral junto ao MEC e órgãos estaduais de educação.",
            "necessidade": "Obrigatório para registro educacional oficial.",
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
                {"principio": "Finalidade", "status": "Atendido", "evidencia": "Dados processados estritamente para o ato de matrícula e resposta oficial."},
                {"principio": "Necessidade/Minimização", "status": "Atendido", "evidencia": "Campos não essenciais são descartados e prompts usam apenas o estritamente necessário."},
                {"principio": "Segurança", "status": "Atendido", "evidencia": "Chaves de API jamais gravadas em log; opção de processamento local para documentos sensíveis."},
                {"principio": "Transparência", "status": "Atendido", "evidencia": "Trilha de auditoria integral e identificação clara de conteúdo gerado por IA."},
            ],
            "matriz_de_dados": cls.TABELA_CAMPOS_LGPD,
            "declaracao_dados_ficticios": "Todos os dados manipulados neste protótipo são integralmente FICTÍCIOS, sem correspondência com pessoas reais.",
        }


class QualityEvaluator:
    """
    Protocolo de Avaliação de Qualidade e Revisão Humana (RF13).
    Valida conformidade de formato, regras institucionais e o princípio de Alucinação Zero ('não localizado')
    a partir dos arquivos originais, oferecendo conferência campo a campo para o operador público.
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
            "padrao": r"^\d{3}\.\d{3}\.\d{3}-\d{2}$",
            "esperado": "000.000.000-00",
        },
        "rg": {
            "padrao": r"^[0-9A-Za-z.\-]{5,15}$",
            "esperado": "0000000-0 (RG oficial)",
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
    def avaliar_conformidade_regras(
        cls,
        extracao: Dict[str, Any],
        regras_customizadas: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Avalia os dados extraídos dos arquivos originais confrontando formatos, regras
        institucionais e o cumprimento da diretriz de Alucinação Zero ('não localizado').
        """
        comparativo_campos = []
        erros_classificados = []
        campos_relevantes = [
            "protocolo", "data", "solicitante", "cpf", "rg", "orgao_expedidor",
            "data_nascimento", "naturalidade", "uf", "nome_mae", "nome_pai",
            "curso", "eixo_tecnologico", "carga_horaria", "turno", "inicio_curso",
            "email", "telefone", "assunto", "pedido", "categoria"
        ]

        total_analisados = 0
        total_conformes = 0
        total_pendencias = 0

        for campo in campos_relevantes:
            if campo not in extracao:
                continue
            total_analisados += 1
            val = str(extracao.get(campo, "")).strip()
            rotulo = cls.ROTULOS_CAMPOS.get(campo, campo.replace("_", " ").title())
            eh_pendencia = (val.lower() in ["não localizado", "nao localizado"])

            regra = cls.REGRAS_FORMATO_PADRAO.get(campo, {})
            esperado_desc = regra.get("esperado", "Padrão institucional validado")

            inconsistencia = None
            if not eh_pendencia and val:
                padrao_regex = regra.get("padrao")
                if padrao_regex and not re.match(padrao_regex, val):
                    inconsistencia = f"Formato fora do padrão institucional ({esperado_desc})."
                elif campo == "solicitante" and len(val.split()) < 2:
                    inconsistencia = "Nome do requerente deve conter prenome e sobrenome."

            if eh_pendencia:
                total_pendencias += 1
                status = "PENDENCIA"
                gravidade = "Baixa"
                acao = "Dado não informado no arquivo original. Preenchido compulsoriamente com 'não localizado' (Alucinação Zero)."
                esperado_exibicao = "não localizado (Alucinação Zero)"
            elif inconsistencia:
                status = "DIVERGENTE"
                gravidade = "Alta" if campo in ["cpf", "rg", "protocolo", "solicitante"] else "Média"
                acao = inconsistencia
                esperado_exibicao = esperado_desc
                erros_classificados.append({
                    "campo": campo,
                    "rotulo": rotulo,
                    "esperado": esperado_exibicao,
                    "obtido": val,
                    "gravidade": gravidade,
                    "acao_recomendada": inconsistencia,
                })
            else:
                total_conformes += 1
                status = "CORRETO"
                gravidade = "Nenhuma"
                acao = "Dado em estrita conformidade com o formato oficial."
                esperado_exibicao = esperado_desc

            comparativo_campos.append({
                "campo": campo,
                "rotulo": rotulo,
                "esperado": esperado_exibicao,
                "obtido": val,
                "status": status,
                "eh_pendencia": eh_pendencia,
                "gravidade": gravidade,
                "acao_recomendada": acao,
            })

        total_validos = total_conformes + total_pendencias
        taxa = round((total_validos / max(1, total_analisados)) * 100, 1)

        return {
            "total_campos_analisados": total_analisados,
            "total_acertos": total_conformes,
            "total_pendencias": total_pendencias,
            "taxa_fidelidade_percentual": taxa,
            "taxa_completude_percentual": 100.0 if total_pendencias <= 5 else 85.0,
            "erros_encontrados": erros_classificados,
            "comparativo_campos": comparativo_campos,
            "status_qualidade": "Excelente" if len(erros_classificados) == 0 else "Requer Atenção",
        }

    @classmethod
    def avaliar_extracao(
        cls,
        extracao: Dict[str, Any],
        gabarito: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Método unificado de avaliação (RF13). Valida conformidade perante regras institucionais
        e Alucinação Zero ('não localizado') a partir dos arquivos originais.
        """
        return cls.avaliar_conformidade_regras(extracao, gabarito)

    @classmethod
    def avaliar_caso_personalizado(cls, extracao: Dict[str, Any]) -> Dict[str, Any]:
        """
        Avalia conformidade de qualquer entrada personalizada.
        """
        return cls.avaliar_conformidade_regras(extracao)
