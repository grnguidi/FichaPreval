// ------------------------------------------------------------------ Dados físicos
// Com o modo ligado, o app não rola: diz quantos e quais dados pegar em cada perícia, ataque e encantamento, já com o
// bônus somado (atributo, nível ÷ 3, acerto da arma, talentos, sets, talismãs e o teto de combate), as vantagens
// (rolar 2d20 e ficar com o maior), os dados extras (atributo, propriedades, Arcano, sets) e quando dá para rerrolar.
// Custos (Mana, Vigor, munição) e a afiação continuam sendo descontados; o crítico é marcado com um toque.
const fisico = () => !!banco.dadosFisicos;
let pedidoDados = [];   // dados pedidos na ação atual: [[quantidade, faces]]
const pedirDados = (n, f) => { if (n > 0) pedidoDados.push([n, f]); };
const limpaExpr = (e) => String(e || "").replace(/\s+/g, " ").replace(/\s*\+\s*/g, " + ").replace(/\s*-\s*/g, " − ").trim();
// no crítico os dados se multiplicam (×2, ou ×3 com Destruidora); os bônus fixos não
const exprCritico = (e, mult = 2) => limpaExpr(String(e || "").replace(/(\d+)\s*d\s*(\d+)/g, (m, n, f) => `${+n * mult}d${f}`));
const Dados = {
  // jogada de ataque: 1d20 (ou 2d20, ficando com o maior na vantagem / o menor na desvantagem) + bônus
  ataque(b, vant, margem = 20, desv = false) {
    if (!fisico()) return R.rolarAtaque(b, vant, margem, rng, desv);
    const dois = !!vant !== !!desv; pedirDados(dois ? 2 : 1, 20);
    return { fisico: true, d20: [], n: dois ? 2 : 1, menor: !!desv && !vant, bonus: b, total: null, margem, critico: false, garantido: false, desastre: false };
  },
  // teste de perícia ou resistência: N d20, fica com o maior
  teste(b, nd20 = 1) {
    if (!fisico()) return R.rolarPericia(b, nd20, rng);
    const n = Math.max(1, int(nd20, 1)); pedirDados(n, 20);
    return { fisico: true, d20: [], n, bonus: b, total: null };
  },
  // dano e pontos de condição: devolve [total, partes] como R.rolarExpr; no modo físico, total = null
  expr(e, dobrar = false, mult = 2) {
    if (!fisico()) return R.rolarExpr(e, rng, dobrar, mult);
    for (const m of String(e || "").matchAll(/(\d+)\s*d\s*(\d+)/g)) pedirDados(+m[1], +m[2]);
    return [null, { expr: limpaExpr(e), crit: /d/.test(String(e)) ? exprCritico(e, mult) : "" }];
  },
};
const qtosD20 = (n, menor) => (n > 1 ? `<b>${n}d20</b> e fique com o <b>${menor ? "menor" : "maior"}</b>` : "<b>1d20</b>");
const sinal = (b) => `${b >= 0 ? "+" : "−"} ${Math.abs(b)}`;
// rerrolagens do livro: Sortudo (perícia) e Sortudo maior (ataque e resistência), 1x por descanso longo
function notaRerrolar(tipo) {
  if (!S) return "";
  if (tipo === "pericia" && C.tal.has("Sortudo")) return `<br><span class="sub">↻ Sortudo: 1x por descanso longo, pode rerrolar este teste.</span>`;
  if ((tipo === "ataque" || tipo === "resist") && C.tal.has("Sortudo maior")) return `<br><span class="sub">↻ Sortudo maior: 1x por descanso longo, pode rerrolar este teste.</span>`;
  return "";
}
function txtAtaqueFisico(at, rot) {
  const crit = at.margem < 20 ? `${at.margem} a 20 no dado` : "20 no dado";
  return `${rot}: role ${qtosD20(at.n, at.menor)} <b>${sinal(at.bonus)}</b> e compare com a CA.`
    + `<br><span class="sub">${crit} = crítico (role o dano do crítico) · 20 natural acerta sempre · 1 natural é desastre (erra; o alvo pode atacar você como ação livre).</span>`
    + notaRerrolar("ataque");
}
function txtDanoFisico(info, rot) {
  if (!info.expr) return `${rot}: —`;
  return `${rot}: role <b>${esc(info.expr)}</b>` + (info.crit && info.crit !== info.expr ? ` <span class="sub">· no crítico: <b>${esc(info.crit)}</b></span>` : "");
}
// teste de perícia/resistência (rolado ou a rolar)
function txtTeste(nome, r, tipo = "pericia") {
  if (r.fisico) return `${nome}: role ${qtosD20(r.n)} <b>${sinal(r.bonus)}</b>.` + notaRerrolar(tipo);
  return `${nome}: <b style="font-size:20px">${r.total}</b> <span class="sub">[d20 ${r.d20.join(", ")}${r.d20.length > 1 ? " → maior" : ""} ${r.bonus >= 0 ? "+" : ""}${r.bonus}]</span>`;
}
// resumo do que pegar na mesa: "2d20 · 3d10 · 1d6"
function resumoDados() {
  const por = {};
  for (const [n, f] of pedidoDados) por[f] = (por[f] || 0) + n;
  pedidoDados = [];
  const fs = Object.keys(por).map(Number).sort((a, b) => b - a);
  return fs.length ? `<div class="pegue">🎲 Pegue: ${fs.map((f) => `<b>${por[f]}d${f}</b>`).join(" · ")}</div>` : "";
}
A["fisico"] = () => {
  banco.dadosFisicos = !banco.dadosFisicos; gravarLocal(); fecharFolha(); render();
  toast(banco.dadosFisicos ? "Dados físicos ligados: o app diz quais dados rolar e quanto somar." : "Dados físicos desligados: o app volta a rolar.");
};
// no modo físico o app não sabe se saiu crítico: um toque reafia a arma (e lembra do Voraz)
A["foi-critico"] = (el) => {
  const i = int(el.dataset.i); S.desgaste[i] = Object.assign(S.desgaste[i] || {}, { usados: 0, desgastada: false });
  salvar(); render(); el.disabled = true; el.textContent = "✓ Crítico marcado: arma reafiada";
};
