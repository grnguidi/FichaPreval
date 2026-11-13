// ------------------------------------------------------------------ criação passo a passo (capítulo "Criando seu Personagem")
const PASSOS = [
  ["Seu Sonho", "Antes de qualquer número, decida por que este personagem busca a Intérprete. Personagem novo entra no nível do grupo, com todos os pontos."],
  ["A Alma", "Escolha a Alma que o personagem carrega: começa com uma habilidade passiva e uma ativa. Sem Alma, ganha +2 pontos de atributo por nível."],
  ["A Espécie", "Duas vantagens e duas desvantagens: um par numérico (bônus e prejuízo de mesmo valor, 1 a 5) e um par descritivo."],
  ["Atributos", "Distribua 16, 14, 12, 11, 10, 9, 8 e 7 pensando no que o personagem faz."],
  ["Perícias e equipamento", "1 perícia de ataque e 5 fora de combate, mais uma a cada 10 de INT ou MEN. A arma inicial respeita os requisitos do nível 1."],
  ["Talentos", "Um talento a cada nível par. Eles ficam ativos o tempo todo e não podem ser trocados."],
  ["Vínculos", "Uma ligação com alguém do grupo e uma pessoa no mundo. Dá para já escolher o Caminho da Meta de Vida."],
  ["Resumo", "Confira antes de criar. Você pode voltar a qualquer passo."],
];
let rasc = null, passo = 0;
const RASC0 = () => ({ nome: "", player: "", sonho: "", nivel: 1, sem_alma: false, alma_nome: "", alma_atr: "INT", alma_hist: "", pas_nome: "", pas_ef: "", atv_nome: "", atv_ef: "",
  especie: "", esp_bon: "", esp_pre: "", esp_val: 0, esp_notas: "", ini: {}, pericias: [], per_atk: "Luta", arma: "", vinc_grupo: "", vinc_mundo: "", caminho: "" });
