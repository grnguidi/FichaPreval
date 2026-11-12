/* Ficha Prevalecentes — versão de mesa para celular */
"use strict";
const D = window.DADOS, R = window.R;
const $ = (s, el = document) => el.querySelector(s);
const esc = (t) => String(t ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const int = (v, d = 0) => { const n = parseInt(String(v ?? "").replace("+", ""), 10); return Number.isFinite(n) ? n : d; };
const OK = "✓", NO = "✗";
const ARMAS = Object.fromEntries(D.armas.map((a) => [a.nome, a]));
const ENC = Object.fromEntries(D.encantamentos.map((e) => [e.nome, e]));
const TAL = {}; D.talentos.forEach((t) => { if (!TAL[t.nome]) TAL[t.nome] = t; });
const TALISMA = Object.fromEntries(D.talismas.map((t) => [t.nome, t]));
const SETS = Object.fromEntries((D.sets || []).map((x) => [x.nome, x]));
const PECAS = ["Capacete", "Peitoral", "Manopla", "Calça", "Bota", "Arma"];
const SLOTS = [...Array(15)].map((_, i) => String(2 + 2 * i)).concat(["extra"]);
const CATS_TAL = [...new Set(D.talentos.map((t) => t.categoria))].sort();
const CATS_ENC = [...new Set(D.encantamentos.map((e) => e.categoria))];
const TIERS = [...new Set(D.encantamentos.flatMap((e) => e.versoes.map((v) => v.tier)))].sort();

// ------------------------------------------------------------------ armazenamento
const CHAVE = "prevalecentes.mesa.v1";
let banco = { fichas: {}, atual: null, tema: "dia", modo: "jogo" };
function lerLocal() { try { const x = JSON.parse(localStorage.getItem(CHAVE)); if (x && x.fichas) banco = Object.assign(banco, x); } catch (e) { /* sem storage */ } }
function gravarLocal() { try { localStorage.setItem(CHAVE, JSON.stringify(banco)); } catch (e) { /* cheio ou bloqueado */ } }
let nuvem = null, nuvemUid = null, timerNuvem = null;
async function ligarNuvem() {
  if (!window.claude || !window.claude.use) return;
  try {
    const db = await window.claude.use("db"), user = await window.claude.use("user");
    if (!db || !user) return;
    nuvemUid = await user.id();
    nuvem = db;
    if (!nuvemUid) { nuvem = null; return; }
    const snap = await Promise.race([db.collection("data/users/" + nuvemUid).get(),
      new Promise((_, rej) => setTimeout(() => rej(new Error("tempo")), 10000))]);
    let mudou = false;
    for (const d of snap.docs) {
      const dados = d.data();
      const id = d.id;
      if (!dados || !dados.estado) continue;
      const local = banco.fichas[id];
      if (!local || (dados.estado._salvo || 0) > (local._salvo || 0)) { banco.fichas[id] = dados.estado; mudou = true; }
    }
    if (mudou) { gravarLocal(); if (!S && banco.atual && banco.fichas[banco.atual]) abrirFicha(banco.atual); else render(); }
    if (mudou) toast("Fichas sincronizadas com a sua conta Claude.");
  } catch (e) { nuvem = null; }
}
function enviarNuvem(id) {
  if (!nuvem) return;
  clearTimeout(timerNuvem);
  timerNuvem = setTimeout(async () => {
    try {
      const ref = nuvem.collection("data/users/" + nuvemUid).doc(id);
      if (banco.fichas[id]) await ref.set({ estado: banco.fichas[id] }); else await ref.delete();
    } catch (e) { /* offline: fica no aparelho */ }
  }, 900);
}

// ------------------------------------------------------------------ estado
let S = null, C = null, aba = "ficha";
function novoEstado() {
  return {
    versao: 1, inicializado: true, sem_alma: false, especie_notas: "",
    identidade: { nome: "", player: "", nivel: 1, especie: "", sonho: "", guilda: "" },
    atributos: Object.fromEntries(R.ATRIBUTOS.map((k) => [k, { inicial: "", niveis: "0", especie: "0", bonus: "0" }])),
    vida: { modo: "media", rolagens: [], atual: "", mana_atual: "", vigor_atual: "" },
    pericias: [], prevalencia_attr: "ARC", pericia_ataque: "Luta",
    armas: [{ grupo: "", nivel: "1", props: "" }, { grupo: "", nivel: "1", props: "" }],
    equip: { armadura: "", escudo: "", ca_extra: "", peitoral_set: false },
    encantamentos: [], talentos: Object.fromEntries(SLOTS.map((s) => [s, ""])),
    alma: { nome: "", atr: "INT", restantes: "", historia: "", habilidades: [] },
    talismas: [...Array(7)].map(() => ({ nome: "", efeito: "" })),
    set: {}, inventario: [], dinheiro: "",
    condicoes: Object.fromEntries(R.CONDICOES.map((n) => [n, { max: "100", atual: "", notas: "" }])),
    portao: { Sucessos: [false, false, false, false, false], Falhas: [false, false, false, false, false] }, cicatrizes: "",
    vinculos: { grupo: "", mundo: "", metas: "" }, receitas: "",
    manual: {}, talentos_ativos: [],
  };
}
function normalizar(s) {
  const b = novoEstado();
  const out = Object.assign(b, s || {});
  out.identidade = Object.assign(b.identidade, (s || {}).identidade);
  out.vida = Object.assign(novoEstado().vida, out.vida);
  out.equip = Object.assign(novoEstado().equip, out.equip);
  for (const k of R.ATRIBUTOS) out.atributos[k] = Object.assign({ inicial: "", niveis: "0", especie: "0", bonus: "0" }, (out.atributos || {})[k]);
  out.talentos = Object.assign(Object.fromEntries(SLOTS.map((x) => [x, ""])), out.talentos);
  while (out.armas.length < 2) out.armas.push({ grupo: "", nivel: "1", props: "" });
  while (out.talismas.length < 7) out.talismas.push({ nome: "", efeito: "" });
  out.portao = Object.assign(novoEstado().portao, out.portao);
  out.condicoes = Object.assign(novoEstado().condicoes, out.condicoes);
  out.manual = Object.assign({}, out.manual || {});
  out.talentos_ativos = Array.isArray(out.talentos_ativos) ? out.talentos_ativos : [];
  out.inventario = (Array.isArray(out.inventario) ? out.inventario : []).filter((i) => i && (String(i.item || "").trim() || String(i.carga || "").trim()));
  out.set = Object.assign({}, out.set || {});
  return out;
}
function salvar() {
  if (!S || !banco.atual) return;
  S._salvo = Date.now();
  banco.fichas[banco.atual] = S;
  gravarLocal();
  enviarNuvem(banco.atual);
}
function mudar(fn) { fn(S); salvar(); render(); }

// ------------------------------------------------------------------ cálculo (porta do recalc do PC)
const nivel = () => Math.max(1, Math.min(R.NIVEL_MAX, int(S.identidade.nivel, 1)));
const talentos = () => new Set(Object.values(S.talentos).filter(Boolean));
const armasEq = () => S.armas.map((a) => a.grupo).filter((g) => ARMAS[g]);
function bonusTalismas(nv, tal) {
  const out = {};
  S.talismas.slice(0, R.slotsTalismas(nv, tal)).forEach((t) => {
    const b = (TALISMA[t.nome] || {}).bonus || {};
    for (const [k, v] of Object.entries(b)) out[k] = (out[k] || 0) + v;
  });
  return out;
}
function protecao(tipo) {
  const lista = tipo === "armadura" ? D.armaduras : D.escudos;
  return lista.find((x) => x.nome === S.equip[tipo]) || null;
}
function calcular() {
  const nv = nivel(), tal = talentos();
  const tb = bonusTalismas(nv, tal);
  const a = {};
  for (const k of R.ATRIBUTOS) {
    const x = S.atributos[k];
    a[k] = int(x.inicial) + int(x.niveis) + int(x.especie) + int(x.bonus) + (tb[k] || 0);
    if (S.manual[k] != null) a[k] = int(S.manual[k]);
  }
  const nVida = R.curva(a.VIT) + (tal.has("Vida Dura") ? 3 : 0);
  const soma = S.vida.modo === "media" ? 7 * nVida : (S.vida.rolagens || []).slice(0, nVida).reduce((x, y) => x + y, 0);
  const arm = protecao("armadura"), esc = protecao("escudo");
  const d = R.derivadas(a, nv, tal, soma, arm ? arm.ca : 0, esc ? esc.ca : 0, int(S.equip.ca_extra));
  const ativos = new Set(S.talentos_ativos.filter((n) => tal.has(n) && (R.EFEITOS_TALENTOS[n] || {}).tipo === "sit"));
  const ef = R.efeitosTalentos(tal, ativos, S.equip.armadura || "");
  d.ca = Math.max(10, Math.min(25, d.ca + ef.ca)); d.movimento += ef.mov; d.iniciativa_bonus += ef.iniciativa;
  d.descoberta += ef.descoberta; d.contra_encant += ef.contra;
  d.vida_auto = d.vida; d.mana_auto = d.mana;
  if (S.manual.vida != null) d.vida = int(S.manual.vida);
  if (S.manual.mana != null) d.mana = int(S.manual.mana);
  let carga = 0;
  for (const it of S.inventario || []) carga += parseFloat(String(it.carga || 0).replace(",", ".")) || 0;
  carga += (arm ? arm.peso : 0) + (esc ? esc.peso : 0) - (tal.has("Veterano de Armadura") && arm ? 2 : 0);
  carga += S.talismas.filter((t) => t.nome).length;
  S.armas.forEach((w) => { const ar = ARMAS[w.grupo]; if (ar) { const l = ar.tabela.find((x) => x.nivel === int(w.nivel, 1)); if (l) carga += l.espaco; } });
  const limLent = tal.has("Mochileiro") ? 0.6 : 0.5;
  const lentidao = carga > 0 && carga >= d.carga * limLent, exaustao = carga > 0 && d.carga - carga <= 10;
  const disp = R.pontosDeNivel(nv, S.sem_alma);
  const gastos = R.ATRIBUTOS.reduce((s, k) => s + int(S.atributos[k].niveis), 0);
  const ini = R.ATRIBUTOS.map((k) => int(S.atributos[k].inicial)).filter(Boolean);
  const treinadas = new Set(S.pericias);
  const C = { nv, tal, a, tb, d, ef, ativos, nVida, soma, arm, esc, carga, lentidao, exaustao, mov: lentidao ? Math.min(6, d.movimento) : d.movimento, disp, gastos, resto: disp - gastos, treinadas, avisos: [] };
  // avisos
  const av = C.avisos;
  for (const k of Object.keys(S.manual)) av.push(["info", `${R.NOMES_ATR[k] || (k === "vida" ? "Vida máx." : "Mana máx.")} com valor manual (${S.manual[k]}).`]);
  if (C.resto > 0) av.push(["erro", `Faltam ${C.resto} pontos de atributo para distribuir.`]);
  if (C.resto < 0) av.push(["erro", `Você gastou ${-C.resto} pontos de atributo a mais.`]);
  const faltIni = R.VALORES_INICIAIS.filter((x) => !ini.includes(x));
  if (faltIni.length) av.push(["erro", `Distribuição inicial incompleta (faltam ${faltIni.join(", ")}).`]);
  if (S.vida.modo === "rolar" && (S.vida.rolagens || []).length < nVida) av.push(["erro", `Role ${nVida - S.vida.rolagens.length} dado(s) de vida novo(s).`]);
  if (treinadas.size > d.pericias_treinadas_max) av.push(["erro", `Perícias treinadas: ${treinadas.size} de ${d.pericias_treinadas_max}.`]);
  else if (treinadas.size < d.pericias_treinadas_max) av.push(["info", `Pode treinar mais ${d.pericias_treinadas_max - treinadas.size} perícia(s).`]);
  const usados = S.encantamentos.filter((x) => x.equipado && ENC[x.familia]).reduce((s, x) => s + ENC[x.familia].espaco, 0);
  C.espUsados = usados;
  if (usados > d.espacos_encant) av.push(["erro", `Encantamentos equipados ocupam ${usados} de ${d.espacos_encant} espaços.`]);
  if (lentidao) av.push(["erro", `Carga ${carga} de ${d.carga}: Lentidão (movimento 6 m).`]);
  if (exaustao) av.push(["erro", "Carga: 10 ou menos espaços livres — Exaustão."]);
  const nTal = S.talismas.filter((t) => t.nome).length;
  if (nTal > d.talismas) av.push(["erro", `Talismãs: ${nTal} equipados, limite ${d.talismas}.`]);
  S.armas.forEach((w, i) => { const f = w.grupo && ARMAS[w.grupo] ? statusArma(C, w.grupo, int(w.nivel, 1)) : []; if (f.length) av.push(["erro", `Arma ${i + 1} (${w.grupo}): ${f.join(", ")}.`]); });
  for (const tipo of ["armadura", "escudo"]) { const it = protecao(tipo); if (it) { const m = statusProtecao(C, tipo, it); if (m.length) av.push(["erro", `${it.nome}: ${m.join(", ")}.`]); } }
  for (const sl of SLOTS) {
    const ativo = sl === "extra" ? tal.has("Versátil") : int(sl) <= nv;
    const nome = S.talentos[sl];
    if (nome && TAL[nome]) { const m = statusTal(C, TAL[nome], sl); if (m.length) av.push(["erro", `Talento ${nome}: ${m.join(", ")}.`]); }
    else if (ativo) av.push(["erro", `Talento do nível ${sl === "extra" ? "extra (Versátil)" : sl} não escolhido.`]);
  }
  for (const x of S.encantamentos) {
    const e = ENC[x.familia]; if (!e) continue;
    const prox = e.versoes.find((v) => !x.versoes.includes(v.nivel));
    if (prox && !R.statusVersao(prox, e.dominio, a, nv).length) av.push(["info", `${e.nome}: versão nível ${prox.nivel} já pode ser aprendida.`]);
  }
  return C;
}
function statusArma(C, grupo, nv) {
  const m = [];
  if (nv > C.d.max_nivel_arma) m.push(`nível de personagem ${2 * nv - 1}`);
  return m.concat(R.reqFalta(R.reqArma(ARMAS[grupo], nv), C.a));
}
function statusProtecao(C, tipo, it) {
  const m = [], forca = Math.max(R.cap(C.a.FOR), R.cap(C.a.TEN));
  if (it.req && forca < it.req) m.push(`${it.req} de Força ou Tenacidade`);
  if (tipo === "armadura" && !S.equip.peitoral_set && C.nv < it.nivel) m.push(`nível ${it.nivel}`);
  if (tipo === "escudo") {
    if (armasEq().length >= 2) m.push("as duas mãos estão com armas");
    if (armasEq().includes("Lança-Arma")) m.push("Lança-Arma já tem escudo");
  }
  return m;
}
function statusTal(C, t, slot) {
  const idx = SLOTS.indexOf(slot);
  let antes = new Set(SLOTS.slice(0, idx).map((s) => S.talentos[s]).filter(Boolean));
  if (slot === "extra") antes = new Set(SLOTS.slice(0, -1).filter((s) => int(s) <= C.nv).map((s) => S.talentos[s]).filter(Boolean));
  const outros = new Set(SLOTS.filter((s) => s !== slot).map((s) => S.talentos[s]).filter(Boolean));
  const m = R.statusTalento(t, slot === "extra" ? 8 : int(slot), antes, C.a, C.treinadas, armasEq(), outros);
  if (slot !== "extra" && int(slot) > C.nv) m.unshift(`slot do nível ${slot}`);
  return m;
}
const ordenar = (lista) => lista.filter((x) => !x.motivo.length).concat(lista.filter((x) => x.motivo.length));

// ------------------------------------------------------------------ interface: helpers
function secao(t, extra = "") { return `<div class="secao">${esc(t)}${extra ? `<span class="extra">${extra}</span>` : ""}</div>`; }
function caixa(t, v, sub, cor = "var(--c-atr)") { return `<div class="cartao caixa"><div class="faixa" style="background:${cor}">${esc(t)}</div><b>${v}</b><small>${sub || "&nbsp;"}</small></div>`; }
let timerToast;
function toast(msg, ms) { const t = $("#toast"); t.innerHTML = msg; t.classList.add("on"); clearTimeout(timerToast); timerToast = setTimeout(() => t.classList.remove("on"), ms || (msg.includes("<hr>") ? 6000 : 3200)); }
function folha(titulo, corpo, rodape = "", aoMontar) {
  $("#folha-tit").textContent = titulo;
  $("#folha-corpo").innerHTML = corpo;
  $("#folha-rod").innerHTML = rodape;
  $("#folha-rod").classList.toggle("oculto", !rodape);
  $("#folha").classList.add("on"); $("#veu").classList.add("on");
  $("#folha-corpo").scrollTop = 0;
  if (aoMontar) aoMontar($("#folha-corpo"));
}
function fecharFolha() { $("#folha").classList.remove("on"); $("#veu").classList.remove("on"); pickerAtual = null; }

/* Seletor genérico: itens [{id,nome,sub,motivo[],busca}] — permitidos primeiro */
let pickerAtual = null;
function seletor(cfg) {
  pickerAtual = cfg;
  const filtros = (cfg.filtros || []).map((f) => `<select data-filtro="${f.chave}">${f.opcoes.map((o) => `<option ${o === f.valor ? "selected" : ""}>${esc(o)}</option>`).join("")}</select>`).join("");
  folha(cfg.titulo, `${cfg.busca === false ? "" : `<input class="busca" id="sel-busca" placeholder="Buscar…" value="${esc(cfg.texto || "")}">`}
    ${filtros ? `<div class="filtros">${filtros}</div>` : ""}<div class="contagem" id="sel-cont"></div><div class="lista" id="sel-lista"></div>`, "", (c) => {
    const b = $("#sel-busca", c); if (b) b.addEventListener("input", () => { cfg.texto = b.value; listarSeletor(); });
    c.querySelectorAll("[data-filtro]").forEach((s) => s.addEventListener("change", () => { cfg.filtros.find((f) => f.chave === s.dataset.filtro).valor = s.value; listarSeletor(); }));
    listarSeletor();
  });
}
function listarSeletor() {
  const cfg = pickerAtual; if (!cfg) return;
  const txt = (cfg.texto || "").trim().toLowerCase();
  let itens = cfg.itens(Object.fromEntries((cfg.filtros || []).map((f) => [f.chave, f.valor])));
  if (txt) itens = itens.filter((i) => (i.nome + " " + (i.busca || "")).toLowerCase().includes(txt));
  itens = ordenar(itens);
  const nOk = itens.filter((i) => !i.motivo.length).length;
  $("#sel-cont").textContent = `${itens.length} itens · ${nOk} disponíveis`;
  $("#sel-lista").innerHTML = (cfg.extraTopo || "") + (itens.length ? itens.slice(0, 400).map((i) => `<div class="item ${i.motivo.length ? "bloq" : ""}" data-a="sel-item" data-id="${esc(i.id)}">
      <span class="marca ${i.motivo.length ? "erro" : "ok"}">${i.motivo.length ? NO : OK}</span>
      <div class="tx"><b>${esc(i.nome)}</b><small>${esc(i.motivo.length ? i.motivo.join(" · ") : i.sub || "")}</small></div>
      ${cfg.detalhe ? `<span class="sub">›</span>` : ""}</div>`).join("") : `<div class="vazio-msg">Nada encontrado.</div>`);
}
function itemSeletor(id) {
  const cfg = pickerAtual; if (!cfg) return;
  if (id === "__nenhum") { cfg.escolher(""); fecharFolha(); return; }
  const it = cfg.itens(Object.fromEntries((cfg.filtros || []).map((f) => [f.chave, f.valor]))).find((x) => String(x.id) === String(id));
  if (!it) return;
  if (cfg.detalhe) {
    const volta = cfg;
    folha(it.nome, cfg.detalhe(it.id) + (it.motivo.length ? `<p class="erro"><b>Ainda não dá:</b> ${esc(it.motivo.join(", "))}</p>` : ""),
      `<button class="botao leve" data-a="sel-voltar">‹ Voltar</button><button class="botao prim" data-a="sel-ok" data-id="${esc(it.id)}" ${it.motivo.length ? "disabled" : ""}>${esc(cfg.rotuloOk || "Escolher")}</button>`);
    pickerAtual = volta;
    return;
  }
  if (it.motivo.length) { toast(`<b>${esc(it.nome)}</b>: ${esc(it.motivo.join(", "))}`); return; }
  cfg.escolher(it.id); fecharFolha();
}

// ------------------------------------------------------------------ render
function render() {
  aplicarTema();
  const vazio = !S;
  $("#nav").classList.toggle("oculto", vazio);
  $("#nivel").classList.toggle("oculto", vazio);
  if (vazio) { document.documentElement.classList.remove("jogo"); $("#t-nome").textContent = "Prevalecentes"; $("#t-sub").textContent = "Ficha de mesa"; $("#pagina").innerHTML = telaInicial(); pintarSessao(); return; }
  C = calcular();
  $("#t-nome").textContent = S.identidade.nome || "Sonhador sem nome";
  $("#t-sub").innerHTML = C.resto ? `<span style="color:#f0a08c">${C.resto > 0 ? `faltam ${C.resto} pontos` : `excedeu ${-C.resto}`}</span>` : (S.identidade.especie || "") + (S.sem_alma ? " · sem alma" : "");
  $("#nv").textContent = `Nv ${C.nv}`;
  document.documentElement.classList.toggle("jogo", banco.modo !== "edicao");
  document.querySelectorAll("#nav button").forEach((b) => b.classList.toggle("on", b.dataset.aba === aba));
  const faixa = banco.modo === "edicao"
    ? `<div class="faixa-modo ed"><span>✎ <b>Modo Edição</b> — criar, subir de nível, escolher e aprender</span><button data-a="modo">⚔ Jogar</button></div>`
    : `<div class="faixa-modo"><span>⚔ <b>Modo Jogo</b> — rolar, gastar e anotar na mesa</span><button data-a="modo">✎ Editar</button></div>`;
  $("#pagina").innerHTML = faixa + { ficha: pFicha, combate: pCombate, pericias: pPericias, grimorio: pGrimorio, talentos: pTalentos, bolsa: pBolsa }[aba]();
  pintarSessao();
}
function aplicarTema() { document.documentElement.classList.toggle("noite", banco.tema === "noite"); }

function telaInicial() {
  const ids = Object.keys(banco.fichas);
  return `<div class="capa"><div class="orn">❦</div><h1>Prevalecentes</h1><p class="sub">Ficha de mesa · edição 3.1</p></div>
    ${secao("Suas fichas")}
    ${ids.length ? `<div class="lista">${ids.map((id) => { const f = banco.fichas[id]; return `<div class="item" data-a="abrir" data-id="${id}"><div class="tx"><b>${esc(f.identidade.nome || "Sem nome")}</b><small>Nível ${f.identidade.nivel} · ${esc(f.identidade.especie || "—")}${f.sem_alma ? " · sem alma" : ""}</small></div><span class="sub">›</span></div>`; }).join("")}</div>`
      : `<div class="vazio-msg">Nenhuma ficha neste aparelho ainda.</div>`}
    <div class="linhabts"><button class="botao prim" data-a="nova">✦ Nova ficha</button><button class="botao leve" data-a="importar">Abrir arquivo .json</button></div>
    <p class="sub" style="margin-top:14px">Abra aqui o mesmo arquivo .json do programa de PC. As fichas ficam guardadas neste aparelho; use “Exportar” no menu para levar de volta ao PC.</p>`;
}

function pFicha() {
  const d = C.d, v = S.vida;
  const vital = (nome, cor, chave, max) => {
    const atual = v[chave] === "" || v[chave] == null ? max : int(v[chave], max);
    const pct = Math.max(0, Math.min(100, (atual / Math.max(1, max)) * 100));
    return `<div class="cartao vital"><div class="rot" style="background:${cor}">${nome}</div>
      <div class="val" data-a="editar-vital" data-chave="${chave}" data-max="${max}"><b>${atual}</b> <small>/ ${max}${(chave === "atual" && S.manual.vida != null) || (chave === "mana_atual" && S.manual.mana != null) ? " ✎" : ""}</small><div class="barra"><i style="width:${pct}%;background:${cor}"></i></div></div>
      <div class="passos"><button data-a="vital" data-chave="${chave}" data-d="-1" data-max="${max}">−</button><button data-a="vital" data-chave="${chave}" data-d="1" data-max="${max}">+</button></div></div>`;
  };
  const falta = Math.max(0, C.nVida - (v.rolagens || []).length);
  let h = secao("Vigor do corpo") + `<div class="vitais">${vital("VIDA", "var(--c-vida)", "atual", d.vida)}${vital("MANA", "var(--c-mana)", "mana_atual", d.mana)}${vital("VIGOR", "var(--c-vigor)", "vigor_atual", d.vigor)}</div>
    <p class="sub" style="margin:8px 2px">Vigor recupera ${d.vigor_regen}/turno · Dados de vida: ${C.nVida}d12 ${v.modo === "media" ? "(média 7)" : `(rolados: ${Math.min(v.rolagens.length, C.nVida)})`}
    <span class="so-ed">· <a href="#" data-a="modo-vida" style="color:var(--vinho)">${v.modo === "media" ? "usar rolagem" : "usar média"}</a>
    ${v.modo === "rolar" && falta ? ` · <a href="#" data-a="rolar-vida" style="color:var(--vinho);font-weight:700">🎲 rolar ${falta}d12</a>` : ""}</span></p>`;
  h += `<div class="grade g3 g4m">${caixa("CA", d.ca, `TEN +${d.ca_ten}`, "var(--c-ca)")}${caixa("Movimento", `${C.mov} m`, `${Math.round(C.mov / 1.5)} quadrados${C.lentidao ? " · lento" : ""}`, "var(--c-mov)")}
    ${caixa("Iniciativa", `+${d.iniciativa_bonus}`, `${d.iniciativa_dados}d20, o maior`)}${caixa("Ações extras", d.acoes_extras, C.exaustao ? "Exaustão" : "por DES")}
    ${caixa("Carga", `${C.carga}/${d.carga}`, C.lentidao ? "Lentidão" : "atual / máx.")}${caixa("Red. dano", d.rd ? `${d.rd}d4` : "—", "por TEN")}
    ${caixa("Descoberta", d.descoberta, "por Arcano")}${caixa("Talismãs", `${S.talismas.filter((t) => t.nome).length}/${d.talismas}`, "espaços", "var(--c-tal)")}</div>`;
  h += secao("Atributos", `${C.gastos}/${C.disp} pontos de nível`) + `<div class="grade g2 g4m">${R.ATRIBUTOS.map((k) => {
    const val = C.a[k], x = S.atributos[k];
    return `<div class="cartao atr"><div class="faixa" style="background:var(--c-atr);color:var(--ouro2)">${R.NOMES_ATR[k]}</div>
      <div class="total ${val > 99 ? "erro" : ""}" data-a="manual" data-k="${k}">${val}${S.manual[k] != null ? `<span style="font-size:14px;color:var(--vinho)"> ✎</span>` : ""}</div><div class="info">Curva ${d.curva[k]} · BC +${d.bc[k]} · ${1 + Math.floor(R.cap(val) / 20)}d20${R.vantagem(val) ? ` · <span class="vant">vant.</span>` : ""}</div>
      <div class="info" style="font-size:11px">ini ${x.inicial || "—"} · esp ${int(x.especie) >= 0 ? "+" : ""}${int(x.especie)}${C.tb[k] ? ` · talismã +${C.tb[k]}` : ""}${int(x.bonus) ? ` · bôn ${int(x.bonus)}` : ""}</div>
      <div class="ctrl so-ed"><button data-a="pts" data-k="${k}" data-d="-1">−</button><span>nível +${int(x.niveis)}</span><button data-a="pts" data-k="${k}" data-d="1">+</button></div></div>`;
  }).join("")}</div>`;
  const erros = C.avisos.filter((a) => a[0] === "erro"), infos = C.avisos.filter((a) => a[0] !== "erro");
  h += secao("Avisos do escriba") + `<div class="lista"><ul class="avisos">${erros.length ? "" : `<li class="tudo">Nada pendente na ficha.</li>`}${erros.concat(infos).map(([t, m]) => `<li class="${t}">${esc(m)}</li>`).join("")}</ul></div>`;
  return h;
}

function linhaArma(i) {
  const w = S.armas[i], ar = ARMAS[w.grupo];
  let h = `<div class="cartao arma a${i}"><div class="linha1"><span style="font-family:var(--tit);color:var(--vinho);width:22px">${i ? "II" : "I"}</span>
    <button class="sel ${ar ? "" : "vazio"}" data-a="esc-arma" data-i="${i}">${ar ? esc(w.grupo) : "Escolher arma"}</button>
    ${ar ? `<button class="sel" style="width:96px" data-a="esc-nivel-arma" data-i="${i}">Nv ${int(w.nivel, 1)}</button>` : ""}</div>`;
  if (!ar) return h + "</div>";
  const nv = int(w.nivel, 1), l = ar.tabela.find((x) => x.nivel === nv) || ar.tabela[0], k = ar.ataque;
  const extra = Math.floor(R.cap(C.a[k]) / 30), acerto = C.d.bc[k] + C.d.n3 + (R.ACERTO_ARMA[nv] || 0) + C.ef.acerto;
  const vig = ar.vigor ? (nv >= 8 ? 10 : nv >= 4 ? 8 : 5) : "—";
  const falta = statusArma(C, w.grupo, nv);
  h += `<dl><div><dt>Dano</dt><dd>${esc(R.danoComDados(l.dano, extra))}</dd></div><div><dt>Ataque</dt><dd>1d20 +${acerto}${R.vantagem(C.a[k]) ? " (vant.)" : ""}</dd></div>
    <div><dt>Crítico</dt><dd>${esc(l.critico)}</dd></div><div><dt>Tipo</dt><dd>${esc(l.tipo)}</dd></div><div><dt>DT</dt><dd>${10 + C.d.bc[k] + C.d.n3}</dd></div>
    <div><dt>Vigor/atk</dt><dd>${vig}</dd></div></dl>
    <div class="sub">${k} · ${l.propriedades} propriedade(s) · peso ${l.espaco}${extra ? ` · +${extra} dado de dano por ${k}` : ""}</div>
    ${falta.length ? `<div class="erro" style="font-size:13.5px;margin-top:4px">${NO} falta: ${esc(falta.join(", "))}</div>` : ""}
    <div class="linhabts"><button class="botao prim" data-a="rolar-arma" data-i="${i}">🎲 Atacar</button></div>
    <details class="acoes"><summary>Ações da arma (${(ar.acoes || []).length})</summary>
    ${ar.descricao ? `<p class="sub">${esc(ar.descricao)}</p>` : ""}
    ${(ar.acoes || []).map((x) => `<div class="acao ${x.sub ? "sub" : ""}"><b>${x.sub ? "↳ " : ""}${esc(x.nome)}</b> — ${esc(x.texto)}</div>`).join("")}</details></div>`;
  return h;
}
function textoEfeitos() {
  const partes = [];
  for (const nome of [...C.tal].sort()) {
    const e = R.EFEITOS_TALENTOS[nome]; if (!e || (e.tipo === "sit" && !C.ativos.has(nome))) continue;
    const bits = [["ca", "CA"], ["mov", "m"], ["acerto", "acerto"], ["iniciativa", "iniciativa"], ["descoberta", "Descoberta"], ["contra", "contra-encant."], ["dt_alma", "DT alma"], ["dano_nivel", "nível de dano"]]
      .filter(([k]) => e[k]).map(([k, r]) => `+${e[k]} ${r}`).concat(Object.entries(e.pericia || {}).map(([p, v]) => `+${v} ${p}`));
    partes.push(`<b>${esc(nome)}</b>${e.tipo === "sit" ? " (ativo)" : ""}: ${bits.join(", ")}`);
  }
  return partes;
}
function pCombate() {
  const d = C.d;
  const ef = textoEfeitos();
  let h = secao("Rolar") + `<div class="linhabts" style="margin-top:0"><button class="botao prim" data-a="rolar-ini">🎲 Iniciativa</button>
    <button class="botao" data-a="conjurar-menu">✧ Conjurar</button><button class="botao leve" data-a="diario">📜 Diário</button></div>
    ${sessao.efeitos.length ? `<div class="lista mestre">${sessao.efeitos.map((e) => `<div class="item"><span class="marca">⏳</span><div class="tx"><b>${esc(e.nome)}</b><small>${e.rodadas ? `${e.rodadas} rodada(s)` : "até o mestre remover"}${e.desc ? " · " + esc(e.desc) : ""}</small></div></div>`).join("")}</div>` : ""}
    <p class="sub">${ef.length ? "Talentos em uso: " + ef.join(" · ") : "Nenhum efeito de talento em uso. Situacionais: aba Talentos → \"ativo agora\"."}</p>`;
  h += secao("Ataque") + `<div class="lista"><div class="cab" style="background:var(--c-atk)">Perícia<span style="flex:1"></span>Bônus</div>${R.PERICIAS_ATAQUE.map(([n, atrs]) =>
    `<div class="item"><div class="tx"><b>${n}</b><small>${atrs.join(" ou ")}</small></div><span class="num">${atrs.map((k) => `+${d.bc[k] + d.n3 + (n === "Luta" || n === "Pontaria" ? C.ef.acerto : 0)}${R.vantagem(C.a[k]) ? "ᵛ" : ""}`).join(" / ")}</span></div>`).join("")}</div>`;
  h += secao("Defesa") + `<div class="lista"><div class="cab" style="background:var(--c-def)">Perícia<span style="flex:1"></span>Bônus</div>${R.PERICIAS_DEFESA.map(([n, k, tn]) =>
    `<div class="item"><div class="tx"><b>${n}</b><small>${k}</small></div><span class="num">+${d.bc[k] + d.n3 + (C.tal.has(tn) ? 2 : 0)}${R.vantagem(C.a[k]) ? "ᵛ" : ""}</span></div>`).join("")}</div>
    <p class="sub">ᵛ = vantagem (2d20). DT: Feitiçaria ${d.dt_feiticaria} · Desejo ${d.dt_desejo}</p>`;
  h += secao("Armas") + linhaArma(0) + linhaArma(1);
  const w0 = ARMAS[S.armas[0].grupo], w1 = ARMAS[S.armas[1].grupo];
  if (w0 && w1) {
    if (!w0.uso_duplo || !w1.uso_duplo) h += `<p class="erro">${NO} ${!w0.uso_duplo ? w0.nome : w1.nome} não permite uso duplo.</p>`;
    else {
      const rq = R.reqUsoDuplo(R.reqArma(w0, int(S.armas[0].nivel, 1)), R.reqArma(w1, int(S.armas[1].nivel, 1)));
      const f = R.reqFalta(rq, C.a);
      h += `<p class="${f.length ? "erro" : "sub"}">Uso duplo: ${Object.entries(rq).map(([k, v]) => `${v} ${k}`).join(", ")} ${f.length ? `— falta ${f.join(", ")}` : OK}.
        Coordenação: 1d20 +${d.bc.DES + d.n3}${C.tal.has("Mãos Gêmeas") ? " +2" : ""} contra DT ${8 + Math.max(int(S.armas[0].nivel, 1), int(S.armas[1].nivel, 1))}.</p>`;
    }
  }
  h += secao("Proteção") + ["armadura", "escudo"].map((t) => {
    const it = protecao(t), m = it ? statusProtecao(C, t, it) : [];
    return `<div style="margin-bottom:8px"><button class="sel ${it ? "" : "vazio"}" data-a="esc-protecao" data-t="${t}">${it ? `${esc(it.nome)} · CA +${it.ca} · peso ${it.peso}` : t === "armadura" ? "Sem armadura" : "Sem escudo"}</button>
      ${m.length ? `<div class="erro" style="font-size:13.5px;margin:3px 2px">${NO} ${esc(m.join(", "))}</div>` : ""}</div>`;
  }).join("") + `<p class="sub">CA ${d.ca} = 10 + armadura ${C.arm ? C.arm.ca : 0} + escudo ${C.esc ? C.esc.ca : 0} + Tenacidade ${d.ca_ten}${int(S.equip.ca_extra) ? ` + outros ${int(S.equip.ca_extra)}` : ""}</p>`;
  h += secao("Talismãs", `${S.talismas.filter((t) => t.nome).length}/${d.talismas}`) + `<div class="lista">${S.talismas.slice(0, Math.max(d.talismas, S.talismas.filter((t) => t.nome).length)).map((t, i) => {
    const info = TALISMA[t.nome];
    return `<div class="item ${i >= d.talismas ? "bloq" : ""}" data-a="esc-talisma" data-i="${i}"><span class="marca" style="color:var(--ouro)">✦</span><div class="tx"><b>${esc(t.nome || "Vazio")}</b><small>${esc(info ? info.efeito : t.nome ? t.efeito : "toque para escolher")}</small></div><span class="sub">›</span></div>`;
  }).join("")}</div>`;
  h += secao("Resistências") + `<div>${R.RESISTENCIAS.map(([lim, n]) => `<span class="chip ${d.resistencias.includes(n) ? "on" : ""}">${d.resistencias.includes(n) ? "☑" : "☐"} ${n} ${lim}</span>`).join("")}</div>`;
  h += secao("Portão da Morte") + ["Sucessos", "Falhas"].map((n) => `<div class="portao"><span class="r" style="background:${n === "Sucessos" ? "var(--c-vigor)" : "var(--c-vida)"}">${n}</span>
    ${S.portao[n].map((on, i) => `<button class="bolinha ${on ? "on" : ""} ${n === "Sucessos" ? "s" : "f"}" data-a="portao" data-n="${n}" data-i="${i}"></button>`).join("")}</div>`).join("")
    + `<p class="sub">d20 no início do turno: 11+ é sucesso. 5 sucessos: volta com 1 de Vida e 1 cicatriz. 5 falhas: morte.</p>`;
  h += secao("Condições") + `<div class="lista">${R.CONDICOES.map((n) => {
    const c = S.condicoes[n] || { atual: "", max: "100" };
    return `<div class="item" data-a="editar-cond" data-n="${n}"><div class="tx"><b>${n}</b>${c.notas ? `<small>${esc(c.notas)}</small>` : ""}</div><span class="num">${int(c.atual)} <span class="sub">/ ${int(c.max, 100)}</span></span></div>`;
  }).join("")}</div>`;
  return h;
}

function pPericias() {
  const d = C.d, n = C.treinadas.size;
  let h = secao("Perícias", `<span class="${n > d.pericias_treinadas_max ? "erro" : ""}">${n}/${d.pericias_treinadas_max} treinadas</span>`)
    + `<div class="lista">${R.PERICIAS.map(([nome, atrs, req]) => {
      const tr = C.treinadas.has(nome), at = atrs || [S.prevalencia_attr || "ARC"];
      const [melhor, bonus0, dados] = R.periciaFora(C.a, C.nv, at, tr);
      const bonus = bonus0 + (C.ef.pericia[nome] || 0);
      return `<div class="item" data-a="treinar" data-n="${esc(nome)}"><span class="check ${tr ? "on" : ""}"></span>
        <div class="tx"><b>${esc(nome)}${req ? " •" : ""}</b><small>${atrs ? atrs.join("/") : `Prevalência usa ${at[0]}`} · ${dados}d20</small></div><span class="num">+${bonus}</span></div>`;
    }).join("")}</div><p class="sub">• exige treino. Bônus = nível ÷ 2, mais a Curva do atributo se treinada.</p>`;
  h += secao("Perícia de ataque treinada") + `<div>${R.PERICIAS_ATAQUE.map(([nn]) => `<span class="chip ${S.pericia_ataque === nn ? "on" : ""}" data-a="per-atk" data-n="${nn}">${nn}</span>`).join("")}</div>`;
  h += secao("Atributo da Prevalência") + `<div>${R.ATRIBUTOS.map((k) => `<span class="chip ${S.prevalencia_attr === k ? "on" : ""}" data-a="prev-attr" data-k="${k}">${k}</span>`).join("")}</div>`;
  return h;
}

function pGrimorio() {
  const d = C.d;
  let h = secao("Grimório") + `<div class="grade g3">${caixa("Espaços", `${C.espUsados}/${d.espacos_encant}`, "equipados", "var(--c-mana)")}
    ${caixa("DT", `${d.dt_feiticaria}/${d.dt_desejo}`, "Feitiçaria / Desejo")}${caixa("Dados extras", `+${d.dados_extra_magia}/+${d.dados_extra_feitico}`, "Magia / Feitiço")}</div>`;
  h += `<div class="linhabts so-ed" style="margin-bottom:10px"><button class="botao prim" data-a="aprender">✦ Aprender encantamento</button></div>`;
  if (!S.encantamentos.length) return h + `<div class="vazio-msg">Nenhum encantamento aprendido.</div>`;
  const impl = (dom) => Math.max(0, ...S.armas.filter((w) => w.grupo === (dom === "Magia" ? "Cajado" : "Selo")).map((w) => int(w.nivel, 1)));
  h += `<div class="lista">${S.encantamentos.map((x, i) => {
    const e = ENC[x.familia]; if (!e) return "";
    const vs = e.versoes.filter((v) => x.versoes.includes(v.nivel)), top = vs[vs.length - 1] || e.versoes[0];
    const ni = impl(e.dominio), conj = ni >= top.nivel;
    return `<div class="item" data-a="ver-enc" data-i="${i}"><span class="check ${x.equipado ? "on" : ""}" data-a="equipar" data-i="${i}"></span>
      <div class="tx"><b>${esc(e.nome)}</b><small>${e.dominio} · nv ${x.versoes.join(", ")} · ${esc(top.mana)} · esp ${e.espaco}${conj ? "" : ` · ${NO} sem ${e.dominio === "Magia" ? "cajado" : "selo"} nv ${top.nivel}`}</small></div>
      <button class="passos" style="border:0;background:none;padding:0" data-a="conjurar" data-f="${esc(e.nome)}" data-v="${top.nivel}"><span class="botao prim" style="min-height:38px;padding:6px 12px">🎲</span></button></div>`;
  }).join("")}</div><p class="sub">Marque a caixa para equipar. Toque no nome para ver a descrição.</p>`;
  return h;
}
function descEnc(nome, destaque) {
  const e = ENC[nome]; if (!e) return "";
  const x = S.encantamentos.find((y) => y.familia === nome);
  return `<p class="meta">${e.dominio} · ${esc(e.categoria)} · Espaço ${e.espaco}</p>` + e.versoes.map((v) => {
    const m = R.statusVersao(v, e.dominio, C.a, C.nv, C.nv === 1 && armasEq().some((g) => g === "Cajado" || g === "Selo"));
    const ja = x && x.versoes.includes(v.nivel);
    return `<div class="desc"><h4>${esc(v.tier)} — Nível ${v.nivel} <span class="${ja || !m.length ? "ok" : "erro"}" style="font-size:13px">${ja ? "· aprendida" : m.length ? "· " + esc(m.join(", ")) : "· pode aprender"}</span></h4>
      <div class="meta">Mana ${esc(v.mana)} · Ação ${esc(v.acao)} · Distância ${esc(v.distancia)}<br>Requisitos: ${esc(v.req_texto)}</div>${esc(v.descricao)}</div>`;
  }).join("");
}

function pTalentos() {
  let h = secao("Talentos", "um a cada nível par") + `<div class="lista">${SLOTS.map((sl) => {
    const ativo = sl === "extra" ? C.tal.has("Versátil") : int(sl) <= C.nv;
    if (sl === "extra" && !ativo && !S.talentos.extra) return "";
    const nome = S.talentos[sl], t = TAL[nome], m = t ? statusTal(C, t, sl) : [];
    const eft = R.EFEITOS_TALENTOS[nome];
    const sw = eft && eft.tipo === "sit" ? `<span class="chip ${C.ativos.has(nome) ? "on" : ""}" style="margin:0" data-a="tal-ativo" data-n="${esc(nome)}">${C.ativos.has(nome) ? "ativo" : "inativo"}</span>` : "";
    const tag = eft ? (eft.tipo === "perm" ? "✓ aplicado · " : `situacional${eft.nota ? " (" + eft.nota + ")" : ""} · `) : "";
    return `<div class="item ${ativo ? "" : "bloq"}" data-a="esc-talento" data-s="${sl}"><span class="marca" style="font-family:var(--tit);color:var(--vinho);width:34px">${sl === "extra" ? "✦" : sl}</span>
      <div class="tx"><b class="${m.length ? "erro" : ""}">${esc(nome || (ativo ? "Escolher talento" : "—"))}</b><small>${esc(t ? (m.length ? NO + " " + m.join(", ") : tag + t.descricao) : ativo ? "toque para escolher" : `liberado no nível ${sl}`)}</small></div>${sw || `<span class="sub">›</span>`}</div>`;
  }).join("")}</div>`;
  h += secao("Vínculos") + `<div class="lista">${[["grupo", "Com o grupo"], ["mundo", "Com o mundo"], ["metas", "Metas de vida"]].map(([k, r]) =>
    `<div class="item" data-a="editar-vinc" data-k="${k}"><div class="tx"><b>${r}</b><small>${esc(S.vinculos[k] || "toque para escrever")}</small></div></div>`).join("")}</div>`;
  return h;
}

// ------------------------------------------------------------------ ações
const A = {};

function setsAtivos() {
  const cont = {};
  for (const p of PECAS) { const n = (S.set[p] || {}).set; if (n && SETS[n]) cont[n] = (cont[n] || 0) + 1; }
  return cont;
}
function pBolsa() {
  const d = C.d, itens = S.inventario;
  const pesoItens = itens.reduce((t, i) => t + (parseFloat(String(i.carga || 0).replace(",", ".")) || 0), 0);
  const pesoArmas = S.armas.reduce((t, w) => { const ar = ARMAS[w.grupo]; const l = ar && ar.tabela.find((x) => x.nivel === int(w.nivel, 1)); return t + (l ? l.espaco : 0); }, 0);
  const pesoProt = (C.arm ? C.arm.peso : 0) + (C.esc ? C.esc.peso : 0) - (C.tal.has("Veterano de Armadura") && C.arm ? 2 : 0);
  const pesoTal = S.talismas.filter((t) => t.nome).length;
  const pct = Math.max(0, Math.min(100, (C.carga / Math.max(1, d.carga)) * 100));
  const cor = C.carga > d.carga || C.lentidao ? "var(--c-vida)" : C.exaustao ? "var(--c-per)" : "var(--c-vigor)";
  let h = secao("Carga", `${C.carga} / ${d.carga}`) + `<div class="cartao" style="padding:12px">
    <div class="barra grossa"><i style="width:${pct}%;background:${cor}"></i></div>
    <p class="sub" style="margin:8px 0 0">Itens ${pesoItens} · armas ${pesoArmas} · proteção ${pesoProt} · talismãs ${pesoTal}
    ${C.lentidao ? `<br><b class="erro">Lentidão</b>: movimento preso em 6 m.` : C.exaustao ? `<br><b class="erro">Exaustão</b>: 10 ou menos de carga livre.` : ""}</p></div>`;
  h += `<div class="cartao dinheiro" data-a="dinheiro"><span>Dinheiro</span><b>${esc(S.dinheiro || "—")}</b><small>toque para mudar</small></div>`;
  h += secao("Itens", `${itens.length}/30`) + (itens.length ? `<div class="lista">${itens.map((it, i) =>
    `<div class="item" data-a="item" data-i="${i}"><span class="marca" style="color:var(--ouro)">◆</span><div class="tx"><b>${esc(it.item || "Sem nome")}</b></div><span class="num">${esc(it.carga || "0")}</span></div>`).join("")}</div>`
    : `<div class="vazio-msg">A bolsa está vazia.</div>`)
    + `<div class="linhabts"><button class="botao prim" data-a="item" data-i="-1" ${itens.length >= 30 ? "disabled" : ""}>＋ Adicionar item</button></div>`;
  const cont = setsAtivos();
  h += secao("Peças de set") + `<div class="lista">${PECAS.map((p) => {
    const x = S.set[p] || {};
    return `<div class="item" data-a="peca" data-p="${p}"><div class="tx"><b>${p}</b><small>${x.set && SETS[x.set] ? `Set ${esc(x.set)}${x.nome ? " · " + esc(x.nome) : ""}` : x.nome ? esc(x.nome) : "sem peça de set"}</small></div><span class="sub so-ed">›</span></div>`;
  }).join("")}</div>`;
  const at = Object.entries(cont).filter(([, q]) => q >= 2).sort((a, b) => b[1] - a[1]);
  h += at.length ? `<div class="lista">${at.map(([n, q]) => `<div class="item" style="display:block"><b style="color:var(--vinho)">Set ${esc(n)} — ${q} peças</b>
      <div class="sub" style="margin-top:3px"><b>2 peças:</b> ${esc(SETS[n].p2)}${q >= 4 ? `<br><b>4 peças:</b> ${esc(SETS[n].p4)}` : `<br><span style="opacity:.7">4 peças: falta ${4 - q}</span>`}</div></div>`).join("")}</div>`
    : `<p class="sub">Duas peças do mesmo set ativam o bônus de 2; quatro ativam o de 4.</p>`;
  h += secao("Talismãs", `${pesoTal}/${d.talismas}`) + `<p class="sub">${S.talismas.filter((t) => t.nome).map((t) => esc(t.nome)).join(" · ") || "Nenhum equipado."} <a href="#" data-a="aba" data-aba="combate" style="color:var(--vinho)">ver em Combate</a></p>`;
  return h;
}
A["dinheiro"] = () => folha("Dinheiro", `<input class="busca" id="dn" value="${esc(S.dinheiro)}" placeholder="ex.: 35 moedas de prata" style="font-size:20px">`,
  `<button class="botao leve" data-a="fechar">Cancelar</button><button class="botao prim" data-a="dinheiro-ok">Salvar</button>`);
A["dinheiro-ok"] = () => { const v = $("#dn").value.trim(); fecharFolha(); mudar((s) => { s.dinheiro = v; }); };
A["item"] = (el) => {
  const i = int(el.dataset.i, -1), it = S.inventario[i] || { item: "", carga: "" };
  folha(i < 0 ? "Novo item" : "Item", `<label class="campo"><span>Item</span><input id="it-n" value="${esc(it.item)}"></label>
    <label class="campo"><span>Carga</span><input id="it-c" type="number" inputmode="decimal" step="0.5" value="${esc(it.carga)}"></label>`,
  `${i >= 0 ? `<button class="botao leve" data-a="item-rem" data-i="${i}">Remover</button>` : `<button class="botao leve" data-a="fechar">Cancelar</button>`}<button class="botao prim" data-a="item-ok" data-i="${i}">Salvar</button>`);
  setTimeout(() => { const x = $("#it-n"); if (x && i < 0) x.focus(); }, 60);
};
A["item-ok"] = (el) => {
  const i = int(el.dataset.i, -1), n = $("#it-n").value.trim(), c = $("#it-c").value.trim();
  fecharFolha(); if (!n && !c) return;
  mudar((s) => { if (i < 0) s.inventario.push({ item: n, carga: c }); else s.inventario[i] = { item: n, carga: c }; });
};
A["item-rem"] = (el) => { const i = int(el.dataset.i); fecharFolha(); mudar((s) => { s.inventario.splice(i, 1); }); };
A["peca"] = (el) => {
  const p = el.dataset.p, x = S.set[p] || { set: "", nome: "" };
  folha(`Peça: ${p}`, `<label class="campo"><span>Set</span><select id="pc-s"><option value="">— sem set —</option>${Object.keys(SETS).sort().map((n) => `<option ${n === x.set ? "selected" : ""}>${esc(n)}</option>`).join("")}</select></label>
    <label class="campo"><span>Nome da peça</span><input id="pc-n" value="${esc(x.nome)}"></label><p class="sub" id="pc-d"></p>`,
  `<button class="botao leve" data-a="fechar">Cancelar</button><button class="botao prim" data-a="peca-ok" data-p="${p}">Salvar</button>`, (c) => {
    const mostra = () => { const s = SETS[$("#pc-s").value]; $("#pc-d").innerHTML = s ? `<b>2:</b> ${esc(s.p2)}<br><b>4:</b> ${esc(s.p4)}` : ""; };
    c.querySelector("#pc-s").addEventListener("change", mostra); mostra();
  });
};
A["peca-ok"] = (el) => { const p = el.dataset.p, st = $("#pc-s").value, n = $("#pc-n").value.trim(); fecharFolha(); mudar((s) => { s.set[p] = { set: st, nome: n }; }); };

// ------------------------------------------------------------------ modo jogo / edição
const SO_EDICAO = new Set(["nivel", "pts", "manual", "modo-vida", "rolar-vida", "esc-arma", "esc-nivel-arma", "esc-protecao", "esc-talisma",
  "esc-talento", "treinar", "per-atk", "prev-attr", "aprender", "prox-versao", "rem-enc", "ident", "peca", "editar-vinc"]);
A["modo"] = () => {
  banco.modo = banco.modo === "edicao" ? "jogo" : "edicao"; gravarLocal(); fecharFolha(); render();
  toast(banco.modo === "edicao" ? "<b>Modo Edição</b>: suba de nível, escolha talentos, armas e encantamentos." : "<b>Modo Jogo</b>: a ficha fica pronta para a mesa.");
};
A["aba"] = (el) => { aba = el.dataset.aba; render(); window.scrollTo(0, 0); };
A["nivel"] = (el) => {
  const n0 = nivel(), n1 = Math.max(1, Math.min(30, n0 + int(el.dataset.d)));
  if (n1 === n0) return;
  mudar((s) => { s.identidade.nivel = n1; });
  if (n1 > n0) {
    const g = R.ganhoNoNivel(n1, S.sem_alma);
    toast(`<b>Nível ${n1}!</b> +${g} pontos de atributo${n1 % 2 === 0 ? " · novo talento" : ""}${n1 % 3 === 0 && !S.sem_alma ? " · alma sobe" : ""}${n1 % 6 === 0 && n1 <= 24 ? " · +1 talismã" : ""}.`);
  }
};
A["pts"] = (el) => {
  const k = el.dataset.k, dlt = int(el.dataset.d), x = S.atributos[k];
  if (dlt > 0 && C.resto <= 0) { toast("Não há pontos de nível sobrando. Suba de nível para ganhar mais."); return; }
  if (dlt < 0 && int(x.niveis) <= 0) return;
  mudar(() => { x.niveis = String(int(x.niveis) + dlt); });
};
A["vital"] = (el) => mudar((s) => {
  const ch = el.dataset.chave, max = int(el.dataset.max);
  const at = s.vida[ch] === "" || s.vida[ch] == null ? max : int(s.vida[ch], max);
  s.vida[ch] = String(Math.max(0, Math.min(max, at + int(el.dataset.d))));
});
A["editar-vital"] = (el) => {
  const ch = el.dataset.chave, max = int(el.dataset.max), nome = { atual: "Vida", mana_atual: "Mana", vigor_atual: "Vigor" }[ch];
  const at = S.vida[ch] === "" ? max : int(S.vida[ch], max);
  folha(`${nome} atual`, `<input class="busca" id="ev" type="number" inputmode="numeric" value="${at}" style="font-size:28px;text-align:center">
    <div class="grade g3" style="margin-top:6px">${[-10, -5, -1, 1, 5, 10].map((x) => `<button class="botao leve" data-a="ev-somar" data-d="${x}">${x > 0 ? "+" : ""}${x}</button>`).join("")}</div>`,
  `<button class="botao leve" data-a="ev-cheio" data-max="${max}">Cheio (${max})</button><button class="botao prim" data-a="ev-ok" data-chave="${ch}" data-max="${max}">Confirmar</button>`);
  if (ch !== "vigor_atual" && banco.modo === "edicao") $("#folha-corpo").insertAdjacentHTML("beforeend", `<div class="linhabts"><button class="botao leve" data-a="manual" data-k="${ch === "atual" ? "vida" : "mana"}">✎ Mudar o máximo (valor rolado fora da ficha)</button></div>`);
};
A["ev-somar"] = (el) => { const i = $("#ev"); i.value = int(i.value) + int(el.dataset.d); };
A["ev-cheio"] = (el) => { $("#ev").value = el.dataset.max; };
A["ev-ok"] = (el) => { const v = Math.max(0, Math.min(int(el.dataset.max), int($("#ev").value))); fecharFolha(); mudar((s) => { s.vida[el.dataset.chave] = String(v); }); };
A["manual"] = (el) => {
  const k = el.dataset.k, nome = R.NOMES_ATR[k] || (k === "vida" ? "Vida máxima" : "Mana máxima");
  const tmp = Object.assign({}, S.manual); delete tmp[k];
  const salvo = S.manual; S.manual = tmp; const auto = (R.NOMES_ATR[k] ? calcular().a[k] : calcular().d[k]); S.manual = salvo;
  folha(nome, `<p class="sub">Calculado pela ficha: <b>${auto}</b>. Digite o valor que você rolou ou definiu fora da ficha; ele substitui o calculado.</p>
    <input class="busca" id="mv" type="number" inputmode="numeric" value="${S.manual[k] != null ? S.manual[k] : auto}" style="font-size:28px;text-align:center"><p class="erro" id="mv-erro"></p>`,
  `<button class="botao leve" data-a="manual-auto" data-k="${k}">Automático</button><button class="botao prim" data-a="manual-ok" data-k="${k}">Usar valor</button>`);
};
A["manual-ok"] = (el) => {
  const v = $("#mv").value.trim();
  if (!/^\d+$/.test(v)) { $("#mv-erro").textContent = "Digite um número inteiro (0 ou mais)."; return; }
  fecharFolha(); mudar((s) => { s.manual[el.dataset.k] = int(v); });
};
A["manual-auto"] = (el) => { fecharFolha(); mudar((s) => { delete s.manual[el.dataset.k]; }); };
A["tal-ativo"] = (el, ev) => { ev.stopPropagation(); const n = el.dataset.n; mudar((s) => { s.talentos_ativos = s.talentos_ativos.includes(n) ? s.talentos_ativos.filter((x) => x !== n) : s.talentos_ativos.concat([n]); }); };

// ----- rolagens
const diario = [], desfazer = [];
const rng = (f) => 1 + Math.floor(Math.random() * f);
function txtAtaque(at, rot = "Acerto") {
  let t = `${rot}: <b style="font-size:20px">${at.total}</b> <span class="sub">[d20 ${at.d20.join(" e ")}${at.d20.length > 1 ? " → maior" : ""} ${at.bonus >= 0 ? "+" : ""}${at.bonus}]</span>`;
  if (at.desastre) t += `<br><b class="erro">DESASTRE</b>: erra sempre; o alvo pode atacar você como ação livre.`;
  else if (at.garantido) t += `<br><b class="ok">20 NATURAL</b>: acerto garantido e crítico (dobra os dados).`;
  else if (at.critico) t += `<br><b class="ok">CRÍTICO</b>: dobra os dados de dano (o acerto ainda compara com a CA).`;
  return t;
}
const txtDano = (tot, partes, rot = "Dano") => `${rot}: <b style="font-size:20px">${tot}</b> <span class="sub">(${partes.map(([t, v]) => v.length ? `${t}[${v.join(", ")}]` : t).join(" ")})</span>`;
function mostrarRolagem(titulo, linhas) {
  diario.unshift({ titulo, linhas, hora: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }) });
  folha(titulo, `<div class="desc" style="font-size:16px;line-height:1.7">${linhas.join("<br>")}</div>`,
    `${desfazer.length ? `<button class="botao leve" data-a="desfazer">↺ Desfazer custo</button>` : ""}<button class="botao prim" data-a="fechar">OK</button>`);
}
/* Desconta custo; se faltar recurso, pergunta antes de rolar. cont(textoCusto) faz a rolagem. */
function pagar(chave, max, custo, rotulo, cont) {
  if (!custo) { cont(""); return; }
  const atual = S.vida[chave] === "" || S.vida[chave] == null ? max : int(S.vida[chave], max);
  if (atual < custo) {
    pendente = () => cont(`${rotulo}: não descontado (tinha ${atual}, custa ${custo})`);
    folha(`${rotulo} insuficiente`, `<p>Você tem <b>${atual}</b> de ${rotulo} e precisa de <b>${custo}</b>.</p>`,
      `<button class="botao leve" data-a="fechar">Cancelar</button><button class="botao prim" data-a="pendente">Rolar sem descontar</button>`);
    return;
  }
  desfazer.push({ chave, antigo: S.vida[chave], desc: `${custo} de ${rotulo}` });
  S.vida[chave] = String(atual - custo); salvar(); render();
  cont(`${rotulo}: −${custo} (restam ${atual - custo})`);
}
let pendente = null;
A["pendente"] = () => { const f = pendente; pendente = null; fecharFolha(); if (f) f(); };
A["desfazer"] = () => {
  const u = desfazer.pop(); if (!u) return;
  fecharFolha(); mudar((s) => { s.vida[u.chave] = u.antigo; });
  toast(`↺ Devolvido: ${esc(u.desc)}.`);
};
A["rolar-arma"] = (el) => {
  const i = int(el.dataset.i), w = S.armas[i], ar = ARMAS[w.grupo]; if (!ar) return;
  const nv = int(w.nivel, 1), k = ar.ataque, nvD = Math.min(10, nv + C.ef.dano_nivel);
  const l = ar.tabela.find((x) => x.nivel === nv), lD = ar.tabela.find((x) => x.nivel === nvD) || l;
  const bonus = C.d.bc[k] + C.d.n3 + (R.ACERTO_ARMA[nv] || 0) + C.ef.acerto;
  const vig = ar.vigor ? (nv >= 8 ? 10 : nv >= 4 ? 8 : 5) : 0;
  pagar("vigor_atual", C.d.vigor, vig, "Vigor", (custo) => {
    const at = R.rolarAtaque(bonus, R.vantagem(C.a[k]), int(l.critico, 20), rng);
    const linhas = [txtAtaque(at)];
    if (!at.desastre) {
      const [tot, partes] = R.rolarExpr(R.danoComDados(lD.dano, Math.floor(R.cap(C.a[k]) / 30)), rng, at.critico);
      linhas.push(txtDano(tot, partes) + ` · ${esc(lD.tipo)}` + (nvD !== nv ? ` · dano de nível ${nvD} (talento)` : ""));
    }
    if (custo) linhas.push(`<span class="sub">${custo}</span>`);
    if (C.ef.acerto) linhas.push(`<span class="sub">Inclui +${C.ef.acerto} de acerto de talento situacional.</span>`);
    mostrarRolagem(`⚔ ${ar.nome} nv ${nv}`, linhas);
  });
};
A["rolar-ini"] = () => {
  const d = [...Array(C.d.iniciativa_dados)].map(() => rng(20)), b = C.d.iniciativa_bonus;
  mostrarRolagem("⏳ Iniciativa", [`Iniciativa: <b style="font-size:20px">${Math.max(...d) + b}</b> <span class="sub">[d20 ${d.join(", ")} → ${Math.max(...d)} +${b}]</span>`]);
};
A["conjurar-menu"] = () => {
  const ops = [];
  S.encantamentos.forEach((x) => { const e = ENC[x.familia]; if (e) e.versoes.filter((v) => x.versoes.includes(v.nivel)).forEach((v) => ops.push({ e, v, eq: x.equipado })); });
  if (!ops.length) { toast("Nenhum encantamento aprendido. Use a aba Grimório."); return; }
  ops.sort((a, b) => (b.eq - a.eq) || a.e.nome.localeCompare(b.e.nome) || a.v.nivel - b.v.nivel);
  folha("Conjurar", `<div class="lista">${ops.map((o) => `<div class="item" data-a="conjurar" data-f="${esc(o.e.nome)}" data-v="${o.v.nivel}"><span class="marca">✧</span>
    <div class="tx"><b>${esc(o.e.nome)}</b><small>${esc(o.v.tier)} nv ${o.v.nivel} · ${esc(o.v.mana)}${o.eq ? "" : " · não equipado"}</small></div><span class="sub">🎲</span></div>`).join("")}</div>`);
};
A["conjurar"] = (el, ev) => {
  if (ev) ev.stopPropagation();
  const e = ENC[el.dataset.f], v = e && e.versoes.find((x) => x.nivel === int(el.dataset.v)); if (!v) return;
  const k = e.dominio === "Magia" ? "INT" : "FE", per = k === "INT" ? "Feitiçaria" : "Desejo";
  const x = S.encantamentos.find((y) => y.familia === e.nome) || {};
  const impl = Math.max(0, ...S.armas.filter((w) => w.grupo === (k === "INT" ? "Cajado" : "Selo")).map((w) => int(w.nivel, 1)));
  pagar("mana_atual", C.d.mana, R.custoMana(v), "Mana", (custo) => {
    const at = R.rolarAtaque(C.d.bc[k] + C.d.n3, R.vantagem(C.a[k]), 20, rng);
    const linhas = [txtAtaque(at, per), `DT para o alvo resistir: <b>${k === "INT" ? C.d.dt_feiticaria : C.d.dt_desejo}</b>`];
    const expr = R.danoDoEncantamento(v.descricao);
    if (expr && !at.desastre) {
      const extra = k === "INT" ? C.d.dados_extra_magia : C.d.dados_extra_feitico;
      const [tot, partes] = R.rolarExpr(R.danoComDados(expr, extra), rng, at.critico);
      linhas.push(txtDano(tot, partes, "Dados do encantamento") + (extra ? ` · +${extra} dado por ${k}` : ""));
    } else if (!expr) linhas.push(`<span class="sub">Este encantamento não tem dados na descrição.</span>`);
    if (custo) linhas.push(`<span class="sub">${custo}</span>`);
    if (!x.equipado) linhas.push(`<span class="erro">Atenção: não está equipado.</span>`);
    if (impl < v.nivel) linhas.push(`<span class="erro">Atenção: precisa de ${k === "INT" ? "cajado" : "selo"} nv ${v.nivel}+ equipado.</span>`);
    mostrarRolagem(`✧ ${e.nome} (${v.tier} nv ${v.nivel})`, linhas);
  });
};
A["diario"] = () => folha("Diário de rolagens", diario.length ? `<div class="lista">${diario.map((r) => `<div class="item" style="display:block"><b style="color:var(--vinho)">${esc(r.titulo)}</b> <span class="sub">${r.hora}</span><div style="font-size:14px;line-height:1.5;margin-top:4px">${r.linhas.join("<br>")}</div></div>`).join("")}</div>` : `<div class="vazio-msg">Nenhuma rolagem nesta sessão.</div>`,
  desfazer.length ? `<button class="botao leve" data-a="desfazer">↺ Desfazer último custo</button>` : "");

