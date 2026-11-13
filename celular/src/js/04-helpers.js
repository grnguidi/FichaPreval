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

