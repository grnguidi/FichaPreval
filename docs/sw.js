// Guarda o app no aparelho para funcionar sem internet.
const VERSAO = "prevalecentes-mesa-v2";
const ARQUIVOS = ["./", "./index.html", "./manifest.webmanifest", "./icone-192.png", "./icone-512.png"];
self.addEventListener("install", (e) => { e.waitUntil(caches.open(VERSAO).then((c) => c.addAll(ARQUIVOS)).then(() => self.skipWaiting())); });
self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== VERSAO).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;
  e.respondWith(caches.match(e.request).then((achado) => {
    const rede = fetch(e.request).then((r) => {
      if (r && (r.ok || r.type === "opaque")) { const cp = r.clone(); caches.open(VERSAO).then((c) => c.put(e.request, cp)); }
      return r;
    }).catch(() => achado);
    return achado || rede;
  }));
});
