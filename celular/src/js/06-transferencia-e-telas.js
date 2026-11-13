// ------------------------------------------------------------------ levar a ficha do app (https) para a mesa do mestre (http)
// Um site https não pode falar com http://IP (o navegador bloqueia), mas pode ABRIR o endereço. A ficha vai no
// "#f=" do endereço (só o navegador vê, nada passa por servidor) e a página do mestre a guarda como ficha sua.
const PAGINA_APP = "https://grnguidi.github.io/FichaPreval/";
const b64u = (u8) => { let s = ""; for (const b of u8) s += String.fromCharCode(b); return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, ""); };
const deB64u = (t) => { const s = atob(t.replace(/-/g, "+").replace(/_/g, "/")); return Uint8Array.from(s, (c) => c.charCodeAt(0)); };
async function viaStream(bytes, Cls, modo) {
  const st = new Blob([bytes]).stream().pipeThrough(new Cls(modo));
  return new Uint8Array(await new Response(st).arrayBuffer());
}
async function empacotarFicha(ficha) {
  const copia = Object.assign({}, ficha); delete copia._salvo;
  const bytes = new TextEncoder().encode(JSON.stringify(copia));
  if (typeof CompressionStream === "function") return "z" + b64u(await viaStream(bytes, CompressionStream, "deflate-raw"));
  return "j" + b64u(bytes);
}
async function desempacotarFicha(txt) {
  let bytes = deB64u(txt.slice(1));
  if (txt[0] === "z") bytes = await viaStream(bytes, DecompressionStream, "deflate-raw");
  return JSON.parse(new TextDecoder().decode(bytes));
}
let mesaAlvo = "";   // endereço da mesa (http://IP:5760) quando a página foi aberta pelo QR/botão do mestre
const mesaValida = (u) => /^http:\/\/[\w.\-]+(:\d{1,5})?$/.test(u);
function lerHash() {
  const h = new URLSearchParams(location.hash.slice(1));
  if (h.get("mesa") && mesaValida(h.get("mesa"))) mesaAlvo = h.get("mesa");
  return h.get("f") || "";
}
async function receberFichaDaUrl(txt) {
  try {
    const s = normalizar(await desempacotarFicha(txt));
    if (!s.identidade) throw new Error();
    const nome = (s.identidade.nome || "").trim();
    let id = nome && Object.keys(banco.fichas).find((k) => (banco.fichas[k].identidade.nome || "").trim() === nome);
    const atualizou = !!id;
    if (!id) id = "ficha-" + Date.now().toString(36);
    banco.fichas[id] = s; banco.atual = id; banco.modo = "jogo"; gravarLocal();
    S = normalizar(s);
    try { history.replaceState(null, "", location.pathname); } catch (e) { /* sem history */ }
    return { nome: nome || "sem nome", atualizou };
  } catch (e) { return null; }
}
async function enviarParaMesa(id, alvo) {
  alvo = alvo || mesaAlvo;
  if (!alvo || !mesaValida(alvo)) { toast("Endereço da mesa inválido. Use o formato http://192.168.0.10:5760"); return; }
  try {
    const t = await empacotarFicha(banco.fichas[id]);
    toast("Abrindo a mesa do mestre…");
    location.href = alvo + "/#f=" + t;
  } catch (e) { toast("Não consegui preparar a ficha para enviar."); }
}
A["enviar-mesa"] = (el) => enviarParaMesa(el.dataset.id);
A["mesa-endereco"] = () => folha("Entrar na mesa", `<p class="sub">Digite o endereço que aparece na tela do mestre (ou aponte a câmera para o QR code). Depois toque na ficha que vai jogar.</p>
  <label class="campo"><span>Endereço da mesa</span><input id="m-end" inputmode="url" placeholder="http://192.168.0.10:5760" value="${esc(mesaAlvo || localStorage.getItem("prevalecentes.mesa.alvo") || "")}"></label>`,
  `<button class="botao leve" data-a="fechar">Cancelar</button><button class="botao prim" data-a="mesa-endereco-ok">Usar</button>`);
