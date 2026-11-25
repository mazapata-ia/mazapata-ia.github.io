#!/usr/bin/env python3
"""Genera el sitio estático de Ofrenda a partir de _fuente/escritos.json.

Uso: python3 _fuente/generar.py   (desde la raíz del repositorio)

Los textos se publican exactamente como están en escritos.json: el cuerpo se
escapa para HTML pero no se corrige ni se modifica.
"""
import datetime
import html
import json
import os
import re
import shutil

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATOS = json.load(open(os.path.join(RAIZ, "_fuente", "escritos.json"), encoding="utf-8"))
SITIO = DATOS["sitio"]
BASE = SITIO["base"]
URL = SITIO["url"].rstrip("/")
VERSION = datetime.datetime.now().strftime("%Y%m%d%H%M")
ANIO = datetime.date.today().year

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]
SECCIONES = {
    "breves": {"num": "I", "nombre": "Textos breves", "corto": "Breves", "titular": "Lo breve", "resumen": "Fragmentos, apuntes y piezas cortas que nacen de una lectura, una conversación o una imagen.", "desc": "Escritura de texto corto", "imagen": "grabado-breves"},
    "largos": {"num": "II", "nombre": "Textos largos", "corto": "Largos", "desc": "Escritura de texto largo", "imagen": "grabado-largos", "titular": "Lo extenso", "resumen": "Ensayos y crónicas que piden más tiempo, más páginas y una lectura sin prisa."},
    "lecturas": {"num": "III", "nombre": "Lecturas que me atraviesan", "corto": "Lecturas",
                 "desc": "Reflexiones sobre libros y artículos leídos", "imagen": "grabado-lecturas", "titular": "Lo que se lee", "resumen": "Reflexiones sobre libros y artículos leídos, y sobre lo que dejan después de cerrarlos."},
}
# Géneros de cada sección: al entrar a una sección se elige el género antes de llegar a los textos.
GENEROS = {
    "breves": [{"id": "poesia", "nombre": "Poesía", "cuaderno": True}],
    "largos": [{"id": "ensayo", "nombre": "Ensayo"}, {"id": "cronica", "nombre": "Crónica"}, {"id": "literatura", "nombre": "Literatura"}],
    "lecturas": [{"id": "libros", "nombre": "Libros"}, {"id": "articulos", "nombre": "Artículos"}],
}
ORDEN = ["breves", "largos", "lecturas"]
GENERADAS = ["breves", "largos", "lecturas", "acerca", "quien-habita", "apoyar", "enviar", "terminos", "derechos-de-autor", "privacidad", "escritos"]

e = lambda s: html.escape(str(s), quote=True)


def fecha(s):
    a, m, d = (int(x) for x in s.split("-"))
    return datetime.date(a, m, d)


def fecha_larga(s):
    d = fecha(s)
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


def mes_anio(s):
    d = fecha(s)
    return f"{MESES[d.month - 1]} {d.year}"


NUM_POEMA = re.compile(r"^[ \t]*(\d+)\.[ \t]*\n")


def texto_plano(x):
    if x.get("poemas"):
        return "\n\n".join(NUM_POEMA.sub("", t, count=1) for t in x["poemas"])
    if x.get("cuerpo"):
        return x["cuerpo"]
    return re.sub(r"<[^>]+>", " ", html.unescape(x.get("cuerpo_html", "")))


def minutos(x):
    return max(1, round(len(texto_plano(x).split()) / 210))


def extracto(x):
    if x.get("cita"):
        return x["cita"]
    if x.get("poemas"):
        lineas = [l.strip() for l in NUM_POEMA.sub("", x["poemas"][0], count=1).split("\n") if l.strip()]
        return " / ".join(lineas[:4]) + (" …" if len(lineas) > 4 else "")
    p = re.split(r"\n\s*\n", texto_plano(x).strip())[0]
    w = p.split()
    return " ".join(w[:32]) + " …" if len(w) > 32 else p


def descripcion(x):
    t = " ".join(texto_plano(x).split())
    return t if len(t) <= 158 else t[:155].rsplit(" ", 1)[0] + "…"


def etiqueta(x):
    return "Muestra" if x.get("muestra") else f"Nº {x['numero']:02d}"


def genero_de(x):
    g = x.get("genero") or GENEROS[x["seccion"]][0]["id"]
    return next(G for G in GENEROS[x["seccion"]] if G["id"] == g)


def url_escrito(x):
    return f"{BASE}escritos/{x['id']}/"


def lienzo(seed, cls="", dens=None):
    c = f' class="{cls}"' if cls else ""
    d = f' data-density="{dens}"' if dens else ""
    return f'<canvas{c} data-seed="{e(seed)}"{d} aria-hidden="true"></canvas>'


def obra(x, cls):
    o = x.get("obra")
    if not o:
        return ""
    autor = f", de {e(o['autor'])}" if o.get("autor") else ""
    return f'<p class="{cls}">Sobre <em>{e(o["titulo"])}</em>{autor}</p>'


def cubierta(x, dens="1.2", mini=False):
    """Imagen de la sección si existe; si no, grabado generativo único para el escrito."""
    img = SECCIONES[x["seccion"]].get("imagen")
    if not img:
        return lienzo(x["id"], dens=dens)
    suf = "-mini" if mini else ""
    return (f'<picture class="cubierta"><source srcset="{BASE}assets/{img}{suf}.webp" type="image/webp">'
            f'<img src="{BASE}assets/{img}{suf}.jpg" alt="" width="{300 if mini else 900}" '
            f'height="{400 if mini else 1200}" loading="lazy"></picture>')


MUESTRA_TAG = '<span class="tag-muestra">Muestra</span>'

# ---------- numeración ----------
ESCRITOS = DATOS["escritos"]
# Un cuaderno por autor: cada uno conserva su orden y su autoría.
CUADERNOS = DATOS.get("cuadernos", [])
PROPIO = next((C for C in CUADERNOS if C["autor"] == SITIO["autora"]), CUADERNOS[0] if CUADERNOS else None)
POEMAS = [t for C in CUADERNOS for t in C["poemas"]]


LIBROS = DATOS.get("libros", [])


def url_libro(L):
    return f"{BASE}{L['seccion']}/{L['genero']}/{L['id']}/"


def tapa_libro(L, cls="libro-tapa"):
    if L.get("portada"):
        return f'<img class="{cls} con-imagen" src="{BASE}{e(L["portada"])}" alt="Portada de {e(L["titulo"])}">'
    return (f'<div class="{cls}" aria-hidden="true"><span class="lt-titulo">{e(L["titulo"])}</span>'
            f'<span class="lt-autor mono">{e(L["autor"])}</span></div>')


def boton_compra(L, cls="btn-compra mono"):
    C = L.get("compra") or {}
    texto = f"Comprar en {e(C.get('tienda', 'la tienda'))}"
    if C.get("url"):
        return f'<a class="{cls}" href="{e(C["url"])}" target="_blank" rel="noopener">{texto} ↗</a>'
    return f'<span class="{cls} inactivo" aria-disabled="true" title="En la muestra este botón no lleva a ninguna tienda">{texto}</span>'


def url_cuaderno(C):
    return f"{BASE}breves/poesia/{C['id']}/"


def poemas_de(n):
    return "1 poema" if n == 1 else f"{n} poemas"
n = 0
for x in sorted(ESCRITOS, key=lambda x: fecha(x["fecha"])):
    if not x.get("muestra"):
        n += 1
        x["numero"] = n


def por_seccion(sec):
    return [x for x in ESCRITOS if x["seccion"] == sec]


