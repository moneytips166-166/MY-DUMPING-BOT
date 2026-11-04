#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DORK PACK BUILDER — bot_fixed.py se saara dork/template/keyword/SQLi data nikaal ke
ek saaf-suthri ZIP banata hai.

  python3 build_dork_pack.py            # bot_fixed.py padh ke zip banata hai
  python3 build_dork_pack.py --out x.zip

Zip me kya:
  01 DORK GEN v2 (UHQ Pro) — 10 templates + variable pools + sample dorks
  02 CLASSIC dork templates — 223, 12 category me banthe
  03 UNIVERSAL DORDS — 7 families + niche table + variables
  04 CMS DORKS — wordpress / joomla / drupal / ...
  05 KEYWORD PACK — payment seeds + templates + niche keywords
  06 SQLI PACK — payloads + gold params + sensitive fields
  07 PARAMS / EXTS / TLDS / PAGES
  08 ALL IN ONE — sab ek file me + ready-to-use dork list
"""
import argparse
import ast
import csv
import io
import os
import random
import re
import zipfile
from datetime import datetime

BOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot_fixed.py")

# ── bot_fixed.py se data nikalo ───────────────────────────────────────────────
WANTED = [
    "DORK_TEMPLATES", "PHP_PARAMS", "ASPX_PARAMS", "CMS_DORKS", "SENSITIVE_KEYWORDS",
    "PAYMENT_SEEDS", "PAYMENT_KEYWORD_TEMPLATES", "SQLI_PAYLOADS", "KW_SPINNER_FRAMES",
    "DORK_SPINNER_FRAMES", "_ADORK_TEMPLATES", "_ADORK_DEFAULT_DOMAINS",
    "_ADORK_DEFAULT_PARAMS", "_ADORK_DEFAULT_FILETYPES", "_ADORK_DEFAULT_SF",
    "_ADORK_DEFAULT_PF", "_V22_PARAMS", "_V22_EXTS", "_V22_PAGES", "_V22_MODS",
    "_V22_TLDS", "_V22_NICHE", "_V22_NICHE_TERMS", "_V19_DORK_FILES",
    "_V19_DORK_PARAMS", "_V19_DORK_TLDS", "_V14_GOLD_SQLI_PARAMS", "_V8_CLEAN_NICHE_MODIFIERS",
]


def load_data():
    src = open(BOT, encoding="utf-8").read()
    tree = ast.parse(src)
    data = {}
    for node in tree.body:
        target = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
        elif isinstance(node, ast.AnnAssign):      # _NAME: dict = {...}
            target = node.target
        name = getattr(target, "id", None) if target is not None else None
        if name in WANTED:
            try:
                data[name] = ast.literal_eval(node.value)
                data["_RANGE_" + name] = (node.lineno, node.end_lineno)
            except Exception:
                pass
    data["_SRC"] = src
    return data


def classic_categories(src, rng):
    """DORK_TEMPLATES ke andar ke CATEGORY comments ke hisaab se todo (line range se)."""
    lines = src.splitlines()
    a, b = rng
    block = lines[a - 1:b]
    cats, cur = [], {"name": "General", "items": []}
    for line in block:
        m = re.search(r"#\s*─+\s*CATEGORY\s*(\d+)\s*:\s*(.+?)\s*─*\s*$", line)
        if m:
            if cur["items"]:
                cats.append(cur)
            cur = {"name": "CATEGORY %s - %s" % (m.group(1), m.group(2).strip()), "items": []}
            continue
        s = line.strip()
        if s.startswith("'"):
            try:
                cur["items"].append(ast.literal_eval(s.rstrip(",")))
            except Exception:
                pass
    if cur["items"]:
        cats.append(cur)
    return cats


def safe(name):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", str(name))[:80]


# ── sample dork generators ───────────────────────────────────────────────────
def gen_v2_sample(data, keyword="shop", n=1000, seed=7):
    rnd = random.Random(seed)
    tpls = data.get("_ADORK_TEMPLATES") or {}
    dom = data.get("_ADORK_DEFAULT_DOMAINS") or [".com"]
    par = data.get("_ADORK_DEFAULT_PARAMS") or ["id"]
    ft = data.get("_ADORK_DEFAULT_FILETYPES") or [".php"]
    sf = data.get("_ADORK_DEFAULT_SF") or ["inurl:"]
    pf = data.get("_ADORK_DEFAULT_PF") or ["index"]
    nb = ["1", "2", "10", "0"]
    out, seen = [], set()
    keys = list(tpls.keys())
    while len(out) < n:
        tid = rnd.choice(keys)
        t = tpls[tid]["template"]
        d = (t.replace("{KW}", keyword)
              .replace("{DE}", rnd.choice(dom))
              .replace("{PF}", rnd.choice(pf))
              .replace("{PT}", rnd.choice(par))
              .replace("{NB}", rnd.choice(nb))
              .replace("{SF}", rnd.choice(sf)))
        d = " ".join(d.split())
        if d.lower() in seen:
            continue
        seen.add(d.lower())
        out.append(d)
    return out


def gen_universal_sample(data, keywords, niche="general", n=500, seed=11):
    rnd = random.Random(seed)
    params = data.get("_V22_PARAMS") or ["id"]
    exts = data.get("_V22_EXTS") or ["php"]
    pages = data.get("_V22_PAGES") or ["index"]
    mods = data.get("_V22_MODS") or ["inurl:"]
    tlds = data.get("_V22_TLDS") or [".com"]
    terms = list(keywords) + list((data.get("_V22_NICHE_TERMS") or {}).get(niche, []))
    rnd.shuffle(params); rnd.shuffle(pages); rnd.shuffle(exts)
    out, seen = [], set()

    def emit(d):
        d = " ".join(d.split())
        if d and d.lower() not in seen:
            seen.add(d.lower()); out.append(d)

    for t in terms:
        for page in pages:
            for prm in params:
                for ext in exts[:3]:
                    emit("%s inurl:%s.%s?%s=" % (t, page, ext, prm))
                    if len(out) >= n: return out
    for t in terms:
        for prm in params:
            for mod in ("inurl:?", "allinurl:?"):
                emit("%s %s%s=" % (t, mod, prm))
                if len(out) >= n: return out
    for t in terms:
        for prm in params[:24]:
            for tld in tlds[:12]:
                emit('"%s" inurl:?%s= site:%s' % (t, prm, tld))
                if len(out) >= n: return out
    for t in terms:
        for mod in mods:
            for page in pages[:18]:
                emit("%s %s%s" % (mod, t, page))
                if len(out) >= n: return out
    for t in terms:
        for prm in params[:20]:
            for pat in ("inurl:api?%s=", "inurl:ajax?%s=", "inurl:json?%s=", "inurl:rest?%s="):
                emit("%s %s" % (t, pat % prm))
                if len(out) >= n: return out
    for t in terms:
        for pat in ("admin", "panel", "cp", "dashboard", "manage", "backend"):
            for prm in params[:10]:
                emit("%s inurl:%s inurl:?%s=" % (t, pat, prm))
                if len(out) >= n: return out
    return out


def fill(tpl, kw="shop", prm="id"):
    return tpl.replace("{kw}", kw).replace("{KW}", kw).replace("{param}", prm).replace("{PT}", prm)


def write(zf, path, text):
    zf.writestr(path, text if text.endswith("\n") else text + "\n")


# ── main ─────────────────────────────────────────────────────────────────────
def build(out_zip):
    d = load_data()
    src = d.pop("_SRC")
    cats = classic_categories(src, d.get("_RANGE_DORK_TEMPLATES") or (239, 486))
    tpls = d.get("_ADORK_TEMPLATES") or {}
    stamp = datetime.now().strftime("%d %b %Y")

    files = 0
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        R = "PYTHON_SNAKE_DORK_PACK/"

        # ── README ──
        write(zf, R + "README.md", f"""# 🐍 PYTHON SNAKE — DORK PACK