A["mesa-endereco-ok"] = () => {
  let u = $("#m-end").value.trim().replace(/\/+$/, "");
  if (u && !/^https?:\/\//.test(u)) u = "http://" + u;
  if (u && !/:\d+$/.test(u)) u += ":5760";
  if (!mesaValida(u)) { toast("Endereço inválido."); return; }
  mesaAlvo = u; try { localStorage.setItem("prevalecentes.mesa.alvo", u); } catch (e) { /* sem storage */ }
  fecharFolha(); render();
};
// iPhone: o app da Tela de Início e o Safari guardam fichas em lugares separados, e o link de "voltar ao app" abre no Safari.
const iosNaTela = () => { try { return /iP(hone|ad|od)/.test(navigator.userAgent) && navigator.standalone === true; } catch (e) { return false; } };
const avisoIos = () => {
  let visto = false; try { visto = localStorage.getItem("prevalecentes.ios.aviso") === "1"; } catch (e) { /* sem storage */ }
  if (!iosNaTela() || visto) return "";
  return `<div class="item" style="border-color:var(--ouro,#b8860b);display:block"><div class="tx"><b>📱 iPhone: guarde uma cópia</b>
    <small>No iPhone, este app e o Safari guardam as fichas separadas, e o iOS pode apagar dados de sites. O botão “Levar de volta ao app” da mesa abre o Safari, não este app.
    Para não perder nada, faça um backup de vez em quando (ou use o app direto pelo Safari).</small></div>
    <div class="linhabts" style="margin-top:8px"><button class="botao prim" data-a="backup-todas">⬇ Backup de todas as fichas</button><button class="botao leve" data-a="aviso-ios-ok">Entendi</button></div></div>`;
};
A["aviso-ios-ok"] = () => { try { localStorage.setItem("prevalecentes.ios.aviso", "1"); } catch (e) { /* sem storage */ } render(); };
A["backup-todas"] = async () => {
  const fichas = {}; for (const [id, f] of Object.entries(banco.fichas)) { const c = Object.assign({}, f); delete c._salvo; fichas[id] = c; }
  if (!Object.keys(fichas).length) { toast("Nenhuma ficha para guardar."); return; }
  const texto = JSON.stringify({ prevalecentes_backup: 1, em: new Date().toISOString(), fichas });
  const nome = "prevalecentes-backup-" + new Date().toISOString().slice(0, 10) + ".json";
  try {
    const arq = new File([texto], nome, { type: "application/json" });
    if (navigator.canShare && navigator.canShare({ files: [arq] })) { await navigator.share({ files: [arq], title: nome }); return; }   // iPhone: abre "Salvar em Arquivos"
  } catch (e) { if (e && e.name === "AbortError") return; /* cai para o download comum */ }
  try {
    const url = URL.createObjectURL(new Blob([texto], { type: "application/json" }));
    const a = document.createElement("a"); a.href = url; a.download = nome; document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 4000); toast(`Backup salvo: ${esc(nome)}`);
  } catch (e) { toast("Não consegui salvar o backup neste navegador."); }
};
A["levar-app"] = async () => {
  if (!S || !banco.atual) { toast("Abra a ficha que quer levar de volta ao app."); return; }
  salvar();
  try {
    const t = await empacotarFicha(banco.fichas[banco.atual] || S);
    toast("Abrindo o app com a sua ficha…");
    location.href = PAGINA_APP + "#f=" + t;
  } catch (e) { toast("Não consegui preparar a ficha."); }
};
A["trazer-ficha"] = () => { location.href = PAGINA_APP + "#mesa=" + encodeURIComponent(location.origin); };

function telaInicial() {
  const ids = Object.keys(banco.fichas);
  return `<div class="capa"><div class="orn">❦</div><h1>Prevalecentes</h1><p class="sub">Ficha de mesa · edição 3.1</p></div>
    ${avisoIos()}
    ${secao("Suas fichas")}
    ${ids.length ? `<div class="lista">${ids.map((id) => { const f = banco.fichas[id]; return `<div class="item" data-a="abrir" data-id="${id}"><div class="tx"><b>${esc(f.identidade.nome || "Sem nome")}</b><small>Nível ${f.identidade.nivel} · ${esc(f.identidade.especie || "—")}${f.sem_alma ? " · sem alma" : ""}</small></div>${mesaAlvo && !sessao.ativa ? `<button class="botao prim" data-a="enviar-mesa" data-id="${id}" style="min-height:36px">Enviar</button>` : `<span class="sub">›</span>`}</div>`; }).join("")}</div>`
      : `<div class="vazio-msg">Nenhuma ficha neste aparelho ainda.</div>`}
    ${mesaAlvo && !sessao.ativa ? `<div class="item" style="border-color:var(--ouro,#b8860b)"><div class="tx"><b>🛡 Mesa do mestre</b><small>${esc(mesaAlvo)} · toque em “Enviar” na ficha que vai jogar</small></div></div>` : ""}
    <div class="linhabts"><button class="botao prim" data-a="nova">✦ Nova ficha</button><button class="botao leve" data-a="importar">Abrir arquivo .json</button></div>
    ${sessao.ativa ? `<div class="linhabts"><button class="botao prim" data-a="trazer-ficha">📲 Trazer minha ficha do app</button></div><p class="sub">Atualizou a ficha em casa no app instalado? Toque acima: ela vem para esta mesa já atualizada.</p>` : `<div class="linhabts"><button class="botao leve" data-a="mesa-endereco">🛡 Entrar na mesa do mestre</button></div>`}
    <p class="sub" style="margin-top:14px">Abra aqui o mesmo arquivo .json do programa de PC. As fichas ficam guardadas neste aparelho; use “Exportar” no menu para levar de volta ao PC.</p>`;
}

