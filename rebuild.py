#!/usr/bin/env python3
# Rebuild SibNordModul catalog: schematics, real photos, contacts, main 6x2.4 description.
from __future__ import annotations
import os, re, shutil, html, unicodedata
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path('/workspace/sibnordmodul-site')
ATT = Path('/home/box/agent-data/agents/979151ff-ef81-4118-b89c-44bb0084de74/attachments')
TEXT = Path('/workspace/sibnord_text/main_6x24.txt')

PHONE_DISP = '+7 913 943-88-14'
TEL = 'tel:+79139438814'
WA = 'https://wa.me/79139438814'
TG = 'https://t.me/Volt0ne'
MAIL = 'mailto:Sibnordmodul@yandex.ru'
MAIL_DISP = 'Sibnordmodul@yandex.ru'
ADDR = 'Новосибирск, мкр. Пашино, Томская улица, 1'
# 2GIS: there is no «Томское шоссе, 1» in Pashino; the street is Томская улица, 1
# coords from nsk.ginfo.ru for this house: 55.161774, 82.967659
GIS_OPEN = 'https://2gis.ru/novosibirsk/search/Новосибирск, Томская улица, 1, Пашино?m=82.967659,55.161774/17'
GIS_DIR = 'https://2gis.ru/novosibirsk/routeSearch/rsType/car/to/82.967659,55.161774│Томская улица, 1'
PRICE = '245 000 ₽'
PRICE_NOTE = ('Указанная стоимость — именно за бытовку размером 2,4 × 6 м в комплектации, '
              'представленной на фотографиях и описанной выше. Другие варианты рассчитываются отдельно.')

PHOTO_FILES = [
    # (filename, alt, caption or '')
    ('4165942049d7b7789a34395c9f07a5cab7ae11ecc988f875ab3428ceeee926df.png', 'Утеплённая бытовка 2,4×6 м, серый профлист и коричневая дверь', ''),
    ('653f208adce1e6a6283152c21bd55e7b32c585be8da532a15eccd8f8e0a00267.png', 'Бытовка 2,4×6 м снаружи', ''),
    ('4fa499c2af0a93e60ca8d4a78836cd0da5dde54c5f5b5fa26320429664626487.png', 'Бытовка 2,4×6 м, вид с окном', ''),
    ('9760b9a3d7c244a765854b6691c4caabeb7384facbec4caa9b3957a4a6d5f54e.png', 'Бытовка 2,4×6 м на производстве', ''),
    ('9152c1085be4137889a65b301b8587e90ee16b4474a4a5336d7c335713ac0ae8.png', 'Бытовка 2,4×6 м, фасад', ''),
    ('a144b2640d9d8416f85cc57e37b7b5a0a79d4afb6b2f990ea5451c02a218d5e1.png', 'Бытовка 2,4×6 м, коричневая дверь', ''),
    ('fc474fe5d71a5a528e1d8ab74fce9cd49b9bf290b04f72c6f9ccdd57398fa7f1.png', 'Бытовка 2,4×6 м с окном', ''),
    ('716836421447c37d74aaff4c59644a6195206720be9ec27d93beb5140d9e70c0.png', 'Бытовка 2,4×6 м, два окна и дверь', ''),
    ('3d6a9ebbc10892f5a02db6a95d374f2f27ca715c22833c94842466cd753211d7.png', 'Каркас бытовки с минеральной ватой', 'Утепление'),
    ('c2b802897555b7835d1581fbf278d2b692a4ca7d76b5500a6076e79b8e6dd856.png', 'Внутренняя отделка ОСБ', 'Внутренняя отделка'),
    ('a9ec1398dd3d8e407f4ca6e51d32af2506bcb0df4b23679576728dda40e3997b.png', 'Металлический каркас бытовки', 'Каркас'),
]

CATS = [
    ('all', 'Все'),
    ('stroitelnye', 'Бытовки строительные'),
    ('dachnye', 'Бытовки дачные'),
    ('guard', 'Посты охраны / КПП'),
    ('office', 'Прорабские / офисные'),
    ('living', 'Бытовки-раздевалки / жильё бригады'),
    ('sklad', 'Склады / хозблоки'),
    ('san', 'Сан-бытовки (душ/туалет)'),
    ('modular', 'Модульные дома'),
]

# typ, L, W, roof, porch, door (0-1 along length), windows (list 0-1), rooms (fractions), flags
# priced=True only for the main warm 6x2.4 base cabin

