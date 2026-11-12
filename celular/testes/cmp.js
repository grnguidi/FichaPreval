const R = require('../regras.js');
const casos = require('./casos.json'), D = require('./dados.json');
const arma = n => D.armas.find(x => x.nome === n), enc = n => D.encantamentos.find(x => x.nome === n), tal = n => D.talentos.find(x => x.nome === n);
const ord = o => Object.entries(o).sort((x, y) => x[0] < y[0] ? -1 : 1);
let falhas = 0;
for (const [i, c] of casos.entries()) {
  const I = c.in, O = c.out;
  const d = R.derivadas(I.a, I.nivel, new Set(I.tal), I.soma, ...I.ca);
  const dd = {}; for (const [k, v] of Object.entries(d)) dd[k] = (v && typeof v === 'object' && !Array.isArray(v)) ? ord(v) : v;
  const ar = arma(I.arma), rq = R.reqArma(ar, I.nv);
  const e = enc(I.enc), v = e.versoes.find(x => x.nivel === I.ver);
  const got = {
    d: dd, rq: ord(rq), falta: R.reqFalta(rq, I.a), sv: R.statusVersao(v, e.dominio, I.a, I.nivel, I.impl),
    st: R.statusTalento(D.talentos[I.tal_nome], I.slot, new Set(I.antes), I.a, new Set(I.trein), I.armas_eq, new Set(I.ja)),
    pts: R.pontosDeNivel(I.nivel, I.sem), ganho: R.ganhoNoNivel(I.nivel, I.sem), duplo: ord(R.reqUsoDuplo(rq, R.reqArma(D.armas[0], 1))),
    per: R.PERICIAS.map(([, atrs], j) => R.periciaFora(I.a, I.nivel, atrs || ['ARC'], I.pers[j])), dano: R.danoComDados(I.dano, I.extra),
  };
  for (const k of Object.keys(O)) {
    if (JSON.stringify(got[k]) !== JSON.stringify(O[k])) {
      if (falhas++ < 8) console.log('caso', i, k, '\n py', JSON.stringify(O[k]).slice(0, 300), '\n js', JSON.stringify(got[k]).slice(0, 300));
    }
  }
}
console.log('casos', casos.length, 'divergências', falhas);
