// ------------------------------------------------------------------ Corpo (Perda de Membros, 3.4) e Crença (Cultos e Igrejas, 3.4)
const CULTO_VAZIO = { papel: "", crenca: "", nome: "", divindade: "", profeta: "", tema: "", regra_faz: "", regra_nunca: "", grau: 1, abalado: false,
  local: "", discipulos: "", comunidades: "", igreja: "", na_igreja: false, preces_usadas: 0, milagres_usados: 0, notas: "" };
function normalizarCulto(c) {
  const o = Object.assign({}, CULTO_VAZIO, c && typeof c === "object" ? c : {});
  for (const k of Object.keys(CULTO_VAZIO)) if (typeof CULTO_VAZIO[k] === "string") o[k] = String(o[k] || "");
  if (!["", "fiel", "profeta"].includes(o.papel)) o.papel = "";
  o.grau = Math.max(1, Math.min(5, int(o.grau, 1)));
  o.abalado = !!o.abalado; o.na_igreja = !!o.na_igreja;
  o.preces_usadas = Math.max(0, int(o.preces_usadas)); o.milagres_usados = Math.max(0, int(o.milagres_usados));
  if (!R.IGREJAS[o.igreja]) o.igreja = "";
  return o;
}
const ROT_TIPO = { olhos: ["Olhos", "Olho"], bracos: ["Braços e mãos", "Braço"], pernas: ["Pernas", "Perna"] };