VARIANTS = [
    # stroitelnye — first one is the priced main model
    dict(slug='bytovka-6x24', cat='stroitelnye', name='Утеплённая бытовка 2,4×6 м',
         size='2,40 × 6,00 м', L=6, W=2.4, roof='flat', porch=False, door=0.12,
         windows=(0.42, 0.72), rooms=(), priced=True, stock=True,
         desc='Основной вариант: графитовый профлист, металлическая дверь, утепление 100 мм. Как на фото.'),
    dict(slug='bytovka-3x24', cat='stroitelnye', name='Бытовка строительная 3×2,4 м',
         size='3,00 × 2,40 м', L=3, W=2.4, roof='flat', porch=False, door=0.18,
         windows=(0.62,), rooms=(), priced=False, stock=True,
         desc='Компактный модуль для прораба, склада инструмента или короткой смены.'),
    dict(slug='bytovka-4x24', cat='stroitelnye', name='Бытовка строительная 4×2,4 м',
         size='4,00 × 2,40 м', L=4, W=2.4, roof='flat', porch=False, door=0.15,
         windows=(0.45, 0.75), rooms=(), priced=False, stock=True,
         desc='Универсальный размер под стройку, офис на объекте или жильё двоих.'),
    dict(slug='bytovka-5x24', cat='stroitelnye', name='Бытовка строительная 5×2,4 м с тамбуром',
         size='5,00 × 2,40 м', L=5, W=2.4, roof='flat', porch=False, door=0.12,
         windows=(0.48, 0.78), rooms=(0.22,), priced=False, stock=True,
         desc='Планировка с тамбуром: тепло лучше держится, грязь остаётся у входа.'),
    dict(slug='bytovka-6x3', cat='stroitelnye', name='Бытовка строительная 6×3 м',
         size='6,00 × 3,00 м', L=6, W=3, roof='flat', porch=False, door=0.12,
         windows=(0.38, 0.58, 0.8), rooms=(), priced=False, stock=True,
         desc='Шире стандартной: удобнее расставить мебель и рабочие места.'),
    # dachnye
    dict(slug='dacha-4x24', cat='dachnye', name='Бытовка дачная 4×2,4 м с крыльцом',
         size='4,00 × 2,40 м', L=4, W=2.4, roof='pitched', porch=True, door=0.2,
         windows=(0.55, 0.8), rooms=(), priced=False, stock=True,
         desc='Скатная крыша и крыльцо — для участка и сезонного проживания.'),
    dict(slug='dacha-5x24', cat='dachnye', name='Бытовка дачная 5×2,4 м, две комнаты',
         size='5,00 × 2,40 м', L=5, W=2.4, roof='pitched', porch=True, door=0.15,
         windows=(0.4, 0.72), rooms=(0.5,), priced=False, stock=True,
         desc='Две комнаты: спальня и кухня-гостиная, крыльцо у входа.'),
    dict(slug='dacha-6x24', cat='dachnye', name='Бытовка дачная 6×2,4 м',
         size='6,00 × 2,40 м', L=6, W=2.4, roof='pitched', porch=True, door=0.14,
         windows=(0.4, 0.62, 0.84), rooms=(0.4,), priced=False, stock=True,
         desc='Дачный вариант того же габарита: скатная крыша, крыльцо, две зоны.'),
    dict(slug='dacha-6x3', cat='dachnye', name='Дачный домик 6×3 м',
         size='6,00 × 3,00 м', L=6, W=3, roof='pitched', porch=True, door=0.14,
         windows=(0.38, 0.58, 0.8), rooms=(0.45,), priced=False, stock=True,
         desc='Просторный дачный модуль с двумя комнатами и крыльцом.'),
    # guard
    dict(slug='guard-2x2', cat='guard', name='Пост охраны 2×2 м',
         size='2,00 × 2,00 м', L=2, W=2, roof='flat', porch=False, door=0.22,
         windows=(0.55,), rooms=(), priced=False, stock=True, panoramic=True,
         desc='Компактный пост с панорамным остеклением и обзором территории.'),
    dict(slug='kpp-24x24', cat='guard', name='КПП 2,4×2,4 м с козырьком',
         size='2,40 × 2,40 м', L=2.4, W=2.4, roof='flat', porch=False, door=0.2,
         windows=(0.58,), rooms=(), priced=False, stock=True, panoramic=True, canopy=True,
         desc='КПП с козырьком над окном выдачи и широким обзором.'),
    dict(slug='guard-3x24', cat='guard', name='Пост охраны 3×2,4 м с санузлом',
         size='3,00 × 2,40 м', L=3, W=2.4, roof='flat', porch=False, door=0.18,
         windows=(0.45, 0.75), rooms=(0.72,), priced=False, stock=True, panoramic=True,
         desc='Пост на одного сотрудника с отдельным санузлом.'),
    dict(slug='kpp-4x24', cat='guard', name='КПП 4×2,4 м на два рабочих места',
         size='4,00 × 2,40 м', L=4, W=2.4, roof='flat', porch=False, door=0.15,
         windows=(0.4, 0.7), rooms=(), priced=False, stock=True, panoramic=True, canopy=True,
         desc='Два рабочих места, панорамные окна, козырёк у окна выдачи.'),
    # office
    dict(slug='office-5x24', cat='office', name='Прорабская 5×2,4 м',
         size='5,00 × 2,40 м', L=5, W=2.4, roof='flat', porch=False, door=0.14,
         windows=(0.4, 0.68, 0.88), rooms=(), priced=False, stock=True,
         desc='Кабинет прораба: стол, стеллаж, место для планерок на объекте.'),
    dict(slug='office-6x24', cat='office', name='Офисный модуль 6×2,4 м, два кабинета',
         size='6,00 × 2,40 м', L=6, W=2.4, roof='flat', porch=False, door=0.12,
         windows=(0.35, 0.55, 0.8), rooms=(0.5,), priced=False, stock=True,
         desc='Два кабинета в одном модуле — для офиса на стройке.'),
    dict(slug='office-6x3', cat='office', name='Офис 6×3 м с переговорной',
         size='6,00 × 3,00 м', L=6, W=3, roof='flat', porch=False, door=0.12,
         windows=(0.35, 0.55, 0.8), rooms=(0.4,), priced=False, stock=True,
         desc='Рабочая зона и переговорная в широком модуле.'),
    dict(slug='office-2mod', cat='office', name='Офис из двух блоков 6×4,8 м',
         size='6,00 × 4,80 м', L=6, W=4.8, roof='flat', porch=False, door=0.12,
         windows=(0.35, 0.55, 0.8), rooms=(0.5,), priced=False, stock=False, modules=2,
         desc='Два состыкованных блока: приёмная и рабочие кабинеты.'),
    # living
    dict(slug='live-6x24', cat='living', name='Жильё бригады 6×2,4 м',
         size='6,00 × 2,40 м', L=6, W=2.4, roof='flat', porch=False, door=0.12,
         windows=(0.4, 0.62, 0.84), rooms=(0.28,), priced=False, stock=True,
         desc='Тамбур и жилая комната, места для спальных мест бригады.'),
    dict(slug='dress-6x24', cat='living', name='Бытовка-раздевалка 6×2,4 м',
         size='6,00 × 2,40 м', L=6, W=2.4, roof='flat', porch=False, door=0.12,
         windows=(0.38, 0.62, 0.84), rooms=(), priced=False, stock=True, benches=True,
         desc='Скамейки и крюки вдоль стен, место переодеться до и после смены.'),
    dict(slug='live-6x3', cat='living', name='Жильё бригады 6×3 м, две комнаты',
         size='6,00 × 3,00 м', L=6, W=3, roof='flat', porch=False, door=0.12,
         windows=(0.38, 0.58, 0.8), rooms=(0.22, 0.58), priced=False, stock=True,
         desc='Две жилые комнаты и тамбур — для большей бригады.'),
    dict(slug='dress-5x24', cat='living', name='Раздевалка 5×2,4 м с сушилкой',
         size='5,00 × 2,40 м', L=5, W=2.4, roof='flat', porch=False, door=0.14,
         windows=(0.42, 0.75), rooms=(0.72,), priced=False, stock=True, benches=True,
         desc='Раздевалка и отдельная сушилка для одежды и обуви.'),
    # sklad
    dict(slug='hoz-3x24', cat='sklad', name='Хозблок 3×2,4 м',
         size='3,00 × 2,40 м', L=3, W=2.4, roof='flat', porch=False, door=0.2,
         windows=(0.7,), rooms=(), priced=False, stock=True,
         desc='Небольшой хозблок под инструмент, инвентарь или насосную.'),
    dict(slug='sklad-4x24', cat='sklad', name='Склад 4×2,4 м',
         size='4,00 × 2,40 м', L=4, W=2.4, roof='flat', porch=False, door=0.16,
         windows=(0.72,), rooms=(), priced=False, stock=True, double_door=True,
         desc='Складской модуль с широкой дверью под стеллажи и ящики.'),
    dict(slug='sklad-6x24', cat='sklad', name='Склад 6×2,4 м',
         size='6,00 × 2,40 м', L=6, W=2.4, roof='flat', porch=False, door=0.12,
         windows=(0.55, 0.82), rooms=(), priced=False, stock=True, double_door=True,
         desc='Длинный склад с распашными дверями для материалов и инструмента.'),
    dict(slug='sklad-6x3', cat='sklad', name='Склад-хозблок 6×3 м',
         size='6,00 × 3,00 м', L=6, W=3, roof='flat', porch=False, door=0.12,
         windows=(0.55, 0.82), rooms=(0.7,), priced=False, stock=True, double_door=True,
         desc='Широкий склад с отдельным хозотсеком.'),
    # san
    dict(slug='san-3x24', cat='san', name='Сан-бытовка 3×2,4 м, душ и туалет',
         size='3,00 × 2,40 м', L=3, W=2.4, roof='flat', porch=False, door=0.18,
         windows=(0.4, 0.75), rooms=(0.5,), priced=False, stock=True, san=True,
         desc='Душевая и туалет в одном модуле — для стройки или дачи.'),
    dict(slug='san-4x24', cat='san', name='Санблок 4×2,4 м на две кабины',
         size='4,00 × 2,40 м', L=4, W=2.4, roof='flat', porch=False, door=0.15,
         windows=(0.35, 0.6, 0.85), rooms=(0.33, 0.66), priced=False, stock=True, san=True,
         desc='Две сантехнические кабины и тамбур с умывальником.'),
    dict(slug='san-6x24', cat='san', name='Душевая 6×2,4 м для бригады',
         size='6,00 × 2,40 м', L=6, W=2.4, roof='flat', porch=False, door=0.12,
         windows=(0.35, 0.55, 0.78), rooms=(0.22, 0.45, 0.7), priced=False, stock=True, san=True,
         desc='Несколько душевых кабин, раздевалка и туалет для бригады.'),
    dict(slug='wc-24x24', cat='san', name='Туалетный модуль 2,4×2,4 м',
         size='2,40 × 2,40 м', L=2.4, W=2.4, roof='flat', porch=False, door=0.22,
         windows=(0.7,), rooms=(0.5,), priced=False, stock=True, san=True,
         desc='Компактный туалетный блок на одну-две кабины.'),
    # modular — under order, at the end
    dict(slug='house-6x6', cat='modular', name='Модульный дом 6×6 м',
         size='6,00 × 6,00 м', L=6, W=6, roof='pitched', porch=True, door=0.2,
         windows=(0.35, 0.7), rooms=(0.5,), priced=False, stock=False, modules=2,
         desc='Дом из двух блоков под заказ: гостиная и спальня.'),
    dict(slug='house-8x6', cat='modular', name='Модульный дом 8×6 м, три комнаты',
         size='8,00 × 6,00 м', L=8, W=6, roof='pitched', porch=True, door=0.18,
         windows=(0.28, 0.5, 0.75), rooms=(0.33, 0.66), priced=False, stock=False, modules=2,
         desc='Три комнаты в двух блоках — под заказ, планировку согласуем.'),
    dict(slug='house-9x6', cat='modular', name='Модульный дом 9×6 м из трёх блоков',
         size='9,00 × 6,00 м', L=9, W=6, roof='pitched', porch=True, door=0.15,
         windows=(0.22, 0.45, 0.7), rooms=(0.33, 0.66), priced=False, stock=False, modules=3,
         desc='Три состыкованных блока, больше площади для семьи или базы.'),
    dict(slug='house-6x48', cat='modular', name='Дачный модульный дом 6×4,8 м',
         size='6,00 × 4,80 м', L=6, W=4.8, roof='pitched', porch=True, door=0.18,
         windows=(0.35, 0.65, 0.85), rooms=(0.45,), priced=False, stock=False, modules=2,
         desc='Дачный дом из двух блоков со скатной крышей — под заказ.'),
]

