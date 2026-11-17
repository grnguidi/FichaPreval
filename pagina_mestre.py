# -*- coding: utf-8 -*-
"""Página do painel do mestre (inimigos, anotações e combate). Servida só neste computador por mestre_web.py."""
HTML = r"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Painel do mestre</title>
<style>
:root{--fundo:#f3ead2;--papel:#fbf6e9;--tinta:#2a2118;--tinta2:#6b5d49;--ouro:#b8860b;--vinho:#7a1f2b;--verde:#3d5a2e;--azul:#2f5d8a;--roxo:#6a3d8a;--linha:#d9c9a3;--erro:#a3262c;--ok:#2f6b2f}
@media (prefers-color-scheme:dark){:root{--fundo:#12170f;--papel:#1b2218;--tinta:#ece3cf;--tinta2:#a99f89;--linha:#3a4433;--vinho:#d8727f;--verde:#8fbf74;--azul:#7db0e0;--roxo:#c09ae0;--erro:#ef8086;--ok:#8fd08f}}
*{box-sizing:border-box}
body{margin:0;background:var(--fundo);color:var(--tinta);font:15px/1.4 Georgia,'Times New Roman',serif}
header.topo{display:flex;gap:14px;align-items:center;padding:10px 18px;background:#1b2520;color:#e8d9a8;position:sticky;top:0;z-index:5}
header.topo h1{font-size:19px;margin:0;font-variant:small-caps;letter-spacing:.06em;font-weight:600}
nav{display:flex;gap:6px;margin-left:18px}
nav button{background:transparent;border:1px solid #6d5f3a;color:#e8d9a8;padding:6px 14px;border-radius:6px;cursor:pointer;font:inherit}
nav button.on{background:#e8d9a8;color:#1b2520}
#estado-sessao{font-size:13px;opacity:.9}
#btn-dados{background:#e8d9a8;color:#1b2520;border-color:#e8d9a8;font-weight:700}
.dado-res{font-size:34px;font-weight:700;color:var(--vinho);text-align:center;margin:6px 0 2px}
.hist{max-height:170px;overflow:auto;font-size:13.5px;border-top:1px solid var(--linha);margin-top:8px;padding-top:6px}
main{padding:14px 18px;max-width:1700px;margin:0 auto}
button,select,input,textarea{font:inherit;color:inherit}
button.b{background:var(--papel);border:1px solid var(--ouro);color:var(--tinta);border-radius:6px;padding:5px 11px;cursor:pointer}
button.b:hover{background:var(--linha)}
button.p{background:var(--vinho);border-color:var(--vinho);color:#fff}
button.p:hover{filter:brightness(1.1);background:var(--vinho)}
button.mini{padding:2px 8px;font-size:13px}
button.perigo{border-color:var(--erro);color:var(--erro)}
input,select,textarea{background:var(--papel);border:1px solid var(--linha);border-radius:5px;padding:4px 7px}
input[type=number]{width:86px}
textarea{width:100%;resize:vertical}
label.c{display:flex;flex-direction:column;gap:2px;font-size:12.5px;color:var(--tinta2)}
label.c input,label.c select{color:var(--tinta);font-size:15px}
.linha{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.grade{display:grid;gap:10px}
.g2{grid-template-columns:repeat(2,1fr)}.g3{grid-template-columns:repeat(3,1fr)}.g4{grid-template-columns:repeat(4,1fr)}.g7{grid-template-columns:repeat(7,minmax(90px,1fr))}
.cart{background:var(--papel);border:1px solid var(--linha);border-left:4px solid var(--ouro);border-radius:8px;padding:10px 12px;margin-bottom:10px}
.cart.jog{border-left-color:var(--azul)}.cart.ini{border-left-color:var(--vinho)}.cart.caido{opacity:.55}.cart.vez{box-shadow:0 0 0 2px var(--ouro)}
.cart header{display:flex;gap:8px;align-items:baseline;flex-wrap:wrap;margin-bottom:6px}
.cart header b{font-size:17px}
small,.sub{color:var(--tinta2);font-size:13px}
.tag{display:inline-block;padding:1px 8px;border-radius:10px;font-size:12px;background:var(--linha);color:var(--tinta)}
.tag.v{background:var(--vinho);color:#fff}.tag.az{background:var(--azul);color:#fff}.tag.ok{background:var(--verde);color:#fff}.tag.er{background:var(--erro);color:#fff}
.barra{position:relative;height:19px;background:var(--linha);border-radius:10px;overflow:hidden;margin:3px 0}
.barra i{position:absolute;inset:0 auto 0 0;display:block}
.barra span{position:relative;z-index:1;display:block;text-align:center;font-size:12.5px;line-height:19px;color:#fff;text-shadow:0 0 3px #000}
.barra.fina{height:13px}.barra.fina span{font-size:11px;line-height:13px}
.duas{display:grid;grid-template-columns:minmax(360px,1fr) minmax(460px,1.35fr);gap:16px;align-items:start}
@media(max-width:1000px){.duas{grid-template-columns:1fr}.g7{grid-template-columns:repeat(3,1fr)}}
h2{font-size:17px;margin:4px 0 8px;color:var(--vinho);font-variant:small-caps;letter-spacing:.05em}
h3{font-size:15px;margin:12px 0 6px;color:var(--vinho)}
.ordem{display:flex;gap:6px;flex-wrap:wrap;margin:8px 0}
.ordem .tag{font-size:13px;padding:3px 10px}.ordem .tag.vez{background:var(--ouro);color:#1b1b1b;font-weight:700}
.tres{display:grid;grid-template-columns:minmax(250px,310px) minmax(340px,1fr) minmax(430px,1.3fr);gap:16px;align-items:start}
@media(max-width:1250px){.tres{grid-template-columns:minmax(240px,290px) 1fr}.tres>:nth-child(3){grid-column:1/-1}}
@media(max-width:800px){.tres{grid-template-columns:1fr}}
.tabela{position:sticky;top:64px;background:var(--papel);border:1px solid var(--ouro);border-radius:8px;padding:8px}
.tabela h2{margin:0 0 6px}
.linha-ini{display:grid;grid-template-columns:24px 40px 1fr auto;gap:6px;align-items:center;padding:5px 6px;border-radius:6px;margin-bottom:4px;border-left:4px solid var(--azul);background:var(--fundo);cursor:pointer}
.linha-ini.i{border-left-color:var(--vinho)}.linha-ini.vez{background:var(--ouro);color:#1b1b1b;font-weight:700;border-left-color:#1b1b1b}.linha-ini.vez small{color:#222}
.linha-ini.caido{opacity:.45;text-decoration:line-through}.linha-ini.abre{border:1px dashed var(--ouro);border-left-width:4px}
.linha-ini .pos{font-size:12px;opacity:.7;text-align:center}.linha-ini .n{font-size:22px;font-weight:700;text-align:center;line-height:1}
.linha-ini .mini-barra{height:6px;background:rgba(0,0,0,.2);border-radius:3px;overflow:hidden;margin-top:3px}.linha-ini .mini-barra i{display:block;height:100%;background:var(--vinho)}
.flash{animation:fl 1.2s}@keyframes fl{0%,60%{box-shadow:0 0 0 3px var(--ouro)}100%{box-shadow:none}}
.aviso{background:var(--papel);border:1px dashed var(--ouro);padding:8px 12px;border-radius:6px;margin:8px 0;color:var(--tinta2)}
.lista-esq{display:grid;grid-template-columns:330px 1fr;gap:16px;align-items:start}
@media(max-width:900px){.lista-esq{grid-template-columns:1fr}}
.item{background:var(--papel);border:1px solid var(--linha);border-radius:7px;padding:8px 10px;margin-bottom:6px;cursor:pointer}
.item:hover{border-color:var(--ouro)}.item.on{border-color:var(--vinho);box-shadow:0 0 0 1px var(--vinho)}
.painel{background:var(--papel);border:1px solid var(--linha);border-radius:8px;padding:14px}
.lista-esq>div{min-width:0}
.painel{overflow-x:hidden}
.linha-golpe,.linha-hab{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px;align-items:flex-end;padding-bottom:6px;border-bottom:1px dashed var(--linha)}
.linha-golpe label.c,.linha-hab label.c{flex:1 1 120px;min-width:0}
.linha-hab label.c:nth-child(3){flex:3 1 260px}
.linha-golpe input[type=number]{width:100%}
.painel input,.painel select,.painel textarea{max-width:100%}
.chips{display:flex;gap:5px;flex-wrap:wrap;margin:4px 0}
.chip{border:1px solid var(--linha);border-radius:12px;padding:1px 9px;font-size:13px;cursor:pointer;background:var(--papel)}
.chip.on{background:var(--vinho);color:#fff;border-color:var(--vinho)}
.chip.fixo{cursor:default}
details>summary{cursor:pointer;color:var(--tinta2);margin:4px 0}
#toast{position:fixed;right:16px;bottom:16px;max-width:430px;background:#1b2520;color:#e8d9a8;padding:12px 16px;border-radius:8px;box-shadow:0 4px 18px #0007;display:none;z-index:20;line-height:1.5}
#toast.on{display:block}#toast .b{margin-top:6px}
dialog{border:2px solid var(--ouro);border-radius:10px;background:var(--papel);color:var(--tinta);max-width:640px;width:92vw;padding:16px 18px}
dialog::backdrop{background:#0008}
.ok{color:var(--ok)}.er{color:var(--erro)}
.item b{display:block}
.vazio{color:var(--tinta2);padding:18px;text-align:center}
</style>
</head>
<body>
<header class="topo"><h1>⚜ Painel do mestre</h1>
<nav><button data-aba="combate" class="on">⚔ Combate</button><button data-aba="inimigos">👹 Inimigos</button><button data-aba="notas">📝 Anotações</button></nav>
<button class="b" id="btn-dados" style="margin-left:auto" title="Rolar dados">🎲 Dados</button><span id="estado-sessao" style="margin-left:14px"></span></header>
<main>
<section id="aba-combate"></section>
<section id="aba-inimigos" hidden></section>
<section id="aba-notas" hidden></section>
</main>
<div id="toast"></div>
<dialog id="dlg"></dialog>
<script>
"use strict";
const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const num = (v, p = 0) => { const n = Math.round(Number(v)); return Number.isFinite(n) ? n : p; };
async function api(url, corpo) {
  const r = await fetch(url, corpo === undefined ? { cache: "no-store" } : { method: "POST", body: JSON.stringify(corpo) });
  return r.json();
}
let CFG = { tiers: [], condicoes: [], tipos_dano: [], efeitos: [] }, LIB = [], NOTAS = [], E = { jogadores: [], inimigos: [], ordem: [], log: [], registro: [] };
let aba = "combate";
function toast(html, ms = 5000, botoes) {
  const t = $("#toast"); t.innerHTML = html; t.classList.add("on");
  if (botoes) botoes.forEach(([txt, fn]) => { const b = document.createElement("button"); b.className = "b p mini"; b.textContent = txt; b.style.marginRight = "6px"; b.onclick = () => { fn(); t.classList.remove("on"); }; t.appendChild(document.createElement("br")); t.appendChild(b); });
  clearTimeout(toast.t); toast.t = setTimeout(() => t.classList.remove("on"), ms);
}
function dialogo(titulo, corpo, ok, rotuloOk = "OK") {
  const d = $("#dlg");
  d.innerHTML = `<h2>${esc(titulo)}</h2><div id="dlg-c">${corpo}</div><div class="linha" style="justify-content:flex-end;margin-top:12px"><button class="b" id="dlg-x">Cancelar</button><button class="b p" id="dlg-ok">${esc(rotuloOk)}</button></div>`;
  $("#dlg-x").onclick = () => d.close();
  $("#dlg-ok").onclick = async () => { if ((await ok($("#dlg-c"))) !== false) d.close(); };
  d.showModal();
}
const optTipos = (sel = "") => `<option value="">— tipo —</option>` + CFG.tipos_dano.map((t) => `<option ${t === sel ? "selected" : ""}>${esc(t)}</option>`).join("");

// ------------------------------------------------------------------ dados
function rolarDados(expr, dobrar = false) {
  const t = String(expr == null ? "" : expr).toLowerCase().replace(/\s+/g, "").replace(/(^|[+\-])d(\d+)/g, "$11d$2");
  let total = 0; const partes = [];
  for (const m of t.matchAll(/([+-]?)(\d+)d(\d+)|([+-]?)(\d+)/g)) {
    if (m[2]) {
      const sinal = m[1] === "-" ? -1 : 1, q = Math.min(300, Math.max(1, +m[2])) * (dobrar ? 2 : 1), f = Math.max(2, Math.min(1000, +m[3]));
      const vals = [...Array(q)].map(() => 1 + Math.floor(Math.random() * f)), sub = sinal * vals.reduce((a, b) => a + b, 0);
      partes.push({ txt: `${sinal < 0 ? "-" : ""}${q}d${f}`, vals, sub }); total += sub;
    } else if (m[5]) { const sub = (m[4] === "-" ? -1 : 1) * +m[5]; partes.push({ txt: (sub >= 0 ? "+" : "") + sub, vals: [], sub }); total += sub; }
  }
  return { total, partes, ok: partes.length > 0 };
}
const txtPartes = (r) => r.partes.map((p) => p.vals.length ? `${p.txt}[${p.vals.length > 14 ? p.vals.slice(0, 14).join(", ") + "…" : p.vals.join(", ")}]` : p.txt).join(" ");
const HIST = [];
function abrirDados() {
  const rapidos = [4, 6, 8, 10, 12, 20, 100].map((f) => `<button class="b mini" data-d="1d${f}">d${f}</button>`).join(" ");
  dialogo("Rolar dados", `<div class="linha"><input id="dd-e" placeholder="ex.: 2d6+3, 4d8, d20" style="flex:1" autofocus><button class="b p" id="dd-r">🎲 Rolar</button></div>
    <div class="linha" style="margin-top:8px">${rapidos}</div>
    <div class="linha" style="margin-top:8px"><button class="b mini" data-v="1">d20 com vantagem</button><button class="b mini" data-v="-1">d20 com desvantagem</button><label><input type="checkbox" id="dd-c"> crítico (dobra os dados)</label></div>
    <div class="dado-res" id="dd-t">—</div><div class="sub" id="dd-p" style="text-align:center"></div><div class="hist" id="dd-h"></div>`, () => { }, "Fechar");
  const c = $("#dlg-c"), mostra = (rot, r) => {
    $("#dd-t", c).textContent = r.total; $("#dd-p", c).textContent = `${rot}: ${txtPartes(r)}`;
    HIST.unshift(`${rot} → <b>${r.total}</b> <span class="sub">${esc(txtPartes(r))}</span>`); HIST.length = Math.min(HIST.length, 30); $("#dd-h", c).innerHTML = HIST.join("<br>");
  }, rola = (expr) => { const r = rolarDados(expr, $("#dd-c", c).checked); if (!r.ok) { toast("Expressão inválida. Use algo como 2d6+3."); return; } mostra(expr, r); };
  $("#dd-h", c).innerHTML = HIST.join("<br>");
  $("#dd-r", c).onclick = () => rola($("#dd-e", c).value);
  $("#dd-e", c).onkeydown = (e) => { if (e.key === "Enter") rola($("#dd-e", c).value); };
  c.addEventListener("click", (ev) => {
    const d = ev.target.closest("[data-d]"), v = ev.target.closest("[data-v]");
    if (d) { $("#dd-e", c).value = d.dataset.d; rola(d.dataset.d); }
    else if (v) { const a = rolarDados("1d20"), b = rolarDados("1d20"), adv = v.dataset.v === "1", ok = adv ? (a.total >= b.total ? a : b) : (a.total <= b.total ? a : b); mostra(`d20 ${adv ? "com vantagem" : "com desvantagem"} (${a.total} e ${b.total})`, ok); }
  });
}
$("#btn-dados").onclick = abrirDados;

// ------------------------------------------------------------------ abas
$$("nav button").forEach((b) => b.onclick = () => { aba = b.dataset.aba; $$("nav button").forEach((x) => x.classList.toggle("on", x === b)); ["combate", "inimigos", "notas"].forEach((a) => $("#aba-" + a).hidden = a !== aba); if (aba === "inimigos") renderInimigos(); if (aba === "notas") renderNotas(); else renderCombate(true); });

// ------------------------------------------------------------------ COMBATE
const FORM = {};   // o que está digitado em cada cartão (sobrevive à atualização da tela)
const fm = (k) => FORM[k] || (FORM[k] = { v: "", t: "", corpo: true, direto: false, cond: "Veneno", pts: "", alvo: "" });
const barra = (atual, max, cor, fina) => { const p = max > 0 ? Math.max(0, Math.min(100, atual / max * 100)) : 0; return `<div class="barra ${fina ? "fina" : ""}"><i style="width:${p}%;background:${cor}"></i><span>${atual} / ${max}</span></div>`; };
function cartaoJogador(j) {
  const f = j.ficha || {}, k = "j:" + j.nome, s = fm(k), vez = E.ordem[E.vez] && E.ordem[E.vez][0] === j.nome;
  const conds = (f.condicoes || []).filter((c) => c[1] > 0).map((c) => `<span class="tag er">${esc(c[0])} ${c[1]}/${c[2]}</span>`).join("");
  const efs = (j.efeitos || []).map((e) => `<span class="chip">${esc(e.nome)}${e.rodadas ? " · " + e.rodadas + "t" : ""} <b data-a="rem-efeito" data-n="${esc(j.nome)}" data-cid="${esc(e.id)}" style="cursor:pointer">×</b></span>`).join("");
  const portao = f.vida === 0 && f.vida_max ? `<span class="tag er">INCAPAZ · portão ${(f.portao || [0, 0])[0]}✔ ${(f.portao || [0, 0])[1]}✘</span>` : "";
  return `<header><label><input type="checkbox" data-a="sel" data-n="${esc(j.nome)}" ${s.sel ? "checked" : ""}> <b>${esc(j.nome)}</b></label>
    <small>${esc(f.personagem || "sem ficha ainda")}${f.nivel ? " · Nv " + f.nivel : ""}${f.ca ? " · CA " + f.ca : ""}${f.movimento ? " · " + f.movimento + " m" : ""}</small>
    ${vez ? `<span class="tag v">VEZ</span>` : ""}${j.mao ? `<span class="tag ok">✋</span>` : ""}${j.sem_sinal ? `<span class="tag er">sem sinal</span>` : ""}${portao}</header>
    ${f.vida_max ? barra(f.vida, f.vida_max, "var(--vinho)") + `<div class="linha" style="gap:10px"><div style="flex:1">${barra(f.mana, f.mana_max, "var(--azul)", 1)}</div><div style="flex:1">${barra(f.vigor, f.vigor_max, "var(--verde)", 1)}</div></div>` : `<div class="sub">Aguardando a ficha do celular.</div>`}
    <div class="chips">${conds}${efs}</div>
    <div class="linha" data-k="${esc(k)}"><input type="number" data-f="v" placeholder="valor" value="${esc(s.v)}"><select data-f="t">${optTipos(s.t)}</select>
      <button class="b p mini" data-a="j-dano" data-n="${esc(j.nome)}">💥 Dano</button><button class="b mini" data-a="j-cura" data-n="${esc(j.nome)}">💚 Cura</button>
      <button class="b mini" data-a="j-cond" data-n="${esc(j.nome)}">☠ Condição</button><button class="b mini" data-a="j-efeito" data-n="${esc(j.nome)}">✨ Efeito</button></div>`;
}
function cartaoInimigo(x) {
  const k = "i:" + x.iid, s = fm(k), vez = E.ordem[E.vez] && E.ordem[E.vez][0] === x.nome;
  const conds = CFG.condicoes.map((c) => { const b = x.cond[c]; if (!b) return ""; const imune = b.afinidade === "imune";
    return `<div title="${esc(c)}: ${imune ? "imune" : b.atual + " de " + b.max}${b.ativacoes ? " · ativou " + b.ativacoes + "×" : ""}"><small>${esc(c)}${b.afinidade ? " (" + b.afinidade + ")" : ""}</small>${imune ? `<div class="barra fina"><span>imune</span></div>` : barra(Math.max(0, b.atual), b.max, "var(--roxo)", 1)}</div>`; }).join("");
  const alvos = E.jogadores.map((j) => `<option ${s.alvo === j.nome ? "selected" : ""}>${esc(j.nome)}</option>`).join("");
  const golpes = (x.golpes || []).map((g, i) => `<div class="linha" style="margin:3px 0"><b>${esc(g.nome)}</b> <small>+${g.bonus} · ${g.dano}${g.tipo ? " " + esc(g.tipo) : ""}${g.alcance ? " · " + esc(g.alcance) : ""}${g.cond ? " · " + esc(g.cond) + " " + (g.cond_pts || x.cond_por_golpe) : ""}</small>
    <button class="b mini" data-a="atacar" data-i="${esc(x.iid)}" data-g="${i}">🎲 Atacar</button>${g.efeito ? `<small style="flex-basis:100%">${esc(g.efeito)}</small>` : ""}</div>`).join("");
  const pk = (x.pontos_chave || []).map((p, i) => `<span class="chip ${p.revelado ? "on" : ""}" data-a="pk" data-i="${esc(x.iid)}" data-p="${i}" title="${esc(p.efeito || "")}">🎯 ${esc(p.nome)}${p.revelado ? " (revelado)" : ""}</span>`).join("");
  const efs = (x.efeitos || []).map((e, i) => `<span class="chip">${esc(e.nome)}${e.turnos ? " · " + e.turnos + "t" : ""} <b data-a="rem-ef" data-i="${esc(x.iid)}" data-e="${i}" style="cursor:pointer">×</b></span>`).join("")
    + (x.dots || []).map((d) => `<span class="chip fixo">${esc(d.cond)} −${d.pct}%/turno${d.turnos ? " · " + d.turnos + "t" : ""}</span>`).join("");
  const habs = (x.habilidades || []).map((h) => `<div><b>${esc(h.nome)}</b> <small>${esc(h.acao)}</small><br>${esc(h.texto)}</div>`).join("");
  return `<header><b>${esc(x.nome)}</b><span class="tag v">${esc(x.tier)} · NMP ${x.nmp}</span><small>CA ${x.ca} · Ataque +${x.ataque} · DT ${x.dt}</small>
    ${vez ? `<span class="tag v">VEZ</span>` : ""}${x.exposto ? `<span class="tag er">EXPOSTO</span>` : ""}${x.caido ? `<span class="tag er">DERROTADO</span>` : ""}
    <span style="margin-left:auto" class="linha"><small>ini</small><input type="number" style="width:58px" data-a="ini" data-i="${esc(x.iid)}" data-n="${esc(x.nome)}" value="${x.ini == null ? "" : x.ini}"><button class="b mini" data-a="editar" data-i="${esc(x.iid)}">✎</button><button class="b mini perigo" data-a="remover" data-i="${esc(x.iid)}">✖</button></span></header>
    ${barra(x.vida, x.vida_max, "var(--vinho)")}${x.postura_max ? `<small>Postura</small>${barra(x.postura, x.postura_max, "var(--ouro)", 1)}` : ""}
    <div class="chips">${efs}${pk}</div>
    <div class="linha" data-k="${esc(k)}"><input type="number" data-f="v" placeholder="dano" value="${esc(s.v)}"><select data-f="t">${optTipos(s.t)}</select>
      <label><input type="checkbox" data-f="corpo" ${s.corpo ? "checked" : ""}> corpo a corpo</label><label><input type="checkbox" data-f="direto" ${s.direto ? "checked" : ""}> direto</label>
      <button class="b p mini" data-a="i-dano" data-i="${esc(x.iid)}">💥 Dano</button><button class="b mini" data-a="i-cura" data-i="${esc(x.iid)}">💚 Cura</button></div>
    <div class="linha" data-k="${esc(k)}" style="margin-top:6px"><select data-f="cond">${CFG.condicoes.map((c) => `<option ${s.cond === c ? "selected" : ""}>${esc(c)}</option>`).join("")}</select>
      <input type="number" data-f="pts" placeholder="pontos" value="${esc(s.pts)}"><button class="b mini" data-a="i-cond" data-i="${esc(x.iid)}">☠ Aplicar condição</button></div>
    <details><summary>Barras de condição</summary><div class="grade g4" style="margin-top:4px">${conds}</div></details>
    <details open><summary>Golpes</summary>${golpes || "<small>Sem golpes cadastrados.</small>"}
      <div class="linha"><small>Alvo do ataque:</small><select data-f="alvo" data-k="${esc(k)}">${alvos}</select></div></details>
    ${habs ? `<details><summary>Habilidades</summary>${habs}</details>` : ""}
    <textarea rows="2" placeholder="Anotações deste inimigo" data-a="nota-i" data-i="${esc(x.iid)}">${esc(x.notas || "")}</textarea>`;
}
function sync(cont, itens, chave, html, classe) {
  const ids = new Set(itens.map(chave));
  [...cont.children].forEach((el) => { if (!ids.has(el.dataset.k)) el.remove(); });
  itens.forEach((it, i) => {
    const k = chave(it), h = html(it);
    let el = [...cont.children].find((c) => c.dataset.k === k);
    if (!el) { el = document.createElement("div"); el.dataset.k = k; cont.appendChild(el); }
    const cls = "cart " + classe(it);
    if (el.className !== cls) el.className = cls;
    if (el.dataset.h !== h && !el.contains(document.activeElement)) { el.innerHTML = h; el.dataset.h = h; }
    if (cont.children[i] !== el) cont.insertBefore(el, cont.children[i] || null);
  });
}
// Tabela de iniciativa (estilo mesa de combate): a ordem decrescente, quem age agora em destaque, o que cada um rolou
function pintaOrdem() {
  const box = $("#c-ordem");
  if (!E.ordem.length) { box.innerHTML = `<small>Ninguém rolou iniciativa ainda. Use “⚔ Iniciar combate”: escolha os inimigos e a quantidade, e a tabela sai pronta.</small>`; return; }
  const quem = (n) => { const j = E.jogadores.find((x) => x.nome === n); if (j) return { tipo: "j", sub: (j.ficha || {}).personagem || "", vida: (j.ficha || {}).vida, max: (j.ficha || {}).vida_max }; const x = E.inimigos.find((i) => i.nome === n); return x ? { tipo: "i", sub: x.tier, vida: x.vida, max: x.vida_max, caido: x.caido } : { tipo: "j", sub: "" }; };
  const atual = E.vez === -1 ? E.abertura : (E.ordem[E.vez] || [])[0];
  const prox = E.ordem[(E.vez + 1) % E.ordem.length];
  let h = E.abertura ? `<div class="linha-ini abre ${E.vez === -1 ? "vez" : ""}" data-oa="foco" data-n="${esc(E.abertura)}"><span class="pos">⚡</span><span class="n" style="font-size:15px">abre</span><div><b>${esc(E.abertura)}</b><br><small>deu o primeiro golpe: age antes da tabela</small></div><span></span></div>` : "";
  h += E.ordem.map((o, i) => {
    const q = quem(o[0]), d = (E.detalhe || {})[o[0]], rolou = d ? `🎲 ${d.rolos.join(", ")}${d.bonus ? " " + (d.bonus > 0 ? "+" : "") + d.bonus : ""}${d.rodadas > 1 ? " · desempatou" : ""}` : "";
    const p = q.max ? Math.max(0, Math.min(100, q.vida / q.max * 100)) : null;
    return `<div class="linha-ini ${q.tipo} ${i === E.vez ? "vez" : ""} ${q.caido ? "caido" : ""}" data-oa="foco" data-n="${esc(o[0])}"><span class="pos">${i + 1}</span><span class="n" data-oa="ini" data-n="${esc(o[0])}" data-v="${o[1]}" title="Duplo clique para trocar o valor">${o[1]}</span>
      <div><b>${i === E.vez ? "▶ " : ""}${esc(o[0])}</b><br><small>${esc(q.sub)}${rolou ? (q.sub ? " · " : "") + rolou : ""}</small>${p != null ? `<div class="mini-barra"><i style="width:${p}%"></i></div>` : ""}</div>
      <span><button class="b mini perigo" data-oa="tirar" data-n="${esc(o[0])}" title="Tirar da ordem">✖</button></span></div>`;
  }).join("");
  h += `<div class="sub" style="margin-top:6px">${atual ? `Agora: <b>${esc(atual)}</b>` : ""}${prox && E.ordem.length > 1 ? ` · Próximo: <b>${esc(prox[0])}</b>` : ""}</div>`;
  if (box.dataset.h !== h) { box.innerHTML = h; box.dataset.h = h; }
}
function renderCombate(forca) {
  const raiz = $("#aba-combate");
  if (!raiz.dataset.pronto) {
    raiz.dataset.pronto = "1";
    raiz.innerHTML = `<div class="linha" style="margin-bottom:6px"><h2 style="margin:0" id="c-rodada">Rodada 1</h2>
      <button class="b p" data-a="iniciar">⚔ Iniciar combate</button><button class="b p" data-a="passar">Passar turno ▶</button><button class="b" data-a="add-inimigos">＋ Inimigos</button><button class="b" data-a="iniciativa" title="Rola a iniciativa de todos de novo">↻ Rolar iniciativa</button><button class="b perigo" data-a="encerrar">Encerrar combate</button></div>
      <div id="c-aviso"></div>
      <div class="tres"><div class="tabela"><h2>Ordem de iniciativa</h2><div id="c-ordem"></div></div>
      <div><div class="linha"><h2 style="margin:0">Jogadores</h2><span style="margin-left:auto" class="linha" id="c-lote"></span></div><div id="c-jog"></div></div>
      <div><h2>Inimigos</h2><div id="c-ini"></div></div></div>
      <details><summary>Registro</summary><div id="c-log" class="sub"></div></details>`;
  }
  $("#estado-sessao").textContent = E.sessao ? `Sessão aberta · ${E.jogadores.length} jogador(es)` : "Sem sessão aberta";
  $("#c-rodada").textContent = "Rodada " + (E.rodada || 1);
  pintaOrdem();
  $("#c-aviso").innerHTML = E.sessao ? "" : `<div class="aviso">A sessão ainda não está aberta. Aqui você já pode montar o combate com os inimigos; para ver e atingir os jogadores, abra a mesa no programa (Sessão → Mesa do mestre).</div>`;
  const marcados = E.jogadores.filter((j) => fm("j:" + j.nome).sel);
  const lote = $("#c-lote");
  if (!lote.contains(document.activeElement)) lote.innerHTML = E.jogadores.length ? `<small>Marcados (${marcados.length}):</small><input type="number" data-lote="v" placeholder="valor" value="${esc(fm("lote").v)}"><select data-lote="t">${optTipos(fm("lote").t)}</select><button class="b p mini" data-a="lote-dano">💥 Dano</button><button class="b mini" data-a="lote-cura">💚 Cura</button><button class="b mini" data-a="sel-todos">todos</button>` : "";
  sync($("#c-jog"), E.jogadores, (j) => "j:" + j.nome, cartaoJogador, (j) => "jog" + (E.ordem[E.vez] && E.ordem[E.vez][0] === j.nome ? " vez" : ""));
  sync($("#c-ini"), E.inimigos, (x) => "i:" + x.iid, cartaoInimigo, (x) => "ini" + (x.caido ? " caido" : "") + (E.ordem[E.vez] && E.ordem[E.vez][0] === x.nome ? " vez" : ""));
  if (!E.jogadores.length && !$("#c-jog").children.length) $("#c-jog").innerHTML = `<div class="vazio">Nenhum jogador na mesa.</div>`;
  else if (E.jogadores.length) { const v = $("#c-jog > .vazio"); if (v) v.remove(); }
  if (!E.inimigos.length && !$("#c-ini .vazio")) $("#c-ini").innerHTML = `<div class="vazio">Nenhum inimigo no combate. Use “＋ Inimigos”.</div>`;
  else if (E.inimigos.length) { const v = $("#c-ini > .vazio"); if (v) v.remove(); }
  $("#c-log").innerHTML = [...E.log.map((l) => `${l[0]} — ${esc(l[1])}`), ...(E.registro || []).map((l) => `${l[0]} — ${esc(l[1])}`)].slice(0, 80).join("<br>");
}
async function atualizar() {
  try { const novo = await api("/api/estado"); const mudou = JSON.stringify(novo) !== JSON.stringify(E); E = novo; if (mudou && aba === "combate") renderCombate(); } catch (e) { $("#estado-sessao").textContent = "Painel sem conexão com o programa"; }
}
setInterval(atualizar, 1200);

// --- eventos do combate
document.addEventListener("input", (ev) => {
  const el = ev.target, caixa = el.closest("[data-k]");
  if (el.dataset.lote) { fm("lote")[el.dataset.lote] = el.value; return; }
  if (caixa && el.dataset.f) { const s = fm(caixa.dataset.k); s[el.dataset.f] = el.type === "checkbox" ? el.checked : el.value; }
  else if (el.dataset.f && el.dataset.k) fm(el.dataset.k)[el.dataset.f] = el.value;
});
document.addEventListener("change", async (ev) => {
  const el = ev.target;
  if (el.dataset.a === "sel") { fm("j:" + el.dataset.n).sel = el.checked; renderCombate(); }
  else if (el.dataset.a === "ini") { const v = el.value === "" ? null : num(el.value); if (v != null) await api("/api/combate/ini", { nome: el.dataset.n, valor: v }); atualizar(); }
  else if (el.dataset.a === "nota-i") { await api("/api/combate/editar", { iid: el.dataset.i, campos: { notas: el.value } }); }
});
document.addEventListener("click", async (ev) => {
  const el = ev.target.closest("[data-a]");
  if (!el || el.tagName === "INPUT" || el.tagName === "TEXTAREA") return;
  const a = el.dataset.a, k = (id) => fm(id);
  const feito = async (p) => { const r = await p; atualizar(); return r; };
  if (a === "iniciar") iniciarCombate();
  else if (a === "iniciativa") { if (!E.inimigos.length && !E.jogadores.length) { toast("Não há ninguém no combate."); return; } await feito(api("/api/combate/iniciativa", {})); }
  else if (a === "passar") { await feito(api("/api/combate/passar", {})); }
  else if (a === "encerrar") { if (confirm("Encerrar o combate e tirar todos os inimigos?")) await feito(api("/api/combate/encerrar", {})); }
  else if (a === "add-inimigos") adicionarInimigos();
  else if (a === "sel-todos") { const todos = E.jogadores.every((j) => fm("j:" + j.nome).sel); E.jogadores.forEach((j) => fm("j:" + j.nome).sel = !todos); renderCombate(); $$("#c-jog [data-a=sel]").forEach((c) => c.checked = !todos); }
  else if (a === "lote-dano" || a === "lote-cura") {
    const alvos = E.jogadores.filter((j) => fm("j:" + j.nome).sel).map((j) => j.nome), s = fm("lote"), v = num(s.v);
    if (!alvos.length || !v) { toast("Marque jogadores e digite um valor."); return; }
    const r = await api("/api/jogador/dano", { alvos, valor: a === "lote-cura" ? -Math.abs(v) : Math.abs(v), tipo: s.t || "", desc: "" }); if (!r.ok) toast(esc(r.erro)); else toast(`${a === "lote-cura" ? "Cura" : "Dano"} de ${Math.abs(v)} enviado a ${alvos.join(", ")}.`, 2500);
  }
  else if (a === "j-dano" || a === "j-cura") {
    const s = k("j:" + el.dataset.n), v = num(s.v); if (!v) { toast("Digite um valor."); return; }
    const r = await api("/api/jogador/dano", { alvos: [el.dataset.n], valor: a === "j-cura" ? -Math.abs(v) : Math.abs(v), tipo: s.t || "", desc: "" });
    if (!r.ok) toast(esc(r.erro)); else { s.v = ""; toast(`${a === "j-cura" ? "Cura" : "Dano"} de ${Math.abs(v)}${s.t ? " (" + esc(s.t) + ")" : ""} enviado a ${esc(el.dataset.n)}.`, 2200); }
    atualizar();
  }
  else if (a === "j-cond") {
    const nome = el.dataset.n;
    dialogo(`Condição em ${nome}`, `<div class="grade g3"><label class="c">Condição<select id="d-c">${CFG.condicoes.map((c) => `<option>${c}</option>`).join("")}</select></label><label class="c">Pontos<input type="number" id="d-p" value="20"></label><label class="c">DT do teste<input type="number" id="d-dt" value="${num((E.inimigos[0] || {}).dt, 15)}"></label></div><p class="sub">O jogador rola Fortitude (Veneno, Podridão, Sangramento, Congelamento) ou Vontade (Sono, Loucura, Morte); sucesso recebe metade.</p>`,
      async (c) => { const r = await api("/api/jogador/pontos", { alvos: [nome], cond: $("#d-c", c).value, pontos: num($("#d-p", c).value), dt: num($("#d-dt", c).value, 10), desc: "" }); if (!r.ok) { toast(esc(r.erro)); return false; } toast("Pontos enviados.", 2000); atualizar(); }, "Enviar");
  }
  else if (a === "j-efeito") {
    const nome = el.dataset.n;
    dialogo(`Efeito em ${nome}`, `<div class="grade g2"><label class="c">Efeito<select id="d-e">${CFG.efeitos.map((c) => `<option>${c}</option>`).join("")}</select></label><label class="c">Duração (turnos, 0 = até remover)<input type="number" id="d-r" value="1"></label></div><label class="c"><input type="checkbox" id="d-fc"> dura até o fim do combate</label>`,
      async (c) => { const r = await api("/api/jogador/efeito", { alvos: [nome], nome: $("#d-e", c).value, rodadas: num($("#d-r", c).value), desc: "", fim_combate: $("#d-fc", c).checked }); if (!r.ok) { toast(esc(r.erro)); return false; } atualizar(); }, "Aplicar");
  }
  else if (a === "rem-efeito") { await feito(api("/api/jogador/remover-efeito", { nome: el.dataset.n, cid: el.dataset.cid })); }
  else if (a === "i-dano" || a === "i-cura") {
    const s = k("i:" + el.dataset.i), v = num(s.v); if (!v) { toast("Digite um valor."); return; }
    const r = await api(a === "i-dano" ? "/api/combate/dano" : "/api/combate/cura", { iid: el.dataset.i, valor: Math.abs(v), tipo: s.t || "", corpo: !!s.corpo, direto: !!s.direto });
    s.v = ""; if (r.notas && r.notas.length) toast(r.notas.map(esc).join("<br>"), 4500); atualizar();
  }
  else if (a === "i-cond") {
    const s = k("i:" + el.dataset.i), v = num(s.pts, 0); if (!v) { toast("Digite os pontos."); return; }
    const r = await api("/api/combate/condicao", { iid: el.dataset.i, cond: s.cond, pontos: v });
    s.pts = ""; if (r.notas && r.notas.length) toast(r.notas.map(esc).join("<br>"), 6000); atualizar();
  }
  else if (a === "pk") { const x = E.inimigos.find((i) => i.iid === el.dataset.i), p = x.pontos_chave[num(el.dataset.p)]; await feito(api("/api/combate/ponto-chave", { iid: x.iid, idx: num(el.dataset.p), revelado: !p.revelado })); }
  else if (a === "rem-ef") { const x = E.inimigos.find((i) => i.iid === el.dataset.i); const efs = x.efeitos.filter((_, i) => i !== num(el.dataset.e)); await feito(api("/api/combate/editar", { iid: x.iid, campos: { efeitos: efs } })); }
  else if (a === "remover") { if (confirm("Tirar este inimigo do combate?")) await feito(api("/api/combate/remover", { iid: el.dataset.i })); }
  else if (a === "editar") editarInimigoCombate(E.inimigos.find((i) => i.iid === el.dataset.i));
  else if (a === "atacar") atacar(E.inimigos.find((i) => i.iid === el.dataset.i), num(el.dataset.g));
});
document.addEventListener("click", async (ev) => {
  const el = ev.target.closest("[data-oa]"); if (!el) return;
  const a = el.dataset.oa, n = el.dataset.n;
  if (a === "tirar") { ev.stopPropagation(); if (!confirm(`Tirar ${n} da ordem de iniciativa?`)) return; const x = E.inimigos.find((i) => i.nome === n); if (x) await api("/api/combate/remover", { iid: x.iid }); else await api("/api/combate/tirar", { nome: n }); atualizar(); }
  else if (a === "foco") { const x = E.inimigos.find((i) => i.nome === n), k = x ? "i:" + x.iid : "j:" + n, alvo = $(`#aba-combate [data-k="${CSS.escape(k)}"]`); if (alvo) { alvo.scrollIntoView({ behavior: "smooth", block: "center" }); alvo.classList.remove("flash"); void alvo.offsetWidth; alvo.classList.add("flash"); } }
});
document.addEventListener("dblclick", async (ev) => {
  const el = ev.target.closest("[data-oa=ini]"); if (!el) return;
  const v = prompt(`Iniciativa de ${el.dataset.n}:`, el.dataset.v); if (v === null || v === "") return;
  await api("/api/combate/ini", { nome: el.dataset.n, valor: num(v) }); atualizar();
});
// Começar um combate: escolhe os inimigos e quantos, quem da mesa entra e quem deu o primeiro golpe; a iniciativa sai rolada e a tabela montada
async function iniciarCombate() {
  await carregarLib();
  if (!LIB.length) { toast("A biblioteca está vazia. Crie inimigos na aba Inimigos antes de iniciar o combate."); return; }
  const jog = E.jogadores.map((j) => `<label style="display:block"><input type="checkbox" data-ij="${esc(j.nome)}" checked> <b>${esc(j.nome)}</b> <small>${esc((j.ficha || {}).personagem || "")}${(j.ficha || {}).iniciativa_dados ? ` · ${j.ficha.iniciativa_dados}d20 ${j.ficha.iniciativa >= 0 ? "+" : ""}${j.ficha.iniciativa}` : ""}</small></label>`).join("") || `<small>Nenhum jogador na mesa (a sessão não está aberta): o combate começa só com os inimigos.</small>`;
  dialogo("Iniciar combate", `<h3 style="margin-top:0">Inimigos e quantidade</h3><div style="max-height:34vh;overflow:auto">${LIB.map((x) => `<div class="linha" style="justify-content:space-between;margin-bottom:5px"><span><b>${esc(x.nome)}</b> <small>${esc(x.tier)} · NMP ${x.nmp} · Vida ${x.vida}${x.ini_dados > 1 || x.ini_bonus ? ` · ini ${x.ini_dados}d20 ${x.ini_bonus >= 0 ? "+" : ""}${x.ini_bonus}` : ""}</small></span><input type="number" min="0" value="0" style="width:64px" data-iq="${esc(x.id)}"></div>`).join("")}</div>
    <h3>Quem da mesa entra</h3>${jog}
    <h3>Quem deu o primeiro golpe?</h3><select id="i-prim" style="width:100%"><option value="">Ninguém (todos entram na tabela)</option></select>
    <p class="sub">Quem começa o combate rola com vantagem e age antes de a tabela rodar. Todos rolam 1d20 (mais 1d20 a cada 20 de Destreza), ficam com o maior e somam o Bônus de Combate de Destreza; quem empata rola de novo.</p>
    ${E.inimigos.length ? `<label><input type="checkbox" id="i-limpa" checked> tirar os ${E.inimigos.length} inimigo(s) que já estão no combate</label>` : ""}`,
    async (c) => {
      const itens = $$("[data-iq]", c).map((i) => ({ id: i.dataset.iq, qtd: num(i.value) })).filter((i) => i.qtd > 0);
      if (!itens.length) { toast("Escolha pelo menos um inimigo."); return false; }
      const jogadores = $$("[data-ij]", c).filter((i) => i.checked).map((i) => i.dataset.ij);
      const r = await api("/api/combate/iniciar", { itens, jogadores, primeiro: $("#i-prim", c).value, limpar: $("#i-limpa", c) ? $("#i-limpa", c).checked : true });
      if (!r.ok) { toast(esc(r.erro || "Não consegui iniciar.")); return false; }
      await atualizar(); toast("Combate iniciado. Iniciativa rolada: a tabela está à esquerda.", 3500);
    }, "🎲 Rolar iniciativa e começar");
  const c = $("#dlg-c"), atualizaPrim = () => {
    const sel = $("#i-prim"), antes = sel.value, nomes = $$("[data-ij]", c).filter((i) => i.checked).map((i) => i.dataset.ij);
    $$("[data-iq]", c).forEach((i) => { const q = num(i.value); if (q > 0) { const x = LIB.find((l) => l.id === i.dataset.iq); nomes.push(q === 1 ? x.nome : x.nome + " 1"); } });
    sel.innerHTML = `<option value="">Ninguém (todos entram na tabela)</option>` + nomes.map((n) => `<option ${n === antes ? "selected" : ""}>${esc(n)}</option>`).join("");
  };
  c.addEventListener("input", atualizaPrim); c.addEventListener("change", atualizaPrim); atualizaPrim();
}
function editarInimigoCombate(x) {
  dialogo(`Ajustar ${x.nome}`, `<div class="grade g3"><label class="c">Nome<input id="e-n" value="${esc(x.nome)}"></label><label class="c">Vida<input type="number" id="e-v" value="${x.vida}"></label><label class="c">Vida máxima<input type="number" id="e-vm" value="${x.vida_max}"></label>
    <label class="c">Postura<input type="number" id="e-p" value="${x.postura}"></label><label class="c">CA<input type="number" id="e-ca" value="${x.ca}"></label><label class="c">DT<input type="number" id="e-dt" value="${x.dt}"></label></div>
    <div class="linha" style="margin-top:8px"><label><input type="checkbox" id="e-ex" ${x.exposto ? "checked" : ""}> Exposto</label><label><input type="checkbox" id="e-cx" ${x.caido ? "checked" : ""}> Derrotado</label></div>
    <label class="c" style="margin-top:8px">Novo efeito (texto)<input id="e-ef" placeholder="ex.: Atordoado"></label><label class="c">Duração em turnos (0 = até remover)<input type="number" id="e-et" value="0"></label>`,
    async (c) => {
      const campos = { nome: $("#e-n", c).value, vida_max: num($("#e-vm", c).value), vida: num($("#e-v", c).value), postura: num($("#e-p", c).value), ca: num($("#e-ca", c).value), dt: num($("#e-dt", c).value), exposto: $("#e-ex", c).checked, caido: $("#e-cx", c).checked };
      const ef = $("#e-ef", c).value.trim(); if (ef) campos.efeitos = x.efeitos.concat([{ nome: ef, turnos: num($("#e-et", c).value) }]);
      await api("/api/combate/editar", { iid: x.iid, campos }); atualizar();
    }, "Salvar");
}
function atacar(x, gi) {
  const g = x.golpes[gi], s = fm("i:" + x.iid), alvo = E.jogadores.find((j) => j.nome === (s.alvo || (E.jogadores[0] || {}).nome));
  const d20 = 1 + Math.floor(Math.random() * 20), total = d20 + num(g.bonus), ca = alvo && alvo.ficha ? num(alvo.ficha.ca) : null;
  const crit = d20 === 20, desastre = d20 === 1, acerta = crit || (!desastre && ca != null && total >= ca);
  const dr = rolarDados(String(g.dano), crit), dano = dr.ok ? dr.total : num(g.dano);     // o dano é rolado (o crítico dobra os dados)
  let txt = `<b>${esc(x.nome)} — ${esc(g.nome)}</b>: d20 ${d20} + ${g.bonus} = <b>${total}</b>` + (ca != null ? ` contra CA ${ca} de ${esc(alvo.nome)}` : " (sem alvo)");
  txt += crit ? `<br><b class="ok">CRÍTICO</b> (acerta sempre; dobra o dano)` : desastre ? `<br><b class="er">DESASTRE</b> (erra sempre)` : ca != null ? (acerta ? `<br><b class="ok">Acertou</b>` : `<br><b class="er">Errou</b>`) : "";
  const botoes = [];
  if (acerta || ca == null) txt += `<br>Dano: <b>${dano}</b> <span class="sub">${esc(String(g.dano))}${crit ? " ×2 dados" : ""} → ${esc(txtPartes(dr))}</span>`;
  if (alvo && acerta) botoes.push([`Aplicar ${dano}${g.tipo ? " " + g.tipo : ""} em ${alvo.nome}`, async () => {
    await api("/api/jogador/dano", { alvos: [alvo.nome], valor: dano, tipo: g.tipo || "", desc: `${x.nome}: ${g.nome}` });
    if (g.cond) await api("/api/jogador/pontos", { alvos: [alvo.nome], cond: g.cond, pontos: g.cond_pts || x.cond_por_golpe, dt: x.dt, desc: `${x.nome}: ${g.nome}` });
    atualizar();
  }]);
  toast(txt, 14000, botoes);
}
function adicionarInimigos() {
  if (!LIB.length) { toast("A biblioteca está vazia. Crie inimigos na aba Inimigos."); return; }
  dialogo("Inimigos deste combate", `<div style="max-height:55vh;overflow:auto">${LIB.map((x) => `<div class="linha" style="justify-content:space-between;margin-bottom:6px"><span><b>${esc(x.nome)}</b> <small>${esc(x.tier)} · NMP ${x.nmp} · Vida ${x.vida}</small></span><input type="number" min="0" value="0" style="width:64px" data-add="${esc(x.id)}"></div>`).join("")}</div>`,
    async (c) => { const itens = $$("[data-add]", c).map((i) => ({ id: i.dataset.add, qtd: num(i.value) })).filter((i) => i.qtd > 0); if (!itens.length) return false; await api("/api/combate/adicionar", { itens }); atualizar(); }, "Adicionar ao combate");
}

// ------------------------------------------------------------------ INIMIGOS
let ED = null;      // inimigo em edição
let infoCalc = null;
const novoVazio = () => ({ id: "", nome: "", tier: "Comum", nmp: E.nmp || 5, jogadores: (E.jogadores || []).length || 4, vida: 1, ca: 0, ataque: 0, dt: 0, postura: 0, vida_condicao: 0, cond_por_golpe: 0, atencao: "", descricao: "", ini_dados: 1, ini_bonus: 0, golpes: [], habilidades: [], pontos_chave: [], resistencias: [], imunidades: [], vulnerabilidades: [], afinidades: {}, set_drops: "", loot: "", notas: "" });
async function carregarLib() { LIB = (await api("/api/inimigos")).itens || []; }
async function renderInimigos() {
  await carregarLib();
  const raiz = $("#aba-inimigos");
  const busca = ($("#li-busca") || {}).value || "", tier = ($("#li-tier") || {}).value || "";
  raiz.innerHTML = `<div class="lista-esq"><div><div class="linha" style="margin-bottom:8px"><button class="b p" data-ia="novo">＋ Novo inimigo</button></div>
    <div class="linha" style="margin-bottom:8px"><input id="li-busca" placeholder="Buscar…" value="${esc(busca)}" style="flex:1"><select id="li-tier"><option value="">Todas</option>${CFG.tiers.map((t) => `<option ${t === tier ? "selected" : ""}>${t}</option>`).join("")}</select></div>
    <div id="li-lista"></div></div><div id="li-ed"></div></div>`;
  const pinta = () => {
    const b = $("#li-busca").value.toLowerCase(), t = $("#li-tier").value;
    const itens = LIB.filter((x) => (!t || x.tier === t) && (!b || x.nome.toLowerCase().includes(b))).sort((a, b) => CFG.tiers.indexOf(a.tier) - CFG.tiers.indexOf(b.tier) || a.nmp - b.nmp || a.nome.localeCompare(b.nome));
    $("#li-lista").innerHTML = itens.length ? itens.map((x) => `<div class="item ${ED && ED.id === x.id ? "on" : ""}" data-ia="abrir" data-id="${esc(x.id)}"><b>${esc(x.nome)}</b><small>${esc(x.tier)} · NMP ${x.nmp} · Vida ${x.vida} · CA ${x.ca}</small></div>`).join("") : `<div class="vazio">Nenhum inimigo${LIB.length ? " com esse filtro" : " ainda"}.</div>`;
  };
  $("#li-busca").oninput = pinta; $("#li-tier").onchange = pinta; pinta();
  pintaEditor();
}
function chipsTipos(campo) { return `<div class="chips">${CFG.tipos_dano.map((t) => `<span class="chip ${ED[campo].includes(t) ? "on" : ""}" data-ia="tipo" data-c="${campo}" data-t="${esc(t)}">${esc(t)}</span>`).join("")}</div>`; }
function pintaEditor() {
  const box = $("#li-ed");
  if (!ED) { box.innerHTML = `<div class="painel vazio">Escolha um inimigo ou crie um novo.<br><small>Ao criar, escolha a classe e o nível: Vida, CA, Ataque, DT, Postura e dano saem da tabela do livro. O resto (golpes, habilidades, Pontos Chave) é seu.</small></div>`; return; }
  const x = ED, big = ["Animal", "Prevalecente", "Deus"].includes(x.tier);
  box.innerHTML = `<div class="painel">
    <div class="grade g4"><label class="c">Nome<input data-ef="nome" value="${esc(x.nome)}"></label>
      <label class="c">Classe<select data-ef="tier">${CFG.tiers.map((t) => `<option ${t === x.tier ? "selected" : ""}>${t}</option>`).join("")}</select></label>
      <label class="c">Nível (NMP 1–30)<input type="number" min="1" max="30" data-ef="nmp" value="${x.nmp}"></label>
      <label class="c" title="Animal, Prevalecente e Deus: a Vida e a vida de condição valem × jogadores ÷ 4">Jogadores do grupo<input type="number" min="1" max="12" data-ef="jogadores" value="${x.jogadores}"></label></div>
    <div class="linha" style="margin:8px 0"><button class="b" data-ia="calc">↻ Preencher com os valores do livro</button><small id="calc-info"></small></div>
    <div class="grade g7"><label class="c">Vida<input type="number" data-ef="vida" value="${x.vida}"></label><label class="c">CA<input type="number" data-ef="ca" value="${x.ca}"></label>
      <label class="c">Ataque (bônus)<input type="number" data-ef="ataque" value="${x.ataque}"></label><label class="c">DT<input type="number" data-ef="dt" value="${x.dt}"></label>
      <label class="c">Postura<input type="number" data-ef="postura" value="${x.postura}"></label><label class="c">Vida de condição<input type="number" data-ef="vida_condicao" value="${x.vida_condicao}"></label>
      <label class="c" title="Pontos de condição por golpe ou habilidade que aplica condição">Pontos por golpe<input type="number" data-ef="cond_por_golpe" value="${x.cond_por_golpe}"></label></div>
    <div class="grade g2" style="margin-top:8px"><label class="c">Atenção (rastrear e localizar)<input data-ef="atencao" value="${esc(x.atencao)}"></label><label class="c">Loot básico (ouro, itens simples)<input data-ef="loot" value="${esc(x.loot)}"></label></div>
    <div class="linha" style="margin-top:8px"><b>Iniciativa:</b><label class="c" title="1d20 por dado, fica o maior (como o jogador: +1d20 a cada 20 de Destreza)">dados d20<input type="number" min="1" max="10" data-ef="ini_dados" value="${x.ini_dados || 1}"></label><label class="c">bônus<input type="number" data-ef="ini_bonus" value="${x.ini_bonus || 0}"></label><small>o livro não dá número de Destreza aos inimigos: aumente se ele for rápido</small></div>
    <label class="c" style="margin-top:8px">Descrição<textarea rows="3" data-ef="descricao">${esc(x.descricao)}</textarea></label>
    <h3>Golpes <button class="b mini" data-ia="add-golpe">＋ golpe</button></h3>
    ${x.golpes.map((g, i) => `<div class="linha-golpe"><label class="c">Nome<input data-g="${i}.nome" value="${esc(g.nome)}"></label><label class="c">Tipo de dano<select data-g="${i}.tipo">${optTipos(g.tipo)}</select></label>
      <label class="c">Alcance<input data-g="${i}.alcance" value="${esc(g.alcance)}" placeholder="corpo, 9 m…"></label><label class="c">Acerto +<input type="number" data-g="${i}.bonus" value="${g.bonus}"></label><label class="c" title="Dados do golpe, ex.: 13d10 + 4. Também aceita número fixo.">Dano (dados)<input data-g="${i}.dano" value="${esc(g.dano)}" placeholder="2d8 + 3"></label>
      <label class="c">Efeito<input data-g="${i}.efeito" value="${esc(g.efeito)}"></label><span class="linha"><select data-g="${i}.cond" title="Condição que o golpe aplica"><option value="">sem condição</option>${CFG.condicoes.map((c) => `<option ${g.cond === c ? "selected" : ""}>${c}</option>`).join("")}</select><button class="b mini perigo" data-ia="rem-golpe" data-i="${i}">✖</button></span></div>`).join("") || "<small>Sem golpes.</small>"}
    <h3>Habilidades <button class="b mini" data-ia="add-hab">＋ habilidade</button></h3>
    ${x.habilidades.map((h, i) => `<div class="linha-hab"><label class="c">Nome<input data-h="${i}.nome" value="${esc(h.nome)}"></label><label class="c">Ação<select data-h="${i}.acao">${["", "Comum", "Bônus", "Movimento", "Reação", "Completa", "Passiva"].map((a) => `<option ${h.acao === a ? "selected" : ""}>${a}</option>`).join("")}</select></label>
      <label class="c">Texto<textarea rows="2" data-h="${i}.texto">${esc(h.texto)}</textarea></label><button class="b mini perigo" data-ia="rem-hab" data-i="${i}">✖</button></div>`).join("") || "<small>Sem habilidades.</small>"}
    ${big ? `<h3>Pontos Chave (1 a 3) <button class="b mini" data-ia="add-pk" ${x.pontos_chave.length >= 3 ? "disabled" : ""}>＋ ponto chave</button></h3>
      ${x.pontos_chave.map((p, i) => `<div class="linha" style="margin-bottom:5px"><input data-p="${i}.nome" placeholder="parte do corpo / ponto fraco" value="${esc(p.nome)}"><input data-p="${i}.efeito" placeholder="efeito ao acertar" value="${esc(p.efeito)}" style="flex:1"><button class="b mini perigo" data-ia="rem-pk" data-i="${i}">✖</button></div>`).join("") || "<small>Nenhum.</small>"}` : ""}
    <h3>Defesas por tipo de dano</h3><details><summary>Resistências (metade do dano) · ${x.resistencias.length}</summary>${chipsTipos("resistencias")}</details>
    <details><summary>Imunidades (nenhum dano) · ${x.imunidades.length}</summary>${chipsTipos("imunidades")}</details><details><summary>Vulnerabilidades (+50%) · ${x.vulnerabilidades.length}</summary>${chipsTipos("vulnerabilidades")}</details>
    <h3>Afinidades de condição</h3><div class="grade g7">${CFG.condicoes.map((c) => `<label class="c">${c}<select data-af="${c}"><option value="">—</option>${CFG.afinidades.map((a) => `<option value="${a}" ${(x.afinidades[c] || "") === a ? "selected" : ""}>${a === "vulneravel" ? "vulnerável" : a}</option>`).join("")}</select></label>`).join("")}</div>
    ${big ? `<label class="c" style="margin-top:10px">Set e Drops (itens que cai, DT de coleta)<textarea rows="3" data-ef="set_drops">${esc(x.set_drops)}</textarea></label>` : ""}
    <label class="c" style="margin-top:8px">Anotações<textarea rows="3" data-ef="notas">${esc(x.notas)}</textarea></label>
    <div class="linha" style="margin-top:12px"><button class="b p" data-ia="salvar">💾 Salvar</button><button class="b" data-ia="dup" ${x.id ? "" : "disabled"}>Duplicar</button><button class="b" data-ia="combate" ${x.id ? "" : "disabled"}>⚔ Levar ao combate</button><button class="b perigo" data-ia="excluir" ${x.id ? "" : "disabled"} style="margin-left:auto">Excluir</button><span id="ed-ok" class="sub"></span></div></div>`;
  if (infoCalc) mostraInfo();
}
function mostraInfo() {
  const c = infoCalc, el = $("#calc-info"); if (!el) return;
  el.innerHTML = `Dano por turno: ${esc(c.dano_expr)} ≈ <b>${c.dano_turno}</b> em ${c.golpes} golpe(s) (≈ ${c.dano_golpe} cada, ${esc(c.dano_golpe_dados)}) · Resistências = Ataque (+${c.resistencia}) · Quantos aparecem: ${esc(c.quantos)}${c.extra_deus ? "<br>" + esc(c.extra_deus) : ""}`;
}
async function calcular(refazGolpes) {
  const x = ED, c = await api(`/api/calcular?tier=${encodeURIComponent(x.tier)}&nmp=${x.nmp}&jog=${x.jogadores}`);
  if (c.erro) { toast(esc(c.erro)); return; }
  infoCalc = c; Object.assign(x, { vida: c.vida, ca: c.ca, ataque: c.ataque, dt: c.dt, postura: c.postura, vida_condicao: c.vida_condicao, cond_por_golpe: c.cond_por_golpe });
  if (refazGolpes || !x.golpes.length) x.golpes = [...Array(c.golpes)].map((_, i) => ({ nome: c.golpes > 1 ? `Golpe ${i + 1}` : "Golpe", tipo: "", alcance: "", bonus: c.ataque, dano: c.dano_golpe_dados, efeito: "", cond: "", cond_pts: 0 }));
  else x.golpes.forEach((g) => { g.bonus = c.ataque; g.dano = c.dano_golpe_dados; });
  pintaEditor();
}
document.addEventListener("input", (ev) => {
  const el = ev.target; if (!ED || !$("#li-ed").contains(el)) return;
  if (el.dataset.ef) { const f = el.dataset.ef; ED[f] = el.type === "number" ? num(el.value) : el.value; }
  else if (el.dataset.g) { const [i, f] = el.dataset.g.split("."); ED.golpes[i][f] = el.type === "number" ? num(el.value) : el.value; }
  else if (el.dataset.h) { const [i, f] = el.dataset.h.split("."); ED.habilidades[i][f] = el.value; }
  else if (el.dataset.p) { const [i, f] = el.dataset.p.split("."); ED.pontos_chave[i][f] = el.value; }
  else if (el.dataset.af) { if (el.value) ED.afinidades[el.dataset.af] = el.value; else delete ED.afinidades[el.dataset.af]; }
});
document.addEventListener("change", (ev) => {
  const el = ev.target; if (!ED || !$("#li-ed").contains(el)) return;
  if (el.dataset.ef === "tier" || el.dataset.ef === "nmp" || el.dataset.ef === "jogadores") { if (!ED.id || confirm("Refazer Vida, CA, Ataque, DT, Postura e dano com a tabela do livro para esta classe e nível?")) calcular(!ED.id); }
  else if (el.dataset.g && el.dataset.g.endsWith(".cond") || el.dataset.g && el.dataset.g.endsWith(".tipo")) { /* já guardado */ }
});
document.addEventListener("click", async (ev) => {
  const el = ev.target.closest("[data-ia]"); if (!el) return;
  const a = el.dataset.ia;
  if (a === "novo") { ED = novoVazio(); infoCalc = null; await calcular(true); $$("#li-lista .item").forEach((i) => i.classList.remove("on")); }
  else if (a === "abrir") { ED = JSON.parse(JSON.stringify(LIB.find((x) => x.id === el.dataset.id))); infoCalc = null; $$("#li-lista .item").forEach((i) => i.classList.toggle("on", i === el)); pintaEditor(); }
  else if (!ED) return;
  else if (a === "calc") await calcular(true);
  else if (a === "add-golpe") { ED.golpes.push({ nome: "Golpe", tipo: "", alcance: "", bonus: ED.ataque, dano: (infoCalc ? infoCalc.dano_golpe_dados : "1d8"), efeito: "", cond: "", cond_pts: 0 }); pintaEditor(); }
  else if (a === "rem-golpe") { ED.golpes.splice(num(el.dataset.i), 1); pintaEditor(); }
  else if (a === "add-hab") { ED.habilidades.push({ nome: "", acao: "", texto: "" }); pintaEditor(); }
  else if (a === "rem-hab") { ED.habilidades.splice(num(el.dataset.i), 1); pintaEditor(); }
  else if (a === "add-pk") { if (ED.pontos_chave.length < 3) ED.pontos_chave.push({ nome: "", efeito: "" }); pintaEditor(); }
  else if (a === "rem-pk") { ED.pontos_chave.splice(num(el.dataset.i), 1); pintaEditor(); }
  else if (a === "tipo") { const l = ED[el.dataset.c], t = el.dataset.t; const i = l.indexOf(t); if (i >= 0) l.splice(i, 1); else { l.push(t); ["resistencias", "imunidades", "vulnerabilidades"].filter((c) => c !== el.dataset.c).forEach((c) => { ED[c] = ED[c].filter((x) => x !== t); }); } el.classList.toggle("on"); }
  else if (a === "salvar") {
    if (!ED.nome.trim()) { toast("Dê um nome ao inimigo."); return; }
    const r = await api("/api/inimigos", ED); if (r.item) { ED = r.item; await carregarLib(); $("#ed-ok").textContent = "salvo ✔"; renderInimigos(); }
  }
  else if (a === "dup") { const c = JSON.parse(JSON.stringify(ED)); c.id = ""; c.nome += " (cópia)"; const r = await api("/api/inimigos", c); ED = r.item; await renderInimigos(); }
  else if (a === "excluir") { if (confirm(`Excluir ${ED.nome} da biblioteca?`)) { await api("/api/inimigos/excluir", { id: ED.id }); ED = null; renderInimigos(); } }
  else if (a === "combate") { await api("/api/inimigos", ED); const qtd = num(prompt("Quantos " + ED.nome + " entram no combate?", ED.tier === "Lacaio" ? "3" : "1"), 1); await api("/api/combate/adicionar", { itens: [{ id: ED.id, qtd }] }); toast(`${qtd} × ${esc(ED.nome)} no combate.`, 2500); }
});

// ------------------------------------------------------------------ ANOTAÇÕES
let NOTA = null, tSalva = null;
async function renderNotas() {
  NOTAS = (await api("/api/notas")).itens || [];
  const raiz = $("#aba-notas"), busca = ($("#ln-busca") || {}).value || "", tag = ($("#ln-tag") || {}).value || "";
  const tags = [...new Set(NOTAS.map((n) => n.etiqueta).filter(Boolean))].sort();
  raiz.innerHTML = `<div class="lista-esq"><div><div class="linha" style="margin-bottom:8px"><button class="b p" data-na="nova">＋ Nova anotação</button></div>
    <div class="linha" style="margin-bottom:8px"><input id="ln-busca" placeholder="Buscar no texto…" value="${esc(busca)}" style="flex:1"><select id="ln-tag"><option value="">Todas</option>${tags.map((t) => `<option ${t === tag ? "selected" : ""}>${esc(t)}</option>`).join("")}</select></div>
    <div id="ln-lista" class="nota-lista"></div></div><div id="ln-ed"></div></div>`;
  const pinta = () => {
    const b = $("#ln-busca").value.toLowerCase(), t = $("#ln-tag").value;
    const itens = NOTAS.filter((n) => (!t || n.etiqueta === t) && (!b || (n.titulo + " " + n.texto).toLowerCase().includes(b))).sort((a, b) => (b.fixa - a.fixa) || (b.em - a.em));
    $("#ln-lista").innerHTML = itens.length ? itens.map((n) => `<div class="item ${NOTA && NOTA.id === n.id ? "on" : ""}" data-na="abrir" data-id="${esc(n.id)}"><b>${n.fixa ? "📌 " : ""}${esc(n.titulo)}</b><small>${esc(n.etiqueta || "sem etiqueta")} · ${esc(n.texto.slice(0, 60).replace(/\n/g, " "))}</small></div>`).join("") : `<div class="vazio">Nenhuma anotação.</div>`;
  };
  $("#ln-busca").oninput = pinta; $("#ln-tag").onchange = pinta; pinta(); pintaNota();
}
function pintaNota() {
  const box = $("#ln-ed");
  if (!NOTA) { box.innerHTML = `<div class="painel vazio">Escolha uma anotação ou crie uma nova.<br><small>Guarda sozinha enquanto você escreve. Use etiquetas (NPC, Lugar, Enredo, Regras…) para achar depois.</small></div>`; return; }
  box.innerHTML = `<div class="painel"><div class="grade g3"><label class="c" style="grid-column:span 2">Título<input id="n-t" value="${esc(NOTA.titulo)}"></label><label class="c">Etiqueta<input id="n-e" list="n-etiquetas" value="${esc(NOTA.etiqueta)}"><datalist id="n-etiquetas">${["NPC", "Lugar", "Enredo", "Regras", "Sessão", "Loot", "Ideias"].map((x) => `<option>${x}</option>`).join("")}</datalist></label></div>
    <label class="c" style="margin-top:8px">Texto<textarea id="n-x" rows="22">${esc(NOTA.texto)}</textarea></label>
    <div class="linha" style="margin-top:8px"><label><input type="checkbox" id="n-f" ${NOTA.fixa ? "checked" : ""}> fixar no topo</label><span id="n-ok" class="sub"></span><button class="b perigo" data-na="excluir" style="margin-left:auto">Excluir</button></div></div>`;
  const guarda = () => { NOTA.titulo = $("#n-t").value; NOTA.etiqueta = $("#n-e").value.trim(); NOTA.texto = $("#n-x").value; NOTA.fixa = $("#n-f").checked; $("#n-ok").textContent = "salvando…"; clearTimeout(tSalva); tSalva = setTimeout(async () => { const r = await api("/api/notas", NOTA); if (r.item) { NOTA.id = r.item.id; NOTA.em = r.item.em; const i = NOTAS.findIndex((n) => n.id === NOTA.id); if (i >= 0) NOTAS[i] = Object.assign({}, NOTA); else NOTAS.push(Object.assign({}, NOTA)); if ($("#n-ok")) $("#n-ok").textContent = "salvo ✔"; } }, 600); };
  ["#n-t", "#n-e", "#n-x"].forEach((s) => $(s).oninput = guarda); $("#n-f").onchange = guarda;
}
document.addEventListener("click", async (ev) => {
  const el = ev.target.closest("[data-na]"); if (!el) return;
  const a = el.dataset.na;
  if (a === "nova") { NOTA = { id: "", titulo: "Nova anotação", etiqueta: "", texto: "", fixa: false, em: 0 }; const r = await api("/api/notas", NOTA); NOTA = r.item; await renderNotas(); $("#n-t").select(); }
  else if (a === "abrir") { clearTimeout(tSalva); NOTA = Object.assign({}, NOTAS.find((n) => n.id === el.dataset.id)); $$("#ln-lista .item").forEach((i) => i.classList.toggle("on", i === el)); pintaNota(); }
  else if (a === "excluir" && NOTA && confirm("Excluir esta anotação?")) { await api("/api/notas/excluir", { id: NOTA.id }); NOTA = null; renderNotas(); }
});

// ------------------------------------------------------------------ começo
(async () => {
  CFG = await api("/api/config");
  await Promise.all([carregarLib(), atualizar()]);
  renderCombate();
})();
</script>
</body>
</html>
"""
