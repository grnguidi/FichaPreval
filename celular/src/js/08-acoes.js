// ------------------------------------------------------------------ ações

function setsAtivos() {
  const cont = {};
  for (const p of PECAS) { const n = (S.set[p] || {}).set; if (n && SETS[n]) cont[n] = (cont[n] || 0) + 1; }
  return cont;
}
function pBolsa() {
  const d = C.d, itens = S.inventario;
  const pesoItens = R.pesoInventario(itens), pesoSet = R.pesoPecasSet(S.set || {});
  const pesoArmas = S.armas.reduce((t, w) => { const ar = ARMAS[w.grupo]; const l = ar && ar.tabela.find((x) => x.nivel === int(w.nivel, 1)); return t + (l ? l.espaco : 0); }, 0);
  const pesoProt = (C.arm ? C.arm.peso : 0) + (C.esc ? C.esc.peso : 0) - (C.tal.has("Veterano de Armadura") && C.arm ? 2 : 0);
  const pesoTal = S.talismas.filter((t) => t.nome).length;
  const pct = Math.max(0, Math.min(100, (C.carga / Math.max(1, d.carga)) * 100));
  const cor = C.carga > d.carga || C.lentidao ? "var(--c-vida)" : C.exaustao ? "var(--c-per)" : "var(--c-vigor)";
  let h = secao("Equipamento") + ["armadura", "escudo"].map((t) => {
    const it = protecao(t), m = it ? statusProtecao(C, t, it) : [];
    return `<div style="margin-bottom:8px"><button class="sel ${it ? "" : "vazio"}" data-a="esc-protecao" data-t="${t}">${it ? `${esc(it.nome)} · CA +${it.ca} · peso ${it.peso}` : t === "armadura" ? "Sem armadura" : "Sem escudo"}</button>
      ${m.length ? `<div class="erro" style="font-size:13.5px;margin:3px 2px">${NO} ${esc(m.join(", "))}</div>` : ""}</div>`;
  }).join("") + `<p class="sub">CA ${d.ca} = 10 + armadura ${C.arm ? C.arm.ca : 0} + escudo ${C.esc ? C.esc.ca : 0} + Tenacidade ${d.ca_ten}${int(S.equip.ca_extra) ? ` + outros ${int(S.equip.ca_extra)}` : ""}${C.esc ? ". Escudo: como reação, +2 de CA contra um ataque" + (C.esc.nome === "Escudo Pequeno" ? " ou Parry (contra-ataque com vantagem se o inimigo errar)" : "") : ""}</p>`;
  h += secao("Talismãs", `${S.talismas.filter((t) => t.nome).length}/${d.talismas}`) + `<div class="lista">${S.talismas.slice(0, Math.max(d.talismas, S.talismas.filter((t) => t.nome).length)).map((t, i) => {
    const info = TALISMA[t.nome];
    return `<div class="item ${i >= d.talismas ? "bloq" : ""}" data-a="esc-talisma" data-i="${i}"><span class="marca" style="color:var(--ouro)">✦</span><div class="tx"><b>${esc(t.nome || "Vazio")}</b><small>${esc(info ? info.efeito : t.nome ? t.efeito : "toque para escolher")}</small></div><span class="sub">›</span></div>`;
  }).join("")}</div>`;
  h += secao("Carga", `${C.carga} / ${d.carga}`) + `<div class="cartao" style="padding:12px">
    <div class="barra grossa"><i style="width:${pct}%;background:${cor}"></i></div>
    <p class="sub" style="margin:8px 0 0">Itens ${pesoItens} · armas ${pesoArmas} · proteção ${pesoProt} · talismãs ${pesoTal}${pesoSet ? ` · peças de set ${pesoSet}` : ""}${R.cargaExtraItens(itens, ITENS) ? ` · mochila +${R.cargaExtraItens(itens, ITENS)} de capacidade` : ""}
    ${C.lentidao ? `<br><b class="erro">Lentidão</b>: movimento preso em 6 m.` : C.exaustao ? `<br><b class="erro">Exaustão</b>: 10 ou menos de carga livre.` : ""}</p></div>`;
  const mo = R.separarMoedas(S.dinheiro_c);
  h += `<div class="cartao dinheiro" data-a="dinheiro"><span>Dinheiro</span><b>${esc(R.formatarDinheiro(S.dinheiro_c))}</b><small>toque para mudar</small></div>
    <div class="moedas">${R.MOEDAS.map((k) => `<span class="chip">${mo[k]} ${k === "Contos" ? "Contos" : k === "Contilha" ? "Contilha" : "de " + k}</span>`).join("")}</div>
    ${S.dinheiro_nota ? `<p class="sub">Anotação antiga: ${esc(S.dinheiro_nota)}</p>` : ""}`;
  h += secao("Itens", `${itens.length}/30`) + (itens.length ? `<div class="lista">${itens.map((it, i) =>
    { const info = itemLivro(it.item), q = Math.max(1, int(it.qtd, 1)), usa = info && info.uso && info.uso.consome;
      return `<div class="item" data-a="item" data-i="${i}"><span class="marca" style="color:var(--ouro)">◆</span><div class="tx"><b>${q > 1 ? q + "× " : ""}${esc(it.item || "Sem nome")}</b>${info ? `<small>${esc(info.desc.slice(0, 70))}${info.desc.length > 70 ? "…" : ""}</small>` : ""}</div>
        ${usa ? `<button class="botao prim mini" data-a="usar-item" data-i="${i}">Usar</button>` : ""}<span class="num">${(parseFloat(String(it.carga || 0).replace(",", ".")) || 0) * q}</span></div>`; }).join("")}</div>`
    : `<div class="vazio-msg">A bolsa está vazia.</div>`)
    + `<div class="linhabts"><button class="botao prim" data-a="item" data-i="-1" ${itens.length >= 30 ? "disabled" : ""}>＋ Adicionar item</button><button class="botao" data-a="comprar">🛒 Comprar do livro</button></div>`;
  const cont = setsAtivos();
  h += secao("Peças de set") + `<div class="lista">${PECAS.map((p) => {
    const x = S.set[p] || {};
    return `<div class="item" data-a="peca" data-p="${p}"><div class="tx"><b>${p}</b><small>${x.set && SETS[x.set] ? `Set ${esc(x.set)}${x.nome ? " · " + esc(x.nome) : ""}` : x.nome ? esc(x.nome) : "sem peça de set"}</small></div><span class="sub so-ed">›</span></div>`;
  }).join("")}</div>`;
  const at = Object.entries(cont).filter(([, q]) => q >= 2).sort((a, b) => b[1] - a[1]);
  h += at.length ? `<div class="lista">${at.map(([n, q]) => `<div class="item" style="display:block"><b style="color:var(--vinho)">Set ${esc(n)} — ${q} peças</b>
      <div class="sub" style="margin-top:3px"><b>2 peças:</b> ${esc(SETS[n].p2)}${q >= 4 ? `<br><b>4 peças:</b> ${esc(SETS[n].p4)}` : `<br><span style="opacity:.7">4 peças: falta ${4 - q}</span>`}</div></div>`).join("")}</div>`
    : `<p class="sub">Duas peças do mesmo set ativam o bônus de 2; quatro ativam o de 4.</p>`;
  return h;
}
A["dinheiro"] = () => {
  const mo = R.separarMoedas(S.dinheiro_c);
  folha("Dinheiro", `<p class="sub">10 Contos = 1 de prata · 100 de prata = 1 de ouro · 1000 de ouro = 1 Contilha. Pode digitar sem converter: a ficha arruma.</p>
    <div class="grade g2">${R.MOEDAS.map((k) => `<label class="campo"><span>${k === "Contos" ? "Contos" : k === "Contilha" ? "Contilhas" : "Contos de " + k}</span><input class="din" data-k="${k}" type="number" inputmode="numeric" min="0" value="${mo[k]}"></label>`).join("")}</div>
    <label class="campo"><span>Ganhar ou gastar (ex.: +2 de ouro, -35 de prata)</span><input id="din-mov" placeholder="+15 contos"></label>`,
  `<button class="botao leve" data-a="fechar">Cancelar</button><button class="botao prim" data-a="dinheiro-ok">Salvar</button>`);
};
A["dinheiro-ok"] = () => {
  let total = [...document.querySelectorAll(".din")].reduce((t, x) => t + Math.max(0, int(x.value)) * R.CONTOS_POR[x.dataset.k], 0);
  const mov = $("#din-mov").value.trim();
  if (mov) { const v = R.lerDinheiro(mov); if (v != null) total += mov.startsWith("-") || mov.startsWith("−") ? -v : v; }
  fecharFolha();
  mudar((s) => { s.dinheiro_c = Math.max(0, total); s.dinheiro = R.formatarDinheiro(s.dinheiro_c); delete s.dinheiro_nota; });
};
A["comprar"] = () => {
  const cats = [...new Set(ITENS.map((x) => x.categoria))];
  folha("Comprar do livro", `<p class="meta">Você tem ${esc(R.formatarDinheiro(S.dinheiro_c))}.</p>` + cats.map((c) => `<div class="secao">${esc(c)}</div><div class="lista">${ITENS.filter((x) => x.categoria === c).map((x) => {
    const pr = R.precoEmContos(x.preco);
    return `<div class="item ${pr != null && pr > S.dinheiro_c ? "bloq" : ""}" data-a="comprar-item" data-n="${esc(x.nome)}"><div class="tx"><b>${esc(x.nome)}</b><small>${esc(x.preco)} · peso ${x.peso}</small></div><span class="sub">›</span></div>`;
  }).join("")}</div>`).join(""));
};
A["comprar-item"] = (el) => {
  const x = itemLivro(el.dataset.n), pr = R.precoEmContos(x.preco) || 0;
  folha(esc(x.nome), `<div class="desc">${esc(x.desc)}</div><p class="meta">${esc(x.preco)} cada · peso ${x.peso}</p>
    <label class="campo"><span>Quantidade</span><input id="cp-q" type="number" inputmode="numeric" min="1" value="1"></label>
    <p class="sub" id="cp-t"></p>`,
  `<button class="botao leve" data-a="comprar">‹ Lista</button><button class="botao prim" data-a="comprar-ok" data-n="${esc(x.nome)}">Comprar</button>`, (c) => {
    const at = () => { const q = Math.max(1, int($("#cp-q").value, 1)); $("#cp-t").innerHTML = `Total: <b>${esc(R.formatarDinheiro(pr * q))}</b> · você tem ${esc(R.formatarDinheiro(S.dinheiro_c))}${pr * q > S.dinheiro_c ? ` · <b class="erro">não dá</b>` : ""}`; };
    c.querySelector("#cp-q").addEventListener("input", at); at();
  });
};
A["comprar-ok"] = (el) => {
  const x = itemLivro(el.dataset.n), q = Math.max(1, int($("#cp-q").value, 1)), total = (R.precoEmContos(x.preco) || 0) * q;
  if (total > S.dinheiro_c && !el.dataset.ok) { $("#cp-t").innerHTML += `<br><b class="erro">Falta dinheiro. Toque em Comprar de novo para comprar mesmo assim (fica 0).</b>`; el.dataset.ok = "1"; return; }
  fecharFolha();
  mudar((s) => {
    s.dinheiro_c = Math.max(0, s.dinheiro_c - total); s.dinheiro = R.formatarDinheiro(s.dinheiro_c);
    const ja = s.inventario.find((y) => String(y.item || "").toLowerCase() === x.nome.toLowerCase());
    if (ja) ja.qtd = String(Math.max(1, int(ja.qtd, 1)) + q); else s.inventario.push({ item: x.nome, carga: String(x.peso), qtd: String(q) });
  });
  registrarDiario({ titulo: "🛒 Compra", linhas: [`${q}× ${esc(x.nome)} por ${esc(R.formatarDinheiro(total))}.`, `Restam ${esc(R.formatarDinheiro(S.dinheiro_c))}.`] });
  toast(`Comprou ${q}× <b>${esc(x.nome)}</b>.`);
};
A["item"] = (el) => {
  const i = int(el.dataset.i, -1), it = S.inventario[i] || { item: "", carga: "", qtd: "1" };
  const cats = [...new Set(ITENS.map((x) => x.categoria))];
  const lista = `<label class="campo"><span>Do livro</span><select id="it-l"><option value="">— item personalizado —</option>${cats.map((c) =>
    `<optgroup label="${esc(c)}">${ITENS.filter((x) => x.categoria === c).map((x) => `<option ${x.nome === it.item ? "selected" : ""}>${esc(x.nome)}</option>`).join("")}</optgroup>`).join("")}</select></label>`;
  folha(i < 0 ? "Novo item" : "Item", lista + `<label class="campo"><span>Item</span><input id="it-n" value="${esc(it.item)}"></label>
    <div style="display:flex;gap:10px"><label class="campo" style="flex:1"><span>Quantidade</span><input id="it-q" type="number" inputmode="numeric" min="1" value="${esc(it.qtd || "1")}"></label>
    <label class="campo" style="flex:1"><span>Peso (cada)</span><input id="it-c" type="number" inputmode="decimal" step="0.5" value="${esc(it.carga)}"></label></div>
    <p class="sub" id="it-d"></p>`,
  `${i >= 0 ? `<button class="botao leve" data-a="item-rem" data-i="${i}">Remover</button>` : `<button class="botao leve" data-a="fechar">Cancelar</button>`}<button class="botao prim" data-a="item-ok" data-i="${i}">Salvar</button>`, (c) => {
    const mostra = (preencher) => {
      const x = itemLivro($("#it-l").value);
      $("#it-d").innerHTML = x ? `${esc(x.desc)} <i>(${esc(x.preco)})</i>` : "";
      if (x && preencher) { $("#it-n").value = x.nome; $("#it-c").value = String(x.peso); }
    };
    c.querySelector("#it-l").addEventListener("change", () => mostra(true)); mostra(false);
  });
};
A["item-ok"] = (el) => {
  const i = int(el.dataset.i, -1), n = $("#it-n").value.trim(), c = $("#it-c").value.trim(), q = String(Math.max(1, int($("#it-q").value, 1)));
  fecharFolha(); if (!n && !c) return;
  mudar((s) => { const x = { item: n, carga: c, qtd: q }; if (i < 0) s.inventario.push(x); else s.inventario[i] = x; });
};
function usarItem(i) {
  const it = S.inventario[i], info = itemLivro(it && it.item); if (!info || !info.uso) return [];
  const u = info.uso, linhas = [];
  for (const k of ["mana", "vigor"]) if (u[k]) {
    const ch = k + "_atual", mx = C.d[k], antes = S.vida[ch] === "" || S.vida[ch] == null ? mx : int(S.vida[ch], mx);
    const ganho = u[k] === "tudo" ? mx - antes : R.rolarExpr(String(u[k]), rng)[0];
    desfazer.push({ chave: ch, antigo: S.vida[ch], desc: info.nome });
    S.vida[ch] = String(Math.min(mx, antes + ganho)); linhas.push(`${k === "mana" ? "Mana" : "Vigor"}: ${antes} → ${Math.min(mx, antes + ganho)}`);
  }
  if (u.condicao) {
    const c = S.condicoes[u.condicao], antes = int(c.atual), depois = Math.max(0, antes - u.pontos);
    c.atual = depois ? String(depois) : ""; linhas.push(`${u.condicao}: ${antes} → ${depois}`);
  }
  const q = Math.max(1, int(it.qtd, 1));
  if (q > 1) it.qtd = String(q - 1); else S.inventario.splice(i, 1);
  linhas.push(q > 1 ? `Restam ${q - 1}.` : "Era o último.");
  salvar(); render();
  return linhas;
}
A["usar-item"] = (el, ev) => {
  if (ev) ev.stopPropagation();
  const it = S.inventario[int(el.dataset.i)], nome = it ? it.item : "";
  const linhas = usarItem(int(el.dataset.i));
  const info = itemLivro(nome), m = info && info.desc.toLowerCase().match(/a[çc][ãa]o (b[ôo]nus|comum|completa)/);
  const aviso = marcarAcao(m ? { "bônus": "Bônus", "bonus": "Bônus", comum: "Comum", completa: "Completa" }[m[1]] : "Comum");
  if (linhas.length) mostrarRolagem(`⚗ ${esc(nome)}`, linhas.concat(aviso ? [`<span class="erro">${aviso}</span>`] : [], [`<span class="sub">${esc(D.itens_regras || "")}</span>`]));
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