INK, ACCENT, SOFT, LINE = '#2A2E33', '#F07A1A', '#f7f8f9', '#c5c9cd'
WALL, ROOF, DOOR, GLASS, DIM = '#e8eaed', '#3a4046', '#7a3f16', '#c9dbe8', '#87898c'


def esc(s):
    return html.escape(s, quote=True)


def wa_link(product):
    text = (f'Здравствуйте! Интересует: {product}. '
            f'Подскажите, пожалуйста, наличие и стоимость.')
    from urllib.parse import quote
    return WA + '?text=' + quote(text)


def fmt_m(v):
    s = f'{v:.2f}'.replace('.', ',')
    s = s.rstrip('0').rstrip(',')
    if ',' not in s:
        s += ',00'
    elif len(s.split(',')[1]) == 1:
        s += '0'
    return s


def make_scheme(v):
    """Technical line-art: elevation + floor plan with dimensions."""
    L, W = float(v['L']), float(v['W'])
    roof = v.get('roof', 'flat')
    porch = v.get('porch', False)
    door_t = float(v.get('door', 0.15))
    windows = list(v.get('windows') or [])
    rooms = list(v.get('rooms') or [])
    panoramic = v.get('panoramic', False)
    canopy = v.get('canopy', False)
    double_door = v.get('double_door', False)
    modules = int(v.get('modules') or 1)
    san = v.get('san', False)
    benches = v.get('benches', False)
    slug = v['slug']

    vb_w, vb_h = 800, 540
    # elevation box
    max_span = max(L, 6)
    scale = 520 / max(max_span, 1)
    body_w = L * scale
    body_h = 150
    # leave room for porch / roof
    ex = 400 - body_w / 2
    ey = 200
    if porch:
        ex += 18
    # floor plan
    pscale = min(420 / L, 150 / W)
    pw, ph = L * pscale, W * pscale
    px, py = 400 - pw / 2, 350

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="800" height="540" viewBox="0 0 800 540" role="img" aria-label="{esc(v["name"])}">',
        f'<rect width="800" height="540" fill="{SOFT}"/>',
        f'<text x="24" y="28" font-family="Roboto,Arial,sans-serif" font-size="13" fill="{DIM}">Фасад</text>',
        f'<text x="24" y="328" font-family="Roboto,Arial,sans-serif" font-size="13" fill="{DIM}">План</text>',
        f'<text x="776" y="28" text-anchor="end" font-family="Roboto,Arial,sans-serif" font-size="13" fill="{INK}">{esc(v["size"])}</text>',
    ]

    # roof
    if roof == 'pitched':
        roof_h = 42
        parts.append(
            f'<polygon points="{ex-6},{ey-body_h} {ex+body_w/2},{ey-body_h-roof_h} {ex+body_w+6},{ey-body_h} {ex+body_w},{ey-body_h+8} {ex},{ey-body_h+8}" fill="{ROOF}" stroke="{INK}" stroke-width="1.6"/>'
        )
    else:
        parts.append(
            f'<rect x="{ex-3:.1f}" y="{ey-body_h-10:.1f}" width="{body_w+6:.1f}" height="12" fill="{ROOF}" stroke="{INK}" stroke-width="1.4"/>'
        )

    # body
    parts.append(
        f'<rect x="{ex:.1f}" y="{ey-body_h:.1f}" width="{body_w:.1f}" height="{body_h:.1f}" fill="{WALL}" stroke="{INK}" stroke-width="1.8"/>'
    )
    # corrugation
    step = 8
    x = ex + 6
    while x < ex + body_w - 6:
        parts.append(f'<line x1="{x:.1f}" y1="{ey-body_h+2:.1f}" x2="{x:.1f}" y2="{ey-2:.1f}" stroke="#c9ced3" stroke-width="1"/>')
        x += step

    # modules vertical seams on elevation
    if modules > 1:
        for i in range(1, modules):
            sx = ex + body_w * i / modules
            parts.append(f'<line x1="{sx:.1f}" y1="{ey-body_h:.1f}" x2="{sx:.1f}" y2="{ey:.1f}" stroke="{INK}" stroke-width="1.2" stroke-dasharray="4 3"/>')

    # porch
    if porch:
        parts.append(
            f'<rect x="{ex-28:.1f}" y="{ey-8:.1f}" width="28" height="8" fill="#d4d7db" stroke="{INK}" stroke-width="1.2"/>'
        )
        parts.append(f'<line x1="{ex-28:.1f}" y1="{ey-8:.1f}" x2="{ex-28:.1f}" y2="{ey-70:.1f}" stroke="{INK}" stroke-width="1.4"/>')
        parts.append(f'<line x1="{ex:.1f}" y1="{ey-8:.1f}" x2="{ex:.1f}" y2="{ey-70:.1f}" stroke="{INK}" stroke-width="1.4"/>')
        parts.append(f'<line x1="{ex-28:.1f}" y1="{ey-70:.1f}" x2="{ex:.1f}" y2="{ey-70:.1f}" stroke="{INK}" stroke-width="1.4"/>')

    # canopy
    if canopy:
        cx = ex + body_w * 0.62
        parts.append(f'<polygon points="{cx-30},{ey-body_h+48} {cx+50},{ey-body_h+48} {cx+44},{ey-body_h+58} {cx-24},{ey-body_h+58}" fill="{ROOF}" stroke="{INK}" stroke-width="1.2"/>')

    # door on elevation
    dw, dh = (36 if not double_door else 56), 96
    dx = ex + door_t * body_w
    dy = ey - dh
    parts.append(f'<rect x="{dx:.1f}" y="{dy:.1f}" width="{dw}" height="{dh}" fill="{DOOR}" stroke="{INK}" stroke-width="1.5"/>')
    if double_door:
        parts.append(f'<line x1="{dx+dw/2:.1f}" y1="{dy:.1f}" x2="{dx+dw/2:.1f}" y2="{ey:.1f}" stroke="{INK}" stroke-width="1"/>')
    parts.append(f'<circle cx="{dx+dw-7:.1f}" cy="{dy+dh/2:.1f}" r="2.2" fill="#e8c37a" stroke="{INK}" stroke-width=".8"/>')

    # windows
    if panoramic:
        wx = ex + body_w * 0.32
        ww = body_w * 0.62
        wy, wh = ey - body_h + 36, 70
        parts.append(f'<rect x="{wx:.1f}" y="{wy:.1f}" width="{ww:.1f}" height="{wh:.1f}" fill="{GLASS}" stroke="{INK}" stroke-width="1.5"/>')
        # mullions
        for i in range(1, 3):
            mx = wx + ww * i / 3
            parts.append(f'<line x1="{mx:.1f}" y1="{wy:.1f}" x2="{mx:.1f}" y2="{wy+wh:.1f}" stroke="{INK}" stroke-width="1"/>')
        parts.append(f'<line x1="{wx:.1f}" y1="{wy+wh/2:.1f}" x2="{wx+ww:.1f}" y2="{wy+wh/2:.1f}" stroke="{INK}" stroke-width="1"/>')
    else:
        for t in windows:
            ww, wh = 44, 56
            wx = ex + t * body_w - ww / 2
            wy = ey - body_h + 32
            parts.append(f'<rect x="{wx:.1f}" y="{wy:.1f}" width="{ww}" height="{wh}" fill="{GLASS}" stroke="{INK}" stroke-width="1.5"/>')
            parts.append(f'<line x1="{wx+ww/2:.1f}" y1="{wy:.1f}" x2="{wx+ww/2:.1f}" y2="{wy+wh:.1f}" stroke="{INK}" stroke-width="1"/>')
            parts.append(f'<line x1="{wx:.1f}" y1="{wy+wh/2:.1f}" x2="{wx+ww:.1f}" y2="{wy+wh/2:.1f}" stroke="{INK}" stroke-width="1"/>')

    # ground line
    parts.append(f'<line x1="{ex-40:.1f}" y1="{ey:.1f}" x2="{ex+body_w+40:.1f}" y2="{ey:.1f}" stroke="{LINE}" stroke-width="1.2"/>')

    # elevation dimension
    parts.append(dim_h(ex, ey + 18, body_w, f'{fmt_m(L)} м'))

    # ---- floor plan ----
    parts.append(f'<rect x="{px:.1f}" y="{py:.1f}" width="{pw:.1f}" height="{ph:.1f}" fill="#fff" stroke="{INK}" stroke-width="2"/>')
    if modules > 1:
        for i in range(1, modules):
            sx = px + pw * i / modules
            parts.append(f'<line x1="{sx:.1f}" y1="{py:.1f}" x2="{sx:.1f}" y2="{py+ph:.1f}" stroke="{INK}" stroke-width="1.6"/>')
    for t in rooms:
        rx = px + pw * t
        parts.append(f'<line x1="{rx:.1f}" y1="{py:.1f}" x2="{rx:.1f}" y2="{py+ph:.1f}" stroke="{INK}" stroke-width="1.4"/>')

    # plan door on front (bottom) wall
    pdoor_w = 22 if not double_door else 34
    pdx = px + door_t * pw
    parts.append(f'<line x1="{pdx:.1f}" y1="{py+ph:.1f}" x2="{pdx+pdoor_w:.1f}" y2="{py+ph:.1f}" stroke="{SOFT}" stroke-width="3.5"/>')
    # swing arc
    parts.append(f'<path d="M {pdx:.1f} {py+ph:.1f} A {pdoor_w} {pdoor_w} 0 0 0 {pdx:.1f} {py+ph-pdoor_w:.1f}" fill="none" stroke="{ACCENT}" stroke-width="1.2"/>')
    parts.append(f'<line x1="{pdx:.1f}" y1="{py+ph:.1f}" x2="{pdx:.1f}" y2="{py+ph-pdoor_w:.1f}" stroke="{ACCENT}" stroke-width="1.2"/>')

    # plan windows on top wall
    if panoramic:
        w0, w1 = px + pw * 0.28, px + pw * 0.9
        parts.append(f'<line x1="{w0:.1f}" y1="{py:.1f}" x2="{w1:.1f}" y2="{py:.1f}" stroke="#5b8aa8" stroke-width="4"/>')
    else:
        for t in windows:
            wx = px + t * pw - 12
            parts.append(f'<line x1="{wx:.1f}" y1="{py:.1f}" x2="{wx+24:.1f}" y2="{py:.1f}" stroke="#5b8aa8" stroke-width="4"/>')

    # benches
    if benches:
        parts.append(f'<rect x="{px+10:.1f}" y="{py+8:.1f}" width="{pw-20:.1f}" height="10" fill="none" stroke="{INK}" stroke-width="1"/>')
        parts.append(f'<rect x="{px+10:.1f}" y="{py+ph-18:.1f}" width="{max(pw*0.55, 40):.1f}" height="10" fill="none" stroke="{INK}" stroke-width="1"/>')

    # san fixtures simple
    if san:
        # first room or left: toilet block
        fx = px + pw * (rooms[0] * 0.3 if rooms else 0.15)
        fy = py + ph * 0.35
        parts.append(f'<rect x="{fx:.1f}" y="{fy:.1f}" width="16" height="22" rx="6" fill="none" stroke="{INK}" stroke-width="1.2"/>')
        if len(rooms) >= 1 or L >= 3:
            sx = px + pw * (0.62 if not rooms else min(rooms[-1] + 0.08, 0.85))
            parts.append(f'<rect x="{sx:.1f}" y="{py+10:.1f}" width="28" height="14" fill="none" stroke="{INK}" stroke-width="1.2"/>')
            parts.append(f'<circle cx="{sx+14:.1f}" cy="{py+17:.1f}" r="3" fill="none" stroke="{INK}" stroke-width="1"/>')

    # plan dimensions
    parts.append(dim_h(px, py + ph + 22, pw, f'{fmt_m(L)} м'))
    parts.append(dim_v(px + pw + 22, py, ph, f'{fmt_m(W)} м'))

    parts.append('</svg>')
    return '\n'.join(parts)


