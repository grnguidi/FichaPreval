// ------------------------------------------------------------------ grupo: interação entre jogadores na sessão
// O PC do mestre guarda e repassa tudo (grupo.py). Tudo que mexe na ficha de outro vira um pedido que ele aceita.
const AJUDAS = new Set(["medicina", "incentivo", "cura", "buff", "refeicao"]), REACOES = ["🎉", "👏", "😱", "💀"];
const SINAIS = ["Preciso de cura", "Vou focar este alvo", "Recuem!", "Guardem a Reação", "Sem Mana", "Pronto para o combo"];
const jaAceitos = new Set();
async function ga(m, okMsg) {
  if (!sessao.id) { pedirNomeSessao(); return false; }
  try {
    const r = await api("/api/grupo", Object.assign({ id: sessao.id }, m));
    if (!r.ok) { toast(esc(r.erro || "Não deu certo.")); return false; }
    if (r.msg || okMsg) toast(esc(r.msg || okMsg));
    consultarSessao();
    return true;
  } catch (e) { toast("Sem conexão com o mestre…"); return false; }
}
function grupoChegou(g) {
  sessao.grupo = g;
  const meus = g.propostas.filter((p) => p.para === sessao.id);
  if (banco.autoAjuda) meus.filter((p) => AJUDAS.has(p.tipo) && !jaAceitos.has(p.id)).forEach((p) => { jaAceitos.add(p.id); ga({ acao: "responder", num: p.id, aceitar: true }); });
  const nb = $("#nav-grupo");
  if (nb) nb.classList.toggle("pend", meus.length > 0 || !!(g.teste && g.teste.aberto && !g.teste.ja));
}
function bonusPericia(nome) {   // [bônus, dados] como na aba Perícias; defesas e ataques pelo Bônus de Combate
  const c = calcular(), p = R.PERICIAS.find((x) => x[0] === nome);
  if (p) {
    const tr = c.treinadas.has(nome), at = p[1] || [S.prevalencia_attr || "ARC"], [, b0, dados] = R.periciaFora(c.a, c.nv, at, tr);
    const mestre = c.escolha.pericia_mestre.includes(nome);
    return [b0 + (c.ef.pericia[nome] || 0) + (mestre ? 2 : 0), dados + (mestre ? 1 : 0)];
  }
  const d = R.PERICIAS_DEFESA.find((x) => x[0] === nome);
  if (d) return [c.d.bc[d[1]] + c.d.n3 + (c.tal.has(d[2]) ? 2 : 0), R.vantagem(c.a[d[1]]) ? 2 : 1];
  return [0, 1];
}
function rolarPericiaNome(nome) {
  const [b, d] = bonusPericia(nome), r = R.rolarPericia(b, d, rng);
  return { total: r.total, txt: `${nome}: ${r.total} [d20 ${r.d20.join(", ")}${r.d20.length > 1 ? " → maior" : ""} +${r.bonus}]` };
}
function compartilharRolagem(titulo, linhas) {
  const g = sessao.grupo;
  if (!sessao.id || !g || !g.cfg.feed || banco.compartilhar === false) return;
  const limpo = (x) => String(x).replace(/<[^>]*>/g, "");
  api("/api/grupo", { id: sessao.id, acao: "rolagem", titulo: limpo(titulo), linhas: linhas.slice(0, 4).map(limpo), destaque: /cr[íi]tico|desastre/i.test(linhas.join(" ")) }).catch(() => {});
}
const dinheiroMeu = () => (S ? int(S.dinheiro_c) : 0);

