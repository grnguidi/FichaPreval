// ------------------------------------------------------------------ render
function render() {
  aplicarTema();
  montarNav();
  const vazio = !S;
  $("#nav").classList.toggle("oculto", vazio);
  $("#nivel").classList.toggle("oculto", vazio);
  if (vazio) { aplicarLayout(); document.documentElement.classList.remove("jogo"); $("#t-nome").textContent = "Conestoga connection"; $("#t-sub").textContent = "Ficha de mesa"; if ($("#t-foto")) $("#t-foto").hidden = true; $("#pagina").innerHTML = telaInicial(); pintarSessao(); return; }
  C = calcular();
  $("#t-nome").textContent = S.identidade.nome || "Sonhador sem nome";
  const tf = $("#t-foto"); if (tf) { tf.hidden = !S.foto; if (S.foto && tf.getAttribute("src") !== S.foto) tf.src = S.foto; }
  $("#t-sub").innerHTML = C.resto ? `<span style="color:#f0a08c">${C.resto > 0 ? `faltam ${C.resto} pontos` : `excedeu ${-C.resto}`}</span>` : (S.identidade.especie || "") + (S.sem_alma ? " · sem alma" : "");
  $("#nv").textContent = `Nv ${C.nv}`;
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
  if (banco.tema === "vitral") banco.tema = "trilha";   // o tema Vitral virou o Diário de trilha
  h.classList.toggle("noite", banco.tema === "noite"); h.classList.toggle("trilha", banco.tema === "trilha");
  const m = document.querySelector('meta[name="theme-color"]');
  if (m) m.setAttribute("content", banco.tema === "trilha" ? "#1f3d5c" : banco.tema === "noite" ? "#0d120f" : "#1b2520");
}

