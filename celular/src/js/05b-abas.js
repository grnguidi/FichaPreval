// ------------------------------------------------------------------ abas: 5 fixas (+ Grupo na sessão), cada uma com sub-abas
// A barra de baixo responde a uma pergunta por aba; as páginas antigas viram sub-abas. As seções de cada página
// viram blocos que abrem e fecham (o app lembra), e os textos de ajuda (p.ajuda) ficam atrás de um "?".
const IC = {   // ícones de traço, todos do mesmo desenho (24×24, cor do texto)
  ficha: '<path d="M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8z"/><path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6"/>',
  combate: '<path d="M4 4l10 10M4 4h4M4 4v4M20 4L10 14M20 4h-4M20 4v4M7 17l-3 3M17 17l3 3M8 13l3 3M16 13l-3 3"/>',
  saberes: '<path d="M4 5.5C4 4.7 4.7 4 5.5 4H11v16H5.5c-.8 0-1.5-.7-1.5-1.5v-13zM20 5.5c0-.8-.7-1.5-1.5-1.5H13v16h5.5c.8 0 1.5-.7 1.5-1.5v-13z"/><path d="M7 8h2M15 8h2M7 11h2M15 11h2"/>',
  bolsa: '<path d="M7 8V6a5 5 0 0 1 10 0v2"/><rect x="4" y="8" width="16" height="13" rx="3"/><path d="M9 13h6"/>',
  diario: '<path d="M6 3h11a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6z"/><path d="M6 3v18M9 8h6M9 12h6M9 16h3"/>',
  grupo: '<path d="M9 11a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7zM2.5 20c1-3.5 3.5-5 6.5-5s5.5 1.5 6.5 5"/><path d="M16 4.5a3 3 0 0 1 0 6M18 14.5c2 .6 3.2 2.3 3.6 5"/>',
};
const icone = (k) => `<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${IC[k]}</svg>`;
const ABAS = {
  ficha: { rot: "Ficha", subs: [["resumo", "Resumo"], ["atributos", "Atributos"], ["especie", "Espécie e alma"]] },
  combate: { rot: "Combate", subs: [["turno", "Turno"], ["armas", "Armas"], ["magias", "Magias"], ["defesas", "Defesas"]] },
  saberes: { rot: "Saberes", subs: [["pericias", "Perícias"], ["talentos", "Talentos"], ["grimorio", "Grimório"]] },
  bolsa: { rot: "Bolsa", subs: [["itens", "Itens"], ["equip", "Equipamento"], ["dinheiro", "Dinheiro"]] },
  diario: { rot: "Diário", subs: [["notas", "Notas"], ["rolagens", "Rolagens"], ["metas", "Metas e vínculos"]] },
  grupo: { rot: "Grupo", subs: [] },
};
// nomes antigos de aba (botões, avisos e o Layout de mesa ainda podem pedir por eles)
const ALIAS_ABA = { pericias: ["saberes", "pericias"], grimorio: ["saberes", "grimorio"], talentos: ["saberes", "talentos"], alma: ["ficha", "especie"],
  notas: ["diario", "notas"], turno: ["combate", "turno"], metas: ["diario", "metas"], rolagens: ["diario", "rolagens"] };