function pGrupo() {
  const g = sessao.grupo;
  if (!sessao.id) return `<div class="vazio-msg">Entre na mesa para ver o grupo.<br><button class="botao prim" data-a="sessao-nome" style="margin-top:10px">Entrar na mesa</button></div>`;
  if (!g) return `<div class="vazio-msg">Carregando o grupo…</div>`;
  const eu = sessao.id, para = g.propostas.filter((p) => p.para === eu), meus = g.propostas.filter((p) => p.de === eu);
  let h = "";
  if (para.length || meus.length) {
    h += secao("Pedidos") + `<div class="lista">` + para.map((p) => `<div class="item pedido"><div class="tx"><b>${esc(p.de)}</b> quer te dar<small>${esc(p.texto)}</small></div>
      <button class="botao prim mini" data-a="g-resp" data-id="${p.id}" data-s="1">Aceitar</button><button class="botao leve mini" data-a="g-resp" data-id="${p.id}" data-s="0">Recusar</button></div>`).join("")
      + meus.map((p) => `<div class="item"><div class="tx"><b>Aguardando ${esc(p.para)}</b><small>${esc(p.texto)}</small></div><button class="botao leve mini" data-a="g-cancelar" data-id="${p.id}">Cancelar</button></div>`).join("") + `</div>`;
  }
  if (g.teste) {
    const t = g.teste;
    h += secao("Teste em grupo") + `<div class="cartao" style="padding:12px"><b>${esc(t.pericia)}</b>${t.dt ? ` <span class="sub">DT ${t.dt}</span>` : ""}
      ${t.aberto ? `<p class="sub" style="margin:6px 0">${t.rolaram.length ? "Já rolaram: " + esc(t.rolaram.join(", ")) + ". " : ""}${t.faltam.length ? "Faltam: " + esc(t.faltam.join(", ")) + "." : ""} O resultado aparece quando todos rolarem.</p>
        ${t.ja ? `<span class="ok">Você rolou ${t.res.length ? t.res[0].total : ""}.</span>` : `<button class="botao prim" data-a="g-teste">🎲 Rolar ${esc(t.pericia)}</button>`}`
      : `<div class="lista" style="margin-top:8px">${t.res.map((r) => `<div class="item"><div class="tx"><b>${esc(r.nome)}</b></div><b style="font-size:19px">${r.total}</b>${t.dt ? `<span class="${r.total >= t.dt ? "ok" : "erro"}" style="margin-left:8px">${r.total >= t.dt ? "passou" : "falhou"}</span>` : ""}</div>`).join("")}</div>`}</div>`;
  }
  const membros = g.membros.slice().sort((a, b) => (b.eu ? 1 : 0) - (a.eu ? 1 : 0));
  h += secao("Aliados", g.ordem.length ? "em combate" : "") + membros.map((m) => {
    const barra = m.pct == null ? "" : `<div class="gbarra"><i style="width:${m.pct}%;background:${m.pct > 50 ? "var(--c-vigor)" : m.pct > 20 ? "var(--c-per)" : "var(--c-vida)"}"></i></div>`;
    const conds = (m.cond || []).map((c) => `<span class="chip">${esc(c[0])} ${c[1]}/${c[2]}</span>`).join("") + (m.efeitos || []).map((e) => `<span class="chip ef">⏳ ${esc(e)}</span>`).join("");
    return `<div class="cartao aliado ${m.vez ? "vez" : ""} ${m.incapaz ? "caido" : ""}" ${m.eu ? "" : `data-a="g-aliado" data-n="${esc(m.nome)}"`}>
      <div class="topo-al"><b>${esc(m.nome)}${m.eu ? " (você)" : ""}</b><span class="sub">${esc(m.personagem || "")}${m.nivel ? ` · Nv ${m.nivel}` : ""}${m.vez ? " · ⚔ vez" : ""}${m.sem_sinal ? " · sem sinal" : ""}</span>
        ${m.vida ? `<span class="vida">${m.vida[0]}/${m.vida[1]}</span>` : m.pct != null ? `<span class="vida">${m.pct}%</span>` : ""}</div>
      ${barra}${m.incapaz ? `<p class="erro" style="margin:6px 0 0"><b>Incapaz</b> — Portão da Morte: ${m.portao ? m.portao[0] : 0} sucesso(s), ${m.portao ? m.portao[1] : 0} falha(s)${m.eu ? "" : ". Toque para ajudar com Medicina."}</p>` : ""}
      ${conds ? `<div class="chips">${conds}</div>` : ""}
      ${m.sinal ? `<p class="sinal">⚑ ${esc(m.sinal)}</p>` : ""}${m.intencao ? `<p class="sub" style="margin:4px 0 0">Pretende: ${esc(m.intencao)}</p>` : ""}
      ${m.vinculo ? `<p class="sub" style="margin:4px 0 0">Vínculo: ${esc(m.vinculo)}</p>` : ""}
      ${m.eu ? `<div class="acoes-al"><button class="botao leve mini" data-a="g-sinal">⚑ Sinal e intenção</button>
        <span class="sub">Mostrar aos aliados:</span>${[["tudo", "tudo"], ["barra", "só a barra"], ["nada", "nada"]].map(([v, r]) => `<button class="chip-acao ${g.vis === v ? "on" : ""}" data-a="g-vis" data-v="${v}">${r}</button>`).join("")}</div>` : ""}
    </div>`;
  }).join("") + (g.cfg.ajuda && membros.length > 1 ? `<button class="botao leve" data-a="g-refeicao" style="width:100%;margin-top:8px">🍲 Cozinhar para o grupo</button>` : "");
  if (g.espolio) {
    h += secao("Espólio", "marque o que você quer") + `<div class="lista">` + g.espolio.itens.map((i) => {
      const quero = i.quer.includes(eu);
      return `<div class="item"><div class="tx"><b>${i.qtd}× ${esc(i.item)}</b><small>${i.quer.length ? "Querem: " + esc(i.quer.join(", ")) : "Ninguém marcou"}</small></div>
        <button class="botao ${quero ? "prim" : "leve"} mini" data-a="g-quero" data-id="${i.id}" data-s="${quero ? 0 : 1}">${quero ? "✓ Quero" : "Quero"}</button></div>`;
    }).join("") + `</div>` + (g.espolio.contos ? `<p class="sub">Dinheiro a dividir: ${esc(g.espolio.contos_txt)}.</p>` : "") + `<p class="sub">O mestre divide: empate é decidido no d20.</p>`;
  }
  if (g.caixa) {
    h += secao("Caixa do grupo") + `<div class="cartao dinheiro" data-a="g-caixa"><span>Caixa</span><b>${esc(g.caixa.txt)}</b><small>pôr ou tirar ›</small></div>`
      + (g.caixa.log.length ? `<p class="sub" style="margin:6px 2px">${g.caixa.log.slice(0, 4).map(esc).join("<br>")}</p>` : "");
  }
  if (g.cfg.feed) {
    h += secao("Rolagens do grupo", `<button class="chip-acao ${banco.compartilhar === false ? "" : "on"}" data-a="g-compartilhar">${banco.compartilhar === false ? "minhas: ocultas" : "minhas: visíveis"}</button>`)
      + (g.feed.length ? `<div class="lista">` + g.feed.slice(0, 20).map((f) => `<div class="item feed ${f.destaque ? "dest" : ""}"><div class="tx"><b>${esc(f.quem)} · ${esc(f.titulo)}</b><small>${f.linhas.map(esc).join("<br>")}</small>
        <div class="reacoes">${REACOES.map((r) => { const q = (f.reacoes[r] || []); return `<button class="${q.includes(eu) ? "on" : ""}" data-a="g-reagir" data-seq="${f.seq}" data-r="${r}">${r}${q.length ? " " + q.length : ""}</button>`; }).join("")}<span class="sub">${esc(f.hora)}</span></div></div></div>`).join("") + `</div>`
        : `<div class="vazio-msg">Nenhuma rolagem ainda.</div>`);
  }
  if (g.cfg.diario) {
    h += secao("Diário do grupo") + `<button class="botao leve" data-a="g-nota" style="width:100%">＋ Anotar</button>`
      + (g.notas.length ? `<div class="lista" style="margin-top:8px">` + g.notas.map((n) => `<div class="item"><div class="tx"><b>${esc(n.quem)}</b> <span class="sub">${esc(n.hora)}</span><small style="white-space:pre-wrap">${esc(n.texto)}</small></div>
        ${n.quem === eu ? `<button class="botao leve mini" data-a="g-nota-del" data-id="${n.id}" aria-label="Apagar nota">✕</button>` : ""}</div>`).join("") + `</div>` : "");
  }
  h += `<p class="sub" style="margin-top:16px"><button class="chip-acao ${banco.autoAjuda ? "on" : ""}" data-a="g-auto">${banco.autoAjuda ? "✓ " : ""}Aceitar ajudas sem perguntar</button> Trocas de item e dinheiro sempre perguntam. O mestre vê tudo e pode desligar cada recurso.</p>`;
  return h;
}
A["g-resp"] = (el) => ga({ acao: "responder", num: int(el.dataset.id), aceitar: el.dataset.s === "1" });
A["g-cancelar"] = (el) => ga({ acao: "cancelar", num: int(el.dataset.id) });
A["g-vis"] = (el) => ga({ acao: "vis", modo: el.dataset.v });
A["g-quero"] = (el) => ga({ acao: "espolio_quero", num: int(el.dataset.id), quer: el.dataset.s === "1" });
A["g-reagir"] = (el) => ga({ acao: "reagir", seq: int(el.dataset.seq), r: el.dataset.r });
A["g-compartilhar"] = () => { banco.compartilhar = banco.compartilhar === false; gravarLocal(); render(); toast(banco.compartilhar ? "Suas rolagens aparecem para o grupo." : "Suas rolagens ficam só com você."); };
A["g-auto"] = () => { banco.autoAjuda = !banco.autoAjuda; gravarLocal(); render(); };
A["g-teste"] = () => {
  if (!S) { toast("Abra uma ficha para rolar."); return; }
  const t = sessao.grupo.teste, r = rolarPericiaNome(t.pericia);
  registrarDiario({ titulo: `🎲 Teste em grupo: ${esc(t.pericia)}`, linhas: [esc(r.txt)] });
  ga({ acao: "teste_rolar", total: r.total, txt: r.txt }, `Você rolou ${r.total}.`);
};
A["g-aliado"] = (el) => {
  const n = el.dataset.n, m = sessao.grupo.membros.find((x) => x.nome === n), cfg = sessao.grupo.cfg; if (!m) return;
  const b = (a, t, s) => `<div class="item" data-a="${a}" data-n="${esc(n)}"><div class="tx"><b>${t}</b><small>${s}</small></div><span class="sub">›</span></div>`;
  folha(n, `<div class="lista">`
    + (cfg.ajuda && m.incapaz ? b("g-medicina", "✚ Medicina", "Teste contra DT 15: um sucesso no Portão da Morte dele") : "")
    + (cfg.ajuda ? b("g-incentivo", "↯ Incentivar", "Gasta sua Reação: ele age logo antes de você neste turno") + b("g-cura", "✦ Curar", "Manda a cura que você rolou para a Vida dele") + b("g-buff", "⏳ Dar um efeito", "Um bônus ou proteção com duração em turnos") : "")
    + (cfg.trocas ? b("g-item", "🎒 Dar um item", "Sai da sua bolsa e entra na dele") + b("g-dinheiro", "🪙 Dar dinheiro", `Você tem ${esc(R.formatarDinheiro(dinheiroMeu()))}`) : "")
    + (cfg.sussurro !== "off" ? b("g-sussurro", "🤫 Sussurrar", cfg.sussurro === "tudo" ? "O mestre também lê" : "O mestre só vê que houve um sussurro") : "")
    + (cfg.diario ? b("g-vinculo", "❧ Vínculo", m.vinculo ? esc(m.vinculo) : "Anote o que liga vocês dois") : "") + `</div>
    <p class="sub">O que mexe na ficha dele vira um pedido: ele (ou o mestre) aceita antes de valer.</p>`);
};
const precisaFicha = () => { if (!S) { toast("Abra uma ficha primeiro."); return true; } return false; };
A["g-medicina"] = (el) => {
  if (precisaFicha()) return;
  const r = rolarPericiaNome("Medicina"); fecharFolha();
  registrarDiario({ titulo: `✚ Medicina em ${esc(el.dataset.n)}`, linhas: [esc(r.txt), r.total >= 15 ? "Sucesso (DT 15)." : "Falhou (DT 15)."] });
  ga({ acao: "propor", tipo: "medicina", para: el.dataset.n, total: r.total, txt: r.txt });
};
A["g-incentivo"] = (el) => { fecharFolha(); if (S) { marcarAcao("Reação"); salvar(); } ga({ acao: "propor", tipo: "incentivo", para: el.dataset.n }); };
A["g-cura"] = (el) => folha(`Curar ${el.dataset.n}`, `<label class="campo"><span>Quanto de Vida</span><input id="gc-v" type="number" inputmode="numeric" min="1"></label>
  <label class="campo"><span>De onde vem (opcional)</span><input id="gc-d" maxlength="60" placeholder="Ex.: Toque Sagrado"></label><p class="sub">Role a cura na sua ficha e mande o total. A Vida dele não passa do máximo.</p>`,
  `<button class="botao leve" data-a="fechar">Cancelar</button><button class="botao prim" data-a="g-cura-ok" data-n="${esc(el.dataset.n)}">Enviar</button>`);
