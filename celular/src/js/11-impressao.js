// ------------------------------------------------------------------ imprimir / PDF
// resumo das ações de uma arma, já com o dano calculado (igual ao PDF do PC).
// Ex.: Chuva de Flechas · Completa · até 5 × 4d10 (crítico 12d10) · 5 flechas
const TIRA_ACAO = [/^como (?:uma )?(?:a[çc][ãa]o (?:comum|b[ôo]nus|completa|de movimento|livre)|rea[çc][ãa]o)\s*,?\s*/i,
  /^voc[êe] gasta uma a[çc][ãa]o (?:comum|b[ôo]nus|completa|de movimento)\s*(?:para|e)?\s*(?:que\s*)?/i, /^para\s+/i,
  /^voc[êe] pode gastar uma a[çc][ãa]o (?:comum|b[ôo]nus|completa|de movimento)\s*(?:,|para|e)?\s*/i, /^voc[êe] pode gastar\s*/i, /^voc[êe] pode\s*/i, /^gaste\s*/i];
function resumoTexto(texto, limite = 150) {
  let t = String(texto || "").replace(/\s+/g, " ").trim();
  for (const rx of TIRA_ACAO) t = t.replace(rx, "");
  let out = "";
  for (const f of t.split(/(?<=[.!?])\s/)) { out = (out + " " + f).trim(); if (out.length >= 60) break; }
  out = out.replace(/\.$/, "");
  out = out.charAt(0).toUpperCase() + out.slice(1);
  if (out.length > limite) out = out.slice(0, limite).replace(/\s+\S*$/, "").replace(/[,;:]$/, "") + "…";
  return out;
}
function resumoAcoes(i) {
  const w = S.armas[i], ar = ARMAS[w.grupo]; if (!ar || !ar.acoes) return [];
  const base = danoArma(i, 0), nomeP = (p) => p.split("(")[0].trim();
  const multDe = (x) => (x.props.some((p) => nomeP(p) === "Destruidora") ? 3 : 2);
  const linhas = [];
  for (const x of ar.acoes) {
    if (x.sub || ["•", "Nota"].includes(x.nome.trim())) continue;
    const r = R.acaoArma(x.nome, x.texto); if (r.nota) continue;
    const tl = String(x.texto || "").toLowerCase(), nome = x.nome.replace(/^passiva:\s*/i, "");
    let delta = r.delta || 0;
    const m = tl.match(/aumentar o dano em (\d+|um|uma|dois) n[íi]ve/);
    if (m && !delta) delta = { um: 1, uma: 1, dois: 2 }[m[1]] || int(m[1]);
    if (r.passiva) { linhas.push([nome, "Passiva", esc(resumoTexto(x.texto))]); continue; }
    if (tl.includes("metade do dano") && tl.includes("vira pontos")) {   // Preparar Flecha
      const conds = ["Veneno", "Sangramento", "Congelamento", "Sono", "Loucura", "Podridão"].filter((c) => tl.includes(c.toLowerCase())).join(", ");
      linhas.push([nome, r.acao || "—", `próxima flecha: role <b>${esc(base.ep.dano)}</b> (crítico ${esc(exprCritico(base.ep.dano, multDe(base)))}); metade vira dano e o valor inteiro vira pontos de ${conds || "condição"}`]);
      continue;
    }
    const gatilho = /^(ao |quando |sempre que |caso )/.test(tl) && !r.acao;
    if (!r.ataque || gatilho) { linhas.push([nome, gatilho ? "Gatilho" : (r.acao || "—"), esc(resumoTexto(x.texto))]); continue; }
    const dx = danoArma(i, delta) || base, ep = dx.ep, mult = r.mult || multDe(dx);
    const dano = ep.dano + (dx.furiaDano ? ` + ${dx.furiaDano}` : ""), crit = exprCritico(ep.dano, mult);
    const n = r.golpes || 1, golpes = n > 1 ? (r.ate ? `até ${n} × ` : `${n} × `) : "";
    const partes = [r.critico ? `crítico automático: <b>${golpes}${esc(crit)}</b>` : `<b>${golpes}${esc(dano)}</b> (crítico ${esc(crit)})`];
    for (const [xx, tp, cnd] of ep.extras) if (!cnd) partes.push(`+ ${esc(xx)} ${esc(tp)}`);
    if (dx.nvD !== dx.nv) partes.push(`dano de nível ${dx.nvD}`);
    if (r.vantagem === 1) partes.push("com vantagem"); else if (r.vantagem === -1) partes.push("com desvantagem");
    if (r.teste) partes.push(`alvo testa ${esc(r.teste)}`);
    const q = r.municao || 0;
    if (q) { const tp = r.municao_tipo || "munição", pl = tp.endsWith("ão") ? tp.slice(0, -2) + "ões" : tp + "s"; partes.push(q < 0 ? `todas as ${pl}` : `${q} ${q === 1 ? tp : pl}`); }
    let tipo = r.acao || "Comum";
    if (r.acao === "Bônus" && /pr[óo]ximo ataque/.test(tl)) partes[0] = "próximo ataque: " + partes[0];
    const extra = x.nome !== "Atacar" && n === 1 && !partes[0].startsWith("próximo") ? resumoTexto(x.texto, 90) : "";
    linhas.push([nome, tipo, partes.join(" · ") + (extra ? ` — <span class="sub">${esc(extra)}</span>` : "")]);
  }
  return linhas;
}
function folhaImpressao() {
  const d = C.d, v = S.vida, at = (ch, mx) => (v[ch] === "" || v[ch] == null ? mx : int(v[ch], mx));
  const t = (cab, linhas) => `<table><thead><tr>${cab.map((c) => `<th>${c}</th>`).join("")}</tr></thead><tbody>${linhas.map((l) => `<tr>${l.map((c) => `<td>${c}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
  const sec = (x) => `<h2><span class="flam">${x}</span></h2>`;
  let h = `<div class="cab${S.foto ? " com-foto" : ""}">${S.foto ? `<img class="foto-impr" src="${S.foto}" alt="">` : ""}<h1>${esc(S.identidade.nome || "Sonhador sem nome")}</h1><p class="linha">Player: ${esc(S.identidade.player || "—")} · Nível ${C.nv} · ${esc(S.identidade.especie || "—")}${S.sem_alma ? " · sem alma" : ""} · Guilda ${esc(S.identidade.guilda || "—")}</p>
    ${S.identidade.sonho ? `<p class="linha">Sonho: ${esc(S.identidade.sonho)}</p>` : ""}</div>`;
  // características de espécie: ajustes de atributo e o par descritivo (vantagem e desvantagem)
  const ajustes = R.ATRIBUTOS.map((k) => [k, int(S.atributos[k].especie)]).filter(([, n]) => n).map(([k, n]) => `${n > 0 ? "+" : "−"}${Math.abs(n)} ${R.NOMES_ATR[k]}`);
  const notasEsp = String(S.especie_notas || "").trim();
  if (S.identidade.especie || ajustes.length || notasEsp) h += sec("Características de espécie")
    + `<p class="linha"><b>${esc(S.identidade.especie || "Espécie")}</b>${ajustes.length ? ` — atributos: ${ajustes.join(", ")}` : ""}</p>`
    + `<p class="linha">${notasEsp ? esc(notasEsp).replace(/\n/g, "<br>") : "<i>Sem par descritivo anotado (vantagem e desvantagem da espécie).</i>"}</p>`;
  // os números do corpo em janelas de arco ogival: o vidro colorido leva o rótulo
  const jan = (rot, val, sub, cor) => `<div class="jan" style="--vidro:${cor}"><b>${rot}</b><span>${val}</span><small>${sub}</small></div>`;
  h += sec("Vigor do corpo") + `<div class="janelas">${[
    jan("Vida", d.vida, `atual ${at("atual", d.vida)}`, "#a3334f"), jan("Mana", d.mana, `atual ${at("mana_atual", d.mana)}`, "#5b4fae"),
    jan("Vigor", d.vigor, `atual ${at("vigor_atual", d.vigor)}`, "#4e8a4a"), jan("Movimento", `${C.mov} m`, `${Math.floor(C.mov / 1.5)} quadrados`, "#3f8a7a"),
    jan("CA", d.ca, "classe de armadura", "#6f6678")].join("")}</div><div class="janelas">${[
    jan("Carga", C.carga, `máx. ${d.carga}`, "#4a2c6b"), jan("Iniciativa", `+${d.iniciativa_bonus}`, `${d.iniciativa_dados}d20 (maior)`, "#4a2c6b"),
    jan("Ações extras", d.acoes_extras, "por Destreza", "#4a2c6b"), jan("Red. de dano", d.rd ? `${d.rd}d4` : "—", "por Tenacidade", "#4a2c6b"),
    jan("Descoberta", d.descoberta, "por Arcano", "#4a2c6b")].join("")}</div>`;
  h += sec("Atributos") + t(["Atributo", "Pontos", "Curva", "BC", "Dados"], R.ATRIBUTOS.map((k) => [R.NOMES_ATR[k], C.a[k], d.curva[k], `+${d.bc[k]}`, `${1 + Math.floor(R.cap(C.a[k]) / 20)}d20`]));
  const per = R.PERICIAS.map(([n, ats, tr]) => { const x = ats || [S.prevalencia_attr || "ARC"]; const [, b, dd] = R.periciaFora(C.a, C.nv, x, C.treinadas.has(n)); return [esc(n) + (tr ? " •" : ""), C.treinadas.has(n) ? "✔" : "", `+${b + (C.ef.pericia[n] || 0)}`, `${dd}d20`]; });
  const meio = Math.ceil(per.length / 2);   // duas colunas lado a lado, em ordem alfabética de cima para baixo
  h += sec("Perícias") + t(["Perícia", "T", "Bônus", "Dados", "Perícia", "T", "Bônus", "Dados"], per.slice(0, meio).map((l, i) => l.concat(per[i + meio] || ["", "", "", ""])));
  h += sec("Ataque e defesa") + t(["Perícia", "Bônus"], R.PERICIAS_ATAQUE.map(([n, ats]) => [n + (S.pericia_ataque === n ? " (treinada)" : ""), ats.map((k) => `+${bonusPericiaAtaque(n, k)}`).join(" / ")])
    .concat(R.PERICIAS_DEFESA.map(([n, k, tn]) => [n, `+${bonusDefesa(n, k, tn)}`]))) + `<p class="linha">DT Feitiçaria ${d.dt_feiticaria} · DT Desejo ${d.dt_desejo} · Resistências: ${d.resistencias.join(", ") || "—"}</p>`;
  h += sec("Armas e proteção") + t(["Arma", "Nível", "Acerto", "Dano", "Crítico", "Propriedades"], S.armas.map((w, i) => [w, i]).filter(([w]) => ARMAS[w.grupo]).map(([w, i]) => {
      const x = danoArma(i, 0), per = periciaDaArma(w.grupo, x.k);
      const atk = ataquePericia(per, x.k, { arma: true, ef: C.escolha.maestria.includes(w.grupo) ? 1 : 0, fora: (R.ACERTO_ARMA[x.nv] || 0) + x.ep.acerto });
      return [esc(w.grupo), w.nivel, `${per} 1d20 +${atk.b}${atk.vant ? " (vant.)" : ""}`, esc(x.ep.dano) + (x.nvD !== x.nv ? ` (nível ${x.nvD})` : ""), `${x.ep.margem}${x.props.some((p) => p.startsWith("Destruidora")) ? " ×3" : ""}`, esc(w.props || "—")];
    }))
    + S.armas.map((w, i) => [w, i]).filter(([w]) => ARMAS[w.grupo]).map(([w, i]) => { const l = resumoAcoes(i); return l.length ? `<table class="acoes"><thead><tr><th>Ações — ${esc(w.grupo)} nv ${w.nivel}</th><th>Ação</th><th>Efeito (já calculado)</th></tr></thead><tbody>${l.map((r) => `<tr><td>${esc(r[0])}</td><td>${esc(r[1])}</td><td>${r[2]}</td></tr>`).join("")}</tbody></table>` : ""; }).join("")
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
  // a tabela de fora só serve de moldura: a faixa de vitral (thead) e o pé com as janelas (tfoot) saem em todas as páginas
  return `<div class="impr"><div class="moldura" aria-hidden="true"><i class="col e"></i><i class="col d"></i><i class="canto a"></i><i class="canto b"></i><i class="canto c"></i><i class="canto d"></i></div><table class="pg"><thead><tr><td><div class="vitral-faixa"></div></td></tr></thead><tbody><tr><td>${h}</td></tr></tbody><tfoot><tr><td><div class="vitral-pe"><i></i><span class="rodape-impr"><b class="folio">✠</b><br>${esc(S.identidade.nome || "Sonhador")} · Ficha Prevalecentes 3.4 · ${new Date().toLocaleDateString("pt-BR")}</span><i></i></div></td></tr></tfoot></table></div>`;
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