A["modo-vida"] = () => mudar((s) => { s.vida.modo = s.vida.modo === "media" ? "rolar" : "media"; });
A["rolar-vida"] = () => {
  const falta = C.nVida - S.vida.rolagens.length; if (falta <= 0) return;
  const novos = [...Array(falta)].map(() => 1 + Math.floor(Math.random() * 12));
  mudar((s) => { s.vida.rolagens = s.vida.rolagens.concat(novos); });
  toast(`🎲 ${falta}d12: ${novos.join(", ")} → +${novos.reduce((a, b) => a + b, 0)} de Vida`);
};
A["treinar"] = (el) => mudar((s) => { const n = el.dataset.n; s.pericias = s.pericias.includes(n) ? s.pericias.filter((x) => x !== n) : s.pericias.concat([n]); });
A["per-atk"] = (el) => mudar((s) => { s.pericia_ataque = el.dataset.n; });
A["prev-attr"] = (el) => mudar((s) => { s.prevalencia_attr = el.dataset.k; });
A["portao"] = (el) => mudar((s) => { const v = s.portao[el.dataset.n]; v[int(el.dataset.i)] = !v[int(el.dataset.i)]; });
A["editar-cond"] = (el) => {
  const n = el.dataset.n, c = S.condicoes[n];
  folha(n, `<label class="campo"><span>Atual</span><input id="c-at" type="number" inputmode="numeric" value="${int(c.atual)}"></label>
    <label class="campo"><span>Máximo</span><input id="c-mx" type="number" inputmode="numeric" value="${int(c.max, 100)}"></label>
    <label class="campo"><span>Notas</span><input id="c-nt" value="${esc(c.notas)}"></label>`,
  `<button class="botao leve" data-a="fechar">Cancelar</button><button class="botao prim" data-a="cond-ok" data-n="${n}">Salvar</button>`);
};
A["cond-ok"] = (el) => { const c = S.condicoes[el.dataset.n]; const at = $("#c-at").value, mx = $("#c-mx").value, nt = $("#c-nt").value; fecharFolha(); mudar(() => { c.atual = at; c.max = mx; c.notas = nt; }); };
A["editar-vinc"] = (el) => {
  const k = el.dataset.k;
  folha({ grupo: "Vínculo com o grupo", mundo: "Vínculo com o mundo", metas: "Metas de vida" }[k], `<label class="campo"><textarea id="vt" rows="5">${esc(S.vinculos[k])}</textarea></label>`,
    `<button class="botao leve" data-a="fechar">Cancelar</button><button class="botao prim" data-a="vinc-ok" data-k="${k}">Salvar</button>`);
};
A["vinc-ok"] = (el) => { const v = $("#vt").value; fecharFolha(); mudar((s) => { s.vinculos[el.dataset.k] = v; }); };

