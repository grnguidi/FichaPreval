/* Regras de Prevalecentes (PREVA 3.1) — tradução fiel de regras.py */
(function (raiz) {
  "use strict";
  const ATRIBUTOS = ["VIT", "MEN", "TEN", "FOR", "DES", "INT", "FE", "ARC"];
  const NOMES_ATR = { VIT: "Vitalidade", MEN: "Mente", TEN: "Tenacidade", FOR: "Força", DES: "Destreza", INT: "Inteligência", FE: "Fé", ARC: "Arcano" };
  const ATR_POR_NOME = Object.fromEntries(Object.entries(NOMES_ATR).map(([k, v]) => [v, k]));
  const VALORES_INICIAIS = [16, 14, 12, 11, 10, 9, 8, 7];
  const NIVEL_MAX = 30;
  const PERICIAS = [
    ["Acrobacia", ["DES"], false], ["Adestramento", ["MEN"], true], ["Agricultura", ["INT", "DES"], true], ["Artes", ["MEN"], false],
    ["Atletismo", ["FOR"], false], ["Ciências", ["INT"], false], ["Costura", ["INT", "DES"], true], ["Crime", ["DES"], false],
    ["Furtividade", ["DES"], false], ["Gastronomia", ["INT", "DES"], false], ["História", ["FE"], false], ["Intuição", ["FE"], false],
    ["Investigação", ["INT"], false], ["Medicina", ["INT"], true], ["Navegação", ["INT", "DES"], false], ["Percepção", ["ARC"], false],
    ["Performance", ["MEN"], false], ["Persuasão", ["MEN"], false], ["Prevalência", null, true], ["Religião", ["FE"], false],
    ["Sorte", ["ARC"], false], ["Tática", ["ARC"], false], ["Tecnologia", ["INT"], true],
  ];
  const PERICIAS_ATAQUE = [["Luta", ["FOR", "DES"]], ["Pontaria", ["DES"]], ["Feitiçaria", ["INT"]], ["Desejo", ["FE"]]];
  const PERICIAS_DEFESA = [["Fortitude", "TEN", "Fortitude de Ferro"], ["Reflexo", "DES", "Reflexos de Gato"],
    ["Astúcia", "MEN", "Mente Blindada"], ["Vontade", "FE", "Vontade Inabalável"]];
  const RESISTENCIAS = [[20, "Fogo"], [30, "Cortante"], [40, "Impacto"], [50, "Veneno"], [60, "Sangramento"], [70, "Magia"], [80, "Magia Pura"], [90, "Sagrado"]];
  const CONDICOES = ["Veneno", "Podridão", "Sangramento", "Congelamento", "Sono", "Loucura", "Morte"];
  const LIMIARES_ACOES = [15, 30, 45, 55, 65, 75, 85, 95];
  const ACERTO_ARMA = { 1: 0, 2: 0, 3: 1, 4: 1, 5: 2, 6: 2, 7: 3, 8: 3, 9: 4, 10: 5 };
  const BONUS_SEM_ALMA = 2;
  const GRUPOS_ARMA = {
    "Adagas": ["Adaga"], "Espadas": ["Espada"], "Espada Grande": ["Espada Grande"], "Katana": ["Katana"],
    "Machado Grande": ["Machado Grande"], "Bastão": ["Bastão"], "Lança-Arma": ["Lança-Arma"], "Lâmina-Dínamo": ["Lâmina-Dínamo"],
    "Arco": ["Arco"], "Besta Pesada": ["Besta Pesada"], "Lira": ["Lira"], "Cajados e Selos": ["Cajado", "Selo"],
  };

  const fdiv = (a, b) => Math.floor(a / b);
  const cap = (v) => Math.max(0, Math.min(99, Math.trunc(Number(v) || 0)));

  function curva(p) {
    p = cap(p);
    let total = 0;
    for (let marco = 5; marco < 100; marco += 5) {
      if (p < marco) break;
      total += marco <= 20 ? 1 : marco <= 35 ? 2 : marco <= 55 ? 3 : marco <= 75 ? 4 : 5;
    }
    if (p >= 99) total += 2;
    return total;
  }
  const bonusCombate = (p) => { p = cap(p); return p >= 99 ? 5 : fdiv(p, 20); };
  const vantagem = (p) => cap(p) >= 60;
  function pontosDeNivel(nivel, semAlma) {
    nivel = Math.max(1, Math.min(NIVEL_MAX, nivel));
    return (10 + (semAlma ? BONUS_SEM_ALMA : 0)) * (nivel - 1) + 5 * fdiv(nivel, 3);
  }
  const ganhoNoNivel = (n, semAlma) => 10 + (n % 3 === 0 ? 5 : 0) + (semAlma ? BONUS_SEM_ALMA : 0);
  const nivelAlma = (n) => fdiv(n, 3);
  const maxNivelArma = (n) => Math.min(10, Math.ceil(n / 2));
  function slotsTalismas(nivel, tal) {
    let n = Math.min(5, 1 + fdiv(nivel, 6));
    if (tal.has("Colecionador de Talismãs")) n += 1;
    if (tal.has("Relicário")) n += 1;
    return n;
  }

  function derivadas(a, nivel, tal, vidaSoma, armCa = 0, escCa = 0, caExtra = 0) {
    const c = {}, bc = {};
    for (const k of ATRIBUTOS) { c[k] = curva(a[k]); bc[k] = bonusCombate(a[k]); }
    const d = { curva: c, bc };
    d.vida_dados = c.VIT + (tal.has("Vida Dura") ? 3 : 0);
    d.vida = 10 + 5 * (nivel - 1) + vidaSoma;
    let mana = 2 * cap(a.MEN) + 2 * c.MEN;
    if (tal.has("Mente Infinita")) mana = Math.trunc(mana * 1.5);
    d.mana = mana;
    d.vigor = 20 + cap(a.FOR) + c.FOR + (tal.has("Fôlego de Guerreiro") ? 10 : 0);
    d.vigor_regen = fdiv(c.FOR, 4);
    d.descoberta = 10 + 10 * fdiv(cap(a.ARC), 15);
    const caTen = Math.min(4, fdiv(cap(a.TEN), 20));
    d.ca_ten = caTen;
    d.ca = Math.max(10, Math.min(25, 10 + caTen + armCa + escCa + caExtra));
    let carga = 10 + 2 * cap(a.TEN) + fdiv(cap(a.FOR), 2) + c.TEN;
    carga += (tal.has("Mochileiro") ? 10 : 0) + (tal.has("Mula de Carga") ? 30 : 0);
    d.carga = carga;
    const des = cap(a.DES);
    d.movimento = 9 + (des >= 30 ? 3 * (1 + fdiv(des - 30, 15)) : 0) + (tal.has("Pé Ligeiro") ? 3 : 0);
    let acoes = LIMIARES_ACOES.filter((t) => des >= t).length;
    if (tal.has("Mão Extra") && des >= 40) acoes += 1;
    d.acoes_extras = acoes;
    d.iniciativa_dados = 1 + fdiv(des, 20);
    d.iniciativa_bonus = bc.DES;
    d.rd = Math.min(4, fdiv(cap(a.TEN), 20));
    const tenRes = cap(a.TEN) + (tal.has("Pele Grossa") ? 10 : 0);
    d.resistencias = RESISTENCIAS.filter(([lim]) => tenRes >= lim).map(([, n]) => n);
    d.n3 = fdiv(nivel, 3);
    d.dt_feiticaria = 10 + bc.INT + fdiv(nivel, 3);
    d.dt_desejo = 10 + bc.FE + fdiv(nivel, 3);
    d.espacos_encant = 1 + fdiv(cap(a.INT) + cap(a.FE), 6) + (tal.has("Cabeça Cheia") ? 1 : 0) + (tal.has("Mente Expandida") ? 1 : 0);
    d.contra_encant = fdiv(Math.max(cap(a.INT), cap(a.FE)), 10);
    d.dados_extra_magia = fdiv(cap(a.INT), 30);
    d.dados_extra_feitico = fdiv(cap(a.FE), 30);
    d.pericias_treinadas_max = 5 + fdiv(Math.max(cap(a.INT), cap(a.MEN)), 10) + (tal.has("Treinado") ? 1 : 0);
    d.alma_nivel = nivelAlma(nivel);
    d.alma_usos = 2 + fdiv(d.alma_nivel, 3);
    d.alma_ativas = 1 + [10, 20, 30].filter((x) => nivel >= x).length;
    d.talismas = slotsTalismas(nivel, tal);
    d.max_nivel_arma = maxNivelArma(nivel);
    return d;
  }

  function periciaFora(a, nivel, atrs, treinada) {
    let melhor = atrs[0];
    for (const k of atrs) if (cap(a[k]) > cap(a[melhor])) melhor = k;
    const val = cap(a[melhor]);
    return [melhor, fdiv(nivel, 2) + (treinada ? curva(val) : 0), 1 + fdiv(val, 20)];
  }

  function reqArma(arma, nv) {
    const out = {};
    for (const r of arma.req) out[r.attr] = r.base + r.por_nivel * (nv - 1);
    return out;
  }
  function reqFalta(reqs, a) {
    return Object.entries(reqs).filter(([k, v]) => a[k] < v).map(([k, v]) => `${NOMES_ATR[k].slice(0, 3).toUpperCase()} ${v} (tem ${cap(a[k])})`);
  }
  function reqUsoDuplo(r1, r2) {
    const out = {};
    for (const k of new Set([...Object.keys(r1), ...Object.keys(r2)])) {
      const x = r1[k] || 0, y = r2[k] || 0;
      out[k] = Math.max(x, y) + fdiv(Math.min(x, y), 2);
    }
    return out;
  }
  function danoComDados(dano, extra) {
    if (extra <= 0) return dano;
    const dados = [...dano.matchAll(/(\d+)d(\d+)/g)];
    if (!dados.length) return dano;
    const maior = Math.max(...dados.map((m) => +m[2]));
    const m = dados.find((x) => +x[2] === maior);
    const re = new RegExp(`\\b${m[1]}d${m[2]}\\b`);
    return dano.replace(re, `${+m[1] + extra}d${m[2]}`);
  }
  function statusVersao(v, dominio, a, nivel, implInicial = false) {
    const mot = [];
    for (const r of v.req_attrs) if (a[r.attr] < r.valor) mot.push(`${r.valor} ${NOMES_ATR[r.attr]} (tem ${cap(a[r.attr])})`);
    const nmin = 2 * v.nivel;
    if (nivel < nmin && !(v.nivel === 1 && implInicial)) mot.push(`nível ${nmin}`);
    return mot;
  }
  function statusTalento(t, nivelSlot, antes, a, treinadas, armasEq, jaEscolhidos) {
    const mot = [];
    if (t.nivel > nivelSlot) mot.push(`nível ${t.nivel}`);
    const req = t.requisito;
    if (req) {
      const m = req.match(/^99 de (\S+)/);
      if (m) {
        const k = ATR_POR_NOME[m[1].replace(/[^\wÀ-ÿ]/g, "")];
        if (k && a[k] < 99) mot.push(req);
      } else if (req.startsWith("Treinado em ")) {
        if (!treinadas.has(req.slice(12))) mot.push(req);
      } else if (GRUPOS_ARMA[req]) {
        if (!GRUPOS_ARMA[req].some((g) => armasEq.includes(g))) mot.push(`arma equipada: ${req}`);
      } else if (!antes.has(req)) mot.push(`talento: ${req}`);
    }
    if (jaEscolhidos.has(t.nome) && !t.descricao.includes("repetir")) mot.push("já escolhido");
    if (t.nome === "Mão Extra" && a.DES < 40) mot.push("40 Destreza");
    return mot;
  }


  // ---------------- Efeitos de talentos ----------------
  const EFEITOS_TALENTOS = {"Passos Leves": {"tipo": "perm", "ca": 1, "nota": "sem Armadura Pesada ou Colossal"}, "Contra-encantador": {"tipo": "perm", "contra": 1}, "Mão Verde": {"tipo": "perm", "pericia": {"Agricultura": 2}}, "Voz dos Animais": {"tipo": "perm", "pericia": {"Adestramento": 2}}, "Engenheiro": {"tipo": "perm", "pericia": {"Tecnologia": 2}}, "Sombra Perfeita": {"tipo": "perm", "pericia": {"Crime": 2}}, "Olhar Aguçado": {"tipo": "perm", "descoberta": 2}, "Identidade Forte": {"tipo": "perm", "dt_alma": 2}, "Estudioso": {"tipo": "perm", "aprendizado": 3}, "Primeiro passo": {"tipo": "sit", "ca": 1, "mov": 3, "nota": "primeiro turno do combate"}, "Provocador": {"tipo": "sit", "ca": 2, "nota": "contra o alvo provocado"}, "Defensor da Base": {"tipo": "sit", "ca": 2, "nota": "lutando dentro da Base"}, "Calmaria": {"tipo": "sit", "acerto": 2, "nota": "agiu por último, primeira rodada"}, "Oportunista": {"tipo": "sit", "acerto": 2, "nota": "Golpe de Oportunidade"}, "Ataque Cruzado": {"tipo": "sit", "acerto": 2, "nota": "ataque bônus após acertar o primeiro"}, "Pares Afinados": {"tipo": "sit", "acerto": 2, "nota": "ataque bônus com duas armas do mesmo grupo"}, "Mão de Falcão": {"tipo": "sit", "acerto": 2, "nota": "Mirar em Ponto Cego"}, "Caçador de Fraquezas": {"tipo": "sit", "acerto": 2, "dano_nivel": 1, "nota": "atacando um Ponto Chave"}, "Maestria": {"tipo": "sit", "acerto": 1, "nota": "com a arma escolhida"}, "Extasiado": {"tipo": "sit", "iniciativa": 5, "nota": "não ser o primeiro na iniciativa"}, "Navegante Nato": {"tipo": "sit", "pericia": {"Navegação": 3}, "nota": "em viagens"}, "Voz Encantadora": {"tipo": "sit", "pericia": {"Artes": 2}, "nota": "ao se apresentar em público"}};
  const ARMADURAS_PESADAS = new Set(["Armadura Pesada", "Armadura Reforçada", "Armadura Colossal"]);
  function efeitosTalentos(talentos, ativos, armadura = "") {
    const out = { ca: 0, mov: 0, acerto: 0, iniciativa: 0, descoberta: 0, contra: 0, dt_alma: 0, aprendizado: 0, dano_nivel: 0, pericia: {} };
    for (const nome of [...talentos].sort()) {
      const ef = EFEITOS_TALENTOS[nome];
      if (!ef || (ef.tipo === "sit" && !ativos.has(nome))) continue;
      if (nome === "Passos Leves" && ARMADURAS_PESADAS.has(armadura)) continue;
      for (const [k, v] of Object.entries(ef)) {
        if (k === "pericia") for (const [p, b] of Object.entries(v)) out.pericia[p] = (out.pericia[p] || 0) + b;
        else if (k in out) out[k] += v;
      }
    }
    return out;
  }
  // ---------------- Dados ----------------
  function rolarExpr(expr, rng, dobrar = false) {
    let total = 0; const partes = [];
    for (const m of String(expr || "").matchAll(/([+-]?)\s*(\d+)\s*d\s*(\d+)|([+-]?)\s*(\d+)/g)) {
      if (m[2]) {
        const sinal = m[1] === "-" ? -1 : 1; let q = +m[2]; const f = +m[3];
        if (dobrar) q *= 2;
        const vals = [...Array(q)].map(() => rng(f));
        const sub = sinal * vals.reduce((a, b) => a + b, 0);
        partes.push([`${sinal < 0 ? "-" : ""}${q}d${f}`, vals, sub]); total += sub;
      } else {
        const sinal = m[4] === "-" ? -1 : 1, sub = sinal * +m[5];
        partes.push([(sub >= 0 ? "+" : "") + sub, [], sub]); total += sub;
      }
    }
    return [total, partes];
  }
  function rolarAtaque(bonus, comVantagem, margem, rng) {
    const d = [...Array(comVantagem ? 2 : 1)].map(() => rng(20)), nat = Math.max(...d);
    return { d20: d, natural: nat, bonus, total: nat + bonus, critico: nat >= margem, garantido: nat === 20, desastre: nat === 1 };
  }
  const custoMana = (v) => { const m = String(v.mana || "").match(/(\d+)/); return m ? +m[1] : null; };
  function danoDoEncantamento(desc) {
    const m = String(desc || "").match(/\d+d\d+(?:\s*\+\s*\d+d\d+)*(?:\s*\+\s*\d+(?!d))?/);
    return m ? m[0].replace(/\s+/g, " ") : null;
  }

  const R = {
    ATRIBUTOS, NOMES_ATR, ATR_POR_NOME, VALORES_INICIAIS, NIVEL_MAX, PERICIAS, PERICIAS_ATAQUE, PERICIAS_DEFESA, RESISTENCIAS,
    CONDICOES, LIMIARES_ACOES, ACERTO_ARMA, GRUPOS_ARMA, BONUS_SEM_ALMA,
    cap, curva, bonusCombate, vantagem, pontosDeNivel, ganhoNoNivel, nivelAlma, maxNivelArma, slotsTalismas, derivadas,
    periciaFora, reqArma, reqFalta, reqUsoDuplo, danoComDados, statusVersao, statusTalento,
    EFEITOS_TALENTOS, ARMADURAS_PESADAS, efeitosTalentos, rolarExpr, rolarAtaque, custoMana, danoDoEncantamento,
  };
  if (typeof module !== "undefined" && module.exports) module.exports = R; else raiz.R = R;
})(typeof window !== "undefined" ? window : globalThis);