# ---------- plantilla ----------
def pagina(ruta, titulo, desc, cuerpo, indexar=True, tipo="website", extra_head="", banda=True):
    canon = URL + "/" + ruta
    titulo_full = (f"{SITIO['nombre']} · {SITIO['autora']}" if titulo == SITIO["nombre"]
                   else f"{titulo} · {SITIO['nombre']}")
    verif = (f'<meta name="google-site-verification" content="{e(SITIO["google_verificacion"])}">'
             if SITIO.get("google_verificacion") else "")
    robots = "" if indexar else '<meta name="robots" content="noindex">'
    barra_html = '<span class="sep" aria-hidden="true"> · </span>'.join(
        f'<a href="{BASE}{r}"{" aria-current=\"page\"" if ruta.startswith(r) else ""}>{t}</a>'
        for r, t in [("quien-habita/", "Quién habita"), ("apoyar/", "Apoyar"), ("enviar/", "Envía tu propuesta")])
    apoyo = SITIO.get("apoyo", {})
    banda_html = f"""
<section class="support-band" aria-label="Apoyar este espacio">
  <div class="wrap">
    <picture class="logo-banda"><source srcset="{BASE}assets/logo-mini.webp" type="image/webp"><img src="{BASE}assets/logo-mini.png" width="90" height="120" alt=""></picture>
    <div>
      <h2>Sostener Ofrenda</h2>
      <p>{e(apoyo.get("texto", ""))}</p>
    </div>
    <a class="btn-light mono" href="{BASE}apoyar/">Hacer un aporte</a>
  </div>
</section>""" if banda else ""
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>try{{var lec=JSON.parse(localStorage.getItem("ofrenda-lectura")||"null");if(lec&&lec.ap){{var h=document.documentElement,k;for(k in lec.ap.a)h.setAttribute("data-lec-"+k,lec.ap.a[k]);for(k in lec.ap.v)h.style.setProperty(k,lec.ap.v[k]);}}}}catch(e){{}}</script>
<title>{e(titulo_full)}</title>
<meta name="description" content="{e(desc)}">
<meta name="author" content="{e(SITIO['autora'])}">
{robots}{verif}
<link rel="canonical" href="{e(canon)}">
<meta property="og:site_name" content="{e(SITIO['nombre'])}">
<meta property="og:title" content="{e(titulo_full)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="{tipo}">
<meta property="og:url" content="{e(canon)}">
<meta property="og:locale" content="es_CO">
<meta property="og:image" content="{URL}/assets/grabado-portada.jpg">
<meta property="og:image:alt" content="Grabado de una misma persona sentada, en tamaño grande y pequeño.">
<meta name="twitter:card" content="summary_large_image">
{extra_head}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,300..700;1,6..72,300..700&family=DM+Mono:wght@400;500&family=Oswald:wght@500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{BASE}assets/estilo.css?v={VERSION}">
<link rel="icon" type="image/png" href="{BASE}assets/favicon.png">
<link rel="apple-touch-icon" href="{BASE}assets/apple-touch-icon.png">
</head>
<body>
<div class="wrap">
  <header class="bar">
    <a class="brand" href="{BASE}" aria-label="{e(SITIO['nombre'])}, inicio">
      <picture class="brand-logo"><source srcset="{BASE}assets/logo-mini.webp" type="image/webp"><img src="{BASE}assets/logo-mini.png" width="34" height="45" alt=""></picture>
      <span>{e(SITIO['nombre'])}</span>
    </a>
    <nav class="bar-center mono" aria-label="Accesos">{barra_html}</nav>
    <button class="menu-btn" id="menu-open" aria-expanded="false" aria-controls="menu" type="button">
      <i></i><i></i><span class="mono">Menú</span>
    </button>
  </header>
</div>

<nav class="menu" id="menu" hidden aria-label="Secciones">
  <div class="wrap">
    <div class="menu-top">
      <span class="mono">Índice general</span>
      <button class="menu-close mono" id="menu-close" type="button">Cerrar</button>
    </div>
    <ol>
      <li><a href="{BASE}"><span class="mono">—</span><span>Portada</span></a></li>
      <li><a href="{BASE}breves/"><span class="mono">I</span><span>Textos breves</span></a></li>
      <li><a href="{BASE}largos/"><span class="mono">II</span><span>Textos largos</span></a></li>
      <li><a href="{BASE}lecturas/"><span class="mono">III</span><span>Lecturas que me atraviesan</span></a></li>
      <li><a href="{BASE}quien-habita/"><span class="mono">IV</span><span>Quién habita</span></a></li>
      <li><a href="{BASE}apoyar/"><span class="mono">V</span><span>Apoyar</span></a></li>
      <li><a href="{BASE}enviar/"><span class="mono">VI</span><span>Envía tu propuesta</span></a></li>
    </ol>
  </div>
</nav>

<main id="view">
{cuerpo}
</main>
{banda_html}
<footer>
  <div class="wrap">
    <span class="mono">{e(SITIO['nombre'])} · {e(SITIO['autora'])} y voces invitadas</span>
    <nav class="mono" aria-label="Pie">
      <a href="{BASE}breves/">Breves</a><a href="{BASE}largos/">Largos</a><a href="{BASE}lecturas/">Lecturas</a><a href="{BASE}quien-habita/">Quién habita</a><a href="{BASE}apoyar/">Apoyar</a><a href="{BASE}enviar/">Envía tu propuesta</a>
    </nav>
  </div>
  <div class="wrap pie-legal">
    <p class="mono">© {ANIO} Ofrenda · Cada texto pertenece a quien lo firma. Todos los derechos reservados.</p>
    <nav class="mono" aria-label="Políticas">
      <a href="{BASE}terminos/">Términos y condiciones</a><a href="{BASE}derechos-de-autor/">Derechos de autor</a><a href="{BASE}privacidad/">Datos personales</a>
    </nav>
  </div>
</footer>
<script src="{BASE}assets/sitio.js?v={VERSION}" defer></script>
<script src="{BASE}assets/lectura.js?v={VERSION}" defer></script>
</body>
</html>
"""


# ---------- vistas ----------
def entrada_indice(x):
    num = "00" if x.get("muestra") else f"{x['numero']:02d}"
    tag = MUESTRA_TAG if x.get("muestra") else ""
    who = ""
    if x.get("obra"):
        o = x["obra"]
        autor = e(o["autor"]) + " · " if o.get("autor") else ""
        who = f'<span class="who">{autor}<em>{e(o["titulo"])}</em></span>'
    return f"""<li class="entry"><a href="{url_escrito(x)}">
  <div class="t"><b>{num}</b><span>{e(x['titulo'])}</span>{tag}</div>{who}
  <p class="q">«{e(extracto(x))}»</p>
</a></li>"""



def pantalla_html():
    """Pantalla de la portada: muestra al azar uno de los textos publicados."""
    pool = []
    for C in CUADERNOS:
        n = len(C["poemas"])
        nombre = C["autor"] + (" (muestra)" if C.get("muestra") else "")
        for i, t in enumerate(C["poemas"], 1):
            pool.append({"t": NUM_POEMA.sub("", t, count=1), "fuente": f"Cuaderno de {nombre} · {i} / {n}",
                         "url": f"{url_cuaderno(C)}#poema-{i}"})
    for x in sorted(ESCRITOS, key=lambda y: (y["fecha"], y.get("numero", 0))):
        if x.get("muestra"):
            continue
        u = url_escrito(x)
        if x.get("poemas"):
            for t in x["poemas"]:
                pool.append({"t": NUM_POEMA.sub("", t, count=1), "fuente": f"De «{x['titulo']}»", "url": u})
        else:
            pool.append({"t": extracto(x), "fuente": f"De «{x['titulo']}»", "url": u})
    if not pool:
        return ""
    a = pool[0]
    estrofas = "".join(f"<p>{e(q)}</p>" for q in re.split(r"\n[ \t]*\n", a["t"]) if q)
    datos = json.dumps(pool, ensure_ascii=False).replace("</", "<\\/")
    return (f'<aside class="pantalla" aria-label="Un texto de Ofrenda al azar"><div class="pantalla-marco">'
            f'<p class="pantalla-et mono">Al azar</p>'
            f'<div class="pantalla-texto" aria-live="polite">{estrofas}</div>'
            f'<div class="pantalla-pie"><a class="pantalla-fuente mono" href="{a["url"]}">{e(a["fuente"])}</a>'
            f'<button class="pantalla-otro mono" type="button">Otro texto</button></div>'
            f'</div></aside><script type="application/json" id="pantalla-datos">{datos}</script>')

def portada():
    pills = f'<a class="pill" href="#ultimos" aria-current="true">Todo</a>' + "".join(
        f'<a class="pill" href="{BASE}{k}/">{SECCIONES[k]["corto"]}</a>' for k in ORDEN)
    dest_html = ""
    for k in ORDEN:
        S = SECCIONES[k]
        reales = [x for x in por_seccion(k) if not x.get("muestra")]
        u = f"{BASE}{k}/"
        titular = S["titular"]
        if k == "breves" and POEMAS:
            tab = "Nuevo"
            ultima = max(C["fecha"] for C in CUADERNOS)
            detalle = f"{mes_anio(ultima)} · " + ("1 cuaderno" if len(CUADERNOS) == 1 else f"{len(CUADERNOS)} cuadernos")
            leer = "Entrar"
        elif reales:
            dest = max(reales, key=lambda x: (fecha(x["fecha"]), x.get("numero", 0)))
            tab = "Nuevo"
            detalle = f"{mes_anio(dest['fecha'])} · " + ("1 texto" if len(reales) == 1 else f"{len(reales)} textos")
            leer = "Ver todos los textos"
        else:
            tab = "Pronto"
            detalle = "En preparación"
            leer = "Ver la sección"
        ancla = ' id="ultimos"' if not dest_html else ""
        dest_html += f"""
  <section class="featured"{ancla} aria-label="{e(S['nombre'])}">
    <span class="vert mono">{S['corto']}</span>
    <a class="cover" href="{u}" aria-label="{e(leer)}: {e(titular)}">
      <span class="tab mono">{tab}</span>
      {cubierta({"seccion": k, "id": k})}
    </a>
    <div class="body">
      <h2><a href="{u}">{e(titular)}</a></h2>
      <p class="excerpt">{e(S["resumen"])}</p>
      <a class="readlink mono" href="{u}">{e(leer)}</a>
    </div>
    <div class="issue"><span class="mono">{detalle}</span></div>
  </section>"""
    cuerpo = f"""<div class="wrap">
  <section class="hero">
    <div>
      <h1 class="masthead"><span>{e(SITIO['nombre'])}</span></h1>
      <p class="lede">Un espacio para pensar, sentir y escribir. La escritura como el resultado de una exploración intelectual.</p>
      <nav class="pills" aria-label="Ir a una sección">{pills}</nav>
    </div>
{pantalla_html()}
  </section>{dest_html}
