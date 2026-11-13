// ------------------------------------------------------------------ armazenamento
const CHAVE = "prevalecentes.mesa.v1";
let banco = { fichas: {}, atual: null, tema: "dia", modo: "jogo" };
function lerLocal() { try { const x = JSON.parse(localStorage.getItem(CHAVE)); if (x && x.fichas) banco = Object.assign(banco, x); } catch (e) { /* sem storage */ } }
function gravarLocal() { try { localStorage.setItem(CHAVE, JSON.stringify(banco)); } catch (e) { /* cheio ou bloqueado */ } }
let nuvem = null, nuvemUid = null, timerNuvem = null;
async function ligarNuvem() {
  if (!window.claude || !window.claude.use) return;
  try {
    const db = await window.claude.use("db"), user = await window.claude.use("user");
    if (!db || !user) return;
    nuvemUid = await user.id();
    nuvem = db;
    if (!nuvemUid) { nuvem = null; return; }
    const snap = await Promise.race([db.collection("data/users/" + nuvemUid).get(),
      new Promise((_, rej) => setTimeout(() => rej(new Error("tempo")), 10000))]);
    let mudou = false;
    for (const d of snap.docs) {
      const dados = d.data();
      const id = d.id;
      if (!dados || !dados.estado) continue;
      const local = banco.fichas[id];
      if (!local || (dados.estado._salvo || 0) > (local._salvo || 0)) { banco.fichas[id] = dados.estado; mudou = true; }
    }
    if (mudou) { gravarLocal(); if (!S && banco.atual && banco.fichas[banco.atual]) abrirFicha(banco.atual); else render(); }
    if (mudou) toast("Fichas sincronizadas com a sua conta Claude.");
  } catch (e) { nuvem = null; }
}
function enviarNuvem(id) {
  if (!nuvem) return;
  clearTimeout(timerNuvem);
  timerNuvem = setTimeout(async () => {
    try {
      const ref = nuvem.collection("data/users/" + nuvemUid).doc(id);
      if (banco.fichas[id]) await ref.set({ estado: banco.fichas[id] }); else await ref.delete();
    } catch (e) { /* offline: fica no aparelho */ }
  }, 900);
}