A["esc-arma"] = (el) => {
  const i = int(el.dataset.i);
  seletor({
    titulo: `Arma ${i + 1}`, busca: false, extraTopo: `<div class="item" data-a="sel-item" data-id="__nenhum"><span class="marca">—</span><div class="tx"><b>Nenhuma</b></div></div>`,
    itens: () => D.armas.map((a) => ({ id: a.nome, nome: a.nome, sub: `ataque por ${a.ataque}${a.uso_duplo ? " · uso duplo" : ""}`, motivo: statusArma(C, a.nome, 1) })),
    detalhe: (id) => { const a = ARMAS[id]; return `<p class="sub">${esc(a.descricao || "")}</p>${(a.acoes || []).map((x) => `<div class="acao ${x.sub ? "sub" : ""}"><b>${esc(x.nome)}</b> — ${esc(x.texto)}</div>`).join("")}`; },
    rotuloOk: "Equipar",
    escolher: (id) => mudar((s) => { s.armas[i].grupo = id; s.armas[i].nivel = "1"; }),
  });
};
A["esc-nivel-arma"] = (el) => {
  const i = int(el.dataset.i), g = S.armas[i].grupo, ar = ARMAS[g];
  seletor({
    titulo: `${g} — nível`, busca: false,
    itens: () => ar.tabela.map((l) => ({ id: l.nivel, nome: `Nível ${l.nivel} · ${l.dano}`, sub: `crítico ${l.critico} · ${l.propriedades} prop. · peso ${l.espaco}`, motivo: statusArma(C, g, l.nivel) })),
    escolher: (id) => mudar((s) => { s.armas[i].nivel = String(id); }),
  });
};
A["esc-protecao"] = (el) => {
  const t = el.dataset.t, lista = t === "armadura" ? D.armaduras : D.escudos;
  seletor({
    titulo: t === "armadura" ? "Armadura" : "Escudo", busca: false,
    extraTopo: `<div class="item" data-a="sel-item" data-id="__nenhum"><span class="marca">—</span><div class="tx"><b>${t === "armadura" ? "Sem armadura" : "Sem escudo"}</b></div></div>`,
    itens: () => lista.map((x) => ({ id: x.nome, nome: x.nome, sub: `CA +${x.ca} · peso ${x.peso}${x.nivel ? ` · nível ${x.nivel}` : ""}${x.req ? ` · ${x.req} FOR/TEN` : ""}`, motivo: statusProtecao(C, t, x) })),
    escolher: (id) => mudar((s) => { s.equip[t] = id; }),
  });
};
A["esc-talisma"] = (el) => {
  const i = int(el.dataset.i);
  seletor({
    titulo: `Talismã ${i + 1}`,
    extraTopo: `<div class="item" data-a="sel-item" data-id="__nenhum"><span class="marca">—</span><div class="tx"><b>Vazio</b></div></div>`,
    itens: () => {
      const fams = new Set(S.talismas.filter((t, j) => j !== i && TALISMA[t.nome]).map((t) => TALISMA[t.nome].familia));
      return D.talismas.map((t) => ({ id: t.nome, nome: t.nome, sub: t.efeito, busca: t.efeito,
        motivo: [].concat(fams.has(t.familia) && !C.tal.has("Relicário") ? ["já há um da mesma família"] : [], i >= C.d.talismas ? [`só ${C.d.talismas} espaço(s)`] : []) }));
    },
    escolher: (id) => mudar((s) => { s.talismas[i] = { nome: id, efeito: id ? TALISMA[id].efeito : "" }; }),
  });
};
A["esc-talento"] = (el) => {
  const sl = el.dataset.s;
  if (sl !== "extra" && int(sl) > C.nv) { toast(`Esse talento é liberado no nível ${sl}.`); return; }
  seletor({
    titulo: sl === "extra" ? "Talento extra (Versátil)" : `Talento do nível ${sl}`,
    filtros: [{ chave: "cat", valor: "Todas as categorias", opcoes: ["Todas as categorias"].concat(CATS_TAL) }],
    extraTopo: S.talentos[sl] ? `<div class="item" data-a="sel-item" data-id="__nenhum"><span class="marca">—</span><div class="tx"><b>Deixar vazio</b></div></div>` : "",
    itens: (f) => D.talentos.filter((t) => f.cat === "Todas as categorias" || t.categoria === f.cat).map((t, j) => ({
      id: t.nome, nome: t.nome, sub: `Nv ${t.nivel}${t.requisito ? " · " + t.requisito : ""} · ${t.categoria.replace("Talentos de ", "")}`, busca: t.descricao, motivo: statusTal(C, t, sl) })),
    detalhe: (id) => { const t = TAL[id]; return `<p class="meta">${esc(t.categoria)} · Nível ${t.nivel}${t.requisito ? ` · requer ${esc(t.requisito)}` : ""}</p><div class="desc">${esc(t.descricao)}</div>`; },
    escolher: (id) => mudar((s) => { s.talentos[sl] = id; }),
  });
};
A["aprender"] = () => {
  const aprendidos = new Set(S.encantamentos.map((x) => x.familia));
  const implIni = C.nv === 1 && armasEq().some((g) => g === "Cajado" || g === "Selo");
  seletor({
    titulo: "Aprender encantamento",
    filtros: [
      { chave: "dom", valor: "Magia e Feitiço", opcoes: ["Magia e Feitiço", "Magia", "Feitiço"] },
      { chave: "tipo", valor: "Todo tipo", opcoes: ["Todo tipo"].concat(TIERS) },
      { chave: "nv", valor: "Qualquer nível", opcoes: ["Qualquer nível"].concat([...Array(10)].map((_, i) => `Nível até ${i + 1}`)) },
      { chave: "esc", valor: "Todas as escolas", opcoes: ["Todas as escolas"].concat(CATS_ENC) },
    ],
    itens: (f) => D.encantamentos.filter((e) => (f.dom === "Magia e Feitiço" || e.dominio === f.dom) && (f.esc === "Todas as escolas" || e.categoria === f.esc)
      && (f.tipo === "Todo tipo" || e.versoes[0].tier === f.tipo) && (f.nv === "Qualquer nível" || e.versoes[0].nivel <= int(f.nv.replace(/\D/g, ""))))
      .map((e) => ({ id: e.nome, nome: e.nome, busca: e.categoria + " " + e.versoes.map((v) => v.descricao).join(" "),
        sub: `${e.dominio} · ${e.versoes[0].tier} · nv ${e.versoes[0].nivel} · ${e.versoes[0].mana} · esp ${e.espaco}`,
        motivo: aprendidos.has(e.nome) ? ["já aprendido"] : R.statusVersao(e.versoes[0], e.dominio, C.a, C.nv, implIni) })),
    detalhe: (id) => descEnc(id), rotuloOk: "Aprender",
    escolher: (id) => mudar((s) => { s.encantamentos.push({ familia: id, versoes: [ENC[id].versoes[0].nivel], equipado: false }); }),
  });
};
A["ver-enc"] = (el, ev) => {
  if (ev.target.closest('[data-a="equipar"]')) return;
  const i = int(el.dataset.i), x = S.encantamentos[i], e = ENC[x.familia];
  const prox = e.versoes.find((v) => !x.versoes.includes(v.nivel));
  const pode = prox && !R.statusVersao(prox, e.dominio, C.a, C.nv).length;
  const conj = e.versoes.filter((v) => x.versoes.includes(v.nivel)).map((v) => `<button class="botao prim" data-a="conjurar" data-f="${esc(e.nome)}" data-v="${v.nivel}">🎲 Conjurar ${esc(v.tier)} nv ${v.nivel} · ${esc(v.mana)}</button>`).join("");
  folha(e.nome, `<div class="linhabts" style="margin:0 0 10px">${conj}</div>` + descEnc(e.nome), `${banco.modo === "edicao" ? `<button class="botao leve" data-a="rem-enc" data-i="${i}">Remover</button>` : ""}${prox && banco.modo === "edicao" ? `<button class="botao prim" data-a="prox-versao" data-i="${i}" ${pode ? "" : "disabled"}>Aprender nv ${prox.nivel}</button>` : ""}`);
};
A["equipar"] = (el) => {
  const x = S.encantamentos[int(el.dataset.i)];
  if (!x.equipado && C.espUsados + ENC[x.familia].espaco > C.d.espacos_encant) { toast(`Sem espaço: ${C.espUsados}/${C.d.espacos_encant} usados.`); return; }
  mudar(() => { x.equipado = !x.equipado; });
};
A["prox-versao"] = (el) => { const x = S.encantamentos[int(el.dataset.i)], e = ENC[x.familia]; const p = e.versoes.find((v) => !x.versoes.includes(v.nivel)); fecharFolha(); mudar(() => { x.versoes.push(p.nivel); x.versoes.sort((a, b) => a - b); }); };
A["rem-enc"] = (el) => { const i = int(el.dataset.i); fecharFolha(); mudar((s) => { s.encantamentos.splice(i, 1); }); };
A["sel-item"] = (el) => itemSeletor(el.dataset.id);
A["sel-voltar"] = () => seletor(pickerAtual);
A["sel-ok"] = (el) => { const cfg = pickerAtual; fecharFolha(); cfg.escolher(el.dataset.id); };
A["fechar"] = () => fecharFolha();