</div>"""
    ld = json.dumps({"@context": "https://schema.org", "@type": "WebSite", "name": SITIO["nombre"],
                     "url": URL + "/", "description": SITIO["descripcion"], "inLanguage": "es",
                     "author": {"@type": "Person", "name": SITIO["autora"]}}, ensure_ascii=False)
    return pagina("", SITIO["nombre"], SITIO["descripcion"], cuerpo,
                  extra_head=f'<script type="application/ld+json">{ld}</script>')


def cuaderno(C):
    S = SECCIONES["breves"]
    poemas = C["poemas"]
    n = len(poemas) + (1 if C.get("sobre") else 0)
    autor = e(C["autor"])
    tag = MUESTRA_TAG if C.get("muestra") else ""
    hojas = ""
    for i, t in enumerate(poemas, 1):
        resto = NUM_POEMA.sub("", t, count=1)
        bloques = [q for q in re.split(r"\n[ \t]*\n", resto) if q]
        estrofas = "".join(f"<p>{e(q)}</p>" for q in bloques)
        # renglones que ocupa el poema (versos + espacios entre estrofas)
        renglones = sum(len(q.split("\n")) for q in bloques) + len(bloques) - 1
        corta = renglones <= 9
        extra = f' corta" style="--arriba:{max(0, (13 - renglones) // 2)}' if corta else ""
        hojas += (f'<article class="hoja{extra}" id="poema-{i}" data-n="{i}" aria-label="Página {i} de {n}, de {autor}">'
                  f'<div class="hoja-texto">{estrofas}</div><p class="folio mono"><span>{autor}</span> · {i}</p></article>')
    if C.get("sobre"):
        hojas += (f'<article class="hoja sobre" id="poema-{n}" data-n="{n}" aria-label="Sobre {autor}">'
                  f'<div class="hoja-texto"><p class="sobre-et mono">Sobre quien escribe</p><p class="sobre-nombre">{autor}</p>'
                  f'<p>{e(C["sobre"])}</p></div><p class="folio mono">{n}</p></article>')
    cuerpo = f"""<div class="wrap">
  <a class="back mono" href="{BASE}breves/poesia/">← Poesía · cuadernos</a>
  <header class="sec-head">
    <span class="roman">{S['num']}</span>
    <h1>Cuaderno de {autor}{tag}</h1>
    <p class="mono">{e(S['nombre'])} · Poesía · {poemas_de(len(poemas))}</p>
  </header>
  <section class="cuaderno" aria-label="Cuaderno de {autor}">
    <nav class="pasar" aria-label="Pasar página">
      <button class="ant mono" type="button" aria-label="Página anterior">← Anterior</button>
      <span class="cuenta mono" aria-live="polite">1 / {n}</span>
      <button class="sig mono" type="button" aria-label="Página siguiente">Siguiente →</button>
    </nav>
    <div class="hojas">{hojas}</div>
    <p class="pista mono">Desliza o usa las flechas para pasar la página</p>
  </section>
</div>"""
    return pagina(f"breves/poesia/{C['id']}/", f"Cuaderno de {C['autor']}",
                  f"Cuaderno de poesía de {C['autor']} en Ofrenda.", cuerpo, indexar=not C.get("muestra"))


def libro(L):
    S = SECCIONES[L["seccion"]]
    G = next(G for G in GENEROS[L["seccion"]] if G["id"] == L["genero"])
    tag = MUESTRA_TAG if L.get("muestra") else ""
    paginas = L["paginas"]
    n = len(paginas) + 1
    hojas = ""
    for i, t in enumerate(paginas, 1):
        parr = "".join(f"<p>{e(q)}</p>" for q in re.split(r"\n[ \t]*\n", t) if q)
        hojas += (f'<article class="hoja" id="poema-{i}" data-n="{i}" aria-label="Página {i} de la muestra">'
                  f'<div class="hoja-texto">{parr}</div><p class="folio mono"><span>{e(L["titulo"])}</span> · {i}</p></article>')
    precio = f'<p class="seguir-precio">{e(L["precio"])}</p>' if L.get("precio") else ""
    nota = '<p class="seguir-nota mono">Muestra: este botón no lleva a ninguna tienda.</p>' if L.get("muestra") else ""
    hojas += (f'<article class="hoja seguir" id="poema-{n}" data-n="{n}" aria-label="Para seguir leyendo">'
              f'<div class="hoja-texto"><p class="sobre-et mono">Fin de la muestra</p><p class="seguir-titulo">Para seguir leyendo</p>'
              f'<p><em>{e(L["titulo"])}</em>, de {e(L["autor"])}, está completo en {e((L.get("compra") or {}).get("tienda", "la tienda"))}.</p>'
              f'{precio}{boton_compra(L)}{nota}</div></article>')
    cuerpo = f"""<div class="wrap">
  <a class="back mono" href="{BASE}{L['seccion']}/{G['id']}/">← {e(G['nombre'])} · {e(S['nombre'])}</a>
  <section class="libro-ficha">
    {tapa_libro(L)}
    <div>
      <p class="mono libro-gen">{e(S['nombre'])} · {e(G['nombre'])} · Libro</p>
      <h1>{e(L['titulo'])}{tag}</h1>
      <p class="libro-autor">{e(L['autor'])}</p>
      <p class="libro-desc">{e(L.get('descripcion', ''))}</p>
      <div class="libro-acciones"><a class="btn-leer mono" href="#muestra">Leer la muestra</a>{boton_compra(L)}</div>
      {f'<p class="libro-precio mono">{e(L["precio"])}</p>' if L.get("precio") else ""}
    </div>
  </section>
  <section class="cuaderno libro" id="muestra" aria-label="Páginas de muestra de {e(L['titulo'])}">
    <nav class="pasar" aria-label="Pasar página">
      <button class="ant mono" type="button" aria-label="Página anterior">← Anterior</button>
      <span class="cuenta mono" aria-live="polite">1 / {n}</span>
      <button class="sig mono" type="button" aria-label="Página siguiente">Siguiente →</button>
    </nav>
    <div class="hojas">{hojas}</div>
    <p class="pista mono">Desliza o usa las flechas para pasar la página</p>
  </section>
