#!/usr/bin/env python3
"""Multi-page SibNordModul site: catalog, rent, custom, about, gallery, contacts."""
from __future__ import annotations
import html, re, shutil
from pathlib import Path
from urllib.parse import quote

import rebuild as rb

ROOT = rb.ROOT
P = rb  # alias

# Contacts from current site footer
PHONE_DISP = '+7 913 943-88-14'
TEL = 'tel:+79139438814'
LANDLINE_DISP = '+7 (383) 375-00-10'
LANDLINE_TEL = 'tel:+73833750010'
WA = 'https://wa.me/79139438814'
TG = 'https://t.me/Volt0ne'
MAIL = 'mailto:Sibnordmodul@yandex.ru'
MAIL_DISP = 'Sibnordmodul@yandex.ru'
ADDR = 'Новосибирск, мкр. Пашино, Томская улица, 1'
GIS_OPEN = 'https://2gis.ru/novosibirsk/search/Новосибирск, Томская улица, 1, Пашино?m=82.967659,55.161774/17'
GIS_DIR = 'https://2gis.ru/novosibirsk/routeSearch/rsType/car/to/82.967659,55.161774│Томская улица, 1'
LAT, LON = 55.161774, 82.967659
PRICE = '245 000 ₽'
PRICE_NOTE = ('Указанная стоимость — именно за бытовку размером 2,4 × 6 м в комплектации, '
              'представленной на фотографиях и описанной на странице каталога. '
              'Другие варианты рассчитываются отдельно.')
RENT_FROM = 'от 8 000 ₽/мес'

# Main menu (overrides old single-page anchors)
PAGES = [
    ('catalog', 'Каталог бытовок'),
    ('rent', 'Аренда бытовок'),
    ('custom', 'Другие решения под заказ'),
    ('about', 'О компании'),
    ('gallery', 'Фотогалерея'),
    ('contacts', 'Контакты'),
]

CATS = [
    ('all', 'Все'),
    ('universal', 'Бытовка (универсальная)'),
    ('stroitelnye', 'Строительная'),
    ('dachnye', 'Дачная'),
    ('sklad', 'Складская'),
    ('guard', 'Пост охраны'),
    ('office', 'Прорабские / офисные'),
    ('living', 'Раздевалки / жильё бригады'),
    ('san', 'Сан-бытовки'),
    ('modular', 'Модульные дома'),
    ('pavilions', 'Павильоны'),
]


def esc(s):
    return html.escape(s, quote=True)


def wa_link(product):
    text = f'Здравствуйте! Интересует: {product}. Подскажите, пожалуйста, наличие и стоимость.'
    return WA + '?text=' + quote(text)


def pth(depth, rel):
    return ('../' * depth) + rel


# ---------- variants: keep useful ones + requested sizes ----------

def V(**kw):
    kw.setdefault('roof', 'flat')
    kw.setdefault('porch', False)
    kw.setdefault('windows', ())
    kw.setdefault('rooms', ())
    kw.setdefault('priced', False)
    kw.setdefault('stock', True)
    return kw


def size_label(L, W):
    def f(x):
        s = f'{x:.2f}'.rstrip('0').rstrip('.')
        return s.replace('.', ',')
    return f'{f(W)} × {f(L)} м' if False else f'{f(L)} × {f(W)} м'


# Standard display uses L × W as length × width, matching existing 2,40 × 6,00 as width × length
# On this site historically: "2,40 × 6,00 м" means 2.4 wide × 6 long.
# User now says 2×3, 2.4×4, 2.4×6 — first number is typically width (2.4) then length (6).
# I'll display as "2,4 × 6 м" (width × length) to match the product name «утеплённая бытовка 2,4 × 6 м».

def disp(w, L):
    def f(x):
        s = f'{x:.2f}'.replace('.', ',')
        s = s.rstrip('0').rstrip(',')
        if ',' not in s:
            return s + ',00' if x >= 3 or True else s
        return s
    # tighter: 2,4 × 6 м
    def f2(x):
        if abs(x - int(x)) < 1e-9:
            return str(int(x))
        s = f'{x:.1f}'.replace('.', ',')
        return s
    return f'{f2(w)} × {f2(L)} м'


# In scheme generator, L is length (long side), W is width.
# User 2.4×6 means W=2.4, L=6.

