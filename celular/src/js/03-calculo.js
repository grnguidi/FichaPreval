// ------------------------------------------------------------------ cálculo (porta do recalc do PC)
const nivel = () => Math.max(1, Math.min(R.NIVEL_MAX, int(S.identidade.nivel, 1)));
const metasConcluidas = () => R.recompensaMetas(S.meta.concluidas).talentos;
const slotValido = (sl) => !sl.startsWith("meta") || int(sl.slice(4)) <= metasConcluidas();
const talentos = () => new Set(Object.entries(S.talentos).filter(([sl, n]) => n && slotValido(sl)).map(([, n]) => n));
const armasEq = () => S.armas.map((a) => a.grupo).filter((g) => ARMAS[g]);
function bonusTalismas(nv, tal) {
  const out = {};
  S.talismas.slice(0, R.slotsTalismas(nv, tal)).forEach((t) => {
    const b = (TALISMA[t.nome] || {}).bonus || {};
    for (const [k, v] of Object.entries(b)) out[k] = (out[k] || 0) + v;
  });
  return out;
}
function protecao(tipo) {
  const lista = tipo === "armadura" ? D.armaduras : D.escudos;
  return lista.find((x) => x.nome === S.equip[tipo]) || null;
}
const custoEnc = (e, v, escolha) => R.descontoMatricula(escolha || C.escolha, e.categoria, v ? R.custoMana(v) : null, e.espaco);
const condMax = (n) => int((S.condicoes[n] || {}).max, 100) + ((C && C.escolha && C.escolha.cond_extra[n]) || 0);
function calcular() {
  const nv = nivel(), tal = talentos();
  const tb = bonusTalismas(nv, tal);
  const a = {};
  for (const k of R.ATRIBUTOS) {
    const x = S.atributos[k];
    a[k] = int(x.inicial) + int(x.niveis) + int(x.especie) + int(x.bonus) + (tb[k] || 0);
    if (S.manual[k] != null) a[k] = int(S.manual[k]);
  }
  const nVida = R.curva(a.VIT) + (tal.has("Vida Dura") ? 3 : 0);
  const soma = S.vida.modo === "media" ? 7 * nVida : (S.vida.rolagens || []).slice(0, nVida).reduce((x, y) => x + y, 0);
  const arm = protecao("armadura"), esc = protecao("escudo");
  const d = R.derivadas(a, nv, tal, soma, arm ? arm.ca : 0, esc ? esc.ca : 0, int(S.equip.ca_extra));
  const ativos = new Set(S.talentos_ativos.filter((n) => tal.has(n) && (R.EFEITOS_TALENTOS[n] || {}).tipo === "sit"));
  const ef = R.efeitosTalentos(tal, ativos, S.equip.armadura || "");
  d.ca = Math.max(10, Math.min(25, d.ca + ef.ca)); d.movimento += ef.mov; d.iniciativa_bonus += ef.iniciativa;
  d.descoberta += ef.descoberta; d.contra_encant += ef.contra;
  d.vida_auto = d.vida; d.mana_auto = d.mana;
  if (S.manual.vida != null) d.vida = int(S.manual.vida);
  if (S.manual.mana != null) d.mana = int(S.manual.mana);
  d.carga += R.cargaExtraItens(S.inventario || [], ITENS);   // Mochila: +5
  let carga = R.pesoInventario(S.inventario || []) + R.pesoPecasSet(S.set || {});
  carga += (arm ? arm.peso : 0) + (esc ? esc.peso : 0) - (tal.has("Veterano de Armadura") && arm ? 2 : 0);
  carga += S.talismas.filter((t) => t.nome).length;
  S.armas.forEach((w) => { const ar = ARMAS[w.grupo]; if (ar) { const l = ar.tabela.find((x) => x.nivel === int(w.nivel, 1)); if (l) carga += l.espaco; } });
  const limLent = tal.has("Mochileiro") ? 0.6 : 0.5;
  const lentidao = carga > 0 && carga >= d.carga * limLent, exaustao = carga > 0 && d.carga - carga <= 10;
  const disp = R.pontosDeNivel(nv, S.sem_alma) + R.recompensaMetas(S.meta.concluidas).pontos;
  const gastos = R.ATRIBUTOS.reduce((s, k) => s + int(S.atributos[k].niveis), 0);
  const ini = R.ATRIBUTOS.map((k) => int(S.atributos[k].inicial)).filter(Boolean);
  const treinadas = new Set(S.pericias);
  const escolha = R.efeitosEscolhas(S.talentos, S.talentos_escolha || {});
  const C = { escolha, nv, tal, a, tb, d, ef, ativos, nVida, soma, arm, esc, carga, lentidao, exaustao, mov: lentidao ? Math.min(6, d.movimento) : d.movimento, disp, gastos, resto: disp - gastos, treinadas, avisos: [] };
  // avisos
  const av = C.avisos;
  for (const k of Object.keys(S.manual)) av.push(["info", `${R.NOMES_ATR[k] || (k === "vida" ? "Vida máx." : "Mana máx.")} com valor manual (${S.manual[k]}).`]);
  if (C.resto > 0) av.push(["erro", `Faltam ${C.resto} pontos de atributo para distribuir.`]);
  for (const n of escolha.pendentes) av.push(["erro", `Talento ${n}: escolha ${R.ROTULO_ESCOLHA[R.ESCOLHA_TALENTO[n]].toLowerCase()} (aba Talentos).`]);
  if (C.resto < 0) av.push(["erro", `Você gastou ${-C.resto} pontos de atributo a mais.`]);
  const faltIni = R.VALORES_INICIAIS.filter((x) => !ini.includes(x));
  if (faltIni.length) av.push(["erro", `Distribuição inicial incompleta (faltam ${faltIni.join(", ")}).`]);
  if (S.vida.modo === "rolar" && (S.vida.rolagens || []).length < nVida) av.push(["erro", `Role ${nVida - S.vida.rolagens.length} dado(s) de vida novo(s).`]);
  if (treinadas.size > d.pericias_treinadas_max) av.push(["erro", `Perícias treinadas: ${treinadas.size} de ${d.pericias_treinadas_max}.`]);
  else if (treinadas.size < d.pericias_treinadas_max) av.push(["info", `Pode treinar mais ${d.pericias_treinadas_max - treinadas.size} perícia(s).`]);
  const usados = S.encantamentos.filter((x) => x.equipado && ENC[x.familia]).reduce((s, x) => s + custoEnc(ENC[x.familia], null, escolha)[1], 0);
  C.espUsados = usados;
  if (usados > d.espacos_encant) av.push(["erro", `Encantamentos equipados ocupam ${usados} de ${d.espacos_encant} espaços.`]);
  if (lentidao) av.push(["erro", `Carga ${carga} de ${d.carga}: Lentidão (movimento 6 m).`]);
  if (exaustao) av.push(["erro", "Carga: 10 ou menos espaços livres — Exaustão."]);
  const nTal = S.talismas.filter((t) => t.nome).length;
  if (nTal > d.talismas) av.push(["erro", `Talismãs: ${nTal} equipados, limite ${d.talismas}.`]);
  S.armas.forEach((w, i) => { const f = w.grupo && ARMAS[w.grupo] ? statusArma(C, w.grupo, int(w.nivel, 1)) : []; if (f.length) av.push(["erro", `Arma ${i + 1} (${w.grupo}): ${f.join(", ")}.`]); });
  for (const tipo of ["armadura", "escudo"]) { const it = protecao(tipo); if (it) { const m = statusProtecao(C, tipo, it); if (m.length) av.push(["erro", `${it.nome}: ${m.join(", ")}.`]); } }
  for (const sl of SLOTS) {
    const ativo = sl === "extra" ? tal.has("Versátil") : int(sl) <= nv;
    const nome = S.talentos[sl];
    if (nome && TAL[nome]) { const m = statusTal(C, TAL[nome], sl); if (m.length) av.push(["erro", `Talento ${nome}: ${m.join(", ")}.`]); }
    else if (ativo) av.push(["erro", `Talento do nível ${sl === "extra" ? "extra (Versátil)" : sl} não escolhido.`]);
  }
  for (const x of S.encantamentos) {
    const e = ENC[x.familia]; if (!e) continue;
    const prox = e.versoes.find((v) => !x.versoes.includes(v.nivel));
    if (prox && !R.statusVersao(prox, e.dominio, a, nv).length) av.push(["info", `${e.nome}: versão nível ${prox.nivel} já pode ser aprendida.`]);
  }
  return C;
}
function statusArma(C, grupo, nv, props = []) {
  const m = [];
  if (nv > C.d.max_nivel_arma) m.push(`nível de personagem ${2 * nv - 1}`);
  return m.concat(R.reqFalta(R.reqComProps(R.reqArma(ARMAS[grupo], nv), props), C.a));
}
function efeitoArma(w, nv) {
  const ar = ARMAS[w.grupo], l = ar.tabela.find((x) => x.nivel === nv) || ar.tabela[0];
  return R.efeitoProps(R.lerProps(w.props), R.danoComDados(l.dano, Math.floor(R.cap(C.a[ar.ataque]) / 30)), int(l.critico, 20));
}
const propsMax = (w) => { const ar = ARMAS[w.grupo]; if (!ar) return 0; const l = ar.tabela.find((x) => x.nivel === int(w.nivel, 1)) || ar.tabela[0]; return l.propriedades + (C.escolha.dominio[w.grupo] || 0); };
function statusProtecao(C, tipo, it) {
  const m = [], forca = Math.max(R.cap(C.a.FOR), R.cap(C.a.TEN));
  if (it.req && forca < it.req) m.push(`${it.req} de Força ou Tenacidade`);
  if (tipo === "armadura" && !S.equip.peitoral_set && C.nv < it.nivel) m.push(`nível ${it.nivel}`);
  if (tipo === "escudo") {
    if (armasEq().length >= 2) m.push("as duas mãos estão com armas");
    if (armasEq().includes("Lança-Arma")) m.push("Lança-Arma já tem escudo");
  }
  return m;
}
function statusTal(C, t, slot) {
  const meta = slot.startsWith("meta"), idx = SLOTS.indexOf(slot);
  let antes = new Set(SLOTS.slice(0, idx).map((s) => S.talentos[s]).filter(Boolean));
  if (slot === "extra" || meta) antes = new Set(SLOTS.slice(0, -1).filter((s) => int(s) <= C.nv).map((s) => S.talentos[s]).filter(Boolean));
  const outros = new Set(SLOTS.concat(META_SLOTS).filter((s) => s !== slot && slotValido(s)).map((s) => S.talentos[s]).filter(Boolean));
  const m = R.statusTalento(t, slot === "extra" ? 8 : meta ? C.nv : int(slot), antes, C.a, C.treinadas, armasEq(), outros);
  if (slot !== "extra" && !meta && int(slot) > C.nv) m.unshift(`slot do nível ${slot}`);
  return m;
}
const ordenar = (lista) => lista.filter((x) => !x.motivo.length).concat(lista.filter((x) => x.motivo.length));