</div>"""
    ld = {"@context": "https://schema.org", "@type": "Book", "name": L["titulo"], "inLanguage": "es",
          "author": {"@type": "Person", "name": L["autor"]}, "description": L.get("descripcion", "")}
    return pagina(url_libro(L)[len(BASE):], f"{L['titulo']}, de {L['autor']}", L.get("descripcion", ""), cuerpo,
                  indexar=not L.get("muestra"), tipo="book",
                  extra_head=f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>')


def estanteria():
    """Poesía: los cuadernos, uno por autor."""
    S = SECCIONES["breves"]
    tapas = ""
    for C in CUADERNOS:
        tag = MUESTRA_TAG if C.get("muestra") else ""
        tapas += (f'<li><a class="tapa" href="{url_cuaderno(C)}">'
                  f'<span class="tapa-et mono">Cuaderno de</span>'
                  f'<span class="tapa-autor">{e(C["autor"])}</span>{tag}'
                  f'<span class="tapa-pie mono">{poemas_de(len(C["poemas"]))} · {mes_anio(C["fecha"])}</span></a></li>')
    # enlaces a /breves/poesia/#poema-N (antes del cambio) abren el cuaderno propio
    salto = (f'<script>if(/^#poema-\\d+$/.test(location.hash))'
             f'location.replace("{url_cuaderno(PROPIO)}"+location.hash);</script>') if PROPIO else ""
    cuerpo = f"""<div class="wrap">{salto}
  <a class="back mono" href="{BASE}breves/">← {e(S['nombre'])}</a>
  <header class="sec-head">
    <span class="roman">{S['num']}</span>
    <h1>Poesía</h1>
    <p class="mono">{e(S['nombre'])} · Cuadernos</p>
  </header>
  <p class="estante-nota">Cada cuaderno reúne los poemas de una persona, en el orden en que quiso compartirlos. No responde a un tema: es su voz.</p>
  <ul class="estante">{tapas}</ul>
</div>"""
    return pagina("breves/poesia/", "Poesía · Textos breves", "Cuadernos de poesía en Ofrenda, uno por cada voz.", cuerpo)


def cantidad(n):
    return "1 texto" if n == 1 else f"{n} textos"


def seccion(k):
    """Página de la sección: primero se elige el género."""
    S = SECCIONES[k]
    filas = ""
    for G in GENEROS[k]:
        if G.get("cuaderno"):
            n, detalle = len(POEMAS), "Cuadernos de quienes escriben"
        else:
            n = (len([x for x in por_seccion(k) if genero_de(x) is G and not x.get("muestra")])
                 + len([L for L in LIBROS if L["seccion"] == k and L["genero"] == G["id"]]))
            detalle = ""
        estado = (("1 cuaderno" if len(CUADERNOS) == 1 else f"{len(CUADERNOS)} cuadernos") if G.get("cuaderno")
                  else cantidad(n)) if n else "En preparación"
        sub = f'<p class="q">{e(detalle)}</p>' if detalle else ""
        filas += f"""<li class="row genero"><a href="{BASE}{k}/{G['id']}/">
      <div><h2>{e(G['nombre'])}</h2>{sub}</div>
      <span class="d mono">{estado}</span>
    </a></li>"""
    salto = ""
    if k == "breves":
        # enlaces antiguos a /breves/#poema-N siguen abriendo el cuaderno
        salto = (f'<script>if(/^#poema-\\d+$/.test(location.hash))'
                 f'location.replace("{url_cuaderno(PROPIO)}"+location.hash);</script>') if PROPIO else ""
    cuerpo = f"""<div class="wrap">{salto}
  <header class="sec-head">
    <span class="roman">{S['num']}</span>
    <h1>{e(S['nombre'])}</h1>
    <p class="mono">{e(S['desc'])} · Elige un género</p>
  </header>
  <ol class="rows generos">{filas}</ol>
</div>"""
    return pagina(f"{k}/", S["nombre"], f"{S['nombre']} en Ofrenda: {S['desc'].lower()}.", cuerpo)


def genero(k, G):
    if G.get("cuaderno"):
        return estanteria()
    S = SECCIONES[k]
    lista = [x for x in reversed(por_seccion(k)) if genero_de(x) is G]
    libros = [L for L in LIBROS if L["seccion"] == k and L["genero"] == G["id"]]
    reales = len([x for x in lista if not x.get("muestra")]) + len([L for L in libros if not L.get("muestra")])
    filas = ""
    for L in libros:
        tag = MUESTRA_TAG if L.get("muestra") else ""
        filas += f"""<li class="row libro-fila"><a href="{url_libro(L)}">
      <div class="lf">{tapa_libro(L, "libro-tapa mini")}<div><h2>{e(L['titulo'])}{tag}</h2><p class="lf-autor">{e(L['autor'])}</p>
      <p class="q">{e(L.get('descripcion', ''))}</p></div></div>
      <span class="d mono">Libro · {len(L['paginas'])} páginas de muestra</span>
    </a></li>"""
    for x in lista:
        ob = obra(x, "q").replace('class="q"', 'class="q" style="font-style:normal;color:var(--ink)"')
        filas += f"""<li class="row"><a href="{url_escrito(x)}">
      <div><h2>{e(x['titulo'])}</h2>{ob}<p class="q">{e(extracto(x))}</p></div>
      <span class="d mono">{fecha_larga(x['fecha'])}</span>
    </a></li>"""
    if not filas:
        filas = '<li><p class="empty">El primer texto de este género está en preparación.</p></li>'
    cuerpo = f"""<div class="wrap">
  <a class="back mono" href="{BASE}{k}/">← {e(S['nombre'])}</a>
  <header class="sec-head">
    <span class="roman">{S['num']}</span>
    <h1>{e(G['nombre'])}</h1>
    <p class="mono">{e(S['nombre'])}{"" if not reales else " · " + cantidad(reales)}</p>
  </header>
  <ol class="rows" reversed>{filas}</ol>
</div>"""
    return pagina(f"{k}/{G['id']}/", f"{G['nombre']} · {S['nombre']}",
                  f"{G['nombre']} en {S['nombre'].lower()} de Ofrenda.", cuerpo)


def cuerpo_html(x):
    if x.get("poemas"):
        bloques = []
        for t in x["poemas"]:
            m = NUM_POEMA.match(t)
            resto = t[m.end():] if m else t
            estrofas = "".join(f"<p>{e(q)}</p>" for q in re.split(r"\n[ \t]*\n", resto) if q)
            bloques.append(f'<section class="poema">{estrofas}</section>')
        return "\n".join(bloques)
    if x.get("cuerpo_html"):
        return x["cuerpo_html"]
    partes = re.split(r"\n[ \t]*\n", x["cuerpo"])
    return "\n".join(f"<p>{e(p)}</p>" for p in partes if p)


def escrito(x):
    S = SECCIONES[x["seccion"]]
    lista = [y for y in por_seccion(x["seccion"]) if genero_de(y) is genero_de(x)]
    i = lista.index(x)

    def enlace(y, rot):
        if not y:
            return "<span></span>"
        return f'<a href="{url_escrito(y)}"><span class="mono">{rot}</span><span>{e(y["titulo"])}</span></a>'

    meta = "".join(f'<div><dt class="mono">{a}</dt><dd>{e(b)}</dd></div>' for a, b in [
        ("Sección", f"{S['num']} · {S['corto']}"),
        ("Fecha", fecha_larga(x["fecha"])), ("Lectura", f"{minutos(x)} min")])
    tag = MUESTRA_TAG if x.get("muestra") else ""
    cita = f'<blockquote class="pull">{e(x["cita"])}</blockquote>' if x.get("cita") else ""
    drop = " drop" if x["seccion"] == "largos" else ""
    con_dibujo = x["seccion"] in ("largos", "lecturas")
    fig = lambda cls: (f'<figure class="{cls}"><picture><source srcset="{BASE}assets/dibujo-hilo.webp" type="image/webp">'
                       f'<img src="{BASE}assets/dibujo-hilo.png" width="600" height="1217" loading="lazy" '
                       f'alt="Dibujo en línea verde de una persona que sostiene un hilo; arriba, el hilo se enreda. Dibujo de {e(SITIO["autora"])}."></picture></figure>')
    lado = fig("dibujo-lado") if con_dibujo else ""
    final = fig("dibujo-final") if con_dibujo else ""
    cuerpo = f"""<div class="wrap">
  <a class="back mono" href="{BASE}{x['seccion']}/{genero_de(x)['id']}/">← {e(genero_de(x)['nombre'])} · {e(S['nombre'])}</a>
  <article class="article">
    <div class="lado"><dl class="meta">{meta}</dl>{lado}</div>
    <div>
      <h1 class="art-title">{e(x['titulo'])}{tag}</h1>
      {obra(x, "art-obra")}
      {cita}
      <div class="prose{drop}">
{cuerpo_html(x)}
      </div>
      {final}
      <div class="signoff"><span class="mono">{e(x.get('autor', SITIO['autora']))}</span><a class="mono" href="{BASE}apoyar/">Apoyar este espacio</a></div>
      <nav class="pager" aria-label="Otros textos de la sección">{enlace(lista[i - 1] if i > 0 else None, "← Anterior")}{enlace(lista[i + 1] if i + 1 < len(lista) else None, "Siguiente →")}</nav>
    </div>
  </article>