A["g-cura-ok"] = (el) => { const v = int($("#gc-v").value); if (v < 1) { $("#gc-v").focus(); return; } const d = $("#gc-d").value; fecharFolha(); ga({ acao: "propor", tipo: "cura", para: el.dataset.n, valor: v, desc: d }); };
A["g-buff"] = (el) => folha(`Efeito em ${el.dataset.n}`, `<label class="campo"><span>Nome do efeito</span><input id="gb-n" maxlength="30" placeholder="Ex.: Bênção"></label>
  <label class="campo"><span>Dura quantos turnos dele (0 = até o mestre tirar)</span><input id="gb-t" type="number" inputmode="numeric" min="0" value="1"></label>
  <label class="campo"><span>O que faz</span><input id="gb-d" maxlength="120" placeholder="Ex.: +2 de acerto"></label>`,
  `<button class="botao leve" data-a="fechar">Cancelar</button><button class="botao prim" data-a="g-buff-ok" data-n="${esc(el.dataset.n)}">Enviar</button>`);
A["g-buff-ok"] = (el) => { const n = $("#gb-n").value.trim(); if (!n) { $("#gb-n").focus(); return; } const m = { acao: "propor", tipo: "buff", para: el.dataset.n, nome: n, turnos: int($("#gb-t").value), desc: $("#gb-d").value }; fecharFolha(); ga(m); };
A["g-item"] = (el) => {
  if (precisaFicha()) return;
  const itens = S.inventario.map((it, i) => ({ it, i })).filter((x) => (x.it.item || "").trim());
  folha(`Dar item a ${el.dataset.n}`, itens.length ? `<div class="lista">${itens.map((x) => `<div class="item" data-a="g-item-q" data-i="${x.i}" data-n="${esc(el.dataset.n)}"><div class="tx"><b>${esc(x.it.item)}</b><small>você tem ${Math.max(1, int(x.it.qtd, 1))}</small></div><span class="sub">›</span></div>`).join("")}</div>` : `<div class="vazio-msg">Sua bolsa está vazia.</div>`);
};
A["g-item-q"] = (el) => {
  const it = S.inventario[int(el.dataset.i)], tem = Math.max(1, int(it.qtd, 1));
  folha(`${it.item} → ${el.dataset.n}`, `<label class="campo"><span>Quantos (você tem ${tem})</span><input id="gi-q" type="number" inputmode="numeric" min="1" max="${tem}" value="1"></label>`,
    `<button class="botao leve" data-a="fechar">Cancelar</button><button class="botao prim" data-a="g-item-ok" data-i="${el.dataset.i}" data-n="${esc(el.dataset.n)}">Oferecer</button>`);
};
A["g-item-ok"] = (el) => {
  const it = S.inventario[int(el.dataset.i)], q = Math.max(1, Math.min(Math.max(1, int(it.qtd, 1)), int($("#gi-q").value, 1)));
  fecharFolha(); ga({ acao: "propor", tipo: "item", para: el.dataset.n, item: { item: it.item, carga: String(it.carga || ""), qtd: q } });
};
A["g-dinheiro"] = (el) => { if (precisaFicha()) return; folha(`Dinheiro para ${el.dataset.n}`, `<label class="campo"><span>Quanto (você tem ${esc(R.formatarDinheiro(dinheiroMeu()))})</span><input id="gd-v" placeholder="Ex.: 35 prata"></label>`,
  `<button class="botao leve" data-a="fechar">Cancelar</button><button class="botao prim" data-a="g-dinheiro-ok" data-n="${esc(el.dataset.n)}">Oferecer</button>`); };
