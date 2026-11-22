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

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]
SECCIONES = {
    "breves": {"num": "I", "nombre": "Textos breves", "corto": "Breves", "titular": "Lo breve", "resumen": "Fragmentos, apuntes y piezas cortas que nacen de una lectura, una conversación o una imagen.", "desc": "Escritura de texto corto", "imagen": "grabado-breves"},
    "largos": {"num": "II", "nombre": "Textos largos", "corto": "Largos", "desc": "Escritura de texto largo", "imagen": "grabado-largos"},
    "lecturas": {"num": "III", "nombre": "Lecturas que me atraviesan", "corto": "Lecturas",
                 "desc": "Reflexiones sobre libros y artículos leídos", "imagen": "grabado-lecturas"},
}
ORDEN = ["breves", "largos", "lecturas"]
GENERADAS = ["breves", "largos", "lecturas", "acerca", "apoyar", "escritos"]

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
    titulo_full = titulo if titulo == SITIO["nombre"] else f"{titulo} · {SITIO['nombre']}"
    verif = (f'<meta name="google-site-verification" content="{e(SITIO["google_verificacion"])}">'
             if SITIO.get("google_verificacion") else "")
    robots = "" if indexar else '<meta name="robots" content="noindex">'
    apoyo = SITIO.get("apoyo", {})
    banda_html = f"""
<section class="support-band" aria-label="Apoyar este espacio">
  <div class="wrap">
    {lienzo("apoyo-sello", dens="2")}
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
<title>{e(titulo_full)}</title>
<meta name="description" content="{e(desc)}">
<meta name="author" content="{e(SITIO['autora'])}">
{robots}{verif}
<link rel="canonical" href="{e(canon)}">
<meta property="og:site_name" content="{e(SITIO['nombre'])}">
<meta property="og:title" content="{e(titulo)}">
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
    <a class="bar-center mono" href="{BASE}">Escritos · Lecturas</a>
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
      <li><a href="{BASE}acerca/"><span class="mono">IV</span><span>Acerca de este espacio</span></a></li>
      <li><a href="{BASE}apoyar/"><span class="mono">V</span><span>Apoyar</span></a></li>
    </ol>
  </div>
</nav>

<main id="view">
{cuerpo}
</main>
{banda_html}
<footer>
  <div class="wrap">
    <span class="mono">{e(SITIO['nombre'])} · {e(SITIO['autora'])}</span>
    <nav class="mono" aria-label="Pie">
      <a href="{BASE}breves/">Breves</a><a href="{BASE}largos/">Largos</a><a href="{BASE}lecturas/">Lecturas</a><a href="{BASE}acerca/">Acerca</a><a href="{BASE}apoyar/">Apoyar</a>
    </nav>
  </div>
</footer>
<script src="{BASE}assets/sitio.js?v={VERSION}" defer></script>
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
    for x in sorted(ESCRITOS, key=lambda y: (y["fecha"], y.get("numero", 0))):
        if x.get("muestra"):
            continue
        u = url_escrito(x)
        if x.get("poemas"):
            for t in x["poemas"]:
                pool.append({"t": NUM_POEMA.sub("", t, count=1), "titulo": x["titulo"], "url": u})
        else:
            pool.append({"t": extracto(x), "titulo": x["titulo"], "url": u})
    if not pool:
        return ""
    a = pool[0]
    estrofas = "".join(f"<p>{e(q)}</p>" for q in re.split(r"\n[ \t]*\n", a["t"]) if q)
    datos = json.dumps(pool, ensure_ascii=False).replace("</", "<\\/")
    return (f'<aside class="pantalla" aria-label="Un texto de Ofrenda al azar"><div class="pantalla-marco">'
            f'<p class="pantalla-et mono">Al azar</p>'
            f'<div class="pantalla-texto" aria-live="polite">{estrofas}</div>'
            f'<div class="pantalla-pie"><a class="pantalla-fuente mono" href="{a["url"]}">De «{e(a["titulo"])}»</a>'
            f'<button class="pantalla-otro mono" type="button">Otro texto</button></div>'
            f'</div></aside><script type="application/json" id="pantalla-datos">{datos}</script>')

def portada():
    pills = f'<a class="pill" href="#ultimos" aria-current="true">Todo</a>' + "".join(
        f'<a class="pill" href="{BASE}{k}/">{SECCIONES[k]["corto"]}</a>' for k in ORDEN)
    dest_html = ""
    for k in ORDEN:
        lista = por_seccion(k)
        reales = [x for x in lista if not x.get("muestra")]
        base = reales or lista
        if not base:
            continue
        dest = max(base, key=lambda x: (fecha(x["fecha"]), x.get("numero", 0)))
        S = SECCIONES[k]
        a_seccion = bool(S.get("titular")) and bool(reales)
        u = f"{BASE}{k}/" if a_seccion else url_escrito(dest)
        titular = S.get("titular") or dest["titulo"]
        resumen = S["resumen"] if a_seccion else extracto(dest)
        leer = "Ver todos los textos" if a_seccion else "Leer este texto"
        detalle = f"{len(reales)} textos" if a_seccion else f"{minutos(dest)} min"
        ancla = ' id="ultimos"' if not dest_html else ""
        dest_html += f"""
  <section class="featured"{ancla} aria-label="{e(SECCIONES[k]['nombre'])}: último texto">
    <span class="vert mono">{"Muestra · " if dest.get("muestra") else ""}{SECCIONES[k]['corto']}</span>
    <a class="cover" href="{u}" aria-label="{e(leer)}: {e(titular)}">
      <span class="tab mono">{"Muestra" if dest.get("muestra") else "Nuevo"}</span>
      {cubierta(dest)}
    </a>
    <div class="body">
      <h2><a href="{u}">{e(titular)}</a></h2>
      {obra(dest, "obra")}
      <p class="excerpt">{e(resumen)}</p>
      <a class="readlink mono" href="{u}">{e(leer)}</a>
    </div>
    <div class="issue">{"<b>Muestra</b>" if dest.get("muestra") else ""}<span class="mono">{mes_anio(dest['fecha'])} · {detalle}</span></div>
  </section>"""
    cuerpo = f"""<div class="wrap">
  <section class="hero">
    <div>
      <h1 class="masthead"><span>{e(SITIO['nombre'])}</span></h1>
      <p class="lede">Un espacio para pensar, sentir y escribir sobre la experiencia humana junto a la novedad que emerge constantemente en la sociedad. La escritura como el resultado de una exploración intelectual.</p>
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


