// ------------------------------------------------------------------ deslizar para os lados entre as abas
// Arrastar a página para a esquerda leva à próxima sub-aba; na última, passa para a primeira da aba seguinte
// (Ficha › Combate › Saberes › Bolsa › Diário › Grupo, se houver sessão). Para a direita, volta.
// Campos de texto, listas que rolam de lado e a própria barra de sub-abas não disparam o gesto.
function sequenciaAbas() {
  const lista = [];
  for (const [k, a] of Object.entries(ABAS)) {
    const b = document.querySelector(`#nav [data-aba="${k}"]`);
    if (!b || b.classList.contains("oculto")) continue;
    if (a.subs.length) a.subs.forEach(([s]) => lista.push([k, s])); else lista.push([k, ""]);
  }
  return lista;
}
function vizinhoAba(passo) {
  const seq = sequenciaAbas(), s = subAtual();
  const i = seq.findIndex(([a, x]) => a === aba && (x === s || !x));
  const j = i + passo;
  return i < 0 || j < 0 || j >= seq.length ? null : seq[j];
}
function irParaVizinho(passo) {
  const v = vizinhoAba(passo); if (!v) return false;
  irPara(v[0], v[1] || undefined); gravarLocal(); render(); window.scrollTo(0, 0);
  return true;
}
// mantém a sub-aba ativa visível na barra (útil quando ela tem mais sub-abas do que cabe na tela)
function mostrarSubAtiva() { const b = document.querySelector("#subabas .seg button.on"); if (b && b.scrollIntoView) b.scrollIntoView({ inline: "center", block: "nearest" }); }

const semMovimento = () => window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
function rolaDeLado(el, limite) {
  for (; el && el !== limite; el = el.parentElement) {
    if (el.scrollWidth > el.clientWidth + 2) { const o = getComputedStyle(el).overflowX; if (o === "auto" || o === "scroll") return true; }
  }
  return false;
}
(function gestoLateral() {
  const pag = $("#pagina"); if (!pag) return;
  let g = null;   // gesto em andamento
  pag.addEventListener("touchstart", (e) => {
    g = null;
    if (e.touches.length !== 1 || $("#folha").classList.contains("on") || $("#nav").classList.contains("oculto")) return;
    const t = e.touches[0], alvo = e.target;
    if (t.clientX < 18 || t.clientX > innerWidth - 18) return;   // bordas: gesto de voltar do sistema
    if (alvo.closest("input,textarea,select,[contenteditable],.seg,.filtros,.sem-deslizar") || rolaDeLado(alvo, pag)) return;
    g = { x: t.clientX, y: t.clientY, t: Date.now(), dx: 0, lado: false };
  }, { passive: true });
  pag.addEventListener("touchmove", (e) => {
    if (!g) return;
    const t = e.touches[0], dx = t.clientX - g.x, dy = t.clientY - g.y;
    if (!g.lado) {
      if (Math.abs(dy) > 12 && Math.abs(dy) > Math.abs(dx)) { g = null; return; }   // é rolagem vertical
      if (Math.abs(dx) < 14 || Math.abs(dx) < Math.abs(dy) * 1.4) return;
      g.lado = true; pag.classList.add("arrastando");
    }
    const tem = vizinhoAba(dx < 0 ? 1 : -1);
    g.dx = tem ? dx : dx * 0.25;   // resistência quando não há para onde ir
    pag.style.transform = `translateX(${g.dx}px)`; pag.style.opacity = String(1 - Math.min(0.35, Math.abs(g.dx) / innerWidth));
  }, { passive: true });
  const fim = () => {
    if (!g || !g.lado) { g = null; return; }
    const { dx, t } = g; g = null;
    const vel = Math.abs(dx) / Math.max(1, Date.now() - t), passo = dx < 0 ? 1 : -1;
    const vai = (Math.abs(dx) > innerWidth * 0.22 || (Math.abs(dx) > 40 && vel > 0.45)) && vizinhoAba(passo);
    pag.classList.remove("arrastando");
    if (!vai || semMovimento()) {
      pag.style.transform = ""; pag.style.opacity = "";
      if (vai) { irParaVizinho(passo); mostrarSubAtiva(); }
      return;
    }
    pag.classList.add("saindo"); pag.style.transform = `translateX(${-passo * innerWidth * 0.6}px)`; pag.style.opacity = "0";
    setTimeout(() => {
      pag.classList.remove("saindo"); pag.classList.add("arrastando");
      irParaVizinho(passo); mostrarSubAtiva();
      pag.style.transform = `translateX(${passo * innerWidth * 0.35}px)`; pag.style.opacity = "0";
      void pag.offsetWidth;
      pag.classList.remove("arrastando"); pag.classList.add("saindo");
      pag.style.transform = ""; pag.style.opacity = "";
      setTimeout(() => pag.classList.remove("saindo"), 200);
    }, 130);
  };
  pag.addEventListener("touchend", fim);
  pag.addEventListener("touchcancel", () => { if (g && g.lado) { pag.classList.remove("arrastando"); pag.style.transform = ""; pag.style.opacity = ""; } g = null; });
})();
