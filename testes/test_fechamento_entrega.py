"""Ferramentas de entrega: apenas fixtures e arquivos temporários, sem decisões reais."""
import copy
import hashlib
import json
import zipfile

import pytest
from ferramentas.fechar_entrega import caminho, conferir_coorte, empacotar, planejar, sha


def arquivo(raiz, nome, conteudo):
    p = raiz / nome
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(conteudo, encoding="utf-8")
    return {"caminho": nome, "sha256": sha(p)}


def pacote(raiz):
    nomes = ["README.md", "requirements.txt", ".env.example", "config.json", "src/main.py",
        "dados/originais/fonte.txt", "dados/gabaritos/ref.json", "dados/processados/ocr.json",
        "prompts/experimento/saida.txt", "documentacao/relatorio.md", "resultados/minutas/minuta.txt",
        "resultados/audios/wav_fixture.txt", "resultados/imagens/png_fixture.txt"]
    return {"revisao_privacidade_concluida": True, "responsavel_revisao": "Revisor fictício",
        "arquivos": [arquivo(raiz, n, "Fixture sem dados reais") for n in nomes]}


def test_zip_preserva_bytes_e_hashes_sem_sobrescrever(tmp_path):
    ficha = pacote(tmp_path)
    saida = tmp_path / "final.zip"
    assert empacotar(tmp_path, ficha, saida) == len(ficha["arquivos"])
    with zipfile.ZipFile(saida) as z:
        assert z.testzip() is None
        manifesto = json.loads(z.read("MANIFESTO_SHA256.json"))
        assert all(hashlib.sha256(z.read(n)).hexdigest() == h for n, h in manifesto.items())
    antes = saida.read_bytes()
    with pytest.raises(FileExistsError):
        empacotar(tmp_path, ficha, saida)
    assert saida.read_bytes() == antes


@pytest.mark.parametrize("nome", ["../fora.txt", ".env", ".env.backup", "src/../README.md",
    "C:/segredo.txt", ".rf10-testes-locais/decisao.json", "src/__pycache__/a.pyc", "src/chave.pem"])
def test_caminhos_privados_ou_externos_bloqueados(tmp_path, nome):
    with pytest.raises(ValueError):
        caminho(tmp_path, nome)


@pytest.mark.parametrize("falha", ["revisao", "hash", "duplicado", "incompleto", "segredo", "sid"])
def test_zip_bloqueia_antes_de_criar_saida(tmp_path, monkeypatch, falha):
    ficha = pacote(tmp_path)
    if falha == "revisao":
        ficha["revisao_privacidade_concluida"] = False
    elif falha == "hash":
        (tmp_path / "README.md").write_text("Alterado", encoding="utf-8")
    elif falha == "duplicado":
        ficha["arquivos"].append(copy.deepcopy(ficha["arquivos"][0]))
    elif falha == "incompleto":
        ficha["arquivos"] = ficha["arquivos"][:5]
    else:
        monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "credencial_ficticia_atual_nao_compartilhar")
        valor = "credencial_ficticia_atual_nao_compartilhar" if falha == "segredo" else "S-1-5-21-555-666-777-1001"
        ficha["arquivos"].append(arquivo(tmp_path, "documentacao/privado.txt", valor))
    saida = tmp_path / "nao_criar.zip"
    with pytest.raises(ValueError):
        empacotar(tmp_path, ficha, saida)
    assert not saida.exists()


def test_fixture_declarada_nao_libera_credencial_atual(tmp_path, monkeypatch):
    ficha = pacote(tmp_path)
    item = arquivo(tmp_path, "testes/fixture.py", 'sid="S-1-5-21-555-666-777-1001"')
    item["justificativa_fixture_sintetica"] = "Identificador sintético de teste inspecionado"
    ficha["arquivos"].append(item)
    empacotar(tmp_path, ficha, tmp_path / "fixture.zip")
    monkeypatch.setenv("CHAVE_SECRET", "segredo_atual_ficticio_bloqueado")
    item.update(arquivo(tmp_path, "testes/fixture.py", "segredo_atual_ficticio_bloqueado"))
    with pytest.raises(ValueError):
        empacotar(tmp_path, ficha, tmp_path / "segredo.zip")