VARIANTS = [
    # UNIVERSAL — many sizes; only warm 2.4×6 is priced
    V(slug='uni-2x3', cat='universal', name='Бытовка универсальная 2×3 м',
      size=disp(2, 3), L=3, W=2, door=0.18, windows=(0.62,),
      desc='Компактный универсальный модуль: для инструмента, сторожки или короткой смены.'),
    V(slug='uni-24x4', cat='universal', name='Бытовка универсальная 2,4×4 м',
      size=disp(2.4, 4), L=4, W=2.4, door=0.15, windows=(0.45, 0.75),
      desc='Универсальный размер под стройку, дачу, склад или пост на объекте.'),
    V(slug='bytovka-6x24', cat='universal', name='Утеплённая бытовка 2,4×6 м',
      size='2,4 × 6 м', L=6, W=2.4, door=0.12, windows=(0.42, 0.72),
      priced=True, desc='Основной вариант: графитовый профлист, металлическая дверь, утепление 100 мм. Как на фотографиях.'),
    V(slug='uni-24x7', cat='universal', name='Бытовка универсальная 2,4×7 м',
      size=disp(2.4, 7), L=7, W=2.4, door=0.12, windows=(0.35, 0.55, 0.78),
      desc='Чуть длиннее стандарта — больше места под мебель и оборудование.'),
    V(slug='uni-3x6', cat='universal', name='Бытовка универсальная 3×6 м',
      size=disp(3, 6), L=6, W=3, door=0.12, windows=(0.38, 0.58, 0.8),
      desc='Шире стандартной: удобнее расставить мебель и рабочие места.'),
    V(slug='uni-24x9', cat='universal', name='Бытовка универсальная 2,4×9 м',
      size=disp(2.4, 9), L=9, W=2.4, door=0.1, windows=(0.28, 0.48, 0.68, 0.86),
      desc='Длинный модуль для бригады, склада или совмещённых зон.'),
    V(slug='uni-24x12', cat='universal', name='Бытовка универсальная 2,4×12 м',
      size=disp(2.4, 12), L=12, W=2.4, door=0.08, windows=(0.22, 0.4, 0.58, 0.76, 0.9),
      rooms=(0.5,), desc='Две зоны в одном корпусе длиной 12 м. Планировку согласуем.'),
    V(slug='uni-double', cat='universal', name='Сдвоенный модуль 6×4,8 м',
      size='6 × 4,8 м', L=6, W=4.8, door=0.12, windows=(0.35, 0.55, 0.8),
      rooms=(0.5,), modules=2, stock=False,
      desc='Два состыкованных блока — больше площади без перехода на модульный дом.'),

    # СТРОИТЕЛЬНАЯ
    V(slug='st-24x4', cat='stroitelnye', name='Бытовка строительная 2,4×4 м',
      size=disp(2.4, 4), L=4, W=2.4, door=0.15, windows=(0.45, 0.75),
      desc='Строительный модуль для прораба, инструмента или короткой смены.'),
    V(slug='st-24x6', cat='stroitelnye', name='Утеплённая бытовка 2,4×6 м',
      size='2,4 × 6 м', L=6, W=2.4, door=0.12, windows=(0.42, 0.72),
      priced=True, desc='Тот же основной вариант 2,4×6 м: утепление 100 мм, комплектация как на фото.'),
    V(slug='st-24x7', cat='stroitelnye', name='Бытовка строительная 2,4×7 м',
      size=disp(2.4, 7), L=7, W=2.4, door=0.12, windows=(0.35, 0.55, 0.78),
      desc='Для стройки, когда стандартной шестиметровой уже мало.'),
    V(slug='st-5x24', cat='stroitelnye', name='Бытовка строительная 2,4×5 м с тамбуром',
      size=disp(2.4, 5), L=5, W=2.4, door=0.12, windows=(0.48, 0.78), rooms=(0.22,),
      desc='Планировка с тамбуром: тепло лучше держится, грязь остаётся у входа.'),
    V(slug='st-3x6', cat='stroitelnye', name='Бытовка строительная 3×6 м',
      size=disp(3, 6), L=6, W=3, door=0.12, windows=(0.38, 0.58, 0.8),
      desc='Широкий строительный модуль под офис на объекте или жильё бригады.'),
    V(slug='st-24x9', cat='stroitelnye', name='Бытовка строительная 2,4×9 м',
      size=disp(2.4, 9), L=9, W=2.4, door=0.1, windows=(0.28, 0.48, 0.68, 0.86),
      desc='Длинный строительный модуль: раздевалка и комната отдыха в одном корпусе.'),
    V(slug='st-24x12', cat='stroitelnye', name='Бытовка строительная 2,4×12 м',
      size=disp(2.4, 12), L=12, W=2.4, door=0.08, windows=(0.22, 0.4, 0.58, 0.76, 0.9),
      rooms=(0.5,), desc='Два отсека в корпусе 12 м — под большие объекты.'),

    # ДАЧНАЯ
    V(slug='dacha-24x4', cat='dachnye', name='Бытовка дачная 2,4×4 м с крыльцом',
      size=disp(2.4, 4), L=4, W=2.4, roof='pitched', porch=True, door=0.2, windows=(0.55, 0.8),
      desc='Скатная крыша и крыльцо — для участка и сезонного проживания.'),
    V(slug='dacha-24x6', cat='dachnye', name='Бытовка дачная 2,4×6 м',
      size='2,4 × 6 м', L=6, W=2.4, roof='pitched', porch=True, door=0.14,
      windows=(0.4, 0.62, 0.84), rooms=(0.4,),
      desc='Дачный вариант: скатная крыша, крыльцо, две зоны. Комплектация и цена — по запросу.'),
    V(slug='dacha-24x7', cat='dachnye', name='Бытовка дачная 2,4×7 м',
      size=disp(2.4, 7), L=7, W=2.4, roof='pitched', porch=True, door=0.14,
      windows=(0.35, 0.55, 0.8), rooms=(0.4,),
      desc='Больше длины для кухни и комнаты на участке.'),
    V(slug='dacha-3x6', cat='dachnye', name='Дачный домик 3×6 м',
      size=disp(3, 6), L=6, W=3, roof='pitched', porch=True, door=0.14,
      windows=(0.38, 0.58, 0.8), rooms=(0.45,),
      desc='Просторный дачный модуль с двумя комнатами и крыльцом.'),
    V(slug='dacha-24x9', cat='dachnye', name='Дачный домик 2,4×9 м',
      size=disp(2.4, 9), L=9, W=2.4, roof='pitched', porch=True, door=0.12,
      windows=(0.28, 0.48, 0.68, 0.86), rooms=(0.33, 0.66),
      desc='Три зоны: тамбур, кухня и спальня. Под заказ по вашей планировке.'),

    # СКЛАДСКАЯ
    V(slug='sklad-2x3', cat='sklad', name='Хозблок 2×3 м',
      size=disp(2, 3), L=3, W=2, door=0.2, windows=(0.7,),
      desc='Небольшой хозблок под инструмент, инвентарь или насосную.'),
    V(slug='sklad-24x4', cat='sklad', name='Складская бытовка 2,4×4 м',
      size=disp(2.4, 4), L=4, W=2.4, door=0.16, windows=(0.72,), double_door=True,
      desc='Складской модуль с широкой дверью под стеллажи и ящики.'),
    V(slug='sklad-24x6', cat='sklad', name='Складская бытовка 2,4×6 м',
      size='2,4 × 6 м', L=6, W=2.4, door=0.12, windows=(0.55, 0.82), double_door=True,
      desc='Склад с распашными дверями для материалов и инструмента. Цена — по запросу.'),
    V(slug='sklad-3x6', cat='sklad', name='Склад 3×6 м',
      size=disp(3, 6), L=6, W=3, door=0.12, windows=(0.55, 0.82), double_door=True,
      desc='Широкий склад-хозблок под объёмное хранение.'),
    V(slug='sklad-24x9', cat='sklad', name='Склад 2,4×9 м',
      size=disp(2.4, 9), L=9, W=2.4, door=0.1, windows=(0.4, 0.7), double_door=True,
      desc='Длинный складской модуль, можно разделить на два отсека.'),
    V(slug='sklad-24x12', cat='sklad', name='Склад 2,4×12 м',
      size=disp(2.4, 12), L=12, W=2.4, door=0.08, windows=(0.3, 0.6, 0.85),
      rooms=(0.5,), double_door=True,
      desc='Два складских отсека в корпусе 12 м.'),

    # ПОСТ ОХРАНЫ
    V(slug='guard-2x2', cat='guard', name='Пост охраны 2×2 м',
      size=disp(2, 2), L=2, W=2, door=0.22, windows=(0.55,), panoramic=True,
      desc='Компактный пост с панорамным остеклением и обзором территории.'),
    V(slug='guard-2x3', cat='guard', name='Пост охраны 2×3 м',
      size=disp(2, 3), L=3, W=2, door=0.18, windows=(0.55,), panoramic=True, canopy=True,
      desc='Пост с козырьком и широким обзором, место для одного сотрудника.'),
    V(slug='kpp-24x24', cat='guard', name='КПП 2,4×2,4 м с козырьком',
      size=disp(2.4, 2.4), L=2.4, W=2.4, door=0.2, windows=(0.58,), panoramic=True, canopy=True,
      desc='КПП с козырьком над окном выдачи и широким обзором.'),
    V(slug='guard-24x4', cat='guard', name='КПП 2,4×4 м на два рабочих места',
      size=disp(2.4, 4), L=4, W=2.4, door=0.15, windows=(0.4, 0.7), panoramic=True, canopy=True,
      desc='Два рабочих места, панорамные окна, козырёк у окна выдачи.'),
    V(slug='guard-3x3', cat='guard', name='Пост охраны 3×3 м с санузлом',
      size=disp(3, 3), L=3, W=3, door=0.18, windows=(0.45, 0.75), rooms=(0.7,), panoramic=True,
      desc='Просторный пост на одного-двух сотрудников с отдельным санузлом.'),

    # OFFICE / LIVING / SAN / MODULAR — keep useful categories
    V(slug='office-5x24', cat='office', name='Прорабская 2,4×5 м',
      size=disp(2.4, 5), L=5, W=2.4, door=0.14, windows=(0.4, 0.68, 0.88),
      desc='Кабинет прораба: стол, стеллаж, место для планерок на объекте.'),
    V(slug='office-6x24', cat='office', name='Офисный модуль 2,4×6 м, два кабинета',
      size='2,4 × 6 м', L=6, W=2.4, door=0.12, windows=(0.35, 0.55, 0.8), rooms=(0.5,),
      desc='Два кабинета в одном модуле — для офиса на стройке. Цена — по запросу.'),
    V(slug='office-3x6', cat='office', name='Офис 3×6 м с переговорной',
      size=disp(3, 6), L=6, W=3, door=0.12, windows=(0.35, 0.55, 0.8), rooms=(0.4,),
      desc='Рабочая зона и переговорная в широком модуле.'),
    V(slug='office-2mod', cat='office', name='Офис из двух блоков 6×4,8 м',
      size='6 × 4,8 м', L=6, W=4.8, door=0.12, windows=(0.35, 0.55, 0.8),
      rooms=(0.5,), modules=2, stock=False,
      desc='Два состыкованных блока: приёмная и рабочие кабинеты.'),

    V(slug='live-6x24', cat='living', name='Жильё бригады 2,4×6 м',
      size='2,4 × 6 м', L=6, W=2.4, door=0.12, windows=(0.4, 0.62, 0.84), rooms=(0.28,),
      desc='Тамбур и жилая комната, места для спальных мест бригады. Цена — по запросу.'),
    V(slug='dress-6x24', cat='living', name='Бытовка-раздевалка 2,4×6 м',
      size='2,4 × 6 м', L=6, W=2.4, door=0.12, windows=(0.38, 0.62, 0.84), benches=True,
      desc='Скамейки и крюки вдоль стен, место переодеться до и после смены.'),
    V(slug='live-3x6', cat='living', name='Жильё бригады 3×6 м, две комнаты',
      size=disp(3, 6), L=6, W=3, door=0.12, windows=(0.38, 0.58, 0.8), rooms=(0.22, 0.58),
      desc='Две жилые комнаты и тамбур — для большей бригады.'),
    V(slug='live-24x9', cat='living', name='Жильё бригады 2,4×9 м',
      size=disp(2.4, 9), L=9, W=2.4, door=0.1, windows=(0.28, 0.48, 0.68, 0.86), rooms=(0.22, 0.55),
      desc='Тамбур, раздевалка и жилая комната в одном корпусе.'),

    V(slug='san-3x24', cat='san', name='Сан-бытовка 2,4×3 м, душ и туалет',
      size=disp(2.4, 3), L=3, W=2.4, door=0.18, windows=(0.4, 0.75), rooms=(0.5,), san=True,
      desc='Душевая и туалет в одном модуле — для стройки или дачи.'),
    V(slug='san-24x4', cat='san', name='Санблок 2,4×4 м на две кабины',
      size=disp(2.4, 4), L=4, W=2.4, door=0.15, windows=(0.35, 0.6, 0.85), rooms=(0.33, 0.66), san=True,
      desc='Две сантехнические кабины и тамбур с умывальником.'),
    V(slug='san-24x6', cat='san', name='Душевая 2,4×6 м для бригады',
      size='2,4 × 6 м', L=6, W=2.4, door=0.12, windows=(0.35, 0.55, 0.78),
      rooms=(0.22, 0.45, 0.7), san=True,
      desc='Несколько душевых кабин, раздевалка и туалет для бригады. Цена — по запросу.'),
    V(slug='wc-24x24', cat='san', name='Туалетный модуль 2,4×2,4 м',
      size=disp(2.4, 2.4), L=2.4, W=2.4, door=0.22, windows=(0.7,), rooms=(0.5,), san=True,
      desc='Компактный туалетный блок на одну-две кабины.'),

    V(slug='house-6x6', cat='modular', name='Модульный дом 6×6 м',
      size='6 × 6 м', L=6, W=6, roof='pitched', porch=True, door=0.2,
      windows=(0.35, 0.7), rooms=(0.5,), modules=2, stock=False,
      desc='Дом из двух блоков под заказ: гостиная и спальня.'),
    V(slug='house-8x6', cat='modular', name='Модульный дом 8×6 м, три комнаты',
      size='8 × 6 м', L=8, W=6, roof='pitched', porch=True, door=0.18,
      windows=(0.28, 0.5, 0.75), rooms=(0.33, 0.66), modules=2, stock=False,
      desc='Три комнаты в двух блоках — под заказ, планировку согласуем.'),
    V(slug='house-9x6', cat='modular', name='Модульный дом 9×6 м из трёх блоков',
      size='9 × 6 м', L=9, W=6, roof='pitched', porch=True, door=0.15,
      windows=(0.22, 0.45, 0.7), rooms=(0.33, 0.66), modules=3, stock=False,
      desc='Три состыкованных блока, больше площади для семьи или базы.'),
    V(slug='house-6x48', cat='modular', name='Дачный модульный дом 6×4,8 м',
      size='6 × 4,8 м', L=6, W=4.8, roof='pitched', porch=True, door=0.18,
      windows=(0.35, 0.65, 0.85), rooms=(0.45,), modules=2, stock=False,
      desc='Дачный дом из двух блоков со скатной крышей — под заказ.'),
]


