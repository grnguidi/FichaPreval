// ------------------------------------------------------------------ mesa: turno, usos, defesas e ações
function limitesTurno() { return R.acoesDoTurno(C.d.acoes_extras, S.acoes_extras_tipos)[0]; }
/* Marca a ação gasta no turno. Completa = Comum + Bônus + Movimento. Devolve um aviso se passou do que havia. */
function marcarAcao(tipo) {
  if (!S || !tipo || !["Comum", "Bônus", "Movimento", "Reação", "Completa"].includes(tipo)) return "";
  const tipos = tipo === "Completa" ? ["Comum", "Bônus", "Movimento"] : [tipo], lim = limitesTurno(), sem = [];
  for (const t of tipos) { S.turno[t] = int(S.turno[t]) + 1; if (S.turno[t] > lim[t]) sem.push(t); }
  salvar();
  return sem.length ? `Não sobrava ação ${sem.join(" e ")} neste turno.` : "";
}
function usosLista() {
  const out = [];
  for (const nome of [...C.tal].sort()) {
    const t = TAL[nome], u = t && R.usosLimitados(t.descricao);
    if (u) out.push({ chave: "tal:" + nome, nome, origem: "Talento", qtd: u[0], periodo: u[1], desc: t.descricao });
  }
  S.talismas.slice(0, C.d.talismas).forEach((t) => {
    const info = TALISMA[t.nome], u = info && R.usosLimitados(info.efeito);
    if (u) out.push({ chave: "tali:" + t.nome, nome: t.nome, origem: "Talismã", qtd: u[0], periodo: u[1], desc: info.efeito });
  });
  return out;
}
function recarregarUsos(evento) {
  for (const u of usosLista()) if (R.recarrega(u.periodo, evento)) delete S.usos[u.chave];
  if (evento === "longo") S.alma.restantes = "";
}
function novoTurno(silencioso) {
  S.turno = {}; recarregarUsos("turno"); salvar();
  if (!silencioso) { render(); toast("Novo turno: ações e usos por turno renovados."); }
}
function novoCombate(silencioso) {
  S.turno = {}; S.contra_usados = 0; recarregarUsos("combate"); salvar();
  if (!silencioso) { render(); toast("Novo combate: ações, contra-encantamentos e usos por combate renovados."); }
}
A["novo-turno"] = () => novoTurno();
A["novo-combate"] = () => novoCombate();
A["turno-marca"] = (el) => {
  const t = el.dataset.t, lim = limitesTurno()[t];
  mudar((s) => { s.turno[t] = int(s.turno[t]) >= lim ? 0 : int(s.turno[t]) + 1; });
};
const pontos = (usados, total) => [...Array(Math.max(total, usados))].map((_, i) => `<i class="${i < usados ? "gasto" : ""}${i >= total ? " extra" : ""}"></i>`).join("");
function cardTurno() {
  const [lim, faltam] = R.acoesDoTurno(C.d.acoes_extras, S.acoes_extras_tipos);
  return secao("Turno") + `<div class="cartao turno">
    <div class="tipos">${R.TIPOS_ACAO.map((t) => { const u = int(S.turno[t]); return `<button class="tipo ${u >= lim[t] ? "cheio" : ""}" data-a="turno-marca" data-t="${t}"><b>${t}</b><span class="pts">${pontos(u, lim[t])}</span></button>`; }).join("")}</div>
    <div class="linhabts" style="margin-top:8px"><button class="botao leve" data-a="novo-turno">↻ Novo turno</button><button class="botao leve" data-a="novo-combate">⚔ Novo combate</button><button class="botao" data-a="acoes-livro">📖 Ações</button></div>
    <p class="sub" style="margin:6px 0 0">Toque no tipo para marcar a ação gasta. Ataques, encantamentos e itens marcam sozinhos.${faltam ? ` <b class="erro">Escolha o tipo de ${faltam} ação(ões) extra(s) na Ficha.</b>` : ""}${sessao.ativa ? " Na mesa, o turno renova quando o mestre passa a vez para você." : ""}</p></div>`;
}
function cardUsos() {
  const us = usosLista(), alma = !S.sem_alma && S.alma.habilidades.some((h) => h.tipo === "Ativo");
  if (!us.length && !alma) return "";
  const rot = { "turno": "por turno", "rodada": "por rodada", "combate": "por combate", "cena": "por cena", "descanso curto": "por descanso curto", "descanso longo": "por descanso longo", "dia": "por dia" };
  let h = secao("Usos") + `<div class="lista">`;
  if (alma) {
    const tot = C.d.alma_usos, rest = S.alma.restantes === "" || S.alma.restantes == null ? tot : int(S.alma.restantes, tot);
    h += `<div class="item"><div class="tx"><b>Alma${S.alma.nome ? " · " + esc(S.alma.nome) : ""}</b><small>habilidades ativas · ${tot} por descanso longo</small></div>
      <span class="pts grande">${pontos(tot - rest, tot)}</span><button class="botao prim mini" data-a="alma-usar">Usar</button><button class="botao leve mini" data-a="alma-recup">↺</button></div>`;
  }
  for (const u of us) {
    const usado = int(S.usos[u.chave]);
    h += `<div class="item" data-a="uso-ver" data-c="${esc(u.chave)}"><div class="tx"><b>${esc(u.nome)}</b><small>${u.origem} · ${u.qtd}x ${rot[u.periodo] || u.periodo}</small></div>
      <span class="pts grande">${pontos(usado, u.qtd)}</span><button class="botao prim mini" data-a="uso" data-c="${esc(u.chave)}" ${usado >= u.qtd ? "disabled" : ""}>Usar</button><button class="botao leve mini" data-a="uso-recup" data-c="${esc(u.chave)}">↺</button></div>`;
  }
  return h + `</div><p class="sub">Recarregam sozinhos: por turno no Novo turno, por combate no Novo combate, e nos descansos.</p>`;
}
A["uso"] = (el, ev) => {
  if (ev) ev.stopPropagation();
  const u = usosLista().find((x) => x.chave === el.dataset.c); if (!u) return;
  mudar((s) => { s.usos[u.chave] = Math.min(u.qtd, int(s.usos[u.chave]) + 1); });
  registrarDiario({ titulo: `✦ ${u.nome}`, linhas: [`Usou (${int(S.usos[u.chave])}/${u.qtd}).`, esc(u.desc)] });
  toast(`<b>${esc(u.nome)}</b>: ${int(S.usos[u.chave])}/${u.qtd} usado(s).`);
};
A["uso-recup"] = (el, ev) => { if (ev) ev.stopPropagation(); mudar((s) => { delete s.usos[el.dataset.c]; }); };
A["uso-ver"] = (el) => { const u = usosLista().find((x) => x.chave === el.dataset.c); if (u) folha(esc(u.nome), `<p class="meta">${u.origem} · ${u.qtd}x por ${u.periodo}</p><div class="desc">${esc(u.desc)}</div>`); };
A["alma-usar"] = (el, ev) => {
  if (ev) ev.stopPropagation();
  const tot = C.d.alma_usos, rest = S.alma.restantes === "" || S.alma.restantes == null ? tot : int(S.alma.restantes, tot);
  if (rest <= 0) { toast("A Alma não tem usos restantes. Recarrega no descanso longo."); return; }
  mudar((s) => { s.alma.restantes = String(rest - 1); });
  toast(`Alma: ${rest - 1}/${tot} usos restantes.`);
};
A["alma-recup"] = (el, ev) => { if (ev) ev.stopPropagation(); mudar((s) => { s.alma.restantes = ""; }); };