A["g-dinheiro-ok"] = (el) => {
  const v = R.lerDinheiro($("#gd-v").value);
  if (!v || v < 1) { toast("Não entendi o valor. Ex.: 35 prata."); return; }
  if (v > dinheiroMeu()) { toast(`Você só tem ${esc(R.formatarDinheiro(dinheiroMeu()))}.`); return; }
  fecharFolha(); ga({ acao: "propor", tipo: "dinheiro", para: el.dataset.n, contos: v });
};
A["g-sussurro"] = (el) => folha(`Sussurrar para ${el.dataset.n}`, `<label class="campo"><span>Mensagem</span><textarea id="gs-t" rows="3" maxlength="300"></textarea></label>`,
  `<button class="botao leve" data-a="fechar">Cancelar</button><button class="botao prim" data-a="g-sussurro-ok" data-n="${esc(el.dataset.n)}">Enviar</button>`);
A["g-sussurro-ok"] = (el) => { const t = $("#gs-t").value.trim(); if (!t) return; fecharFolha(); ga({ acao: "sussurro", para: el.dataset.n, texto: t }); };
A["g-vinculo"] = (el) => { const m = sessao.grupo.membros.find((x) => x.nome === el.dataset.n) || {};
  folha(`Vínculo com ${el.dataset.n}`, `<label class="campo"><span>O que liga vocês dois (os dois veem)</span><textarea id="gv-t" rows="3" maxlength="200">${esc(m.vinculo || "")}</textarea></label>`,
    `<button class="botao leve" data-a="fechar">Cancelar</button><button class="botao prim" data-a="g-vinculo-ok" data-n="${esc(el.dataset.n)}">Salvar</button>`); };
