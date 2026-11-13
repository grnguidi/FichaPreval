/* Ficha Prevalecentes — versão de mesa para celular */
"use strict";
const D = window.DADOS, R = window.R;
const $ = (s, el = document) => el.querySelector(s);
const esc = (t) => String(t ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const int = (v, d = 0) => { const n = parseInt(String(v ?? "").replace("+", ""), 10); return Number.isFinite(n) ? n : d; };
const OK = "✓", NO = "✗";
const ARMAS = Object.fromEntries(D.armas.map((a) => [a.nome, a]));
const ENC = Object.fromEntries(D.encantamentos.map((e) => [e.nome, e]));
const TAL = {}; D.talentos.forEach((t) => { if (!TAL[t.nome]) TAL[t.nome] = t; });
const TALISMA = Object.fromEntries(D.talismas.map((t) => [t.nome, t]));
const SETS = Object.fromEntries((D.sets || []).map((x) => [x.nome, x]));
const PECAS = ["Capacete", "Peitoral", "Manopla", "Calça", "Bota", "Arma"];
const ITENS = D.itens || [];
const ITEM = Object.fromEntries(ITENS.map((i) => [i.nome.toLowerCase(), i]));
const itemLivro = (nome) => ITEM[String(nome || "").trim().toLowerCase()];
const SLOTS = [...Array(15)].map((_, i) => String(2 + 2 * i)).concat(["extra"]);
const META_SLOTS = [...Array(5)].map((_, i) => "meta" + (i + 1));   // talento extra de cada Meta de Vida concluída
const A = {};   // ações dos botões: data-a="nome" chama A["nome"]
const CATS_TAL = [...new Set(D.talentos.map((t) => t.categoria))].sort();
const CATS_ENC = [...new Set(D.encantamentos.map((e) => e.categoria))];
const TIERS = [...new Set(D.encantamentos.flatMap((e) => e.versoes.map((v) => v.tier)))].sort();

