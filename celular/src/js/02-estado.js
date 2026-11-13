// ------------------------------------------------------------------ estado
let S = null, C = null, aba = "ficha";
function novoEstado() {
  return {
    versao: 1, inicializado: true, sem_alma: false, especie_notas: "",
    identidade: { nome: "", player: "", nivel: 1, especie: "", sonho: "", guilda: "" },
    atributos: Object.fromEntries(R.ATRIBUTOS.map((k) => [k, { inicial: "", niveis: "0", especie: "0", bonus: "0" }])),
    vida: { modo: "media", rolagens: [], atual: "", mana_atual: "", vigor_atual: "" },
    pericias: [], prevalencia_attr: "ARC", pericia_ataque: "Luta",
    armas: [{ grupo: "", nivel: "1", props: "" }, { grupo: "", nivel: "1", props: "" }],
    equip: { armadura: "", escudo: "", ca_extra: "", peitoral_set: false },
    encantamentos: [], talentos: Object.fromEntries(SLOTS.map((s) => [s, ""])),
    alma: { nome: "", atr: "INT", restantes: "", historia: "", habilidades: [] },
    talismas: [...Array(7)].map(() => ({ nome: "", efeito: "" })),
    set: {}, inventario: [], dinheiro: "",
    condicoes: Object.fromEntries(R.CONDICOES.map((n) => [n, { max: "100", atual: "", notas: "" }])),
    portao: { Sucessos: [false, false, false, false, false], Falhas: [false, false, false, false, false] }, cicatrizes: "",
    vinculos: { grupo: "", mundo: "", metas: "" }, receitas: "",
    manual: {}, talentos_ativos: [], talentos_escolha: {}, desgaste: {}, descansos_curtos: 0,
    acoes_extras_tipos: [], turno: {}, usos: {}, contra_usados: 0, recursos: {}, dinheiro_c: 0, diario: [],
    meta: { caminho: "", mentor: "", etapas: [false, false, false], concluidas: 0, notas: "" },
  };
}
function normalizar(s) {
  const b = novoEstado();
  const out = Object.assign(b, s || {});
  out.identidade = Object.assign(b.identidade, (s || {}).identidade);
  out.vida = Object.assign(novoEstado().vida, out.vida);
  out.equip = Object.assign(novoEstado().equip, out.equip);
  for (const k of R.ATRIBUTOS) out.atributos[k] = Object.assign({ inicial: "", niveis: "0", especie: "0", bonus: "0" }, (out.atributos || {})[k]);
  out.talentos = Object.assign(Object.fromEntries(SLOTS.concat(META_SLOTS).map((x) => [x, ""])), out.talentos);
  while (out.armas.length < 2) out.armas.push({ grupo: "", nivel: "1", props: "" });
  while (out.talismas.length < 7) out.talismas.push({ nome: "", efeito: "" });
  out.portao = Object.assign(novoEstado().portao, out.portao);
  out.condicoes = Object.assign(novoEstado().condicoes, out.condicoes);
  out.manual = Object.assign({}, out.manual || {});
  out.talentos_ativos = Array.isArray(out.talentos_ativos) ? out.talentos_ativos : [];
  out.inventario = (Array.isArray(out.inventario) ? out.inventario : []).filter((i) => i && (String(i.item || "").trim() || String(i.carga || "").trim()));
  out.set = Object.assign({}, out.set || {});
  out.desgaste = Object.assign({}, out.desgaste || {});
  out.talentos_escolha = Object.assign({}, out.talentos_escolha || {});
  out.acoes_extras_tipos = Array.isArray(out.acoes_extras_tipos) ? out.acoes_extras_tipos : [];
  out.turno = Object.assign({}, out.turno || {});
  out.usos = Object.assign({}, out.usos || {});
  out.contra_usados = int(out.contra_usados);
  out.recursos = Object.assign({}, out.recursos || {});
  out.diario = Array.isArray(out.diario) ? out.diario.slice(0, 100) : [];
  out.meta = Object.assign({ caminho: "", mentor: "", etapas: [false, false, false], concluidas: 0, notas: "" }, out.meta || {});
  if (!Array.isArray(out.meta.etapas)) out.meta.etapas = [false, false, false];
  if (!out.meta.notas && out.vinculos && out.vinculos.metas) out.meta.notas = out.vinculos.metas;
  if (s && s.dinheiro_c == null) {   // ficha antiga (ou do PC antigo): lê o dinheiro escrito à mão
    const v = R.lerDinheiro(out.dinheiro);
    out.dinheiro_c = v == null ? 0 : v;
    if (v == null && out.dinheiro) out.dinheiro_nota = out.dinheiro;
  }
  out.dinheiro_c = Math.max(0, int(out.dinheiro_c));
  out.alma.habilidades = (Array.isArray(out.alma.habilidades) ? out.alma.habilidades : []).filter((h) => h && (h.nome || h.efeito))
    .map((h) => Object.assign({ nome: "", efeito: "", tipo: "", cats: [], tabela: "", ajustes: [], execucao: "" }, h));
  out.descansos_curtos = int(out.descansos_curtos);
  return out;
}
function salvar() {
  if (!S || !banco.atual) return;
  if (S.dinheiro_c != null) S.dinheiro = R.formatarDinheiro(S.dinheiro_c) + (S.dinheiro_nota ? ` (${S.dinheiro_nota})` : "");
  S._salvo = Date.now();
  banco.fichas[banco.atual] = S;
  gravarLocal();
  enviarNuvem(banco.atual);
}
function mudar(fn) { fn(S); salvar(); render(); }