def href(depth, page, anchor=''):
    if page == 'home':
        u = './' if depth == 0 else '../'
    else:
        u = pth(depth, f'{page}/')
    return u + (anchor if anchor else '')


def chat_btns(extra_cls=''):
    return (
        f'<div class="chat-btns {extra_cls}">'
        f'<a class="button button--fill" href="{WA}" target="_blank" rel="noopener">Написать в WhatsApp</a>'
        f'<a class="button" href="{TG}" target="_blank" rel="noopener">Написать в Telegram</a>'
        f'<a class="button button--ink" href="{TEL}">Позвонить</a>'
        f'</div>'
    )


def sprite_svg():
    t = (ROOT / 'index.html').read_text(encoding='utf-8') if (ROOT / 'index.html').exists() else ''
    m = re.search(r'<svg class="sprite".*?</svg>', t, flags=re.S)
    if m:
        return m.group(0)
    # fallback: read saved
    p = Path('/tmp/sibnord_build/sprite.svg')
    return p.read_text() if p.exists() else ''


def head(title, desc, depth, canonical, og_extra=''):
    p = pth(depth, '')
    can = 'https://alexautoperfomance-ctrl.github.io/sibnordmodul-site/' + ('' if canonical == 'index.html' else canonical)
    return f'''<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8"/>
<meta content="width=device-width,initial-scale=1,viewport-fit=cover" name="viewport"/>
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}"/>
<meta name="theme-color" content="#2A2E33"/>
<link rel="canonical" href="{esc(can)}"/>
<meta property="og:title" content="{esc(title)}"/>
<meta property="og:description" content="{esc(desc)}"/>
<meta property="og:type" content="website"/>
<meta property="og:image" content="{p}images/hero-latin.jpg"/>
<link rel="icon" href="{p}favicon.ico" sizes="any"/>
<link rel="icon" href="{p}favicon.png" type="image/png"/>
<link rel="stylesheet" href="{p}styles.css"/>
</head><body>'''


def site_chrome(depth, active):
    p = pth(depth, '')
    sp = sprite_svg()
    # ensure class sprite
    if 'class="sprite"' not in sp and sp.startswith('<svg'):
        sp = sp.replace('<svg', '<svg class="sprite"', 1)
    nav = []
    for key, title in PAGES:
        cls = ' class="is-active"' if key == active else ''
        nav.append(f'<a href="{href(depth, key)}"{cls}>{esc(title)}</a>')
    nav_html = ''.join(nav)
    top = f'''
{sp}
<div class="top-line"><div class="container top-line__inner">
<nav class="menu-top">{nav_html}</nav>
</div></div>
<header class="header"><div class="container header__inner">
<a class="logo" href="{href(depth,'home')}" aria-label="SibNordModul — на главную">
<img alt="SibNordModul" height="64" src="{p}images/logo-latin.svg" width="279"/>
</a>
<div class="header__local">
<p><svg aria-hidden="true" class="icon"><use href="#i-pin"></use></svg> Новосибирск</p>
<div class="phones">
<a class="phone" href="{TEL}"><svg aria-hidden="true" class="icon"><use href="#i-phone"></use></svg>{PHONE_DISP}</a>
<a class="phone" href="{LANDLINE_TEL}">{LANDLINE_DISP}</a>
</div>
</div>
<div class="header__note"><strong>Собственное производство</strong>Бытовки, модульные дома, северные модули</div>
<div class="header__actions">
<div class="header__chats">
<a class="button button--fill" href="{WA}" target="_blank" rel="noopener">WhatsApp</a>
<a class="button" href="{TG}" target="_blank" rel="noopener">Telegram</a>
</div>
<a class="header__mail" href="{MAIL}">{MAIL_DISP}</a>
</div></div></header>
<nav aria-label="Разделы сайта" class="category-nav"><div class="container category-nav__inner">
{nav_html}
</div></nav>
'''
    return top


def footer(depth):
    p = pth(depth, '')
    links_co = ''.join(
        f'<li><a href="{href(depth,k)}">{esc(t)}</a></li>' for k, t in PAGES
    )
    return f'''
<footer class="footer"><div class="container footer__grid">
<div class="footer__intro">
<a aria-label="SibNordModul — на главную" class="logo" href="{href(depth,'home')}">
<img alt="SibNordModul" height="64" src="{p}images/logo-latin-light.svg" width="279"/></a>
<p>Собственное производство бытовок, модульных домов и северных модулей из сэндвич-панелей в Новосибирске.</p>
</div>
<div class="footer__nav"><h3>Разделы</h3><ul>{links_co}</ul></div>
<div class="footer__catalog"><h3>Каталог</h3><ul>
<li><a href="{href(depth,'catalog')}#cat-universal">Бытовка универсальная</a></li>
<li><a href="{href(depth,'catalog')}#cat-stroitelnye">Строительная</a></li>
<li><a href="{href(depth,'catalog')}#cat-dachnye">Дачная</a></li>
<li><a href="{href(depth,'catalog')}#cat-sklad">Складская</a></li>
<li><a href="{href(depth,'catalog')}#cat-guard">Пост охраны</a></li>
<li><a href="{href(depth,'catalog')}#cat-pavilions">Павильоны</a></li>
</ul></div>
<div class="footer__contact">
<p>{esc(ADDR)}</p>
<div class="phones">
<a class="phone" href="{TEL}">{PHONE_DISP}</a>
<a class="phone" href="{LANDLINE_TEL}">{LANDLINE_DISP}</a>
</div>
<a class="mail" href="{MAIL}">{MAIL_DISP}</a>
<div class="footer-chats">
<a class="button button--white" href="{WA}" target="_blank" rel="noopener">WhatsApp</a>
<a class="button button--white" href="{TG}" target="_blank" rel="noopener">Telegram</a>
</div>
</div></div>
<div class="footer__bottom"><div class="container">
<span>© <span data-year="">2026</span> SibNordModul</span>
<button data-privacy="" type="button">О данных в форме</button>
<span>Производство · Продажа · Аренда</span>
</div></div></footer>
<nav aria-label="Быстрые действия" class="mobile-dock">
<button aria-controls="menu-drawer" aria-haspopup="dialog" aria-label="Открыть меню" id="open-menu" type="button">
<svg aria-hidden="true" class="icon"><use href="#i-menu"></use></svg><span>Меню</span></button>
<a href="{href(depth,'catalog')}"><svg aria-hidden="true" class="icon"><use href="#i-cabin"></use></svg><span>Каталог</span></a>
<a href="{WA}" rel="noopener" target="_blank"><svg aria-hidden="true" class="icon"><use href="#i-chat"></use></svg><span>WhatsApp</span></a>
<a href="{TG}" rel="noopener" target="_blank"><svg aria-hidden="true" class="icon"><use href="#i-telegram"></use></svg><span>Telegram</span></a>
<a href="{TEL}"><svg aria-hidden="true" class="icon"><use href="#i-phone"></use></svg><span>Позвонить</span></a>
</nav>
<dialog aria-labelledby="drawer-title" class="drawer" id="menu-drawer">
<div class="drawer__top"><span id="drawer-title">SibNordModul</span>
<button class="close-btn" aria-label="Закрыть меню" data-close="" type="button"><svg aria-hidden="true" class="icon"><use href="#i-close"></use></svg></button></div>
<nav>{''.join(f'<a href="{href(depth,k)}">{esc(t)}</a>' for k,t in PAGES)}</nav>
<div class="drawer__contact">
<div class="phones">
<a class="phone" href="{TEL}">{PHONE_DISP}</a>
<a class="phone" href="{LANDLINE_TEL}">{LANDLINE_DISP}</a>
</div>
<a class="mail" href="{MAIL}">{MAIL_DISP}</a>
<a class="button button--fill" href="{WA}" target="_blank" rel="noopener">WhatsApp</a>
<a class="button" href="{TG}" target="_blank" rel="noopener">Telegram</a>
</div></dialog>
<dialog aria-labelledby="photo-title" class="modal photo-modal" id="photo-modal">
<div class="modal__head"><h2 id="photo-title">Фото</h2>
<button class="close-btn" aria-label="Закрыть" data-close="" type="button"><svg aria-hidden="true" class="icon"><use href="#i-close"></use></svg></button></div>
<div class="photo-modal__frame">
<button class="photo-arrow prev" type="button" aria-label="Назад">‹</button>
<img alt="" id="lightbox-image"/>
<button class="photo-arrow next" type="button" aria-label="Вперёд">›</button>
</div>
<div class="photo-counter"></div>
</dialog>
<dialog aria-labelledby="privacy-title" class="modal" id="privacy-modal">
<div class="modal__head"><h2 id="privacy-title">О данных в форме</h2>
<button class="close-btn" aria-label="Закрыть" data-close="" type="button"><svg aria-hidden="true" class="icon"><use href="#i-close"></use></svg></button></div>
<div class="modal__body privacy-text">
<p>Этот сайт не отправляет и не сохраняет данные формы на сервере. Имя, телефон и выбранный вариант используются в вашем браузере, чтобы подготовить сообщение.</p>
<p>При нажатии кнопки откроется WhatsApp или почтовая программа. Данные будут переданы выбранному сервису в тексте черновика только после вашего подтверждения.</p>
</div></dialog>
<script src="{pth(depth,'script.js')}"></script>
</body></html>
'''


