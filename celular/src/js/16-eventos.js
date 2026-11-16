// ------------------------------------------------------------------ eventos
document.addEventListener("click", (ev) => {
  const el = ev.target.closest("[data-a]");
  if (!el) return;
  const f = A[el.dataset.a];
  if (!f) return;
  if (el.tagName === "A") ev.preventDefault();
  if (S && banco.modo !== "edicao" && SO_EDICAO.has(el.dataset.a)) {
    toast(`Isso muda a ficha — use o <b>Modo Edição</b>. <button class="botao leve" data-a="modo" style="min-height:32px;padding:4px 10px;margin-left:6px">✎ Editar</button>`);
    return;
  }
  f(el, ev);
});
document.addEventListener("DOMContentLoaded", async () => {
  lerLocal();
  if (banco.atual && banco.fichas[banco.atual]) S = normalizar(banco.fichas[banco.atual]);
  const recebida = lerHash();
  let chegou = null;
  if (recebida) chegou = await receberFichaDaUrl(recebida);
  $("#veu").addEventListener("click", fecharFolha);
  $("#arquivo").addEventListener("change", (e) => { if (e.target.files[0]) importarArquivo(e.target.files[0]); e.target.value = ""; });
  render();
  setTimeout(ligarNuvem, 50);
  window.__fichaChegou = !!chegou;
  if (recebida && !(chegou && chegou.mesa)) toast(chegou ? `Ficha <b>${esc(chegou.nome)}</b> ${chegou.atualizou ? "atualizada" : "recebida"}.` : "Não consegui ler a ficha enviada. Tente de novo ou use Abrir arquivo .json.", 5000);
  await detectarSessao();
  if (fichaDoApp) confirmarAtualizacao();
  else if (atualizarSlug && mesaAlvo && !recebida) {   // no app instalado: acha a ficha desse jogador e manda para a mesa
    const ids = Object.keys(banco.fichas).filter((k) => [banco.fichas[k].identidade.player, banco.fichas[k].identidade.nome].some((t) => slugNome(t) === atualizarSlug));
    if (ids.length === 1) enviarParaMesa(ids[0]);
    else toast(ids.length ? "Achei mais de uma ficha desse jogador: toque em <b>Enviar</b> na certa." : "Não achei a ficha deste jogador. Toque em <b>Enviar</b> na ficha certa.", 6000);
  }
  if (chegou && sessao.ativa && !sessao.id) entrarSessao((S.identidade.nome || "").trim() || "Jogador", true);
  if ("serviceWorker" in navigator && (location.protocol === "https:" || location.hostname === "localhost") && !window.claude) navigator.serviceWorker.register("sw.js").catch(() => {});
});