def test_plano_nao_inclui_evidencias_automaticamente(tmp_path):
    pacote(tmp_path)
    arquivo(tmp_path, ".env", "TOKEN=privado")
    plano = planejar(tmp_path)
    nomes = [i["caminho"] for i in plano["arquivos"]]
    assert "src/main.py" in nomes and "dados/originais/fonte.txt" in nomes
    assert ".env" not in nomes and not any(n.startswith("resultados/") for n in nomes)
    assert plano["revisao_privacidade_concluida"] is False


def coorte(raiz):
    ref = arquivo(raiz, "dados/originais/fonte.txt", "Fonte fictícia")
    casos = []
    for numero, status in enumerate(("APROVADO", "REJEITADO")):
        ident = f"EXEC_FIXTURE_{numero}"
        texto = "Minuta fictícia conferível"
        decisao = {"status": status, "operador": "Revisor fictício", "data_decisao": "2099-01-01T12:00:00",
            "justificativa": "Observação de teste", "id_aprovacao": "fixture",
            "hash_texto_aprovado": hashlib.sha256(texto.encode()).hexdigest()}
        registro = {"id_execucao": ident, "modalidade": "texto", "provedor": "openrouter",
            "resultado_resumo": {"sucesso": True}, "texto_final": texto, "decisao_humana": decisao}
        item = arquivo(raiz, f"resultados/logs/{ident}.json", json.dumps(registro))
        casos.append({"id_execucao": ident, "arquivo_registro": item["caminho"], "sha256_registro": item["sha256"],
            "status_esperado": status, "referencia": ref["caminho"], "sha256_referencia": ref["sha256"],
            "revisado_pela_equipe": True, "criterios": {k: "Observação fictícia" for k in
                ("fidelidade", "completude", "formato", "linguagem", "seguranca")}})
    return {"casos": casos}


def test_coorte_confere_sem_modificar_registros(tmp_path):
    ficha = coorte(tmp_path)
    antes = [sha(tmp_path / c["arquivo_registro"]) for c in ficha["casos"]]
    resumo = conferir_coorte(tmp_path, ficha)
    assert resumo["taxa_aprovacao_percentual_coorte"] == 50
    assert antes == [sha(tmp_path / c["arquivo_registro"]) for c in ficha["casos"]]


@pytest.mark.parametrize("falha", ["sem_humano", "duplicado", "sem_criterio", "hash", "sem_rejeicao", "texto_modificado", "mock"])
def test_coorte_recusa_evidencia_inconsistente(tmp_path, falha):
    ficha = coorte(tmp_path)
    caso = ficha["casos"][0]
    if falha == "sem_humano":
        caso["revisado_pela_equipe"] = False
    elif falha == "duplicado":
        ficha["casos"][1] = copy.deepcopy(caso)
    elif falha == "sem_criterio":
        caso["criterios"]["linguagem"] = ""
    elif falha == "hash":
        caso["sha256_registro"] = "0" * 64
    else:
        alvo = ficha["casos"][1] if falha == "sem_rejeicao" else caso
        p = tmp_path / alvo["arquivo_registro"]
        registro = json.loads(p.read_text(encoding="utf-8"))
        if falha == "sem_rejeicao":
            registro["decisao_humana"]["status"] = alvo["status_esperado"] = "APROVADO"
        elif falha == "mock":
            registro["provedor"] = "mock-browser"
        else:
            registro["texto_final"] += " modificado"
        p.write_text(json.dumps(registro), encoding="utf-8")
        alvo["sha256_registro"] = sha(p)
    with pytest.raises(ValueError):
        conferir_coorte(tmp_path, ficha)