def wrap(title, desc, depth, active, canonical, body, og=''):
    return head(title, desc, depth, canonical, og) + site_chrome(depth, active) + f'<main>{body}</main>' + footer(depth)


def page_home():
    cards = [
        ('catalog', 'Каталог бытовок', 'Схемы типовых размеров: универсальные, строительные, дачные, складские, посты охраны и другие решения.'),
        ('rent', 'Аренда бытовок', f'Аренда от 8 000 ₽ в месяц. Оплата наличными или по безналу, с НДС и без НДС.'),
        ('custom', 'Другие решения под заказ', 'Модульные и северные дома из сэндвич-панелей, офисы, КПП, санблоки, любые размеры и планировки.'),
        ('about', 'О компании', 'Своё производство в Новосибирске. Доставка примерно до 1000 км.'),
        ('gallery', 'Фотогалерея', 'Реальные фото наших бытовок и производства.'),
        ('contacts', 'Контакты', 'Телефон, WhatsApp, Telegram, почта и адрес в Пашино. Как добраться.'),
    ]
    items = []
    for key, title, text in cards:
        items.append(
            f'<a class="home-card" href="{href(0,key)}"><h3>{esc(title)}</h3><p>{esc(text)}</p><span>Перейти ›</span></a>'
        )
    return f'''
<section class="hero">
<div class="container hero__inner">
<div class="hero__copy">
<div class="hero__kicker">Производство · продажа · аренда</div>
<h1 id="hero-title">Строительные бытовки <br/>от производителя</h1>
<p>Готовые варианты и изготовление на заказ. Новосибирск и доставка по Сибири.</p>
<p class="hero-price"><strong>Утеплённая бытовка 2,4 × 6 м — {PRICE}</strong>
<span class="hero-price-note">{esc(PRICE_NOTE)}</span></p>
<div class="hero-chats">
<a class="button button--fill" href="{WA}" target="_blank" rel="noopener">Написать в WhatsApp</a>
<a class="button button--ink" href="{TG}" target="_blank" rel="noopener">Написать в Telegram</a>
<a class="button" href="{href(0,'catalog')}">Смотреть каталог ›</a>
</div>
</div>
<div class="hero__visual">
<picture>
<source media="(max-width:767px)" srcset="images/hero-latin-m.webp" type="image/webp"/>
<source srcset="images/hero-latin.webp" type="image/webp"/>
<img alt="Бытовка SibNordModul в графитово-оранжевом оформлении" fetchpriority="high" height="720" src="images/hero-latin.jpg" width="1280"/>
</picture>
<span class="hero__stock">В наличии разные варианты — ждать не нужно</span>
</div>
</div>
</section>
<section class="home-intro">
<div class="container">
<h2>SibNordModul — своё производство в Новосибирске</h2>
<p>Изготавливаем, продаём и сдаём в аренду бытовки для стройки, жилья бригады, прорабской, офиса, дачи и склада. Кроме серийных модулей делаем модульные дома, северные бытовки из сэндвич-панелей и любые нестандартные решения под задачу.</p>
<div class="home-cards">{''.join(items)}</div>
</div>
</section>
'''




# Photo-only «Павильоны» tiles: no sizes, no prices.
# To add more later, put 02.jpg, 03.jpg… into images/pavilions/ and append entries here.
PAVILIONS = [
    {
        'file': '01.jpg',
        'title': 'Павильон — вариант 1',
        'desc': 'С остеклением и деревянными ламелями',
        'alt': 'Павильон с остеклением и деревянными ламелями',
        'w': 1536,
        'h': 1024,
    },
]


def pavilion_img(depth, filename):
    return pth(depth, f'images/pavilions/{filename}')


def pavilion_tile(v, depth=1):
    src = pavilion_img(depth, v['file'])
    search = ' '.join((v['title'], v['desc'])).lower()
    return (
        f'<article class="scheme-tile product" data-cat="pavilions" data-search="{esc(search)}">'
        f'<div class="product-box">'
        f'<a class="product__image product__image--photo scheme-link" href="{src}" data-gallery="pavilions" data-title="{esc(v["title"])}" aria-label="{esc(v["title"])}">'
        f'<img src="{src}" alt="{esc(v["alt"])}" width="{v["w"]}" height="{v["h"]}" loading="lazy" decoding="async"/></a>'
        f'<h3>{esc(v["title"])}</h3>'
        f'<p class="scheme-desc">{esc(v["desc"])}</p>'
        f'<div class="product__footer">'
        f'<a class="button button--fill" href="{wa_link(v["title"])}" target="_blank" rel="noopener">Написать</a>'
        f'</div>'
        f'</div></article>'
    )


def cat_counts():
    c = {k: 0 for k, _ in CATS}
    for v in VARIANTS:
        c[v['cat']] += 1
        c['all'] += 1
    for v in PAVILIONS:
        c['pavilions'] += 1
        c['all'] += 1
    return c


def main_desc_html():
    def items(*rows):
        return '<ul>' + ''.join(f'<li>{esc(r)}</li>' for r in rows) + '</ul>'
    uses = items('Строительная бытовка','Жильё для рабочих и бригады','Прорабская или офис на объекте','Дачный домик','Складское помещение','И другие хозяйственные нужды')
    ext = items('Стены — профлист С8, цвет графит RAL 7024','Крыша — профлист С20, цвет RAL 7024','Металлическая входная дверь','Открывающиеся окна 1000 × 1200 мм')
    frame = items('Швеллер 100 × 45 (5/7,9)','Уголок 63 × 63 мм, толщина 5 мм','Профильная труба 40 × 40 мм, стенка 3 мм','Усиленные укосины из листового металла 4 мм')
    insul = items('Деревянный каркас — доска 50 × 100 мм','Обрешётка — доска 25 × 100 мм','Утеплитель — 100 мм','Ветрозащита и пароизоляция','Стены — ОСБ 9 мм','Пол — ОСБ 15 мм')
    el = items('Розетки и выключатель','Осветительные приборы','Электрический щиток','Закладная под ввод электричества')
    pay = items('Сдаём бытовки в аренду — стоимость договорная.','Продажа бытовок из наличия.','Оплата наличными или безналичным расчётом.','Работаем с НДС и без НДС.')
    # No «Дополнительная комплектация» block — moved to custom page by request
    return f'''
<section class="model-card content-section" id="model-6x24">
  <div class="model-heading">
    <h2>Утеплённая бытовка 2,4×6 — аренда и продажа</h2>
    <p class="model-price">{PRICE}</p>
  </div>
  <p>Собственное производство! Изготавливаем, продаём и сдаём в аренду утеплённые бытовки. Различные варианты уже в наличии — ждать изготовления не нужно!</p>
  <div class="model-uses"><h3>Для чего подойдёт?</h3>{uses}</div>
  <p class="spec-kicker">Комплектация бытовки (как на фото)</p>
  <div class="specs">
    <article class="spec"><h3><svg aria-hidden="true" class="icon"><use href="#i-cabin"></use></svg>Наружная отделка</h3>{ext}</article>
    <article class="spec"><h3><svg aria-hidden="true" class="icon"><use href="#i-frame"></use></svg>Металлический каркас основания</h3>{frame}</article>
    <article class="spec"><h3><svg aria-hidden="true" class="icon"><use href="#i-layers"></use></svg>Утепление и внутренняя конструкция</h3>{insul}</article>
    <article class="spec"><h3><svg aria-hidden="true" class="icon"><use href="#i-bolt"></use></svg>Электрика</h3>{el}</article>
  </div>
  <div class="model-payments">
    <p><strong>Стоимость {PRICE}.</strong> {esc(PRICE_NOTE)}</p>
    <a class="button button--fill" href="{wa_link('Утеплённая бытовка 2,4×6 м, 245 000 ₽')}" target="_blank" rel="noopener">Написать в WhatsApp</a>
    <a class="button" href="{TG}" target="_blank" rel="noopener">Написать в Telegram</a>
  </div>
  <div class="pay-lite"><h3>Аренда и условия оплаты</h3>{pay}</div>
  <p>Есть вопросы? Пишите и звоните! Поможем подобрать подходящую комплектацию. Рассчитаем стоимость под ваши задачи. Возможность изготовления под заказ. Собственное производство — контроль качества на каждом этапе!</p>
</section>
'''