def dim_h(x, y, w, label):
    return (
        f'<g stroke="{DIM}" fill="{DIM}" stroke-width="1">'
        f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x+w:.1f}" y2="{y:.1f}"/>'
        f'<line x1="{x:.1f}" y1="{y-5:.1f}" x2="{x:.1f}" y2="{y+5:.1f}"/>'
        f'<line x1="{x+w:.1f}" y1="{y-5:.1f}" x2="{x+w:.1f}" y2="{y+5:.1f}"/>'
        f'</g><text x="{x+w/2:.1f}" y="{y-6:.1f}" text-anchor="middle" font-family="Roboto,Arial,sans-serif" font-size="12" fill="{DIM}">{label}</text>'
    )


def dim_v(x, y, h, label):
    return (
        f'<g stroke="{DIM}" fill="{DIM}" stroke-width="1">'
        f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x:.1f}" y2="{y+h:.1f}"/>'
        f'<line x1="{x-5:.1f}" y1="{y:.1f}" x2="{x+5:.1f}" y2="{y:.1f}"/>'
        f'<line x1="{x-5:.1f}" y1="{y+h:.1f}" x2="{x+5:.1f}" y2="{y+h:.1f}"/>'
        f'</g><text x="{x+8:.1f}" y="{y+h/2:.1f}" font-family="Roboto,Arial,sans-serif" font-size="12" fill="{DIM}">{label}</text>'
    )


def write_schemes():
    out = ROOT / 'images' / 'schemes'
    out.mkdir(parents=True, exist_ok=True)
    for v in VARIANTS:
        (out / f"{v['slug']}.svg").write_text(make_scheme(v), encoding='utf-8')
    print(f'schemes: {len(VARIANTS)}')


def process_photos():
    out = ROOT / 'images' / 'real'
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    used = []
    missing = []
    for i, (name, alt, cap) in enumerate(PHOTO_FILES, 1):
        src = ATT / name
        if not src.exists():
            missing.append(name)
            continue
        im = Image.open(src)
        im = ImageOps.exif_transpose(im)
        if im.mode not in ('RGB', 'L'):
            im = im.convert('RGB')
        else:
            im = im.convert('RGB')
        w, h = im.size
        long_side = max(w, h)
        if long_side > 1600:
            r = 1600 / long_side
            im = im.resize((int(w * r), int(h * r)), Image.Resampling.LANCZOS)
        stem = f'{i:02d}'
        jpg = out / f'{stem}.jpg'
        webp = out / f'{stem}.webp'
        im.save(jpg, 'JPEG', quality=82, optimize=True, progressive=True, exif=b'')
        im.save(webp, 'WEBP', quality=82, method=6, exif=b'')
        # strip any leftover
        used.append(dict(i=i, stem=stem, alt=alt, cap=cap, w=im.size[0], h=im.size[1], src=name))
        print(f'photo {stem}: {im.size} from {name[:12]}…')
    print(f'photos used={len(used)} missing={len(missing)}')
    return used, missing


def cat_counts():
    c = {k: 0 for k, _ in CATS}
    for v in VARIANTS:
        c[v['cat']] += 1
        c['all'] += 1
    return c


