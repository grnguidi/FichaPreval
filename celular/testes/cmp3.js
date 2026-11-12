// Compara as regras novas do celular com as do PC (casos de gen3.py).
const R = require("./regras_montado.js");
const { casos, itens } = require("./casos3.json");
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
console.log(`regras novas: ${casos.length} casos, ${erros} diferenças`);
process.exit(erros ? 1 : 0);