function pFicha() {
  const d = C.d, v = S.vida;
  const vital = (nome, cor, chave, max) => {
    const atual = v[chave] === "" || v[chave] == null ? max : int(v[chave], max);
    const pct = Math.max(0, Math.min(100, (atual / Math.max(1, max)) * 100));
    return `<div class="cartao vital"><div class="rot" style="background:${cor}">${nome}</div>
      <div class="val" data-a="editar-vital" data-chave="${chave}" data-max="${max}"><b>${atual}</b> <small>/ ${max}${(chave === "atual" && S.manual.vida != null) || (chave === "mana_atual" && S.manual.mana != null) ? " ✎" : ""}</small><div class="barra"><i style="width:${pct}%;background:${cor}"></i></div></div>
      <div class="passos"><button data-a="vital" data-chave="${chave}" data-d="-1" data-max="${max}">−</button><button data-a="vital" data-chave="${chave}" data-d="1" data-max="${max}">+</button></div></div>`;
  };
  const falta = Math.max(0, C.nVida - (v.rolagens || []).length);
  let h = secao("Vigor do corpo") + `<div class="vitais">${vital("VIDA", "var(--c-vida)", "atual", d.vida)}${vital("MANA", "var(--c-mana)", "mana_atual", d.mana)}${vital("VIGOR", "var(--c-vigor)", "vigor_atual", d.vigor)}</div>
    <p class="sub" style="margin:8px 2px">Vigor recupera ${d.vigor_regen}/turno · Dados de vida: ${C.nVida}d12 ${v.modo === "media" ? "(média 7)" : `(rolados: ${Math.min(v.rolagens.length, C.nVida)})`}
    <span class="so-ed">· <a href="#" data-a="modo-vida" style="color:var(--vinho)">${v.modo === "media" ? "usar rolagem" : "usar média"}</a>
    ${v.modo === "rolar" && falta ? ` · <a href="#" data-a="rolar-vida" style="color:var(--vinho);font-weight:700">🎲 rolar ${falta}d12</a>` : ""}</span></p>`;
  h += `<div class="grade g3 g4m">${caixa("CA", d.ca, `TEN +${d.ca_ten}`, "var(--c-ca)")}${caixa("Movimento", `${C.mov} m`, `${Math.round(C.mov / 1.5)} quadrados${C.lentidao ? " · lento" : ""}`, "var(--c-mov)")}
    ${caixa("Iniciativa", `+${d.iniciativa_bonus}`, `${d.iniciativa_dados}d20, o maior`)}<div data-a="extras">${caixa("Ações extras", d.acoes_extras, C.exaustao ? "Exaustão" : d.acoes_extras ? (() => { const [q, f] = R.acoesDoTurno(d.acoes_extras, S.acoes_extras_tipos); return f ? "escolha o tipo ›" : `${q.Comum - 1} Comum · ${q["Bônus"] - 1} Bônus`; })() : "por DES")}</div>
    ${caixa("Carga", `${C.carga}/${d.carga}`, C.lentidao ? "Lentidão" : "atual / máx.")}${caixa("Red. dano", d.rd ? `${d.rd}d4` : "—", "por TEN")}
    ${caixa("Descoberta", d.descoberta, "por Arcano")}${caixa("Talismãs", `${S.talismas.filter((t) => t.nome).length}/${d.talismas}`, "espaços", "var(--c-tal)")}</div>`;
  h += secao("Atributos", `${C.gastos}/${C.disp} pontos de nível`) + `<div class="grade g2 g4m">${R.ATRIBUTOS.map((k) => {
    const val = C.a[k], x = S.atributos[k];
    return `<div class="cartao atr"><div class="faixa" style="background:var(--c-atr);color:var(--ouro2)">${R.NOMES_ATR[k]}</div>
      <div class="total ${val > 99 ? "erro" : ""}" data-a="manual" data-k="${k}">${val}${S.manual[k] != null ? `<span style="font-size:14px;color:var(--vinho)"> ✎</span>` : ""}</div><div class="info">Curva ${d.curva[k]} · BC +${d.bc[k]} · ${1 + Math.floor(R.cap(val) / 20)}d20${R.vantagem(val) ? ` · <span class="vant">vant.</span>` : ""}</div>
      <div class="info" style="font-size:11px">ini ${x.inicial || "—"} · esp ${int(x.especie) >= 0 ? "+" : ""}${int(x.especie)}${C.tb[k] ? ` · talismã +${C.tb[k]}` : ""}${int(x.bonus) ? ` · bôn ${int(x.bonus)}` : ""}</div>
      <div class="ctrl so-ed"><button data-a="pts" data-k="${k}" data-d="-1">−</button><span>nível +${int(x.niveis)}</span><button data-a="pts" data-k="${k}" data-d="1">+</button></div></div>`;
  }).join("")}</div>`;
  const erros = C.avisos.filter((a) => a[0] === "erro"), infos = C.avisos.filter((a) => a[0] !== "erro");
  h += secao("Avisos do escriba") + `<div class="lista"><ul class="avisos">${erros.length ? "" : `<li class="tudo">Nada pendente na ficha.</li>`}${erros.concat(infos).map(([t, m]) => `<li class="${t}">${esc(m)}</li>`).join("")}</ul></div>`;
  return h;
}

