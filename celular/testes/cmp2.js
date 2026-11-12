const R = require('../regras.js'); const casos = require('./casos2.json');
let f = 0;
for (const [i, c] of casos.entries()) {
  let k = 0; const rng = (fa) => (c.seq[k++] % fa) + 1;
  const ex = R.rolarExpr(c.expr, rng, c.dob);
  let k2 = 0; const rng2 = (fa) => (c.seq[k2++] % fa) + 1;
  const atk = R.rolarAtaque(c.atk_in[0], c.atk_in[1], c.atk_in[2], rng2);
  const got = { expr: ex, atk, ef: R.efeitosTalentos(new Set(c.tal), new Set(c.ativos), c.arm), dano: R.danoDoEncantamento(c.desc), custo: R.custoMana({ mana: c.mana }) };
  for (const key of Object.keys(c.out)) {
    const a = JSON.stringify(c.out[key], Object.keys(c.out[key] || {}).sort ? undefined : undefined), b = JSON.stringify(got[key]);
    const norm = (x) => JSON.stringify(x, (kk, v) => (v && typeof v === 'object' && !Array.isArray(v)) ? Object.fromEntries(Object.entries(v).sort()) : v);
    if (norm(c.out[key]) !== norm(got[key])) { if (f++ < 5) console.log(i, key, '\n py', norm(c.out[key]).slice(0, 200), '\n js', norm(got[key]).slice(0, 200)); }
  }
}
console.log('casos', casos.length, 'divergências', f);