> Banaya: {stamp} • Source: `bot_fixed.py`
> Ye pack bot ke andar ka **saara** dork / keyword / SQLi / param data hai — organised text files me.

## Folder map

| Folder | Kya hai | Kitna |
|---|---|---|
| `01_DORK_GEN_V2_UHQ_PRO/` | **Dork Gen v2 (UHQ Pro)** ke 10 templates + variable pools | {len(tpls)} templates |
| `02_CLASSIC_DORK_TEMPLATES/` | purane classic dork templates (12 category) | {sum(len(c['items']) for c in cats)} templates |
| `03_UNIVERSAL_DORKS/` | Universal Dork Engine ke 7 families + niche table | 7 families |
| `04_CMS_DORKS/` | WordPress / Joomla / Drupal … dorks | {len(d.get('CMS_DORKS') or {})} CMS |
| `05_KEYWORD_PACK/` | payment seeds + keyword templates + niche words | {len(d.get('PAYMENT_SEEDS') or [])} seeds |
| `06_SQLI_PACK/` | payloads + gold params + sensitive fields | {len(d.get('SQLI_PAYLOADS') or [])} payload |
| `07_PARAMS_EXTS_TLDS/` | params / extensions / TLDs / pages / file names | {len(d.get('PHP_PARAMS') or [])}+ |
| `08_ALL_IN_ONE/` | sab kuch ek file me + ready-to-use dork list | — |