def page_catalog():
    counts = cat_counts()
    side = ['<aside class="cat-side" aria-label="Категории каталога" id="cats">',
            '<h3>Категории</h3>', '<div class="cat-cats" role="tablist">']
    for key, title in CATS:
        on = ' on' if key == 'all' else ''
        pressed = 'true' if key == 'all' else 'false'
        side.append(
            f'<button type="button" class="cat-cat{on}" id="cat-{key}" data-filter="{key}" aria-pressed="{pressed}">'
            f'<span>{esc(title)}</span><i>{counts[key]}</i></button>'
        )
    side += ['</div>',
             f'<div class="cat-side-note">Не нашли нужный размер? Напишем расчёт и изготовим под задачу.'
             f'<a class="button" href="{TG}" target="_blank" rel="noopener">Telegram</a></div>',
             '</aside>']
    tiles = []
    for v in VARIANTS:
        price_html = (f'<span class="product__price">{PRICE}</span>' if v.get('priced')
                      else '<span class="product__price product__price--request">Цена по запросу</span>')
        sticker = 'В наличии' if v.get('stock') else 'Под заказ'
        sticker_cls = 'sticker' if v.get('stock') else 'sticker sticker--soft'
        href_s = f'../images/schemes/{v["slug"]}.svg'
        more = '<a class="button button--ink" href="#model-6x24">Подробнее</a>' if v.get('priced') else ''
        tiles.append(
            f'<article class="scheme-tile product" data-cat="{v["cat"]}" data-search="{esc((v["name"]+" "+v["size"]+" "+v["desc"]).lower())}">'
            f'<div class="product-box">'
            f'<span class="{sticker_cls}">{sticker}</span>'
            f'<a class="product__image scheme-link" href="{href_s}" data-gallery="schemes" data-title="{esc(v["name"])}" aria-label="Схема: {esc(v["name"])}">'
            f'<img src="{href_s}" alt="Схема: {esc(v["name"])}" width="800" height="540" loading="lazy"/></a>'
            f'<h3>{esc(v["name"])}</h3>'
            f'<p class="product__size">{esc(v["size"])}</p>'
            f'<p class="scheme-desc">{esc(v["desc"])}</p>'
            f'<div class="product__footer">{price_html}'
            f'<a class="button button--fill" href="{wa_link(v["name"]+", "+v["size"])}" target="_blank" rel="noopener">Написать</a>'
            f'{more}</div>'
            f'<p class="product__status">{"Продажа и аренда" if v.get("stock") else "Изготовление на заказ"}</p>'
            f'</div></article>'
        )
    for pv in PAVILIONS:
        tiles.append(pavilion_tile(pv, 1))
    return f'''
<section class="page-hero"><div class="container">
<h1>Каталог бытовок</h1>
<p class="catalog-intro">Выберите категорию слева и размер на схемах. Утеплённая бытовка 2,4 × 6 м в комплектации как на фотографиях — <strong>{PRICE}</strong>. Остальные размеры и исполнения — цена по запросу. В наличии разные варианты — ждать не нужно.</p>
<p class="real-note">{esc(PRICE_NOTE)}</p>
</div></section>
<div class="container cat-page">
<div class="cat-layout">{''.join(side)}
<div class="cat-main">
<div class="scheme-grid" id="scheme-grid">{''.join(tiles)}</div>
<p class="empty-results" hidden>В этой категории пока ничего не нашлось. Выберите другую или напишите нам.</p>
{main_desc_html()}
</div></div></div>
'''


def page_rent():
    return f'''
<section class="page-hero"><div class="container narrow">
<h1>Аренда бытовок</h1>
<p class="lead">Сдаём бытовки в аренду — <strong>от 8 000 ₽ в месяц</strong>. Звоните или пишите, подберём вариант под срок и задачу.</p>
<ul class="plain-list">
<li>Аренда бытовок от 8 000 ₽/мес.</li>
<li>Оплата наличными или безналичным расчётом.</li>
<li>Работаем с НДС и без НДС.</li>
<li>Стоимость конкретной позиции и срока — договорная, уточняйте при обращении.</li>
</ul>
{chat_btns()}
<p class="subtle" style="margin-top:18px">Телефон <a href="{TEL}">{PHONE_DISP}</a>, <a href="{LANDLINE_TEL}">{LANDLINE_DISP}</a> · <a href="{MAIL}">{MAIL_DISP}</a></p>
</div></section>
'''


def page_custom():
    blocks = [
        ('Модульные дома', 'Собираем жилые и дачные дома из отдельных блоков. Можно начать с двух модулей и потом добавить третий. Планировку, число комнат, крыльцо и крышу согласуем до запуска в работу.'),
        ('Северные бытовки из сэндвич-панелей', 'Для холодного климата делаем утеплённые модули из сэндвич-панелей. Это другой контур, чем у серийной бытовки 2,4×6: толщина, узлы и комплектация считаются отдельно под регион и задачу.'),
        ('Офисы и прорабские', 'Кабинет на объекте, офис из двух блоков, приёмная и переговорная. Разводка розеток, освещение, подготовка под отопление — по вашему заданию.'),
        ('Раздевалки и жильё бригады', 'Модули со скамейками, сушилкой, тамбуром и спальными местами. Можно совместить раздевалку, комнату отдыха и сушилку в одном корпусе или в сдвоенном модуле.'),
        ('КПП и посты охраны', 'Посты с панорамным остеклением, козырьком, окном выдачи, одним или двумя рабочими местами, при необходимости — с санузлом.'),
        ('Санитарные блоки и совмещённые модули', 'Душ, туалет, умывальник, несколько кабин, раздевалка при душевой. Также делаем комбинированные решения: бытовка + санблок, офис + склад, пост + хозблок.'),
        ('Любой размер и планировка', 'Кроме типовых 2,4×4, 2,4×6, 2,4×7, 3×6, 2,4×9 и 2,4×12 м изготовим нестандартную длину, ширину, тамбур, перегородки и расстановку окон и дверей.'),
        ('Отопление, тёплый пол, отделка и сантехника', 'По желанию ставим или готовим отопление, тёплый пол, другую внутреннюю отделку, утеплитель другой толщины, сантехнику и дополнительное оборудование. Стоимость опций рассчитывается индивидуально.'),
    ]
    arts = ''.join(
        f'<article class="custom-card"><h3>{esc(t)}</h3><p>{esc(p)}</p></article>'
        for t, p in blocks
    )
    steps = [
        ('Расскажите задачу', 'Напишите или позвоните: что нужно, размер, регион, срок. Если есть схема или список помещений — пришлите, так быстрее посчитаем.'),
        ('Согласуем решение', 'Предложим планировку, комплектацию и срок. Для нестандартных модулей и северных бытовок из сэндвич-панелей расчёт делаем отдельно.'),
        ('Запускаем в работу', 'После подтверждения изготавливаем на своём производстве в Новосибирске и держим в курсе готовности.'),
        ('Отгрузка и доставка', 'Договоримся о самовывозе или доставке примерно до 1000 км: НСО, Алтайский край, Республика Алтай, Кемеровская, Томская, Омская области, Красноярский край, Хакасия.'),
    ]
    st = ''.join(
        f'<article class="step"><h3>{esc(t)}</h3><p>{esc(p)}</p></article>'
        for t, p in steps
    )
    return f'''
<section class="page-hero"><div class="container">
<h1>Другие решения под заказ</h1>
<p class="lead">Изготавливаем не только серийные бытовки. Если нужен модульный дом, северная бытовка из сэндвич-панелей, офис, раздевалка, КПП, санблок или совмещённый модуль — сделаем под вашу задачу. Любой размер, планировка и комплектация.</p>
</div></section>
<section class="content-section"><div class="container">
<div class="custom-grid">{arts}</div>
</div></section>
<section class="content-section soft-band"><div class="container">
<h2>Как заказать нестандартное решение</h2>
<div class="steps">{st}</div>
<div class="cta-band">
<p>Опишите задачу — рассчитаем стоимость и срок. Цена серийной утеплённой бытовки 2,4 × 6 м — {PRICE}; остальные решения считаются отдельно.</p>
{chat_btns()}
</div>
</div></section>
'''


