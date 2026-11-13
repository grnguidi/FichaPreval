// ----- menu e fichas
A["menu"] = () => {
  folha("Menu", `<div class="lista">
    ${S ? `<div class="item" data-a="exportar"><div class="tx"><b>Exportar ficha (.json)</b><small>Para abrir no programa de PC ou guardar uma cópia</small></div></div>` : ""}
    <div class="item" data-a="importar"><div class="tx"><b>Abrir arquivo .json</b><small>Ficha salva pelo programa de PC</small></div></div>
    <div class="item" data-a="nova"><div class="tx"><b>Nova ficha</b><small>Criação rápida</small></div></div>
    <div class="item" data-a="lista"><div class="tx"><b>Trocar de ficha</b><small>${Object.keys(banco.fichas).length} ficha(s) neste aparelho</small></div></div>
    ${S ? `<div class="item" data-a="modo"><div class="tx"><b>${banco.modo === "edicao" ? "⚔ Ir para o Modo Jogo" : "✎ Ir para o Modo Edição"}</b><small>${banco.modo === "edicao" ? "Usar a ficha na mesa" : "Subir de nível, escolher talentos, armas e encantamentos"}</small></div></div>` : ""}
    ${sessao.ativa && S ? `<div class="item" data-a="levar-app"><div class="tx"><b>📲 Levar esta ficha de volta ao app</b><small>Vida, Mana, Vigor e condições de agora vão para o app instalado (substitui a ficha de mesmo nome)</small></div></div>` : ""}
    ${sessao.ativa ? `<div class="item" data-a="sessao-nome"><div class="tx"><b>🛡 Sessão do mestre</b><small>Você está como “${esc(sessao.id || "—")}” · toque para trocar o nome</small></div></div>` : ""}
    ${S ? `<div class="item" data-a="ident"><div class="tx"><b>Nome, player e espécie</b></div></div>` : ""}
    ${S ? `<div class="item" data-a="diario"><div class="tx"><b>📜 Diário de rolagens</b><small>Guardado com a ficha</small></div></div>` : ""}
    ${S ? `<div class="item" data-a="imprimir"><div class="tx"><b>🖨 Imprimir / salvar PDF</b><small>A ficha inteira em folhas A4</small></div></div>` : ""}
    <div class="item" data-a="tema"><div class="tx"><b>${banco.tema === "noite" ? "☀ Modo diurno" : "☾ Modo noturno"}</b></div></div>
    ${S ? `<div class="item" data-a="excluir"><div class="tx"><b class="erro">Excluir esta ficha do aparelho</b></div></div>` : ""}</div>`);
};
A["tema"] = () => { banco.tema = banco.tema === "noite" ? "dia" : "noite"; gravarLocal(); fecharFolha(); render(); };
A["lista"] = () => { fecharFolha(); S = null; banco.atual = null; gravarLocal(); render(); };
A["abrir"] = (el) => abrirFicha(el.dataset.id);
function abrirFicha(id, modo = "jogo") { S = normalizar(banco.fichas[id]); banco.atual = id; banco.modo = modo; gravarLocal(); aba = "ficha"; render(); }
A["exportar"] = async () => {
  const nome = (S.identidade.nome || "ficha").trim().replace(/\s+/g, "_") + ".json";
  const copia = Object.assign({}, S); delete copia._salvo;
  const texto = JSON.stringify(copia, null, 1);
  fecharFolha();
  try {
    const dl = window.claude && window.claude.use ? await window.claude.use("downloads") : null;
    if (dl) { await dl.save({ filename: nome, data: new Blob([texto], { type: "application/json" }) }); return; }
  } catch (e) { /* cai para o download comum */ }
  try {
    const url = URL.createObjectURL(new Blob([texto], { type: "application/json" }));
    const a = document.createElement("a"); a.href = url; a.download = nome; document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 4000);
    toast(`Exportado: ${esc(nome)}`);
  } catch (e) { toast("Não consegui exportar neste navegador."); }
};
A["importar"] = () => { fecharFolha(); $("#arquivo").click(); };
A["excluir"] = () => folha("Excluir ficha?", `<p>Isto apaga <b>${esc(S.identidade.nome || "esta ficha")}</b> deste aparelho. Se quiser guardar, exporte antes.</p>`,
  `<button class="botao leve" data-a="fechar">Cancelar</button><button class="botao prim" data-a="excluir-ok">Excluir</button>`);
