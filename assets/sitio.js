/* Ofrenda: grabados generativos, menú y filtro del índice. */
(function () {
  "use strict";
  var INK = "#1B1A18", PAPER = "#F2EEE8";
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function hashStr(s) {
    var h = 1779033703 ^ s.length;
    for (var i = 0; i < s.length; i++) { h = Math.imul(h ^ s.charCodeAt(i), 3432918353); h = (h << 13) | (h >>> 19); }
    return h >>> 0;
  }
  function rng(seed) {
    var a = seed;
    return function () {
      a = (a + 0x6D2B79F5) | 0;
      var t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  /* Grabado en linóleo: líneas blancas talladas sobre tinta, únicas para cada semilla. */
  function linocut(cv, animar) {
    var r = cv.getBoundingClientRect();
    if (!r.width || !r.height) return;
    var dpr = Math.min(2, window.devicePixelRatio || 1);
    var W = Math.round(r.width * dpr), H = Math.round(r.height * dpr);
    cv.width = W; cv.height = H;
    var ctx = cv.getContext("2d");
    var R = rng(hashStr(cv.dataset.seed || "x"));
    var dens = parseFloat(cv.dataset.density || "1");
    ctx.fillStyle = INK; ctx.fillRect(0, 0, W, H);
    var s = Math.min(W, H);
    var f = []; for (var i = 0; i < 8; i++) f.push(R());
    var k0 = 1.4 + f[0] * 3, k1 = 1.4 + f[1] * 3, k2 = 0.8 + f[2] * 2.2;
    function campo(x, y) { var u = x / s, v = y / s; return Math.sin(u * k0 + f[3] * 6.28) * 1.7 + Math.cos(v * k1 + f[4] * 6.28) * 1.7 + Math.sin((u + v) * k2 + f[5] * 6.28); }
    function masa(x, y) { var u = x / s, v = y / s; return Math.sin(u * 2.4 + f[6] * 6.28) + Math.cos(v * 2.0 + f[7] * 6.28) + Math.sin((u - v) * 3.2 + f[5] * 6.28) * 0.7; }
    var escala = Math.max(0.55, Math.min(1.5, r.width / 260));
    var N = Math.round((W * H) / (s * s) * 150 * dens);
    var paso = 2 * dpr, lineas = [];
    for (var n = 0; n < N; n++) {
      var x = R() * W, y = R() * H, largo = 30 + R() * 150, pts = [];
      for (var k = 0; k < largo; k++) {
        if (x < 0 || y < 0 || x > W || y > H || masa(x, y) < -0.8) break;
        pts.push(x, y);
        var a = campo(x, y);
        x += Math.cos(a) * paso; y += Math.sin(a) * paso;
      }
      if (pts.length > 16) lineas.push({ p: pts, w: (0.45 + R() * 1.7) * dpr * escala });
    }
    ctx.strokeStyle = PAPER; ctx.lineCap = "round";
    function trazar(L) {
      var p = L.p, m = p.length / 2;
      for (var j = 1; j < m; j++) {
        ctx.lineWidth = Math.max(0.35 * dpr, L.w * Math.sin(Math.PI * j / m));
        ctx.beginPath(); ctx.moveTo(p[2 * j - 2], p[2 * j - 1]); ctx.lineTo(p[2 * j], p[2 * j + 1]); ctx.stroke();
      }
    }
    function marco() {
      var m = Math.round(s * 0.045), j = 0.8 * dpr;
      ctx.lineWidth = Math.max(1, 1.3 * dpr * escala);
      ctx.beginPath();
      ctx.moveTo(m + R() * j, m); ctx.lineTo(W - m, m + R() * j); ctx.lineTo(W - m - R() * j, H - m); ctx.lineTo(m, H - m - R() * j); ctx.closePath();
      ctx.stroke();
    }
    if (!animar || reduce) { lineas.forEach(trazar); marco(); return; }
    var idx = 0, porCuadro = Math.max(4, Math.ceil(lineas.length / 30));
    (function sig() {
      for (var c = 0; c < porCuadro && idx < lineas.length; c++) trazar(lineas[idx++]);
      if (idx < lineas.length) requestAnimationFrame(sig); else marco();
    })();
  }
  function grabar(animarHero) {
    document.querySelectorAll("canvas[data-seed]").forEach(function (cv) {
      linocut(cv, animarHero && cv.classList.contains("hero-art"));
    });
  }

  /* Menú */
  var menu = document.getElementById("menu"), abrir = document.getElementById("menu-open"), cerrar = document.getElementById("menu-close");
  function setMenu(on) {
    menu.hidden = !on; abrir.setAttribute("aria-expanded", String(on));
    document.body.style.overflow = on ? "hidden" : "";
    (on ? cerrar : abrir).focus();
  }
  if (menu && abrir && cerrar) {
    abrir.addEventListener("click", function () { setMenu(true); });
    cerrar.addEventListener("click", function () { setMenu(false); });
    document.addEventListener("keydown", function (ev) { if (ev.key === "Escape" && !menu.hidden) setMenu(false); });
  }

  /* Filtro del índice en la portada */
  document.querySelectorAll(".pill[data-filtro]").forEach(function (b) {
    b.addEventListener("click", function () {
      var f = b.dataset.filtro;
      document.querySelectorAll(".pill[data-filtro]").forEach(function (x) { x.setAttribute("aria-pressed", String(x === b)); });
      document.querySelectorAll(".col[data-sec]").forEach(function (c) { c.classList.toggle("dim", f !== "todo" && c.dataset.sec !== f); });
    });
  });

  var t;
  window.addEventListener("resize", function () { clearTimeout(t); t = setTimeout(function () { grabar(false); }, 180); });
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", function () { grabar(true); });
  else grabar(true);
})();

/* Botón "Copiar llave" (Bre-B) */
document.addEventListener("click", function (ev) {
  var b = ev.target.closest && ev.target.closest("[data-copiar]");
  if (!b) return;
  var t = b.getAttribute("data-copiar"), orig = b.textContent;
  var listo = function () { b.textContent = "Copiada"; setTimeout(function () { b.textContent = orig; }, 1800); };
  if (navigator.clipboard) { navigator.clipboard.writeText(t).then(listo, function () {}); }
});

/* Pantalla de la portada: un texto al azar */
(function () {
  var datos = document.getElementById("pantalla-datos");
  var caja = document.querySelector(".pantalla");
  if (!datos || !caja) return;
  var lista; try { lista = JSON.parse(datos.textContent); } catch (e) { return; }
  if (!lista.length) return;
  var texto = caja.querySelector(".pantalla-texto"), fuente = caja.querySelector(".pantalla-fuente"),
      boton = caja.querySelector(".pantalla-otro"), actual = 0;
  function pintar(i) {
    var a = lista[i];
    texto.innerHTML = "";
    a.t.split(/\n[ \t]*\n/).forEach(function (q) {
      if (!q) return;
      var p = document.createElement("p"); p.textContent = q; texto.appendChild(p);
    });
    fuente.textContent = "De «" + a.titulo + "»";
    fuente.href = a.url;
    actual = i;
  }
  function otro() {
    if (lista.length < 2) return actual;
    var i; do { i = Math.floor(Math.random() * lista.length); } while (i === actual);
    return i;
  }
  pintar(otro());
  if (lista.length < 2) { boton.hidden = true; return; }
  boton.addEventListener("click", function () {
    var i = otro();
    texto.classList.add("cambia");
    setTimeout(function () { pintar(i); texto.classList.remove("cambia"); }, 350);
  });
})();