def page_about():
    opts = [
        ('Электрика и освещение', [
            'Разводка электрики под задачу',
            'Освещение помещений',
            'Розетки и выключатели',
            'Электрический щиток',
            'Закладная под ввод электричества',
        ]),
        ('Внутренняя отделка', [
            'Вагонка',
            'МДФ- и ПВХ-панели',
            'ОСБ',
            'Гипсокартон',
            'Линолеум',
        ]),
        ('Отопление и климат', [
            'Конвекторы',
            'Тепловая пушка',
            'Печь',
            'Тёплый пол',
            'Кондиционер',
        ]),
        ('Утепление', [
            'Разные виды утеплителя',
            'Разная толщина теплового контура',
            'Ветрозащита и пароизоляция',
        ]),
        ('Окна, двери и защита', [
            'Дополнительные окна',
            'Дополнительные двери',
            'Решётки на окна',
            'Рольставни',
        ]),
        ('Планировка', [
            'Перегородки',
            'Тамбур',
            'Нестандартные размеры и раскладка помещений',
        ]),
        ('Сантехника', [
            'Туалет',
            'Душ',
            'Умывальник и разводка воды',
        ]),
        ('Мебель и оснащение', [
            'Кровати',
            'Шкафчики и стеллажи',
            'Другое оборудование по заданию',
        ]),
        ('Снаружи и шасси', [
            'Крыльцо и навес',
            'Покраска каркаса',
            'Сани-полозья',
            'Любой цвет профлиста по RAL или оцинковка',
        ]),
    ]
    opt_html = ''.join(
        f'<article class="opt-group"><h3>{esc(t)}</h3><ul>' +
        ''.join(f'<li>{esc(i)}</li>' for i in items) +
        '</ul></article>'
        for t, items in opts
    )
    uses = [
        ('Строительные бытовки', 'Для смены, инструмента и быта на площадке.'),
        ('Жильё бригады и раздевалки', 'Чтобы переодеться, отдохнуть и переночевать без лишних построек на объекте.'),
        ('Прорабские и офисы', 'Кабинет, переговорная или офис из одного или нескольких блоков.'),
        ('Дачные и хозяйственные модули', 'Для участка, хранения и сезонного проживания.'),
        ('Склады и хозблоки', 'Под материалы, инвентарь и оборудование.'),
        ('Посты охраны и КПП', 'С обзором, козырьком и нужной начинкой.'),
        ('Санитарные блоки', 'Душ, туалет, умывальник — отдельно или в составе модуля.'),
        ('Модульные дома и северные бытовки', 'Жилые блоки и конструкции из сэндвич-панелей под задачу и климат.'),
    ]
    use_html = ''.join(
        f'<article class="about-card"><h3>{esc(t)}</h3><p>{esc(p)}</p></article>'
        for t, p in uses
    )
    return f"""
<section class="page-hero about-hero"><div class="container">
<p class="hero__kicker">Производство в Новосибирске</p>
<h1>О компании</h1>
<p class="lead">SibNordModul — собственное производство металлических строительных бытовок, утеплённых модулей, северных бытовок из сэндвич-панелей и модульных домов. Изготавливаем, продаём и сдаём в аренду. Размер, планировку и комплектацию собираем под вашу задачу.</p>
</div></section>

<section class="content-section"><div class="container">
<div class="about-intro text-content">
<p>Мы сами варим каркас, утепляем, обшиваем и комплектуем модули на своей площадке в Новосибирске. Без перепродавца: видно, из чего сделана конструкция, и можно заказать и типовой вариант из наличия, и нестандартный — с нужной раскладкой комнат, цветом и дооснащением.</p>
<p>Бытовки идут на стройку, в жильё бригады, в прорабскую и офис на объекте, на дачу, под склад и хозяйственные нужды. Если нужен другой тепловой контур — делаем северные бытовки из сэндвич-панелей. Если площади одного блока мало — собираем модульный дом или сдвоенный модуль.</p>
<p>В наличии разные варианты — ждать изготовления не обязательно. Под заказ берём любой размер и планировку.</p>
</div>
<div class="about-use-grid">{use_html}</div>
</div></section>

<section class="content-section soft-band"><div class="container">
<h2>Как мы производим</h2>
<p class="section-note">Ниже — наши обычные производственные решения. По заданию можем изменить материалы, толщины и узлы.</p>
<div class="std-grid">
<article class="std-card">
<h3><svg aria-hidden="true" class="icon"><use href="#i-frame"></use></svg>Металлический каркас</h3>
<p>Несущая основа — сварной стальной каркас. В типовой сборке используем швеллер 100 × 45, уголок 63 × 63 мм толщиной 5 мм, профильную трубу 40 × 40 мм со стенкой 3 мм и усиленные укосины из листового металла 4 мм. По желанию каркас окрашиваем.</p>
</article>
<article class="std-card">
<h3><svg aria-hidden="true" class="icon"><use href="#i-cabin"></use></svg>Наружная отделка</h3>
<p>Стены — профлист С8, кровля — профлист С20. Цвет листа выбираете по каталогу RAL, возможен и оцинкованный вариант без цветного покрытия. Ставим металлическую входную дверь и открывающиеся окна. Можно добавить окна, двери, решётки, рольставни, крыльцо или навес.</p>
</article>
<article class="std-card">
<h3><svg aria-hidden="true" class="icon"><use href="#i-layers"></use></svg>Утепление и внутренний контур</h3>
<p>Внутри — деревянный каркас из доски 50 × 100 мм, обрешётка 25 × 100 мм, утеплитель, ветрозащита и пароизоляция. В базовой сборке утеплитель 100 мм, стены — ОСБ 9 мм, пол — ОСБ 15 мм. Вид и толщину утеплителя, а также внутреннюю обшивку подберём отдельно.</p>
</article>
<article class="std-card">
<h3><svg aria-hidden="true" class="icon"><use href="#i-bolt"></use></svg>Электрика</h3>
<p>В стандарт закладываем розетки и выключатель, освещение, электрический щиток и закладную под ввод. Схему, число точек и освещённость можно расширить под помещение.</p>
</article>
</div>
</div></section>

<section class="content-section" id="options"><div class="container">
<h2>Докомплектация</h2>
<p class="section-note">Можем изготовить модуль с любой из этих опций — по отдельности или в наборе. Состав и стоимость дооснащения считаем индивидуально.</p>
<div class="opt-grid">{opt_html}</div>
</div></section>

<section class="content-section soft-band"><div class="container about-bottom">
<div class="about-col">
<h2>Доставка</h2>
<p>Доставляем примерно до 1000 км от Новосибирска: Новосибирская область, Алтайский край, Республика Алтай, Кемеровская, Томская и Омская области, Красноярский край, Хакасия. Способ, срок и условия перевозки обсуждаем при заказе.</p>
</div>
<div class="about-col">
<h2>Продажа, аренда и оплата</h2>
<p>Продаём готовые модули из наличия и изготавливаем под заказ. Сдаём бытовки в аренду — условия и срок договорные. Оплата наличными или безналичным расчётом, работаем с НДС и без НДС.</p>
</div>
</div>
<div class="container">
<div class="cta-band">
<p>Расскажите задачу — подскажем конструкцию, комплектацию и срок. Производим сами и проверяем сборку на каждом этапе, от каркаса до отделки.</p>
{chat_btns()}
<p class="subtle">Телефон <a href="{TEL}">{PHONE_DISP}</a>, <a href="{LANDLINE_TEL}">{LANDLINE_DISP}</a> · <a href="{MAIL}">{MAIL_DISP}</a> · {esc(ADDR)}</p>
</div>
</div></section>
"""

def page_gallery(photos):
    if not photos:
        body = ('<p class="lead">Реальные фото наших бытовок и производства появятся на этой странице. '
                'Пока можно посмотреть схемы в каталоге или написать нам.</p>'
                + chat_btns())
    else:
        tiles = []
        for ph in photos:
            cap = f'<span class="real-cap">{esc(ph["cap"])}</span>' if ph['cap'] else ''
            tiles.append(
                f'<a class="gallery-item" href="../images/real/{ph["stem"]}.jpg" data-gallery="photos" data-title="{esc(ph["cap"] or ph["alt"])}">'
                f'<picture><source srcset="../images/real/{ph["stem"]}.webp" type="image/webp"/>'
                f'<img src="../images/real/{ph["stem"]}.jpg" alt="{esc(ph["alt"])}" width="{ph["w"]}" height="{ph["h"]}" loading="lazy" decoding="async"/></picture>{cap}</a>'
            )
        body = (
            f'<p class="lead">Реальные фото утеплённой бытовки 2,4 × 6 м и этапов производства. Стоимость этой бытовки в показанной комплектации — <strong>{PRICE}</strong>.</p>'
            f'<p class="real-note">{esc(PRICE_NOTE)}</p>'
            f'<div class="gallery-page-grid">{"".join(tiles)}</div>'
        )
    return f'''
<section class="page-hero"><div class="container">
<h1>Фотогалерея</h1>
{body}
</div></section>
'''


