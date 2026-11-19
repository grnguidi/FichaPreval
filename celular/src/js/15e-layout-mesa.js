// ------------------------------------------------------------------ Layout de mesa (opcional, liga no menu como o tema)
// Três peças para a hora da luta: a aba Turno (ações, favoritos e o fim do turno numa tela só), a faixa de vitais
// sempre visível no alto e o dado flutuante. A preferência é do aparelho (banco.layout); os favoritos vão na ficha.
const layoutOn = () => !!banco.layout && !!S;
function aplicarLayout() {
  const on = layoutOn();
  document.documentElement.classList.toggle("layout-mesa", on);
  pintarFaixaVitais(); pintarDadoFlutuante();
}
A["layout"] = () => {
  banco.layout = !banco.layout; gravarLocal(); fecharFolha();
  if (banco.layout && S) irPara("combate", "turno");
  render();
  toast(banco.layout ? "Layout de mesa ligado: Combate abre no Turno, vitais sempre à vista e o dado flutuante." : "Layout de mesa desligado.");
};

// --- favoritos: armas, encantamentos e perícias, guardados na ficha
const chaveFav = (f) => `${f.t}:${f.k}`;
function opcoesFav() {
  const ops = [];
  S.armas.forEach((w, i) => { if (ARMAS[w.grupo]) ops.push({ t: "arma", k: String(i), nome: `${w.grupo} nv ${int(w.nivel, 1)}`, sub: "Atacar" }); });
  S.encantamentos.forEach((x) => {
    const e = ENC[x.familia]; if (!e) return;
    e.versoes.filter((v) => x.versoes.includes(v.nivel)).forEach((v) => ops.push({ t: "enc", k: `${e.nome}|${v.nivel}`, nome: `${e.nome}${e.versoes.length > 1 ? " nv " + v.nivel : ""}`, sub: `${v.mana} · ${v.acao}${x.equipado ? "" : " · não equipado"}` }));
  });
  R.PERICIAS.forEach((p) => { const [b, d] = bonusPericia(p[0]); ops.push({ t: "per", k: p[0], nome: p[0], sub: `+${b} · ${d}d20${C.treinadas.has(p[0]) ? " · treinada" : ""}` }); });
  return ops;
}
function favoritosValidos() {
  const ops = new Map(opcoesFav().map((o) => [chaveFav(o), o]));
  return (S.favoritos || []).map((f) => ops.get(chaveFav(f))).filter(Boolean);
}
function usarFav(f) {
  if (f.t === "arma") return A["rolar-arma"]({ dataset: { i: f.k } });
  if (f.t === "enc") { const [fam, nv] = f.k.split("|"); return A["conjurar"]({ dataset: { f: fam, v: nv } }); }
  if (f.t === "per") { const [b, d] = bonusPericia(f.k); contarPericia(f.k); return A["rolar-per"]({ dataset: { n: f.k, b: String(b), d: String(d), rolar: "1" } }); }
}
A["fav-usar"] = (el) => { const f = favoritosValidos().find((x) => chaveFav(x) === el.dataset.c); if (f) { lembrarUltima(f); usarFav(f); } };
A["fav-editar"] = () => {
  const sel = new Set((S.favoritos || []).map(chaveFav)), ops = opcoesFav();
  const grupo = (t, tit) => { const l = ops.filter((o) => o.t === t); return l.length ? `<p class="meta" style="margin:10px 0 4px">${tit}</p><div class="lista">${l.map((o) => `<label class="item"><input type="checkbox" class="fav-ck" value="${esc(chaveFav(o))}" ${sel.has(chaveFav(o)) ? "checked" : ""} style="width:22px;height:22px;margin-right:10px"><div class="tx"><b>${esc(o.nome)}</b><small>${esc(o.sub)}</small></div></label>`).join("")}</div>` : ""; };
  folha("★ Favoritos do turno", `<p class="sub">Marque o que você usa na sua vez. Aparecem em cartões grandes na aba Turno.</p>${grupo("arma", "Armas")}${grupo("enc", "Encantamentos")}${grupo("per", "Perícias")}`,
    `<button class="botao prim" data-a="fav-ok">Salvar</button>`);
};
A["fav-ok"] = () => {
  const marc = [...document.querySelectorAll(".fav-ck")].filter((c) => c.checked).map((c) => { const i = c.value.indexOf(":"); return { t: c.value.slice(0, i), k: c.value.slice(i + 1) }; });
  fecharFolha(); mudar((s) => { s.favoritos = marc.slice(0, 24); });
};

