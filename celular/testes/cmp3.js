// Compara as regras novas do celular com as do PC (casos de gen3.py).
const R = require("./regras_montado.js");
const dados = require("./casos3.json"), { casos, itens, acoes, usos, extras, rec } = dados;
const igual = (a, b) => JSON.stringify(a) === JSON.stringify(b);
let erros = 0;
const falha = (c, oque, js, py) => { if (erros++ < 8) console.log("DIFERENTE:", oque, JSON.stringify(js), "≠", JSON.stringify(py)); };
for (const c of casos) {
  let i = 0; const rng = (f) => ((c.fila[i++] - 1) % f) + 1;
  const dano = R.defesasContraDano(c.valor, c.tipo, c.d, rng, c.frag, c.louc);
  if (!igual(dano, c.dano)) falha(c, "dano", dano, c.dano);
  const [ac, mx, pts, suc, esp] = c.cond, cond = R.receberCondicao(ac, mx, pts, suc);
  if (!igual(cond, esp)) falha(c, "condição", cond, esp);
  const ds = R.descanso(c.desc_tipo, c.maxs, c.ats, c.conds);
  if (!igual(ds, c.descanso)) falha(c, "descanso", ds, c.descanso);
  if (R.pocaoEspiritualDados(c.nv, c.cv) !== c.pocao) falha(c, "poção", R.pocaoEspiritualDados(c.nv, c.cv), c.pocao);
  const enc = R.condicoesDoEncantamento(c.desc).map(([e, n]) => [e, n, R.escalarArcano(e, c.arc, n)]);
  if (!igual(enc, c.enc)) falha(c, "arcano", enc, c.enc);
  if (R.pesoPecasSet(c.pecas) !== c.peso_set) falha(c, "peso set", R.pesoPecasSet(c.pecas), c.peso_set);
  if (R.cargaExtraItens(c.inv, itens) !== c.extra) falha(c, "mochila", R.cargaExtraItens(c.inv, itens), c.extra);
  if (Math.abs(R.pesoInventario(c.inv) - c.peso_inv) > 1e-9) falha(c, "peso inv", R.pesoInventario(c.inv), c.peso_inv);
  const ep = R.efeitoProps(c.props, c.linha_dano, c.linha_crit);
  if (!igual(ep, c.ef_props)) falha(c, "propriedades", ep, c.ef_props);
  const pp = R.problemasProps(c.props, c.mx_props);
  if (!igual(pp, c.prob_props)) falha(c, "problemas props", pp, c.prob_props);
  const rq = R.reqComProps(c.req_arma, c.props);
  if (!igual(rq, c.req_props)) falha(c, "req pesada", rq, c.req_props);
  const esc = R.efeitosEscolhas(c.slots, c.escolhas);
  if (!igual(esc, c.esc)) falha(c, "escolhas", esc, c.esc);
  const desc = R.descontoMatricula(esc, c.escola, c.mana, c.esp);
  if (!igual(desc, c.desconto)) falha(c, "matrícula", desc, c.desconto);
}
for (const x of (dados.sets || [])) {
  const c = R.condicoesDeSet(x.at); if (!igual(c, x.conds)) falha(null, "sets", c, x.conds);
  const ae = R.arcanoEscala(x.arc, new Set(x.tal)); if (!igual(ae, x.ae)) falha(null, "arcanoEscala", ae, x.ae);
  const e = R.escalarArcano(x.ex, ae[0], x.cn, ae[1]); if (!igual(e, x.esc)) falha(null, "escalar", e, x.esc);
}
for (const [n, t, esp] of acoes) { const r = R.acaoArma(n, t); if (!igual(r, esp)) falha(null, "ação de arma " + n, r, esp); }
for (const [t, esp] of usos) { const r = R.usosLimitados(t); if (!igual(r, esp)) falha(null, "usos", r, esp); }
for (const e of extras) {
  if (!igual(R.acoesDoTurno(e.n, e.tipos), e.turno)) falha(e, "turno", R.acoesDoTurno(e.n, e.tipos), e.turno);
  if (R.almaNivelEfetivo(e.nv, e.aj, e.nc) !== e.ne) falha(e, "alma nível", R.almaNivelEfetivo(e.nv, e.aj, e.nc), e.ne);
  if (R.almaValor(e.tab, e.ne) !== e.val) falha(e, "alma valor", R.almaValor(e.tab, e.ne), e.val);
  if (R.almaDtAjuste(e.aj) !== e.dtaj) falha(e, "alma DT", R.almaDtAjuste(e.aj), e.dtaj);
  if (!igual(R.separarMoedas(e.c), e.sep)) falha(e, "moedas", R.separarMoedas(e.c), e.sep);
  if (R.formatarDinheiro(e.c) !== e.fmt) falha(e, "formatar", R.formatarDinheiro(e.c), e.fmt);
  if (R.lerDinheiro(e.txt) !== e.ler) falha(e, "ler dinheiro " + e.txt, R.lerDinheiro(e.txt), e.ler);
  if (R.precoEmContos(e.txt) !== e.preco) falha(e, "preço " + e.txt, R.precoEmContos(e.txt), e.preco);
  if (!igual(R.recompensaMetas(e.metas_in), e.metas)) falha(e, "metas", R.recompensaMetas(e.metas_in), e.metas);
}
for (const [p, e, esp] of rec) if (R.recarrega(p, e) !== esp) falha(null, "recarga " + p + "/" + e, R.recarrega(p, e), esp);
console.log(`ações de arma ${acoes.length}, textos de usos ${usos.length}, extras ${extras.length}`);
console.log(`regras novas: ${casos.length} casos, ${erros} diferenças`);
process.exit(erros ? 1 : 0);