def page_contacts():
    return f'''
<section class="page-hero"><div class="container">
<h1>Контакты</h1>
<p class="lead">Позвоните или напишите — ответим, подберём вариант и посчитаем доставку.</p>
</div></section>
<section class="content-section"><div class="container contacts-page">
<div class="contacts-actions">
<a class="contact-btn" href="{TEL}"><svg aria-hidden="true" class="icon"><use href="#i-phone"></use></svg><span>Телефон</span><b>{PHONE_DISP}</b></a>
<a class="contact-btn" href="{LANDLINE_TEL}"><svg aria-hidden="true" class="icon"><use href="#i-phone"></use></svg><span>Городской</span><b>{LANDLINE_DISP}</b></a>
<a class="contact-btn" href="{WA}" target="_blank" rel="noopener"><svg aria-hidden="true" class="icon"><use href="#i-chat"></use></svg><span>WhatsApp</span><b>Написать в WhatsApp</b></a>
<a class="contact-btn" href="{TG}" target="_blank" rel="noopener"><svg aria-hidden="true" class="icon"><use href="#i-telegram"></use></svg><span>Telegram</span><b>Написать в Telegram</b></a>
<a class="contact-btn" href="{MAIL}"><svg aria-hidden="true" class="icon"><use href="#i-mail"></use></svg><span>Почта</span><b>{MAIL_DISP}</b></a>
</div>
<div class="contacts-map-block">
<p class="contacts-addr"><svg aria-hidden="true" class="icon"><use href="#i-pin"></use></svg> {esc(ADDR)}</p>
<div class="map-btns">
<a class="button button--fill" href="{GIS_OPEN}" rel="noopener" target="_blank">Открыть в 2ГИС</a>
<a class="button" href="{GIS_DIR}" rel="noopener" target="_blank">Как добраться / построить маршрут</a>
</div>
<div class="map-embed" id="map-2gis" role="region" aria-label="Карта 2ГИС">
<div id="dg-map" style="width:100%;height:380px"></div>
</div>
<p class="contacts-price">Утеплённая бытовка 2,4 × 6 м — <strong>{PRICE}</strong>. {esc(PRICE_NOTE)}</p>
</div>
</div></section>
<script src="https://maps.api.2gis.ru/2.0/loader.js?pkg=full"></script>
<script>
(function(){{
  var done=false;
  function fallback(){{
    if(done) return;
    done=true;
    var el=document.getElementById('dg-map');
    if(!el) return;
    el.innerHTML='<iframe title="SibNordModul на карте" src="https://www.openstreetmap.org/export/embed.html?bbox=82.957659%2C55.151774%2C82.977659%2C55.171774&amp;layer=mapnik&amp;marker=55.161774%2C82.967659" style="width:100%;height:380px;border:0" loading="lazy"></iframe>';
  }}
  setTimeout(fallback, 4000);
  try {{
    if(window.DG && DG.then){{
      DG.then(function(){{
        done=true;
        var map=DG.map('dg-map', {{center: [{LAT}, {LON}], zoom: 16}});
        DG.marker([{LAT}, {LON}]).addTo(map).bindPopup('SibNordModul, Томская улица, 1');
      }});
    }}
  }} catch(e){{ fallback(); }}
}})();
</script>
'''


CSS_ADD = r'''
/* ===== Multi-page layout ===== */
.logo>img{width:auto;height:56px;max-width:260px;object-fit:contain}
.footer .logo>img{height:52px}
.category-nav__inner{flex-wrap:wrap;gap:0 22px}
.category-nav a{font-size:14px}
.category-nav a.is-active,.menu-top a.is-active{color:#ffc394}
.category-nav a.is-active{color:#ffb879}
.footer-chats{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
.home-intro{padding:40px 0 60px}
.home-intro h2{margin-bottom:12px}
.home-intro .container>p{max-width:46em;margin-bottom:28px}
.home-cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}
.home-card{display:flex;flex-direction:column;gap:8px;border:1px solid var(--line);padding:20px 18px;background:#fff;min-height:160px;transition:border-color .15s,transform .15s}
.home-card:hover{border-color:var(--accent);color:inherit;transform:translateY(-2px)}
.home-card h3{font-size:18px}
.home-card p{font-size:13px;color:#6d7378;font-weight:300;flex:1}
.home-card span{font-size:13px;color:var(--accent-dark)}
.page-hero{padding:36px 0 10px}
.page-hero h1{font-size:32px;margin-bottom:14px}
.lead{font-size:16px;max-width:46em;margin-bottom:18px}
.narrow{max-width:820px}
.plain-list{margin:0 0 22px;padding:0;list-style:none}
.plain-list li{position:relative;padding:6px 0 6px 18px}
.plain-list li::before{content:"";position:absolute;left:0;top:14px;width:6px;height:6px;border-radius:50%;background:var(--accent)}
.chat-btns{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px}
.cat-page{padding-bottom:50px}
.custom-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}
.custom-card{border:1px solid var(--line);padding:20px 18px;background:#fff}
.custom-card h3{margin-bottom:8px;font-size:18px}
.custom-card p{font-size:14px;color:#4e555b;font-weight:300}
.soft-band{background:var(--soft);padding:36px 0 48px;margin-top:10px}
.cta-band{margin-top:28px;padding:22px;border:1px solid var(--line);background:#fff}
.cta-band p{margin-bottom:14px}
.about-block{margin:22px 0}
.about-block h2{font-size:22px;margin-bottom:8px}
.contacts-page{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.1fr);gap:32px;padding-bottom:40px;align-items:start}
.contacts-actions{display:flex;flex-direction:column;gap:10px}
.contact-btn{display:flex;flex-direction:column;align-items:flex-start;gap:2px;border:1px solid var(--line);padding:14px 16px;background:#fff}
.contact-btn:hover{border-color:var(--accent);color:inherit}
.contact-btn .icon{color:var(--accent)}
.contact-btn span{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.contact-btn b{font-weight:400;font-size:16px}
.contacts-map-block .contacts-addr{display:flex;gap:6px;align-items:flex-start;margin-bottom:12px;font-size:16px}
.map-embed{margin-top:14px;border:1px solid var(--line);background:var(--soft);min-height:380px}
.map-embed iframe,.map-embed .dg-widget-link,.map-embed > div{display:block;width:100%}
.gallery-page-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin:18px 0 40px}
.gallery-item{position:relative;display:block;background:var(--soft);overflow:hidden;cursor:zoom-in}
.gallery-item img{width:100%;height:220px;object-fit:cover}
.gallery-item .real-cap{position:absolute;left:0;right:0;bottom:0;background:#1d232acc;color:#fff;font-size:12px;padding:6px 8px}
@media(max-width:991px){
  .home-cards{grid-template-columns:repeat(2,minmax(0,1fr))}
  .custom-grid,.contacts-page{grid-template-columns:1fr}
  .gallery-page-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
  .category-nav a{font-size:12px}
}
@media(max-width:767px){
  .home-cards{grid-template-columns:1fr}
  .page-hero h1{font-size:26px}
  .gallery-item img{height:160px}
  .header__chats{display:none}
}

.about-hero .lead{max-width:46em}
.about-intro{max-width:52em;margin-bottom:28px}
.about-use-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}
.about-card{border:1px solid var(--line);background:#fff;padding:18px 16px}
.about-card h3{font-size:16px;margin-bottom:6px}
.about-card p{font-size:13px;color:#5c6369;font-weight:300}
.std-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}
.std-card{background:#fff;border:1px solid var(--line);padding:20px 18px}
.std-card h3{display:flex;align-items:center;gap:8px;font-size:17px;margin-bottom:8px}
.std-card h3 .icon{width:20px;height:20px;color:var(--accent-dark)}
.std-card p{font-size:14px;color:#4e555b;font-weight:300}
.opt-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}
.opt-group{border:1px solid var(--line);background:#fff;padding:18px 16px 14px}
.opt-group h3{font-size:16px;margin-bottom:10px;padding-bottom:8px;border-bottom:1px solid var(--line)}
.opt-group ul{margin:0;padding:0;list-style:none}
.opt-group li{position:relative;padding:5px 0 5px 16px;font-size:13px;color:#4a5157;font-weight:300}
.opt-group li::before{content:"";position:absolute;left:0;top:12px;width:6px;height:6px;border-radius:50%;background:var(--accent)}
.about-bottom{display:grid;grid-template-columns:1fr 1fr;gap:28px;margin-bottom:8px}
.about-col h2{margin-bottom:10px}
.about-col p{font-size:14px;font-weight:300;color:#4e555b;max-width:38em}
@media(max-width:991px){
  .about-use-grid,.opt-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
  .about-bottom,.std-grid{grid-template-columns:1fr}
}
@media(max-width:767px){
  .about-use-grid,.opt-grid{grid-template-columns:1fr}
}
'''


def patch_css():
    css = (ROOT / 'styles.css').read_text(encoding='utf-8')
    marker = '/* ===== Multi-page layout ===== */'
    if marker in css:
        css = css.split(marker)[0].rstrip() + '\n'
    # keep previous catalog css from rebuild, just append page css
    (ROOT / 'styles.css').write_text(css + '\n' + CSS_ADD, encoding='utf-8')


