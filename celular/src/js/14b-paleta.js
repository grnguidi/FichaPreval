// ------------------------------------------------------------------ Minha paleta: cada pessoa cria as cores do seu app
// Cinco cores escolhidas (pedra, moldura, destaque e dois vidros) + claro/escuro; o resto é derivado delas.
// Fica guardada no aparelho (banco.paletas), não na ficha.
const PAL_CHAVES = [["pedra", "Pedra", "Fundo das páginas"], ["moldura", "Moldura", "Cabeçalho e barra de abas"], ["destaque", "Destaque", "Títulos e botões"], ["v1", "Vidro 1", "Vitrais e rosácea"], ["v2", "Vidro 2", "Vitrais e aba ativa"]];
const PAL_MODELOS = [
  { nome: "Catedral", pedra: "#ebe5dc", moldura: "#2a1a3d", destaque: "#5e3591", v1: "#b79ad6", v2: "#a8d89a", escuro: false },
  { nome: "Vigília", pedra: "#121016", moldura: "#08070b", destaque: "#9a62e0", v1: "#c9a8f0", v2: "#b6f0a4", escuro: true },
  { nome: "Rubi", pedra: "#efe6e2", moldura: "#3b1018", destaque: "#9b1d36", v1: "#e58a9b", v2: "#f0c96a", escuro: false },
  { nome: "Esmeralda", pedra: "#e6ebe2", moldura: "#13281c", destaque: "#1f6b42", v1: "#7cc9a0", v2: "#e6d29e", escuro: false },
  { nome: "Âmbar", pedra: "#f1e9da", moldura: "#3a2410", destaque: "#9a5a12", v1: "#f0b45a", v2: "#9cc3d9", escuro: false },
  { nome: "Abismo", pedra: "#0d1418", moldura: "#05090c", destaque: "#3fa7c9", v1: "#7fd3f0", v2: "#c9a8f0", escuro: true },
  { nome: "Brasa", pedra: "#151010", moldura: "#0a0606", destaque: "#e0603a", v1: "#ff9a6b", v2: "#f0d98c", escuro: true },
];

