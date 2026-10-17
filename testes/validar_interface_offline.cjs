// Harness DOM mínimo: código real da interface, fetch local e nenhum navegador/rede.
const fs = require("node:fs");
const vm = require("node:vm");
const assert = require("node:assert/strict");
const elementos = new Map();
const alertas = [];
function el(id) {
  if (!elementos.has(id)) elementos.set(id, {
    value: id === "input-texto-solicitacao" ? "Solicitação fictícia" : "",
    textContent: "", innerHTML: "", style: {}, dataset: {}, listeners: {},
    classList: {add(){},remove(){}},
    addEventListener(tipo,fn){this.listeners[tipo]=fn;},
    querySelectorAll(){return [];},
    getAttribute(){return null;},
    play(){},click(){},
  });
  return elementos.get(id);
}
const estado = {
  sucesso: true, id_execucao: "EXEC_TESTE", extracao: {protocolo:"não localizado"},
  minuta_institucional:"Minuta real do mock de transporte",
  url_pdf:"/arquivos/resultados/minutas/teste.pdf",
  metricas:{duracao_segundos:0.1,total_tokens:12,custo_usd:null,provedor:"mock-transporte",modelo:"modelo"},
  avaliacao_gabarito:{
    tipo_avaliacao:"fidelidade",total_acertos:0,total_campos_analisados:1,
    taxa_fidelidade_percentual:0,status_qualidade:"Requer revisão",
    erros_encontrados:[{campo:"protocolo",esperado:"2099-000001",obtido:"<img src=x onerror=alert(1)>"}],
    comparativo_campos:[{campo:"protocolo",rotulo:"Protocolo",esperado:"2099-000001",
      obtido:"<img src=x onerror=alert(1)>",status:"DIVERGENTE",eh_pendencia:false}]
  }
};
const contexto = {
  console, Date, JSON, String, Number, Map,
  alert:(s)=>alertas.push(s),
  document:{
    addEventListener(tipo,fn){if(tipo==="DOMContentLoaded")fn();},
    querySelectorAll(){return [];},
    getElementById:el
  },
  window:{prompt:()=>null,open(){}},
  fetch:async(url)=>({ok:true,json:async()=> url==="/api/config" ? {has_hf_token:false} :
    url.startsWith("/api/casos/") ? {conteudo:"Solicitação fictícia"} : estado})
};
vm.runInNewContext(fs.readFileSync(require("node:path").join(__dirname,"../src/web/app.js"),"utf8"),contexto);
(async()=>{
  await Promise.resolve(); await Promise.resolve();
  el("input-texto-solicitacao").value="Solicitação fictícia";
  await el("btn-processar-solicitacao").listeners.click();
  assert.equal(el("metric-custo").textContent,"Não informado");
  assert.equal(el("badge-status-revisao").textContent,"Pendente de Revisao Humana");
  assert.ok(!el("tabela-conferencia-body").innerHTML.includes("<img src=x"));
  assert.ok(el("tabela-conferencia-body").innerHTML.includes("&lt;img"));
  assert.equal(alertas.length,0);
  console.log("Interface offline: custo desconhecido, revisão pendente e escape de dados OK.");
})().catch(e=>{console.error(e);process.exitCode=1;});