// --- perícias mais usadas e a última rolagem (memória do aparelho, por ficha)
const CH_USO = "prevalecentes.layout.uso";
function usoPericias() { try { return JSON.parse(localStorage.getItem(CH_USO) || "{}")[banco.atual] || {}; } catch (e) { return {}; } }
function contarPericia(nome) {
  try { const t = JSON.parse(localStorage.getItem(CH_USO) || "{}"), m = t[banco.atual] = t[banco.atual] || {}; m[nome] = (m[nome] || 0) + 1; localStorage.setItem(CH_USO, JSON.stringify(t)); } catch (e) { /* sem storage */ }
}
let ultimaFav = null;
function lembrarUltima(f) { ultimaFav = f; }

// --- aba Turno
function pTurno() {
  const [lim] = R.acoesDoTurno(C.d.acoes_extras, S.acoes_extras_tipos);
  const minha = sessao.ativa && sessao.vez && sessao.vez === sessao.id;
  const cab = sessao.ativa ? (minha ? `<div class="turno-aviso sua">⚔ Sua vez · rodada ${sessao.rodada}</div>` : `<div class="turno-aviso">${sessao.vez ? `Vez de <b>${esc(sessao.vez)}</b>` : "Fora de combate"} · rodada ${sessao.rodada}</div>`) : "";
  const fichas = R.TIPOS_ACAO.map((t) => {
    const u = int(S.turno[t]), n = Math.max(lim[t], u);
    return [...Array(n)].map((_, i) => `<button class="ficha-acao t-${t === "Bônus" ? "bonus" : t === "Reação" ? "reacao" : t === "Movimento" ? "mov" : "comum"} ${i < u ? "gasta" : ""}" data-a="turno-marca" data-t="${t}" aria-label="${t} ${i < u ? "gasta" : "livre"}">${t[0]}</button>`).join("");
  }).join("");
  const favs = favoritosValidos();
  let h = cab + secao("Ações do turno") + `<div class="fichas-acao">${fichas}</div>
    <p class="sub ajuda">C comum · B bônus · M movimento · R reação. Toque para gastar ou devolver; ataques e magias gastam sozinhos.</p>`;
  h += secao("Favoritos", `<button class="botao leve mini" data-a="fav-editar">★ Escolher</button>`);
  h += favs.length ? `<div class="favs">${favs.map((f) => `<button class="fav t-${f.t}" data-a="fav-usar" data-c="${esc(chaveFav(f))}"><b>${esc(f.nome)}</b><small>${esc(f.sub)}</small></button>`).join("")}</div>`
    : `<p class="vazio">Toque em ★ Escolher e marque seus ataques, magias e perícias da luta.</p>`;
  const us = typeof usosLista === "function" ? usosLista() : [];
  if (us.length) h += secao("Usos") + `<div class="favs">${us.map((u) => { const usado = int(S.usos[u.chave]); return `<button class="fav t-uso ${usado >= u.qtd ? "esgotado" : ""}" data-a="uso" data-c="${esc(u.chave)}"><b>${esc(u.nome)}</b><small>${u.qtd - usado}/${u.qtd} restantes</small></button>`; }).join("")}</div>`;
  h += secao("Fim do turno") + `<div class="linhabts">${sessao.ativa && sessao.id ? `<button class="botao prim grande" data-a="turno-terminei">✓ Terminei meu turno</button>` : `<button class="botao prim grande" data-a="novo-turno">↻ Novo turno</button>`}</div>
    <div class="linhabts" style="margin-top:8px">${sessao.ativa && sessao.id ? `<button class="botao leve" data-a="novo-turno">↻ Renovar ações</button>` : ""}<button class="botao leve" data-a="novo-combate">⚔ Novo combate</button><button class="botao leve" data-a="acoes-livro">📖 Ações do livro</button></div>`;
  return h;
}
A["turno-terminei"] = async () => {
  try { const r = await ga({ acao: "sinal", sinal: "Terminei meu turno" }); toast(r && r.ok === false ? esc(r.erro || "O mestre desligou os sinais.") : "Avisado: o mestre vê no Grupo que você terminou."); }
  catch (e) { toast("Sem sinal com o mestre."); }
};

