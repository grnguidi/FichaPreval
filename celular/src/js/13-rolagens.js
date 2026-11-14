// ----- rolagens
const desfazer = [];
const horaAgora = () => new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
function registrarDiario(entrada) {   // o diário fica guardado com a ficha (últimas 100 entradas)
  if (!S) return;
  S.diario.unshift(Object.assign({ hora: horaAgora() }, entrada));
  if (S.diario.length > 100) S.diario.length = 100;
  salvar();
}
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
  registrarDiario({ titulo, linhas });
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
/* Ataque com a arma i. o: {delta (níveis de dano), vant (1 vantagem, -1 desvantagem), critico (garantido), acerto (garantido),
   mult (multiplicador do crítico), rotulo, acao (tipo de ação gasta), teste e dtAttr (resistência do alvo), extra (linhas)} */
let ataquePendente = null;
function recursoMunicao(grupo, tipo) {
  const nomes = (R.RECURSOS_ARMA[grupo] || []).map((r) => r[0]);
  const alvo = { flecha: ["Flechas", "Virotes"], virote: ["Virotes", "Flechas"], cartucho: ["Cartuchos"], frasco: ["Frascos"] }[tipo] || [];
  return alvo.find((n) => nomes.includes(n)) || null;
}
function gastarMunicao(i, tipo, qtd) {
  const w = S.armas[i], n = recursoMunicao(w.grupo, tipo);
  if (!n) return `Gasta ${qtd < 0 ? "toda a" : qtd} ${tipo || "munição"}${qtd !== 1 ? "s" : ""}.`;
  const chave = `${i}:${w.grupo}`, r = S.recursos[chave] = S.recursos[chave] || {}, tem = int(r[n]);
  r[n] = Math.max(0, tem - (qtd < 0 ? tem : qtd));
  return qtd > tem ? `${n}: o contador tinha só ${tem} (ficou 0). Ajuste no − / + da arma.` : `${n}: ${tem} → ${r[n]}.`;
}
function atacar(i, o = {}) {
  const w = S.armas[i], ar = ARMAS[w.grupo]; if (!ar) return;
  const nv = int(w.nivel, 1), k = ar.ataque;
  const l = ar.tabela.find((x) => x.nivel === nv) || ar.tabela[0];
  const [lD, nvD] = R.linhaDanoNivel(ar.tabela, nv, C.ef.dano_nivel + int(o.delta));
  const maestria = C.escolha.maestria.includes(w.grupo) ? 1 : 0, props = R.lerProps(w.props);
  const ep = R.efeitoProps(props, R.danoComDados(lD.dano, Math.floor(R.cap(C.a[k]) / 30)), int(l.critico, 20));
  const bonus = C.d.bc[k] + C.d.n3 + (R.ACERTO_ARMA[nv] || 0) + C.ef.acerto + maestria + ep.acerto;
  const vig = ar.vigor ? (nv >= 8 ? 10 : nv >= 4 ? 8 : 5) : 0;
  const dg = S.desgaste[i] = Object.assign({ usados: 0, desgastada: false, em: 0, contado: -1 }, S.desgaste[i] || {});
  if (dg.desgastada) {
    ataquePendente = [i, o];
    folha(`${ar.nome} desgastada`, `<p>A arma não pode ser usada por um turno depois de desgastar.</p>`,
      `<button class="botao leve" data-a="fechar">Cancelar</button><button class="botao prim" data-a="reafiar" data-i="${i}" data-rolar="1">Já passou — atacar</button>`);
    return;
  }
  pagar("vigor_atual", C.d.vigor, vig, "Vigor", (custo) => {
    const golpes = Math.max(1, int(o.golpes, 1)), ataques = [];
    for (let g = 0; g < golpes; g++) {
      if (g === 0 || !o.umAcerto) {
        const a = R.rolarAtaque(bonus, R.vantagem(C.a[k]) || o.vant === 1, ep.margem, rng, o.vant === -1);
        if (o.critico && !a.desastre) a.critico = true;
        ataques.push(a);
      } else ataques.push(ataques[0]);
    }
    const at = Object.assign({}, ataques[0], { critico: ataques.some((a) => a.critico), desastre: ataques.every((a) => a.desastre) });
    const linhas = golpes > 1 ? [`<span class="sub">${golpes} disparos/golpes, ${o.umAcerto ? "uma só jogada de acerto para todos" : "um teste de acerto para cada"}.</span>`] : [];
    if (golpes === 1) linhas.push(txtAtaque(at));
    if (o.critico) linhas.push(`<span class="ok">Crítico garantido por esta ação.</span>`);
    if (o.acerto) linhas.push(`<span class="ok">Acerto garantido por esta ação.</span>`);
    const turno = sessao.ativa && sessao.meusTurnos ? sessao.meusTurnos : null;
    if (at.critico || turno === null || dg.contado !== turno) {
      const [u, gastou] = R.desgasteAposAtaque(int(dg.usados), at.critico, ep.desgaste);
      dg.usados = u; dg.contado = turno === null ? -1 : turno;
      if (gastou) { dg.desgastada = true; dg.em = sessao.meusTurnos || 0; }
    }
    const mult = Math.max(ep.mult, int(o.mult) || 0);
    let soma = 0;
    ataques.forEach((a, g) => {
      const pre = golpes > 1 ? `<b>#${g + 1}</b> ` : "";
      if (golpes > 1 && (g === 0 || !o.umAcerto)) linhas.push(pre + txtAtaque(a));
      if (a.desastre) return;
      const [tot, partes] = R.rolarExpr(ep.dano, rng, a.critico, mult);
      soma += tot;
      linhas.push(pre + txtDano(tot, partes) + ` · ${esc(lD.tipo)}` + (nvD !== nv ? ` · dano de nível ${nvD}` : "") + (a.critico && mult > 2 ? ` · crítico ×${mult}` : ""));
      for (const [x, tipo, cnd] of ep.extras) {
        const [t2, p2] = R.rolarExpr(x, rng, a.critico, mult);
        soma += t2;
        linhas.push(pre + txtDano(t2, p2, `+ ${esc(tipo)}`) + (cnd ? ` <span class="sub">(${esc(cnd)})</span>` : ""));
      }
    });
    if (!at.desastre) linhas.push(...linhasSet(at.critico));
    if (golpes > 1 && !at.desastre) linhas.push(`Dano somado se todos acertarem: <b>${soma}</b> <span class="sub">— desconte os que errarem a CA do alvo.</span>`);
    if (o.municao) linhas.push(gastarMunicao(i, o.municaoTipo || "", int(o.municao)));
    else {
      const nm = recursoMunicao(w.grupo, "flecha"), r = S.recursos[`${i}:${w.grupo}`] || {};
      if (nm && int(r[nm]) > 0) linhas.push(gastarMunicao(i, "flecha", 1));
    }
    if (!at.desastre) {
      if (ep.voraz && at.critico) {
        const cura = R.rolarExpr("1d10", rng)[0], mx = C.d.vida, antes = S.vida.atual === "" || S.vida.atual == null ? mx : int(S.vida.atual, mx);
        S.vida.atual = String(Math.min(mx, antes + cura));
        linhas.push(`Voraz: recupera ${cura} de Vida (${antes} → ${Math.min(mx, antes + cura)}).`);
      }
    }
    if (o.teste) linhas.push(`O alvo faz <b>${esc(o.teste)}</b> contra DT <b>${10 + C.d.bc[o.dtAttr || k] + C.d.n3}</b>.`);
    for (const x of o.extra || []) linhas.push(x);
    if (props.length) linhas.push(`<span class="sub">Propriedades: ${esc(props.join(", "))}</span>`);
    if (custo) linhas.push(`<span class="sub">${custo}</span>`);
    if (C.ef.acerto) linhas.push(`<span class="sub">Inclui +${C.ef.acerto} de acerto de talento situacional.</span>`);
    if (maestria) linhas.push(`<span class="sub">Inclui +1 de Maestria nesta arma.</span>`);
    linhas.push(`<span class="sub">${at.critico ? `Desgaste: o crítico reafiou a arma.` : dg.desgastada ? `<b class="erro">A arma desgastou</b>: sem uso no próximo turno.` : `Desgaste: restam ${ep.desgaste - dg.usados} turno(s) afiado(s).`}</span>`);
    const aviso = marcarAcao(o.acao || "Comum");
    if (aviso) linhas.push(`<span class="erro">${aviso}</span>`);
    salvar(); render();
    mostrarRolagem(`⚔ ${esc(o.rotulo || ar.nome)} nv ${nv}`, linhas);
  });
}
A["rolar-arma"] = (el) => atacar(int(el.dataset.i), { acao: "Comum" });
A["rolar-ini"] = () => {
  const d = [...Array(C.d.iniciativa_dados)].map(() => rng(20)), b = C.d.iniciativa_bonus;
  mostrarRolagem("⏳ Iniciativa", [`Iniciativa: <b style="font-size:20px">${Math.max(...d) + b}</b> <span class="sub">[d20 ${d.join(", ")} → ${Math.max(...d)} +${b}]</span>`]);
};
A["rolar-per"] = (el) => {
  if (banco.modo === "edicao" && !el.dataset.rolar) return infoPericia(el);
  const r = R.rolarPericia(int(el.dataset.b), int(el.dataset.d, 1), rng);
  mostrarRolagem(`🎲 ${esc(el.dataset.n)}`, [`${esc(el.dataset.n)}: <b style="font-size:20px">${r.total}</b> <span class="sub">[d20 ${r.d20.join(", ")}${r.d20.length > 1 ? " → maior" : ""} +${r.bonus}]</span>`,
    `<span class="sub">DT: fácil 10 · média 15 · difícil 25 · muito difícil 35 · heroica 50 · lendária 80</span>`]);
};
A["esc-props"] = (el) => {
  const i = int(el.dataset.i), w = S.armas[i], max = propsMax(w), atuais = R.lerProps(w.props);
  const tem = (n) => atuais.find((p) => R.nomeProp(p) === n), elAtual = (tem("Elemental") || "").split("(")[1];
  const outras = atuais.filter((p) => !R.NOMES_PROPRIEDADES.includes(R.nomeProp(p)));
  folha(`Propriedades — ${esc(w.grupo)} nv ${int(w.nivel, 1)}`, `<p class="sub" id="pp-c"></p><div class="lista">${R.PROPRIEDADES.map(([n, d]) =>
    `<label class="item" style="cursor:pointer"><input type="checkbox" class="pp" value="${esc(n)}" ${tem(n) ? "checked" : ""} style="width:22px;height:22px;margin-right:10px">
      <div class="tx"><b>${esc(n)}</b><small>${esc(d)}</small>${n === "Elemental" ? `<select id="pp-el" style="margin-top:4px">${R.ELEMENTOS_PROP.map((x) => `<option ${elAtual && elAtual.startsWith(x) ? "selected" : ""}>${x}</option>`).join("")}</select>` : ""}</div></label>`).join("")}</div>
    <label class="campo"><span>Outras (armas especiais), separadas por vírgula</span><input id="pp-o" value="${esc(outras.join(", "))}"></label><p class="erro" id="pp-e"></p>`,
  `<button class="botao leve" data-a="fechar">Cancelar</button><button class="botao prim" data-a="props-ok" data-i="${i}">Salvar</button>`, (c) => {
    const conta = () => {
      const n = c.querySelectorAll(".pp:checked").length;
      $("#pp-c").innerHTML = `<b class="${n > max ? "erro" : ""}">${n} de ${max}</b> (tabela da arma${C.escolha.dominio[w.grupo] ? ` + ${C.escolha.dominio[w.grupo]} do Domínio` : ""})`;
    };
    c.querySelectorAll(".pp").forEach((x) => x.addEventListener("change", conta)); conta();
  });
};
A["props-ok"] = (el) => {
  const i = int(el.dataset.i), w = S.armas[i];
  const props = [...document.querySelectorAll(".pp:checked")].map((x) => x.value === "Elemental" ? `Elemental (${$("#pp-el").value})` : x.value).concat(R.lerProps($("#pp-o").value));
  const prob = R.problemasProps(props, propsMax(w));
  if (prob.length && !el.dataset.ok) { $("#pp-e").innerHTML = `${esc(prob.join("; "))}. Toque em Salvar de novo para salvar assim.`; el.dataset.ok = "1"; return; }
  fecharFolha(); mudar((s) => { s.armas[i].props = props.join(", "); });
};
A["reafiar"] = (el) => {
  const i = int(el.dataset.i), rolar = el.dataset.rolar;
  S.desgaste[i] = { usados: 0, desgastada: false, em: 0, contado: -1 }; salvar(); fecharFolha(); render();
  if (rolar) { const [pi, po] = ataquePendente || [i, { acao: "Comum" }]; ataquePendente = null; atacar(pi, po); }
};
A["descanso"] = (el) => {
  const tipo = el.dataset.t;
  if (tipo === "curto" && S.descansos_curtos >= R.DESCANSOS_CURTOS_MAX && !el.dataset.ok) {
    folha("Descanso curto", `<p>Já foram ${S.descansos_curtos} descansos curtos desde o último longo (o livro permite ${R.DESCANSOS_CURTOS_MAX}).</p>`,
      `<button class="botao leve" data-a="fechar">Cancelar</button><button class="botao prim" data-a="descanso" data-t="curto" data-ok="1">Descansar mesmo assim</button>`);
    return;
  }
  const d = C.d, maxs = { vida: d.vida, mana: d.mana, vigor: d.vigor }, ch = { vida: "atual", mana: "mana_atual", vigor: "vigor_atual" };
  const ats = Object.fromEntries(Object.entries(ch).map(([k, c]) => [k, S.vida[c] === "" || S.vida[c] == null ? maxs[k] : int(S.vida[c], maxs[k])]));
  const conds = Object.fromEntries(R.CONDICOES.map((n) => [n, int(S.condicoes[n].atual)]));
  const [novos, nc] = R.descanso(tipo, maxs, ats, conds);
  for (const [k, c] of Object.entries(ch)) S.vida[c] = String(novos[k]);
  for (const n of R.CONDICOES) S.condicoes[n].atual = nc[n] ? String(nc[n]) : "";
  S.descansos_curtos = tipo === "longo" ? 0 : S.descansos_curtos + 1;
  if (tipo === "longo") S.desgaste = {};
  recarregarUsos(tipo); S.turno = {}; S.contra_usados = 0;
  fecharFolha(); salvar(); render();
  const mud = R.CONDICOES.filter((n) => conds[n] !== nc[n]).map((n) => `${n} ${conds[n]} → ${nc[n]}`);
  mostrarRolagem(tipo === "curto" ? "☾ Descanso curto" : "☀ Descanso longo", ["vida", "mana", "vigor"].map((k) => `${k[0].toUpperCase() + k.slice(1)}: ${ats[k]} → <b>${novos[k]}</b>`)
    .concat(mud.length ? [`Condições: ${mud.join(", ")}`] : []).concat([`<span class="sub">${tipo === "curto" ? "Pode trocar o equipamento livremente. Usos por descanso curto renovados." : "Efeitos temporários médios somem; armas reafiadas; a Poção Espiritual, a Alma e todos os usos voltam."}</span>`]));
};
A["pocao"] = () => {
  const n = R.pocaoEspiritualDados(C.nv, C.d.curva.VIT), [tot, partes] = R.rolarExpr(`${n}d10`, rng);
  const mx = C.d.vida, antes = S.vida.atual === "" || S.vida.atual == null ? mx : int(S.vida.atual, mx);
  desfazer.push({ chave: "atual", antigo: S.vida.atual, desc: "Poção Espiritual" });
  S.vida.atual = String(Math.min(mx, antes + tot)); salvar(); render();
  mostrarRolagem("⚗ Poção Espiritual", [txtDano(tot, partes, "Cura"), `Vida: ${antes} → <b>${Math.min(mx, antes + tot)}</b>`, `<span class="sub">Ação comum para beber; uma por jogador por descanso longo.</span>`]);
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
  const manaC = custoEnc(e, v)[0], desc = manaC != null && manaC !== R.custoMana(v);
  pagar("mana_atual", C.d.mana, manaC, "Mana", (custo) => {
    const acImpl = impl ? (R.ACERTO_ARMA[impl] || 0) : 0;   // "+ acerto do cajado" (Magias) ou do selo (Feitiços)
    const at = R.rolarAtaque(C.d.bc[k] + C.d.n3 + acImpl, R.vantagem(C.a[k]), 20, rng);
    const linhas = [txtAtaque(at, per), `DT para o alvo resistir: <b>${k === "INT" ? C.d.dt_feiticaria : C.d.dt_desejo}</b>`];
    if (acImpl) linhas.push(`<span class="sub">Inclui +${acImpl} de acerto do ${k === "INT" ? "cajado" : "selo"} nv ${impl}.</span>`);
    const avisoAcao = marcarAcao(v.acao);
    if (avisoAcao) linhas.push(`<span class="erro">${avisoAcao}</span>`);
    let expr = R.danoDoEncantamento(v.descricao);
    const conds = R.condicoesDoEncantamento(v.descricao);
    if (expr && conds.length && expr.replace(/\s+/g, " ") === conds[0][0]) expr = null;
    const [arc, extraC] = R.arcanoEscala(C.a.ARC, talentos());
    if (!at.desastre) for (const [ce, cn] of conds) {
      const escl = R.escalarArcano(ce, arc, cn, extraC), [tot, partes] = R.rolarExpr(escl, rng, at.critico);
      linhas.push(txtDano(tot, partes, cn) + " pontos" + (escl !== ce ? ` <span class="sub">· ${ce} → ${escl} por ${arc} de Arcano${arc !== R.cap(C.a.ARC) ? " (Mente Arcana +10)" : ""}${extraC && cn !== "Morte" ? " + 1 cópia (Senhor das Condições)" : ""}</span>` : ""));
    }
    if (!at.desastre) linhas.push(...linhasSet(at.critico));
    if (expr && !at.desastre) {
      const extra = k === "INT" ? C.d.dados_extra_magia : C.d.dados_extra_feitico;
      const [tot, partes] = R.rolarExpr(R.danoComDados(expr, extra), rng, at.critico);
      linhas.push(txtDano(tot, partes, "Dados do encantamento") + (extra ? ` · +${extra} dado por ${k}` : ""));
    } else if (!expr && !conds.length) linhas.push(`<span class="sub">Este encantamento não tem dados na descrição.</span>`);
    if (custo) linhas.push(`<span class="sub">${custo}</span>`);
    if (desc) linhas.push(`<span class="sub">Matrícula: custa ${manaC} de Mana em vez de ${R.custoMana(v)}.</span>`);
    if (!x.equipado) linhas.push(`<span class="erro">Atenção: não está equipado.</span>`);
    if (impl < v.nivel) linhas.push(`<span class="erro">Atenção: precisa de ${k === "INT" ? "cajado" : "selo"} nv ${v.nivel}+ equipado.</span>`);
    mostrarRolagem(`✧ ${e.nome} (${v.tier} nv ${v.nivel})`, linhas);
  });
};
A["diario"] = () => folha("Diário de rolagens", S && S.diario.length ? `<div class="lista">${S.diario.map((r) => `<div class="item" style="display:block"><b style="color:var(--vinho)">${esc(r.titulo)}</b> <span class="sub">${r.hora}</span><div style="font-size:14px;line-height:1.5;margin-top:4px">${r.linhas.join("<br>")}</div></div>`).join("")}</div>` : `<div class="vazio-msg">Nenhuma rolagem ainda.</div>`,
  (desfazer.length ? `<button class="botao leve" data-a="desfazer">↺ Desfazer último custo</button>` : "")
  + (S && S.diario.length ? `<button class="botao leve" data-a="diario-limpar">Limpar</button>` : ""));
