"""
Módulo de Auditoria, Rastreabilidade, LGPD e Avaliação de Qualidade (RF11, RF12, RF13)
"""

import json
import uuid
import hashlib
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

        # Sanitiza parâmetros removendo possíveis chaves de API
        params_limpos = {}
        for k, v in (parametros or {}).items():
            if any(term in k.lower() for term in ["key", "token", "secret", "auth", "pwd"]):
                params_limpos[k] = "[REDACTED]"
            else:
                params_limpos[k] = v

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
                "sucesso": len(erros or []) == 0,
                "campos_extraidos": len(resultado.get("extracao", {})) if isinstance(resultado, dict) else 0,
            },
            "decisao_humana": decisao_humana or {
                "status": "pendente_revisao",
                "operador": "aguardando_validacao",
                "justificativa": "Aguardando deliberação de servidor responsável no painel web.",
            },
        }

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

    def obter_aprovacao_texto(self, exec_id: str, texto: str):
        """Lê a aprovação persistida; não aceita flags enviadas pelo cliente."""
        if not exec_id or not re.fullmatch(r"[A-Za-z0-9_-]+", exec_id):
            return None
        try:
            dado = json.loads((self.log_dir / f"{exec_id}.json").read_text(encoding="utf-8"))
            decisao = dado.get("decisao_humana", {})
            if (decisao.get("status") == "APROVADO" and decisao.get("id_aprovacao")
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
        if not valor or valor == "não localizado":
            return valor
        if tipo == "cpf" and len(valor) >= 11:
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
    Calcula fidelidade, completude, gravidade de erros e taxas de aprovação.
    """

    @staticmethod
    def avaliar_extracao(extracao: Dict[str, Any], gabarito: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compara o resultado obtido contra o gabarito oficial com métricas detalhadas.
        """
        campos_esperados = gabarito.get("campos_esperados", {})
        total_campos = len(campos_esperados)
        acertos = 0
        erros_classificados = []

        for campo, val_esperado in campos_esperados.items():
            val_obtido = extracao.get(campo, "")
            # Normalização para comparação justa
            str_esp = str(val_esperado).strip().lower()
            str_obt = str(val_obtido).strip().lower()

            if str_esp == str_obt or (str_esp in str_obt):
                acertos += 1
            else:
                # Classifica gravidade do erro
                if campo in ["cpf", "rg", "protocolo"]:
                    gravidade = "Alta"
                    acao = "Exige correção manual obrigatória"
                elif campo in ["solicitante", "curso"]:
                    gravidade = "Crítica"
                    acao = "Exige nova geração imediata"
                else:
                    gravidade = "Baixa"
                    acao = "Ajuste secundário opcional"

                erros_classificados.append({
                    "campo": campo,
                    "esperado": val_esperado,
                    "obtido": val_obtido,
                    "gravidade": gravidade,
                    "acao_recomendada": acao,
                })

        taxa_fidelidade = round((acertos / max(1, total_campos)) * 100, 1)

        # Avaliação de completude (campos preenchidos vs 'não localizado' quando ausentes)
        completude = 100.0 if all(k in extracao for k in ["protocolo", "data", "solicitante", "pedido"]) else 75.0

        return {
            "total_campos_analisados": total_campos,
            "total_acertos": acertos,
            "taxa_fidelidade_percentual": taxa_fidelidade,
            "taxa_completude_percentual": completude,
            "erros_encontrados": erros_classificados,
            "status_qualidade": "Excelente" if taxa_fidelidade >= 90 else "Aceitável com Revisão" if taxa_fidelidade >= 70 else "Reprovado",
        }