</div>"""
    ld = {"@context": "https://schema.org", "@type": "Review" if x.get("obra") else "Article",
          "headline": x["titulo"], "datePublished": x["fecha"], "inLanguage": "es",
          "author": {"@type": "Person", "name": x.get("autor", SITIO["autora"])},
          "mainEntityOfPage": URL + f"/escritos/{x['id']}/", "description": descripcion(x)}
    if x.get("obra"):
        ld["itemReviewed"] = {"@type": "CreativeWork", "name": x["obra"]["titulo"],
                              "author": {"@type": "Person", "name": x["obra"].get("autor", "")}}
    extra = (f'<meta property="article:published_time" content="{x["fecha"]}">'
             f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>')
    return pagina(f"escritos/{x['id']}/", x["titulo"], descripcion(x), cuerpo,
                  indexar=not x.get("muestra"), tipo="article", extra_head=extra)


def quien_habita():
    usuario, dominio = "mazapatatrabajo", "gmail.com"
    cuerpo = f"""<div class="wrap"><section class="page habita">
  <div>
    <p class="mono">IV — Quién habita</p>
    <h1>Quién habita</h1>
    <p class="nombre">{e(SITIO['autora'])}</p>
    <p class="big">Pronto, unas palabras sobre quien escribe estas páginas: de dónde viene su escritura, qué la mueve y desde dónde mira el mundo.</p>
    <div class="contacto">
      <span class="mono">Escríbeme</span>
      <a class="correo" data-u="{usuario}" data-d="{dominio}" href="#">{usuario} [arroba] {dominio.replace(".", " [punto] ")}</a>
    </div>
  </div>
  <aside><picture class="retrato"><source srcset="{BASE}assets/mariana.webp" type="image/webp"><img src="{BASE}assets/mariana.jpg" width="900" height="1125" alt="Retrato de {e(SITIO['autora'])}, de brazos cruzados, con camiseta negra sobre un fondo gris verdoso."></picture></aside>
</section></div>"""
    return pagina("quien-habita/", "Quién habita", f"{SITIO['autora']}, quien escribe Ofrenda.", cuerpo)


# Propuestas: el formulario envía a FormSubmit, que reenvía cada propuesta al correo de Mariana.
# Cuando FormSubmit entregue la clave aleatoria (tras confirmar el correo), ponerla en
# escritos.json -> sitio.propuestas.clave para que el correo no aparezca en la dirección del formulario.
def enviar():
    P = SITIO.get("propuestas", {})
    usuario, dominio = "mazapatatrabajo", "gmail.com"
    opciones = ""
    for k in ORDEN:
        for G in GENEROS[k]:
            opciones += f'<option value="{e(SECCIONES[k]["nombre"])} · {e(G["nombre"])}">{e(SECCIONES[k]["nombre"])} · {e(G["nombre"])}</option>'
    opciones += '<option value="No estoy segura/o">No estoy segura/o</option>'
    cuerpo = f"""<div class="wrap"><section class="page enviar">
  <div>
    <p class="mono">VI — Envía tu propuesta</p>
    <h1>Envía tu propuesta</h1>
    <p class="big">Ofrenda también es casa para otras voces. Si escribes, puedes enviar aquí tu texto para que sea leído y considerado para publicación.</p>

    <form class="propuesta" id="propuesta" method="POST" enctype="multipart/form-data" novalidate
          data-u="{usuario}" data-d="{dominio}" data-clave="{e(P.get('clave', ''))}" aria-describedby="prop-nota">
      <input type="hidden" name="_subject" value="Nueva propuesta para Ofrenda">
      <input type="hidden" name="_template" value="table">
      <input type="hidden" name="_captcha" value="false">
      <input type="hidden" name="_next" value="{URL}/enviar/gracias/">
      <input type="hidden" name="_autoresponse" value="Gracias por enviar tu propuesta a Ofrenda. La recibimos y la leeremos con atención.">
      <div class="prop-trampa" aria-hidden="true"><label>No llenes este campo<input type="text" name="_honey" tabindex="-1" autocomplete="off"></label></div>

      <fieldset class="prop-grupo">
        <legend class="mono">I · Quién escribe</legend>
        <div class="prop-campo">
          <label for="prop-nombre">Nombre con el que firmas <span class="prop-req" aria-hidden="true">*</span></label>
          <input id="prop-nombre" name="Nombre" type="text" autocomplete="name" required maxlength="120" aria-describedby="prop-nombre-err">
          <p class="prop-err" id="prop-nombre-err" hidden>Escribe tu nombre o el nombre con el que firmas.</p>
        </div>
        <div class="prop-campo">
          <label for="prop-correo">Correo <span class="prop-req" aria-hidden="true">*</span></label>
          <input id="prop-correo" name="email" type="email" autocomplete="email" required maxlength="160" aria-describedby="prop-correo-ayuda prop-correo-err">
          <p class="prop-ayuda" id="prop-correo-ayuda">Solo para responderte sobre tu propuesta.</p>
          <p class="prop-err" id="prop-correo-err" hidden>Escribe un correo válido, por ejemplo nombre@correo.com.</p>
        </div>
        <div class="prop-campo">
          <label for="prop-lugar">Desde dónde escribes <span class="prop-opc">(opcional)</span></label>
          <input id="prop-lugar" name="Lugar" type="text" autocomplete="address-level2" maxlength="120">
        </div>
        <div class="prop-campo">
          <label for="prop-bio">Unas líneas sobre ti <span class="prop-opc">(opcional)</span></label>
          <textarea id="prop-bio" name="Sobre quien escribe" rows="3" maxlength="800" aria-describedby="prop-bio-ayuda"></textarea>
          <p class="prop-ayuda" id="prop-bio-ayuda">Si tu texto se publica, pueden acompañarlo.</p>
        </div>
      </fieldset>

      <fieldset class="prop-grupo">
        <legend class="mono">II · El texto</legend>
        <div class="prop-campo">
          <label for="prop-titulo">Título <span class="prop-req" aria-hidden="true">*</span></label>
          <input id="prop-titulo" name="Título" type="text" required maxlength="200" aria-describedby="prop-titulo-err">
          <p class="prop-err" id="prop-titulo-err" hidden>Escribe el título del texto (o «Sin título»).</p>
        </div>
        <div class="prop-campo">
          <label for="prop-genero">Sección y género <span class="prop-req" aria-hidden="true">*</span></label>
          <select id="prop-genero" name="Sección y género" required aria-describedby="prop-genero-err">
            <option value="">Elige una opción</option>{opciones}
          </select>
          <p class="prop-err" id="prop-genero-err" hidden>Elige dónde crees que encaja tu texto.</p>
        </div>
        <div class="prop-campo">
          <label for="prop-texto">Tu texto</label>
          <textarea id="prop-texto" name="Texto" rows="12" maxlength="60000" aria-describedby="prop-texto-ayuda prop-contenido-err"></textarea>
          <p class="prop-ayuda" id="prop-texto-ayuda">Pégalo tal como lo escribiste, o adjúntalo abajo.</p>
        </div>
        <div class="prop-campo">
          <label for="prop-archivo">Adjuntar archivo</label>
          <input id="prop-archivo" name="attachment" type="file" accept=".doc,.docx,.pdf,.odt,.rtf,.txt" aria-describedby="prop-archivo-ayuda prop-archivo-err prop-contenido-err">
          <p class="prop-ayuda" id="prop-archivo-ayuda">Word, PDF, ODT, RTF o TXT, de máximo 10 MB.</p>
          <p class="prop-err" id="prop-archivo-err" hidden>El archivo pesa más de 10 MB o no tiene un formato aceptado.</p>
        </div>
        <p class="prop-err" id="prop-contenido-err" hidden>Pega tu texto o adjunta un archivo.</p>
      </fieldset>

      <fieldset class="prop-grupo">
        <legend class="mono">III · Autoría y datos</legend>
        <label class="prop-check"><input type="checkbox" name="Autoría" value="Confirmo que el texto es de mi autoría y que puedo compartirlo" required aria-describedby="prop-autoria-err">
          <span>Confirmo que el texto es de mi autoría y que tengo derecho a compartirlo.</span></label>
        <p class="prop-err" id="prop-autoria-err" hidden>Para enviar, confirma que el texto es tuyo.</p>
        <label class="prop-check"><input type="checkbox" name="Autorización de datos" value="Acepto los términos y autorizo el tratamiento de mis datos" required aria-describedby="prop-datos-err">
          <span>Acepto los <a href="{BASE}terminos/#propuestas">términos para enviar propuestas</a> y autorizo a Ofrenda a tratar mis datos personales para gestionar mi propuesta, según la <a href="{BASE}privacidad/">política de datos personales</a>.</span></label>
        <p class="prop-err" id="prop-datos-err" hidden>Para enviar, acepta los términos y la autorización de datos.</p>
      </fieldset>

      <div class="prop-enviar">
        <button type="submit" class="prop-boton mono">Enviar propuesta</button>
        <p class="prop-estado" id="prop-estado" role="status" aria-live="polite"></p>
      </div>
      <p class="prop-nota" id="prop-nota">Los campos con <span aria-hidden="true">*</span><span class="lec-sr">asterisco</span> son obligatorios. Tus datos solo se usan para responderte.</p>
    </form>
    <noscript><p class="prop-nota">Para enviar tu propuesta necesitas activar JavaScript, o escríbeme a {usuario} [arroba] {dominio.replace(".", " [punto] ")}.</p></noscript>
  </div>
  <aside class="prop-guia" aria-labelledby="prop-guia-t">
    <h2 id="prop-guia-t" class="mono">Antes de enviar</h2>
    <dl>
      <dt>Qué recibe Ofrenda</dt><dd>Poesía, ensayo, crónica, literatura (cuento, relato o fragmento de un libro) y reflexiones sobre lecturas.</dd>
      <dt>Cómo</dt><dd>Pega el texto en el formulario o adjunta un archivo.</dd>
      <dt>Autoría</dt><dd>El texto debe ser tuyo. Si se publica, aparecerá con tu nombre y tal como lo escribiste.</dd>
      <dt>Tus derechos</dt><dd>Conservas los derechos de autor de tu texto. Antes de publicarlo, Ofrenda te escribirá para confirmar.</dd>
      <dt>Varios textos</dt><dd>Envía cada propuesta por separado; si son poemas, puedes reunirlos en un solo archivo.</dd>
    </dl>
  </aside>
