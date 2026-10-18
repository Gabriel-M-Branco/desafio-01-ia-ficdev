"""Planejamento/ZIP e conferência RF13, sem rede, inferência ou alteração de decisões.

O manifesto exige revisão humana explícita. A varredura não detecta todos os dados
pessoais possíveis, especialmente em imagens: não substitui inspeção do pacote.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import zipfile

RAIZ = Path(__file__).resolve().parents[1]
RAIZES = {"src", "testes", "ferramentas", "documentacao", "dados", "prompts", "resultados"}
ARQUIVOS_RAIZ = {"README.md", "AGENTS.md", "requirements.txt", "requirements-validado.txt",
    "Dockerfile", "docker-compose.yml", ".env.example", ".gitignore", ".dockerignore", "config.json", "pytest.ini"}
BLOQUEADOS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".rf10-testes-locais",
    ".llm-diagnosticos", ".integracao-local", ".entrega-local", "backups", "node_modules"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def caminho(raiz, nome):
    if not isinstance(nome, str) or "\\" in nome or ":" in nome:
        raise ValueError("Caminho deve ser relativo, com barras /.")
    rel = PurePosixPath(nome)
    if rel.is_absolute() or not rel.parts or any(p in {"..", "."} for p in rel.parts):
        raise ValueError("Caminho fora do projeto.")
    if any(p.lower() in BLOQUEADOS for p in rel.parts):
        raise ValueError("Diretório privado/cache bloqueado.")
    if any(p.lower().startswith(".env") and p != ".env.example" for p in rel.parts):
        raise ValueError("Configuração secreta bloqueada.")
    if rel.suffix.lower() in {".env", ".zip", ".pyc", ".pem", ".key", ".pfx", ".p12", ".bak", ".tmp"}:
        raise ValueError("Tipo privado/temporário bloqueado.")
    if len(rel.parts) == 1 and nome not in ARQUIVOS_RAIZ:
        raise ValueError("Arquivo raiz fora da lista permitida.")
    if len(rel.parts) > 1 and rel.parts[0] not in RAIZES:
        raise ValueError("Pasta fora da lista permitida.")
    path = raiz.joinpath(*rel.parts)
    if any(p.is_symlink() or (hasattr(p, "is_junction") and p.is_junction())
           for p in [path, *list(path.parents)[:len(rel.parts)-1]]):
        raise ValueError("Links/junções não podem ser empacotados.")
    if not path.resolve().is_relative_to(raiz.resolve()) or not path.is_file():
        raise ValueError("Arquivo inexistente ou fora do projeto.")
    return path


def planejar(raiz):
    itens = []
    # Evidências geradas/históricas nunca entram por varredura automática.
    candidatos = [raiz / n for n in sorted(ARQUIVOS_RAIZ) if (raiz / n).is_file()]
    for pasta in ("src", "testes", "ferramentas", "dados/originais", "dados/gabaritos"):
        candidatos.extend((raiz / pasta).rglob("*"))
    for p in candidatos:
        if not p.is_file():
            continue
        nome = p.relative_to(raiz).as_posix()
        try:
            caminho(raiz, nome)
        except ValueError:
            continue
        itens.append({"caminho": nome, "sha256": sha(p)})
    return {"revisao_privacidade_concluida": False, "responsavel_revisao": "",
        "nota": "Adicionar documentação final, prompts/saídas e evidências reais selecionadas com hashes. Revisar cada conteúdo antes de marcar a revisão. Sem credenciais.",
        "arquivos": sorted(itens, key=lambda i: i["caminho"])}


def segredos_locais(raiz):
    valores = [v for k, v in os.environ.items() if re.search("TOKEN|KEY|PASSWORD|SECRET", k, re.I) and len(v) > 8]
    env = raiz / ".env"
    if env.is_file():
        for linha in env.read_text(encoding="utf-8-sig").splitlines():
            if "=" in linha and not linha.lstrip().startswith("#"):
                chave, valor = linha.split("=", 1)
                valor = valor.strip().strip("\"'")
                if re.search("TOKEN|KEY|PASSWORD|SECRET", chave, re.I) and len(valor) > 8:
                    valores.append(valor)
    return [v.encode() for v in valores]


def empacotar(raiz, manifesto, destino):
    if manifesto.get("revisao_privacidade_concluida") is not True or not manifesto.get("responsavel_revisao", "").strip():
        raise ValueError("Revisão humana de privacidade e responsável obrigatórios.")
    itens = manifesto.get("arquivos", [])
    if not itens:
        raise ValueError("Manifesto vazio.")
    segredos = segredos_locais(raiz)
    conteudos, vistos = [], set()
    for item in itens:
        nome = item["caminho"]
        p = caminho(raiz, nome)
        if nome.casefold() in vistos:
            raise ValueError("Caminho duplicado no Windows.")
        vistos.add(nome.casefold())
        dados = p.read_bytes()
        if hashlib.sha256(dados).hexdigest() != item["sha256"]:
            raise ValueError("Arquivo divergiu do manifesto; revisar novamente.")
        padrao_privado = re.search(rb"(?:sk-or-v1-|hf_)[A-Za-z0-9_-]{16,}|Bearer\s+[A-Za-z0-9_.-]{20,}|S-1-5-21-(?:\d+-){2,}\d+", dados)
        fixture_declarada = nome.startswith("testes/") and nome.endswith(".py") and bool(item.get("justificativa_fixture_sintetica", "").strip())
        if any(s in dados for s in segredos) or (padrao_privado and not fixture_declarada):
            raise ValueError("Possível segredo/identificador privado; pacote bloqueado.")
        conteudos.append((nome, dados))
    obrigatorios = {"README.md", "requirements.txt", ".env.example", "config.json", "src/main.py"}
    if not obrigatorios.issubset({n for n, _ in conteudos}):
        raise ValueError("Estrutura mínima ausente.")
    for pasta in ("dados/originais/", "dados/gabaritos/", "dados/processados/", "prompts/",
                  "documentacao/", "resultados/minutas/", "resultados/audios/", "resultados/imagens/"):
        if not any(n.startswith(pasta) and not n.endswith(".gitkeep") for n, _ in conteudos):
            raise ValueError("Faltam categorias de entregáveis; concluir seleção humana.")
    # A validação completa ocorre antes de abrir a saída; nunca sobrescreve ZIP.
    with zipfile.ZipFile(destino, "x", zipfile.ZIP_DEFLATED) as z:
        for nome, dados in conteudos:
            z.writestr(nome, dados)
        z.writestr("MANIFESTO_SHA256.json", json.dumps({n: hashlib.sha256(d).hexdigest() for n,d in conteudos}, indent=2))
    with zipfile.ZipFile(destino) as z:
        if z.testzip() is not None:
            raise ValueError("ZIP com falha de integridade.")
    return len(conteudos)


def conferir_coorte(raiz, ficha):
    """Valida consistência; nunca prova autoria humana ou altera uma decisão."""
    casos = ficha.get("casos", [])
    if len(casos) < 2:
        raise ValueError("Selecionar pelo menos dois casos finais distintos.")
    ids, estados = set(), set()
    for caso in casos:
        if caso.get("revisado_pela_equipe") is not True:
            raise ValueError("Conferência humana da ficha pendente.")
        p = caminho(raiz, caso["arquivo_registro"])
        if sha(p) != caso["sha256_registro"]:
            raise ValueError("Hash do registro divergente.")
        dado = json.loads(p.read_text(encoding="utf-8-sig"))
        ident = dado.get("id_execucao")
        if not ident or ident != caso.get("id_execucao") or ident in ids or dado.get("modalidade") != "texto":
            raise ValueError("Usar casos finais textuais distintos, com IDs válidos; não TTS/eventos de fonte.")
        ids.add(ident)
        if dado.get("resultado_resumo", {}).get("sucesso") is not True or re.search(r"mock|teste|test", dado.get("provedor", ""), re.I):
            raise ValueError("Não usar falha técnica ou saída mockada como caso final real.")
        decisao = dado.get("decisao_humana", {})
        estado = decisao.get("status")
        if estado != caso.get("status_esperado") or estado not in {"APROVADO", "REJEITADO", "CORRIGIDO"}:
            raise ValueError("Decisão persistida não corresponde à ficha.")
        if not all(decisao.get(k) for k in ("operador", "data_decisao", "justificativa")):
            raise ValueError("Decisão sem responsável/data/justificativa.")
        if estado == "APROVADO" and (not dado.get("texto_final") or not decisao.get("id_aprovacao") or
                decisao.get("hash_texto_aprovado") != hashlib.sha256(dado["texto_final"].encode()).hexdigest()):
            raise ValueError("Aprovação não corresponde ao texto final.")
        referencia = caminho(raiz, caso["referencia"])
        if sha(referencia) != caso["sha256_referencia"]:
            raise ValueError("Referência divergiu.")
        if not all(str(caso.get("criterios", {}).get(k, "")).strip() for k in
                   ("fidelidade", "completude", "formato", "linguagem", "seguranca")):
            raise ValueError("Preencher os cinco critérios com observações verificáveis.")
        estados.add(estado)
    if "APROVADO" not in estados or not estados.intersection({"REJEITADO", "CORRIGIDO"}):
        raise ValueError("Faltam caso APROVADO e caso REJEITADO/CORRIGIDO.")
    aprovados = sum(c["status_esperado"] == "APROVADO" for c in casos)
    return {"casos": len(ids), "aprovados": aprovados,
        "taxa_aprovacao_percentual_coorte": round(100 * aprovados / len(ids), 1),
        "resultado": "Consistência documental conferida; autoria humana e veracidade dependem da equipe."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("acao", choices=("planejar", "zip", "coorte"))
    parser.add_argument("arquivo", type=Path, help="Manifesto/ficha local JSON")
    parser.add_argument("--saida", type=Path, help="Novo ZIP; nunca sobrescreve")
    args = parser.parse_args()
    try:
        if args.acao == "planejar":
            with args.arquivo.open("x", encoding="utf-8") as f:
                json.dump(planejar(RAIZ), f, ensure_ascii=False, indent=2)
            print("Plano criado; revisão e seleção de evidências ainda obrigatórias.")
        else:
            ficha = json.loads(args.arquivo.read_text(encoding="utf-8-sig"))
            if args.acao == "coorte":
                print(json.dumps(conferir_coorte(RAIZ, ficha), ensure_ascii=False))
            elif not args.saida:
                parser.error("zip exige --saida")
            else:
                print("ZIP verificado; arquivos:", empacotar(RAIZ, ficha, args.saida))
    except (ValueError, OSError, KeyError, TypeError, zipfile.BadZipFile):
        parser.exit(1, "Não concluído: revise formato, campos obrigatórios, caminhos, hashes, decisões, privacidade e destino novo. Nenhum detalhe de credencial é exibido.\n")


if __name__ == "__main__":
    main()
