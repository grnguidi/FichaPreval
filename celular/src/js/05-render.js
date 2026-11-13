// ------------------------------------------------------------------ render
function render() {
  aplicarTema();
  const vazio = !S;
  $("#nav").classList.toggle("oculto", vazio);
  $("#nivel").classList.toggle("oculto", vazio);
  if (vazio) { document.documentElement.classList.remove("jogo"); $("#t-nome").textContent = "Prevalecentes"; $("#t-sub").textContent = "Ficha de mesa"; $("#pagina").innerHTML = telaInicial(); pintarSessao(); return; }
  C = calcular();
  $("#t-nome").textContent = S.identidade.nome || "Sonhador sem nome";
  $("#t-sub").innerHTML = C.resto ? `<span style="color:#f0a08c">${C.resto > 0 ? `faltam ${C.resto} pontos` : `excedeu ${-C.resto}`}</span>` : (S.identidade.especie || "") + (S.sem_alma ? " · sem alma" : "");
  $("#nv").textContent = `Nv ${C.nv}`;
  document.documentElement.classList.toggle("jogo", banco.modo !== "edicao");
  document.querySelectorAll("#nav button").forEach((b) => b.classList.toggle("on", b.dataset.aba === aba));
  const faixa = banco.modo === "edicao"
    ? `<div class="faixa-modo ed"><span>✎ <b>Modo Edição</b> — criar, subir de nível, escolher e aprender</span><button data-a="modo">⚔ Jogar</button></div>`
    : `<div class="faixa-modo"><span>⚔ <b>Modo Jogo</b> — rolar, gastar e anotar na mesa</span><button data-a="modo">✎ Editar</button></div>`;
  $("#nav-alma").classList.toggle("oculto", !!S.sem_alma);
  if (aba === "alma" && S.sem_alma) aba = "ficha";
  $("#pagina").innerHTML = faixa + { ficha: pFicha, combate: pCombate, pericias: pPericias, grimorio: pGrimorio, alma: pAlma, talentos: pTalentos, bolsa: pBolsa }[aba]();
  pintarSessao();
}
function aplicarTema() { document.documentElement.classList.toggle("noite", banco.tema === "noite"); }