## Placeholders (template me ye badalte hain)

| Placeholder | Matlab | Values kahan |
|---|---|---|
| `{{kw}}` / `{{KW}}` | keyword | aapka keyword |
| `{{param}}` / `{{PT}}` | URL parameter | `07_.../params.txt` |
| `{{PF}}` | page name | `01_.../variables.txt` |
| `{{DE}}` | domain TLD | `.com .net .ru …` |
| `{{NB}}` | number | 0 / 1 / 2 / 10 |
| `{{SF}}` | search filter | `inurl:` `intitle:` … |

## Kaise use kare

1. Template file se ek line uthao → placeholders bharo → Google me daalo.
2. Ya `08_ALL_IN_ONE/ready_dorks.txt` seedha uthao — already bhare hue dorks.
3. Dork Gen v2 ke templates **UHQ Pro** hain — `(SF)(KW).(PF)?(PT)=(NB) site:(DE)` type ke advanced.

## Note
Ye **template/reference pack** hai (bot ka data). Koi live exploit ya credential nahi hai.
""")

        # ══ 01 DORK GEN V2 ══
        name1 = R + "01_DORK_GEN_V2_UHQ_PRO/"
        lines = ["# DORK GEN v2 (UHQ Pro) — templates", "# format: {id} | {label} | {template} | vars", ""]
        for tid, info in tpls.items():
            lines.append("%-4s | %-38s | %-40s | %s"
                         % (tid, info.get("label", ""), info.get("template", ""),
                            ",".join(info.get("vars") or [])))
        write(zf, name1 + "templates.txt", "\n".join(lines))

        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["id", "label", "template", "vars"])
        for tid, info in tpls.items():
            w.writerow([tid, info.get("label", ""), info.get("template", ""),
                        ",".join(info.get("vars") or [])])
        write(zf, name1 + "templates.csv", buf.getvalue())

        write(zf, name1 + "variables.txt", "\n".join([
            "# DORK GEN v2 — variable pools", "",
            "## Domains ({DE})", *d.get("_ADORK_DEFAULT_DOMAINS", []), "",
            "## Params ({PT})", *d.get("_ADORK_DEFAULT_PARAMS", []), "",
            "## File types", *d.get("_ADORK_DEFAULT_FILETYPES", []), "",
            "## Search filters ({SF})", *d.get("_ADORK_DEFAULT_SF", []), "",
            "## Page filters ({PF})", *d.get("_ADORK_DEFAULT_PF", []), "",
            "## Numbers ({NB})", "0", "1", "2", "10", "",
        ]))

        write(zf, name1 + "how_it_works.md", """# Dork Gen v2 (UHQ Pro) kaise kaam karta hai

Bot 10 template families leta hai aur unme aapke keyword + random variables bharta hai:

```
(KW).(PF)?(PT)=                        →  shop.index?id=
(SF)(KW).(PF)?(PT)=(NB) site:(DE)      →  inurl:shop.view?id=2 site:.ru
(SF)(PT)=(KW).(PF)? site:(DE)          →  intitle:id=shop.view? site:.de
```

**Variables (random rotate hote hain):**
- KW = aapka keyword
- PF = index / view / page / item / product / user / login / search / show / cat
- PT = id / user_id / cat / type / page / item / product
- SF = inurl: / intitle: / allinurl: / allintitle:
- DE = .com .net .org .ru .de .in .pk .us .uk .info
- NB = 0 / 1 / 2 / 10

**Fayda:** 10 templates × 10 PF × 7 PT × 4 SF × 10 DE = **~28,000 unique dork** ek keyword pe.
Bot "exact count" deta hai — jitna maango, sab unique.
""")
        write(zf, name1 + "sample_dorks_1000.txt",
              "\n".join(["# Dork Gen v2 sample — keyword: shop (1000 dorks)", ""] + gen_v2_sample(d, "shop", 1000)))

        # ══ 02 CLASSIC ══
        name2 = R + "02_CLASSIC_DORK_TEMPLATES/"
        allc = []
        index = ["# CLASSIC dork templates — 12 category", ""]
        for ci, c in enumerate(cats, 1):
            fn = "%02d_%s.txt" % (ci, safe(c["name"].split("-", 1)[-1].strip().replace(" ", "_")))
            write(zf, name2 + fn, "\n".join(["# " + c["name"], "# total: %d" % len(c["items"]), ""]
                                            + c["items"]))
            index.append("%2d. %-44s %3d  →  %s" % (ci, c["name"][:44], len(c["items"]), fn))
            allc.extend(c["items"])
        write(zf, name2 + "_INDEX.md", "\n".join(index
                                                 + ["", "**Total: %d templates**" % len(allc)]))
        write(zf, name2 + "ALL_templates.txt", "\n".join(["# saare %d classic templates" % len(allc), ""] + allc))
        write(zf, name2 + "ALL_filled_keyword_shop.txt",
              "\n".join(["# saare templates, keyword = shop, param = id", ""]
                        + [fill(t) for t in allc]))

        # ══ 03 UNIVERSAL ══
        name3 = R + "03_UNIVERSAL_DORKS/"
        write(zf, name3 + "families.md", """# Universal Dork Engine — 7 families