A["excluir-ok"] = () => { const id = banco.atual; delete banco.fichas[id]; banco.atual = null; S = null; gravarLocal(); enviarNuvem(id); fecharFolha(); render(); };
A["ident"] = () => folha("Identidade", `<label class="campo"><span>Nome</span><input id="i-nome" value="${esc(S.identidade.nome)}"></label>
  <label class="campo"><span>Player</span><input id="i-player" value="${esc(S.identidade.player)}"></label>
  <label class="campo"><span>Espécie</span><input id="i-esp" value="${esc(S.identidade.especie)}"></label>
  <label class="campo"><span>Sonho</span><input id="i-sonho" value="${esc(S.identidade.sonho)}"></label>
  <label class="campo"><span>Nível de Guilda</span><input id="i-guilda" value="${esc(S.identidade.guilda || "")}"></label>`,
`<button class="botao leve" data-a="fechar">Cancelar</button><button class="botao prim" data-a="ident-ok">Salvar</button>`);
A["ident-ok"] = () => { const v = (id) => $(id).value; const n = v("#i-nome"), p = v("#i-player"), e = v("#i-esp"), so = v("#i-sonho"), gu = v("#i-guilda"); fecharFolha(); mudar((s) => Object.assign(s.identidade, { nome: n, player: p, especie: e, sonho: so, guilda: gu })); };
A["nova-rapida"] = () => {
  const opts = (k) => [""].concat(R.VALORES_INICIAIS).map((x) => `<option>${x}</option>`).join("");
  const nomes = [""].concat(R.ATRIBUTOS.map((k) => R.NOMES_ATR[k])).map((n) => `<option>${n}</option>`).join("");
  folha("Nova ficha", `<label class="campo"><span>Nome do personagem</span><input id="n-nome"></label>
    <label class="campo"><span>Player</span><input id="n-player"></label>
    <label class="campo"><span>Espécie</span><input id="n-esp"></label>
    <div class="secao">Atributos iniciais</div><p class="sub" style="margin-top:-4px">Use cada valor uma vez: 16, 14, 12, 11, 10, 9, 8, 7.</p>
    <div class="grade g2">${R.ATRIBUTOS.map((k) => `<label class="campo" style="margin:2px 0"><span>${R.NOMES_ATR[k]}</span><select data-ini="${k}">${opts(k)}</select></label>`).join("")}</div>
    <div class="secao">Espécie (par numérico)</div>
    <div class="grade g3"><label class="campo"><span>Bônus em</span><select id="n-bon">${nomes}</select></label><label class="campo"><span>Prejuízo em</span><select id="n-pre">${nomes}</select></label>
    <label class="campo"><span>Valor</span><select id="n-val">${[0, 1, 2, 3, 4, 5].map((x) => `<option>${x}</option>`).join("")}</select></label></div>
    <label class="campo" style="display:flex;align-items:center;gap:10px"><input type="checkbox" id="n-sem" style="width:24px;height:24px"> <span style="margin:0">☠ Sem alma (+2 pontos de atributo por nível)</span></label>
    <p class="erro" id="n-erro"></p>`, `<button class="botao leve" data-a="fechar">Cancelar</button><button class="botao prim" data-a="nova-ok">Criar ficha</button>`, (c) => {
    c.querySelectorAll("[data-ini]").forEach((s) => s.addEventListener("change", () => {
      const usados = [...c.querySelectorAll("[data-ini]")].map((x) => x.value).filter(Boolean);
      c.querySelectorAll("[data-ini]").forEach((x) => [...x.options].forEach((o) => { o.disabled = o.value && o.value !== x.value && usados.includes(o.value); }));
    }));
  });
};
A["nova-ok"] = () => {
  const c = $("#folha-corpo"), ini = {};
  c.querySelectorAll("[data-ini]").forEach((s) => { ini[s.dataset.ini] = s.value; });
  const vals = Object.values(ini);
  if (!$("#n-nome").value.trim()) { $("#n-erro").textContent = "Dê um nome ao personagem."; return; }
  if (vals.includes("") || new Set(vals).size !== 8) { $("#n-erro").textContent = "Atribua os oito valores, cada um uma vez."; return; }
  const val = int($("#n-val").value), kb = R.ATR_POR_NOME[$("#n-bon").value], kp = R.ATR_POR_NOME[$("#n-pre").value];
  if (val && (!kb || !kp || kb === kp)) { $("#n-erro").textContent = "Escolha atributos diferentes para o bônus e o prejuízo."; return; }
  const s = novoEstado();
  s.identidade.nome = $("#n-nome").value.trim(); s.identidade.player = $("#n-player").value.trim(); s.identidade.especie = $("#n-esp").value.trim();
  s.sem_alma = $("#n-sem").checked;
  for (const k of R.ATRIBUTOS) { s.atributos[k].inicial = ini[k]; s.atributos[k].especie = String(val ? (k === kb ? val : k === kp ? -val : 0) : 0); }
  const id = "ficha-" + Date.now().toString(36);
  banco.fichas[id] = s; banco.atual = id; fecharFolha(); abrirFicha(id, "edicao"); salvar();
  toast("Ficha criada. Ela fica guardada neste aparelho.");
};
function importarArquivo(arq) {
  const rd = new FileReader();
  rd.onload = () => {
    try {
      const bruto = JSON.parse(rd.result);
      if (bruto && bruto.prevalecentes_backup && bruto.fichas) {   // backup de todas as fichas (veja "backup-todas")
        let n = 0;
        for (const f of Object.values(bruto.fichas)) {
          const s = normalizar(f); if (!s.identidade) continue;
          const nome = (s.identidade.nome || "").trim();
          const id = (nome && Object.keys(banco.fichas).find((k) => (banco.fichas[k].identidade.nome || "").trim() === nome)) || "ficha-" + Date.now().toString(36) + "-" + (n++);
          banco.fichas[id] = s;
        }
        gravarLocal(); render(); toast(`Backup restaurado: <b>${Object.keys(bruto.fichas).length}</b> ficha(s).`);
        return;
      }
      const s = normalizar(bruto);
      if (!s.identidade) throw new Error();
      const id = "ficha-" + Date.now().toString(36);
      banco.fichas[id] = s; banco.atual = id; abrirFicha(id); salvar();
      toast(`Ficha <b>${esc(s.identidade.nome || "sem nome")}</b> aberta e guardada neste aparelho.`);
    } catch (e) { toast("Esse arquivo não parece ser uma ficha de Prevalecentes."); }
  };
  rd.readAsText(arq);
}