def write_js():
    (ROOT / 'script.js').write_text(r'''
'use strict';
(()=>{
 const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
 const drawer=$('#menu-drawer'), photo=$('#photo-modal');
 function open(d){if(!d)return;d.showModal();document.body.style.overflow='hidden'}
 function close(d){d.close();if(!$$('dialog[open]').length)document.body.style.overflow=''}
 $$('dialog').forEach(d=>{d.addEventListener('cancel',()=>{document.body.style.overflow=''});d.addEventListener('click',e=>{if(e.target.closest('[data-close]'))close(d);if(e.target===d){const r=d.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)close(d)}})});
 const om=$('#open-menu'); if(om) om.addEventListener('click',()=>open(drawer));
 if(drawer) $$('nav a',drawer).forEach(a=>a.addEventListener('click',()=>close(drawer)));
 $$('[data-privacy]').forEach(b=>b.addEventListener('click',()=>open($('#privacy-modal'))));
 $$('[data-year]').forEach(e=>e.textContent=new Date().getFullYear());

 const filters=$$('[data-filter]'), tiles=$$('.scheme-tile');
 let active='all', query='';
 function filter(){
  if(!tiles.length)return;
  let count=0;
  tiles.forEach(p=>{
   const show=(active==='all'||p.dataset.cat===active)&&(!query||(p.dataset.search||'').includes(query));
   p.hidden=!show; if(show)count++;
  });
  const empty=$('.empty-results'); if(empty) empty.hidden=count>0;
  filters.forEach(b=>{
   const on=b.dataset.filter===active;
   b.setAttribute('aria-pressed', on?'true':'false');
   b.classList.toggle('on', on);
  });
 }
 filters.forEach(b=>b.addEventListener('click',()=>{active=b.dataset.filter;filter();history.replaceState(null,'','#cat-'+active)}));
 if(location.hash.startsWith('#cat-')){
  const h=location.hash.slice(5);
  if(filters.some(b=>b.dataset.filter===h)){active=h;filter();}
 }

 let galleryItems=[], current=0;
 function itemsOf(name){return $$(`[data-gallery="${name}"]`).filter(a=>{const t=a.closest('.scheme-tile,.product');return !t||!t.hidden})}
 function showPhoto(i){
  if(!galleryItems.length||!photo)return;
  current=(i+galleryItems.length)%galleryItems.length;
  const a=galleryItems[current], im=$('#lightbox-image');
  im.src=a.getAttribute('href')||a.dataset.full||'';
  im.alt=a.dataset.title||'';
  const t=$('#photo-title'); if(t) t.textContent=a.dataset.title||'';
  const c=$('.photo-counter'); if(c) c.textContent=`${current+1} / ${galleryItems.length}`;
 }
 function openGallery(el){
  const name=el.dataset.gallery||'photos';
  galleryItems=itemsOf(name);
  const i=Math.max(0, galleryItems.indexOf(el));
  showPhoto(i); open(photo);
 }
 $$('[data-gallery]').forEach(a=>a.addEventListener('click',e=>{e.preventDefault();openGallery(a)}));
 const prev=photo&&$('.prev',photo), next=photo&&$('.next',photo);
 if(prev) prev.addEventListener('click',()=>showPhoto(current-1));
 if(next) next.addEventListener('click',()=>showPhoto(current+1));
 document.addEventListener('keydown',e=>{if(photo&&photo.open){if(e.key==='ArrowLeft')showPhoto(current-1);if(e.key==='ArrowRight')showPhoto(current+1)}});
})();
'''.lstrip(), encoding='utf-8')


def write_schemes():
    out = ROOT / 'images' / 'schemes'
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for v in VARIANTS:
        (out / f"{v['slug']}.svg").write_text(rb.make_scheme(v), encoding='utf-8')
    print('schemes', len(VARIANTS))


def write_all(photos):
    pages = {
        ROOT / 'index.html': wrap(
            'Строительные бытовки в Новосибирске — SibNordModul',
            'Собственное производство бытовок в Новосибирске. Утеплённая бытовка 2,4×6 м — 245 000 ₽. Продажа и аренда, модульные дома и северные бытовки из сэндвич-панелей.',
            0, 'home', 'index.html', page_home()),
        ROOT / 'catalog' / 'index.html': wrap(
            'Каталог бытовок — SibNordModul',
            'Каталог бытовок: универсальные, строительные, дачные, складские, посты охраны. Утеплённая бытовка 2,4×6 м — 245 000 ₽, другие варианты — цена по запросу.',
            1, 'catalog', 'catalog/', page_catalog()),
        ROOT / 'rent' / 'index.html': wrap(
            'Аренда бытовок от 8 000 ₽/мес — SibNordModul',
            'Аренда бытовок в Новосибирске от 8 000 ₽ в месяц. Оплата наличными или по безналу, с НДС и без НДС.',
            1, 'rent', 'rent/', page_rent()),
        ROOT / 'custom' / 'index.html': wrap(
            'Другие решения под заказ — SibNordModul',
            'Модульные дома, северные бытовки из сэндвич-панелей, офисы, раздевалки, КПП, санблоки и совмещённые модули под заказ. Новосибирск.',
            1, 'custom', 'custom/', page_custom()),
        ROOT / 'about' / 'index.html': wrap(
            'О компании — SibNordModul',
            'Собственное производство металлических строительных бытовок, утеплённых модулей, северных бытовок из сэндвич-панелей и модульных домов в Новосибирске. Продажа, аренда и докомплектация под задачу.',
            1, 'about', 'about/', page_about()),
        ROOT / 'gallery' / 'index.html': wrap(
            'Фотогалерея — SibNordModul',
            'Реальные фото утеплённой бытовки 2,4×6 м и производства SibNordModul в Новосибирске.',
            1, 'gallery', 'gallery/', page_gallery(photos)),
        ROOT / 'contacts' / 'index.html': wrap(
            'Контакты — SibNordModul, Новосибирск, Пашино',
            'Телефон +7 913 943-88-14, городской +7 (383) 375-00-10, WhatsApp, Telegram, почта Sibnordmodul@yandex.ru. Адрес: Новосибирск, мкр. Пашино, Томская улица, 1.',
            1, 'contacts', 'contacts/', page_contacts()),
    }
    for path, html_s in pages.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html_s, encoding='utf-8')
        print('wrote', path.relative_to(ROOT), 'bytes', path.stat().st_size)


def main():
    # save sprite before overwriting index
    t = (ROOT / 'index.html').read_text(encoding='utf-8')
    m = re.search(r'<svg class="sprite".*?</svg>', t, flags=re.S)
    if not m:
        m = re.search(r'<svg[^>]*class="sprite"[^>]*>.*?</svg>', t, flags=re.S)
    if m:
        Path('/tmp/sibnord_build/sprite.svg').write_text(m.group(0), encoding='utf-8')
        print('sprite saved', len(m.group(0)))
    else:
        print('WARNING: sprite not found in current index')

    photos, missing = rb.process_photos()
    write_schemes()
    write_js()
    write_all(photos)
    patch_css()

    # sanity
    issues = []
    for path in [ROOT/'index.html', ROOT/'catalog'/'index.html', ROOT/'contacts'/'index.html']:
        h = path.read_text(encoding='utf-8')
        if 'https://t.me/Volt0ne' not in h: issues.append(f'{path.name}: no TG')
        if 'wa.me/79139438814' not in h: issues.append(f'{path.name}: no WA')
        if PHONE_DISP not in h: issues.append(f'{path.name}: no phone')
        if LANDLINE_DISP not in h: issues.append(f'{path.name}: no landline')
        if MAIL_DISP not in h: issues.append(f'{path.name}: no mail')
        if 'Дополнительная комплектация' in h: issues.append(f'{path}: extra section leaked')
        if 'Бытовка на фото' in h: issues.append(f'{path}: old menu item')
    # only 245000 as product price, rent 8000 allowed
    home = (ROOT/'index.html').read_text(encoding='utf-8')
    if 'images/hero-latin.jpg' not in home: issues.append('hero missing on home')
    # broken images across pages
    for path in ROOT.rglob('index.html'):
        rel_depth = 0 if path.parent == ROOT else 1
        text = path.read_text(encoding='utf-8')
        for src in re.findall(r'(?:src|href)="((?:\.\./)*images/[^"]+)"', text):
            # resolve
            fp = (path.parent / src).resolve()
            if not fp.exists():
                issues.append(f'missing asset {src} from {path.relative_to(ROOT)}')
        for src in re.findall(r'(?:src|href)="(images/[^"]+)"', text):
            fp = (path.parent / src).resolve()
            if not fp.exists():
                issues.append(f'missing asset {src} from {path.relative_to(ROOT)}')
    print('ISSUES:', issues or 'none')
    print('PHOTOS_USED', len(photos), 'MISSING', len(missing))
    counts = cat_counts()
    print('CATEGORY_COUNTS', counts)
    print('VARIANTS', len(VARIANTS))
    Path('/tmp/sibnord_build/pages_report.txt').write_text(
        f'photos_used={len(photos)}\nmissing={missing}\ncounts={counts}\nissues={issues}\n',
        encoding='utf-8')


if __name__ == '__main__':
    main()
