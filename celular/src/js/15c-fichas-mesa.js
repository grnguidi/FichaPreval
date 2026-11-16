// ------------------------------------------------------------------ fichas da mesa (pasta fichas/ no notebook do mestre)
// O jogador escolhe a ficha dele (Bruno, Carol...), o celular baixa o .json do notebook e devolve cada mudança.
// Quando o arquivo muda por outro caminho (o mestre abriu e salvou no PC), o celular percebe pela versão e baixa de novo.
// "Atualizar minha ficha" troca o .json do notebook pela ficha guardada no app instalado.
const CH_FICHA = "prevalecentes.sessao.ficha", CH_ATUALIZAR = "prevalecentes.atualizar";
Object.assign(sessao, { fichasLista: null, ficha: "", fichaVer: "", fichaEnviada: 0, fichaOk: false, criandoMesa: false });
let enviandoArq = false, baixandoArq = false, fichaDoApp = null;
const chaveMesa = () => "mesa-" + sessao.ficha;
const nomeDaFichaMesa = () => { const f = (sessao.fichasLista || []).find((x) => x.slug === sessao.ficha); return f ? f.nome : (sessao.id || sessao.ficha); };
const slugNome = (t) => String(t || "").normalize("NFKD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/[^a-z0-9_-]+/g, "-").replace(/^[-_]+|[-_]+$/g, "").slice(0, 30);
const novoIdFicha = () => (sessao.criandoMesa && sessao.ficha) ? (sessao.criandoMesa = false, chaveMesa()) : "ficha-" + Date.now().toString(36);
const naFichaDaMesa = () => !!(sessao.ficha && S && banco.atual === chaveMesa());

function pedirFichaMesa() {
  const lista = sessao.fichasLista || [];
  folha("Quem é você?", `<p class="sub">Escolha a sua ficha. Ela fica guardada no notebook do mestre e acompanha você durante a sessão.</p>
    ${sessao.pedeSenha ? `<label class="campo"><span>Senha da mesa</span><input id="ss-s" value="${esc(sessao.senha)}" maxlength="20" inputmode="numeric" autocomplete="off"></label>` : ""}
    <div class="lista">${lista.map((f) => `<div class="item" data-a="ficha-mesa" data-s="${esc(f.slug)}" data-n="${esc(f.nome)}"><div class="tx"><b>${esc(f.nome)}</b><small>${f.tem ? "ficha salva no notebook" : "ainda sem ficha: criar"}</small></div><span class="sub">›</span></div>`).join("")}
    <div class="item" data-a="ficha-mesa-outra"><div class="tx"><b>Outra pessoa…</b><small>Digite um nome e crie uma ficha nova</small></div><span class="sub">›</span></div></div>`,
  `<button class="botao leve" data-a="fechar">Agora não</button>`);
}
A["ficha-mesa-menu"] = () => { fecharFolha(); pedirFichaMesa(); };
function lerSenhaFolha() {
  if ($("#ss-s")) { sessao.senha = $("#ss-s").value.trim(); try { localStorage.setItem(CH_SENHA, sessao.senha); } catch (e) { /* sem storage */ } }
}
A["ficha-mesa"] = (el) => { lerSenhaFolha(); fecharFolha(); entrarComFicha(el.dataset.n, el.dataset.s); };
A["ficha-mesa-outra"] = () => {
  const senha = $("#ss-s") ? `<label class="campo"><span>Senha da mesa</span><input id="ss-s" value="${esc(sessao.senha)}" maxlength="20" inputmode="numeric" autocomplete="off"></label>` : "";
  folha("Outra pessoa", `<label class="campo"><span>Seu nome</span><input id="fo-n" maxlength="30" autocomplete="off"></label>${senha}`,
    `<button class="botao leve" data-a="ficha-mesa-menu">‹ Voltar</button><button class="botao prim" data-a="ficha-mesa-outra-ok">Entrar</button>`);
};
A["ficha-mesa-outra-ok"] = () => {
  const n = $("#fo-n").value.trim(), s = slugNome(n);
  if (!s) { $("#fo-n").focus(); toast("Digite um nome com letras ou números."); return; }
  lerSenhaFolha(); fecharFolha(); entrarComFicha(n, s);
};
async function entrarComFicha(nome, slug) {
  sessao.ficha = slug; sessao.fichaOk = false; sessao.fichaVer = ""; sessao.fichaEnviada = 0; sessao.criandoMesa = false;
  sessao.id = "";                       // nova entrada: a mesa dá o nome da ficha e uma chave deste aparelho
  await entrarSessao(nome, true);
  if (!sessao.conectado) { sessao.ficha = ""; try { localStorage.setItem(CH_FICHA, ""); } catch (e) { /* sem storage */ } }
}

// Baixa a ficha do notebook. Se o celular tem uma versão mais nova (mudou sem sinal), ela vale e vai para o notebook.
async function carregarFichaMesa(depois = false) {
  if (!sessao.ficha || !sessao.id || baixandoArq) return false;
  baixandoArq = true;
  try {
    let r;
    try { r = await api("/api/ficha-arq?id=" + encodeURIComponent(sessao.id) + "&k=" + sessao.chave); } catch (e) { return false; }
    if (!r.ok) return false;
    const chave = chaveMesa(), local = banco.fichas[chave], desvio = (r.agora || Date.now()) - Date.now();   // relógio do notebook × do celular
    const localAtual = naFichaDaMesa() ? S : local;
    if (r.existe) {
      const localMaisNova = localAtual && (localAtual._salvo || 0) + desvio > r.mtime + 2000 && localAtual._salvo !== sessao.fichaEnviada;
      sessao.fichaVer = r.ver;
      if (localMaisNova) {
        if (!naFichaDaMesa()) { banco.fichas[chave] = localAtual; abrirFicha(chave); }
        sessao.fichaOk = true; enviarFichaMesa(true); return true;
      }
      const s = normalizar(r.ficha); s._salvo = r.mtime - desvio;
      banco.fichas[chave] = s; gravarLocal(); sessao.fichaEnviada = s._salvo;
      if (naFichaDaMesa() || depois) { S = normalizar(s); banco.atual = chave; if (!sessao.fichaOk && !depois) banco.modo = "jogo"; render(); if (depois) toast("O mestre atualizou a sua ficha."); }
      else abrirFicha(chave, "jogo");
      sessao.fichaOk = true;
      return true;
    }
    // o notebook ainda não tem ficha deste jogador
    sessao.fichaOk = true;
    if (local && local.identidade) { sessao.fichaVer = ""; if (!naFichaDaMesa()) abrirFicha(chave); enviarFichaMesa(true); return true; }
    sessao.fichaVer = "";
    sessao.criandoMesa = true;
    folha("Sem ficha ainda", `<p class="sub">Não há ficha de <b>${esc(nomeDaFichaMesa())}</b> no notebook do mestre. Crie uma agora ou traga a que você já tem no app instalado.</p>`,
      `<button class="botao leve" data-a="atualizar-ficha-ok">📲 Trazer do app</button><button class="botao prim" data-a="nova-mesa">✦ Criar ficha nova</button>`);
    return true;
  } finally { baixandoArq = false; }
}
A["nova-mesa"] = () => { fecharFolha(); sessao.criandoMesa = true; A["nova"](); };

// Devolve a ficha ao notebook depois de cada mudança (conferido a cada 1,5 s; só usa a rede quando mudou).
async function enviarFichaMesa(forcar = false) {
  if (!naFichaDaMesa() || !sessao.id || !sessao.conectado || !sessao.fichaOk || enviandoArq || baixandoArq) return;
  if (!forcar && S._salvo === sessao.fichaEnviada) return;
  enviandoArq = true;
  const alvo = S._salvo;
  try {
    const r = await api("/api/ficha-salvar", { id: sessao.id, estado: S, base: sessao.fichaVer || null, forcar }, 30000);
    if (r.ok) { sessao.fichaVer = r.ver; sessao.fichaEnviada = alvo; }
    else if (r.conflito) { sessao.fichaVer = r.ver; enviandoArq = false; carregarFichaMesa(true); return; }
  } catch (e) { /* sem sinal: tenta na próxima */ }
  enviandoArq = false;
}
setInterval(() => enviarFichaMesa(), 1500);

// "Atualizar minha ficha": troca a ficha do notebook pela que está no app instalado (outro endereço, então a ficha viaja no #f= do link).
A["atualizar-ficha"] = () => {
  if (!sessao.ficha) { pedirFichaMesa(); return; }
  folha("Atualizar minha ficha", `<p>Isto pega a ficha guardada no <b>app instalado</b> e troca a ficha de <b>${esc(nomeDaFichaMesa())}</b> no notebook do mestre.
    A ficha atual vai para a pasta de backup do mestre.</p><p class="sub">Vamos abrir o app e voltar para a mesa em seguida.</p>`,
    `<button class="botao leve" data-a="fechar">Cancelar</button><button class="botao prim" data-a="atualizar-ficha-ok">Continuar</button>`);
};
A["atualizar-ficha-ok"] = () => {
  try { localStorage.setItem(CH_ATUALIZAR, JSON.stringify({ slug: sessao.ficha, t: Date.now() })); } catch (e) { toast("Este navegador não guarda dados. Não dá para atualizar a ficha."); return; }
  location.href = PAGINA_APP + "#mesa=" + encodeURIComponent(location.origin) + "&atualizar=" + encodeURIComponent(sessao.ficha);
};
function intencaoAtualizar() {
  try { const x = JSON.parse(localStorage.getItem(CH_ATUALIZAR) || "null"); if (x && x.slug && Date.now() - x.t < 15 * 60 * 1000) return x; } catch (e) { /* sem storage */ }
  return null;
}
function limparIntencao() { try { localStorage.removeItem(CH_ATUALIZAR); } catch (e) { /* sem storage */ } }
function confirmarAtualizacao() {
  const s = fichaDoApp; fichaDoApp = null;
  if (!s) return;
  if (!sessao.ficha) { limparIntencao(); toast("Escolha primeiro a sua ficha da mesa e toque em Atualizar minha ficha."); return; }
  fichaDoApp = s;
  folha("Atualizar minha ficha?", `<p>Chegou do app: <b>${esc(s.identidade.nome || "sem nome")}</b>, nível ${esc(String(s.identidade.nivel || 1))}.</p>
    <p>Ela vai <b>substituir</b> a ficha de <b>${esc(nomeDaFichaMesa())}</b> no notebook do mestre.</p>`,
    `<button class="botao leve" data-a="atualizar-cancela">Cancelar</button><button class="botao prim" data-a="atualizar-confirma">Substituir</button>`);
}
A["atualizar-cancela"] = () => { fichaDoApp = null; limparIntencao(); fecharFolha(); };
A["atualizar-confirma"] = () => {
  const s = fichaDoApp; fichaDoApp = null; limparIntencao(); fecharFolha();
  if (!s || !sessao.ficha) return;
  const n = normalizar(s); n._salvo = Date.now();
  banco.fichas[chaveMesa()] = n; gravarLocal();
  abrirFicha(chaveMesa(), "jogo"); sessao.fichaOk = true; sessao.criandoMesa = false;
  enviarFichaMesa(true);
  toast(`Ficha de <b>${esc(nomeDaFichaMesa())}</b> atualizada no notebook.`);
};