Keyword dekh ke niche khud detect hota hai, phir ye families chalti hain:

| # | Family | Format |
|---|---|---|
| A | page + param + ext | `{term} inurl:{page}.{ext}?{param}=` |
| B | plain inurl param | `{term} inurl:?{param}=` / `allinurl:?{param}=` |
| C | niche + param + TLD | `"{term}" inurl:?{param}= site:{tld}` |
| D | mod + page | `{mod} {term}{page}` |
| E | api / ajax / json / rest | `{term} inurl:api?{param}=` |
| F | admin / panel / dashboard | `{term} inurl:admin inurl:?{param}=` |
| G | filler | jab count bacha ho |

**Variables:** pages 33 • params 41 • exts 8 • mods 11 • TLDs 20
""")
        write(zf, name3 + "variables.txt", "\n".join([
            "# Universal engine variables", "",
            "## Params", *d.get("_V22_PARAMS", []), "",
            "## Pages", *d.get("_V22_PAGES", []), "",
            "## Extensions", *d.get("_V22_EXTS", []), "",
            "## Mods", *d.get("_V22_MODS", []), "",
            "## TLDs", *d.get("_V22_TLDS", []), "",
        ]))
        nic_lines = ["# Niche table", "", "## Niche → detect words"]
        for k, v in (d.get("_V22_NICHE") or {}).items():
            nic_lines.append("- **%s**: %s" % (k, ", ".join(v)))
        nic_lines += ["", "## Niche → extra terms"]
        for k, v in (d.get("_V22_NICHE_TERMS") or {}).items():
            nic_lines.append("- **%s**: %s" % (k, ", ".join(v)))
        write(zf, name3 + "niches.md", "\n".join(nic_lines))
        write(zf, name3 + "sample_general_500.txt",
              "\n".join(["# Universal sample — general niche (500)", ""]
                        + gen_universal_sample(d, ["login", "account"], "general", 500)))
        write(zf, name3 + "sample_gaming_500.txt",
              "\n".join(["# Universal sample — gaming niche (500)", ""]
                        + gen_universal_sample(d, ["steam", "valorant"], "gaming", 500)))

        # ══ 04 CMS ══
        name4 = R + "04_CMS_DORKS/"
        idx4 = ["# CMS dorks", ""]
        for cms, arr in (d.get("CMS_DORKS") or {}).items():
            write(zf, name4 + safe(cms) + ".txt", "\n".join(["# " + cms, ""] + list(arr)))
            idx4.append("- **%s**: %d dorks → `%s.txt`" % (cms, len(arr), safe(cms)))
        write(zf, name4 + "_INDEX.md", "\n".join(idx4))

        # ══ 05 KEYWORD ══
        name5 = R + "05_KEYWORD_PACK/"
        write(zf, name5 + "payment_seeds.txt", "\n".join(["# payment / CC seeds", ""] + d.get("PAYMENT_SEEDS", [])))
        write(zf, name5 + "payment_keyword_templates.txt",
              "\n".join(["# payment keyword templates", ""] + d.get("PAYMENT_KEYWORD_TEMPLATES", [])))
        write(zf, name5 + "niche_keywords.txt", "\n".join(
            ["# niche keywords", ""] + ["## " + k + "\n" + "\n".join(v) + "\n"
                                        for k, v in (d.get("_V22_NICHE") or {}).items()]))

        # ══ 06 SQLI ══
        name6 = R + "06_SQLI_PACK/"
        write(zf, name6 + "payloads.txt", "\n".join(["# SQLi test payloads", ""] + d.get("SQLI_PAYLOADS", [])))
        write(zf, name6 + "gold_params.txt", "\n".join(["# high-hit SQLi params", ""] + d.get("_V14_GOLD_SQLI_PARAMS", [])))
        sens = ["# Sensitive field names (CC / CVV / expiry ...)", ""]
        for k, v in (d.get("SENSITIVE_KEYWORDS") or {}).items():
            sens += ["## " + k, *v, ""]
        write(zf, name6 + "sensitive_fields.txt", "\n".join(sens))

        # ══ 07 PARAMS ══
        name7 = R + "07_PARAMS_EXTS_TLDS/"
        write(zf, name7 + "php_params.txt", "\n".join(["# PHP params (%d)" % len(d.get('PHP_PARAMS', [])), ""] + d.get("PHP_PARAMS", [])))
        write(zf, name7 + "aspx_params.txt", "\n".join(["# ASPX params", ""] + d.get("ASPX_PARAMS", [])))
        write(zf, name7 + "universal_params.txt", "\n".join(["# universal params", ""] + d.get("_V22_PARAMS", [])))
        write(zf, name7 + "pages.txt", "\n".join(["# page names", ""] + d.get("_V22_PAGES", [])))
        write(zf, name7 + "extensions.txt", "\n".join(["# extensions", ""] + d.get("_V22_EXTS", [])))
        write(zf, name7 + "tlds.txt", "\n".join(["# TLDs", ""] + d.get("_V22_TLDS", [])))
        write(zf, name7 + "dork_page_files.txt", "\n".join(["# page files (product.php ...)", ""] + d.get("_V19_DORK_FILES", [])))
        write(zf, name7 + "dork_params.txt", "\n".join(["# dork params", ""] + d.get("_V19_DORK_PARAMS", [])))
        write(zf, name7 + "dork_tlds.txt", "\n".join(["# dork TLDs", ""] + d.get("_V19_DORK_TLDS", [])))
        write(zf, name7 + "clean_niche_modifiers.txt", "\n".join(["# refinery modifiers", ""] + d.get("_V8_CLEAN_NICHE_MODIFIERS", [])))

        # ══ 08 ALL IN ONE ══
        name8 = R + "08_ALL_IN_ONE/"
        combo = ["# SAARE templates — ek file me", "", "## DORK GEN v2 (UHQ Pro)"]
        combo += ["%-40s  %s" % (i["template"], i.get("label", "")) for i in tpls.values()]
        combo += ["", "## CLASSIC (%d)" % len(allc)] + allc
        combo += ["", "## CMS"]
        for cms, arr in (d.get("CMS_DORKS") or {}).items():
            combo += [""] + list(arr)
        write(zf, name8 + "all_templates.txt", "\n".join(combo))

        ready = []
        ready += gen_v2_sample(d, "shop", 2000, seed=3)
        ready += gen_v2_sample(d, "login", 1500, seed=4)
        ready += gen_universal_sample(d, ["shop", "store"], "ecom", 1500, seed=5)
        ready += [fill(t, "shop", "id") for t in allc]
        seen, uniq = set(), []
        for r in ready:
            if r.lower() not in seen:
                seen.add(r.lower()); uniq.append(r)
        write(zf, name8 + "ready_dorks.txt",
              "\n".join(["# READY-TO-USE dorks (%d unique) — copy → Google" % len(uniq), ""] + uniq))

        write(zf, name8 + "stats.txt", "\n".join([
            "# PACK STATS", "",
            "dork_gen_v2_templates : %d" % len(tpls),
            "classic_templates     : %d" % len(allc),
            "classic_categories    : %d" % len(cats),
            "cms_profiles          : %d" % len(d.get("CMS_DORKS") or {}),
            "payment_seeds         : %d" % len(d.get("PAYMENT_SEEDS") or []),
            "payment_kw_templates  : %d" % len(d.get("PAYMENT_KEYWORD_TEMPLATES") or []),
            "sqli_payloads         : %d" % len(d.get("SQLI_PAYLOADS") or []),
            "php_params            : %d" % len(d.get("PHP_PARAMS") or []),
            "universal_params      : %d" % len(d.get("_V22_PARAMS") or []),
            "universal_pages       : %d" % len(d.get("_V22_PAGES") or []),
            "ready_dorks           : %d" % len(uniq),
            "",
            "generated: %s" % stamp,
        ]))

        files = len(zf.namelist())

    size = os.path.getsize(out_zip)
    print("=" * 66)
    print("  ✅ DORK PACK READY")
    print("=" * 66)
    print("  File    : %s" % os.path.basename(out_zip))
    print("  Size    : %.1f KB" % (size / 1024))
    print("  Files   : %d" % files)
    print("  v2 tpl  : %d   classic: %d   ready dorks: %d" % (len(tpls), len(allc), len(uniq)))
    print("=" * 66)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="PYTHON_SNAKE_DORK_PACK.zip")
    a = ap.parse_args()
    build(a.out)