function linhaArma(i) {
  const w = S.armas[i], ar = ARMAS[w.grupo];
  let h = `<div class="cartao arma a${i}"><div class="linha1"><span style="font-family:var(--tit);color:var(--vinho);width:22px">${i ? "II" : "I"}</span>
    <button class="sel ${ar ? "" : "vazio"}" data-a="esc-arma" data-i="${i}">${ar ? esc(w.grupo) : "Escolher arma"}</button>
    ${ar ? `<button class="sel" style="width:96px" data-a="esc-nivel-arma" data-i="${i}">Nv ${int(w.nivel, 1)}</button>` : ""}</div>`;
  if (!ar) return h + "</div>";
  const nv = int(w.nivel, 1), l = ar.tabela.find((x) => x.nivel === nv) || ar.tabela[0], k = ar.ataque;
  const props = R.lerProps(w.props), ep = efeitoArma(w, nv);
  const extra = Math.floor(R.cap(C.a[k]) / 30), acerto = C.d.bc[k] + C.d.n3 + (R.ACERTO_ARMA[nv] || 0) + C.ef.acerto + (C.escolha.maestria.includes(w.grupo) ? 1 : 0) + ep.acerto;
  const dom = C.escolha.dominio[w.grupo] || 0, pmax = l.propriedades + dom, prob = R.problemasProps(props, pmax);
  const vig = ar.vigor ? (nv >= 8 ? 10 : nv >= 4 ? 8 : 5) : "—";
  const falta = statusArma(C, w.grupo, nv, props);
  h += `<dl><div><dt>Dano</dt><dd>${esc(ep.dano + ep.extras.filter((x) => !x[2]).map((x) => ` + ${x[0]} ${x[1]}`).join(""))}</dd></div><div><dt>Ataque</dt><dd>1d20 +${acerto}${R.vantagem(C.a[k]) ? " (vant.)" : ""}</dd></div>
    <div><dt>Crítico</dt><dd>${ep.margem}${ep.mult === 3 ? " ×3" : ""}</dd></div><div><dt>Tipo</dt><dd>${esc(l.tipo)}</dd></div><div><dt>DT</dt><dd>${10 + C.d.bc[k] + C.d.n3}</dd></div>
    <div><dt>Vigor/atk</dt><dd>${vig}</dd></div></dl>
    <button class="sel ${props.length ? "" : "vazio"}" style="margin-top:6px;font-size:14px" data-a="esc-props" data-i="${i}">Propriedades ${props.length}/${pmax}${dom ? ` (+${dom} Domínio)` : ""}: ${esc(props.join(", ") || "nenhuma")}</button>
    ${prob.length ? `<div class="erro" style="font-size:13.5px;margin-top:4px">${NO} ${esc(prob.join("; "))}</div>` : ""}
    <div class="sub">${k} · peso ${l.espaco}${C.escolha.maestria.includes(w.grupo) ? " · Maestria +1" : ""}${extra ? ` · +${extra} dado de dano por ${k}` : ""}</div>
    ${falta.length ? `<div class="erro" style="font-size:13.5px;margin-top:4px">${NO} falta: ${esc(falta.join(", "))}</div>` : ""}
    ${(() => { const dg = S.desgaste[i] || {}; return dg.desgastada
      ? `<div class="erro" style="font-size:13.5px;margin-top:4px">Desgastada: sem uso por um turno. <a href="#" data-a="reafiar" data-i="${i}">Já passou</a></div>`
      : `<div class="sub">Afiada: ${ep.desgaste - int(dg.usados)}/${ep.desgaste} turnos · o crítico reafia</div>`; })()}
    ${(R.RECURSOS_ARMA[w.grupo] || []).length ? `<div class="recursos">${R.RECURSOS_ARMA[w.grupo].map(([n, mx]) => { const v = int(((S.recursos[`${i}:${w.grupo}`]) || {})[n]);
      return `<span class="recurso"><button data-a="recurso" data-i="${i}" data-n="${esc(n)}" data-d="-1" aria-label="menos">−</button><b>${esc(n)}</b> ${v}${mx ? `/${mx}` : ""}<button data-a="recurso" data-i="${i}" data-n="${esc(n)}" data-d="1" aria-label="mais">+</button></span>`; }).join("")}</div>` : ""}
    <div class="linhabts"><button class="botao prim" data-a="rolar-arma" data-i="${i}">🎲 Atacar</button></div>
    <div class="acoes-arma">${(ar.acoes || []).map((x, j) => { const p = R.acaoArma(x.nome, x.texto);
      return p.nota || x.nome === "Atacar" ? "" : `<button class="chip-acao ${p.passiva ? "passiva" : ""}" data-a="acao-arma" data-i="${i}" data-j="${j}">${esc(x.nome)}${p.acao ? `<small>${p.acao}</small>` : p.passiva ? "<small>automático</small>" : ""}</button>`; }).join("")}</div>
    ${(ar.descricao || (ar.acoes || []).some((x) => R.acaoArma(x.nome, x.texto).nota)) ? `<details class="acoes"><summary>Mecânica da arma</summary>${ar.descricao ? `<p class="sub">${esc(ar.descricao)}</p>` : ""}
      ${(ar.acoes || []).filter((x) => R.acaoArma(x.nome, x.texto).nota).map((x) => `<div class="acao ${x.sub ? "sub" : ""}"><b>${x.sub ? "↳ " : ""}${esc(x.nome)}</b> — ${esc(x.texto)}</div>`).join("")}</details>` : ""}</div>`;
  return h;
}
function textoEfeitos() {
  const partes = [];
  for (const nome of [...C.tal].sort()) {
    const e = R.EFEITOS_TALENTOS[nome]; if (!e || (e.tipo === "sit" && !C.ativos.has(nome))) continue;
    const bits = [["ca", "CA"], ["mov", "m"], ["acerto", "acerto"], ["iniciativa", "iniciativa"], ["descoberta", "Descoberta"], ["contra", "contra-encant."], ["dt_alma", "DT alma"], ["dano_nivel", "nível de dano"]]
      .filter(([k]) => e[k]).map(([k, r]) => `+${e[k]} ${r}`).concat(Object.entries(e.pericia || {}).map(([p, v]) => `+${v} ${p}`));
    partes.push(`<b>${esc(nome)}</b>${e.tipo === "sit" ? " (ativo)" : ""}: ${bits.join(", ")}`);
  }
  const x = C.escolha;
  if (x.maestria.length) partes.push(`<b>Maestria</b>: ${esc(x.maestria.join(", "))} (+1 acerto)`);
  if (Object.keys(x.dominio).length) partes.push(`<b>Domínio</b>: ${Object.entries(x.dominio).map(([g, n]) => `${esc(g)} +${n} propriedade${n > 1 ? "s" : ""}`).join(", ")}`);
  if (x.mana) partes.push(`<b>Matrícula</b>: ${x.todas_escolas ? "todas as escolas" : esc(x.escolas.join(", "))} (−${x.mana} Mana${x.espaco ? ", −1 espaço" : ""})`);
  if (x.pericia_mestre.length) partes.push(`<b>Mestre das Perícias</b>: ${esc(x.pericia_mestre.join(", "))} (+2 e 1 vantagem)`);
  for (const [n, v] of Object.entries(x.cond_extra)) partes.push(`<b>Condição Endurecida</b>: ${n} +${v}`);
  return partes;
}
function pCombate() {
  const d = C.d;
  const ef = textoEfeitos();
  const armasBt = S.armas.map((w, i) => ARMAS[w.grupo] ? `<button class="botao prim" data-a="rolar-arma" data-i="${i}">⚔ ${esc(w.grupo)}</button>` : "").join("");
  let h = secao("Rolar") + `<div class="linhabts" style="margin-top:0">${armasBt}<button class="botao" data-a="conjurar-menu">✧ Conjurar</button>
    <button class="botao" data-a="rolar-ini">🎲 Iniciativa</button><button class="botao leve" data-a="diario">📜 Diário</button></div>
    ${sessao.efeitos.length ? `<div class="lista mestre">${sessao.efeitos.map((e) => `<div class="item"><span class="marca">⏳</span><div class="tx"><b>${esc(e.nome)}</b><small>${durEfeito(e)}${e.desc ? " · " + esc(e.desc) : ""}</small></div></div>`).join("")}</div>` : ""}
    ${ef.length ? `<p class="sub">Talentos em uso: ${ef.join(" · ")}</p>` : ""}`;
  h += cardTurno() + cardUsos();
  h += secao("Defesa") + `<div class="lista">${R.PERICIAS_DEFESA.map(([n, k, tn]) =>
    `<div class="item" data-a="rolar-def" data-n="${n}"><div class="tx"><b>${n}</b><small>${k}${R.vantagem(C.a[k]) ? " · vantagem" : ""}</small></div><span class="num">+${bonusDefesa(n, k, tn)}</span><span class="sub">🎲</span></div>`).join("")}
    <div class="item" data-a="contra"><div class="tx"><b>Contradomínio</b><small>anular encantamento · ${S.contra_usados}/${d.contra_encant} neste combate</small></div><span class="sub">🎲</span></div></div>`;
  h += secao("Ataque sem arma") + `<div class="lista">${R.PERICIAS_ATAQUE.map(([n, atrs]) =>
    `<div class="item" data-a="rolar-atk" data-n="${n}"><div class="tx"><b>${n}</b><small>${atrs.join(" ou ")}</small></div><span class="num">${atrs.map((k) => `+${d.bc[k] + d.n3 + (n === "Luta" || n === "Pontaria" ? C.ef.acerto : 0)}${R.vantagem(C.a[k]) ? "ᵛ" : ""}`).join(" / ")}</span><span class="sub">🎲</span></div>`).join("")}</div>
    <p class="sub">ᵛ = vantagem (2d20). DT: Feitiçaria ${d.dt_feiticaria} · Desejo ${d.dt_desejo} · Provocar ${R.dtProvocar(d, C.nv)}</p>`;
  h += secao("Armas") + linhaArma(0) + linhaArma(1);
  const w0 = ARMAS[S.armas[0].grupo], w1 = ARMAS[S.armas[1].grupo];
  if (w0 && w1) {
    if (!w0.uso_duplo || !w1.uso_duplo) h += `<p class="erro">${NO} ${!w0.uso_duplo ? w0.nome : w1.nome} não permite uso duplo.</p>`;
    else {
      const rq = R.reqUsoDuplo(R.reqArma(w0, int(S.armas[0].nivel, 1)), R.reqArma(w1, int(S.armas[1].nivel, 1)));
      const f = R.reqFalta(rq, C.a), conj = ["Cajado", "Selo"].includes(w0.nome) || ["Cajado", "Selo"].includes(w1.nome);
      h += `<p class="${f.length ? "erro" : "sub"}">Uso duplo: ${Object.entries(rq).map(([k, v]) => `${v} ${k}`).join(", ")} ${f.length ? `— falta ${f.join(", ")}` : OK}.
        Coordenação contra DT ${8 + Math.max(int(S.armas[0].nivel, 1), int(S.armas[1].nivel, 1))} no começo do turno em que atacar com as duas.</p>
        <div class="linhabts"><button class="botao" data-a="coord" data-k="DES">🎲 Coordenação</button>${conj ? `<button class="botao" data-a="coord" data-k="ARC">🎲 Coordenação ao conjurar</button>` : ""}</div>`;
    }
  }
  h += secao("Condições") + `<div class="conds">${R.CONDICOES.map((n) => {
    const c = S.condicoes[n] || { atual: "", max: "100" }, mx = condMax(n), at = int(c.atual), pct = Math.max(0, Math.min(100, (at / Math.max(1, mx)) * 100));
    return `<button class="cond ${at ? "on" : ""}" data-a="editar-cond" data-n="${n}"><b>${n}</b><span>${at}/${mx}</span><i style="width:${pct}%"></i></button>`;
  }).join("")}</div><p class="sub">Enchem com pontos; ao chegar no máximo, o efeito ativa e a barra zera. Descanso curto tira 25 de cada; o longo zera. Toque para ver o efeito.</p>`;
  h += secao("Portão da Morte") + ["Sucessos", "Falhas"].map((n) => `<div class="portao"><span class="r" style="background:${n === "Sucessos" ? "var(--c-vigor)" : "var(--c-vida)"}">${n}</span>
    ${S.portao[n].map((on, i) => `<button class="bolinha ${on ? "on" : ""} ${n === "Sucessos" ? "s" : "f"}" data-a="portao" data-n="${n}" data-i="${i}"></button>`).join("")}</div>`).join("")
    + `<p class="sub">d20 no início do turno: 11+ é sucesso. 5 sucessos: volta com 1 de Vida e 1 cicatriz. 5 falhas: morte.</p>`;
  h += secao("Resistências") + `<div>${R.RESISTENCIAS.map(([lim, n]) => `<span class="chip ${d.resistencias.includes(n) ? "on" : ""}">${d.resistencias.includes(n) ? "☑" : "☐"} ${n} ${lim}</span>`).join("")}</div>`;
  h += secao("Descanso") + `<div class="linhabts" style="margin-top:0"><button class="botao" data-a="descanso" data-t="curto">☾ Descanso curto</button><button class="botao" data-a="descanso" data-t="longo">☀ Longo</button>
    <button class="botao" data-a="pocao">⚗ Poção Espiritual</button></div>
    <p class="sub">Descansos curtos desde o longo: ${S.descansos_curtos}/${R.DESCANSOS_CURTOS_MAX} · Poção Espiritual: ${R.pocaoEspiritualDados(C.nv, d.curva.VIT)}d10</p>`;
  return h;
}

