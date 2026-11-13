// ------------------------------------------------------------------ sessão do mestre (quando o PC do mestre serve esta página)
const sessao = { ativa: false, id: "", mao: false, rodada: 0, efeitos: [], conectado: false, ultimo: "", timer: null, falhas: 0, vez: "", turno: 0, meusTurnos: 0, ackEv: 0, token: "" };
const durEfeito = (e) => e.rodadas ? `${e.rodadas} turno(s)` : e.fim_combate ? "até o fim do combate" : "até o mestre remover";
const CH_SESSAO = "prevalecentes.sessao.id", CH_ACK = "prevalecentes.sessao.ack";
async function api(url, corpo) {
  const r = await fetch(url, corpo === undefined ? { cache: "no-store" } : { method: "POST", body: JSON.stringify(corpo) });
  if (!r.ok) throw new Error(r.status);
  return r.json();
}
async function detectarSessao() {
  if (!/^https?:$/.test(location.protocol) || location.protocol === "https:") return;
  try {
    const r = await api("/api/sessao");
    if (!r || !r.sessao) return;
  } catch (e) { return; }
  sessao.ativa = true;
  try {
    sessao.id = localStorage.getItem(CH_SESSAO) || "";
    const [tk, n] = JSON.parse(localStorage.getItem(CH_ACK) || "[]");   // recarregou a página: não repete o que já aplicou
    if (tk) { sessao.token = tk; sessao.ackEv = int(n); }
  } catch (e) { /* sem storage */ }
  if (sessao.id) entrarSessao(sessao.id); else if (!window.__fichaChegou) pedirNomeSessao();
  pintarSessao();
}
function pedirNomeSessao() {
  const sug = S ? (S.identidade.player || S.identidade.nome || "") : "";
  folha("Entrar na mesa", `<p class="sub">Esta página veio do PC do mestre. Com uma ficha aberta, o mestre vê sua Vida, Mana e Vigor e pode mandar dano e condições.</p>
    <label class="campo"><span>Seu nome na mesa</span><input id="ss-n" value="${esc(sessao.id || sug)}" maxlength="30"></label>`,
  `<button class="botao leve" data-a="fechar">Agora não</button><button class="botao prim" data-a="sessao-ok">Entrar</button>`);
}
A["sessao-nome"] = () => pedirNomeSessao();
A["sessao-ok"] = () => { const n = $("#ss-n").value.trim(); if (!n) { $("#ss-n").focus(); return; } fecharFolha(); entrarSessao(n, true); };
async function entrarSessao(nome, novo = false) {
  try {
    if (novo && sessao.id && sessao.id !== nome) sessao.id = "";
    sessao.id = await api("/api/oi", { nome, id: novo ? "" : sessao.id }).then((r) => r.id);
    try { localStorage.setItem(CH_SESSAO, sessao.id); } catch (e) { /* sem storage */ }
    sessao.conectado = true; sessao.ultimo = "";
    if (novo) toast(`Na mesa como <b>${esc(sessao.id)}</b>.`);
  } catch (e) { sessao.conectado = false; toast("Não consegui falar com o mestre. Você está na mesma rede?"); }
  clearInterval(sessao.timer); sessao.timer = setInterval(consultarSessao, 1500);
  consultarSessao(); pintarSessao();
}
function resumoSessao() {
  if (!S) return null;
  const c = calcular(), d = c.d, at = (ch, max) => (S.vida[ch] === "" || S.vida[ch] == null ? max : int(S.vida[ch], max));
  return { personagem: S.identidade.nome || "", especie: S.identidade.especie || "", nivel: c.nv,
    vida: at("atual", d.vida), vida_max: d.vida, mana: at("mana_atual", d.mana), mana_max: d.mana, vigor: at("vigor_atual", d.vigor), vigor_max: d.vigor,
    ca: d.ca, movimento: c.mov, iniciativa: d.iniciativa_bonus,
    portao: [S.portao.Sucessos.filter(Boolean).length, S.portao.Falhas.filter(Boolean).length],
    condicoes: R.CONDICOES.map((n) => [n, int((S.condicoes[n] || {}).atual), condMax(n)]),
    iniciativa_dados: d.iniciativa_dados, rd: d.rd, resistencias: d.resistencias,
    defesas: Object.fromEntries(R.PERICIAS_DEFESA.map(([n, k, tn]) => [n, [d.bc[k] + d.n3 + (c.tal.has(tn) ? 2 : 0), R.vantagem(c.a[k])]])),
    inventario: S.inventario.map((i) => ({ item: i.item || "", carga: String(i.carga || ""), qtd: Math.max(1, int(i.qtd, 1)) })),
    dinheiro: R.formatarDinheiro(S.dinheiro_c), carga: [Math.round(c.carga * 10) / 10, d.carga],
    sem_alma: !!S.sem_alma };
}
async function consultarSessao() {
  if (!sessao.id) return;
  let r;
  try { r = await api("/api/estado?id=" + encodeURIComponent(sessao.id) + "&ack=" + sessao.ackEv); }
  catch (e) { if (sessao.conectado) { sessao.conectado = false; pintarSessao(); } return; }
  if (!r.ok) { entrarSessao(sessao.id); return; }   // o mestre reiniciou: entra de novo com o mesmo nome
  const mudou = !sessao.conectado || sessao.mao !== r.mao || sessao.rodada !== r.rodada || sessao.vez !== (r.vez || "") || JSON.stringify(sessao.efeitos) !== JSON.stringify(r.efeitos || []);
  sessao.conectado = true; sessao.mao = r.mao; sessao.rodada = r.rodada; sessao.vez = r.vez || ""; sessao.turno = r.turno || 0;
  sessao.efeitos = r.efeitos || [];
  if (r.token && r.token !== sessao.token) { sessao.token = r.token; sessao.ackEv = 0; }   // o mestre reiniciou: a contagem recomeça
  // O mestre repete o evento até receber o ack, então ignora o que já foi processado (dano nunca vale duas vezes).
  const novos = (r.eventos || []).filter((e) => !(e.seq <= sessao.ackEv));
  const avisos = novos.map(receberEvento).filter(Boolean);
  novos.forEach((e) => { sessao.ackEv = Math.max(sessao.ackEv, e.seq || 0); });
  if (novos.length) { try { localStorage.setItem(CH_ACK, JSON.stringify([sessao.token, sessao.ackEv])); } catch (e) { /* sem storage */ } }
  if (r.palavra) { avisos.push("🎤 <b>O mestre te deu a palavra!</b>"); vibrar([300, 120, 300]); }
  if (avisos.length) toast(avisos.join("<hr>"));
  if (mudou) { if (S && (aba === "combate")) render(); else pintarSessao(); }
  const res = resumoSessao(), txt = JSON.stringify(res);
  if (res && txt !== sessao.ultimo) {
    try { await api("/api/ficha", { id: sessao.id, dados: res }); sessao.ultimo = txt; } catch (e) { /* tenta na próxima */ }
  }
}
const vibrar = (p) => { try { if (navigator.vibrate) navigator.vibrate(p); } catch (e) { /* sem vibração */ } };
function receberEvento(ev) {
  const hora = new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
  if (ev.tipo === "dano") {
    const valor = int(ev.valor), desc = String(ev.desc || "");
    const oque = valor < 0 ? `Cura de ${-valor}` : `${valor} de dano${ev.dano_tipo ? ` (${esc(ev.dano_tipo)})` : ""}`;
    let linha = "";
    if (S) {
      const c = calcular(), max = c.d.vida, antes = S.vida.atual === "" || S.vida.atual == null ? max : int(S.vida.atual, max);
      const nomes = new Set(sessao.efeitos.map((e) => e.nome));
      const [final, notas] = valor > 0 ? R.defesasContraDano(valor, ev.dano_tipo || "", c.d, rng, nomes.has("Fragilizado"), nomes.has("Loucura")) : [valor, []];
      const depois = Math.max(0, Math.min(max, antes - final));
      S.vida.atual = String(depois); salvar(); render();
      linha = (valor > 0 && notas.length ? `Recebeu <b>${final}</b> <span class="sub">(${esc(notas.join("; "))})</span><br>` : "")
        + `Vida: ${antes} → <b>${depois}</b>${depois === 0 && antes > 0 ? ` — <b class="erro">INCAPAZ</b>: role o Portão da Morte no início do turno.${final > Math.floor(max / 2) ? " Dano maior que metade da Vida: 1 falha automática." : ""}` : ""}`;
      relatar(valor > 0 && notas.length ? `recebeu ${final} de ${valor} (${notas.join("; ")}), Vida ${depois}/${max}` : `Vida ${depois}/${max}${depois === 0 && antes > 0 ? " — INCAPAZ" : ""}`);
    }
    registrarDiario({ titulo: "📣 Do mestre", linhas: [oque + (desc ? " — " + esc(desc) : ""), linha].filter(Boolean), hora });
    vibrar(valor < 0 ? 120 : [200, 80, 200]);
    return `📣 <b>${oque}</b>${desc ? " — " + esc(desc) : ""}${linha ? "<br>" + linha : ""}`;
  } else if (ev.tipo === "cond_pontos" && S) {
    return condicaoDoMestre(ev, hora);
  } else if (ev.tipo === "item" && S) {
    return itemDoMestre(ev, hora);
  } else if (ev.tipo === "combate" && S) {
    novoCombate(true); render();
    return ev.fase === "inicio" ? "⚔ <b>Começou o combate!</b> Ações e usos por combate renovados." : "🕊 <b>Fim do combate.</b> Usos por combate renovados. <button class=\"botao leve\" data-a=\"levar-app\" style=\"min-height:32px;padding:4px 10px\">📲 Levar ficha ao app</button>";
  } else if (ev.tipo === "vez") {
    sessao.meusTurnos += 1;
    if (S) novoTurno(true);
    for (const dg of Object.values(S ? S.desgaste : {})) if (dg.desgastada && sessao.meusTurnos >= (dg.em || 0) + 2) Object.assign(dg, { usados: 0, desgastada: false, contado: -1 });
    if (S) { salvar(); render(); }
    vibrar([150, 80, 150, 80, 300]);
    return "⚔ <b>É a sua vez!</b>";
  } else if (ev.tipo === "condicao") {
    const dur = durEfeito(ev);
    registrarDiario({ titulo: "📣 Condição", linhas: [`${esc(ev.nome)} (${dur})${ev.desc ? " — " + esc(ev.desc) : ""}`], hora });
    vibrar(200);
    return `⏳ <b>${esc(ev.nome)}</b> (${dur})${ev.desc ? " — " + esc(ev.desc) : ""}`;
  } else if (ev.tipo === "fim") {
    return `Terminou: <b>${esc(ev.nome)}</b>`;
  }
  return "";
}
function relatar(texto, ativou) {
  if (!sessao.id || !texto) return;
  api("/api/relato", { id: sessao.id, texto, ativou: ativou || null }).catch(() => { /* o mestre vê a ficha de qualquer jeito */ });
}
function condicaoDoMestre(ev, hora) {
  const cond = ev.condicao, c = S.condicoes[cond]; if (!c) return "";
  const C2 = calcular(), defesa = R.CONDICAO_TESTE[cond] || "Fortitude";
  const [, k, tn] = R.PERICIAS_DEFESA.find((x) => x[0] === defesa);
  const bonus = C2.d.bc[k] + C2.d.n3 + (C2.tal.has(tn) ? 2 : 0);
  const autoFalha = defesa === "Vontade" && sessao.efeitos.some((e) => e.nome === "Loucura");
  const t = R.rolarDefesa(bonus, R.vantagem(C2.a[k]), rng), suc = !autoFalha && t.total >= int(ev.dt);
  const mx = condMax(cond), antes = int(c.atual), [rec, novo, ativou] = R.receberCondicao(antes, mx, int(ev.pontos), suc);
  c.atual = novo ? String(novo) : "";
  const teste = `${defesa} ${t.total} [d20 ${t.d20.join(", ")} +${bonus}] contra DT ${int(ev.dt)}: ${autoFalha ? "falha automática (Loucura)" : suc ? "SUCESSO, metade" : "falhou"}`;
  const linhas = [`${int(ev.pontos)} de ${esc(cond)}${ev.desc ? " — " + esc(ev.desc) : ""}`, teste, `${cond}: ${antes} → ${Math.min(antes + rec, mx)}/${mx} (+${rec})`];
  let relato = `${teste}; ${cond} +${rec} → ${Math.min(antes + rec, mx)}/${mx}`;
  if (ativou) {
    const info = R.CONDICAO_ATIVA[cond];
    linhas.push(`<b class="erro">⚠ ${cond.toUpperCase()} ATIVOU</b>: ${esc(info.desc)} A barra volta a zero.`);
    relato += ` — ${cond.toUpperCase()} ATIVOU`;
    if (info.pct_ja) {
      const perda = Math.max(1, Math.floor(C2.d.vida * info.pct_ja / 100)), vida = S.vida.atual === "" || S.vida.atual == null ? C2.d.vida : int(S.vida.atual, C2.d.vida);
      S.vida.atual = String(Math.max(0, vida - perda)); linhas.push(`Vida: ${vida} → ${Math.max(0, vida - perda)} (−${perda})`); relato += `, perdeu ${perda} de Vida`;
    }
    vibrar([300, 100, 300, 100, 300]);
  } else vibrar(200);
  salvar(); render();
  registrarDiario({ titulo: `📣 ${cond}`, linhas, hora });
  relatar(relato, ativou ? cond : null);
  return `📣 ${linhas.join("<br>")}`;
}
function itemDoMestre(ev, hora) {
  let txt;
  if (ev.acao === "dar") {
    const it = ev.item || {}, nome = String(it.item || "").slice(0, 40), q = Math.max(1, int(it.qtd, 1));
    const ja = S.inventario.find((x) => String(x.item || "").trim().toLowerCase() === nome.toLowerCase());
    if (ja) ja.qtd = String(Math.max(1, int(ja.qtd, 1)) + q); else S.inventario.push({ item: nome, carga: String(it.carga || ""), qtd: String(q) });
    txt = `🎒 Recebeu <b>${q}× ${esc(nome)}</b>${ev.desc ? " — " + esc(ev.desc) : ""}`;
  } else {
    const nome = String(ev.nome || ""), q = Math.max(1, int(ev.qtd, 1));
    const i = S.inventario.findIndex((x) => String(x.item || "").trim().toLowerCase() === nome.toLowerCase());
    if (i < 0) return `O mestre tirou ${esc(nome)}, mas o item não está mais na bolsa.`;
    const resto = Math.max(1, int(S.inventario[i].qtd, 1)) - q;
    if (resto > 0) S.inventario[i].qtd = String(resto); else S.inventario.splice(i, 1);
    txt = `🎒 O mestre tirou <b>${q}× ${esc(nome)}</b>${ev.desc ? " — " + esc(ev.desc) : ""}`;
  }
  salvar(); render(); vibrar(120);
  registrarDiario({ titulo: "📣 Bolsa", linhas: [txt], hora });
  return txt;
}
A["sessao-mao"] = async () => {
  if (!sessao.id) { pedirNomeSessao(); return; }
  try { await api(sessao.mao ? "/api/abaixar" : "/api/mao", { id: sessao.id }); sessao.mao = !sessao.mao; pintarSessao(); consultarSessao(); }
  catch (e) { toast("Sem conexão com o mestre…"); }
};
A["sessao-efeitos"] = () => folha(`Mesa · Rodada ${sessao.rodada}`, sessao.efeitos.length
  ? `<div class="lista">${sessao.efeitos.map((e) => `<div class="item"><span class="marca">⏳</span><div class="tx"><b>${esc(e.nome)}</b><small>${durEfeito(e)}${e.desc ? " · " + esc(e.desc) : ""}</small></div></div>`).join("")}</div>`
  : `<div class="vazio-msg">Nenhum efeito do mestre em você.</div>`, `<button class="botao leve" data-a="sessao-nome">Trocar nome</button><button class="botao prim" data-a="fechar">OK</button>`);
function pintarSessao() {
  const b = $("#mesa");
  if (!b) return;
  b.classList.toggle("oculto", !sessao.ativa);
  document.body.classList.toggle("com-mesa", sessao.ativa);
  if (!sessao.ativa) return;
  const ef = sessao.efeitos.length ? ` · ⏳ ${sessao.efeitos.map((e) => esc(e.nome)).join(", ")}` : "";
  const minha = sessao.vez && sessao.vez === sessao.id;
  b.classList.toggle("vez", !!minha);
  b.innerHTML = `<button class="info" data-a="sessao-efeitos"><b>${sessao.conectado ? (minha ? "⚔ SUA VEZ" : "🛡 Mesa") : "⚠ Sem sinal"}</b> · Rodada ${sessao.rodada}${sessao.vez && !minha ? ` · vez de ${esc(sessao.vez)}` : ""}${ef}${S ? "" : " · abra uma ficha"}</button>
    <button class="mao ${sessao.mao ? "on" : ""}" data-a="sessao-mao">✋ ${sessao.mao ? "Abaixar" : "Mão"}</button>`;
}