function attrsRasc() {
  const a = {};
  for (const k of R.ATRIBUTOS) a[k] = int(rasc.ini[k]) + (rasc.esp_val ? (R.ATR_POR_NOME[rasc.esp_bon] === k ? rasc.esp_val : R.ATR_POR_NOME[rasc.esp_pre] === k ? -rasc.esp_val : 0) : 0);
  return a;
}
const limPericias = () => { const a = attrsRasc(); return 5 + Math.floor(Math.max(R.cap(a.INT), R.cap(a.MEN)) / 10); };
function corpoPasso() {
  const v = (x) => esc(String(x == null ? "" : x)), opt = (val, sel, txt) => `<option value="${v(val)}" ${sel ? "selected" : ""}>${v(txt == null ? val : txt)}</option>`;
  const nomesAtr = [""].concat(R.ATRIBUTOS.map((k) => R.NOMES_ATR[k]));
  switch (passo) {
    case 0: return `<label class="campo"><span>Nome do personagem</span><input id="wz-nome" value="${v(rasc.nome)}"></label>
      <label class="campo"><span>Player</span><input id="wz-player" value="${v(rasc.player)}"></label>
      <label class="campo"><span>Sonho</span><textarea id="wz-sonho" rows="3" style="width:100%">${v(rasc.sonho)}</textarea></label>
      <label class="campo"><span>Nível inicial</span><select id="wz-nivel">${[...Array(R.NIVEL_MAX)].map((_, i) => opt(i + 1, rasc.nivel === i + 1, `Nível ${i + 1}`)).join("")}</select></label>
      <p class="sub"><a href="#" data-a="nova-rapida" style="color:var(--vinho)">Prefere a criação rápida, numa tela só?</a></p>`;
    case 1: return `<label class="campo" style="display:flex;align-items:center;gap:10px"><input type="checkbox" id="wz-sem" ${rasc.sem_alma ? "checked" : ""} style="width:24px;height:24px"><span style="margin:0">☠ Jogar sem Alma (+2 pontos de atributo por nível)</span></label>
      <div id="wz-alma" ${rasc.sem_alma ? 'style="display:none"' : ""}><label class="campo"><span>Nome da Alma</span><input id="wz-an" value="${v(rasc.alma_nome)}"></label>
      <label class="campo"><span>DT da Alma usa</span><select id="wz-aa">${opt("INT", rasc.alma_atr !== "FE", "Inteligência (Feitiçaria)")}${opt("FE", rasc.alma_atr === "FE", "Fé (Desejo)")}</select></label>
      <label class="campo"><span>Quem foi, por que está com você, que habilidade tinha em vida</span><textarea id="wz-ah" rows="3" style="width:100%">${v(rasc.alma_hist)}</textarea></label>
      <div class="grade g2"><label class="campo"><span>Passiva</span><input id="wz-pn" value="${v(rasc.pas_nome)}" placeholder="nome"></label><label class="campo"><span>Efeito da passiva</span><input id="wz-pe" value="${v(rasc.pas_ef)}"></label>
      <label class="campo"><span>Ativa</span><input id="wz-tn" value="${v(rasc.atv_nome)}" placeholder="nome"></label><label class="campo"><span>Efeito da ativa</span><input id="wz-te" value="${v(rasc.atv_ef)}"></label></div>
      <p class="sub">Depois, na aba Alma, o montador calcula dano, área e bônus pela tabela do livro.</p></div>`;
    case 2: return `<label class="campo"><span>Espécie</span><input id="wz-esp" value="${v(rasc.especie)}"></label>
      <div class="grade g3"><label class="campo"><span>Bônus em</span><select id="wz-bon">${nomesAtr.map((n) => opt(n, rasc.esp_bon === n)).join("")}</select></label>
      <label class="campo"><span>Prejuízo em</span><select id="wz-pre">${nomesAtr.map((n) => opt(n, rasc.esp_pre === n)).join("")}</select></label>
      <label class="campo"><span>Valor</span><select id="wz-val">${[0, 1, 2, 3, 4, 5].map((n) => opt(n, rasc.esp_val === n)).join("")}</select></label></div>
      <label class="campo"><span>Par descritivo (vantagem e desvantagem)</span><textarea id="wz-notas" rows="3" style="width:100%">${v(rasc.esp_notas)}</textarea></label>`;
    case 3: return `<div class="grade g2">${R.ATRIBUTOS.map((k) => `<label class="campo" style="margin:2px 0"><span>${R.NOMES_ATR[k]}</span><select data-ini="${k}">${[""].concat(R.VALORES_INICIAIS).map((x) => opt(x, String(rasc.ini[k] || "") === String(x))).join("")}</select></label>`).join("")}</div>
      <p class="sub">${rasc.esp_val ? `Espécie: +${rasc.esp_val} em ${v(rasc.esp_bon)}, −${rasc.esp_val} em ${v(rasc.esp_pre)}.` : ""} Os pontos dos níveis acima do 1 você distribui na Ficha depois de criar.</p>`;
    case 4: {
      const a = attrsRasc();
      return `<p class="meta">Escolha até <b>${limPericias()}</b> perícias fora de combate.</p><div class="lista">${R.PERICIAS.map(([n, at, tr]) => `<label class="item" style="cursor:pointer"><input type="checkbox" class="wz-per" value="${v(n)}" ${rasc.pericias.includes(n) ? "checked" : ""} style="width:20px;height:20px;margin-right:10px"><div class="tx"><b>${v(n)}${tr ? " •" : ""}</b><small>${at ? at.join("/") : "à escolha"}</small></div></label>`).join("")}</div>
        <label class="campo"><span>Perícia de ataque treinada</span><select id="wz-atk">${R.PERICIAS_ATAQUE.map(([n]) => opt(n, rasc.per_atk === n)).join("")}</select></label>
        <label class="campo"><span>Arma inicial</span><select id="wz-arma">${opt("", !rasc.arma, "— nenhuma —")}${D.armas.map((w) => { const f = R.reqFalta(R.reqArma(w, 1), a); return `<option value="${v(w.nome)}" ${rasc.arma === w.nome ? "selected" : ""} ${f.length ? "disabled" : ""}>${v(w.nome)}${f.length ? ` — falta ${v(f.join(", "))}` : ""}</option>`; }).join("")}</select></label>
        <p class="sub">Com cajado ou selo, escolha 3 encantamentos de nível 1 no Grimório depois de criar.</p>`;
    }
    case 5: { const n = Math.floor(rasc.nivel / 2); return `<p>${n ? `No nível ${rasc.nivel} você escolhe <b>${n}</b> talento(s), na aba Talentos, depois de criar a ficha.` : "No nível 1 ainda não há talento: o primeiro vem no nível 2."}</p>`; }
    case 6: return `<label class="campo"><span>Vínculo com o grupo</span><input id="wz-vg" value="${v(rasc.vinc_grupo)}"></label>
      <label class="campo"><span>Vínculo com o mundo</span><input id="wz-vm" value="${v(rasc.vinc_mundo)}"></label>
      <label class="campo"><span>Caminho da Meta de Vida</span><select id="wz-cam">${opt("", !rasc.caminho, "— decidir depois —")}${R.CAMINHOS.map(([n, pp]) => opt(n, rasc.caminho === n, `${n} (${pp})`)).join("")}</select></label>`;
    default: {
      const a = attrsRasc();
      return `<div class="lista">${[["Nome", rasc.nome], ["Player", rasc.player], ["Nível", rasc.nivel], ["Sonho", rasc.sonho], ["Alma", rasc.sem_alma ? "sem Alma" : rasc.alma_nome || "—"],
        ["Espécie", rasc.especie || "—"], ["Atributos", R.ATRIBUTOS.map((k) => `${k} ${a[k]}`).join(" · ")], ["Perícias", rasc.pericias.join(", ") || "—"], ["Ataque", rasc.per_atk],
        ["Arma", rasc.arma || "—"], ["Vínculos", [rasc.vinc_grupo, rasc.vinc_mundo].filter(Boolean).join(" · ") || "—"], ["Meta de Vida", rasc.caminho || "—"]]
        .map(([t, x]) => `<div class="item"><div class="tx"><b>${t}</b><small>${v(x)}</small></div></div>`).join("")}</div>`;
    }
  }
}
function ligarPasso(c) {
  if (passo === 1) c.querySelector("#wz-sem").addEventListener("change", (e) => { $("#wz-alma").style.display = e.target.checked ? "none" : ""; });
  if (passo === 3) c.querySelectorAll("[data-ini]").forEach((sel) => sel.addEventListener("change", () => {
    const usados = [...c.querySelectorAll("[data-ini]")].map((x) => x.value).filter(Boolean);
    c.querySelectorAll("[data-ini]").forEach((x) => [...x.options].forEach((o) => { o.disabled = o.value && o.value !== x.value && usados.includes(o.value); }));
  }));
  if (passo === 3) c.querySelector("[data-ini]").dispatchEvent(new Event("change"));
}
function lerPasso() {
  const val = (id) => { const e = $(id); return e ? e.value : ""; };
  if (passo === 0) Object.assign(rasc, { nome: val("#wz-nome").trim(), player: val("#wz-player").trim(), sonho: val("#wz-sonho"), nivel: int(val("#wz-nivel"), 1) });
  if (passo === 1) Object.assign(rasc, { sem_alma: $("#wz-sem").checked, alma_nome: val("#wz-an").trim(), alma_atr: val("#wz-aa") || "INT", alma_hist: val("#wz-ah"),
    pas_nome: val("#wz-pn").trim(), pas_ef: val("#wz-pe").trim(), atv_nome: val("#wz-tn").trim(), atv_ef: val("#wz-te").trim() });
  if (passo === 2) Object.assign(rasc, { especie: val("#wz-esp").trim(), esp_bon: val("#wz-bon"), esp_pre: val("#wz-pre"), esp_val: int(val("#wz-val")), esp_notas: val("#wz-notas") });
  if (passo === 3) document.querySelectorAll("[data-ini]").forEach((x) => { rasc.ini[x.dataset.ini] = x.value; });
  if (passo === 4) Object.assign(rasc, { pericias: [...document.querySelectorAll(".wz-per:checked")].map((x) => x.value), per_atk: val("#wz-atk"), arma: val("#wz-arma") });
  if (passo === 6) Object.assign(rasc, { vinc_grupo: val("#wz-vg").trim(), vinc_mundo: val("#wz-vm").trim(), caminho: val("#wz-cam") });
}
function erroPasso() {
  if (passo === 0 && !rasc.nome) return "Dê um nome ao personagem.";
  if (passo === 2 && rasc.esp_val && (!rasc.esp_bon || !rasc.esp_pre || rasc.esp_bon === rasc.esp_pre)) return "Escolha atributos diferentes para o bônus e o prejuízo.";
  if (passo === 3) { const vals = R.ATRIBUTOS.map((k) => String(rasc.ini[k] || "")); if (vals.includes("") || new Set(vals).size !== 8) return "Atribua os oito valores, cada um uma vez."; }
  if (passo === 4 && rasc.pericias.length > limPericias()) return `São no máximo ${limPericias()} perícias.`;
  return "";
}
function mostrarPasso() {
  const ult = passo === PASSOS.length - 1;
  folha(`Novo personagem · ${passo + 1}/${PASSOS.length}`, `<div class="passos-wz">${PASSOS.map((_, i) => `<i class="${i < passo ? "feito" : i === passo ? "atual" : ""}"></i>`).join("")}</div>
    <p class="meta" style="margin-top:8px"><b>${PASSOS[passo][0]}</b></p><p class="sub">${PASSOS[passo][1]}</p>${corpoPasso()}<p class="erro" id="wz-erro"></p>`,
  `<button class="botao leve" data-a="${passo ? "wz-voltar" : "fechar"}">${passo ? "‹ Voltar" : "Cancelar"}</button><button class="botao prim" data-a="wz-prox">${ult ? "⚜ Criar ficha" : "Próximo ›"}</button>`, ligarPasso);
}
A["nova"] = () => { rasc = RASC0(); passo = 0; mostrarPasso(); };
A["wz-voltar"] = () => { lerPasso(); passo = Math.max(0, passo - 1); mostrarPasso(); };
A["wz-prox"] = () => {
  lerPasso();
  const e = erroPasso(); if (e) { $("#wz-erro").textContent = e; return; }
  if (passo < PASSOS.length - 1) { passo++; mostrarPasso(); return; }
  const s = novoEstado(), a = rasc;
  Object.assign(s.identidade, { nome: a.nome, player: a.player, sonho: a.sonho, nivel: a.nivel, especie: a.especie });
  s.sem_alma = a.sem_alma; s.especie_notas = a.esp_notas;
  for (const k of R.ATRIBUTOS) { s.atributos[k].inicial = String(a.ini[k]); s.atributos[k].especie = String(a.esp_val ? (R.ATR_POR_NOME[a.esp_bon] === k ? a.esp_val : R.ATR_POR_NOME[a.esp_pre] === k ? -a.esp_val : 0) : 0); }
  if (!a.sem_alma) {
    Object.assign(s.alma, { nome: a.alma_nome, atr: a.alma_atr, historia: a.alma_hist });
    s.alma.habilidades = [[a.pas_nome, a.pas_ef, "Passivo"], [a.atv_nome, a.atv_ef, "Ativo"]].filter(([n, ef]) => n || ef)
      .map(([n, ef, t]) => ({ nome: n, efeito: ef, tipo: t, cats: t === "Ativo" ? ["Dano"] : [], tabela: "", ajustes: [], execucao: t === "Ativo" ? "Comum" : "" }));
  }
  s.pericias = a.pericias; s.pericia_ataque = a.per_atk;
  if (a.arma) s.armas[0] = { grupo: a.arma, nivel: "1", props: "" };
  s.vinculos.grupo = a.vinc_grupo; s.vinculos.mundo = a.vinc_mundo; s.meta.caminho = a.caminho;
  const id = "ficha-" + Date.now().toString(36);
  banco.fichas[id] = s; banco.atual = id; fecharFolha(); abrirFicha(id, "edicao"); salvar();
  toast(a.nivel > 1 ? `Ficha criada no nível ${a.nivel}: distribua os pontos e escolha os talentos.` : "Ficha criada. Ela fica guardada neste aparelho.", 5000);
};

