// ------------------------------------------------------------------ Alma
const almaDT = () => { const k = S.alma.atr === "FE" ? "FE" : "INT"; return 10 + C.d.bc[k] + C.d.n3 + C.ef.dt_alma; };
function infoHab(h) {
  const ne = R.almaNivelEfetivo(C.d.alma_nivel, h.ajustes || [], Math.max(1, (h.cats || []).length));
  return { ne, valor: h.tabela ? R.almaValor(h.tabela, ne) : "", dt: almaDT() + R.almaDtAjuste(h.ajustes || []) };
}
function pAlma() {
  if (S.sem_alma) return secao("Alma") + `<div class="vazio-msg">Este personagem joga sem Alma: +2 pontos de atributo a cada nível.</div>`;
  const d = C.d, al = S.alma, tot = d.alma_usos, rest = al.restantes === "" || al.restantes == null ? tot : int(al.restantes, tot);
  const ativas = al.habilidades.filter((h) => h.tipo === "Ativo").length;
  let h = secao("Alma") + `<div class="cartao" style="padding:12px 14px" data-a="alma-ident"><b style="font-size:20px;color:var(--vinho)">${esc(al.nome || "Alma sem nome")}</b>
    <div class="sub" style="margin-top:4px">${esc(al.historia || "Quem foi, por que está com você, que habilidade tinha em vida.")}</div><small class="so-ed" style="color:var(--vinho)">✎ editar</small></div>
    <div class="grade g3 g4m" style="margin-top:10px">${caixa("Nível da alma", d.alma_nivel, "nível ÷ 3")}${caixa("DT", almaDT(), al.atr === "FE" ? "Desejo (Fé)" : "Feitiçaria (INT)")}
    ${caixa("Usos", `${rest}/${tot}`, "por descanso longo")}${caixa("Ativas", `${ativas}/${d.alma_ativas}`, "liberadas")}</div>
    <div class="linhabts"><button class="botao prim" data-a="alma-usar">Gastar 1 uso</button><button class="botao leve" data-a="alma-recup">↺ Recarregar</button></div>`;
  h += secao("Habilidades") + (al.habilidades.length ? al.habilidades.map((x, i) => {
    const inf = infoHab(x);
    return `<div class="cartao hab"><div class="topo-hab"><b>${esc(x.nome || "Habilidade sem nome")}</b><span class="chip ${x.tipo === "Ativo" ? "on" : ""}" style="margin:0">${x.tipo || "—"}</span></div>
      <small class="sub">${esc((x.cats || []).join(" + ") || "categoria livre")}${x.execucao ? ` · ação ${esc(x.execucao)}` : ""}${x.tipo === "Ativo" && (x.cats || []).some((c) => c !== "Interlúdio") ? ` · DT ${inf.dt}` : ""}</small>
      ${x.tabela ? `<p style="margin:6px 0">${esc(x.tabela)}: <b>${esc(inf.valor)}</b> <span class="sub">(nível efetivo ${inf.ne})</span></p>` : ""}
      ${x.efeito ? `<p class="desc" style="margin:4px 0">${esc(x.efeito)}</p>` : ""}
      <div class="linhabts">${x.tipo === "Ativo" ? `<button class="botao prim" data-a="hab-usar" data-i="${i}">${x.tabela && x.tabela.startsWith("Dano") ? "🎲 Usar e rolar" : "✓ Usar"}</button>` : ""}<button class="botao leve so-ed" data-a="hab-editar" data-i="${i}">✎ Editar</button></div></div>`;
  }).join("") : `<div class="vazio-msg">Nenhuma habilidade ainda.</div>`)
    + `<div class="linhabts so-ed"><button class="botao prim" data-a="hab-editar" data-i="-1" ${al.habilidades.length >= 6 ? "disabled" : ""}>＋ Habilidade</button></div>
    <p class="sub">Toda Alma começa com 1 passiva e 1 ativa; novas ativas nos níveis 10, 20 e 30. A Alma nunca cura. O valor vem da Tabela de valores do livro, no nível da alma com os ajustes da habilidade.</p>`;
  return h;
}
A["alma-ident"] = () => {
  if (banco.modo !== "edicao") return;
  folha("A Alma", `<label class="campo"><span>Nome</span><input id="al-n" value="${esc(S.alma.nome)}"></label>
    <label class="campo"><span>DT usa</span><select id="al-a"><option value="INT" ${S.alma.atr !== "FE" ? "selected" : ""}>Inteligência (Feitiçaria)</option><option value="FE" ${S.alma.atr === "FE" ? "selected" : ""}>Fé (Desejo)</option></select></label>
    <label class="campo"><span>Quem foi, por que está com você, que habilidade tinha em vida</span><textarea id="al-h" rows="5" style="width:100%">${esc(S.alma.historia)}</textarea></label>`,
  `<button class="botao leve" data-a="fechar">Cancelar</button><button class="botao prim" data-a="alma-ident-ok">Salvar</button>`);
};
A["alma-ident-ok"] = () => { const n = $("#al-n").value.trim(), a = $("#al-a").value, h = $("#al-h").value; fecharFolha(); mudar((s) => { s.alma.nome = n; s.alma.atr = a; s.alma.historia = h; }); };
A["hab-editar"] = (el) => {
  const i = int(el.dataset.i, -1), x = Object.assign({ nome: "", efeito: "", tipo: "Ativo", cats: ["Dano"], tabela: "", ajustes: [], execucao: "Comum" }, S.alma.habilidades[i] || {});
  const op = (v, sel) => `<option ${sel ? "selected" : ""}>${esc(v)}</option>`;
  folha(i < 0 ? "Nova habilidade" : "Habilidade", `<label class="campo"><span>Nome</span><input id="hb-n" value="${esc(x.nome)}"></label>
    <div class="grade g2"><label class="campo"><span>Tipo</span><select id="hb-t">${op("Ativo", x.tipo === "Ativo")}${op("Passivo", x.tipo === "Passivo")}</select></label>
    <label class="campo"><span>Execução</span><select id="hb-e">${R.ALMA_EXECUCAO.map((e) => op(e, x.execucao === e)).join("")}</select></label></div>
    <div class="secao">Categorias</div><div>${R.ALMA_CATEGORIAS.map((c) => `<label class="chip"><input type="checkbox" class="hb-c" value="${c}" ${(x.cats || []).includes(c) ? "checked" : ""}> ${c}</label>`).join("")}</div>
    <p class="sub">Cada categoria a mais (mesclar) custa 1 nível.</p>
    <label class="campo"><span>Valor da tabela</span><select id="hb-tab"><option value="">— nenhum (descrever no efeito) —</option>${Object.keys(R.ALMA_TABELAS).map((t) => op(t, x.tabela === t)).join("")}</select></label>
    <div class="secao">Ajustes (facilitar e dificultar)</div><div class="lista">${R.ALMA_AJUSTES.map(([v, t]) =>
      `<label class="item" style="cursor:pointer"><input type="checkbox" class="hb-a" value="${esc(t)}" ${(x.ajustes || []).includes(t) ? "checked" : ""} style="width:20px;height:20px;margin-right:10px"><div class="tx"><b>${esc(t)}</b></div><span class="num">${v > 0 ? "+" : ""}${v}</span></label>`).join("")}</div>
    <p class="meta" id="hb-prev"></p>
    <label class="campo"><span>Efeito (alcance, alvo, duração, detalhes combinados com o mestre)</span><textarea id="hb-ef" rows="4" style="width:100%">${esc(x.efeito)}</textarea></label>`,
  `${i >= 0 ? `<button class="botao leve" data-a="hab-rem" data-i="${i}">Remover</button>` : `<button class="botao leve" data-a="fechar">Cancelar</button>`}<button class="botao prim" data-a="hab-ok" data-i="${i}">Salvar</button>`, (c) => {
    const prev = () => {
      const cats = [...c.querySelectorAll(".hb-c:checked")].map((y) => y.value), aj = [...c.querySelectorAll(".hb-a:checked")].map((y) => y.value), tab = $("#hb-tab").value;
      const ne = R.almaNivelEfetivo(C.d.alma_nivel, aj, Math.max(1, cats.length));
      $("#hb-prev").innerHTML = `Nível da alma ${C.d.alma_nivel} → nível efetivo <b>${ne}</b>${tab ? ` · ${esc(tab)}: <b>${esc(R.almaValor(tab, ne))}</b>` : ""} · DT ${almaDT() + R.almaDtAjuste(aj)}`;
    };
    c.querySelectorAll("input,select").forEach((y) => y.addEventListener("change", prev)); prev();
  });
};
A["hab-ok"] = (el) => {
  const i = int(el.dataset.i, -1), c = $("#folha-corpo");
  const x = { nome: $("#hb-n").value.trim(), tipo: $("#hb-t").value, execucao: $("#hb-e").value, tabela: $("#hb-tab").value, efeito: $("#hb-ef").value.trim(),
    cats: [...c.querySelectorAll(".hb-c:checked")].map((y) => y.value), ajustes: [...c.querySelectorAll(".hb-a:checked")].map((y) => y.value) };
  fecharFolha(); mudar((s) => { if (i < 0) s.alma.habilidades.push(x); else s.alma.habilidades[i] = x; });
};
A["hab-rem"] = (el) => { const i = int(el.dataset.i); fecharFolha(); mudar((s) => { s.alma.habilidades.splice(i, 1); }); };
A["hab-usar"] = (el) => {
  const x = S.alma.habilidades[int(el.dataset.i)], tot = C.d.alma_usos, rest = S.alma.restantes === "" || S.alma.restantes == null ? tot : int(S.alma.restantes, tot);
  if (rest <= 0) { toast("A Alma não tem usos restantes. Recarrega no descanso longo."); return; }
  const inf = infoHab(x), linhas = [];
  S.alma.restantes = String(rest - 1);
  if (x.tabela && x.tabela.startsWith("Dano")) {
    const expr = inf.valor.replace(/\s*\(.*\)/, ""), [tot2, partes] = R.rolarExpr(expr, rng);
    linhas.push(txtDano(tot2, partes) + (inf.valor.includes("desvantagem") ? ` <span class="sub">(com desvantagem)</span>` : "") + (x.tabela.includes("múltiplos") ? " em cada alvo" : ""));
  } else if (x.tabela) linhas.push(`${esc(x.tabela)}: <b>${esc(inf.valor)}</b>`);
  if ((x.cats || []).some((c) => c !== "Interlúdio")) linhas.push(`DT: <b>${inf.dt}</b>`);
  if (x.efeito) linhas.push(esc(x.efeito));
  linhas.push(`<span class="sub">Usos da Alma: ${rest - 1}/${tot}.</span>`);
  const aviso = marcarAcao(x.execucao);
  if (aviso) linhas.push(`<span class="erro">${aviso}</span>`);
  salvar(); render();
  mostrarRolagem(`☽ ${esc(x.nome || "Habilidade da Alma")}`, linhas);
};