function irPara(a, s) {
  if (ALIAS_ABA[a]) [a, s] = ALIAS_ABA[a];
  aba = ABAS[a] ? a : "ficha";
  banco.subs = banco.subs || {};
  if (s) banco.subs[aba] = s;
}
function subAtual() {
  const subs = ABAS[aba] ? ABAS[aba].subs : [];
  const s = (banco.subs || {})[aba];
  return subs.some((x) => x[0] === s) ? s : (subs[0] || [""])[0];
}
function montarNav() {
  const nav = $("#nav"); if (!nav || nav.dataset.ok) return;
  nav.innerHTML = Object.entries(ABAS).map(([k, a]) => `<button data-a="aba" data-aba="${k}" ${k === "grupo" ? 'id="nav-grupo" class="oculto"' : ""}>${icone(k)}<span>${a.rot}</span><b class="ponto" hidden></b></button>`).join("");
  nav.dataset.ok = "1";
}
// avisos nas próprias abas
function pintarPontos() {
  const marca = (k, on, t) => { const b = document.querySelector(`#nav [data-aba="${k}"] .ponto`); if (b) { b.hidden = !on; b.title = on ? t : ""; } };
  if (!S || !C) { ["ficha", "combate", "bolsa", "saberes"].forEach((k) => marca(k, false)); return; }
  marca("combate", !!(sessao.ativa && sessao.vez && sessao.vez === sessao.id), "Sua vez");
  marca("bolsa", C.carga > C.d.carga || !!C.lentidao, "Carga acima do limite");
  marca("ficha", C.resto > 0, "Pontos para distribuir");
}

// ---- páginas: cada página antiga é cortada nas suas seções, e as sub-abas escolhem quais mostrar
function secoesDe(html) {
  const d = document.createElement("div"); d.innerHTML = html;
  const out = []; let cur = { titulo: "", extra: "", nos: [] }; out.push(cur);
  for (const e of [...d.children]) {
    if (e.classList.contains("secao")) {
      const ex = e.querySelector(".extra"); if (ex) ex.remove();
      cur = { titulo: e.textContent.trim(), extra: ex ? ex.innerHTML : "", nos: [] }; out.push(cur);
    } else cur.nos.push(e);
  }
  return out.filter((s) => s.titulo || s.nos.length);
}
const pegar = (secs, titulos) => secs.filter((s) => titulos.includes(s.titulo));
const tirar = (secs, titulos) => secs.filter((s) => !titulos.includes(s.titulo));
function blocoHtml(s, chave) {
  const ajuda = s.nos.filter((n) => n.matches("p.ajuda")), resto = s.nos.filter((n) => !n.matches("p.ajuda"));
  const corpo = resto.map((n) => n.outerHTML).join("");
  if (!s.titulo) return corpo;
  const k = `${chave}:${s.titulo}`, fechado = !!(banco.fechados || {})[k];
  return `<section class="bloco ${fechado ? "fechado" : ""}">
    <div class="secao bloco-cab" data-a="bloco" data-k="${esc(k)}" role="button" aria-expanded="${fechado ? "false" : "true"}">${capitular(s.titulo)}${s.extra ? `<span class="extra">${s.extra}</span>` : ""}
      ${ajuda.length ? `<button class="ajuda-bt" data-a="ajuda" aria-label="O que é isto?">?</button>` : ""}<span class="chev" aria-hidden="true"></span></div>
    ${ajuda.length ? `<div class="ajuda-txt" hidden>${ajuda.map((n) => n.innerHTML).join("<br>")}</div>` : ""}
    <div class="bloco-corpo">${corpo}</div></section>`;
}
const montar = (secs) => secs.map((s) => blocoHtml(s, `${aba}/${subAtual()}`)).join("");
A["bloco"] = (el) => {
  const sec = el.closest(".bloco"); if (!sec) return;
  const fechado = sec.classList.toggle("fechado");
  el.setAttribute("aria-expanded", fechado ? "false" : "true");
  banco.fechados = banco.fechados || {};
  if (fechado) banco.fechados[el.dataset.k] = 1; else delete banco.fechados[el.dataset.k];
  gravarLocal();
};
A["ajuda"] = (el, ev) => {
  if (ev) ev.stopPropagation();
  const t = el.closest(".bloco").querySelector(".ajuda-txt"); if (t) t.hidden = !t.hidden;
  el.classList.toggle("on", t && !t.hidden);
};

