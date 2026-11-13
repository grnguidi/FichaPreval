// ------------------------------------------------------------------ modo jogo / edição
const SO_EDICAO = new Set(["hab-editar", "hab-ok", "hab-rem", "alma-ident-ok", "meta-n", "meta-perder", "extras-ok", "esc-props", "props-ok", "tal-escolha", "nivel", "pts", "manual", "modo-vida", "rolar-vida", "esc-arma", "esc-nivel-arma", "esc-protecao", "esc-talisma",
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
function opcoesEscolha(sl) {
  const tipo = R.ESCOLHA_TALENTO[S.talentos[sl]];
  if (tipo === "arma") { const eq = armasEq(); return eq.concat(D.armas.map((a) => a.nome).filter((n) => !eq.includes(n))); }
  if (tipo === "escola" || tipo === "escola_ou_mana") {
    const con = [...new Set(S.encantamentos.filter((x) => ENC[x.familia]).map((x) => ENC[x.familia].categoria))];
    const todas = [...new Set(D.encantamentos.map((e) => e.categoria))].sort();
    return (tipo === "escola_ou_mana" ? [R.MATRICULA_MANA2] : []).concat(con, todas.filter((c) => !con.includes(c)));
  }
  if (tipo === "condicao") return R.CONDICOES.slice();
  if (tipo === "pericia") return S.pericias.length ? S.pericias.slice().sort() : R.PERICIAS.map((p) => p[0]);
  return [];
}
A["tal-escolha"] = (el, ev) => {
  if (ev) ev.stopPropagation();
  const sl = el.dataset.s, nome = S.talentos[sl], atual = S.talentos_escolha[sl] || "";
  folha(`${nome}: ${R.ROTULO_ESCOLHA[R.ESCOLHA_TALENTO[nome]].toLowerCase()}`, `<p class="sub">${esc((TAL[nome] || {}).descricao || "")}</p><div class="lista">${opcoesEscolha(sl).map((o) =>
    `<div class="item" data-a="tal-escolha-ok" data-s="${sl}" data-v="${esc(o)}"><span class="check ${o === atual ? "on" : ""}"></span><div class="tx"><b>${esc(o)}</b></div></div>`).join("")}</div>`);
};
A["tal-escolha-ok"] = (el) => { const sl = el.dataset.s, v = el.dataset.v; fecharFolha(); mudar((s) => { s.talentos_escolha[sl] = v; }); };
A["tal-ativo"] = (el, ev) => { ev.stopPropagation(); const n = el.dataset.n; mudar((s) => { s.talentos_ativos = s.talentos_ativos.includes(n) ? s.talentos_ativos.filter((x) => x !== n) : s.talentos_ativos.concat([n]); }); };