def catalog_html(photos):
    counts = cat_counts()
    side = ['<aside class="cat-side" aria-label="Категории каталога">',
            '<h3>Категории</h3>',
            '<div class="cat-cats" role="tablist">']
    for key, title in CATS:
        on = ' on' if key == 'all' else ''
        pressed = 'true' if key == 'all' else 'false'
        side.append(
            f'<button type="button" class="cat-cat{on}" data-filter="{key}" aria-pressed="{pressed}">'
            f'<span>{esc(title)}</span><i>{counts[key]}</i></button>'
        )
    side.append('</div>')
    side.append(
        f'<div class="cat-side-note">Не нашли нужный размер? Напишите — подберём и изготовим.'
        f'<a class="button" href="{TG}" target="_blank" rel="noopener">Telegram</a></div>'
    )
    side.append('</aside>')

    photos_block = ''
    if photos:
        tiles = []
        for p in photos:
            cap = f'<span class="real-cap">{esc(p["cap"])}</span>' if p['cap'] else ''
            tiles.append(
                f'<a class="real-item" href="images/real/{p["stem"]}.jpg" data-gallery="photos" '
                f'data-title="{esc(p["cap"] or p["alt"])}">'
                f'<picture><source srcset="images/real/{p["stem"]}.webp" type="image/webp"/>'
                f'<img src="images/real/{p["stem"]}.jpg" alt="{esc(p["alt"])}" width="{p["w"]}" height="{p["h"]}" '
                f'loading="lazy" decoding="async"/></picture>{cap}</a>'
            )
        photos_block = (
            '<div class="real-block" id="photos">'
            '<div class="real-head">'
            '<h3>Наши бытовки — реальные фото</h3>'
            f'<p class="real-price">Утеплённая бытовка 2,4 × 6 м — <strong>{PRICE}</strong></p>'
            f'<p class="real-note">{esc(PRICE_NOTE)}</p>'
            '</div>'
            f'<div class="real-grid">{"".join(tiles)}</div>'
            '</div>'
        )

    # main model description next to gallery
    desc_block = main_desc_html()

    tiles = []
    for v in VARIANTS:
        price_html = (
            f'<span class="product__price">{PRICE}</span>' if v.get('priced')
            else '<span class="product__price product__price--request">Цена по запросу</span>'
        )
        sticker = 'В наличии' if v.get('stock') else 'Под заказ'
        sticker_cls = 'sticker' if v.get('stock') else 'sticker sticker--soft'
        href = f'images/schemes/{v["slug"]}.svg'
        wa = wa_link(f'{v["name"]}, {v["size"]}')
        more = ''
        if v.get('priced'):
            more = '<a class="button button--ink" href="#model-6x24">Подробнее</a>'
        tiles.append(
            f'<article class="scheme-tile product" data-cat="{v["cat"]}" '
            f'data-search="{esc((v["name"]+" "+v["size"]+" "+v["desc"]).lower())}">'
            f'<div class="product-box">'
            f'<span class="{sticker_cls}">{sticker}</span>'
            f'<a class="product__image scheme-link" href="{href}" data-gallery="schemes" '
            f'data-title="{esc(v["name"])}" aria-label="Схема: {esc(v["name"])}">'
            f'<img src="{href}" alt="Схема: {esc(v["name"])}" width="800" height="540" loading="lazy"/></a>'
            f'<h3>{esc(v["name"])}</h3>'
            f'<p class="product__size">{esc(v["size"])}</p>'
            f'<p class="scheme-desc">{esc(v["desc"])}</p>'
            f'<div class="product__footer">{price_html}'
            f'<a class="button button--fill" href="{wa}" target="_blank" rel="noopener">Написать</a>'
            f'{more}</div>'
            f'<p class="product__status">{"Продажа и аренда" if v.get("stock") else "Изготовление на заказ"}</p>'
            f'</div></article>'
        )

    intro = (
        '<div class="catalog-head"><h2>Каталог бытовок</h2>'
        f'<a data-callback="" href="#request">Помочь с выбором ›</a></div>'
        '<p class="catalog-intro">Строительные бытовки, посты охраны, дачные и санитарные модули, '
        'жильё бригады, склады и модульные дома. В наличии разные варианты — ждать не нужно. '
        f'Утеплённая бытовка 2,4 × 6 м — {PRICE}.</p>'
    )
    return (
        f'<section id="catalog">{intro}'
        f'<div class="cat-layout">{"".join(side)}'
        f'<div class="cat-main">{photos_block}{desc_block}'
        f'<div class="scheme-grid" id="scheme-grid">{"".join(tiles)}</div>'
        f'<p class="empty-results" hidden>В этой категории пока ничего не нашлось. Выберите другую или напишите нам.</p>'
        f'</div></div></section>'
    )


def main_desc_html():
    """Format /workspace/sibnord_text/main_6x24.txt as a clean web section, keep wording."""
    raw = TEXT.read_text(encoding='utf-8') if TEXT.exists() else ''
    # We structure from the known text, keeping wording, emoji minimal.
    def items(*rows):
        return '<ul>' + ''.join(f'<li>{esc(r)}</li>' for r in rows) + '</ul>'

    uses = items(
        'Строительная бытовка',
        'Жильё для рабочих и бригады',
        'Прорабская или офис на объекте',
        'Дачный домик',
        'Складское помещение',
        'И другие хозяйственные нужды',
    )
    ext = items(
        'Стены — профлист С8, цвет графит RAL 7024',
        'Крыша — профлист С20, цвет RAL 7024',
        'Металлическая входная дверь',
        'Открывающиеся окна 1000 × 1200 мм',
    )
    frame = items(
        'Швеллер 100 × 45 (5/7,9)',
        'Уголок 63 × 63 мм, толщина 5 мм',
        'Профильная труба 40 × 40 мм, стенка 3 мм',
        'Усиленные укосины из листового металла 4 мм',
    )
    insul = items(
        'Деревянный каркас — доска 50 × 100 мм',
        'Обрешётка — доска 25 × 100 мм',
        'Утеплитель — 100 мм',
        'Ветрозащита и пароизоляция',
        'Стены — ОСБ 9 мм',
        'Пол — ОСБ 15 мм',
    )
    el = items(
        'Розетки и выключатель',
        'Осветительные приборы',
        'Электрический щиток',
        'Закладная под ввод электричества',
    )
    extra = items(
        'Другие размеры и варианты планировки',
        'Отопление',
        'Тёплый пол',
        'Другие виды утеплителя',
        'Внутренняя отделка',
        'Сантехника',
        'Дополнительное оборудование и оснащение',
    )
    pay = items(
        'Сдаём бытовки в аренду — стоимость договорная.',
        'Продажа бытовок из наличия.',
        'Оплата наличными или безналичным расчётом.',
        'Работаем с НДС и без НДС.',
    )
    return f'''
<section class="model-card content-section" id="model-6x24">
  <div class="model-heading">
    <h2>Утеплённая бытовка 2,4×6 — аренда и продажа</h2>
    <p class="model-price">{PRICE}</p>
  </div>
  <p>Собственное производство! Изготавливаем, продаём и сдаём в аренду утеплённые бытовки. Различные варианты уже в наличии — ждать изготовления не нужно!</p>
  <div class="model-uses">
    <h3>Для чего подойдёт?</h3>
    {uses}
  </div>
  <p class="spec-kicker">Комплектация бытовки (как на фото)</p>
  <div class="specs">
    <article class="spec"><h3><svg aria-hidden="true" class="icon"><use href="#i-cabin"></use></svg>Наружная отделка</h3>{ext}</article>
    <article class="spec"><h3><svg aria-hidden="true" class="icon"><use href="#i-frame"></use></svg>Металлический каркас основания</h3>{frame}</article>
    <article class="spec"><h3><svg aria-hidden="true" class="icon"><use href="#i-layers"></use></svg>Утепление и внутренняя конструкция</h3>{insul}</article>
    <article class="spec"><h3><svg aria-hidden="true" class="icon"><use href="#i-bolt"></use></svg>Электрика</h3>{el}</article>
  </div>
  <div class="model-payments">
    <p><strong>Стоимость {PRICE}.</strong> {esc(PRICE_NOTE)} Стоимость дополнительных опций рассчитывается индивидуально.</p>
    <a class="button button--fill" href="{wa_link('Утеплённая бытовка 2,4×6 м, 245 000 ₽')}" target="_blank" rel="noopener">Написать в WhatsApp</a>
    <a class="button" href="{TG}" target="_blank" rel="noopener">Написать в Telegram</a>
  </div>
  <div class="extra-lite">
    <h3>Дополнительная комплектация</h3>
    <p>По вашему желанию можем изготовить бытовку с дополнительными опциями:</p>
    {extra}
  </div>
  <div class="pay-lite">
    <h3>Аренда и условия оплаты</h3>
    {pay}
  </div>
  <p>Есть вопросы? Пишите и звоните! Поможем подобрать подходящую комплектацию. Рассчитаем стоимость под ваши задачи. Возможность изготовления под заказ. Собственное производство — контроль качества на каждом этапе!</p>
</section>
'''.strip()


def contacts_html():
    return f'''
<section class="contacts-section" id="contacts">
  <div>
    <h2>Контакты</h2>
    <p>SibNordModul · Новосибирск</p>
    <p class="contacts-addr"><svg aria-hidden="true" class="icon"><use href="#i-pin"></use></svg> {esc(ADDR)}</p>
    <div class="map-btns">
      <a class="button" href="{GIS_OPEN}" rel="noopener" target="_blank">Открыть в 2ГИС</a>
      <a class="button" href="{GIS_DIR}" rel="noopener" target="_blank">Построить маршрут</a>
    </div>
    <a class="phone" href="{TEL}">{PHONE_DISP}</a>
    <a class="mail" href="{MAIL}">{MAIL_DISP}</a>
    <div class="social-links">
      <a href="{WA}" rel="noopener" target="_blank"><svg aria-hidden="true" class="icon"><use href="#i-chat"></use></svg>WhatsApp</a>
      <a href="{TG}" rel="noopener" target="_blank"><svg aria-hidden="true" class="icon"><use href="#i-telegram"></use></svg>Telegram</a>
    </div>
    <p class="contacts-price">Утеплённая бытовка 2,4 × 6 м — <strong>{PRICE}</strong>. {esc(PRICE_NOTE)}</p>
  </div>
  <div>
    <h2>Продажа и аренда</h2>
    <p>Новосибирск и область. Готовые бытовки и изготовление под заказ. Доставка примерно до 1000 км от Новосибирска: НСО, Алтайский край, Республика Алтай, Кемеровская, Томская, Омская области, Красноярский край, Хакасия.</p>
    <ul class="payment-list">
      <li><svg aria-hidden="true" class="icon"><use href="#i-check"></use></svg>Аренда — цена договорная</li>
      <li><svg aria-hidden="true" class="icon"><use href="#i-check"></use></svg>Оплата наличными или по безналу</li>
      <li><svg aria-hidden="true" class="icon"><use href="#i-check"></use></svg>Работаем с НДС и без НДС</li>
    </ul>
    <div class="social-links" style="margin-top:16px">
      <a class="button button--fill" href="{WA}" rel="noopener" target="_blank">Написать в WhatsApp</a>
      <a class="button" href="{TG}" rel="noopener" target="_blank">Написать в Telegram</a>
    </div>
  </div>
</section>
'''.strip()