// ----- menu e fichas
A["menu"] = () => {
  folha("Menu", `<div class="lista">
    ${S ? `<div class="item" data-a="exportar"><div class="tx"><b>Exportar ficha (.json)</b><small>Para abrir no programa de PC ou guardar uma cópia</small></div></div>` : ""}
    <div class="item" data-a="importar"><div class="tx"><b>Abrir arquivo .json</b><small>Ficha salva pelo programa de PC</small></div></div>
    <div class="item" data-a="nova"><div class="tx"><b>Nova ficha</b><small>Criação rápida</small></div></div>
    <div class="item" data-a="lista"><div class="tx"><b>Trocar de ficha</b><small>${Object.keys(banco.fichas).length} ficha(s) neste aparelho</small></div></div>
    ${S ? `<div class="item" data-a="modo"><div class="tx"><b>${banco.modo === "edicao" ? "⚔ Ir para o Modo Jogo" : "✎ Ir para o Modo Edição"}</b><small>${banco.modo === "edicao" ? "Usar a ficha na mesa" : "Subir de nível, escolher talentos, armas e encantamentos"}</small></div></div>` : ""}
    ${sessao.ativa ? `<div class="item" data-a="sessao-nome"><div class="tx"><b>🛡 Sessão do mestre</b><small>Você está como “${esc(sessao.id || "—")}” · toque para trocar o nome</small></div></div>` : ""}
    ${S ? `<div class="item" data-a="ident"><div class="tx"><b>Nome, player e espécie</b></div></div>` : ""}
    ${S ? `<div class="item" data-a="diario"><div class="tx"><b>📜 Diário de rolagens</b></div></div>` : ""}
    <div class="item" data-a="tema"><div class="tx"><b>${banco.tema === "noite" ? "☀ Modo diurno" : "☾ Modo noturno"}</b></div></div>
    ${S ? `<div class="item" data-a="excluir"><div class="tx"><b class="erro">Excluir esta ficha do aparelho</b></div></div>` : ""}</div>`);
};
A["tema"] = () => { banco.tema = banco.tema === "noite" ? "dia" : "noite"; gravarLocal(); fecharFolha(); render(); };
A["lista"] = () => { fecharFolha(); S = null; banco.atual = null; gravarLocal(); render(); };
A["abrir"] = (el) => abrirFicha(el.dataset.id);
function abrirFicha(id, modo = "jogo") { S = normalizar(banco.fichas[id]); banco.atual = id; banco.modo = modo; gravarLocal(); aba = "ficha"; render(); }
A["exportar"] = async () => {
  const nome = (S.identidade.nome || "ficha").trim().replace(/\s+/g, "_") + ".json";
  const copia = Object.assign({}, S); delete copia._salvo;
  const texto = JSON.stringify(copia, null, 1);
  fecharFolha();
  try {
    const dl = window.claude && window.claude.use ? await window.claude.use("downloads") : null;
    if (dl) { await dl.save({ filename: nome, data: new Blob([texto], { type: "application/json" }) }); return; }
  } catch (e) { /* cai para o download comum */ }
  try {
    const url = URL.createObjectURL(new Blob([texto], { type: "application/json" }));
    const a = document.createElement("a"); a.href = url; a.download = nome; document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 4000);
    toast(`Exportado: ${esc(nome)}`);
  } catch (e) { toast("Não consegui exportar neste navegador."); }
};
A["importar"] = () => { fecharFolha(); $("#arquivo").click(); };
A["excluir"] = () => folha("Excluir ficha?", `<p>Isto apaga <b>${esc(S.identidade.nome || "esta ficha")}</b> deste aparelho. Se quiser guardar, exporte antes.</p>`,
  `<button class="botao leve" data-a="fechar">Cancelar</button><button class="botao prim" data-a="excluir-ok">Excluir</button>`);