A["diario-limpar"] = () => { fecharFolha(); mudar((s) => { s.diario = []; }); toast("Diário limpo."); };

A["modo-vida"] = () => mudar((s) => { s.vida.modo = s.vida.modo === "media" ? "rolar" : "media"; });
A["rolar-vida"] = () => {
  const falta = C.nVida - S.vida.rolagens.length; if (falta <= 0) return;
  const novos = [...Array(falta)].map(() => 1 + Math.floor(Math.random() * 12));
  mudar((s) => { s.vida.rolagens = s.vida.rolagens.concat(novos); });
  toast(`🎲 ${falta}d12: ${novos.join(", ")} → +${novos.reduce((a, b) => a + b, 0)} de Vida`);
};
A["info-atr"] = (el) => {
  const k = el.dataset.k, [desc, afeta] = R.ATRIBUTOS_RESUMO[k];
  folha(`${R.NOMES_ATR[k]} · ${C.a[k]}`, `<div class="desc">${esc(desc)}</div>
    <div class="secao">Com o valor atual</div><ul class="avisos">${R.efeitosAtributo(k, C.a, C.d).map((x) => `<li class="ok">${esc(x)}</li>`).join("")}</ul>
    <div class="secao">O que ele move</div><ul class="avisos">${afeta.map((x) => `<li class="info">${esc(x)}</li>`).join("")}</ul>
    <p class="sub">10 é o início da jornada, 50 é maestria, 90 é talento extraordinário. Acima de 99 conta como 99.</p>`,
  `<button class="botao prim" data-a="fechar">OK</button>`);
};
function infoPericia(el) {
  const n = el.dataset.n, [resumo, usada] = R.PERICIAS_RESUMO[n] || ["", ""];
  const p = R.PERICIAS.find((x) => x[0] === n), atrs = p ? p[1] : null, req = p ? p[2] : false, tr = C.treinadas.has(n);
  const at = atrs ? atrs.map((k) => R.NOMES_ATR[k]).join(" ou ") : `à escolha do jogador (agora ${R.NOMES_ATR[S.prevalencia_attr || "ARC"]})`;
  folha(esc(n), `<p class="meta">Atributo: ${at}${req ? " · exige treino (sem treino, só um sucesso crítico passa)" : ""}${usada ? ` · Usada em: ${esc(usada)}` : ""}</p>
    <div class="desc">${esc(resumo)}</div>
    <p class="sub">Teste: ${el.dataset.d}d20 (1 a mais a cada 20 pontos do atributo, fica o maior) +${el.dataset.b}. Treinada soma a Curva do atributo; todas somam nível ÷ 2.</p>
    <p class="sub">DT: fácil 10 · média 15 · difícil 25 · muito difícil 35 · heroica 50 · lendária 80</p>`,
  `<button class="botao leve" data-a="treinar" data-n="${esc(n)}" data-fechar="1">${tr ? "Tirar o treino" : "Treinar"}</button><button class="botao prim" data-a="rolar-per" data-rolar="1" data-n="${esc(n)}" data-b="${el.dataset.b}" data-d="${el.dataset.d}">🎲 Rolar</button>`);
}
A["treinar"] = (el) => { if (el.dataset.fechar) fecharFolha(); mudar((s) => { const n = el.dataset.n; s.pericias = s.pericias.includes(n) ? s.pericias.filter((x) => x !== n) : s.pericias.concat([n]); }); };
A["per-atk"] = (el) => mudar((s) => { s.pericia_ataque = el.dataset.n; });
A["prev-attr"] = (el) => mudar((s) => { s.prevalencia_attr = el.dataset.k; });
A["portao"] = (el) => mudar((s) => { const v = s.portao[el.dataset.n]; v[int(el.dataset.i)] = !v[int(el.dataset.i)]; });
A["editar-cond"] = (el) => {
  const n = el.dataset.n, c = S.condicoes[n];
  folha(n, `<p class="sub">Ao encher: ${esc((R.CONDICAO_ATIVA[n] || {}).desc || "")} Teste: ${R.CONDICAO_TESTE[n] || ""} (sucesso recebe metade).${C.escolha.cond_extra[n] ? ` Condição Endurecida: +${C.escolha.cond_extra[n]} no máximo.` : ""}</p><label class="campo"><span>Acumulado</span><input id="c-at" type="number" inputmode="numeric" value="${int(c.atual)}"></label>
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
  if (sl.startsWith("meta") && !slotValido(sl)) { toast("Esse talento vem com uma Meta de Vida concluída."); return; }
  if (sl !== "extra" && !sl.startsWith("meta") && int(sl) > C.nv) { toast(`Esse talento é liberado no nível ${sl}.`); return; }
  seletor({
    titulo: sl === "extra" ? "Talento extra (Versátil)" : sl.startsWith("meta") ? `Talento da Meta ${sl.slice(4)}` : `Talento do nível ${sl}`,
    filtros: [{ chave: "cat", valor: "Todas as categorias", opcoes: ["Todas as categorias"].concat(CATS_TAL) }],
    extraTopo: S.talentos[sl] ? `<div class="item" data-a="sel-item" data-id="__nenhum"><span class="marca">—</span><div class="tx"><b>Deixar vazio</b></div></div>` : "",
    itens: (f) => D.talentos.filter((t) => f.cat === "Todas as categorias" || t.categoria === f.cat).map((t, j) => ({
      id: t.nome, nome: t.nome, sub: `Nv ${t.nivel}${t.requisito ? " · " + t.requisito : ""} · ${t.categoria.replace("Talentos de ", "")}`, busca: t.descricao, motivo: statusTal(C, t, sl) })),
    detalhe: (id) => { const t = TAL[id]; return `<p class="meta">${esc(t.categoria)} · Nível ${t.nivel}${t.requisito ? ` · requer ${esc(t.requisito)}` : ""}</p><div class="desc">${esc(t.descricao)}</div>`; },
    escolher: (id) => mudar((s) => { if (s.talentos[sl] !== id) delete s.talentos_escolha[sl]; s.talentos[sl] = id; }),
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
  if (!x.equipado && C.espUsados + custoEnc(ENC[x.familia])[1] > C.d.espacos_encant) { toast(`Sem espaço: ${C.espUsados}/${C.d.espacos_encant} usados.`); return; }
  mudar(() => { x.equipado = !x.equipado; });
};
A["prox-versao"] = (el) => { const x = S.encantamentos[int(el.dataset.i)], e = ENC[x.familia]; const p = e.versoes.find((v) => !x.versoes.includes(v.nivel)); fecharFolha(); mudar(() => { x.versoes.push(p.nivel); x.versoes.sort((a, b) => a - b); }); };
A["rem-enc"] = (el) => { const i = int(el.dataset.i); fecharFolha(); mudar((s) => { s.encantamentos.splice(i, 1); }); };
A["sel-item"] = (el) => itemSeletor(el.dataset.id);
A["sel-voltar"] = () => seletor(pickerAtual);
A["sel-ok"] = (el) => { const cfg = pickerAtual; fecharFolha(); cfg.escolher(el.dataset.id); };
A["fechar"] = () => fecharFolha();