A["g-vinculo-ok"] = (el) => { const t = $("#gv-t").value; fecharFolha(); ga({ acao: "vinculo", com: el.dataset.n, texto: t }, "Vínculo anotado."); };
A["g-sinal"] = () => { const eu = sessao.grupo.membros.find((m) => m.eu) || {};
  folha("Sinal e intenção", `<div class="chips">${SINAIS.map((s) => `<button class="chip-acao" data-a="g-sinal-p" data-s="${esc(s)}">${esc(s)}</button>`).join("")}</div>
    <label class="campo"><span>Sinal para o grupo</span><input id="gn-s" maxlength="40" value="${esc(eu.sinal || "")}"></label>
    <label class="campo"><span>O que pretendo fazer no meu turno</span><input id="gn-i" maxlength="80" value="${esc(eu.intencao || "")}"></label>
    <p class="sub">Some sozinho quando o seu turno termina.</p>`,
    `<button class="botao leve" data-a="g-sinal-ok" data-limpar="1">Limpar</button><button class="botao prim" data-a="g-sinal-ok">Mostrar</button>`); };
A["g-sinal-p"] = (el) => { $("#gn-s").value = el.dataset.s; };
A["g-sinal-ok"] = (el) => { const m = el.dataset.limpar ? { sinal: "", intencao: "" } : { sinal: $("#gn-s").value, intencao: $("#gn-i").value }; fecharFolha(); ga(Object.assign({ acao: "sinal" }, m)); };
A["g-caixa"] = () => folha("Caixa do grupo", `<p class="sub">A caixa tem ${esc(sessao.grupo.caixa.txt)}. Você tem ${esc(R.formatarDinheiro(dinheiroMeu()))}.</p>
  <label class="campo"><span>Valor</span><input id="gx-v" placeholder="Ex.: 2 ouro"></label>${sessao.grupo.caixa.log.length ? `<p class="sub">${sessao.grupo.caixa.log.map(esc).join("<br>")}</p>` : ""}`,
  `<button class="botao leve" data-a="g-caixa-ok" data-s="-1">Tirar</button><button class="botao prim" data-a="g-caixa-ok" data-s="1">Pôr</button>`);