A["excluir-ok"] = () => { const id = banco.atual; delete banco.fichas[id]; banco.atual = null; S = null; gravarLocal(); enviarNuvem(id); fecharFolha(); render(); };
A["ident"] = () => folha("Identidade", `<label class="campo"><span>Nome</span><input id="i-nome" value="${esc(S.identidade.nome)}"></label>
  <label class="campo"><span>Player</span><input id="i-player" value="${esc(S.identidade.player)}"></label>
  <label class="campo"><span>Espécie</span><input id="i-esp" value="${esc(S.identidade.especie)}"></label>
  <label class="campo"><span>Sonho</span><input id="i-sonho" value="${esc(S.identidade.sonho)}"></label>`,
`<button class="botao leve" data-a="fechar">Cancelar</button><button class="botao prim" data-a="ident-ok">Salvar</button>`);
A["ident-ok"] = () => { const v = (id) => $(id).value; const n = v("#i-nome"), p = v("#i-player"), e = v("#i-esp"), so = v("#i-sonho"); fecharFolha(); mudar((s) => Object.assign(s.identidade, { nome: n, player: p, especie: e, sonho: so })); };
A["nova"] = () => {
  const opts = (k) => [""].concat(R.VALORES_INICIAIS).map((x) => `<option>${x}</option>`).join("");
  const nomes = [""].concat(R.ATRIBUTOS.map((k) => R.NOMES_ATR[k])).map((n) => `<option>${n}</option>`).join("");
  folha("Nova ficha", `<label class="campo"><span>Nome do personagem</span><input id="n-nome"></label>
    <label class="campo"><span>Player</span><input id="n-player"></label>
    <label class="campo"><span>Espécie</span><input id="n-esp"></label>
    <div class="secao">Atributos iniciais</div><p class="sub" style="margin-top:-4px">Use cada valor uma vez: 16, 14, 12, 11, 10, 9, 8, 7.</p>
    <div class="grade g2">${R.ATRIBUTOS.map((k) => `<label class="campo" style="margin:2px 0"><span>${R.NOMES_ATR[k]}</span><select data-ini="${k}">${opts(k)}</select></label>`).join("")}</div>
    <div class="secao">Espécie (par numérico)</div>
    <div class="grade g3"><label class="campo"><span>Bônus em</span><select id="n-bon">${nomes}</select></label><label class="campo"><span>Prejuízo em</span><select id="n-pre">${nomes}</select></label>
    <label class="campo"><span>Valor</span><select id="n-val">${[0, 1, 2, 3, 4, 5].map((x) => `<option>${x}</option>`).join("")}</select></label></div>
    <label class="campo" style="display:flex;align-items:center;gap:10px"><input type="checkbox" id="n-sem" style="width:24px;height:24px"> <span style="margin:0">☠ Sem alma (+2 pontos de atributo por nível)</span></label>
    <p class="erro" id="n-erro"></p>`, `<button class="botao leve" data-a="fechar">Cancelar</button><button class="botao prim" data-a="nova-ok">Criar ficha</button>`, (c) => {
    c.querySelectorAll("[data-ini]").forEach((s) => s.addEventListener("change", () => {
      const usados = [...c.querySelectorAll("[data-ini]")].map((x) => x.value).filter(Boolean);
      c.querySelectorAll("[data-ini]").forEach((x) => [...x.options].forEach((o) => { o.disabled = o.value && o.value !== x.value && usados.includes(o.value); }));
    }));
  });
};
A["nova-ok"] = () => {
  const c = $("#folha-corpo"), ini = {};
  c.querySelectorAll("[data-ini]").forEach((s) => { ini[s.dataset.ini] = s.value; });
  const vals = Object.values(ini);
  if (!$("#n-nome").value.trim()) { $("#n-erro").textContent = "Dê um nome ao personagem."; return; }
  if (vals.includes("") || new Set(vals).size !== 8) { $("#n-erro").textContent = "Atribua os oito valores, cada um uma vez."; return; }
  const val = int($("#n-val").value), kb = R.ATR_POR_NOME[$("#n-bon").value], kp = R.ATR_POR_NOME[$("#n-pre").value];
  if (val && (!kb || !kp || kb === kp)) { $("#n-erro").textContent = "Escolha atributos diferentes para o bônus e o prejuízo."; return; }
  const s = novoEstado();
  s.identidade.nome = $("#n-nome").value.trim(); s.identidade.player = $("#n-player").value.trim(); s.identidade.especie = $("#n-esp").value.trim();
  s.sem_alma = $("#n-sem").checked;
  for (const k of R.ATRIBUTOS) { s.atributos[k].inicial = ini[k]; s.atributos[k].especie = String(val ? (k === kb ? val : k === kp ? -val : 0) : 0); }
  const id = "ficha-" + Date.now().toString(36);
  banco.fichas[id] = s; banco.atual = id; fecharFolha(); abrirFicha(id, "edicao"); salvar();
  toast("Ficha criada. Ela fica guardada neste aparelho.");
};
function importarArquivo(arq) {
  const rd = new FileReader();
  rd.onload = () => {
    try {
      const s = normalizar(JSON.parse(rd.result));
      if (!s.identidade) throw new Error();
      const id = "ficha-" + Date.now().toString(36);
      banco.fichas[id] = s; banco.atual = id; abrirFicha(id); salvar();
      toast(`Ficha <b>${esc(s.identidade.nome || "sem nome")}</b> aberta e guardada neste aparelho.`);
    } catch (e) { toast("Esse arquivo não parece ser uma ficha de Prevalecentes."); }
  };
  rd.readAsText(arq);
}