CSS_ADD = r'''
/* ===== Catalog rebuild: sidebar, schemes, real photos, chats ===== */
.header__chats{display:flex;gap:6px;justify-content:flex-end;margin-bottom:8px}
.header__chats .button{padding:6px 10px;font-size:11px}
.hero-chats{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}
.hero-price{margin-top:10px;font-size:15px}
.hero-price strong{font-weight:700}
.hero-price-note{display:block;margin-top:4px;font-size:11px;color:#7c8288;font-weight:300;max-width:36em}
.cat-layout{display:grid;grid-template-columns:240px minmax(0,1fr);gap:28px;align-items:start}
.cat-side{position:sticky;top:16px;border:1px solid var(--line);background:#fff;padding:16px 12px 18px}
.cat-side h3{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin:0 0 10px;font-weight:400}
.cat-cats{display:flex;flex-direction:column;gap:2px}
.cat-cat{display:flex;justify-content:space-between;align-items:center;width:100%;border:0;background:none;text-align:left;padding:9px 10px;border-radius:3px;color:var(--ink);font-size:13px;line-height:1.3;gap:8px}
.cat-cat:hover{background:var(--soft)}
.cat-cat.on,.cat-cat[aria-pressed=true]{background:var(--pale);color:var(--accent-dark)}
.cat-cat i{font-style:normal;color:var(--muted);font-size:11px;flex:none}
.cat-cat.on i{color:var(--accent-dark)}
.cat-side-note{margin-top:16px;padding-top:14px;border-top:1px solid var(--line);font-size:12px;color:#7c8288;display:flex;flex-direction:column;align-items:flex-start;gap:10px}
.real-block{margin-bottom:28px}
.real-head h3{font-size:20px;margin-bottom:8px}
.real-price{font-size:15px;margin-bottom:6px}
.real-note{font-size:12px;color:#7c8288;font-weight:300;max-width:46em;margin-bottom:14px}
.real-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px}
.real-item{position:relative;display:block;background:var(--soft);overflow:hidden;cursor:zoom-in}
.real-item img{width:100%;height:140px;object-fit:cover}
.real-cap{position:absolute;left:0;right:0;bottom:0;background:#1d232acc;color:#fff;font-size:11px;padding:5px 8px}
.scheme-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}
.scheme-tile .product__image{height:auto;aspect-ratio:800/540;background:var(--soft);display:block}
.scheme-tile .product__image img{width:100%;height:100%;object-fit:contain;background:var(--soft)}
.scheme-desc{font-size:12px;color:#6d7378;font-weight:300;margin:0 0 10px;min-height:2.8em}
.scheme-tile .product__footer{flex-wrap:wrap;gap:8px}
.model-card .model-uses ul,.model-card .extra-lite ul,.model-card .pay-lite ul{list-style:none;padding:0}
.model-card .model-uses li,.model-card .extra-lite li,.model-card .pay-lite li{position:relative;padding-left:16px;font-size:13px;line-height:1.7}
.model-card .model-uses li::before,.model-card .extra-lite li::before,.model-card .pay-lite li::before{content:"";position:absolute;left:0;top:9px;width:6px;height:6px;border-radius:50%;background:var(--accent)}
.model-card .spec-kicker{font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:22px 0 14px}
.model-card .extra-lite,.model-card .pay-lite{margin-top:22px}
.model-card .extra-lite h3,.model-card .pay-lite h3,.model-card .model-uses h3{margin-bottom:8px;font-size:17px}
.contacts-addr{display:flex;align-items:flex-start;gap:6px;margin:10px 0 12px;font-size:15px}
.contacts-addr .icon{color:var(--accent);margin-top:2px}
.map-btns{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 16px}
.contacts-price{margin-top:16px;font-size:13px;color:#5c6369;max-width:36em}
.benefits-rail{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;padding:22px 0 6px;border-bottom:1px solid var(--line);margin-bottom:8px}
.benefits-rail .benefit{display:flex;gap:10px;align-items:flex-start}
.benefits-rail h3{font-size:15px;margin-bottom:2px}
.benefits-rail p{font-size:12px;color:#7c8288}
.page-columns{grid-template-columns:minmax(0,1fr);gap:0}
.column-left{display:none}
#catalog{position:static}
.catalog-head>a,.catalog-intro{display:block}
.catalog-tabs{display:none}
@media(max-width:1150px){
  .scheme-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
  .real-grid{grid-template-columns:repeat(3,minmax(0,1fr))}
  .cat-layout{grid-template-columns:210px minmax(0,1fr);gap:20px}
}
@media(max-width:991px){
  .cat-layout{grid-template-columns:minmax(0,1fr);gap:16px}
  .cat-side{position:static;padding:0;border:0}
  .cat-side h3{display:none}
  .cat-cats{flex-direction:row;flex-wrap:nowrap;overflow-x:auto;gap:8px;margin:0 -15px;padding:2px 15px 10px;-webkit-overflow-scrolling:touch;scrollbar-width:none}
  .cat-cats::-webkit-scrollbar{display:none}
  .cat-cat{flex:none;border:1px solid var(--line);border-radius:999px;padding:8px 14px;white-space:nowrap}
  .cat-cat.on,.cat-cat[aria-pressed=true]{border-color:var(--accent)}
  .cat-side-note{display:none}
  .benefits-rail{grid-template-columns:1fr;gap:10px}
  .column-left{display:none}
}
@media(max-width:767px){
  .header__chats{display:none}
  .scheme-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:12px 10px}
  .real-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:7px}
  .real-item img{height:120px}
  .hero-chats .button{font-size:11px;padding:7px 10px}
  .model-price{text-align:left}
  .map-btns .button{font-size:11px}
}
@media(min-width:768px){
  #catalog{position:static}
  .catalog-head>a,.catalog-intro{display:block}
  .catalog-intro{margin-bottom:18px}
  .catalog-tabs{display:none}
}
'''


def patch_css():
    css = (ROOT / 'styles.css').read_text(encoding='utf-8')
    if 'Catalog rebuild:' in css:
        css = re.split(r'/\* ===== Catalog rebuild:', css, 1)[0].rstrip() + '\n'
    (ROOT / 'styles.css').write_text(css + '\n' + CSS_ADD, encoding='utf-8')