// cores: utilitários
const hexRgb = (h) => { h = String(h || "").replace("#", ""); if (h.length === 3) h = h.replace(/./g, "$&$&"); const n = parseInt(h, 16); return isNaN(n) || h.length !== 6 ? [0, 0, 0] : [n >> 16 & 255, n >> 8 & 255, n & 255]; };
const rgbHex = (c) => "#" + c.map((v) => Math.round(Math.max(0, Math.min(255, v))).toString(16).padStart(2, "0")).join("");
const mistura = (a, b, t) => { const x = hexRgb(a), y = hexRgb(b); return rgbHex(x.map((v, i) => v + (y[i] - v) * t)); };
const lumin = (h) => { const c = hexRgb(h).map((v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }); return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]; };
const contraste = (a, b) => { const x = lumin(a), y = lumin(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
const corValida = (h) => /^#[0-9a-f]{6}$/i.test(String(h || ""));
// empurra a cor do texto para o preto (ou o branco) até ficar legível sobre o fundo
function legivel(cor, fundo, minimo) {
  const alvo = contraste("#000000", fundo) >= contraste("#ffffff", fundo) ? "#000000" : "#ffffff";
  for (let t = 0; t <= 1.0001; t += 0.05) { const c = mistura(cor, alvo, t); if (contraste(c, fundo) >= minimo) return c; }
  return alvo;
}

// as 5 cores viram o tema inteiro; avisos lista o que precisou ser ajustado
function derivarPaleta(p) {
  const e = !!p.escuro, pedra = p.pedra, avisos = [];
  // a moldura leva textos e botões claros (dourado, lilás): precisa ser escura
  let mold = p.moldura;
  for (let t = 0.05; lumin(mold) > 0.06 && t <= 1; t += 0.05) mold = mistura(p.moldura, "#000000", t);
  if (mold !== p.moldura) avisos.push("a moldura foi escurecida para os textos claros sobre ela continuarem legíveis");
  const V = {};
  V.fundo = mold; V.fundo2 = mistura(mold, "#ffffff", e ? 0.07 : 0.12);
  V.perg = pedra; V.perg2 = mistura(pedra, e ? "#ffffff" : "#000000", e ? 0.07 : 0.07);
  V.campo = mistura(pedra, e ? "#ffffff" : "#ffffff", e ? 0.04 : 0.5);
  const tinta0 = e ? mistura(p.v1, "#ffffff", 0.75) : mistura(mold, "#000000", 0.2);
  V.tinta = legivel(tinta0, V.campo, 7); if (V.tinta !== tinta0) avisos.push("o texto foi ajustado para ficar legível");
  V.tinta2 = legivel(mistura(V.tinta, pedra, 0.38), V.campo, 4.5);
  V.linha = mistura(pedra, V.tinta, e ? 0.16 : 0.18);
  V.vinho = legivel(e ? mistura(p.destaque, "#ffffff", 0.35) : p.destaque, pedra, 4.5);
  if (V.vinho.toLowerCase() !== (e ? mistura(p.destaque, "#ffffff", 0.35) : p.destaque).toLowerCase()) avisos.push("o destaque foi ajustado para aparecer sobre a pedra");
  V.verde = legivel(e ? p.v2 : mistura(p.v2, "#000000", 0.4), pedra, 3);
  V.ouro = "#b8955a"; V.ouro2 = "#e6d29e";
  V.lilas = p.v1; V.lilas2 = mistura(p.v1, "#ffffff", 0.45); V.verdec = p.v2;
  V.chumbo = e ? "#000000" : mistura(mold, "#000000", 0.25);
  V.faixa = mistura(pedra, "#ffffff", 0.6);
  V.rosa = mistura(pedra, "#a3334f", e ? 0.18 : 0.08); V.agua = mistura(pedra, p.v2, e ? 0.12 : 0.18);
  V["c-atr"] = mistura(mold, "#ffffff", 0.12);
  V.brilho = e ? "0 0 7px currentColor" : "0 0 0 transparent";
  V.sombra = e ? "none" : `0 1px 0 rgba(0,0,0,.04),0 6px 16px -10px ${mold}`;
  // texto sobre a moldura (cabeçalho, abas, botão principal)
  const claraMold = lumin(mold) > 0.3;
  V.sobre = claraMold ? legivel(mistura(mold, "#000000", 0.7), mold, 7) : legivel(V.ouro2, mold, 4.5);
  V.sobre2 = claraMold ? legivel(mistura(mold, "#000000", 0.55), mold, 4.5) : legivel(V.lilas2, mold, 4.5);
  V.sobreAt = legivel(p.v2, mold, 3);
  V.vidros = [mistura(p.destaque, p.v1, 0.35), p.v2, p.v1, "#e2cf9a", V.lilas2, mistura(p.v2, "#000000", 0.15)];
  return { V, avisos };
}

// ornamentos em SVG com as cores da paleta (iguais aos do CSS, só que recoloridos)
const svgUri = (s) => `url("data:image/svg+xml,${encodeURIComponent(s)}")`;
function svgRosacea(vid, ch, ouro, miolo, petala) {
  const c = 40, r = 36; let p = "", raios = "", lob = "";
  for (let k = 0; k < 8; k++) {
    const a0 = k * Math.PI / 4 - Math.PI / 2, a1 = a0 + Math.PI / 4;
    p += `<path d='M${c} ${c} L${(c + r * Math.cos(a0)).toFixed(1)} ${(c + r * Math.sin(a0)).toFixed(1)} A${r} ${r} 0 0 1 ${(c + r * Math.cos(a1)).toFixed(1)} ${(c + r * Math.sin(a1)).toFixed(1)}Z' fill='${vid[k % 4]}'/>`;
    raios += `<line x1='${c}' y1='${c}' x2='${(c + r * Math.cos(k * Math.PI / 4)).toFixed(1)}' y2='${(c + r * Math.sin(k * Math.PI / 4)).toFixed(1)}'/>`;
    lob += `<circle cx='${(c + 19 * Math.cos(k * Math.PI / 4 + Math.PI / 8)).toFixed(1)}' cy='${(c + 19 * Math.sin(k * Math.PI / 4 + Math.PI / 8)).toFixed(1)}' r='6.2'/>`;
  }
  return `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 80 80'><circle cx='${c}' cy='${c}' r='39' fill='${ch}'/>${p}<g stroke='${ch}' stroke-width='2.4' fill='none'>${raios}</g><g fill='${petala}' stroke='${ch}' stroke-width='2'>${lob}</g><circle cx='${c}' cy='${c}' r='${r}' fill='none' stroke='${ouro}' stroke-width='2.2'/><circle cx='${c}' cy='${c}' r='39' fill='none' stroke='${ouro}' stroke-width='1.4'/><circle cx='${c}' cy='${c}' r='9' fill='${miolo}' stroke='${ouro}' stroke-width='2.4'/></svg>`;
}
const svgLanceta = (cima, baixo, meio, ch, ouro) => `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 64'><path d='M2 63 V24 Q2 3 12 1 Q22 3 22 24 V63Z' fill='${meio}' stroke='${ouro}' stroke-width='1.6'/><path d='M2 24 Q2 3 12 1 Q22 3 22 24Z' fill='${cima}' stroke='${ch}' stroke-width='1.2'/><path d='M12 40 H22 V63 H12Z' fill='${baixo}' stroke='${ch}' stroke-width='1.2'/><path d='M2 40 H12 V63 H2Z' fill='${meio}' stroke='${ch}' stroke-width='1.2'/><path d='M12 1 V63 M2 24 H22 M2 40 H22' stroke='${ch}' stroke-width='1.4' fill='none'/><circle cx='12' cy='14' r='3.6' fill='${baixo}' stroke='${ch}' stroke-width='1.2'/></svg>`;
const svgQuadri = (cor, miolo, ch) => `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 20 20'><g fill='${cor}' stroke='${ch}' stroke-width='1'><circle cx='10' cy='5' r='4.2'/><circle cx='15' cy='10' r='4.2'/><circle cx='10' cy='15' r='4.2'/><circle cx='5' cy='10' r='4.2'/></g><circle cx='10' cy='10' r='2.6' fill='${miolo}' stroke='${ch}'/></svg>`;
const svgTri = (cor, ch) => `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 14 10'><g fill='${cor}' stroke='${ch}' stroke-width='.8'><circle cx='7' cy='3' r='2.6'/><circle cx='3.5' cy='7' r='2.6'/><circle cx='10.5' cy='7' r='2.6'/></g></svg>`;
const svgFaixa = (vid, ch) => `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 ${vid.length * 14} 10' preserveAspectRatio='none'>${vid.map((c, i) => `<rect x='${i * 14}' y='0' width='14' height='10' fill='${c}'/><line x1='${i * 14}' y1='0' x2='${i * 14}' y2='10' stroke='${ch}' stroke-width='2'/>`).join("")}</svg>`;

function cssPaleta(p) {
  const { V } = derivarPaleta(p), e = !!p.escuro, H = "html.pessoal";
  const vars = ["fundo", "fundo2", "perg", "perg2", "campo", "tinta", "tinta2", "ouro", "ouro2", "vinho", "verde", "faixa", "linha", "rosa", "agua", "chumbo", "lilas", "lilas2", "verdec", "brilho", "sombra", "c-atr"].map((k) => `--${k}:${V[k]}`).join(";");
  const brilho = e ? `filter:drop-shadow(0 0 4px ${p.v1}99)` : "filter:none";
  const rosa = svgUri(svgRosacea(V.vidros, V.chumbo, V.ouro2, e ? "#fff6e0" : "#f6f1fa", V.lilas2));
  return `${H}{${vars}}
${H} .topo:after{background-image:${svgUri(svgFaixa(V.vidros, V.chumbo))};box-shadow:${e ? `0 2px 10px ${p.v1}59` : "none"}}
${H} .rosa-topo,${H} .fach-centro .rosa-g,${H} .capa .orn{background-image:${rosa};${brilho}}
${H} .fachada .lanc{background-image:${svgUri(svgLanceta(V.vidros[0], p.v2, p.v1, V.chumbo, V.ouro2))};${brilho}}
${H} .secao:before{background-image:${svgUri(svgQuadri(p.v1, p.v2, V.chumbo))};${brilho}}
${H} .cartao.caixa:before{background-image:${svgUri(svgTri(p.v2, V.chumbo))}}
${H} .topo,${H} .topo .nome b{color:${V.sobre}}
${H} .topo .nome small,${H} .nivel,${H} .icone{color:${V.sobre2}}
${H} .nav button{color:${V.sobre2}}
${H} .nav button.on{color:${V.sobreAt}}
${H} .nav button:before{border-color:${V.sobre2}73}
${H} .nav button.on:before{border-color:${V.sobreAt};background:${p.v2}1f}
${H} .botao.prim{background:${V.fundo};border-color:${e ? p.v1 : V.fundo};color:${V.sobre}}
${H} .modo-pill.ed,${H} .ficha-acao.t-bonus,${H} .turno-aviso.sua{background:${V.vinho};border-color:${V.vinho};color:${legivel(e ? V.perg : "#ffffff", V.vinho, 4.5)}}
${H} .secao .cap,${H} .secao,${H} .fach-nome{color:${V.vinho}}`;
}

function paletaAtual() { const l = banco.paletas || []; return l[banco.paletaAtual] || l[0] || null; }
// aplica (ou tira) a paleta pessoal; chamada por aplicarTema e pela prévia ao vivo do editor
function pintarPaleta(p) {
  const h = document.documentElement; let st = $("#paleta-css");
  if (!p) { h.classList.remove("pessoal"); if (st) st.textContent = ""; return; }
  if (!st) { st = document.createElement("style"); st.id = "paleta-css"; document.head.appendChild(st); }
  st.textContent = cssPaleta(p);
  h.classList.add("pessoal"); h.classList.toggle("noite", !!p.escuro);
  const m = document.querySelector('meta[name="theme-color"]'); if (m) m.setAttribute("content", derivarPaleta(p).V.fundo);
}

// código para compartilhar: PAL-pedra-moldura-destaque-v1-v2-c|e
const codigoPaleta = (p) => "PAL-" + PAL_CHAVES.map(([k]) => p[k].replace("#", "").toLowerCase()).join("-") + "-" + (p.escuro ? "e" : "c");
function lerCodigoPaleta(txt) {
  const m = String(txt || "").trim().match(/PAL-([0-9a-f]{6})-([0-9a-f]{6})-([0-9a-f]{6})-([0-9a-f]{6})-([0-9a-f]{6})-([ce])/i);
  if (!m) return null;
  const p = { nome: "Paleta recebida", escuro: m[6].toLowerCase() === "e" };
  PAL_CHAVES.forEach(([k], i) => { p[k] = "#" + m[i + 1].toLowerCase(); });
  return p;
}

let palEdit = null, palIdx = -1;   // paleta em edição (cópia) e a posição dela na lista (-1 = nova)
function editorPaleta(p, idx) {
  palEdit = { ...p }; palIdx = idx;
  const modelos = PAL_MODELOS.map((m, i) => `<button class="pal-modelo" data-a="pal-modelo" data-i="${i}" title="${esc(m.nome)}"><i style="background:${m.moldura}"></i><i style="background:${m.pedra}"></i><i style="background:${m.destaque}"></i><i style="background:${m.v1}"></i><i style="background:${m.v2}"></i><span>${esc(m.nome)}</span></button>`).join("");
  folha("🎨 Minha paleta", `
    <label class="pal-nome">Nome <input id="pal-nome" maxlength="30" value="${esc(palEdit.nome || "")}"></label>
    <div class="pal-cores">${PAL_CHAVES.map(([k, rot, dica]) => `<label class="pal-cor"><input type="color" data-k="${k}" value="${palEdit[k]}"><span><b>${rot}</b><small>${dica}</small></span></label>`).join("")}</div>
    <div class="seg pal-modo"><button data-a="pal-escuro" data-v="0" class="${palEdit.escuro ? "" : "on"}">☀ Clara</button><button data-a="pal-escuro" data-v="1" class="${palEdit.escuro ? "on" : ""}">☾ Escura</button></div>
    <p class="ajuda" id="pal-avisos"></p>
    <div class="secao">${capitular("Partir de um modelo")}</div><div class="pal-modelos">${modelos}</div>
    <div class="secao">${capitular("Compartilhar")}</div>
    <div class="pal-codigo"><input id="pal-cod" readonly value="${codigoPaleta(palEdit)}"><button class="chip-acao" data-a="pal-copiar">Copiar</button></div>
    <div class="pal-codigo"><input id="pal-colar" placeholder="Cole aqui o código de outra pessoa"><button class="chip-acao" data-a="pal-receber">Usar</button></div>
    <p class="ajuda">A paleta fica guardada neste aparelho e vale para todas as fichas. O PDF e a folha impressa continuam no visual Catedral.</p>`,
    `${idx >= 0 ? `<button class="botao leve erro" data-a="pal-apagar">Apagar</button>` : ""}<button class="botao leve" data-a="pal-cancelar">Cancelar</button><button class="botao prim" data-a="pal-salvar">Salvar e usar</button>`,
    (c) => { c.querySelectorAll('input[type="color"]').forEach((i) => i.addEventListener("input", () => { palEdit[i.dataset.k] = i.value; previaPaleta(); })); previaPaleta(); });
}
function previaPaleta() {
  pintarPaleta(palEdit);
  const { avisos } = derivarPaleta(palEdit);
  if ($("#pal-avisos")) $("#pal-avisos").textContent = avisos.length ? "Ajuste automático: " + avisos.join("; ") + "." : "";
  if ($("#pal-cod")) $("#pal-cod").value = codigoPaleta(palEdit);
}
function recarregarEditor() { const nome = $("#pal-nome") ? $("#pal-nome").value : palEdit.nome; editorPaleta({ ...palEdit, nome }, palIdx); }

A["paletas"] = () => {
  const l = banco.paletas || [];
  const lista = l.map((p, i) => `<div class="item pal-item ${banco.tema === "minha" && i === banco.paletaAtual ? "on" : ""}" data-a="pal-usar" data-i="${i}"><span class="pal-amostra"><i style="background:${p.moldura}"></i><i style="background:${p.pedra}"></i><i style="background:${p.destaque}"></i><i style="background:${p.v1}"></i><i style="background:${p.v2}"></i></span><div class="tx"><b>${esc(p.nome || "Sem nome")}</b><small>${p.escuro ? "Escura" : "Clara"}${banco.tema === "minha" && i === banco.paletaAtual ? " · em uso" : ""}</small></div><button class="chip-acao" data-a="pal-editar" data-i="${i}">Editar</button></div>`).join("");
  folha("🎨 Minhas paletas", `<div class="lista">${lista || `<p class="ajuda">Nenhuma paleta ainda. Crie a sua escolhendo 5 cores, ou parta de um modelo.</p>`}</div>
    <div class="item" data-a="pal-tema" data-v="dia"><div class="tx"><b>☀ Voltar para a Catedral</b></div></div>
    <div class="item" data-a="pal-tema" data-v="noite"><div class="tx"><b>☾ Voltar para a Vigília</b></div></div>`,
    `<button class="botao prim" data-a="pal-nova">＋ Nova paleta</button>`);
};
A["pal-nova"] = () => editorPaleta({ ...PAL_MODELOS[banco.tema === "noite" ? 1 : 0], nome: `Minha paleta ${(banco.paletas || []).length + 1}` }, -1);
A["pal-editar"] = (el, ev) => { if (ev) ev.stopPropagation(); const i = int(el.dataset.i); editorPaleta(banco.paletas[i], i); };
A["pal-usar"] = (el, ev) => { if (ev && ev.target.closest('[data-a="pal-editar"]')) return; banco.paletaAtual = int(el.dataset.i); banco.tema = "minha"; gravarLocal(); fecharFolha(); render(); };
A["pal-tema"] = (el) => { banco.tema = el.dataset.v; gravarLocal(); fecharFolha(); render(); };
A["pal-modelo"] = (el) => { const m = PAL_MODELOS[int(el.dataset.i)]; PAL_CHAVES.forEach(([k]) => { palEdit[k] = m[k]; }); palEdit.escuro = m.escuro; recarregarEditor(); };
A["pal-escuro"] = (el) => { palEdit.escuro = el.dataset.v === "1"; recarregarEditor(); };
A["pal-copiar"] = () => { const t = codigoPaleta(palEdit); (navigator.clipboard ? navigator.clipboard.writeText(t) : Promise.reject()).then(() => toast("Código copiado. Mande para quem quiser a mesma paleta."), () => { const i = $("#pal-cod"); i.select(); toast("Selecionei o código: copie e envie."); }); };
A["pal-receber"] = () => { const p = lerCodigoPaleta($("#pal-colar").value); if (!p) { toast("Código inválido. Ele começa com PAL- e tem 5 cores."); return; } PAL_CHAVES.forEach(([k]) => { palEdit[k] = p[k]; }); palEdit.escuro = p.escuro; recarregarEditor(); toast("Paleta recebida. Toque em Salvar para guardar."); };
A["pal-cancelar"] = () => { palEdit = null; fecharFolha(); aplicarTema(); };
A["pal-salvar"] = () => {
  const p = { ...palEdit, nome: ($("#pal-nome").value || "").trim() || "Minha paleta" };
  banco.paletas = banco.paletas || [];
  if (palIdx >= 0) banco.paletas[palIdx] = p; else { banco.paletas.push(p); palIdx = banco.paletas.length - 1; }
  banco.paletaAtual = palIdx; banco.tema = "minha"; palEdit = null; gravarLocal(); fecharFolha(); render(); toast(`Paleta “${esc(p.nome)}” em uso.`);
};
A["pal-apagar"] = () => {
  if (!confirm("Apagar esta paleta?")) return;
  banco.paletas.splice(palIdx, 1);
  if (banco.tema === "minha" && (!banco.paletas.length || banco.paletaAtual === palIdx)) { banco.tema = "dia"; banco.paletaAtual = 0; } else if (banco.paletaAtual > palIdx) banco.paletaAtual--;
  palEdit = null; gravarLocal(); fecharFolha(); render();
};