// ---------------- Corpo
function pCorpo() {
  const c = S.corpo, pm = C.pm, ed = banco.modo === "edicao";
  const limiar = Math.ceil(C.d.vida / 2);
  let h = secao("Corpo", pm.estados.length ? `<span class="erro">${esc(pm.estados.join(" · "))}</span>` : "inteiro");
  h += pm.notas.length ? `<div class="cartao" style="padding:10px 14px">${pm.notas.map((n) => `<p style="margin:4px 0;line-height:1.4">${esc(n)}</p>`).join("")}
      <p class="sub" style="margin:6px 0 0">Já aplicado na ficha: CA, deslocamento, Carga, Reflexo, Atletismo, Percepção e o acerto e dano das armas.</p></div>`
    : `<p class="sub" style="margin:4px 0 10px">Nenhum membro perdido.</p>`;
  h += `<p class="sub ajuda">Um único golpe com dano final igual ou maior que a metade da Vida máxima (${limiar} para você) remove 1 membro. Danos mentais (Psíquico, Êxtase, Melódico, Radiante), Veneno, Sangramento, Podridão e Congelamento não removem. A perda é permanente: nenhuma cura recupera um membro. Toque no membro para marcar a perda.</p>`;
  h += `<div class="linhabts" style="margin-top:6px"><button class="botao prim" data-a="membro-sortear">🎲 Golpe forte: sortear o membro</button></div>`;
  for (const tipo of ["olhos", "bracos", "pernas"]) {
    const lista = c[tipo], ok = lista.filter((m) => !m.perdido).length;
    h += secao(ROT_TIPO[tipo][0], `${ok}/${lista.length}`);
    h += lista.length ? `<div class="lista">${lista.map((m, i) => {
      const mao = tipo === "bracos" ? `<span class="chip ${m.mao ? "on" : ""}" style="margin:0" data-a="membro-mao" data-i="${i}">${m.perdido ? "sem mão" : m.mao ? esc(R.nomeMao(m.nome)) : "mão perdida"}</span>` : "";
      return `<div class="item" data-a="membro" data-t="${tipo}" data-i="${i}"><span class="check ${m.perdido ? "" : "on"}"></span>
        <div class="tx"><b class="${m.perdido ? "erro" : ""}">${esc(m.nome)}</b><small>${m.perdido ? "perdido" : "inteiro"}</small></div>${mao}</div>`;
    }).join("")}</div>` : `<p class="vazio">A espécie não tem ${ROT_TIPO[tipo][0].toLowerCase()}.</p>`;
    h += `<div class="linhabts so-ed" style="margin-top:6px"><button class="botao leve" data-a="membro-qtd" data-t="${tipo}" data-d="-1">− ${ROT_TIPO[tipo][1]}</button><button class="botao leve" data-a="membro-qtd" data-t="${tipo}" data-d="1">+ ${ROT_TIPO[tipo][1]}</button></div>`;
  }
  h += secao("Outros membros", "da espécie");
  h += c.outros.length ? `<div class="lista">${c.outros.map((m, i) => `<div class="item" data-a="membro" data-t="outros" data-i="${i}"><span class="check ${m.perdido ? "" : "on"}"></span>
      <div class="tx"><b class="${m.perdido ? "erro" : ""}">${esc(m.nome)}</b><small>${m.perdido ? "perdido · sem regra no livro, o Mestre decide" : "inteiro"}</small></div>
      <span class="chip so-ed" style="margin:0" data-a="membro-tirar" data-i="${i}">remover</span></div>`).join("")}</div>`
    : `<p class="vazio">Cauda, asas, antenas, chifres… o que a espécie tiver a mais.</p>`;
  h += `<div class="linhabts so-ed" style="margin-top:6px"><button class="botao leve" data-a="membro-outro">+ Outro membro</button><button class="botao leve" data-a="membro-padrao">Corpo padrão (2 · 2 · 2)</button></div>`;
  h += `<p class="sub ajuda">Espécie com mais ou menos membros: no Modo Edição, use − e + em cada grupo. A penalidade conta quantos sobram: com 2 ou mais, nenhuma; com 1, a de "perdeu 1"; com nenhum, a de "perdeu os 2". Membros que a espécie nunca teve não dão penalidade. O braço inclui a mão: perder o braço leva a mão junto.${ed ? "" : " Para mudar a quantidade, toque em ✎ Editar."}</p>`;
  return h;
}
A["membro"] = (el) => {
  const t = el.dataset.t, i = int(el.dataset.i), m = S.corpo[t][i]; if (!m) return;
  if (m.perdido) {
    folha(`Recuperar ${esc(m.nome)}?`, `<p>A perda de um membro é permanente: nenhuma cura, nem a Poção Espiritual, recupera um membro perdido. Use só para corrigir uma marcação errada (ou se o Mestre permitir uma prótese ou um milagre).</p>`,
      `<button class="botao leve" data-a="fechar">Cancelar</button><button class="botao prim" data-a="membro-ok" data-t="${t}" data-i="${i}" data-v="0">Desmarcar a perda</button>`);
    return;
  }
  folha(`Perdeu ${esc(m.nome)}?`, `<p class="sub">${t === "bracos" ? "O braço inclui a mão. " : ""}A perda é permanente e entra no Diário.</p>`,
    `<button class="botao leve" data-a="fechar">Cancelar</button><button class="botao prim" data-a="membro-ok" data-t="${t}" data-i="${i}" data-v="1">Marcar como perdido</button>`);
};
function perderMembro(t, i, mao) {
  const m = S.corpo[t][i]; if (!m) return;
  const nome = mao ? R.nomeMao(m.nome) : m.nome;
  mudar((s) => { const x = s.corpo[t][i]; if (mao) x.mao = false; else { x.perdido = true; if (t === "bracos") x.mao = false; } s.corpo = R.normalizarCorpo(s.corpo); });
  const est = C.pm.estados;
  registrarDiario({ titulo: `✂ Membro perdido: ${esc(nome)}`, linhas: [est.length ? `Agora: ${esc(est.join(", "))}.` : "Sem penalidade (a espécie tem membros de sobra)."] });
  toast(`Perdeu: <b>${esc(nome)}</b>.${est.length ? " " + esc(est.join(", ")) + "." : ""}`);
}
A["membro-ok"] = (el) => {
  const t = el.dataset.t, i = int(el.dataset.i); fecharFolha();
  if (el.dataset.v === "1") { perderMembro(t, i, el.dataset.mao === "1"); return; }
  mudar((s) => { s.corpo[t][i].perdido = false; if (t === "bracos") s.corpo[t][i].mao = true; });
};
A["membro-mao"] = (el, ev) => {
  if (ev) ev.stopPropagation();
  const i = int(el.dataset.i), m = S.corpo.bracos[i]; if (!m || m.perdido) return;
  if (m.mao) folha(`Perdeu ${esc(R.nomeMao(m.nome))}?`, `<p class="sub">Só a mão; o braço continua. A perda é permanente.</p>`,
    `<button class="botao leve" data-a="fechar">Cancelar</button><button class="botao prim" data-a="membro-ok" data-t="bracos" data-i="${i}" data-v="1" data-mao="1">Marcar como perdida</button>`);
  else mudar((s) => { s.corpo.bracos[i].mao = true; });
};
A["membro-qtd"] = (el) => {
  const t = el.dataset.t, d = int(el.dataset.d);
  mudar((s) => {
    const l = s.corpo[t];
    if (d > 0 && l.length < 12) l.push(Object.assign({ nome: R.nomeMembro(t, l.length), perdido: false }, t === "bracos" ? { mao: true } : {}));
    if (d < 0 && l.length) l.pop();
  });
};
A["membro-outro"] = () => folha("Outro membro da espécie", `<input class="busca" id="mo" placeholder="Ex.: Cauda, Asa esquerda, Antena">`,
  `<button class="botao leve" data-a="fechar">Cancelar</button><button class="botao prim" data-a="membro-outro-ok">Adicionar</button>`);
