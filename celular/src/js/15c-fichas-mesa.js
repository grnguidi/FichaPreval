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

const CH_COD = "prevalecentes.sessao.codigos";
const codigosMesa = () => { try { return JSON.parse(localStorage.getItem(CH_COD) || "{}") || {}; } catch (e) { return {}; } };
const guardarCodigoMesa = (slug, cod) => { const c = codigosMesa(); if (cod) c[slug] = cod; else delete c[slug]; try { localStorage.setItem(CH_COD, JSON.stringify(c)); } catch (e) { /* sem storage */ } };
const fotoMesa = (ref, cls = "avatar") => ref ? `<img class="${cls}" src="/api/foto?f=${ref}" alt="" loading="lazy">` : `<span class="${cls} vazio">☺</span>`;
async function atualizarFichasLista() {
  try { const r = await api("/api/sessao?id=" + encodeURIComponent(sessao.id || "")); if (r && Array.isArray(r.fichas)) sessao.fichasLista = r.fichas; } catch (e) { /* fica com a lista que tinha */ }
}
// As fichas são criadas pelo mestre. Cada uma fica presa ao primeiro jogador que a escolhe (ele cria um código).
function pedirFichaMesa() {
  const lista = sessao.fichasLista || [], cod = codigosMesa();
  folha("Quem é você?", `<p class="sub">Escolha a sua ficha. Ela fica guardada com o mestre e acompanha você na sessão. Na primeira vez você cria um código: só entra nela de novo quem souber o código.</p>
    ${sessao.pedeSenha ? `<label class="campo"><span>Senha da mesa</span><input id="ss-s" value="${esc(sessao.senha)}" maxlength="20" inputmode="numeric" autocomplete="off"></label>` : ""}
    <div class="lista">${lista.map((f) => {
      const minha = f.minha || (f.presa && cod[f.slug]);
      const sub = f.uso ? `em uso por ${esc(f.uso)}` : (f.tem ? `${esc(f.personagem || "sem nome")} · nível ${esc(String(f.nivel || 1))}` : "ainda sem ficha: você traz a sua ou cria do zero")
        + (minha ? " · é a sua" : f.presa ? " · já tem dono (pede o código)" : "");
      return `<div class="item ${f.uso ? "apagado" : ""}" data-a="ficha-mesa" data-s="${esc(f.slug)}" data-n="${esc(f.nome)}">${fotoMesa(f.foto ? f.slug + "&v=" + f.foto : "")}<div class="tx"><b>${esc(f.nome)}</b><small>${sub}</small></div><span class="sub">›</span></div>`;
    }).join("") || `<p class="sub">O mestre ainda não criou fichas para esta mesa.</p>`}</div>`,
  `<button class="botao leve" data-a="fechar">Agora não</button>`);
}
A["ficha-mesa-menu"] = async () => { fecharFolha(); await atualizarFichasLista(); pedirFichaMesa(); };
function lerSenhaFolha() {
  if ($("#ss-s")) { sessao.senha = $("#ss-s").value.trim(); try { localStorage.setItem(CH_SENHA, sessao.senha); } catch (e) { /* sem storage */ } }
}
A["ficha-mesa"] = (el) => {
  const f = (sessao.fichasLista || []).find((x) => x.slug === el.dataset.s) || { slug: el.dataset.s, nome: el.dataset.n };
  if (f.uso) { toast(`Esta ficha está em uso por <b>${esc(f.uso)}</b>.`); return; }
  lerSenhaFolha();
  const cod = codigosMesa()[f.slug];
  if (cod && (f.presa || f.minha)) { fecharFolha(); entrarComFicha(f.nome, f.slug, cod); return; }
  pedirCodigoFicha(f.nome, f.slug, !!f.presa);
};
function pedirCodigoFicha(nome, slug, presa, erro = "") {
  folha(esc(nome), `${erro ? `<p class="erro">${erro}</p>` : ""}<p class="sub">${presa ? "Esta ficha já tem dono. Digite o código dela (se esqueceu, o mestre vê o código ou libera a ficha)."
    : "Crie um código para esta ficha (3 a 12 letras ou números). Só entra nela de novo quem souber o código."}</p>
    <label class="campo"><span>Código da ficha</span><input id="fm-cod" maxlength="12" autocomplete="off" autocapitalize="off"></label>`,
    `<button class="botao leve" data-a="ficha-mesa-menu">‹ Voltar</button><button class="botao prim" data-a="ficha-mesa-cod" data-s="${esc(slug)}" data-n="${esc(nome)}">Entrar</button>`);
}
A["ficha-mesa-cod"] = (el) => {
  const cod = $("#fm-cod").value.trim();
  if (cod.length < 3) { $("#fm-cod").focus(); toast("O código precisa de pelo menos 3 caracteres."); return; }
  fecharFolha(); entrarComFicha(el.dataset.n, el.dataset.s, cod);
};
// A mesa recusou a ficha: mostra o motivo e volta para a escolha.
async function fichaRecusada(r) {
  const slug = sessao.ficha, nome = nomeDaFichaMesa();
  sessao.conectado = false; sessao.laco += 1; sessao.ficha = ""; sessao.id = "";
  try { localStorage.setItem(CH_FICHA, ""); } catch (e) { /* sem storage */ }
  pintarSessao();
  if (r.erro === "ficha_presa") { guardarCodigoMesa(slug, ""); pedirCodigoFicha(nome, slug, true, "Código errado para esta ficha."); return; }
  if (r.erro === "ficha_codigo") { pedirCodigoFicha(nome, slug, false); return; }
  toast(r.erro === "ficha_em_uso" ? `Esta ficha está em uso por <b>${esc(r.por || "outro jogador")}</b>.` : "Essa ficha não existe mais na mesa.", 5000);
  await atualizarFichasLista(); pedirFichaMesa();
}
async function entrarComFicha(nome, slug, codigo = "") {
  sessao.ficha = slug; sessao.codigo = codigo; sessao.fichaOk = false; sessao.fichaVer = ""; sessao.fichaEnviada = 0; sessao.criandoMesa = false;
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
    semFichaAinda();
    return true;
  } finally { baixandoArq = false; }
}
// A ficha da mesa ainda está vazia: o jogador liga uma ficha que já tem (deste aparelho, de um arquivo .json ou do app instalado) ou cria do zero.
function semFichaAinda() {
  const locais = Object.keys(banco.fichas).filter((k) => !k.startsWith("mesa-") && banco.fichas[k] && banco.fichas[k].identidade);
  folha("Sem ficha ainda", `<p class="sub">A ficha de <b>${esc(nomeDaFichaMesa())}</b> ainda está vazia. Ligue uma ficha que você já tem ou crie uma do zero; depois disso ela fica guardada com o mestre.</p>
    <div class="lista">${locais.map((k) => `<div class="item" data-a="mesa-de-local" data-id="${esc(k)}"><div class="tx"><b>${esc(banco.fichas[k].identidade.nome || "sem nome")}</b><small>ficha deste aparelho · nível ${esc(String(banco.fichas[k].identidade.nivel || 1))}</small></div><span class="sub">usar ›</span></div>`).join("")}
    <div class="item" data-a="mesa-de-arquivo"><div class="tx"><b>📂 Abrir um arquivo .json</b><small>Uma ficha exportada do app ou do programa de PC</small></div><span class="sub">›</span></div>
    <div class="item" data-a="atualizar-ficha-ok"><div class="tx"><b>📲 Trazer do app instalado</b><small>Pega a ficha guardada no app deste celular</small></div><span class="sub">›</span></div></div>`,
    `<button class="botao prim" data-a="nova-mesa">✦ Criar ficha do zero</button>`);
}
function adotarFichaMesa(s) {
  if (!sessao.ficha) return;
  const n = normalizar(JSON.parse(JSON.stringify(s))); n._salvo = Date.now();
  banco.fichas[chaveMesa()] = n; gravarLocal();
  abrirFicha(chaveMesa(), "jogo"); sessao.fichaOk = true; sessao.criandoMesa = false;
  enviarFichaMesa(true);
  toast(`Ficha <b>${esc(n.identidade.nome || "sem nome")}</b> ligada à mesa.`);
}
A["mesa-de-local"] = (el) => { const s = banco.fichas[el.dataset.id]; fecharFolha(); if (s) adotarFichaMesa(s); };
A["mesa-de-arquivo"] = () => {
  const inp = document.createElement("input"); inp.type = "file"; inp.accept = ".json,application/json";
  inp.onchange = () => {
    const arq = inp.files[0]; if (!arq) return;
    const rd = new FileReader();
    rd.onload = () => {
      try {
        const d = JSON.parse(rd.result);
        if (!d || !d.identidade) throw new Error("não é ficha");
        fecharFolha(); adotarFichaMesa(d);
      } catch (e) { toast("Este arquivo não é uma ficha de Prevalecentes."); }
    };
    rd.readAsText(arq);
  };
  inp.click();
};
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