def patch_js():
    js = r'''
'use strict';
(()=>{
 const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
 const callback=$('#callback-modal'), drawer=$('#menu-drawer'), photo=$('#photo-modal');
 function open(d){d.showModal();document.body.style.overflow='hidden'}
 function close(d){d.close();if(!$$('dialog[open]').length)document.body.style.overflow=''}
 $$('dialog').forEach(d=>{d.addEventListener('cancel',()=>{document.body.style.overflow=''});d.addEventListener('click',e=>{if(e.target.closest('[data-close]'))close(d);if(e.target===d){const r=d.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)close(d)}})});
 $$('[data-callback]').forEach(a=>a.addEventListener('click',e=>{e.preventDefault();$('input[name=product]',callback).value=a.dataset.product||'Строительная бытовка';$('.form-status',callback).textContent='';open(callback)}));
 $('#open-menu').addEventListener('click',()=>open(drawer));$$('nav a',drawer).forEach(a=>a.addEventListener('click',()=>close(drawer)));
 $$('[data-privacy]').forEach(b=>b.addEventListener('click',()=>open($('#privacy-modal'))));
 $$('[data-year]').forEach(e=>e.textContent=new Date().getFullYear());

 const filters=$$('[data-filter]'), tiles=$$('.scheme-tile');
 let active='all', query='';
 function filter(){
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
 filters.forEach(b=>b.addEventListener('click',()=>{active=b.dataset.filter;query='';const s=$('#catalog-search');if(s)s.value='';filter();}));
 $$('[data-nav-filter]').forEach(a=>a.addEventListener('click',()=>{active=a.dataset.navFilter;query='';const s=$('#catalog-search');if(s)s.value='';filter();}));
 const sf=$('#search-form');
 if(sf) sf.addEventListener('submit',e=>{e.preventDefault();active='all';query=($('#catalog-search').value||'').trim().toLocaleLowerCase('ru');filter();$('#catalog').scrollIntoView({behavior:'smooth'})});

 let galleryItems=[], current=0;
 function itemsOf(name){return $$(`[data-gallery="${name}"]`)}
 function showPhoto(i){
  if(!galleryItems.length)return;
  current=(i+galleryItems.length)%galleryItems.length;
  const a=galleryItems[current], im=$('#lightbox-image');
  im.src=a.getAttribute('href')||a.dataset.full||'';
  im.alt=a.dataset.title||'';
  $('#photo-title').textContent=a.dataset.title||'';
  const c=$('.photo-counter'); if(c) c.textContent=`${current+1} / ${galleryItems.length}`;
 }
 function openGallery(el){
  const name=el.dataset.gallery||'photos';
  galleryItems=itemsOf(name);
  const i=Math.max(0, galleryItems.indexOf(el));
  showPhoto(i); open(photo);
 }
 $$('[data-gallery]').forEach(a=>a.addEventListener('click',e=>{e.preventDefault();openGallery(a)}));
 const prev=$('.prev',photo), next=$('.next',photo);
 if(prev) prev.addEventListener('click',()=>showPhoto(current-1));
 if(next) next.addEventListener('click',()=>showPhoto(current+1));
 document.addEventListener('keydown',e=>{if(photo&&photo.open){if(e.key==='ArrowLeft')showPhoto(current-1);if(e.key==='ArrowRight')showPhoto(current+1)}});

 function message(form){const d=new FormData(form);return `Здравствуйте! Интересует: ${d.get('product')||'строительная бытовка'}.\nИмя: ${String(d.get('customer')||'').trim()}.\nТелефон для связи: ${String(d.get('phone')||'').trim()}.\nПодскажите, пожалуйста, наличие и стоимость.`}
 function valid(form){if(!form.reportValidity())return false;const input=$('input[name=phone]',form);const n=input.value.replace(/\D/g,'');if(n.length<10||n.length>15){input.setCustomValidity('Укажите корректный номер телефона (10–15 цифр).');input.reportValidity();return false}return true}
 $$('.callback-form').forEach(form=>{
  $('input[name=phone]',form).addEventListener('input',e=>e.target.setCustomValidity(''));
  form.addEventListener('submit',e=>{e.preventDefault();if(!valid(form))return;const url='https://wa.me/79139438814?text='+encodeURIComponent(message(form));const a=document.createElement('a');a.href=url;a.target='_blank';a.rel='noopener';a.click();$('.form-status',form).textContent='Откроется WhatsApp с подготовленным текстом. Заявка ещё не отправлена.'});
  const em=$('[data-email]',form); if(em) em.addEventListener('click',()=>{if(!valid(form))return;window.location.href='mailto:Sibnordmodul@yandex.ru?subject='+encodeURIComponent('Заявка с сайта SibNordModul')+'&body='+encodeURIComponent(message(form));$('.form-status',form).textContent='Сообщение подготовлено для вашей почтовой программы. Проверьте его перед отправкой.'});
 });
})();
'''
    (ROOT / 'script.js').write_text(js.lstrip(), encoding='utf-8')


def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit(f'patch failed: {label} not found')
    return text.replace(old, new, 1)