function bonusDefesa(n, k, tn) { return C.d.bc[k] + C.d.n3 + (C.tal.has(tn) ? 2 : 0); }
A["rolar-def"] = (el) => {
  const [n, k, tn] = R.PERICIAS_DEFESA.find((x) => x[0] === el.dataset.n), b = bonusDefesa(n, k, tn);
  const r = R.rolarDefesa(b, R.vantagem(C.a[k]), rng);
  mostrarRolagem(`🛡 ${n}`, [`${n}: <b style="font-size:20px">${r.total}</b> <span class="sub">[d20 ${r.d20.join(", ")}${r.d20.length > 1 ? " → maior" : ""} +${b}]</span>`,
    `<span class="sub">Compare com a DT do efeito ou da habilidade do inimigo.</span>`]);
};
A["rolar-atk"] = (el) => {
  const [n, atrs] = R.PERICIAS_ATAQUE.find((x) => x[0] === el.dataset.n);
  const k = atrs.reduce((m, x) => (C.d.bc[x] > C.d.bc[m] ? x : m), atrs[0]);
  const b = C.d.bc[k] + C.d.n3 + (n === "Luta" || n === "Pontaria" ? C.ef.acerto : 0);
  const at = R.rolarAtaque(b, R.vantagem(C.a[k]), 20, rng);
  mostrarRolagem(`🎲 ${n}`, [txtAtaque(at, n), `<span class="sub">Teste de ${n} (${k}) sem arma; os ataques com arma ficam no cartão da arma.</span>`]);
};
A["contra"] = () => {
  const max = C.d.contra_encant;
  folha("Contradomínio", `<p>Anule um encantamento inimigo: 1d20 + BC + nível ÷ 3 contra a DT dele (10 + BC dele + nível dele ÷ 3).</p>
    <p class="meta">Contra-encantamentos neste combate: <b>${S.contra_usados}/${max}</b> (1 a cada 10 de INT ou Fé)</p>`,
  `<button class="botao" data-a="contra-rolar" data-k="INT">Anular Magia (INT)</button><button class="botao prim" data-a="contra-rolar" data-k="FE">Anular Feitiço (Fé)</button>`);
};
A["contra-rolar"] = (el) => {
  const k = el.dataset.k, b = C.d.bc[k] + C.d.n3 + (C.tal.has("Contra-encantador") ? 2 : 0), max = C.d.contra_encant;
  const r = R.rolarDefesa(b, R.vantagem(C.a[k]), rng);
  S.contra_usados = int(S.contra_usados) + 1; salvar(); render();
  mostrarRolagem("✧ Contradomínio", [`${k === "INT" ? "Feitiçaria" : "Desejo"}: <b style="font-size:20px">${r.total}</b> <span class="sub">[d20 ${r.d20.join(", ")}${r.d20.length > 1 ? " → maior" : ""} +${b}]</span>`,
    `Anula se for maior ou igual à DT do encantamento inimigo.`, S.contra_usados > max ? `<span class="erro">Passou do limite: ${S.contra_usados}/${max} neste combate.</span>` : `<span class="sub">Contra-encantamentos: ${S.contra_usados}/${max} neste combate.</span>`]
    .concat(C.tal.has("Contra-encantador") ? [`<span class="sub">Inclui +2 de Contra-encantador.</span>`] : []));
};
A["coord"] = (el) => {
  const k = el.dataset.k || "DES", b = C.d.bc[k] + C.d.n3 + (C.tal.has("Mãos Gêmeas") ? 2 : 0);
  const dt = 8 + Math.max(int(S.armas[0].nivel, 1), int(S.armas[1].nivel, 1));
  const r = R.rolarDefesa(b, R.vantagem(C.a[k]), rng), ok = r.total >= dt;
  mostrarRolagem("⚔ Coordenação", [`Coordenação (${k}): <b style="font-size:20px">${r.total}</b> <span class="sub">[d20 ${r.d20.join(", ")}${r.d20.length > 1 ? " → maior" : ""} +${b}]</span> contra DT ${dt}`,
    ok ? `<b class="ok">Sucesso</b>: luta normalmente neste turno.` : k === "ARC" ? `<b class="erro">Falha</b>: os encantamentos deste turno perdem o último dado de dano (mínimo 1).` : `<b class="erro">Descoordenado</b>: o dano das armas neste turno cai 1 nível (no nível 1, metade).`]);
};
A["acoes-livro"] = () => {
  const grupos = R.TIPOS_ACAO.map((t) => [t, R.ACOES_LIVRO.filter((a) => a[1] === t)]);
  folha("Ações do livro", grupos.map(([t, lista]) => `<div class="secao">${t}</div><div class="lista">${lista.map(([n, , teste, d]) =>
    `<div class="item" data-a="acao-livro" data-n="${esc(n)}"><div class="tx"><b>${esc(n)}</b><small>${esc(d)}${teste === "provocar" ? ` DT ${R.dtProvocar(C.d, C.nv)}.` : ""}</small></div><span class="sub">${teste ? "🎲" : "✓"}</span></div>`).join("")}</div>`).join(""));
};
A["acao-livro"] = (el) => {
  const [n, tipo, teste, d] = R.ACOES_LIVRO.find((a) => a[0] === el.dataset.n);
  fecharFolha();
  if (teste === "ataque") {
    const armas = S.armas.map((w, i) => [w, i]).filter(([w]) => ARMAS[w.grupo]);
    if (!armas.length) { const aviso = marcarAcao(tipo); render(); toast(`${n}: sem arma equipada. ${aviso}`); return; }
    if (armas.length === 1) { atacar(armas[0][1], { acao: tipo, rotulo: n }); return; }
    folha(n, `<p>Com qual arma?</p><div class="linhabts">${armas.map(([w, i]) => `<button class="botao prim" data-a="acao-livro-arma" data-i="${i}" data-n="${esc(n)}" data-t="${tipo}">⚔ ${esc(w.grupo)}</button>`).join("")}</div>`);
    return;
  }
  const aviso = marcarAcao(tipo), linhas = [esc(d)];
  if (teste === "provocar") linhas.push(`O alvo faz Vontade contra DT <b>${R.dtProvocar(C.d, C.nv)}</b> (10 + BC de Mente + nível ÷ 3).`);
  else if (teste) {
    const pr = R.PERICIAS.find((x) => x[0] === teste), at = pr[1] || [S.prevalencia_attr || "ARC"];
    const [, b0, dados] = R.periciaFora(C.a, C.nv, at, C.treinadas.has(teste)), b = b0 + (C.ef.pericia[teste] || 0);
    const r = R.rolarPericia(b, dados, rng);
    linhas.push(`${teste}: <b style="font-size:20px">${r.total}</b> <span class="sub">[d20 ${r.d20.join(", ")}${r.d20.length > 1 ? " → maior" : ""} +${b}]</span>`);
  }
  if (aviso) linhas.push(`<span class="erro">${aviso}</span>`);
  render();
  mostrarRolagem(`${tipo === "Reação" ? "↯" : "▸"} ${n} (${tipo})`, linhas);
};
A["acao-livro-arma"] = (el) => { fecharFolha(); atacar(int(el.dataset.i), { acao: el.dataset.t, rotulo: el.dataset.n }); };
A["acao-arma"] = (el, ev) => {
  if (ev) ev.stopPropagation();
  const i = int(el.dataset.i), j = int(el.dataset.j), w = S.armas[i], ar = ARMAS[w.grupo], x = ar.acoes[j], p = R.acaoArma(x.nome, x.texto);
  const op = (v, t, sel) => `<option value="${v}" ${sel ? "selected" : ""}>${t}</option>`;
  const dt = p.teste ? 10 + C.d.bc[p.dt_attr || ar.ataque] + C.d.n3 : 0;
  folha(esc(x.nome), `<p class="meta">${p.acao ? `Gasta: ação ${p.acao}` : "Sem custo de ação definido"}${p.passiva ? " · efeito automático" : ""}</p><div class="desc">${esc(x.texto)}</div>
    ${p.passiva ? "" : `<div class="secao">Ajustes do ataque</div><div class="grade g3">
      <label class="campo"><span>Nível de dano</span><select id="aa-d">${[-3, -2, -1, 0, 1, 2, 3].map((n) => op(n, n > 0 ? `+${n}` : n, n === Math.max(-3, Math.min(3, p.delta)))).join("")}</select></label>
      <label class="campo"><span>Rolagem</span><select id="aa-v">${op(0, "normal", p.vantagem === 0)}${op(1, "vantagem", p.vantagem === 1)}${op(-1, "desvantagem", p.vantagem === -1)}</select></label>
      <label class="campo"><span>Crítico</span><select id="aa-c">${op(0, "normal", !p.critico)}${op(1, "garantido", p.critico)}</select></label></div>
      <p class="sub">Os ajustes vêm do texto da ação; confira antes de rolar.${p.mult ? ` Crítico ×${p.mult}.` : ""}${p.teste ? ` O alvo faz ${p.teste} contra DT ${dt}.` : ""}</p>`}`,
  `<button class="botao leve" data-a="acao-arma-usar" data-i="${i}" data-j="${j}">✓ Usar${p.acao ? ` (${p.acao})` : ""}</button>${p.passiva ? "" : `<button class="botao prim" data-a="acao-arma-rolar" data-i="${i}" data-j="${j}">🎲 Rolar ataque</button>`}`);
};
A["acao-arma-rolar"] = (el) => {
  const i = int(el.dataset.i), j = int(el.dataset.j), ar = ARMAS[S.armas[i].grupo], x = ar.acoes[j], p = R.acaoArma(x.nome, x.texto);
  const o = { delta: int($("#aa-d").value), vant: int($("#aa-v").value), critico: $("#aa-c").value === "1", acerto: p.acerto_garantido, mult: p.mult,
    rotulo: `${ar.nome}: ${x.nome}`, acao: p.acao || "Comum", teste: p.teste, dtAttr: p.dt_attr };
  fecharFolha(); atacar(i, o);
};
A["acao-arma-usar"] = (el) => {
  const i = int(el.dataset.i), j = int(el.dataset.j), ar = ARMAS[S.armas[i].grupo], x = ar.acoes[j], p = R.acaoArma(x.nome, x.texto);
  const aviso = marcarAcao(p.acao);
  registrarDiario({ titulo: `⚔ ${x.nome}`, linhas: [esc(x.texto)].concat(aviso ? [aviso] : []) });
  fecharFolha(); render(); toast(`<b>${esc(x.nome)}</b>${p.acao ? ` (ação ${p.acao})` : ""}. ${aviso}`);
};
A["recurso"] = (el, ev) => {
  if (ev) ev.stopPropagation();
  const i = int(el.dataset.i), w = S.armas[i], chave = `${i}:${w.grupo}`, n = el.dataset.n;
  const [, mx] = (R.RECURSOS_ARMA[w.grupo] || []).find((r) => r[0] === n) || [n, 0];
  mudar((s) => { const r = s.recursos[chave] = s.recursos[chave] || {}; r[n] = Math.max(0, int(r[n]) + int(el.dataset.d)); if (mx) r[n] = Math.min(mx, r[n]); });
};

