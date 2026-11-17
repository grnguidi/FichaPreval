// ------------------------------------------------------------------ dados livres, Portão da Morte e Estourar (Adaga)
const HIST_DADOS = [];
// "d20", "2d6+3", "4d8 - 1": aceita dado sem quantidade e espaços
const normDados = (e) => String(e == null ? "" : e).toLowerCase().replace(/\s+/g, "").replace(/(^|[+\-])d(\d+)/g, "$11d$2");
const txtPartes = (partes) => partes.map(([t, v]) => (v.length ? `${t}[${v.length > 14 ? v.slice(0, 14).join(", ") + "…" : v.join(", ")}]` : t)).join(" ");
function rolarLivre(expr, dobrar) {
  const e = normDados(expr);
  if (!/\d+d\d+|^\d+$/.test(e)) return null;
  const [total, partes] = R.rolarExpr(e, rng, !!dobrar);
  return { total, partes, expr: e };
}
A["dados"] = () => {
  const rapidos = [4, 6, 8, 10, 12, 20, 100].map((f) => `<button class="botao leve mini" data-a="dado-rapido" data-e="1d${f}">d${f}</button>`).join(" ");
  folha("🎲 Rolar dados", `<div class="grade g2" style="grid-template-columns:1fr auto;align-items:end"><label class="campo"><span>Expressão</span><input id="dd-e" placeholder="2d6+3, 4d8, d20" inputmode="text" autocapitalize="off" autocomplete="off"></label>
    <button class="botao prim" data-a="dado-rolar">🎲 Rolar</button></div>
    <div class="linhabts" style="margin-top:8px;flex-wrap:wrap">${rapidos}</div>
    <div class="linhabts" style="margin-top:8px"><button class="botao leve mini" data-a="dado-vant" data-v="1">d20 vantagem</button><button class="botao leve mini" data-a="dado-vant" data-v="-1">d20 desvantagem</button></div>
    <label class="campo" style="flex-direction:row;gap:8px;align-items:center;margin-top:8px"><input type="checkbox" id="dd-c" style="width:22px;height:22px"><span style="margin:0">Crítico (dobra os dados)</span></label>
    <div id="dd-t" style="font-size:44px;font-weight:700;text-align:center;color:var(--vinho);margin:8px 0 0">—</div><div class="sub" id="dd-p" style="text-align:center"></div>
    <div class="sub" id="dd-h" style="margin-top:10px;max-height:150px;overflow:auto">${HIST_DADOS.join("<br>")}</div>`,
  `<button class="botao prim" data-a="fechar">Fechar</button>`);
};
function mostrarDado(rot, total, partes) {
  const t = $("#dd-t"); if (t) { t.textContent = total; $("#dd-p").textContent = `${rot}: ${txtPartes(partes)}`; }
  HIST_DADOS.unshift(`${esc(rot)} → <b>${total}</b> <span class="sub">${esc(txtPartes(partes))}</span>`); HIST_DADOS.length = Math.min(HIST_DADOS.length, 30);
  if ($("#dd-h")) $("#dd-h").innerHTML = HIST_DADOS.join("<br>");
  if (S) registrarDiario({ titulo: "🎲 Dados", linhas: [`${esc(rot)}: <b>${total}</b> <span class="sub">${esc(txtPartes(partes))}</span>`] });
}
const rolaExpr = (e) => { const r = rolarLivre(e, $("#dd-c") && $("#dd-c").checked); if (!r) { toast("Expressão inválida. Use algo como 2d6+3."); return; } mostrarDado(e, r.total, r.partes); };
A["dado-rolar"] = () => rolaExpr($("#dd-e").value);
A["dado-rapido"] = (el) => { $("#dd-e").value = el.dataset.e; rolaExpr(el.dataset.e); };
A["dado-vant"] = (el) => {
  const a = R.rolarExpr("1d20", rng), b = R.rolarExpr("1d20", rng), adv = el.dataset.v === "1", pega = adv ? (a[0] >= b[0] ? a : b) : (a[0] <= b[0] ? a : b);
  mostrarDado(`d20 ${adv ? "com vantagem" : "com desvantagem"} (${a[0]} e ${b[0]})`, pega[0], pega[1]);
};

// Portão da Morte: o d20 do começo do turno marca o sucesso ou a falha sozinho (11+ é sucesso)
A["portao-rolar"] = () => {
  const v = rng(20), suc = v >= 11, lim = C.d.limite_morte;
  let msg = "";
  mudar((s) => {
    const arr = s.portao[suc ? "Sucessos" : "Falhas"], i = arr.indexOf(false);
    if (i >= 0 && i < (suc ? 5 : lim)) arr[i] = true;
    const ns = s.portao.Sucessos.filter(Boolean).length, nf = s.portao.Falhas.slice(0, lim).filter(Boolean).length;
    msg = `🎲 Portão da Morte: <b>${v}</b> — ${suc ? "sucesso" : "falha"} (${ns}/5 sucessos, ${nf}/${lim} falhas).`;
    if (ns >= 5) {   // 5 sucessos: volta com 1 de Vida e uma cicatriz
      s.vida.atual = "1"; s.portao = { Sucessos: [false, false, false, false, false], Falhas: [false, false, false, false, false] };
      const n = R.contarCicatrizes(s.cicatrizes); s.cicatrizes = !String(s.cicatrizes || "").trim() || /^\d+$/.test(String(s.cicatrizes).trim()) ? String(n + 1) : s.cicatrizes + ", +1";
      msg += " <b>Você volta com 1 de Vida e ganha uma cicatriz.</b>";
    } else if (nf >= lim) msg += ` <b class="erro">${lim} falhas: o personagem morreu.</b>`;
  });
  mostrarRolagem("☠ Portão da Morte", [msg]);
};

// Adaga (3.3): Estourar remove os acúmulos de Sangria do alvo e causa 2 dados do dado-base da adaga por acúmulo (ignora RD)
function estourar(i) {
  const w = S.armas[i], ar = ARMAS[w.grupo], nv = int(w.nivel, 1), l = ar.tabela.find((x) => x.nivel === nv) || ar.tabela[0];
  const faces = Math.max(...[...String(l.dano).matchAll(/\d+d(\d+)/g)].map((m) => +m[1]), 4), chave = `${i}:${w.grupo}`;
  const n = int((S.recursos[chave] || {})["Acúmulos de Sangria"]);
  if (!n) { toast("Sem acúmulos de Sangria no alvo. Ajuste o contador da Adaga (＋ a cada acerto) antes de Estourar."); return; }
  const [tot, partes] = R.rolarExpr(`${2 * n}d${faces}`, rng);
  mudar((s) => { s.recursos[chave]["Acúmulos de Sangria"] = 0; });
  const aviso = marcarAcao("Bônus");
  mostrarRolagem("💥 Estourar", [txtDano(tot, partes), `<span class="sub">${n} acúmulo(s) × 2 dados de d${faces} (dado-base da adaga nv ${nv}). O dano ignora RD. Execução Silenciosa: com o alvo abaixo de 25% da vida e 5 ou mais acúmulos, é crítico automático (dobre o resultado).</span>`].concat(aviso ? [`<span class="erro">${aviso}</span>`] : []));
}