function pEspecie() {
  const ajustes = R.ATRIBUTOS.map((k) => [k, int(S.atributos[k].especie)]).filter(([, n]) => n).map(([k, n]) => `${n > 0 ? "+" : "−"}${Math.abs(n)} ${R.NOMES_ATR[k]}`);
  const notas = String(S.especie_notas || "").trim();
  return secao("Espécie") + `<div class="cartao" style="padding:12px 14px" ${banco.modo === "edicao" ? 'data-a="especie-editar"' : ""}>
      <b style="font-size:17px">${esc(S.identidade.especie || "Espécie não anotada")}</b>${ajustes.length ? `<div class="sub" style="margin-top:2px">${ajustes.join(" · ")}</div>` : ""}
      <p style="margin:8px 0 0;line-height:1.45">${notas ? esc(notas).replace(/\n/g, "<br>") : '<span class="sub">Sem par descritivo anotado (vantagem e desvantagem).</span>'}</p>
      ${banco.modo === "edicao" ? '<div class="sub" style="margin-top:6px">Toque para editar.</div>' : ""}</div>`;
}
A["especie-editar"] = () => folha("Espécie", `<label class="campo"><span>Espécie</span><input id="es-n" value="${esc(S.identidade.especie || "")}"></label>
  <label class="campo"><span>Vantagem e desvantagem</span><textarea id="es-t" rows="6" style="width:100%">${esc(S.especie_notas || "")}</textarea></label>
  <p class="sub">Os pontos de atributo da espécie ficam na sub-aba Atributos.</p>`, `<button class="botao prim" data-a="especie-ok">Salvar</button>`);
A["especie-ok"] = () => { const n = $("#es-n").value.trim(), t = $("#es-t").value; fecharFolha(); mudar((s) => { s.identidade.especie = n; s.especie_notas = t; }); };

function pMagias() {   // Combate › Magias: o que dá para conjurar agora, em um toque
  const ops = [];
  S.encantamentos.forEach((x) => { const e = ENC[x.familia]; if (e) e.versoes.filter((v) => x.versoes.includes(v.nivel)).forEach((v) => ops.push({ e, v, eq: x.equipado })); });
  ops.sort((a, b) => (b.eq - a.eq) || a.e.nome.localeCompare(b.e.nome) || a.v.nivel - b.v.nivel);
  const mana = S.vida.mana_atual === "" || S.vida.mana_atual == null ? C.d.mana : int(S.vida.mana_atual, C.d.mana);
  let h = secao("Magias", `Mana ${mana}/${C.d.mana}`);
  if (!ops.length) return h + `<p class="vazio">Nenhum encantamento aprendido ainda.</p><button class="botao leve" data-a="aba" data-aba="grimorio" style="width:100%">Abrir o Grimório</button>`;
  h += `<div class="lista">${ops.map((o) => { const custo = custoEnc(o.e, o.v)[0], falta = custo > mana;
    return `<div class="item ${falta ? "apagado" : ""}" data-a="conjurar" data-f="${esc(o.e.nome)}" data-v="${o.v.nivel}"><span class="marca">✧</span>
      <div class="tx"><b>${esc(o.e.nome)}</b><small>${esc(o.v.tier)} nv ${o.v.nivel} · ${esc(o.v.mana)} · ${esc(o.v.acao)}${o.v.distancia ? " · " + esc(o.v.distancia) : ""}${o.eq ? "" : " · não equipado"}${falta ? " · falta mana" : ""}</small></div><span class="sub">🎲</span></div>`; }).join("")}</div>
    <p class="sub ajuda">Toque para conjurar: a Mana e a ação são gastas sozinhas. Para aprender e equipar, use Saberes › Grimório.</p>`;
  return h;
}
function pRolagens() {
  const lista = S.diario.length ? `<div class="lista">${S.diario.map((r) => `<div class="item" style="display:block"><b style="color:var(--vinho)">${esc(r.titulo)}</b> <span class="sub">${r.hora}</span><div style="font-size:14px;line-height:1.5;margin-top:4px">${r.linhas.join("<br>")}</div></div>`).join("")}</div>`
    : `<p class="vazio">Nenhuma rolagem ainda.</p>`;
  return secao("Rolagens", `${S.diario.length} registradas`) + lista
    + `<div class="linhabts" style="margin-top:10px">${desfazer.length ? `<button class="botao leve" data-a="desfazer">↺ Desfazer último custo</button>` : ""}${S.diario.length ? `<button class="botao leve" data-a="diario-limpar">Limpar</button>` : ""}</div>`;
}