A["membro-outro-ok"] = () => { const v = $("#mo").value.trim(); fecharFolha(); if (v) mudar((s) => { s.corpo.outros.push({ nome: v, perdido: false }); }); };
A["membro-tirar"] = (el, ev) => { if (ev) ev.stopPropagation(); mudar((s) => { s.corpo.outros.splice(int(el.dataset.i), 1); }); };
A["membro-padrao"] = () => folha("Corpo padrão", `<p>Volta a 2 olhos, 2 braços e 2 pernas, todos inteiros, e apaga os outros membros.</p>`,
  `<button class="botao leve" data-a="fechar">Cancelar</button><button class="botao prim" data-a="membro-padrao-ok">Voltar ao padrão</button>`);
A["membro-padrao-ok"] = () => { fecharFolha(); mudar((s) => { s.corpo = R.corpoPadrao(); }); };
// 1d8 do livro (com a espécie diferente, 1 dado do tamanho da lista); no modo de dados físicos a pessoa toca no resultado
A["membro-sortear"] = () => {
  const lista = R.membrosParaSortear(S.corpo);
  if (!lista.length) { toast("Não sobrou membro para perder."); return; }
  const n = lista.length, sorteado = fisico() ? -1 : rng(n) - 1;
  folha(`Qual membro (1d${n})`, `${sorteado >= 0 ? `<p>Resultado: <b style="font-size:20px">${sorteado + 1}</b> → <b>${esc(lista[sorteado][3])}</b></p>` : `<p>Role <b>1d${n}</b> e toque no resultado.</p>`}
    <div class="lista">${lista.map(([t, i, mao, nome], k) => `<div class="item ${k === sorteado ? "on" : ""}" data-a="membro-ok" data-t="${t}" data-i="${i}" data-v="1" data-mao="${mao ? 1 : 0}">
      <span class="marca" style="font-family:var(--tit);color:var(--vinho);width:26px">${k + 1}</span><div class="tx"><b>${esc(nome)}</b></div>${k === sorteado ? '<span class="sub">◀</span>' : ""}</div>`).join("")}</div>
    <p class="sub">Se o golpe deixa óbvio qual foi atingido (uma flecha no rosto), o Mestre pode escolher. Toque no membro para confirmar a perda.</p>`,
    `<button class="botao leve" data-a="fechar">Cancelar</button>${sorteado >= 0 ? `<button class="botao leve" data-a="membro-sortear">Rolar de novo</button>` : ""}`);
};