def seccion(k):
    S = SECCIONES[k]
    lista = list(reversed(por_seccion(k)))
    reales = len([x for x in lista if not x.get("muestra")])
    filas = ""
    for x in lista:
        ob = obra(x, "q").replace('class="q"', 'class="q" style="font-style:normal;color:var(--ink)"')
        filas += f"""<li class="row"><a href="{url_escrito(x)}">
      <div><h2>{e(x['titulo'])}</h2>{ob}<p class="q">{e(extracto(x))}</p></div>
      <span class="d mono">{fecha_larga(x['fecha'])}</span>
    </a></li>"""
    if not filas:
        filas = '<li><p class="empty">El primer texto de esta sección está en preparación.</p></li>'
    cuerpo = f"""<div class="wrap">
  <header class="sec-head">
    <span class="roman">{S['num']}</span>
    <h1>{e(S['nombre'])}</h1>
    <p class="mono">{e(S['desc'])} · {"1 texto" if reales == 1 else f"{reales} textos"}</p>
  </header>
  <ol class="rows" reversed>{filas}</ol>
</div>"""
    return pagina(f"{k}/", S["nombre"], f"{S['nombre']} de {SITIO['autora']}: {S['desc'].lower()}.", cuerpo)


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
    lista = por_seccion(x["seccion"])
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
    cuerpo = f"""<div class="wrap">
  <a class="back mono" href="{BASE}{x['seccion']}/">← {e(S['nombre'])}</a>
  <article class="article">
    <dl class="meta">{meta}</dl>
    <div>
      <h1 class="art-title">{e(x['titulo'])}{tag}</h1>
      {obra(x, "art-obra")}
      {cita}
      <div class="prose{drop}">
{cuerpo_html(x)}
      </div>
      <div class="signoff"><span class="mono">{e(SITIO['autora'])}</span><a class="mono" href="{BASE}apoyar/">Apoyar este espacio</a></div>
      <nav class="pager" aria-label="Otros textos de la sección">{enlace(lista[i - 1] if i > 0 else None, "← Anterior")}{enlace(lista[i + 1] if i + 1 < len(lista) else None, "Siguiente →")}</nav>
    </div>
  </article>
</div>"""
    ld = {"@context": "https://schema.org", "@type": "Review" if x.get("obra") else "Article",
          "headline": x["titulo"], "datePublished": x["fecha"], "inLanguage": "es",
          "author": {"@type": "Person", "name": SITIO["autora"]},
          "mainEntityOfPage": URL + f"/escritos/{x['id']}/", "description": descripcion(x)}
    if x.get("obra"):
        ld["itemReviewed"] = {"@type": "CreativeWork", "name": x["obra"]["titulo"],
                              "author": {"@type": "Person", "name": x["obra"].get("autor", "")}}
    extra = (f'<meta property="article:published_time" content="{x["fecha"]}">'
             f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>')
    return pagina(f"escritos/{x['id']}/", x["titulo"], descripcion(x), cuerpo,
                  indexar=not x.get("muestra"), tipo="article", extra_head=extra)


def acerca():
    secs = "".join(f"""<li><a href="{BASE}{k}/"><span class="mono">{SECCIONES[k]['num']}</span>
      <div><b>{SECCIONES[k]['nombre']}</b><small>{SECCIONES[k]['desc']}</small></div></a></li>""" for k in ORDEN)
    cuerpo = f"""<div class="wrap"><section class="page">
  <div>
    <p class="mono">Acerca de este espacio</p>
    <h1>Biblioteca intelectual que alimenta la escritura</h1>
    <p class="big">Un espacio para pensar, sentir y escribir sobre la experiencia humana.</p>
    <p>La escritura como el resultado de una exploración intelectual. Aquí se publican textos terminados de {e(SITIO['autora'])}, organizados en tres secciones.</p>
    <ul class="secs">{secs}</ul>
  </div>
  <aside>{lienzo("acerca-biblioteca", dens="1.1")}</aside>
</section></div>"""
    return pagina("acerca/", "Acerca de este espacio", SITIO["descripcion"], cuerpo)


def apoyar():
    A = SITIO.get("apoyo", {})
    formas = ""
    for o in A.get("opciones", []):
        tipo = o.get("tipo")
        cab = f'<div class="aporte-cab"><b>{e(o["plataforma"])}</b><small>{e(o.get("detalle", ""))}</small></div>'
        if tipo == "kofi" and o.get("usuario"):
            src = f'https://ko-fi.com/{e(o["usuario"])}/?hidefeed=true&amp;widget=true&amp;embed=true'
            formas += (f'<li class="aporte">{cab}<div class="kofi-marco"><iframe id="kofiframe" src="{src}" '
                       f'title="Hacer un aporte a Ofrenda en Ko-fi" loading="lazy" height="712"></iframe></div></li>')
        elif tipo == "breb" and o.get("llave"):
            qr = (f'<img class="qr" src="{BASE}{e(o["qr"])}" width="180" height="180" alt="Código QR de Bre-B para aportar a Ofrenda">'
                  if o.get("qr") else "")
            formas += (f'<li class="aporte">{cab}<div class="breb">{qr}<div><span class="mono">Llave Bre-B</span>'
                       f'<code class="llave">{e(o["llave"])}</code>'
                       f'<button class="copiar mono" type="button" data-copiar="{e(o["llave"])}">Copiar llave</button></div></div></li>')
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
  <aside>{lienzo("apoyo-pagina", dens="1.3")}</aside>
</section></div>"""
    return pagina("apoyar/", "Apoyar", "Formas de apoyar Ofrenda, el espacio de escritura de " + SITIO["autora"] + ".",
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
for x in ESCRITOS:
    escribir(f"escritos/{x['id']}/index.html", escrito(x))
escribir("acerca/index.html", acerca())
escribir("apoyar/index.html", apoyar())
escribir("404.html", no_encontrado())

hoy = datetime.date.today().isoformat()
urls = [("", hoy), ("breves/", hoy), ("largos/", hoy), ("lecturas/", hoy), ("acerca/", None), ("apoyar/", None)]
urls += [(f"escritos/{x['id']}/", x["fecha"]) for x in ESCRITOS if not x.get("muestra")]
sm = "".join(f"<url><loc>{e(URL + '/' + u)}</loc>{f'<lastmod>{m}</lastmod>' if m else ''}</url>\n" for u, m in urls)
escribir("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n'
         '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + sm + "</urlset>\n")
escribir("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {URL}/sitemap.xml\n")
print(f"Sitio generado: {len(ESCRITOS)} escritos, {len(urls)} direcciones en el sitemap.")
