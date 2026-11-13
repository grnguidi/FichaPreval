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
  function rolarExpr(expr, rng, dobrar = false, mult = 2) {
    let total = 0; const partes = [];
    for (const m of String(expr || "").matchAll(/([+-]?)\s*(\d+)\s*d\s*(\d+)|([+-]?)\s*(\d+)/g)) {
      if (m[2]) {
        const sinal = m[1] === "-" ? -1 : 1; let q = +m[2]; const f = +m[3];
        if (dobrar) q *= mult;
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
  function rolarAtaque(bonus, comVantagem, margem, rng, desvantagem = false) {
    const dois = !!comVantagem !== !!desvantagem;
    const d = [...Array(dois ? 2 : 1)].map(() => rng(20)), nat = desvantagem && !comVantagem ? Math.min(...d) : Math.max(...d);
    return { d20: d, natural: nat, bonus, total: nat + bonus, critico: nat >= margem, garantido: nat === 20, desastre: nat === 1 };
  }
  const custoMana = (v) => { const m = String(v.mana || "").match(/(\d+)/); return m ? +m[1] : null; };
  function danoDoEncantamento(desc) {
    const m = String(desc || "").match(/\d+d\d+(?:\s*\+\s*\d+d\d+)*(?:\s*\+\s*\d+(?!d))?/);
    return m ? m[0].replace(/\s+/g, " ") : null;
  }

  // ---------------- Livro: tipos de dano, efeitos e condições (gerado de regras.py pelo build) ----------------
  const LIVRO = {};
  const { TIPOS_DANO, DANO_SEM_RD, EFEITOS_LIVRO, NOTA_EFEITOS, CONDICAO_TESTE, CONDICAO_ATIVA, CONDICAO_DESCANSO_CURTO,
    DESCANSOS_CURTOS_MAX, DESGASTE_TURNOS, PECAS_SET_PESO, DADO_INFERIOR } = LIVRO;
  const NOMES_DANO = (TIPOS_DANO || []).map((t) => t[0]);
  const DANO_MENTAL = new Set((TIPOS_DANO || []).filter((t) => t[1] === "Mental").map((t) => t[0]));
  function receberCondicao(acumulado, maximo, pontos, sucesso) {
    const rec = sucesso ? Math.floor(pontos / 2) : pontos, novo = Math.max(0, acumulado + rec);
    return maximo > 0 && novo >= maximo ? [rec, 0, true] : [rec, novo, false];
  }
  function defesasContraDano(valor, tipo, d, rng, fragilizado = false, loucura = false) {
    const notas = [];
    if (valor <= 0) return [valor, notas];
    let total = valor;
    if (tipo === "Direto") return [total, notas];
    if (loucura && DANO_MENTAL.has(tipo)) { total *= 2; notas.push("Loucura: dano mental em dobro"); }
    const rd = fragilizado || DANO_SEM_RD.includes(tipo) ? 0 : (d.rd | 0);
    if (rd) {
      const rolos = [...Array(rd)].map(() => rng(4)), s = rolos.reduce((a, b) => a + b, 0);
      total = Math.max(0, total - s); notas.push(`RD ${rd}d4 [${rolos.join(", ")}] −${s}`);
    } else if (fragilizado && d.rd) notas.push("Fragilizado: sem RD");
    if (tipo && (d.resistencias || []).includes(tipo) && !fragilizado) { total = Math.floor(total / 2); notas.push(`resistência a ${tipo}: metade`); }
    return [total, notas];
  }
  function rolarPericia(bonus, dados, rng) {
    const d = [...Array(Math.max(1, dados))].map(() => rng(20)), nat = Math.max(...d);
    return { d20: d, natural: nat, bonus, total: nat + bonus };
  }
  function rolarDefesa(bonus, comVantagem, rng) { return rolarPericia(bonus, comVantagem ? 2 : 1, rng); }
  function descanso(tipo, maximos, atuais, condicoes) {
    const novos = {}, cond = {};
    for (const [k, mx] of Object.entries(maximos)) { const at = k in atuais ? atuais[k] : mx; novos[k] = tipo === "longo" ? mx : Math.min(mx, at + Math.floor(mx / 2)); }
    for (const [n, v] of Object.entries(condicoes)) cond[n] = tipo === "longo" ? 0 : Math.max(0, v - CONDICAO_DESCANSO_CURTO);
    return [novos, cond];
  }
  const pocaoEspiritualDados = (nivel, curvaVit) => Math.max(2, Math.floor(nivel / 2) + Math.floor(curvaVit / 2));
  function desgasteAposAtaque(usados, critico, limite = DESGASTE_TURNOS) {
    if (critico) return [0, false];
    usados += 1;
    return [usados, usados >= limite];
  }
  function condicoesDoEncantamento(desc) {
    const out = [];
    for (const m of String(desc || "").matchAll(/(\d+d\d+(?:\s*\+\s*\d+d\d+)*(?:\s*\+\s*\d+(?!\d|\s*d\d))?)\s+(?:pontos\s+)?de\s+(Veneno|Podridão|Sangramento|Congelamento|Sono|Loucura|Morte)/gi)) {
      const nome = CONDICOES.find((c) => c.toLowerCase() === m[2].toLowerCase());
      out.push([m[1].replace(/\s+/g, " "), nome]);
    }
    return out;
  }
  function escalarArcano(expr, arcano, condicao) {
    const arc = cap(arcano), dados = [...String(expr).matchAll(/(\d+)d(\d+)/g)].map((m) => [+m[1], +m[2]]);
    const fixo = [...String(expr).matchAll(/\+\s*(\d+)(?!\d|d)/g)].reduce((t, m) => t + +m[1], 0);
    if (!dados.length) return expr;
    const copias = condicao === "Morte" ? 0 : Math.floor(arc / 20), inferiores = Math.floor(arc / 15), soma = {};
    for (const [q, f] of dados) soma[f] = (soma[f] || 0) + q * (1 + copias);
    const maior = Math.max(...dados.map((x) => x[1]));
    if (inferiores) { const inf = DADO_INFERIOR[maior] || 4; soma[inf] = (soma[inf] || 0) + inferiores; }
    const partes = Object.entries(soma).sort((a, b) => b[0] - a[0]).map(([f, q]) => `${q}d${f}`);
    return partes.join(" + ") + (fixo ? ` + ${fixo}` : "");
  }
  const pesoPecasSet = (pecas) => PECAS_SET_PESO.filter((p) => (pecas[p] || {}).set || (pecas[p] || {}).nome).length;
  function cargaExtraItens(inv, itensLivro) {
    const por = Object.fromEntries(itensLivro.map((i) => [i.nome.toLowerCase(), i]));
    let extra = 0;
    for (const it of inv) { const u = (por[String(it.item || "").trim().toLowerCase()] || {}).uso || {}; extra = Math.max(extra, u.carga | 0); }
    return extra;
  }
  function pesoInventario(inv) {
    let t = 0;
    for (const it of inv) {
      const c = parseFloat(String(it.carga || 0).replace(",", ".")) || 0;
      const q = Math.max(1, parseInt(String(it.qtd || 1), 10) || 1);
      t += c * q;
    }
    return t;
  }

  // ---------------- Talentos com escolha (tabela vem de regras.py pelo build) ----------------
  const { ESCOLHA_TALENTO, ROTULO_ESCOLHA, MATRICULA_MANA2 } = LIVRO;
  function efeitosEscolhas(slots, escolhas) {
    const out = { maestria: [], dominio: {}, escolas: [], mana: 0, espaco: 0, todas_escolas: false, cond_extra: {}, pericia_mestre: [], pendentes: [] };
    const nomes = new Set(Object.values(slots).filter(Boolean));
    const ordem = Object.keys(slots).sort((a, b) => ((a === "extra") - (b === "extra")) || ((/^\d+$/.test(a) ? +a : 99) - (/^\d+$/.test(b) ? +b : 99)));
    for (const slot of ordem) {
      const nome = slots[slot], tipo = ESCOLHA_TALENTO[nome];
      if (!tipo) continue;
      const v = String(escolhas[slot] || "").trim();
      if (!v) { out.pendentes.push(nome); continue; }
      if (nome === "Maestria" || nome === "Maestria dupla") { if (!out.maestria.includes(v)) out.maestria.push(v); }
      else if (nome === "Domínio") out.dominio[v] = (out.dominio[v] || 0) + 1 + (nomes.has("Arma de família") ? 1 : 0);
      else if (nome === "Matrícula") { if (!out.escolas.includes(v)) out.escolas.push(v); out.mana = Math.max(out.mana, 1); out.espaco = 1; }
      else if (nome === "Matrícula avançada") { if (v === MATRICULA_MANA2) out.mana = 2; else if (!out.escolas.includes(v)) out.escolas.push(v); }
      else if (nome === "Condição Endurecida") out.cond_extra[v] = (out.cond_extra[v] || 0) + 20;
      else if (nome === "Mestre das Perícias") { if (!out.pericia_mestre.includes(v)) out.pericia_mestre.push(v); }
    }
    if (nomes.has("Matrícula Suprema") && out.escolas.length) { out.todas_escolas = true; out.mana = Math.min(3, Math.max(out.mana, 1)); }
    return out;
  }
  function descontoMatricula(esc, escola, mana, espaco) {
    if (!esc.mana || !(esc.todas_escolas || esc.escolas.includes(escola))) return [mana, espaco];
    const m = mana == null ? null : (mana <= 0 ? mana : Math.max(1, mana - esc.mana));
    return [m, Math.max(1, espaco - (esc.espaco || 0))];
  }

  // ---------------- Propriedades de armas (tabela vem de regras.py pelo build) ----------------
  const { PROPRIEDADES, ELEMENTOS_PROP } = LIVRO;
  const NOMES_PROPRIEDADES = (PROPRIEDADES || []).map((p) => p[0]);
  const DADO_ACIMA = { 4: 6, 6: 8, 8: 10, 10: 12 };
  const lerProps = (t) => String(t || "").split(",").map((p) => p.trim()).filter(Boolean);
  const nomeProp = (p) => p.split("(")[0].trim();
  function problemasProps(props, maximo) {
    const nomes = props.map(nomeProp), m = [];
    if (props.length > maximo) m.push(`${props.length} propriedades, o limite é ${maximo}`);
    const rep = [...new Set(nomes.filter((n) => nomes.filter((x) => x === n).length > 1))].sort();
    if (rep.length) m.push("repetidas: " + rep.join(", "));
    if (nomes.includes("Poderosa") && !nomes.includes("Cruel")) m.push("Poderosa exige Cruel");
    if (props.some((p) => nomeProp(p) === "Elemental" && !p.includes("("))) m.push("Elemental sem elemento");
    return m;
  }
  function subirDado(expr) {
    const dados = [...String(expr).matchAll(/(\d+)d(\d+)/g)].map((m) => [+m[1], +m[2]]);
    if (!dados.length) return expr;
    if (Math.max(...dados.map((x) => x[1])) >= 12) return danoComDados(expr, 1);
    return String(expr).replace(/(\d+)d(\d+)/g, (_, q, f) => `${q}d${DADO_ACIMA[+f] || +f}`);
  }
  function efeitoProps(props, dano, critico) {
    const nomes = props.map(nomeProp);
    const out = { dano, margem: parseInt(critico, 10), mult: 2, acerto: 0, extras: [], desgaste: DESGASTE_TURNOS, voraz: false, furtividade: 0, forca_x2: false };
    if (nomes.includes("Pesada")) { out.dano = subirDado(out.dano); out.forca_x2 = true; }
    if (nomes.includes("Afiada")) out.dano = danoComDados(out.dano, 1);
    const fixo = (nomes.includes("Cruel") ? 3 : 0) + (nomes.includes("Poderosa") && nomes.includes("Cruel") ? 2 : 0);
    if (fixo) out.dano = `${out.dano} + ${fixo}`;
    if (nomes.includes("Certeira")) out.margem -= 1;
    if (nomes.includes("Destruidora")) out.mult = 3;
    if (nomes.includes("Equilibrada")) out.acerto = 1;
    if (nomes.includes("Reforçada")) out.desgaste = 4;
    out.voraz = nomes.includes("Voraz");
    if (nomes.includes("Discreta")) out.furtividade = 5;
    for (const p of props) {
      const n = nomeProp(p);
      if (n === "Elemental") { const el = p.includes("(") ? p.slice(p.indexOf("(") + 1, p.lastIndexOf(")")).trim() : ""; if (el) out.extras.push(["1d6", el, ""]); }
      else if (n === "Sagrada") out.extras.push(["1d6", "Sagrado", "contra profanos, mortos-vivos ou de Podridão"]);
      else if (n === "Profana") out.extras.push(["1d6", "Necrótico", "contra sagrados ou celestiais"]);
    }
    return out;
  }
  const reqComProps = (reqs, props) => props.map(nomeProp).includes("Pesada") && "FOR" in reqs ? Object.assign({}, reqs, { FOR: reqs.FOR * 2 }) : reqs;

  // ---------------- Ações em combate, usos, ações de arma, Alma, Metas, dinheiro (tabelas vêm de regras.py) ----------------
  const { TIPOS_ACAO, ACOES_LIVRO, NIVEL_RECARGA, EVENTO_RECARGA, RECURSOS_ARMA, ALMA_TABELAS, ALMA_CATEGORIAS, ALMA_EXECUCAO, ALMA_AJUSTES,
    CAMINHOS, ETAPAS_META, METAS_MAX, CONTOS_POR, MOEDAS } = LIVRO;
  const dtProvocar = (d, nivel) => 10 + d.bc.MEN + Math.floor(nivel / 3);
  function acoesDoTurno(extras, tipos) {
    const q = { Comum: 1, "Bônus": 1, Movimento: 1, "Reação": 1 };
    let faltam = 0;
    for (let i = 0; i < extras; i++) {
      let t = i < tipos.length ? tipos[i] : "";
      if (t !== "Comum" && t !== "Bônus") { faltam++; t = "Comum"; }
      q[t]++;
    }
    return [q, faltam];
  }
  const NUM_PT = { uma: 1, duas: 2, "três": 3 };
  function usosLimitados(texto) {
    const m = String(texto || "").match(/\b(\d+|uma|duas|três)\s*(?:x|vez(?:es)?)\s*por\s*(descanso curto|descanso longo|combate|cena|turno|rodada|dia)\b/i);
    if (!m) return null;
    const q = m[1].toLowerCase();
    return [/^\d+$/.test(q) ? +q : NUM_PT[q], m[2].toLowerCase()];
  }
  const recarrega = (periodo, evento) => (periodo in NIVEL_RECARGA ? NIVEL_RECARGA[periodo] : 3) <= EVENTO_RECARGA[evento];
  const N_TXT = { um: 1, uma: 1, dois: 2, duas: 2, "três": 3 };
  const TIPO_ACAO_RE = [["Completa", /a[çc][ãa]o completa/], ["Reação", /\brea[çc][ãa]o\b/], ["Bônus", /a[çc][ãa]o b[ôo]nus/],
    ["Comum", /a[çc][ãa]o comum/], ["Movimento", /a[çc][ãa]o de movimento/], ["Livre", /a[çc][ãa]o livre/]];
  const capitaliza = (x) => x.charAt(0).toUpperCase() + x.slice(1).toLowerCase();
  function acaoArma(nome, texto) {
    const t = texto || "", tl = t.toLowerCase();
    const out = { nome, acao: "", ataque: false, delta: 0, vantagem: 0, critico: false, acerto_garantido: false, mult: 0, teste: "", dt_attr: "", passiva: false, nota: false };
    const pos = TIPO_ACAO_RE.map(([tipo, rx]) => { const m = tl.match(rx); return m ? [m.index, tipo] : null; }).filter(Boolean);
    if (pos.length) out.acao = pos.sort((a, b) => a[0] - b[0] || (a[1] < b[1] ? -1 : 1))[0][1];
    const automatico = tl.startsWith("sempre que") && !/pode gastar|pode,? como uma rea/.test(tl);
    out.passiva = nome.toLowerCase().startsWith("passiva") || automatico || nome === "Nota";
    const c0 = nome.charAt(0);
    out.nota = ["•", "Nota", "Acúmulos de Melodia", "Paz", "Calma", "Melancolia"].includes(nome.trim()) || nome.length > 34 || (c0 !== c0.toUpperCase() && c0 === c0.toLowerCase());
    out.ataque = /\batac|\bataque|\bgolpe|\bestocada|\bdispar|\bcorte\b|teste de acerto|\btiro\b|explos/i.test(nome + " " + t) && !out.passiva;
    let delta = 0;
    for (const m of tl.matchAll(/([+\-−]?\s*\d+|um|uma|dois|duas|três)\s*n[íi]ve(?:l|is)\s*(?:de dano\s*)?(acima|a mais|abaixo|a menos|inferior)?/g)) {
      const q = m[1].replace("−", "-").replace(/ /g, "");
      const n = q in N_TXT ? N_TXT[q] : Math.abs(parseInt(q, 10));
      const dir = m[2] || "", neg = ["abaixo", "a menos", "inferior"].includes(dir) || q.startsWith("-");
      if (!dir && !q.startsWith("+") && !q.startsWith("-")) {
        const ctx = tl.slice(Math.max(0, m.index - 12), m.index);
        if (!ctx.includes("+") && !ctx.includes("-") && !ctx.includes("−")) continue;
      }
      delta += neg ? -n : n;
    }
    out.delta = delta;
    if (/com vantagem/.test(tl)) out.vantagem = 1;
    if (/com desvantagem/.test(tl)) out.vantagem = -1;
    out.critico = /cr[íi]tico (?:autom[áa]tico|garantido)/.test(tl);
    out.acerto_garantido = tl.includes("acerto garantido");
    let m = tl.match(/multiplicador do cr[íi]tico [^.]*?para (\d+)x/) || tl.match(/x2\s*->\s*x(\d)/);
    if (m) out.mult = +m[1];
    m = tl.match(/teste de (fortitude|reflexos?|vontade|ast[úu]cia)\s*\(dt 10 \+ b[ôo]nus de combate de (\w+)/);
    if (m) { out.teste = capitaliza(m[1]); out.dt_attr = ATR_POR_NOME[capitaliza(m[2])] || ""; }
    else { m = tl.match(/(?:resist[êe]ncia com|teste de) (fortitude|reflexos?|vontade|ast[úu]cia)/); if (m) out.teste = capitaliza(m[1]); }
    return out;
  }
  function linhaDanoNivel(tabela, nv, delta) {
    const alvo = Math.max(1, Math.min(10, nv + delta));
    return [tabela.find((x) => x.nivel === alvo) || tabela[tabela.length - 1], alvo];
  }
  function almaNivelEfetivo(nivelAlma, ajustes, nCat) {
    const sel = new Set(ajustes), soma = ALMA_AJUSTES.filter(([, t]) => sel.has(t)).reduce((s, [v]) => s + v, 0);
    return Math.max(0, Math.min(11, nivelAlma + soma - Math.max(0, nCat - 1)));
  }
  const almaDtAjuste = (aj) => (aj.includes("+3 na DT") ? 3 : 0) - (aj.includes("−3 na DT") ? 3 : 0);
  const almaValor = (tabela, nv) => { const v = ALMA_TABELAS[tabela]; return v ? v[Math.max(0, Math.min(11, nv))] : ""; };
  function recompensaMetas(c) { const n = Math.max(0, Math.min(METAS_MAX, parseInt(c, 10) || 0)); return { talentos: n, pontos: n >= 1 ? 5 : 0 }; }
  function precoEmContos(texto) {
    const t = String(texto || "").toLowerCase();
    let m = t.match(/(\d+)\s*contilhas?/); if (m) return +m[1] * CONTOS_POR.Contilha;
    m = t.match(/(\d+)\s*contos?\s*de\s*(prata|ouro)/); if (m) return +m[1] * CONTOS_POR[m[2]];
    m = t.match(/(\d+)\s*contos?/); return m ? +m[1] : null;
  }
  function separarMoedas(contos) {
    let resto = Math.max(0, parseInt(contos, 10) || 0); const out = {};
    for (const k of MOEDAS) { out[k] = Math.floor(resto / CONTOS_POR[k]); resto %= CONTOS_POR[k]; }
    return out;
  }
  function formatarDinheiro(contos) {
    const m = separarMoedas(contos), p = m.Contilha ? [`${m.Contilha} Contilha${m.Contilha > 1 ? "s" : ""}`] : [];
    for (const k of ["ouro", "prata"]) if (m[k]) p.push(`${m[k]} de ${k}`);
    if (m.Contos || !p.length) p.push(`${m.Contos} Conto${m.Contos === 1 ? "" : "s"}`);
    return p.join(", ");
  }
  function lerDinheiro(texto) {
    let t = String(texto || "").toLowerCase();
    if (!/\d/.test(t)) return null;
    let total = 0, achou = false;
    for (const [rx, mult] of [[/(\d+)\s*contilhas?/g, CONTOS_POR.Contilha], [/(\d+)\s*(?:contos?\s*)?(?:de\s*)?ouros?/g, CONTOS_POR.ouro], [/(\d+)\s*(?:contos?\s*)?(?:de\s*)?pratas?/g, CONTOS_POR.prata]]) {
      for (const m of t.matchAll(rx)) { total += +m[1] * mult; achou = true; }
      t = t.replace(rx, " ");
    }
    for (const m of t.matchAll(/(\d+)\s*(?:contos?)?/g)) { total += +m[1]; achou = true; }
    return achou ? total : null;
  }

  const R = {
    ATRIBUTOS, NOMES_ATR, ATR_POR_NOME, VALORES_INICIAIS, NIVEL_MAX, PERICIAS, PERICIAS_ATAQUE, PERICIAS_DEFESA, RESISTENCIAS,
    CONDICOES, LIMIARES_ACOES, ACERTO_ARMA, GRUPOS_ARMA, BONUS_SEM_ALMA,
    cap, curva, bonusCombate, vantagem, pontosDeNivel, ganhoNoNivel, nivelAlma, maxNivelArma, slotsTalismas, derivadas,
    periciaFora, reqArma, reqFalta, reqUsoDuplo, danoComDados, statusVersao, statusTalento,
    EFEITOS_TALENTOS, ARMADURAS_PESADAS, efeitosTalentos, rolarExpr, rolarAtaque, custoMana, danoDoEncantamento,
    TIPOS_DANO, NOMES_DANO, DANO_SEM_RD, EFEITOS_LIVRO, NOTA_EFEITOS, CONDICAO_TESTE, CONDICAO_ATIVA, DESCANSOS_CURTOS_MAX, DESGASTE_TURNOS,
    receberCondicao, defesasContraDano, rolarPericia, rolarDefesa, descanso, pocaoEspiritualDados, desgasteAposAtaque,
    condicoesDoEncantamento, escalarArcano, pesoPecasSet, cargaExtraItens, pesoInventario,
    ESCOLHA_TALENTO, ROTULO_ESCOLHA, MATRICULA_MANA2, efeitosEscolhas, descontoMatricula,
    PROPRIEDADES, NOMES_PROPRIEDADES, ELEMENTOS_PROP, lerProps, nomeProp, problemasProps, subirDado, efeitoProps, reqComProps,
    TIPOS_ACAO, ACOES_LIVRO, RECURSOS_ARMA, ALMA_TABELAS, ALMA_CATEGORIAS, ALMA_EXECUCAO, ALMA_AJUSTES, CAMINHOS, ETAPAS_META, METAS_MAX, CONTOS_POR, MOEDAS,
    dtProvocar, acoesDoTurno, usosLimitados, recarrega, acaoArma, linhaDanoNivel, almaNivelEfetivo, almaDtAjuste, almaValor, recompensaMetas,
    precoEmContos, separarMoedas, formatarDinheiro, lerDinheiro,
  };
  if (typeof module !== "undefined" && module.exports) module.exports = R; else raiz.R = R;
})(typeof window !== "undefined" ? window : globalThis);