// --- faixa de vitais: fica no alto enquanto você rola qualquer aba
function pintarFaixaVitais() {
  const f = $("#faixa-vitais"); if (!f) return;
  if (!layoutOn()) { f.hidden = true; return; }
  const v = S.vida, d = C.d;
  const barra = (rot, cor, ch, mx) => { const at = v[ch] === "" || v[ch] == null ? mx : int(v[ch], mx), p = Math.max(0, Math.min(100, (at / Math.max(1, mx)) * 100));
    return `<button class="fv" data-a="editar-vital" data-chave="${ch}" data-max="${mx}" aria-label="${rot} ${at} de ${mx}"><span>${rot} <b>${at}</b>/${mx}</span><i><em style="width:${p}%;background:${cor}"></em></i></button>`; };
  const conds = R.CONDICOES.filter((n) => int((S.condicoes[n] || {}).atual)).map((n) => `<button class="fv-cond" data-a="editar-cond" data-n="${n}">${n} ${int(S.condicoes[n].atual)}</button>`).join("");
  f.innerHTML = `<div class="fv-linha">${barra("Vida", "var(--c-vida)", "atual", d.vida)}${barra("Mana", "var(--c-mana)", "mana_atual", d.mana)}${barra("Vigor", "var(--c-vigor)", "vigor_atual", d.vigor)}</div>${conds ? `<div class="fv-conds">${conds}</div>` : ""}`;
  f.hidden = false;
}

// --- dado flutuante: toque abre o leque; segurar abre o diário
function pintarDadoFlutuante() {
  const b = $("#dado-flutuante"); if (b) b.hidden = !layoutOn();
}
A["leque"] = () => {
  if (Date.now() - segurouEm < 800) return;    // foi um toque longo: o diário já abriu
  const uso = usoPericias(), top = Object.keys(uso).sort((a, b) => uso[b] - uso[a]).slice(0, 4);
  // as mais roladas nesta ficha; o resto se completa com as treinadas e, por fim, Percepção e Intuição
  const extra = [...C.treinadas].filter((n) => R.PERICIAS.some((p) => p[0] === n)).sort((a, b) => bonusPericia(b)[0] - bonusPericia(a)[0]);
  const pers = [...new Set([...top, ...extra, "Percepção", "Intuição"])].filter((n) => R.PERICIAS.some((p) => p[0] === n)).slice(0, 4);
  folha("🎲 Rolar", `<div class="favs">
      <button class="fav" data-a="rolar-ini"><b>⏳ Iniciativa</b><small>${C.d.iniciativa_dados}d20 +${C.d.iniciativa_bonus}</small></button>
      ${ultimaFav ? `<button class="fav" data-a="leque-repetir"><b>↻ ${esc(ultimaFav.nome)}</b><small>repetir a última</small></button>` : ""}
      ${pers.map((n) => { const [b, d] = bonusPericia(n); return `<button class="fav t-per" data-a="leque-per" data-n="${esc(n)}"><b>${esc(n)}</b><small>+${b} · ${d}d20</small></button>`; }).join("")}
      <button class="fav" data-a="dados"><b>🎲 Dado livre</b><small>2d6+3, d20…</small></button>
      <button class="fav" data-a="diario"><b>📜 Diário</b><small>últimas rolagens</small></button>
    </div><p class="sub">Primeiro as perícias que você mais rola nesta ficha; depois as treinadas.</p>`);
};
A["leque-per"] = (el) => { fecharFolha(); const f = { t: "per", k: el.dataset.n, nome: el.dataset.n }; lembrarUltima(f); usarFav(f); };
A["leque-repetir"] = () => { fecharFolha(); if (ultimaFav) usarFav(ultimaFav); };
let segurouEm = 0;
(function segurarDado() {
  let t = null;
  const ini = () => { clearTimeout(t); t = setTimeout(() => { t = null; segurouEm = Date.now(); if (S) A["diario"](); }, 600); };
  const fim = (ev) => { if (t) { clearTimeout(t); t = null; } else if (ev.cancelable) ev.preventDefault(); };
  const ligar = () => {
    const b = $("#dado-flutuante"); if (!b) return;
    b.addEventListener("touchstart", ini, { passive: true }); b.addEventListener("touchend", fim);
    b.addEventListener("mousedown", ini); b.addEventListener("mouseup", fim); b.addEventListener("mouseleave", () => { clearTimeout(t); t = null; });
  };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", ligar); else ligar();
})();