A["extras"] = () => {
  const n = C.d.acoes_extras;
  if (!n) { toast("Ações extras vêm com 15, 30, 45, 55, 65, 75, 85 e 95 de Destreza."); return; }
  folha("Ações extras", `<p class="sub">Cada ação extra da Destreza é Comum ou Bônus, escolhida uma vez e fixa (o livro não deixa trocar depois).</p>
    ${[...Array(n)].map((_, i) => `<label class="campo"><span>Ação extra ${i + 1} (DES ${R.LIMIARES_ACOES[i]})</span><select class="ext" ${banco.modo === "edicao" ? "" : "disabled"}>
      <option value="">— escolher —</option>${["Comum", "Bônus"].map((t) => `<option ${S.acoes_extras_tipos[i] === t ? "selected" : ""}>${t}</option>`).join("")}</select></label>`).join("")}
    ${banco.modo === "edicao" ? "" : `<p class="sub">Para escolher, use o Modo Edição.</p>`}`,
  banco.modo === "edicao" ? `<button class="botao leve" data-a="fechar">Cancelar</button><button class="botao prim" data-a="extras-ok">Salvar</button>` : "");
};
A["extras-ok"] = () => { const v = [...document.querySelectorAll(".ext")].map((x) => x.value); fecharFolha(); mudar((s) => { s.acoes_extras_tipos = v; }); };