A["g-caixa-ok"] = (el) => {
  if (precisaFicha()) return;
  const v = R.lerDinheiro($("#gx-v").value), s = int(el.dataset.s);
  if (!v || v < 1) { toast("Não entendi o valor. Ex.: 2 ouro."); return; }
  if (s > 0 && v > dinheiroMeu()) { toast(`Você só tem ${esc(R.formatarDinheiro(dinheiroMeu()))}.`); return; }
  fecharFolha(); ga({ acao: "caixa", delta: s * v });
};
A["g-nota"] = () => folha("Diário do grupo", `<label class="campo"><span>Nota (todos do grupo leem)</span><textarea id="gt-t" rows="4" maxlength="400"></textarea></label>`,
  `<button class="botao leve" data-a="fechar">Cancelar</button><button class="botao prim" data-a="g-nota-ok">Anotar</button>`);
A["g-nota-ok"] = () => { const t = $("#gt-t").value.trim(); if (!t) return; fecharFolha(); ga({ acao: "nota_add", texto: t }); };
A["g-nota-del"] = (el) => ga({ acao: "nota_del", num: int(el.dataset.id) });
A["g-refeicao"] = () => {
  if (precisaFicha()) return;
  const [b, d] = bonusPericia("Gastronomia"), outros = sessao.grupo.membros.filter((m) => !m.eu);
  folha("Cozinhar para o grupo", `<label class="campo"><span>Nível da refeição</span><select id="gr-n">${[1, 2, 3, 4].map((n) => `<option value="${n}">Nível ${n} — DT ${R.REFEICOES[n][0]}</option>`).join("")}</select></label>
    <p class="sub" id="gr-b">${esc(R.REFEICOES[1][1])}</p>
    <div class="lista"><label class="item"><input type="checkbox" class="gr-q" value="" checked style="width:22px;height:22px;margin-right:10px"><div class="tx"><b>Você</b></div></label>
    ${outros.map((m) => `<label class="item"><input type="checkbox" class="gr-q" value="${esc(m.nome)}" checked style="width:22px;height:22px;margin-right:10px"><div class="tx"><b>${esc(m.nome)}</b></div></label>`).join("")}</div>
    <p class="sub">Seu teste de Gastronomia: ${d}d20 +${b}. O nível depende dos ingredientes; combine com o mestre. O benefício dura até o próximo descanso longo.</p>`,
    `<button class="botao leve" data-a="fechar">Cancelar</button><button class="botao prim" data-a="g-refeicao-ok">🎲 Cozinhar</button>`,
    (c) => $("#gr-n", c).addEventListener("change", (e) => { $("#gr-b", c).textContent = R.REFEICOES[e.target.value][1]; }));
};
A["g-refeicao-ok"] = () => {
  const nivel = int($("#gr-n").value, 1), marc = [...document.querySelectorAll(".gr-q:checked")].map((x) => x.value), r = rolarPericiaNome("Gastronomia");
  fecharFolha();
  registrarDiario({ titulo: `🍲 Refeição de nível ${nivel}`, linhas: [esc(r.txt), r.total >= R.REFEICOES[nivel][0] ? "Deu certo." : `Falhou (DT ${R.REFEICOES[nivel][0]}).`] });
  ga({ acao: "propor", tipo: "refeicao", nivel, total: r.total, txt: r.txt, eu: marc.includes(""), alvos: marc.filter(Boolean) });
};
// eventos do grupo que chegam pelo mestre
function eventoGrupo(ev, hora) {
  if (ev.tipo === "aviso") {
    registrarDiario({ titulo: "👥 Grupo", linhas: [esc(ev.texto)], hora });
    return `👥 ${esc(ev.texto)}`;
  } else if (ev.tipo === "pedido") {
    vibrar([120, 60, 120]);
    return banco.autoAjuda ? "" : `👥 <b>${esc(ev.de)}</b> quer te dar: ${esc(ev.texto)} <button class="botao leve" data-a="aba" data-aba="grupo" style="min-height:32px;padding:4px 10px">Ver</button>`;
  } else if (ev.tipo === "portao" && S) {
    const i = S.portao.Sucessos.indexOf(false);
    if (i >= 0) S.portao.Sucessos[i] = true;
    const n = S.portao.Sucessos.filter(Boolean).length;
    salvar(); render(); vibrar(200);
    const txt = `Medicina de ${esc(ev.de)}: +1 sucesso no Portão da Morte (${n}/5).${n >= 5 ? " Você volta com 1 de Vida e uma cicatriz." : ""}`;
    registrarDiario({ titulo: "✚ Portão da Morte", linhas: [txt], hora });
    relatar(`Portão da Morte: ${n} sucesso(s) (Medicina de ${ev.de})`);
    return `✚ ${txt}`;
  } else if (ev.tipo === "dinheiro" && S) {
    const d = int(ev.delta), antes = dinheiroMeu();
    S.dinheiro_c = Math.max(0, antes + d); S.dinheiro_nota = "";
    salvar(); render();
    const txt = `${d >= 0 ? "Recebeu" : "Entregou"} ${esc(R.formatarDinheiro(Math.abs(d)))}${ev.desc ? " — " + esc(ev.desc) : ""}. Agora: ${esc(R.formatarDinheiro(S.dinheiro_c))}.`;
    registrarDiario({ titulo: "🪙 Dinheiro", linhas: [txt], hora });
    return `🪙 ${txt}`;
  } else if (ev.tipo === "sussurro") {
    vibrar([80, 60, 80]);
    registrarDiario({ titulo: `🤫 Sussurro de ${esc(ev.de)}`, linhas: [esc(ev.texto)], hora });
    return `🤫 <b>${esc(ev.de)}</b>: ${esc(ev.texto)}<hr>`;
  } else if (ev.tipo === "teste") {
    vibrar([200, 80, 200]);
    return `🎲 O mestre pediu <b>${esc(ev.pericia)}</b>${ev.dt ? ` (DT ${int(ev.dt)})` : ""} de todos. <button class="botao leve" data-a="aba" data-aba="grupo" style="min-height:32px;padding:4px 10px">Rolar</button>`;
  }
  return null;
}