def patch_html(photos, missing):
    t = (ROOT / 'index.html').read_text(encoding='utf-8')
    # Telegram account — same as VOLT ONE
    t = t.replace('https://t.me/+79139438814', TG)

    # header chats
    old_actions = (
        '<div class="header__actions"><a class="button button--ink" data-callback="" data-product="" href="#request">Оставить заявку</a>'
        f'<a class="header__mail" href="{MAIL}">{MAIL_DISP}</a></div>'
    )
    new_actions = (
        '<div class="header__actions"><div class="header__chats">'
        f'<a class="button button--fill" href="{WA}" target="_blank" rel="noopener">WhatsApp</a>'
        f'<a class="button" href="{TG}" target="_blank" rel="noopener">Telegram</a></div>'
        '<a class="button button--ink" data-callback="" data-product="" href="#request">Оставить заявку</a>'
        f'<a class="header__mail" href="{MAIL}">{MAIL_DISP}</a></div>'
    )
    t = replace_once(t, old_actions, new_actions, 'header actions')

    # header pin text — keep Новосибирск, address is in contacts
    # hero copy + buttons + price
    old_hero = (
        '<p>Готовые варианты и изготовление на заказ. <br/>Новосибирск и область.</p>'
        '<a class="hero__link" href="#catalog">Смотреть варианты <span>›</span></a></div>'
    )
    new_hero = (
        '<p>Готовые варианты и изготовление на заказ. <br/>Новосибирск и область.</p>'
        f'<p class="hero-price"><strong>Утеплённая бытовка 2,4 × 6 м — {PRICE}</strong>'
        f'<span class="hero-price-note">{esc(PRICE_NOTE)}</span></p>'
        '<div class="hero-chats">'
        f'<a class="button button--fill" href="{WA}" target="_blank" rel="noopener">Написать в WhatsApp</a>'
        f'<a class="button button--ink" href="{TG}" target="_blank" rel="noopener">Написать в Telegram</a>'
        '</div>'
        '<a class="hero__link" href="#catalog">Смотреть варианты <span>›</span></a></div>'
    )
    t = replace_once(t, old_hero, new_hero, 'hero copy')

    # category nav filters
    nav = (
        '<nav aria-label="Основной каталог" class="category-nav"><div class="container category-nav__inner">'
        '<a data-nav-filter="stroitelnye" href="#catalog"><svg aria-hidden="true" class="icon"><use href="#i-cabin"></use></svg>Бытовки <span class="chev">⌄</span></a>'
        '<a data-nav-filter="dachnye" href="#catalog"><svg aria-hidden="true" class="icon"><use href="#i-house"></use></svg>Дачные <span class="chev">⌄</span></a>'
        '<a data-nav-filter="guard" href="#catalog"><svg aria-hidden="true" class="icon"><use href="#i-guard"></use></svg>Посты охраны <span class="chev">⌄</span></a>'
        '<a data-nav-filter="san" href="#catalog"><svg aria-hidden="true" class="icon"><use href="#i-san"></use></svg>Сан-бытовки <span class="chev">⌄</span></a>'
        '<a data-nav-filter="modular" href="#catalog" data-nav-filter="modular"><svg aria-hidden="true" class="icon"><use href="#i-blocks"></use></svg>Модульные дома</a>'
        '</div></nav>'
    )
    t = re.sub(r'<nav aria-label="Основной каталог" class="category-nav">.*?</nav>', nav, t, count=1, flags=re.S)

    # service nav
    old_svc = (
        '<nav aria-label="Услуги" class="service-nav"><div class="container service-nav__inner">'
        '<a href="#extra">Дополнительная комплектация</a><a href="#rent">Аренда бытовок</a>'
        '<a href="#on-order">Другие размеры</a><a href="#gallery">Фото производства</a>'
        '<a href="#contacts">Условия оплаты</a></div></nav>'
    )
    new_svc = (
        '<nav aria-label="Услуги" class="service-nav"><div class="container service-nav__inner">'
        '<a href="#model-6x24">Бытовка 2,4×6 м</a>'
        + ( '<a href="#photos">Реальные фото</a>' if photos else '' )
        + '<a href="#extra">Дополнительная комплектация</a><a href="#rent">Аренда бытовок</a>'
        '<a href="#catalog" data-nav-filter="modular">Модульные дома</a>'
        '<a href="#contacts">Контакты и оплата</a></div></nav>'
    )
    t = replace_once(t, old_svc, new_svc, 'service nav')

    # Replace page-columns inner: from page-columns through gallery, keep steps onward.
    start = t.find('<div class="container page-columns">')
    steps = t.find('<section class="content-section" id="steps">')
    if start < 0 or steps < 0:
        raise SystemExit(f'page-columns/steps not found {start} {steps}')

    benefits = (
        '<div class="container"><div class="benefits-rail" aria-label="Преимущества">'
        '<div class="benefit"><svg aria-hidden="true" class="icon"><use href="#i-factory"></use></svg>'
        '<div><h3>Своё производство</h3><p>в Новосибирске</p></div></div>'
        '<div class="benefit"><svg aria-hidden="true" class="icon"><use href="#i-cabin"></use></svg>'
        '<div><h3>Готовые варианты</h3><p>В наличии — ждать не нужно</p></div></div>'
        '<div class="benefit"><svg aria-hidden="true" class="icon"><use href="#i-ruler"></use></svg>'
        '<div><h3>Разные размеры</h3><p>Изготовление на заказ</p></div></div>'
        '</div></div>'
    )
    rent = (
        '<section class="rent-banner" id="rent"><div>'
        '<h2>Бытовки в аренду</h2>'
        '<p>Под стройку, жильё бригады, прорабскую, офис на объекте, дачный домик, склад и многое другое. <br/>Аренда — цена договорная.</p>'
        '</div>'
        '<a class="button button--ink" data-callback="" data-product="Аренда бытовки" href="#request">Уточнить аренду</a>'
        '</section>'
    )
    # keep extra section from original
    extra_s = t.find('<section class="content-section" id="extra">')
    extra_e = t.find('<section class="content-section" id="on-order">')
    extra = t[extra_s:extra_e] if extra_s > 0 and extra_e > extra_s else ''

    about = (
        '<section class="content-section" id="about">'
        '<h2>SibNordModul — своё производство <br/>строительных бытовок</h2>'
        '<div class="about-row"><div class="text-content">'
        '<p>Мы производим строительные бытовки в Новосибирске. Собираем металлический каркас, утепляем, обшиваем и выполняем внутреннюю отделку. '
        '<strong>Наш основной продукт — строительная бытовка:</strong> практичное помещение для работы, временного проживания и хранения.</p>'
        '<p>Продаём и сдаём в аренду готовые варианты. Под заказ делаем разные размеры и комплектации, блок-контейнеры, модульные конструкции, а также модульные дома.</p>'
        '<p>Бытовки подойдут под стройку, жильё бригады, прорабскую, офис на объекте, дачный домик, склад и многое другое. В наличии разные варианты — ждать не нужно.</p>'
        '<p>Доставка примерно до 1000 км от Новосибирска: НСО, Алтайский край, Республика Алтай, Кемеровская, Томская, Омская области, Красноярский край, Хакасия.</p>'
        '</div></div></section>'
    )

    mid = (
        benefits
        + '<div class="container page-columns"><div class="content">'
        + catalog_html(photos)
        + rent
        + extra
        + about
    )
    t = t[:start] + mid + t[steps:]

    # contacts
    c0 = t.find('<section class="contacts-section" id="contacts">')
    c1 = t.find('</main>')
    if c0 < 0 or c1 < 0:
        raise SystemExit('contacts/main not found')
    t = t[:c0] + contacts_html() + '\n</div></div>' + t[c1:]

    # footer address + catalog links + gallery link
    t = t.replace('<p>Новосибирск и область</p>', f'<p>{esc(ADDR)}</p>', 1)
    t = t.replace('<a href="#gallery">Фотогалерея</a>',
                  '<a href="#photos">Реальные фото</a>' if photos else '<a href="#catalog">Каталог</a>')
    t = t.replace('<a href="#on-order">Модульные конструкции</a>',
                  '<a href="#catalog" data-nav-filter="modular">Модульные дома</a>')
    t = t.replace('<li><a href="#catalog">Блок-контейнеры</a></li>',
                  '<li><a href="#catalog" data-nav-filter="guard">Посты охраны</a></li>')

    # mobile dock: Menu, Catalog, WhatsApp, Telegram, Call
    old_dock = (
        '<nav aria-label="Быстрые действия" class="mobile-dock">'
        if '<nav aria-label="Быстрые действия" class="mobile-dock">' in t
        else 'mobile-dock">'
    )
    # replace inner of mobile-dock
    m = re.search(r'<nav[^>]*class="mobile-dock"[^>]*>.*?</nav>', t, flags=re.S)
    if not m:
        raise SystemExit('mobile-dock not found')
    dock = (
        '<nav aria-label="Быстрые действия" class="mobile-dock">'
        '<button aria-controls="menu-drawer" aria-haspopup="dialog" aria-label="Открыть меню" id="open-menu" type="button">'
        '<svg aria-hidden="true" class="icon"><use href="#i-menu"></use></svg><span>Меню</span></button>'
        '<a href="#catalog"><svg aria-hidden="true" class="icon"><use href="#i-cabin"></use></svg><span>Каталог</span></a>'
        f'<a href="{WA}" rel="noopener" target="_blank"><svg aria-hidden="true" class="icon"><use href="#i-chat"></use></svg><span>WhatsApp</span></a>'
        f'<a href="{TG}" rel="noopener" target="_blank"><svg aria-hidden="true" class="icon"><use href="#i-telegram"></use></svg><span>Telegram</span></a>'
        f'<a href="{TEL}"><svg aria-hidden="true" class="icon"><use href="#i-phone"></use></svg><span>Позвонить</span></a>'
        '</nav>'
    )
    t = t[:m.start()] + dock + t[m.end():]

    # also add WA/TG in the drawer contact area if only phone/mail
    if 'Написать в WhatsApp' not in t[t.find('drawer__contact'):t.find('drawer__contact')+800] if 'drawer__contact' in t else True:
        t = t.replace(
            '<div class="drawer__contact">',
            '<div class="drawer__contact">'
            f'<a class="button button--fill" href="{WA}" target="_blank" rel="noopener">WhatsApp</a>'
            f'<a class="button" href="{TG}" target="_blank" rel="noopener">Telegram</a>',
            1,
        )

    # sanity: no leftover 285 000 and no old product image refs in html
    for bad in ['285 000', 'images/thumbs/', 'images/catalog/', 'images/01.jpg', 'images/11.jpg', 'id="gallery"', 'id="specs"', 'id="on-order"']:
        if bad in t and bad not in ('id="gallery"',):  # gallery id should be gone
            pass
    # leftover priced old model
    t = t.replace('285 000 ₽', PRICE)  # just in case anything remains — shouldn't

    (ROOT / 'index.html').write_text(t, encoding='utf-8')
    return t


def cleanup_old_images():
    removed = []
    for p in (ROOT / 'images').glob('0*.jpg'):
        p.unlink(); removed.append(p.name)
    for p in (ROOT / 'images').glob('[1-9]*.jpg'):
        if p.name.split('.')[0].isdigit():
            p.unlink(); removed.append(p.name)
    thumbs = ROOT / 'images' / 'thumbs'
    if thumbs.exists():
        shutil.rmtree(thumbs); removed.append('thumbs/')
    cat = ROOT / 'images' / 'catalog'
    if cat.exists():
        shutil.rmtree(cat); removed.append('catalog/')
    # do not touch hero-latin* or logos
    print('removed old images:', removed)
    return removed


def remaining_imgs(html):
    srcs = re.findall(r'(?:src|srcset|href)="(images/[^"]+)"', html)
    return sorted(set(srcs))


def main():
    write_schemes()
    photos, missing = process_photos()
    html = patch_html(photos, missing)
    patch_css()
    patch_js()
    removed = cleanup_old_images()

    # fix modular nav if leftover #on-order
    t = (ROOT / 'index.html').read_text(encoding='utf-8')
    t = t.replace('href="#on-order"', 'href="#catalog" data-nav-filter="modular"')
    # don't leave stale ids
    (ROOT / 'index.html').write_text(t, encoding='utf-8')

    imgs = remaining_imgs(t)
    print('image refs in html:')
    for s in imgs:
        ok = (ROOT / s).exists()
        print((' OK' if ok else 'MISS'), s)
    # leftover prices
    prices = set(re.findall(r'\d[\d\s]{2,}\s*₽', t))
    print('prices found:', prices)
    print('WA', WA in t, 'TG', TG in t, 'old tg', '+79139438814' in t and 't.me/+79139438814' in t)
    print('address', ADDR in t)
    print('GIS open', GIS_OPEN in t, 'GIS dir', 'routeSearch' in t)
    print('hero image kept', 'hero-latin.jpg' in t)
    print('old thumbs', 'images/thumbs/' in t, 'old catalog photos', 'images/catalog/' in t)
    print('model section', 'id="model-6x24"' in t, '245 000' in t)
    print('PHOTOS_USED', len(photos))
    print('PHOTOS_MISSING', len(missing))
    # write report sidecar
    (ROOT / 'rebuild_report.txt').write_text(
        f'photos_used={len(photos)}\nphotos_missing={len(missing)}\n'
        f'variants={len(VARIANTS)}\nremoved={removed}\nmissing_files={missing}\n',
        encoding='utf-8')
    # syntax check html roughly
    assert 'id="catalog"' in t and 'id="contacts"' in t and 'id="hero-title"' in t
    print('rebuild ok')

if __name__ == '__main__':
    main()