function paginaAtual() {
  const s = subAtual();
  if (aba === "ficha") {
    const f = secoesDe(pFicha());
    if (s === "atributos") return montar(pegar(f, ["Atributos"]));
    if (s === "especie") return montar(secoesDe(pEspecie() + (S.sem_alma ? "" : pAlma())));
    return montar(tirar(f, ["Atributos"]));
  }
  if (aba === "combate") {
    const c = secoesDe(pCombate());
    if (s === "turno") return montar(pegar(c, ["Rolar"]).concat(secoesDe(pTurno())));
    if (s === "armas") return montar(pegar(c, ["Armas", "Ataque sem arma"]));
    if (s === "magias") return montar(secoesDe(pMagias()));
    return montar(tirar(c, ["Rolar", "Turno", "Usos", "Armas", "Ataque sem arma"]));
  }
  if (aba === "saberes") {
    if (s === "talentos") return montar(tirar(secoesDe(pTalentos()), ["Metas de Vida", "Vínculos"]));
    if (s === "grimorio") return montar(secoesDe(pGrimorio()));
    return montar(secoesDe(pPericias()));
  }
  if (aba === "bolsa") {
    const b = secoesDe(pBolsa());
    const dinheiro = [];
    b.forEach((x) => { x.nos = x.nos.filter((n) => { const m = n.matches(".dinheiro, .moedas"); if (m) dinheiro.push(n); return !m; }); });
    if (s === "dinheiro") return montar([{ titulo: "Dinheiro", extra: "", nos: dinheiro }]);
    if (s === "equip") return montar(tirar(b, ["Carga", "Itens"]));
    return montar(pegar(b, ["Carga", "Itens"]));
  }
  if (aba === "diario") {
    if (s === "rolagens") return montar(secoesDe(pRolagens()));
    if (s === "metas") return montar(pegar(secoesDe(pTalentos()), ["Metas de Vida", "Vínculos"]));
    return montar(secoesDe(pNotas()));
  }
  if (aba === "grupo") return pGrupo();
  return pFicha();
}
function barraSub() {
  const a = ABAS[aba], s = subAtual(), ed = banco.modo === "edicao";
  const subs = a.subs.map(([k, r]) => [k, k === "especie" && S.sem_alma ? "Espécie" : r]);
  return `<div class="subabas" id="subabas"><div class="seg" role="tablist">${subs.length ? subs.map(([k, r]) => `<button role="tab" aria-selected="${k === s}" class="${k === s ? "on" : ""}" data-a="sub" data-s="${k}">${r}</button>`).join("") : `<b class="seg-tit">${a.rot}</b>`}</div>
    <button class="modo-pill ${ed ? "ed" : ""}" data-a="modo" aria-label="${ed ? "Voltar ao Modo Jogo" : "Editar a ficha"}">${ed ? "⚔ Jogar" : "✎ Editar"}</button></div>`;
}
A["sub"] = (el) => { banco.subs = banco.subs || {}; banco.subs[aba] = el.dataset.s; gravarLocal(); render(); window.scrollTo(0, 0); mostrarSubAtiva(); };
function medirTopo() { const t = document.querySelector(".topo"); if (t) document.documentElement.style.setProperty("--topo-h", t.offsetHeight + "px"); }
window.addEventListener("resize", medirTopo);

// a rosácea do cabeçalho dá uma volta a cada rolagem
let timerRosa;
function girarRosacea() {
  const h = document.documentElement; h.classList.remove("rolando"); void h.offsetWidth; h.classList.add("rolando");
  clearTimeout(timerRosa); timerRosa = setTimeout(() => h.classList.remove("rolando"), 1300);
}