// ---------------- Crença e Culto
const CULTO = () => D.cultos || {};
function pCrenca() {
  const c = S.culto, L = CULTO(), fe = C.a.FE, campo = (k, rot, vazio) => `<div class="item" data-a="culto-txt" data-k="${k}" data-r="${esc(rot)}"><div class="tx"><b>${rot}</b><small>${esc(c[k] || vazio || "toque para escrever")}</small></div></div>`;
  let h = secao("Crença") + `<div>${[["", "Sem culto"], ["fiel", "Fiel de um culto"], ["profeta", "Profeta (fundador)"]].map(([k, r]) => `<span class="chip ${c.papel === k ? "on" : ""}" data-a="culto-papel" data-k="${k}">${r}</span>`).join("")}</div>
    <div class="lista" style="margin-top:8px">${campo("crenca", "No que acredita", "deuses, a Intérprete, um ideal, nada…")}</div>`;
  if (!c.papel) return h + `<p class="sub ajuda">Cada povo, tribo e cidade criou suas próprias crenças, porque ninguém sabe como é a Intérprete. Com Fé 20 ou mais, o personagem pode fundar um Culto e virar o Profeta dele (você tem ${fe} de Fé).</p>`;
  const tema = (L.temas || {})[c.tema];
  const temas = `<div>${Object.keys(L.temas || {}).map((t) => `<span class="chip ${c.tema === t ? "on" : ""}" data-a="culto-tema" data-k="${esc(t)}">${esc(t)}</span>`).join("")}</div>`;
  if (c.papel === "fiel") {
    h += secao("Culto que segue") + `<div class="lista">${campo("nome", "Culto")}${campo("profeta", "Profeta")}${campo("divindade", "Divindade")}</div>` + `<p class="sub" style="margin:8px 0 4px">Tema</p>` + temas;
    h += secao("Grau do Culto") + passosGrau(c);
    if (tema) h += `<div class="cartao" style="padding:10px 14px;margin-top:8px"><b>Bênção (${esc(c.tema)})</b>${c.grau >= 2 ? "" : ' <span class="sub">· a partir do Grau 2</span>'}<p style="margin:4px 0 0;line-height:1.4">${esc(tema.bencao)}</p>
      <p class="sub" style="margin:6px 0 0">Vale perto do Profeta (até ${R.poderesCulto(c.grau).bencao_alcance} m), ou até o próximo descanso longo se você descansou na Igreja do Culto.</p></div>`;
    h += `<div class="lista" style="margin-top:8px">${campo("regra_faz", "Os seguidores devem")}${campo("regra_nunca", "Os seguidores nunca podem")}${campo("notas", "Anotações")}</div>`;
    return h;
  }
  // Profeta
  const ig = R.IGREJAS[c.igreja] && c.na_igreja && c.grau >= 2, pod = R.poderesCulto(c.grau, ig && c.grau >= 5), ativo = !c.abalado;
  const preces = pod.preces, milagres = pod.milagres;
  if (fe < R.CULTO_FE_MIN) h += `<p class="erro" style="font-size:14px">${NO} Fundar um Culto exige ${R.CULTO_FE_MIN} de Fé (você tem ${fe}).</p>`;
  h += secao("O Culto") + `<div class="lista">${campo("nome", "Nome")}${campo("divindade", "Divindade", "a Intérprete como você a imagina, um deus local, uma Alma ancestral, um ideal")}</div>`
    + `<p class="sub" style="margin:8px 0 4px">Tema</p>` + temas
    + `<div class="lista" style="margin-top:8px">${campo("regra_faz", "Os seguidores devem")}${campo("regra_nunca", "Os seguidores nunca podem")}</div>`
    + `<div class="lista" style="margin-top:8px"><div class="item" data-a="culto-abalado"><span class="check ${c.abalado ? "on" : ""}"></span><div class="tx"><b class="${c.abalado ? "erro" : ""}">Abalado</b><small>${c.abalado ? "você quebrou uma regra: sem os poderes do Culto até se redimir diante dos seguidores" : "marque se você quebrar uma regra do próprio Culto"}</small></div></div></div>`;
  h += secao("Grau do Culto", `Grau ${c.grau}`) + passosGrau(c);
  h += secao("Poderes", ativo ? (tema ? esc(c.tema) : "escolha o Tema") : `<span class="erro">Abalado</span>`);
  if (!tema) h += `<p class="vazio">Escolha o Tema para ver os poderes.</p>`;
  else {
    const linha = (nome, liberado, texto, extra = "") => `<div class="item ${liberado && ativo ? "" : "bloq"}" style="display:block"><b>${nome}</b>${liberado ? "" : ` <span class="sub">· ${extra}</span>`}<div style="font-size:14px;line-height:1.45;margin-top:3px">${esc(texto)}</div></div>`;
    h += `<div class="lista">${linha(`Bênção · sempre ativa, aliados a ${pod.bencao_alcance} m`, pod.bencao, tema.bencao, "Grau 2")}
      ${linha(`Prece · ${preces ? `${Math.max(0, preces - c.preces_usadas)}/${preces} por descanso longo` : "1 por descanso longo"}`, preces > 0, tema.prece.replace(/× o Grau/, `× o Grau (${5 * c.grau})`), "Grau 3")}
      ${linha(`Milagre · ${milagres ? `${Math.max(0, milagres - c.milagres_usados)}/${milagres} neste Andar · DT ${R.dtMilagre(C.a, C.nv)}` : "1 por Andar"}`, milagres > 0, tema.milagre, "Grau 5")}</div>`;
    h += `<div class="linhabts" style="margin-top:8px">${preces ? `<button class="botao" data-a="culto-usar" data-k="preces" ${!ativo || c.preces_usadas >= preces ? "disabled" : ""}>🙏 Usar Prece</button>` : ""}
      ${milagres ? `<button class="botao" data-a="culto-usar" data-k="milagres" ${!ativo || c.milagres_usados >= milagres ? "disabled" : ""}>✨ Usar Milagre</button>` : ""}
      ${c.preces_usadas || c.milagres_usados ? `<button class="botao leve" data-a="culto-recup">↺ Devolver usos</button>` : ""}</div>`;
    h += `<p class="sub ajuda">${esc(L.poderes_nota || "")} A Prece volta sozinha no descanso longo.</p>`;
  }
  h += secao("Seguidores") + `<div class="lista">${campo("comunidades", "Comunidades convertidas")}${campo("local", "Local sagrado")}${campo("discipulos", `Discípulos (até ${pod.discipulos})`, pod.discipulos ? "NPCs que mantêm o Culto vivo enquanto o grupo viaja" : "a partir do Grau 2")}</div>`;
  h += `<p class="sub ajuda">${esc(L.conversao || "")}</p>`;
  h += secao("Igreja") + `<div>${["", ...Object.keys(R.IGREJAS)].map((k) => `<span class="chip ${c.igreja === k ? "on" : ""}" data-a="culto-igreja" data-k="${k}">${k || "Nenhuma"}</span>`).join("")}</div>`;
  if (c.igreja) {
    const info = (L.igrejas || []).find((x) => x.nome === c.igreja) || {};
    h += `<p class="sub" style="margin:6px 0">Base nível ${esc(info.base || "?")} · ${info.vagas || R.IGREJAS[c.igreja]} vaga(s) para Cultos.</p>
      <div class="lista"><div class="item" data-a="culto-naigreja"><span class="check ${c.na_igreja ? "on" : ""}"></span><div class="tx"><b>O Culto ocupa uma vaga</b><small>${c.grau < 2 ? "exige Grau 2 ou mais" : "cerimônia na Igreja com pelo menos 1 Discípulo"}</small></div></div>
      ${(L.igreja_beneficios || []).map((b) => `<div class="item ${ig && c.grau >= b.grau ? "" : "bloq"}" style="display:block"><b>Grau ${b.grau} · ${esc(b.nome)}</b><div style="font-size:14px;line-height:1.45;margin-top:3px">${esc(b.texto)}</div></div>`).join("")}</div>`;
  }
  h += `<p class="sub ajuda">${esc(L.igreja_nota || "")}</p>`;
  h += `<div class="lista" style="margin-top:8px">${campo("notas", "Anotações")}</div>
    <div class="linhabts so-ed" style="margin-top:8px"><button class="botao leve" data-a="culto-andar">Subiu de Andar</button></div>`;
  return h;
}
function passosGrau(c) {
  const L = CULTO();
  return `<div class="lista">${(L.graus || []).map((g) => `<div class="item ${g.grau <= c.grau ? "" : "bloq"}" data-a="culto-grau" data-k="${g.grau}"><span class="check ${g.grau <= c.grau ? "on" : ""}"></span>
    <div class="tx"><b>Grau ${g.grau} · ${esc(g.tamanho)}</b><small style="white-space:normal">${esc(g.objetivo)} → ${esc(g.poderes)}</small></div></div>`).join("")}</div>
    <p class="sub ajuda">O Culto cresce por objetivos cumpridos na mesa; o Mestre anota o Grau. Toque no Grau alcançado.</p>`;
}
A["culto-papel"] = (el) => mudar((s) => { s.culto.papel = el.dataset.k; });
A["culto-tema"] = (el) => mudar((s) => { s.culto.tema = s.culto.tema === el.dataset.k ? "" : el.dataset.k; });
A["culto-grau"] = (el) => mudar((s) => { const g = int(el.dataset.k, 1); s.culto.grau = s.culto.grau === g && g > 1 ? g - 1 : g; });
A["culto-abalado"] = () => {
  mudar((s) => { s.culto.abalado = !s.culto.abalado; });
  registrarDiario({ titulo: S.culto.abalado ? "⚠ Culto Abalado" : "✦ Culto restaurado", linhas: [S.culto.abalado ? "O Profeta quebrou uma regra do Culto e perdeu os poderes." : "O Profeta se redimiu diante dos seguidores."] });
};
A["culto-igreja"] = (el) => mudar((s) => { s.culto.igreja = el.dataset.k; if (!el.dataset.k) s.culto.na_igreja = false; });
A["culto-naigreja"] = () => {
  if (!S.culto.na_igreja && S.culto.grau < 2) { toast("Para entrar na Igreja, o Culto precisa estar no Grau 2 ou mais."); return; }
  mudar((s) => { s.culto.na_igreja = !s.culto.na_igreja; });
};
A["culto-txt"] = (el) => {
  const k = el.dataset.k, longo = ["crenca", "notas", "comunidades", "discipulos", "regra_faz", "regra_nunca"].includes(k);
  folha(esc(el.dataset.r), longo ? `<textarea id="ct" rows="5" style="width:100%">${esc(S.culto[k])}</textarea>` : `<input class="busca" id="ct" value="${esc(S.culto[k])}">`,
    `<button class="botao leve" data-a="fechar">Cancelar</button><button class="botao prim" data-a="culto-txt-ok" data-k="${k}">Salvar</button>`);
};
A["culto-txt-ok"] = (el) => { const v = $("#ct").value; fecharFolha(); mudar((s) => { s.culto[el.dataset.k] = el.dataset.k === "nome" || el.dataset.k === "divindade" || el.dataset.k === "profeta" || el.dataset.k === "local" ? v.trim() : v; }); };
A["culto-usar"] = (el) => {
  const k = el.dataset.k, c = S.culto, L = CULTO(), tema = (L.temas || {})[c.tema] || {};
  const pod = R.poderesCulto(c.grau, R.IGREJAS[c.igreja] && c.na_igreja && c.grau >= 5);
  const max = k === "preces" ? pod.preces : pod.milagres, campoU = k === "preces" ? "preces_usadas" : "milagres_usados";
  if (c.abalado) { toast("Culto Abalado: sem poderes até se redimir."); return; }
  if (c[campoU] >= max) { toast(k === "preces" ? "Sem Preces até o próximo descanso longo." : "Sem Milagres neste Andar."); return; }
  mudar((s) => { s.culto[campoU] += 1; });
  const txt = k === "preces" ? tema.prece : tema.milagre, nome = k === "preces" ? "🙏 Prece" : "✨ Milagre";
  const linhas = [esc(txt || ""), `<span class="sub">${max - S.culto[campoU]}/${max} restante(s)${k === "milagres" ? ` neste Andar · DT ${R.dtMilagre(C.a, C.nv)} se pedir teste` : " até o descanso longo"}.</span>`];
  registrarDiario({ titulo: `${nome} · ${esc(c.tema)}`, linhas });
  mostrarRolagem(`${nome} · ${esc(c.tema)}`, linhas);
};
A["culto-recup"] = () => mudar((s) => { s.culto.preces_usadas = 0; s.culto.milagres_usados = 0; });
A["culto-andar"] = () => folha("Subiu de Andar", `<p>${esc(CULTO().andar || "")}</p>`,
  `<button class="botao leve" data-a="fechar">Cancelar</button><button class="botao prim" data-a="culto-andar-ok">Recomeçar no Grau 1</button>`);
A["culto-andar-ok"] = () => {
  fecharFolha();
  mudar((s) => Object.assign(s.culto, { grau: 1, local: "", discipulos: "", comunidades: "", igreja: "", na_igreja: false, preces_usadas: 0, milagres_usados: 0 }));
  registrarDiario({ titulo: "✦ Culto no Andar novo", linhas: ["O Culto recomeça no Grau 1; Tema e regras continuam."] });
};