function pPericias() {
  const d = C.d, n = C.treinadas.size;
  let h = secao("Perícias", `<span class="${n > d.pericias_treinadas_max ? "erro" : ""}">${n}/${d.pericias_treinadas_max} treinadas</span>`)
    + `<div class="lista">${R.PERICIAS.map(([nome, atrs, req]) => {
      const tr = C.treinadas.has(nome), at = atrs || [S.prevalencia_attr || "ARC"];
      const [melhor, bonus0, dados] = R.periciaFora(C.a, C.nv, at, tr);
      const mestre = C.escolha.pericia_mestre.includes(nome);
      const discreta = nome === "Furtividade" && S.armas.some((w) => ARMAS[w.grupo] && R.lerProps(w.props).map(R.nomeProp).includes("Discreta")) ? 5 : 0;
      const bonus = bonus0 + (C.ef.pericia[nome] || 0) + (mestre ? 2 : 0) + discreta;
      return `<div class="item" data-a="rolar-per" data-n="${esc(nome)}" data-b="${bonus}" data-d="${dados + (mestre ? 1 : 0)}"><span class="check ${tr ? "on" : ""}" data-a="treinar" data-n="${esc(nome)}"></span>
        <div class="tx"><b>${esc(nome)}${req ? " •" : ""}</b><small>${atrs ? atrs.join("/") : `Prevalência usa ${at[0]}`} · ${dados + (mestre ? 1 : 0)}d20${mestre ? " · Mestre" : ""}</small></div><span class="num">+${bonus}</span><span class="sub">🎲</span></div>`;
    }).join("")}</div><p class="sub">${banco.modo === "edicao" ? "Toque na perícia para ver o que ela faz" : "Toque na perícia para rolar (1d20 a mais a cada 20 pontos do atributo, fica o maior)"}. A caixa marca o treino (Modo Edição). • exige treino.</p>`;
  h += secao("Perícia de ataque treinada") + `<div>${R.PERICIAS_ATAQUE.map(([nn]) => `<span class="chip ${S.pericia_ataque === nn ? "on" : ""}" data-a="per-atk" data-n="${nn}">${nn}</span>`).join("")}</div>`;
  h += secao("Atributo da Prevalência") + `<div>${R.ATRIBUTOS.map((k) => `<span class="chip ${S.prevalencia_attr === k ? "on" : ""}" data-a="prev-attr" data-k="${k}">${k}</span>`).join("")}</div>`;
  return h;
}