</section></div>"""
    return pagina("enviar/", "Envía tu propuesta", "Envía tu texto a Ofrenda: poesía, ensayo, crónica, literatura y lecturas.", cuerpo)


ACTUALIZACION = "24 de noviembre de 2026"
LEGALES = [("terminos/", "Términos y condiciones"), ("derechos-de-autor/", "Derechos de autor"), ("privacidad/", "Datos personales")]
NORMAS = {
    "ley23": "https://cancilleria.gov.co/normograma/compilacion/docs/ley_0023_1982.htm",
    "dec351": "https://cancilleria.gov.co/normograma/compilacion/docs/decision_comisioncandina_dec351.htm",
    "ley1581": "https://cancilleria.gov.co/normograma/compilacion/docs/ley_1581_2012.htm",
    "sic": "https://www.sic.gov.co/",
}


def correo_html():
    u, d = "mazapatatrabajo", "gmail.com"
    return f'<a class="correo" data-u="{u}" data-d="{d}" href="#">{u} [arroba] {d.replace(".", " [punto] ")}</a>'


def norma(clave, texto):
    return f'<a href="{NORMAS[clave]}" target="_blank" rel="noopener">{texto}</a>'


def legal(ruta, titulo, desc, intro, secciones):
    """secciones: lista de (id, título, html)."""
    otras = "".join(f'<li><a href="{BASE}{r}"{" aria-current=\"page\"" if r == ruta else ""}>{e(t)}</a></li>' for r, t in LEGALES)
    cuerpo_s = "".join(f'<section id="{i}" aria-labelledby="{i}-t"><h2 id="{i}-t"><span class="mono">{n:02d}</span>{e(t)}</h2>{h}</section>'
                       for n, (i, t, h) in enumerate(secciones, 1))
    cuerpo = f"""<div class="wrap"><div class="legal">
  <header class="legal-cab">
    <p class="mono">Ofrenda · Políticas</p>
    <h1>{e(titulo)}</h1>
    <p class="mono legal-fecha">Última actualización: {ACTUALIZACION}</p>
  </header>
  <aside class="legal-lado">
    <nav aria-label="Políticas de Ofrenda"><p class="mono">Políticas</p><ul>{otras}</ul></nav>
  </aside>
  <article class="prose legal-texto">
    <p class="legal-intro">{intro}</p>
    {cuerpo_s}
  </article>
</div></div>"""
    return pagina(ruta, titulo, desc, cuerpo)


def terminos():
    C = correo_html()
    sec = [
        ("que-es", "Qué es Ofrenda", f"""<p>Ofrenda es un espacio de lectura y escritura que publica textos de Mariana Zapata y de voces invitadas: poesía, ensayo, crónica, literatura y reflexiones sobre lecturas. Leer los textos es gratuito.</p>"""),
        ("uso", "Uso del sitio", f"""<p>Puedes leer los textos, compartir sus enlaces y citar fragmentos breves como se explica en la política de <a href="{BASE}derechos-de-autor/">derechos de autor</a>.</p>
<p>No está permitido:</p>
<ul><li>copiar o publicar en otro lugar textos completos o partes sustanciales sin autorización de su autor;</li>
<li>usar los textos o imágenes con fines comerciales sin autorización;</li>
<li>presentar como propio un texto publicado en Ofrenda o atribuirlo a otra persona;</li>
<li>intentar afectar el funcionamiento o la seguridad del sitio.</li></ul>"""),
        ("voces", "Textos de voces invitadas", """<p>Cada texto pertenece a quien lo firma. Las ideas y opiniones expresadas en cada texto son de su autor o autora. Ofrenda publica los textos tal como sus autores los entregan, sin corregirlos ni modificarlos.</p>"""),
        ("propuestas", "Envío de propuestas", f"""<p>Cualquier persona puede enviar un texto desde <a href="{BASE}enviar/">Envía tu propuesta</a>. Al hacerlo:</p>
<ul><li><strong>Declaras</strong> que el texto es de tu autoría, que tienes derecho a compartirlo y que no infringe derechos de otras personas.</li>
<li><strong>Conservas todos tus derechos de autor.</strong> Enviar una propuesta no transfiere ningún derecho a Ofrenda.</li>
<li>Enviar un texto no obliga a Ofrenda a publicarlo. La selección es una decisión editorial de Ofrenda.</li>
<li>Si tu texto es seleccionado, Ofrenda te escribirá <strong>antes de publicarlo</strong> para pedir tu autorización. Con ella, Ofrenda podrá publicarlo en este sitio de forma gratuita y <strong>no exclusiva</strong>: puedes seguir publicándolo donde quieras.</li>
<li>Tu texto se publicará con tu nombre o firma y tal como lo enviaste.</li>
<li>Puedes pedir en cualquier momento que se retire un texto tuyo publicado en Ofrenda escribiendo a {C}.</li>
<li>La publicación no genera pago, salvo que se acuerde algo distinto por escrito.</li></ul>
<p>Los datos que envíes con tu propuesta se tratan según la <a href="{BASE}privacidad/">política de datos personales</a>.</p>"""),
        ("aportes", "Aportes y compras", """<p>Los aportes que se hacen desde la página Apoyar (Ko-fi o Bre-B) son voluntarios: sirven para sostener el sitio y no dan acceso a contenidos exclusivos. Los pagos los procesan esas plataformas y entidades financieras, con sus propios términos. Ofrenda no recibe ni guarda datos de tarjetas o cuentas.</p>
<p>Cuando un libro se ofrece para la venta, la compra se hace en la tienda externa que se indica (por ejemplo, Amazon) y se rige por los términos de esa tienda. Ofrenda no procesa pagos de libros.</p>"""),
        ("enlaces", "Enlaces a otros sitios", """<p>Ofrenda puede enlazar a sitios de terceros (tiendas, plataformas de pago o normas oficiales). Ofrenda no controla esos sitios ni responde por su contenido o por sus políticas.</p>"""),
        ("responsabilidad", "Disponibilidad y responsabilidad", """<p>Ofrenda procura que el sitio funcione bien y esté disponible, pero puede tener interrupciones o errores. El sitio se ofrece tal como está, sin garantías de disponibilidad permanente.</p>"""),
        ("cambios", "Cambios a estos términos", """<p>Estos términos pueden actualizarse. La versión vigente es siempre la publicada en esta página, con su fecha de actualización.</p>"""),
        ("ley", "Ley aplicable", """<p>Estos términos se rigen por las leyes de la República de Colombia.</p>"""),
        ("contacto", "Contacto", f"""<p>Para cualquier pregunta sobre estos términos, escribe a {C}.</p>"""),
    ]
    intro = "Estos términos regulan el uso de Ofrenda (mazapata-ia.github.io), un espacio de escritura creado y administrado por Mariana Zapata. Al navegar el sitio, leer sus textos o enviar una propuesta, aceptas estos términos."
    return legal("terminos/", "Términos y condiciones", "Términos y condiciones de uso de Ofrenda y del envío de propuestas.", intro, sec)


def derechos():
    C = correo_html()
    sec = [
        ("proteccion", "Las obras están protegidas", f"""<p>Los textos, dibujos, fotografías y demás obras publicadas en Ofrenda están protegidos por el derecho de autor, de acuerdo con la {norma("ley23", "Ley 23 de 1982")}, la {norma("dec351", "Decisión Andina 351 de 1993")} y las demás normas aplicables. Esta protección existe por la sola creación de la obra y no depende de ningún registro.</p>
