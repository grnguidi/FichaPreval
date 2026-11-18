// ------------------------------------------------------------------ aba Anotações
// Anotações livres do jogador (pistas, nomes, mapas de cabeça, combinados com o mestre). Ficam na ficha:
// vão no .json, na ficha da mesa e no backup. Funcionam no Modo Jogo e no Modo Edição.
const hojeTxt = () => { const d = new Date(); return `${String(d.getDate()).padStart(2, "0")}/${String(d.getMonth() + 1).padStart(2, "0")}/${d.getFullYear()} ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`; };
function pNotas() {
  const ns = S.anotacoes || [];
  let h = secao("Anotações", `${ns.length} anotaç${ns.length === 1 ? "ão" : "ões"}`)
    + `<p class="sub">Pistas, nomes, lugares, combinados com o mestre. Ficam guardadas na ficha.</p>
      <button class="botao prim" data-a="nota-nova" style="width:100%;margin:4px 0 12px">✍ Nova anotação</button>`;
  if (!ns.length) h += `<p class="vazio">Escreva aqui o que o grupo descobriu na trilha.</p>`;
  h += ns.map((n) => `<div class="cartao nota" data-a="nota-abrir" data-id="${esc(n.id)}">
      <div class="nota-cab"><b>${esc(n.titulo || "Sem título")}</b><small>${esc(n.quando)}</small></div>
      <p>${esc(n.texto).replace(/\n/g, "<br>") || '<span class="sub">vazia</span>'}</p></div>`).join("");
  return h;
}
function editorNota(n) {
  folha(n ? "Anotação" : "Nova anotação", `<label class="campo"><span>Título</span><input id="nt-t" maxlength="80" value="${esc(n ? n.titulo : "")}" placeholder="O ferreiro de Andar 2"></label>
    <label class="campo"><span>Texto</span><textarea id="nt-x" rows="9" style="width:100%">${esc(n ? n.texto : "")}</textarea></label>`,
    `${n ? `<button class="botao leve" data-a="nota-apagar" data-id="${esc(n.id)}">Apagar</button>` : `<button class="botao leve" data-a="fechar">Cancelar</button>`}<button class="botao prim" data-a="nota-ok" data-id="${esc(n ? n.id : "")}">Salvar</button>`,
    (c) => { const t = $("#nt-x", c); if (t && !n) setTimeout(() => $("#nt-t", c).focus(), 50); });
}
A["nota-nova"] = () => editorNota(null);
A["nota-abrir"] = (el) => { const n = (S.anotacoes || []).find((x) => x.id === el.dataset.id); if (n) editorNota(n); };
A["nota-ok"] = (el) => {
  const titulo = $("#nt-t").value.trim(), texto = $("#nt-x").value;
  if (!titulo && !texto.trim()) { fecharFolha(); return; }
  fecharFolha();
  mudar((s) => {
    const n = s.anotacoes.find((x) => x.id === el.dataset.id);
    if (n) { n.titulo = titulo; n.texto = texto; n.quando = hojeTxt(); }
    else s.anotacoes.unshift({ id: Math.random().toString(36).slice(2, 10), titulo, texto, quando: hojeTxt() });
  });
};
A["nota-apagar"] = (el) => {
  if (!confirm("Apagar esta anotação?")) return;
  fecharFolha(); mudar((s) => { s.anotacoes = s.anotacoes.filter((x) => x.id !== el.dataset.id); });
};
