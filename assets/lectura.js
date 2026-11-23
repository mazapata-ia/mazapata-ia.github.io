/* Ofrenda: panel de lectura y accesibilidad.
   Los ajustes se aplican con atributos data-lec-* y variables CSS en <html>,
   se guardan en localStorage y se recuperan antes de pintar la página
   (ver el script en línea del <head>). */
(function () {
  "use strict";
  var CLAVE = "ofrenda-lectura";
  var html = document.documentElement;
  var TAMANOS = [0.85, 0.92, 1, 1.1, 1.2, 1.32, 1.45, 1.6, 1.8, 2];
  var INTER = { original: null, amplio: 1.2, "muy-amplio": 1.45 };
  var LETRAS = { original: null, amplio: "0.04em", "muy-amplio": "0.08em" };
  var PALABRAS = { original: null, amplio: "0.14em", "muy-amplio": "0.3em" };
  var BASE = {
    t: 1, fuente: "original", inter: "original", letras: "original", palabras: "original",
    alinear: "original", tema: "original", fondo: "#F2EEE8", texto: "#1B1A18",
    ancho: "medio", enfoque: false, decoracion: true, anim: "normal"
  };
  var VARS_COLOR = ["--paper", "--paper-2", "--ink", "--ink-soft", "--rule", "--accent", "--hoja", "--banda", "--banda-texto"];

  /* ---------- color y contraste (WCAG) ---------- */
  function rgb(h) { h = h.replace("#", ""); if (h.length === 3) h = h.replace(/./g, "$&$&"); return [0, 2, 4].map(function (i) { return parseInt(h.substr(i, 2), 16); }); }
  function hex(c) { return "#" + c.map(function (x) { x = Math.max(0, Math.min(255, Math.round(x))); return (x < 16 ? "0" : "") + x.toString(16); }).join("").toUpperCase(); }
  function lum(h) { return rgb(h).map(function (v) { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }).reduce(function (a, v, i) { return a + v * [0.2126, 0.7152, 0.0722][i]; }, 0); }
  function contraste(a, b) { var x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); }
  function mezcla(a, b, p) { var x = rgb(a), y = rgb(b); return hex(x.map(function (v, i) { return v + (y[i] - v) * p; })); }
  /* Acerca el color del texto al negro o al blanco hasta alcanzar el contraste pedido. */
  function asegurar(texto, fondo, minimo) {
    if (contraste(texto, fondo) >= minimo) return texto;
    var meta = contraste("#000000", fondo) >= contraste("#FFFFFF", fondo) ? "#000000" : "#FFFFFF";
    for (var p = 0.05; p <= 1.0001; p += 0.05) { var c = mezcla(texto, meta, p); if (contraste(c, fondo) >= minimo) return c; }
    return meta;
  }
  function coloresPersonales(fondo, texto) {
    var ink = asegurar(texto, fondo, 7);
    var claro = lum(fondo) > 0.4;
    var hoja = mezcla(fondo, claro ? "#FFFFFF" : "#000000", 0.35);
    if (contraste(ink, hoja) < 7) hoja = fondo;
    var suave = asegurar(mezcla(ink, fondo, 0.28), fondo, 4.5);
    return {
      ajustado: ink !== texto, ink: ink,
      vars: { "--paper": fondo, "--paper-2": mezcla(fondo, ink, 0.07), "--ink": ink, "--ink-soft": suave,
              "--rule": mezcla(fondo, ink, 0.28), "--accent": suave, "--hoja": hoja, "--banda": ink, "--banda-texto": fondo },
      esquema: claro ? "light" : "dark"
    };
  }

  /* ---------- estado ---------- */
  var s = leer();
  function leer() {
    var o = {};
    try { var g = JSON.parse(localStorage.getItem(CLAVE) || "null"); if (g && g.s) o = g.s; } catch (e) {}
    var r = {}; for (var k in BASE) r[k] = (k in o) ? o[k] : BASE[k];
    return r;
  }
  function calcular() {
    var a = {}, v = {};
    if (s.t !== 1) { a.t = String(s.t); v["--lec-t"] = String(s.t); }
    if (s.fuente !== "original") a.fuente = s.fuente;
    if (INTER[s.inter]) { a.inter = s.inter; v["--lec-i"] = String(INTER[s.inter]); }
    if (LETRAS[s.letras]) { a.letras = s.letras; v["--lec-l"] = LETRAS[s.letras]; }
    if (PALABRAS[s.palabras]) { a.palabras = s.palabras; v["--lec-w"] = PALABRAS[s.palabras]; }
    if (s.alinear !== "original") a.alinear = s.alinear;
    if (s.ancho !== "medio") a.ancho = s.ancho;
    if (s.enfoque) a.enfoque = "si";
    if (!s.decoracion) a.decoracion = "no";
    if (s.anim !== "normal") a.anim = s.anim;
    if (s.tema === "personal") {
      var c = coloresPersonales(s.fondo, s.texto);
      a.tema = "personal";
      for (var k in c.vars) v[k] = c.vars[k];
      v["color-scheme"] = c.esquema;
    } else if (s.tema !== "original") a.tema = s.tema;
    return { a: a, v: v };
  }
  function aplicar(guardar) {
    var ap = calcular();
    Array.prototype.slice.call(html.attributes).forEach(function (at) {
      if (at.name.indexOf("data-lec-") === 0) html.removeAttribute(at.name);
    });
    ["--lec-t", "--lec-i", "--lec-l", "--lec-w", "color-scheme"].concat(VARS_COLOR).forEach(function (k) { html.style.removeProperty(k); });
    for (var k in ap.a) html.setAttribute("data-lec-" + k, ap.a[k]);
    for (var j in ap.v) html.style.setProperty(j, ap.v[j]);
    if (guardar) {
      try {
        var cambios = {}; for (var b in BASE) if (s[b] !== BASE[b]) cambios[b] = s[b];
        if (Object.keys(cambios).length) localStorage.setItem(CLAVE, JSON.stringify({ v: 1, s: cambios, ap: ap }));
        else localStorage.removeItem(CLAVE);
      } catch (e) {}
    }
  }
  window.addEventListener("storage", function (ev) { if (ev.key === CLAVE) { s = leer(); aplicar(false); sincronizar(); } });

  /* ---------- panel ---------- */
  var boton, panel, aviso, salida, menos, mas, bloquePersonal, notaContraste, titulo;

  function grupo(nombre, leyenda, opciones, extra) {
    var h = '<fieldset class="lec-grupo"><legend>' + leyenda + '</legend><div class="lec-opciones">';
    opciones.forEach(function (o) {
      h += '<label class="lec-op"><input type="radio" name="lec-' + nombre + '" value="' + o[0] + '"><span' +
           (o[2] ? ' style="' + o[2] + '"' : "") + '>' + o[1] + '</span></label>';
    });
    return h + '</div>' + (extra || "") + '</fieldset>';
  }
  function interruptor(nombre, texto, detalle) {
    return '<label class="lec-interruptor"><input type="checkbox" role="switch" name="lec-' + nombre + '" aria-describedby="lec-d-' + nombre + '">' +
           '<span><b>' + texto + '</b><small id="lec-d-' + nombre + '">' + detalle + '</small></span></label>';
  }
  function muestraColor(f, t) { return '<i class="lec-muestra-color" aria-hidden="true" style="background:' + f + ';color:' + t + '">a</i>'; }

  function construir() {
    boton = document.createElement("button");
    boton.type = "button";
    boton.className = "lec-boton";
    boton.setAttribute("aria-expanded", "false");
    boton.setAttribute("aria-controls", "lec-panel");
    boton.setAttribute("aria-label", "Ajustes de lectura y accesibilidad");
    boton.title = "Ajustes de lectura";
    boton.innerHTML = '<span aria-hidden="true">A<i>a</i></span>';

    panel = document.createElement("section");
    panel.id = "lec-panel";
    panel.className = "lec-panel";
    panel.hidden = true;
    panel.setAttribute("role", "dialog");
    panel.setAttribute("aria-modal", "false");
    panel.setAttribute("aria-labelledby", "lec-titulo");
    panel.innerHTML =
      '<div class="lec-cab"><div><span class="mono">Lectura · accesibilidad</span>' +
      '<h2 id="lec-titulo" tabindex="-1">Ajustes de lectura</h2></div>' +
      '<button type="button" class="lec-cerrar mono" aria-label="Cerrar ajustes de lectura">Cerrar</button></div>' +
      '<div class="lec-cuerpo">' +
        '<section class="lec-seccion" aria-labelledby="lec-s1"><h3 id="lec-s1">I · Texto</h3>' +
          '<div class="lec-grupo" role="group" aria-labelledby="lec-etq-t"><p class="lec-etq" id="lec-etq-t">Tamaño de letra</p><div class="lec-tamano">' +
            '<button type="button" data-tam="-1" aria-label="Reducir el tamaño de letra">A−</button>' +
            '<output id="lec-tam" aria-live="polite">100 %</output>' +
            '<button type="button" data-tam="1" aria-label="Aumentar el tamaño de letra">A+</button></div></div>' +
          grupo("fuente", "Tipografía", [["original", "Original", "font-family:Newsreader,Georgia,serif"],
            ["sans", "Sans serif", "font-family:'Atkinson Hyperlegible',Arial,sans-serif"],
            ["dislexia", "Para dislexia", "font-family:OpenDyslexic,Arial,sans-serif"]]) +
          grupo("inter", "Interlineado", [["original", "Original"], ["amplio", "Amplio"], ["muy-amplio", "Muy amplio"]]) +
          grupo("letras", "Espacio entre letras", [["original", "Original"], ["amplio", "Amplio"], ["muy-amplio", "Muy amplio"]]) +
          grupo("palabras", "Espacio entre palabras", [["original", "Original"], ["amplio", "Amplio"], ["muy-amplio", "Muy amplio"]]) +
          grupo("alinear", "Alineación", [["original", "Original"], ["izquierda", "Izquierda"], ["justificada", "Justificada"]]) +
        '</section>' +
        '<section class="lec-seccion" aria-labelledby="lec-s2"><h3 id="lec-s2">II · Colores</h3>' +
          grupo("tema", "Modo de color", [
            ["original", muestraColor("#F2EEE8", "#1B1A18") + "Original"],
            ["claro", muestraColor("#FFFFFF", "#141414") + "Claro"],
            ["oscuro", muestraColor("#171614", "#EAE5DC") + "Oscuro"],
            ["sepia", muestraColor("#F3E9D2", "#3A2E20") + "Sepia"],
            ["contraste", muestraColor("#000000", "#FFE14D") + "Alto contraste"],
            ["personal", "Personalizado"]],
            '<div class="lec-personal" id="lec-personal" hidden>' +
              '<label>Fondo<input type="color" name="lec-fondo"></label>' +
              '<label>Texto<input type="color" name="lec-texto"></label>' +
              '<p class="lec-contraste" id="lec-contraste" aria-live="polite"></p></div>') +
        '</section>' +
        '<section class="lec-seccion" aria-labelledby="lec-s3"><h3 id="lec-s3">III · Experiencia de lectura</h3>' +
          grupo("ancho", "Ancho del texto", [["estrecho", "Estrecho"], ["medio", "Medio"], ["amplio", "Amplio"]]) +
          '<div class="lec-grupo">' +
            interruptor("enfoque", "Lectura enfocada", "Oculta el pie, la franja de apoyo y los datos laterales, y atenúa la barra superior.") +
            interruptor("decoracion", "Ocultar decoración", "Quita grabados, dibujos, numerales e imágenes secundarias.") +
          '</div>' +
          grupo("anim", "Animaciones", [["normal", "Normales"], ["reducidas", "Reducidas"], ["ninguna", "Ninguna"]]) +
        '</section>' +
      '</div>' +
      '<div class="lec-pie"><button type="button" class="lec-restablecer mono">Restablecer todo</button>' +
      '<span class="lec-guardado">Se guarda en este navegador</span></div>' +
      '<p class="lec-sr" id="lec-aviso" aria-live="polite"></p>';

    document.body.appendChild(panel);
    document.body.appendChild(boton);

    aviso = panel.querySelector("#lec-aviso");
    salida = panel.querySelector("#lec-tam");
    menos = panel.querySelector('[data-tam="-1"]');
    mas = panel.querySelector('[data-tam="1"]');
    bloquePersonal = panel.querySelector("#lec-personal");
    notaContraste = panel.querySelector("#lec-contraste");
    titulo = panel.querySelector("#lec-titulo");

    boton.addEventListener("click", function () { panel.hidden ? abrir() : cerrar(true); });
    panel.querySelector(".lec-cerrar").addEventListener("click", function () { cerrar(true); });
    panel.querySelectorAll("[data-tam]").forEach(function (b) {
      b.addEventListener("click", function () {
        var i = TAMANOS.indexOf(s.t); if (i < 0) i = 2;
        i = Math.max(0, Math.min(TAMANOS.length - 1, i + parseInt(b.dataset.tam, 10)));
        s.t = TAMANOS[i]; cambio(); anunciar("Tamaño de letra: " + Math.round(s.t * 100) + " %");
      });
    });
    panel.addEventListener("change", function (ev) {
      var el = ev.target, n = (el.name || "").replace("lec-", "");
      if (!n) return;
      if (el.type === "radio") s[n] = el.value;
      else if (el.type === "checkbox") s[n] = n === "decoracion" ? !el.checked : el.checked;
      else if (el.type === "color") { s[n] = el.value.toUpperCase(); s.tema = "personal"; }
      else return;
      cambio();
      if (el.type === "radio") anunciar(textoGrupo(el) + ": " + el.parentNode.textContent.trim());
      if (el.type === "checkbox") anunciar(el.parentNode.querySelector("b").textContent + (el.checked ? ": activado" : ": desactivado"));
    });
    panel.addEventListener("input", function (ev) {
      if (ev.target.type === "color") { s[ev.target.name.replace("lec-", "")] = ev.target.value.toUpperCase(); s.tema = "personal"; cambio(); }
    });
    panel.querySelector(".lec-restablecer").addEventListener("click", function () {
      for (var k in BASE) s[k] = BASE[k];
      cambio(); anunciar("Se restablecieron todos los ajustes de lectura");
      titulo.focus();
    });
    document.addEventListener("keydown", function (ev) {
      if (ev.key === "Escape" && !panel.hidden) { ev.stopPropagation(); cerrar(true); }
    }, true);
    sincronizar();
  }
  function textoGrupo(el) { var f = el.closest("fieldset"); return f ? f.querySelector("legend").textContent : ""; }
  function anunciar(t) { aviso.textContent = ""; setTimeout(function () { aviso.textContent = t; }, 30); }
  function abrir() {
    panel.hidden = false; boton.setAttribute("aria-expanded", "true");
    titulo.focus();
  }
  function cerrar(devolverFoco) {
    panel.hidden = true; boton.setAttribute("aria-expanded", "false");
    if (devolverFoco) boton.focus();
  }
  function cambio() { aplicar(true); sincronizar(); }
  function sincronizar() {
    if (!panel) return;
    panel.querySelectorAll('input[type="radio"]').forEach(function (r) { r.checked = s[r.name.replace("lec-", "")] === r.value; });
    panel.querySelector('[name="lec-enfoque"]').checked = !!s.enfoque;
    panel.querySelector('[name="lec-decoracion"]').checked = !s.decoracion;
    panel.querySelector('[name="lec-fondo"]').value = s.fondo.toLowerCase();
    panel.querySelector('[name="lec-texto"]').value = s.texto.toLowerCase();
    var i = TAMANOS.indexOf(s.t);
    salida.textContent = Math.round(s.t * 100) + " %";
    menos.disabled = i === 0; mas.disabled = i === TAMANOS.length - 1;
    bloquePersonal.hidden = s.tema !== "personal";
    if (s.tema === "personal") {
      var c = coloresPersonales(s.fondo, s.texto);
      var r = contraste(c.ink, s.fondo);
      notaContraste.innerHTML = "Contraste <b>" + r.toFixed(1).replace(".", ",") + " : 1</b> · " +
        (r >= 7 ? "muy legible" : "legible") +
        (c.ajustado ? ". Ajustamos el tono del texto (" + c.ink + ") para que se lea bien sobre ese fondo." : ".");
    }
  }

  aplicar(false);
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", construir);
  else construir();
})();
