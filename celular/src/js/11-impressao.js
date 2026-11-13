// ------------------------------------------------------------------ imprimir / PDF
function folhaImpressao() {
  const d = C.d, v = S.vida, at = (ch, mx) => (v[ch] === "" || v[ch] == null ? mx : int(v[ch], mx));
  const t = (cab, linhas) => `<table><thead><tr>${cab.map((c) => `<th>${c}</th>`).join("")}</tr></thead><tbody>${linhas.map((l) => `<tr>${l.map((c) => `<td>${c}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
  const sec = (x) => `<h2>${x}</h2>`;
  let h = `<h1>${esc(S.identidade.nome || "Sonhador sem nome")}</h1><p class="linha">Player: ${esc(S.identidade.player || "—")} · Nível ${C.nv} · ${esc(S.identidade.especie || "—")}${S.sem_alma ? " · sem alma" : ""} · Guilda ${esc(S.identidade.guilda || "—")}</p>
    ${S.identidade.sonho ? `<p class="linha">Sonho: ${esc(S.identidade.sonho)}</p>` : ""}`;
  h += sec("Vigor do corpo") + t(["Vida", "Mana", "Vigor", "CA", "Movimento", "Iniciativa", "Ações extras", "RD", "Carga", "Descoberta"],
    [[`${at("atual", d.vida)}/${d.vida}`, `${at("mana_atual", d.mana)}/${d.mana}`, `${at("vigor_atual", d.vigor)}/${d.vigor}`, d.ca, `${C.mov} m`, `+${d.iniciativa_bonus} (${d.iniciativa_dados}d20)`, d.acoes_extras, d.rd ? `${d.rd}d4` : "—", `${C.carga}/${d.carga}`, d.descoberta]]);
  h += sec("Atributos") + t(["Atributo", "Pontos", "Curva", "BC", "Dados"], R.ATRIBUTOS.map((k) => [R.NOMES_ATR[k], C.a[k], d.curva[k], `+${d.bc[k]}`, `${1 + Math.floor(R.cap(C.a[k]) / 20)}d20`]));
  h += sec("Perícias") + t(["Perícia", "T", "Bônus", "Dados"], R.PERICIAS.map(([n, ats, tr]) => { const x = ats || [S.prevalencia_attr || "ARC"]; const [, b, dd] = R.periciaFora(C.a, C.nv, x, C.treinadas.has(n)); return [esc(n) + (tr ? " •" : ""), C.treinadas.has(n) ? "✔" : "", `+${b + (C.ef.pericia[n] || 0)}`, `${dd}d20`]; }));
  h += sec("Ataque e defesa") + t(["Perícia", "Bônus"], R.PERICIAS_ATAQUE.map(([n, ats]) => [n + (S.pericia_ataque === n ? " (treinada)" : ""), ats.map((k) => `+${d.bc[k] + d.n3}`).join(" / ")])
    .concat(R.PERICIAS_DEFESA.map(([n, k, tn]) => [n, `+${bonusDefesa(n, k, tn)}`]))) + `<p class="linha">DT Feitiçaria ${d.dt_feiticaria} · DT Desejo ${d.dt_desejo} · Resistências: ${d.resistencias.join(", ") || "—"}</p>`;
  h += sec("Armas e proteção") + t(["Arma", "Nível", "Dano", "Crítico", "Propriedades"], S.armas.filter((w) => ARMAS[w.grupo]).map((w) => { const e = efeitoArma(w, int(w.nivel, 1)); return [esc(w.grupo), w.nivel, esc(e.dano), e.margem, esc(w.props || "—")]; }))
    + `<p class="linha">Armadura: ${esc(S.equip.armadura || "—")} · Escudo: ${esc(S.equip.escudo || "—")} · Talismãs: ${S.talismas.filter((x) => x.nome).map((x) => esc(x.nome)).join(", ") || "—"}</p>`;
  const pecas = PECAS.filter((p) => S.set[p] && (S.set[p].set || S.set[p].nome)).map((p) => [p, esc(S.set[p].set || "—"), esc(S.set[p].nome || "")]);
  if (pecas.length) h += t(["Peça de set", "Set", "Nome"], pecas);
  h += sec("Inventário") + t(["Item", "Qtd", "Peso"], (S.inventario.length ? S.inventario : [{ item: "—" }]).map((i) => [esc(i.item), i.qtd || "1", i.carga || ""])) + `<p class="linha">Dinheiro: ${esc(R.formatarDinheiro(S.dinheiro_c))}</p>`;
  if (S.encantamentos.length) h += sec("Encantamentos") + t(["Encantamento", "Versões", "Mana", "Espaço", "Equipado"], S.encantamentos.filter((x) => ENC[x.familia]).map((x) => { const e = ENC[x.familia], top = e.versoes.filter((y) => x.versoes.includes(y.nivel)).pop() || e.versoes[0]; return [esc(e.nome), x.versoes.join(", "), esc(top.mana), custoEnc(e)[1], x.equipado ? "✔" : ""]; }));
  const tal = SLOTS.concat(META_SLOTS).filter((sl) => S.talentos[sl] && slotValido(sl));
  if (tal.length) h += sec("Talentos") + t(["Slot", "Talento", "Escolha"], tal.map((sl) => [sl, esc(S.talentos[sl]), esc(S.talentos_escolha[sl] || "")]));
  if (!S.sem_alma) h += sec("Alma") + `<p class="linha">${esc(S.alma.nome || "—")} · nível ${d.alma_nivel} · DT ${almaDT()} · ${d.alma_usos} usos por descanso longo</p>`
    + (S.alma.habilidades.length ? t(["Habilidade", "Tipo", "Valor", "Efeito"], S.alma.habilidades.map((x) => { const inf = infoHab(x); return [esc(x.nome), x.tipo, x.tabela ? `${esc(x.tabela)}: ${esc(inf.valor)}` : "", esc(x.efeito)]; })) : "");
  h += sec("Condições e Portão") + t(R.CONDICOES, [R.CONDICOES.map((n) => `${int(S.condicoes[n].atual)}/${condMax(n)}`)]) + `<p class="linha">Portão: ${S.portao.Sucessos.filter(Boolean).length} sucesso(s), ${S.portao.Falhas.filter(Boolean).length} falha(s) · Cicatrizes: ${esc(S.cicatrizes || "—")}</p>`;
  h += sec("Vínculos e Meta de Vida") + `<p class="linha">Grupo: ${esc(S.vinculos.grupo || "—")} · Mundo: ${esc(S.vinculos.mundo || "—")}</p><p class="linha">Meta: ${esc(S.meta.caminho || "—")}${S.meta.caminho ? ` · etapas ${S.meta.etapas.filter(Boolean).length}/3` : ""} · concluídas ${int(S.meta.concluidas)}</p>`;
  return `<div class="impr">${h}<p class="rodape-impr">Ficha Prevalecentes 3.1 · ${new Date().toLocaleDateString("pt-BR")}</p></div>`;
}
A["imprimir"] = () => {
  fecharFolha();
  let div = $("#impressao");
  if (!div) { div = document.createElement("div"); div.id = "impressao"; document.body.appendChild(div); }
  div.innerHTML = folhaImpressao();
  document.documentElement.classList.add("imprimindo");
  setTimeout(() => window.print(), 60);
};
window.addEventListener("afterprint", () => document.documentElement.classList.remove("imprimindo"));

