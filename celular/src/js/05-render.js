// ------------------------------------------------------------------ render
function render() {
  aplicarTema();
  montarNav();
  const vazio = !S;
  $("#nav").classList.toggle("oculto", vazio);
  $("#nivel").classList.toggle("oculto", vazio);
  if (vazio) { aplicarLayout(); document.documentElement.classList.remove("jogo"); $("#t-nome").textContent = "Conestoga connection"; $("#t-sub").textContent = "Ficha de mesa"; if ($("#t-foto")) $("#t-foto").hidden = true; if ($("#t-rosa")) $("#t-rosa").hidden = false; $("#pagina").innerHTML = telaInicial(); pintarSessao(); return; }
  C = calcular();
  $("#t-nome").textContent = S.identidade.nome || "Sonhador sem nome";
  const tf = $("#t-foto"); if (tf) { tf.hidden = !S.foto; if (S.foto && tf.getAttribute("src") !== S.foto) tf.src = S.foto; }
  if ($("#t-rosa")) $("#t-rosa").hidden = !!S.foto;
  $("#t-sub").innerHTML = C.resto ? `<span style="color:#f0a08c">${C.resto > 0 ? `faltam ${C.resto} pontos` : `excedeu ${-C.resto}`}</span>` : (S.identidade.especie || "") + (S.sem_alma ? " · sem alma" : "");
  $("#nv").textContent = `Nv ${romano(C.nv)}`;
  document.documentElement.classList.toggle("jogo", banco.modo !== "edicao");
  irPara(aba);
  if (aba === "grupo" && !(sessao.ativa && sessao.id)) aba = "ficha";
  $("#pagina").innerHTML = barraSub() + paginaAtual();
  document.querySelectorAll("#nav button").forEach((b) => b.classList.toggle("on", b.dataset.aba === aba));
  aplicarLayout();
  pintarSessao();
  pintarPontos();
  medirTopo();
}
function aplicarTema() {
  const h = document.documentElement;
  if (banco.tema === "minha" && !paletaAtual()) banco.tema = "dia";
  if (!["noite", "minha"].includes(banco.tema)) banco.tema = "dia";   // Catedral (dia), Vigília (noite) ou a paleta da pessoa
  if (banco.tema === "minha") { pintarPaleta(paletaAtual()); return; }
  pintarPaleta(null);
  h.classList.toggle("noite", banco.tema === "noite");
  const m = document.querySelector('meta[name="theme-color"]');
  if (m) m.setAttribute("content", banco.tema === "noite" ? "#08070b" : "#2a1a3d");
}