<p class="legal-aviso">© Mariana Zapata y los autores de cada obra. Todos los derechos reservados.</p>"""),
        ("titulares", "A quién pertenece cada obra", """<p>Cada obra pertenece a su autor o autora. Los textos y dibujos de Mariana Zapata son de su autoría. Los textos de voces invitadas pertenecen a quienes los firman. Publicar una obra en Ofrenda no transfiere sus derechos a Ofrenda ni a ninguna otra persona.</p>"""),
        ("morales", "Derechos morales", """<p>Cada autor conserva siempre el derecho a que se reconozca su autoría y a que su obra no sea deformada o modificada de forma que afecte su honor o su reputación. La ley colombiana reconoce estos derechos como perpetuos, inalienables e irrenunciables (artículo 30 de la Ley 23 de 1982).</p>"""),
        ("patrimoniales", "Derechos patrimoniales", """<p>Solo el autor, o quien tenga sus derechos, puede autorizar o prohibir que su obra se reproduzca, se comunique al público (incluida su publicación en internet), se distribuya, se traduzca, se adapte o se transforme (artículo 12 de la Ley 23 de 1982).</p>"""),
        ("permitido", "Lo que puedes hacer", """<ul><li>Leer los textos en el sitio.</li>
<li>Compartir el enlace de cualquier página.</li>
<li>Citar pasajes breves, siempre que menciones el nombre del autor y el título de la obra, y que la cita no sea tan extensa que reemplace la lectura del original (artículo 31 de la Ley 23 de 1982). Te agradecemos incluir el enlace a Ofrenda.</li></ul>"""),
        ("autorizacion", "Lo que necesita autorización", f"""<p>Necesitas la autorización previa y por escrito del autor para:</p>
<ul><li>reproducir una obra completa o una parte sustancial en otro sitio, red social, blog, revista, libro o antología, también en capturas de pantalla o imágenes;</li>
<li>usar una obra con fines comerciales o publicitarios;</li>
<li>traducirla, adaptarla, musicalizarla, grabarla en audio o video o leerla en público;</li>
<li>usar las obras para entrenar, alimentar o ajustar sistemas de inteligencia artificial, o para minería de textos y datos.</li></ul>
<p>Para pedir un permiso escribe a {C} indicando la obra, el uso que quieres darle y el medio donde aparecerá. Si la obra es de una voz invitada, Ofrenda te pondrá en contacto con su autor.</p>"""),
        ("infracciones", "Si encuentras una copia no autorizada", f"""<p>Si ves una obra de Ofrenda publicada en otro lugar sin autorización, o si crees que algo publicado en Ofrenda infringe tus derechos, escribe a {C} con el enlace y una breve explicación. Lo revisaremos y, si corresponde, retiraremos el contenido.</p>"""),
        ("normas", "Normas de referencia", f"""<ul><li>{norma("ley23", "Ley 23 de 1982, sobre derechos de autor")} (Normograma de la Cancillería).</li>
<li>{norma("dec351", "Decisión 351 de 1993, Régimen Común sobre Derecho de Autor y Derechos Conexos")} (Normograma de la Cancillería).</li></ul>"""),
    ]
    intro = "Todo lo que se publica en Ofrenda tiene autor. Esta política explica a quién pertenecen las obras, qué puedes hacer con ellas y qué necesita permiso."
    return legal("derechos-de-autor/", "Derechos de autor", "Política de derechos de autor de Ofrenda: las obras pertenecen a sus autores.", intro, sec)


def privacidad():
    C = correo_html()
    sec = [
        ("responsable", "Responsable", f"""<p>La responsable del tratamiento de los datos personales que se recogen en Ofrenda es <strong>Mariana Zapata</strong>, persona natural que crea y administra el sitio, en Colombia. Contacto: {C}.</p>
<p>Esta política se rige por la {norma("ley1581", "Ley 1581 de 2012")} y sus decretos reglamentarios.</p>"""),
        ("datos", "Qué datos se recogen", f"""<ul><li><strong>Formulario de propuestas:</strong> nombre o firma, correo electrónico, lugar desde donde escribes (opcional), unas líneas sobre ti (opcional) y el texto o archivo que envías.</li>
<li><strong>Correos:</strong> si escribes directamente, tu dirección de correo y lo que cuentes en el mensaje.</li>
<li><strong>Aportes:</strong> los procesan Ko-fi, PayPal o tu banco. Ofrenda no recibe ni guarda datos de tarjetas o cuentas; puede recibir de esas plataformas el nombre y el mensaje que decidas dejar.</li>
<li><strong>Preferencias de lectura:</strong> los ajustes del panel de lectura (tamaño de letra, colores, etc.) se guardan solo en tu navegador y no se envían a Ofrenda.</li></ul>
<p>Ofrenda no usa cookies propias ni herramientas de analítica o publicidad. Los proveedores técnicos del sitio (GitHub, que lo aloja; Google Fonts, que entrega tipografías; y Ko-fi, en la página Apoyar) pueden registrar datos técnicos como la dirección IP según sus propias políticas.</p>
<p>Ofrenda no solicita datos sensibles. Te pedimos no incluirlos en tu propuesta ni en tus datos de contacto.</p>"""),
        ("finalidades", "Para qué se usan", """<ul><li>Leer y evaluar tu propuesta.</li>
<li>Responderte y mantener contacto sobre ella.</li>
<li>Si tu texto se publica y lo autorizas: mostrar junto a él tu nombre o firma y, si lo enviaste, el lugar y las líneas sobre ti.</li>
<li>Atender tus consultas, solicitudes y reclamos.</li></ul>
<p>Tus datos no se venden, no se alquilan y no se usan para enviarte publicidad.</p>"""),
        ("terceros", "Quién más interviene", """<p>Para funcionar, Ofrenda se apoya en servicios de terceros que pueden tratar tus datos por cuenta de Ofrenda:</p>
<ul><li><strong>FormSubmit</strong>, que recibe el formulario de propuestas y lo reenvía por correo.</li>
<li><strong>Google (Gmail)</strong>, donde se reciben y guardan los correos.</li>
<li><strong>GitHub</strong>, que aloja el sitio.</li></ul>
<p>Algunos de estos servicios guardan la información en servidores fuera de Colombia. Al enviar tu propuesta y dar tu autorización, aceptas que tus datos se traten en esos servidores para las finalidades descritas.</p>"""),
        ("menores", "Menores de edad", """<p>Si tienes menos de 18 años, envía tu propuesta con el acompañamiento y la autorización de tu madre, padre o representante legal.</p>"""),
        ("conservacion", "Cuánto tiempo se guardan", """<p>Los datos se guardan mientras sean necesarios para las finalidades descritas. Si tu texto está publicado, los datos que lo acompañan se conservan mientras siga publicado. Puedes pedir en cualquier momento que se borren tus datos y tu propuesta.</p>"""),
        ("derechos", "Tus derechos", """<p>Como titular de tus datos tienes derecho a (artículo 8 de la Ley 1581 de 2012):</p>
<ul><li>conocer, actualizar y rectificar tus datos;</li>
<li>pedir prueba de la autorización que diste;</li>
<li>ser informado, si lo pides, sobre el uso que se ha dado a tus datos;</li>
<li>presentar quejas ante la Superintendencia de Industria y Comercio;</li>
<li>revocar la autorización o pedir que se borren tus datos, en los términos que establece la ley;</li>
<li>acceder gratis a tus datos.</li></ul>"""),
        ("ejercer", "Cómo ejercerlos", f"""<p>Escribe a {C} con el asunto «Datos personales», tu nombre, el correo con el que enviaste tu propuesta y lo que solicitas.</p>