function pGrimorio() {
  const d = C.d;
  let h = secao("Grimório") + `<div class="grade g3">${caixa("Espaços", `${C.espUsados}/${d.espacos_encant}`, "equipados", "var(--c-mana)")}
    ${caixa("DT", `${d.dt_feiticaria}/${d.dt_desejo}`, "Feitiçaria / Desejo")}${caixa("Dados extras", `+${d.dados_extra_magia}/+${d.dados_extra_feitico}`, "Magia / Feitiço")}</div>`;
  h += `<div class="linhabts so-ed" style="margin-bottom:10px"><button class="botao prim" data-a="aprender">✦ Aprender encantamento</button></div>`;
  if (!S.encantamentos.length) return h + `<div class="vazio-msg">Nenhum encantamento aprendido.</div>`;
  const impl = (dom) => Math.max(0, ...S.armas.filter((w) => w.grupo === (dom === "Magia" ? "Cajado" : "Selo")).map((w) => int(w.nivel, 1)));
  h += `<div class="lista">${S.encantamentos.map((x, i) => {
    const e = ENC[x.familia]; if (!e) return "";
    const vs = e.versoes.filter((v) => x.versoes.includes(v.nivel)), top = vs[vs.length - 1] || e.versoes[0];
    const ni = impl(e.dominio), conj = ni >= top.nivel;
    return `<div class="item" data-a="ver-enc" data-i="${i}"><span class="check ${x.equipado ? "on" : ""}" data-a="equipar" data-i="${i}"></span>
      <div class="tx"><b>${esc(e.nome)}</b><small>${e.dominio} · nv ${x.versoes.join(", ")} · ${esc(top.mana)}${custoEnc(e, top)[0] != null && custoEnc(e, top)[0] !== R.custoMana(top) ? ` (Matrícula: ${custoEnc(e, top)[0]})` : ""} · esp ${custoEnc(e)[1]}${conj ? "" : ` · ${NO} sem ${e.dominio === "Magia" ? "cajado" : "selo"} nv ${top.nivel}`}</small></div>
      <button class="passos" style="border:0;background:none;padding:0" data-a="conjurar" data-f="${esc(e.nome)}" data-v="${top.nivel}"><span class="botao prim" style="min-height:38px;padding:6px 12px">🎲</span></button></div>`;
  }).join("")}</div><p class="sub">Marque a caixa para equipar. Toque no nome para ver a descrição.</p>`;
  return h;
}
function descEnc(nome, destaque) {
  const e = ENC[nome]; if (!e) return "";
  const x = S.encantamentos.find((y) => y.familia === nome);
  return `<p class="meta">${e.dominio} · ${esc(e.categoria)} · Espaço ${e.espaco}</p>` + e.versoes.map((v) => {
    const m = R.statusVersao(v, e.dominio, C.a, C.nv, C.nv === 1 && armasEq().some((g) => g === "Cajado" || g === "Selo"));
    const ja = x && x.versoes.includes(v.nivel);
    return `<div class="desc"><h4>${esc(v.tier)} — Nível ${v.nivel} <span class="${ja || !m.length ? "ok" : "erro"}" style="font-size:13px">${ja ? "· aprendida" : m.length ? "· " + esc(m.join(", ")) : "· pode aprender"}</span></h4>
      <div class="meta">Mana ${esc(v.mana)} · Ação ${esc(v.acao)} · Distância ${esc(v.distancia)}<br>Requisitos: ${esc(v.req_texto)}</div>${esc(v.descricao)}</div>`;
  }).join("");
}

