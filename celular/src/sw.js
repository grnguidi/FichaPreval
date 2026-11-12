// Guarda o app no aparelho para funcionar sem internet.
// A página busca primeiro na rede (assim uma versão nova aparece na hora) e usa a cópia guardada sem internet.
const VERSAO = "prevalecentes-mesa-v5";
const ARQUIVOS = ["./", "./index.html", "./manifest.webmanifest", "./icone-192.png", "./icone-512.png"];
self.addEventListener("install", (e) => { e.waitUntil(caches.open(VERSAO).then((c) => c.addAll(ARQUIVOS)).then(() => self.skipWaiting())); });
self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== VERSAO).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});
const guardar = (req, r) => { if (r && (r.ok || r.type === "opaque")) { const cp = r.clone(); caches.open(VERSAO).then((c) => c.put(req, cp)); } return r; };
self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  const pagina = req.mode === "navigate" || new URL(req.url).pathname.endsWith(".html");
  if (pagina) {   // rede primeiro, com 4 s de limite; sem rede, a cópia guardada
    e.respondWith(Promise.race([
      fetch(req, { cache: "no-store" }).then((r) => guardar(req, r)),
      new Promise((_, falha) => setTimeout(falha, 4000)),
    ]).catch(() => caches.match(req).then((a) => a || caches.match("./index.html"))));
    return;
  }
  e.respondWith(caches.match(req).then((achado) => achado || fetch(req).then((r) => guardar(req, r))));
});