// ------------------------------------------------------------------ sessão do mestre (quando o PC do mestre serve esta página)
const sessao = { ativa: false, id: "", mao: false, rodada: 0, efeitos: [], conectado: false, ultimo: "", timer: null, falhas: 0 };
const CH_SESSAO = "prevalecentes.sessao.id";
async function api(url, corpo) {
  const r = await fetch(url, corpo === undefined ? { cache: "no-store" } : { method: "POST", body: JSON.stringify(corpo) });
  if (!r.ok) throw new Error(r.status);
  return r.json();
}
async function detectarSessao() {
  if (!/^https?:$/.test(location.protocol) || location.protocol === "https:") return;
  try {
    const r = await api("/api/sessao");
    if (!r || !r.sessao) return;
  } catch (e) { return; }
  sessao.ativa = true;
  try { sessao.id = localStorage.getItem(CH_SESSAO) || ""; } catch (e) { /* sem storage */ }
  if (sessao.id) entrarSessao(sessao.id); else pedirNomeSessao();
  pintarSessao();
}
function pedirNomeSessao() {
  const sug = S ? (S.identidade.player || S.identidade.nome || "") : "";
  folha("Entrar na mesa", `<p class="sub">Esta página veio do PC do mestre. Com uma ficha aberta, o mestre vê sua Vida, Mana e Vigor e pode mandar dano e condições.</p>
    <label class="campo"><span>Seu nome na mesa</span><input id="ss-n" value="${esc(sessao.id || sug)}" maxlength="30"></label>`,
  `<button class="botao leve" data-a="fechar">Agora não</button><button class="botao prim" data-a="sessao-ok">Entrar</button>`);
}
A["sessao-nome"] = () => pedirNomeSessao();
A["sessao-ok"] = () => { const n = $("#ss-n").value.trim(); if (!n) { $("#ss-n").focus(); return; } fecharFolha(); entrarSessao(n, true); };
async function entrarSessao(nome, novo = false) {
  try {
    if (novo && sessao.id && sessao.id !== nome) sessao.id = "";
    sessao.id = await api("/api/oi", { nome, id: novo ? "" : sessao.id }).then((r) => r.id);
    try { localStorage.setItem(CH_SESSAO, sessao.id); } catch (e) { /* sem storage */ }
    sessao.conectado = true; sessao.ultimo = "";
    if (novo) toast(`Na mesa como <b>${esc(sessao.id)}</b>.`);
  } catch (e) { sessao.conectado = false; toast("Não consegui falar com o mestre. Você está na mesma rede?"); }
  clearInterval(sessao.timer); sessao.timer = setInterval(consultarSessao, 1500);
  consultarSessao(); pintarSessao();
}
function resumoSessao() {
  if (!S) return null;
  const c = calcular(), d = c.d, at = (ch, max) => (S.vida[ch] === "" || S.vida[ch] == null ? max : int(S.vida[ch], max));
  return { personagem: S.identidade.nome || "", especie: S.identidade.especie || "", nivel: c.nv,
    vida: at("atual", d.vida), vida_max: d.vida, mana: at("mana_atual", d.mana), mana_max: d.mana, vigor: at("vigor_atual", d.vigor), vigor_max: d.vigor,
    ca: d.ca, movimento: c.mov, iniciativa: d.iniciativa_bonus,
    portao: [S.portao.Sucessos.filter(Boolean).length, S.portao.Falhas.filter(Boolean).length],
    condicoes: R.CONDICOES.filter((n) => int((S.condicoes[n] || {}).atual)).map((n) => [n, int(S.condicoes[n].atual), int(S.condicoes[n].max, 100)]),
    sem_alma: !!S.sem_alma };
}
async function consultarSessao() {
  if (!sessao.id) return;
  let r;
  try { r = await api("/api/estado?id=" + encodeURIComponent(sessao.id)); }
  catch (e) { if (sessao.conectado) { sessao.conectado = false; pintarSessao(); } return; }
  if (!r.ok) { entrarSessao(sessao.id); return; }   // o mestre reiniciou: entra de novo com o mesmo nome
  const mudou = !sessao.conectado || sessao.mao !== r.mao || sessao.rodada !== r.rodada || JSON.stringify(sessao.efeitos) !== JSON.stringify(r.efeitos || []);
  sessao.conectado = true; sessao.mao = r.mao; sessao.rodada = r.rodada;
  sessao.efeitos = r.efeitos || [];
  const avisos = (r.eventos || []).map(receberEvento).filter(Boolean);
  if (r.palavra) { avisos.push("🎤 <b>O mestre te deu a palavra!</b>"); vibrar([300, 120, 300]); }
  if (avisos.length) toast(avisos.join("<hr>"));
  if (mudou) { if (S && (aba === "combate")) render(); else pintarSessao(); }
  const res = resumoSessao(), txt = JSON.stringify(res);
  if (res && txt !== sessao.ultimo) {
    try { await api("/api/ficha", { id: sessao.id, dados: res }); sessao.ultimo = txt; } catch (e) { /* tenta na próxima */ }
  }
}
const vibrar = (p) => { try { if (navigator.vibrate) navigator.vibrate(p); } catch (e) { /* sem vibração */ } };
function receberEvento(ev) {
  const hora = new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
  if (ev.tipo === "dano") {
    const valor = int(ev.valor), desc = String(ev.desc || "");
    const oque = valor < 0 ? `Cura de ${-valor}` : `${valor} de dano${ev.dano_tipo ? ` (${esc(ev.dano_tipo)})` : ""}`;
    let linha = "";
    if (S) {
      const max = calcular().d.vida, antes = S.vida.atual === "" || S.vida.atual == null ? max : int(S.vida.atual, max);
      const depois = Math.max(0, Math.min(max, antes - valor));
      S.vida.atual = String(depois); salvar(); render();
      linha = `Vida: ${antes} → <b>${depois}</b>${depois === 0 && antes > 0 ? ` — <b class="erro">INCAPAZ</b>: role o Portão da Morte no início do turno.` : ""}`;
    }
    diario.unshift({ titulo: "📣 Do mestre", linhas: [oque + (desc ? " — " + esc(desc) : ""), linha].filter(Boolean), hora });
    vibrar(valor < 0 ? 120 : [200, 80, 200]);
    return `📣 <b>${oque}</b>${desc ? " — " + esc(desc) : ""}${linha ? "<br>" + linha : ""}`;
  } else if (ev.tipo === "condicao") {
    const dur = ev.rodadas ? `${ev.rodadas} rodada(s)` : "até o mestre remover";
    diario.unshift({ titulo: "📣 Condição", linhas: [`${esc(ev.nome)} (${dur})${ev.desc ? " — " + esc(ev.desc) : ""}`], hora });
    vibrar(200);
    return `⏳ <b>${esc(ev.nome)}</b> (${dur})${ev.desc ? " — " + esc(ev.desc) : ""}`;
  } else if (ev.tipo === "fim") {
    return `Terminou: <b>${esc(ev.nome)}</b>`;
  }
  return "";
}
A["sessao-mao"] = async () => {
  if (!sessao.id) { pedirNomeSessao(); return; }
  try { await api(sessao.mao ? "/api/abaixar" : "/api/mao", { id: sessao.id }); sessao.mao = !sessao.mao; pintarSessao(); consultarSessao(); }
  catch (e) { toast("Sem conexão com o mestre…"); }
};
A["sessao-efeitos"] = () => folha(`Mesa · Rodada ${sessao.rodada}`, sessao.efeitos.length
  ? `<div class="lista">${sessao.efeitos.map((e) => `<div class="item"><span class="marca">⏳</span><div class="tx"><b>${esc(e.nome)}</b><small>${e.rodadas ? `${e.rodadas} rodada(s)` : "até o mestre remover"}${e.desc ? " · " + esc(e.desc) : ""}</small></div></div>`).join("")}</div>`
  : `<div class="vazio-msg">Nenhuma condição do mestre em você.</div>`, `<button class="botao leve" data-a="sessao-nome">Trocar nome</button><button class="botao prim" data-a="fechar">OK</button>`);