function linhaTalento(sl) {
  const meta = sl.startsWith("meta"), ativo = sl === "extra" ? C.tal.has("Versátil") : meta ? slotValido(sl) : int(sl) <= C.nv;
  const nome = S.talentos[sl], t = TAL[nome], m = t ? statusTal(C, t, sl) : [];
  const eft = R.EFEITOS_TALENTOS[nome];
  const sw = eft && eft.tipo === "sit" ? `<span class="chip ${C.ativos.has(nome) ? "on" : ""}" style="margin:0" data-a="tal-ativo" data-n="${esc(nome)}">${C.ativos.has(nome) ? "ativo" : "inativo"}</span>` : "";
  const tipoE = R.ESCOLHA_TALENTO[nome], valE = S.talentos_escolha[sl] || "";
  const tag = tipoE ? (valE ? `✓ ${R.ROTULO_ESCOLHA[tipoE]}: ${valE} · ` : `escolha ${R.ROTULO_ESCOLHA[tipoE].toLowerCase()} · `)
    : eft ? (eft.tipo === "perm" ? "✓ aplicado · " : `situacional${eft.nota ? " (" + eft.nota + ")" : ""} · `) : "";
  const chipE = tipoE ? `<span class="chip ${valE ? "on" : ""}" style="margin:0;max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" data-a="tal-escolha" data-s="${sl}">${esc(valE || "escolher")}</span>` : "";
  const rot = sl === "extra" ? "✦" : meta ? `M${sl.slice(4)}` : sl;
  return `<div class="item ${ativo ? "" : "bloq"}" data-a="esc-talento" data-s="${sl}"><span class="marca" style="font-family:var(--tit);color:var(--vinho);width:34px">${rot}</span>
    <div class="tx"><b class="${m.length ? "erro" : ""}">${esc(nome || (ativo ? "Escolher talento" : "—"))}</b><small>${esc(t ? (m.length ? NO + " " + m.join(", ") : tag + t.descricao) : ativo ? (meta ? "talento da Meta de Vida · toque para escolher" : "toque para escolher") : `liberado no nível ${sl}`)}</small></div>${chipE || sw || `<span class="sub">›</span>`}</div>`;
}
function pTalentos() {
  const niveis = SLOTS.filter((x) => x !== "extra"), abertos = niveis.filter((x) => int(x) <= C.nv || S.talentos[x]);
  const futuros = niveis.filter((x) => !abertos.includes(x));
  const extras = (C.tal.has("Versátil") || S.talentos.extra ? ["extra"] : []).concat(META_SLOTS.filter((x) => slotValido(x) || S.talentos[x]));
  let h = secao("Talentos", "um a cada nível par") + `<div class="lista">${abertos.concat(extras).map(linhaTalento).join("")}
    ${futuros.length ? linhaTalento(futuros[0]) : ""}</div>`;
  if (futuros.length > 1) h += `<details class="acoes"><summary>Mais ${futuros.length - 1} slots nos próximos níveis</summary><div class="lista">${futuros.slice(1).map(linhaTalento).join("")}</div></details>`;
  // Metas de Vida
  const mt = S.meta, cam = R.CAMINHOS.find((c) => c[0] === mt.caminho), rec = R.recompensaMetas(mt.concluidas);
  h += secao("Metas de Vida", `${rec.talentos} concluída(s)`) + `<div class="lista">
    <div class="item" data-a="meta-caminho"><div class="tx"><b>${cam ? `Caminho do ${esc(cam[0])}` : "Escolher Caminho"}</b><small>${cam ? `perícia: ${esc(cam[1])}${C.treinadas.has(cam[1]) ? "" : ` · <span class="erro">treine ${esc(cam[1])} antes da Etapa 1</span>`}` : "uma Meta por vez, com um mentor do Andar"}</small></div><span class="sub">›</span></div>
    <div class="item" data-a="meta-mentor"><div class="tx"><b>Mentor</b><small>${esc(mt.mentor || "toque para anotar")}</small></div></div>
    ${cam ? cam[2].map((t, k) => `<div class="item" data-a="meta-etapa" data-k="${k}"><span class="check ${mt.etapas[k] ? "on" : ""}"></span><div class="tx"><b>Etapa ${k + 1} · ${R.ETAPAS_META[k]}</b><small>${esc(t)}</small></div></div>`).join("") : ""}
    <div class="item" data-a="meta-notas"><div class="tx"><b>Anotações</b><small>${esc(mt.notas || "toque para escrever")}</small></div></div></div>
    ${cam && mt.etapas.every(Boolean) ? `<div class="linhabts"><button class="botao prim" data-a="meta-concluir">✦ Concluir a Meta</button></div>` : ""}
    <p class="sub">Cada Meta concluída dá 1 talento extra; a primeira dá também +5 pontos em um atributo.${rec.talentos ? ` Você já tem ${rec.talentos} talento(s) de Meta (M1…)${rec.pontos ? " e os +5 pontos na distribuição" : ""}.` : ""}
    <span class="so-ed"> · <a href="#" data-a="meta-n" data-d="1" style="color:var(--vinho)">+1 concluída</a> · <a href="#" data-a="meta-n" data-d="-1" style="color:var(--vinho)">−1</a> · <a href="#" data-a="meta-perder" style="color:var(--vinho)">perder a Meta (subiu de Andar)</a></span></p>`;
  h += secao("Vínculos") + `<div class="lista">${[["grupo", "Com o grupo"], ["mundo", "Com o mundo"]].map(([k, r]) =>
    `<div class="item" data-a="editar-vinc" data-k="${k}"><div class="tx"><b>${r}</b><small>${esc(S.vinculos[k] || "toque para escrever")}</small></div></div>`).join("")}</div>`;
  return h;
}
A["meta-caminho"] = () => folha("Caminho da Meta de Vida", `<div class="lista">${R.CAMINHOS.map(([n, p, et]) =>
  `<div class="item" data-a="meta-caminho-ok" data-n="${esc(n)}"><span class="check ${S.meta.caminho === n ? "on" : ""}"></span><div class="tx"><b>${esc(n)} <span class="sub">(${esc(p)})</span></b><small>${esc(et.join(" → "))}</small></div></div>`).join("")}
  <div class="item" data-a="meta-caminho-ok" data-n=""><div class="tx"><b>Nenhum</b></div></div></div>`);