// ------------------------------------------------------------------ foto do personagem
// A imagem é cortada em quadrado e reduzida a 256 px (JPEG) para caber na ficha e viajar pela sessão.
A["foto"] = () => {
  if (banco.modo !== "edicao" && S.foto) return;      // no modo jogo o toque na foto não troca nada
  const inp = document.createElement("input"); inp.type = "file"; inp.accept = "image/*";
  inp.onchange = () => {
    const arq = inp.files[0]; if (!arq) return;
    const url = URL.createObjectURL(arq), img = new Image();
    img.onload = () => {
      const lado = Math.min(img.width, img.height), cv = document.createElement("canvas");
      cv.width = cv.height = 256;
      cv.getContext("2d").drawImage(img, (img.width - lado) / 2, (img.height - lado) / 2, lado, lado, 0, 0, 256, 256);
      URL.revokeObjectURL(url);
      const dados = cv.toDataURL("image/jpeg", 0.82);
      mudar((s) => { s.foto = dados; });
      toast("Foto do personagem guardada na ficha.");
    };
    img.onerror = () => { URL.revokeObjectURL(url); toast("Não consegui ler essa imagem."); };
    img.src = url;
  };
  inp.click();
};
A["foto-tirar"] = () => { mudar((s) => { s.foto = ""; }); };