function pintarSessao() {
  const b = $("#mesa");
  if (!b) return;
  b.classList.toggle("oculto", !sessao.ativa);
  document.body.classList.toggle("com-mesa", sessao.ativa);
  if (!sessao.ativa) return;
  const ef = sessao.efeitos.length ? ` · ⏳ ${sessao.efeitos.map((e) => esc(e.nome)).join(", ")}` : "";
  b.innerHTML = `<button class="info" data-a="sessao-efeitos"><b>${sessao.conectado ? "🛡 Mesa" : "⚠ Sem sinal"}</b> · Rodada ${sessao.rodada}${ef}${S ? "" : " · abra uma ficha"}</button>
    <button class="mao ${sessao.mao ? "on" : ""}" data-a="sessao-mao">✋ ${sessao.mao ? "Abaixar" : "Mão"}</button>`;
}

// ------------------------------------------------------------------ eventos
document.addEventListener("click", (ev) => {
  const el = ev.target.closest("[data-a]");
  if (!el) return;
  const f = A[el.dataset.a];
  if (!f) return;
  if (el.tagName === "A") ev.preventDefault();
  if (S && banco.modo !== "edicao" && SO_EDICAO.has(el.dataset.a)) {
    toast(`Isso muda a ficha — use o <b>Modo Edição</b>. <button class="botao leve" data-a="modo" style="min-height:32px;padding:4px 10px;margin-left:6px">✎ Editar</button>`);
    return;
  }
  f(el, ev);
});
document.addEventListener("DOMContentLoaded", () => {
  lerLocal();
  if (banco.atual && banco.fichas[banco.atual]) S = normalizar(banco.fichas[banco.atual]);
  $("#veu").addEventListener("click", fecharFolha);
  $("#arquivo").addEventListener("change", (e) => { if (e.target.files[0]) importarArquivo(e.target.files[0]); e.target.value = ""; });
  render();
  setTimeout(ligarNuvem, 50);
  detectarSessao();
  if ("serviceWorker" in navigator && (location.protocol === "https:" || location.hostname === "localhost") && !window.claude) navigator.serviceWorker.register("sw.js").catch(() => {});
});