A["meta-caminho-ok"] = (el) => { const n = el.dataset.n; fecharFolha(); mudar((s) => { if (s.meta.caminho !== n) s.meta.etapas = [false, false, false]; s.meta.caminho = n; }); };
A["meta-mentor"] = () => folha("Mentor", `<input class="busca" id="mm" value="${esc(S.meta.mentor)}" placeholder="NPC do ofício no Andar atual">`,
  `<button class="botao leve" data-a="fechar">Cancelar</button><button class="botao prim" data-a="meta-mentor-ok">Salvar</button>`);
A["meta-mentor-ok"] = () => { const v = $("#mm").value.trim(); fecharFolha(); mudar((s) => { s.meta.mentor = v; }); };
A["meta-notas"] = () => folha("Anotações da Meta", `<textarea id="mn" rows="5" style="width:100%">${esc(S.meta.notas)}</textarea>`,
  `<button class="botao leve" data-a="fechar">Cancelar</button><button class="botao prim" data-a="meta-notas-ok">Salvar</button>`);
A["meta-notas-ok"] = () => { const v = $("#mn").value; fecharFolha(); mudar((s) => { s.meta.notas = v; s.vinculos.metas = v; }); };
A["meta-etapa"] = (el) => {
  const k = int(el.dataset.k);
  if (!S.meta.etapas[k] && k > 0 && !S.meta.etapas[k - 1]) { toast("Cada etapa só vale depois da anterior."); return; }
  mudar((s) => { s.meta.etapas[k] = !s.meta.etapas[k]; if (!s.meta.etapas[k]) for (let x = k + 1; x < 3; x++) s.meta.etapas[x] = false; });
};
A["meta-concluir"] = () => {
  const primeira = int(S.meta.concluidas) === 0;
  mudar((s) => { s.meta.concluidas = Math.min(R.METAS_MAX, int(s.meta.concluidas) + 1); s.meta.etapas = [false, false, false]; s.meta.mentor = ""; });
  registrarDiario({ titulo: "✦ Meta de Vida concluída", linhas: [`Caminho do ${esc(S.meta.caminho)}.`, primeira ? "Ganhou 1 talento extra e +5 pontos em um atributo." : "Ganhou 1 talento extra."] });
  toast(`✦ <b>Meta concluída!</b> ${primeira ? "1 talento extra e +5 pontos de atributo." : "1 talento extra."} Escolha o talento M${S.meta.concluidas} acima.`, 6000);
};
A["meta-n"] = (el) => mudar((s) => { s.meta.concluidas = Math.max(0, Math.min(R.METAS_MAX, int(s.meta.concluidas) + int(el.dataset.d))); });
A["meta-perder"] = () => { mudar((s) => { s.meta.etapas = [false, false, false]; s.meta.mentor = ""; s.meta.caminho = ""; }); toast("Meta em andamento perdida (ficam os talentos e pontos já ganhos)."); };