<ul><li><strong>Consultas:</strong> se responden en máximo 10 días hábiles. Si no es posible, te avisaremos el motivo y la nueva fecha, que no superará 5 días hábiles más (artículo 14 de la Ley 1581).</li>
<li><strong>Reclamos</strong> (corrección, actualización, supresión o incumplimiento): se atienden en máximo 15 días hábiles, prorrogables hasta por 8 días hábiles más avisándote el motivo (artículo 15 de la Ley 1581).</li></ul>
<p>Si después de este trámite no estás conforme, puedes acudir a la {norma("sic", "Superintendencia de Industria y Comercio")}.</p>"""),
        ("seguridad", "Seguridad", """<p>Ofrenda toma medidas razonables para proteger tus datos: por ejemplo, su correo no aparece escrito en el código del sitio y los datos del formulario viajan cifrados. Ningún sistema en internet es completamente seguro, así que te pedimos no enviar información que no sea necesaria.</p>"""),
        ("vigencia", "Vigencia y cambios", f"""<p>Esta política rige desde el {ACTUALIZACION}. Si cambia, la nueva versión se publicará en esta página con su fecha de actualización.</p>"""),
    ]
    intro = "Esta política explica qué datos personales recoge Ofrenda, para qué los usa y cómo puedes conocerlos, corregirlos o pedir que se borren."
    return legal("privacidad/", "Política de tratamiento de datos personales", "Cómo trata Ofrenda los datos personales, según la Ley 1581 de 2012.", intro, sec)


def gracias():
    cuerpo = f"""<div class="wrap"><section class="page enviar-gracias">
  <div>
    <p class="mono">VI — Envía tu propuesta</p>
    <h1>Gracias</h1>
    <p class="big">Tu propuesta llegó. La leeremos con atención y te escribiremos al correo que dejaste.</p>
    <p><a class="btn-leer mono" href="{BASE}">Volver a la portada</a></p>
  </div>
</section></div>"""
    return pagina("enviar/gracias/", "Gracias por tu propuesta", "Tu propuesta llegó a Ofrenda.", cuerpo, indexar=False)


def redireccion(destino, texto="Ir a Quién habita"):
    u = f"{BASE}{destino}"
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Ofrenda</title>
<link rel="canonical" href="{URL}/{destino}"><meta name="robots" content="noindex">
<meta http-equiv="refresh" content="0; url={u}"></head>
<body><p><a href="{u}">{texto}</a></p></body></html>
"""


def apoyar():
    A = SITIO.get("apoyo", {})
    formas = ""
    for o in A.get("opciones", []):
        tipo = o.get("tipo")
        cab = f'<div class="aporte-cab"><b>{e(o["plataforma"])}</b><small>{e(o.get("detalle", ""))}</small></div>'
        if tipo == "kofi" and o.get("usuario"):
            src = f'https://ko-fi.com/{e(o["usuario"])}/?hidefeed=true&amp;widget=true&amp;embed=true'
            formas += (f'<li class="aporte">{cab}<div class="breb kofi"><div class="breb-marco">'
                       f'<p class="breb-et mono">Un gesto desde cualquier lugar</p>'
                       f'<div class="kofi-panel"><iframe id="kofiframe" src="{src}" '
                       f'title="Hacer un aporte a Ofrenda en Ko-fi" loading="lazy" height="550"></iframe></div>'
                       f'</div></div></li>')
        elif tipo == "breb" and o.get("llave"):
            qr = (f'<div class="breb-qr"><img src="{BASE}{e(o["qr"])}" width="600" height="600" '
                  f'alt="Código QR de Bre-B para aportar a Ofrenda"></div>' if o.get("qr") else "")
            formas += (f'<li class="aporte">{cab}<div class="breb"><div class="breb-marco">'
                       f'<p class="breb-et mono">Un gesto desde aquí</p>'
                       f'<div class="breb-cuerpo">{qr}<div class="breb-llave">'
                       f'<span class="mono">Llave Bre-B</span>'
                       f'<code class="llave">{e(o["llave"])}</code>'
                       f'<button class="copiar mono" type="button" data-copiar="{e(o["llave"])}">Copiar llave</button>'
                       f'<p class="breb-nota">Al transferir, tu app te mostrará el nombre de quien recibe, en parte oculto, para que confirmes que es correcto.</p>'
                       f'</div></div></div></div></li>')
        elif o.get("url"):
            formas += (f'<li class="way"><div><b>{e(o["plataforma"])}</b><small>{e(o.get("detalle", ""))}</small></div>'
                       f'<a class="mono" href="{e(o["url"])}" target="_blank" rel="noopener">Aportar</a></li>')
    cuerpo = f"""<div class="wrap"><section class="page">
  <div>
    <p class="mono">V — Apoyar</p>
    <h1>Sostener Ofrenda</h1>
    <p class="big">{e(A.get("texto", ""))}</p>
    <ul class="ways">{formas}</ul>
    <p class="note">Los aportes se procesan en la plataforma elegida; este sitio no guarda datos de pago. Gracias por leer.</p>
  </div>
  <aside><picture class="logo-oficial"><source srcset="{BASE}assets/grabado-portada.webp" type="image/webp"><img src="{BASE}assets/grabado-portada.jpg" width="900" height="1200" loading="lazy" alt="Grabado de Ofrenda: una misma persona sentada, en tamaño grande y pequeño, con una cinta verde."></picture></aside>
</section></div>"""
    return pagina("apoyar/", "Apoyar", "Formas de apoyar Ofrenda, espacio de escritura.",
                  cuerpo, banda=False)


def no_encontrado():
    cuerpo = f'<div class="wrap"><p class="error">Esta página no existe. <a href="{BASE}">Volver a la portada</a></p></div>'
    return pagina("404.html", "Página no encontrada", SITIO["descripcion"], cuerpo, indexar=False)


# ---------- escritura ----------
def escribir(ruta, contenido):
    p = os.path.join(RAIZ, ruta)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(contenido)


for d in GENERADAS:
    shutil.rmtree(os.path.join(RAIZ, d), ignore_errors=True)

escribir("index.html", portada())
for k in ORDEN:
    escribir(f"{k}/index.html", seccion(k))
    for G in GENEROS[k]:
        escribir(f"{k}/{G['id']}/index.html", genero(k, G))
for x in ESCRITOS:
    escribir(f"escritos/{x['id']}/index.html", escrito(x))
for C in CUADERNOS:
    escribir(f"breves/poesia/{C['id']}/index.html", cuaderno(C))
    _pagina_de = {int(m.group(1)): i for i, t in enumerate(C["poemas"], 1) if (m := NUM_POEMA.match(t))}
    for viejo, num in C.get("antiguas", {}).items():
        escribir(f"escritos/{viejo}/index.html",
                 redireccion(f"breves/poesia/{C['id']}/#poema-{_pagina_de.get(num, 1)}", "Ir al cuaderno"))
for L in LIBROS:
    escribir(url_libro(L)[len(BASE):] + "index.html", libro(L))
escribir("quien-habita/index.html", quien_habita())
escribir("enviar/index.html", enviar())
escribir("enviar/gracias/index.html", gracias())
escribir("terminos/index.html", terminos())
escribir("derechos-de-autor/index.html", derechos())
escribir("privacidad/index.html", privacidad())
escribir("acerca/index.html", redireccion("quien-habita/"))
escribir("apoyar/index.html", apoyar())
escribir("404.html", no_encontrado())

hoy = datetime.date.today().isoformat()
urls = [("", hoy)]
for k in ORDEN:
    urls += [(f"{k}/", hoy)] + [(f"{k}/{G['id']}/", hoy) for G in GENEROS[k]]
urls += [(f"breves/poesia/{C['id']}/", C["fecha"]) for C in CUADERNOS if not C.get("muestra")]
urls += [(url_libro(L)[len(BASE):], L["fecha"]) for L in LIBROS if not L.get("muestra")]
urls += [("quien-habita/", None), ("apoyar/", None), ("enviar/", None), ("terminos/", None), ("derechos-de-autor/", None), ("privacidad/", None)]
urls += [(f"escritos/{x['id']}/", x["fecha"]) for x in ESCRITOS if not x.get("muestra")]
sm = "".join(f"<url><loc>{e(URL + '/' + u)}</loc>{f'<lastmod>{m}</lastmod>' if m else ''}</url>\n" for u, m in urls)
escribir("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n'
         '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + sm + "</urlset>\n")
escribir("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {URL}/sitemap.xml\n")
print(f"Sitio generado: {len(CUADERNOS)} cuadernos, {len(ESCRITOS)} escritos, {len(urls)} direcciones en el sitemap.")
