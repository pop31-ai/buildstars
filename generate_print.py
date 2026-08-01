"""
ЗВЕЗДА СТРОИТЕЛЕЙ - генератор файлов для печати.

Печать:
  - board_a2.pdf  - поле-звезда, формат A2 (420x594 мм)
  - cards_a4.pdf  - карты стройматериалов + события (A4, 9 карт на лист)
  - pawns_a4.pdf  - 8 фишек-жетонов + подставки (A4)
  - dice_a4.pdf   - развёртка кубика d6 (A4)
  - rules_a4.pdf  - краткие правила (A4)

Запуск:
  python generate_print.py
"""

import math
import os
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(__file__), "print")
os.makedirs(OUT, exist_ok=True)

MM = 300 / 25.4          # пикселей в миллиметре (300 dpi)
FONT_DIR = "C:\\Windows\\Fonts"

# ---- форматы листов, px ----
A2_W, A2_H = int(420 * MM), int(594 * MM)
A4_W, A4_H = int(210 * MM), int(297 * MM)

# ---- цвета ----
PLAYER_COLORS = [
    (38, 104, 201),   # Синий строитель
    (44, 162, 95),    # Зелёный строитель
    (222, 62, 52),    # Красный строитель
    (226, 169, 37),   # Золотой строитель
]
PLAYER_NAMES = ["СИНИЙ", "ЗЕЛЁНЫЙ", "КРАСНЫЙ", "ЗОЛОТОЙ"]
MAT_COLORS = {
    "BRICK": (189, 66, 46),
    "WOOD": (159, 112, 56),
    "STEEL": (110, 121, 136),
    "GLASS": (64, 152, 201),
}
MAT_NAMES = {
    "BRICK": "КИРПИЧ",
    "WOOD": "ДЕРЕВО",
    "STEEL": "СТАЛЬ",
    "GLASS": "СТЕКЛО",
}
PAPER = (244, 246, 250)
BLUE_LINE = (150, 180, 215)

# ---- геометрия звезды (мм, центр в (210, 320) листа A2) ----
CX, CY = 210, 320
ROUT, RIN = 185, 120


def star_vertices():
    v = []
    for i in range(8):
        a = math.radians(90 - i * 45)
        rr = ROUT if i % 2 == 0 else RIN
        v.append((CX + rr * math.cos(a), CY - rr * math.sin(a)))
    return v


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


MAT_ROT = ["BRICK", "WOOD", "STEEL", "GLASS"]  # 4 типа


def cell_layout():
    """Список клеток: (индекс, x_mm, y_mm, тип, доп). Порядок по часовой."""
    v = star_vertices()
    cells = []
    for s in range(4):
        va, vb = v[2 * s], v[2 * s + 1]
        vc = v[(2 * s + 2) % 8]
        # ребро вниз: tip -> valley
        p1 = lerp(va, vb, 0.27)
        p2 = lerp(va, vb, 0.50)
        p3 = lerp(va, vb, 0.73)
        # ребро вверх: valley -> next tip
        q1 = lerp(vb, vc, 0.27)
        q2 = lerp(vb, vc, 0.50)
        q3 = lerp(vb, vc, 0.73)
        m = MAT_ROT  # [BRICK, WOOD, STEEL, GLASS]
        row = [("BASE", s), ("MAT", m[0]), ("EVENT", None), ("MAT", m[1]),
               ("FWD", 2), ("MAT", m[2]), ("BACK", 2), ("MAT", m[3])]
        pos = [va, p1, p2, p3, vb, q1, q2, q3]
        for k in range(8):
            typ, extra = row[k]
            cells.append((s * 8 + k, pos[k][0], pos[k][1], typ, extra))
    return cells


def mm(v):
    return int(v * MM)


# ---- шрифты ----
def font(size, bold=False):
    name = "arialbd.ttf" if bold else "arial.ttf"
    return ImageFont.truetype(os.path.join(FONT_DIR, name), mm(size))


def text_w(draw, s, f):
    b = draw.textbbox((0, 0), s, font=f)
    return b[2] - b[0]


def text_h(draw, s, f):
    b = draw.textbbox((0, 0), s, font=f)
    return b[3] - b[1]


def centered(draw, cx, cy, s, f, fill):
    w = text_w(draw, s, f)
    draw.text((cx - w / 2, cy), s, font=f, fill=fill)


def rr(draw, box, rad, fill=None, outline=None, width=1):
    draw.rounded_rectangle(box, radius=rad, fill=fill, outline=outline, width=width)


# ---- иконки ----
def icon_brick(d, cx, cy, r):
    brick_w, brick_h = r * 0.42, r * 0.26
    x0, y0 = cx - brick_w * 1.5, cy - brick_h * 1.05
    for row in range(2):
        off = brick_w * 0.5 if row % 2 else 0
        for col in range(3):
            x = x0 + col * brick_w + off
            y = y0 + row * (brick_h + r * 0.06)
            rr(d, [x, y, x + brick_w - 1, y + brick_h - 1], 2,
               fill=(178, 62, 44), outline=(120, 40, 30), width=1)


def icon_wood(d, cx, cy, r):
    w, h = r * 1.15, r * 0.22
    x0, y0 = cx - w / 2, cy - h * 1.1
    for i in range(3):
        y = y0 + i * (h + r * 0.12)
        rr(d, [x0, y, x0 + w, y + h], 2, fill=(170, 120, 62), outline=(110, 76, 40), width=1)
        d.line([(x0 + w * 0.3, y + 1), (x0 + w * 0.85, y + h - 1)], fill=(135, 92, 48), width=1)


def icon_steel(d, cx, cy, r):
    flange, web, gap = r * 0.5, r * 0.22, r * 0.22
    x0 = cx - flange / 2
    d.rectangle([x0, cy - r * 0.72, x0 + flange, cy - r * 0.72 + r * 0.2], fill=(126, 138, 154), outline=(70, 80, 94))
    d.rectangle([x0, cy + r * 0.72 - r * 0.2, x0 + flange, cy + r * 0.72], fill=(126, 138, 154), outline=(70, 80, 94))
    d.rectangle([cx - web / 2, cy - r * 0.52, cx + web / 2, cy + r * 0.52], fill=(140, 152, 168), outline=(70, 80, 94))
    for dy in (-r * 0.35, 0, r * 0.35):
        d.ellipse([cx - web / 2 - 1, cy + dy - 2, cx - web / 2 + 2, cy + dy + 2], fill=(70, 80, 94))
        d.ellipse([cx + web / 2 - 2, cy + dy - 2, cx + web / 2 + 1, cy + dy + 2], fill=(70, 80, 94))


def icon_glass(d, cx, cy, r):
    pane = r * 0.34
    gap = r * 0.12
    x0, y0 = cx - pane - gap / 2, cy - pane - gap / 2
    for iy in range(2):
        for ix in range(2):
            x = x0 + ix * (pane + gap)
            y = y0 + iy * (pane + gap)
            rr(d, [x, y, x + pane, y + pane], 2, fill=(120, 190, 228), outline=(255, 255, 255), width=2)
    d.line([(cx - r * 0.5, cy - r * 0.6), (cx + r * 0.55, cy - r * 0.1)], fill=(255, 255, 255), width=3)


def icon_event(d, cx, cy, r):
    rr(d, [cx - r * 0.62, cy - r * 0.85, cx + r * 0.62, cy + r * 0.85], r * 0.12,
       fill=(140, 96, 190), outline=(95, 60, 135), width=2)
    d.text((cx, cy - r * 0.55), "?", font=font(0.95 * r, True), fill=(255, 255, 255))


def icon_chevron(d, cx, cy, r, forward=True):
    s = 1 if forward else -1
    color = (56, 66, 84)
    for k in range(2):
        x = cx + s * (k * r * 0.42 - r * 0.28)
        d.polygon([(x + s * r * 0.3, cy), (x, cy - r * 0.5), (x + s * r * 0.16, cy - r * 0.5),
                   (x + s * r * 0.62, cy), (x + s * r * 0.16, cy + r * 0.5), (x, cy + r * 0.5)],
                  fill=color)


def icon_helmet(d, cx, cy, r, color):
    d.arc([cx - r, cy - r, cx + r, cy + r], 0, 180, fill=color, width=mm(1.6))
    d.rectangle([cx - r, cy - r * 0.12, cx + r, cy - r * 0.12 + mm(1.6)], fill=color)
    for i in range(5):
        x = cx - r + (i + 0.5) * (2 * r / 5)
        d.rectangle([x - mm(0.5), cy - r * 0.05, x + mm(0.5), cy + r * 0.12], fill=(255, 255, 255))


def icon_tower(d, cx, cy, w, h, floors, fill_empty=(235, 238, 243)):
    """Колонна башни из `floors` этажей, возвращает список центров этажей."""
    cx = int(cx); cy = int(cy); w = int(w); h = int(h)
    x0, y0 = cx - w / 2, cy - h / 2
    fh = h / floors
    centers = []
    for i in range(floors):
        y = y0 + i * fh + fh * 0.06
        rr(d, [x0, y, x0 + w, y + fh * 0.88], 3, fill=fill_empty,
           outline=(120, 130, 145), width=mm(0.8))
        d.text((x0 + 2, y + fh * 0.24), str(i + 1), font=font(fh * 0.4, True), fill=(120, 130, 145))
        centers.append((cx, y + fh * 0.44))
    # крыша
    d.polygon([(x0 - w * 0.08, y0), (cx, y0 - h * 0.14), (x0 + w * 1.08, y0)], fill=(200, 90, 70))
    return centers


# ============================ ПОЛЕ A2 ============================
def draw_board():
    img = Image.new("RGB", (A2_W, A2_H), PAPER)
    d = ImageDraw.Draw(img)

    # фон-чертёж
    for x in range(0, A2_W, mm(10)):
        d.line([(x, 0), (x, A2_H)], fill=(236, 241, 248), width=1)
    for y in range(0, A2_H, mm(10)):
        d.line([(0, y), (A2_W, y)], fill=(236, 241, 248), width=1)

    # заголовок
    t1 = font(34, True)
    centered(d, A2_W / 2, mm(16), "ЗВЕЗДА СТРОИТЕЛЕЙ", t1, (24, 34, 56))
    d.rectangle([A2_W / 2 - mm(70), mm(34), A2_W / 2 + mm(70), mm(35.2)], fill=(226, 169, 37))
    centered(d, A2_W / 2, mm(42), "Строй башню, обойди звезду, вернись первым на базу",
             font(9), (90, 100, 120))

    # контур звезды (подложка)
    v = star_vertices()
    star_pts = [(x * MM, y * MM) for x, y in v]
    d.polygon(star_pts, fill=(224, 232, 244), outline=(160, 180, 210), width=mm(1.2))

    # водяной знак - маленькая звезда в центре
    wm = [(CX + rr * math.cos(math.radians(90 - i * 45)) * 0.42,
           CY - rr * math.sin(math.radians(90 - i * 45)) * 0.42)
          for i, rr in enumerate([90, 58] * 4)]
    d.polygon([(x * MM, y * MM) for x, y in wm], fill=(210, 222, 240))

    cells = cell_layout()
    for idx, x, y, typ, extra in cells:
        px, py = x * MM, y * MM
        if typ == "BASE":
            r = mm(20)
            col = PLAYER_COLORS[extra]
            d.ellipse([px - r, py - r, px + r, py + r], fill=col, outline=(255, 255, 255), width=mm(2))
            d.ellipse([px - r + mm(3), py - r + mm(3), px + r - mm(3), py + r - mm(3)],
                      outline=(255, 255, 255), width=mm(0.8))
            centered(d, px, py - mm(6), "БАЗА", font(9, True), (255, 255, 255))
            centered(d, px, py + mm(4), PLAYER_NAMES[extra], font(6, True), (255, 255, 255))
        elif typ == "MAT":
            r = mm(14.5)
            col = MAT_COLORS[extra]
            d.ellipse([px - r, py - r, px + r, py + r], fill=(255, 255, 255), outline=col, width=mm(1.6))
            icon_map[extra](d, px, py, mm(10.5))
        elif typ == "EVENT":
            r = mm(14.5)
            d.ellipse([px - r, py - r, px + r, py + r], fill=(240, 231, 250), outline=(140, 96, 190), width=mm(1.6))
            icon_event(d, px, py, mm(10))
        elif typ == "FWD":
            r = mm(14.5)
            d.ellipse([px - r, py - r, px + r, py + r], fill=(233, 239, 246), outline=(90, 108, 130), width=mm(1.6))
            icon_chevron(d, px, py, mm(8.5), True)
        elif typ == "BACK":
            r = mm(14.5)
            d.ellipse([px - r, py - r, px + r, py + r], fill=(233, 239, 246), outline=(90, 108, 130), width=mm(1.6))
            icon_chevron(d, px, py, mm(8.5), False)

    # номера клеток (мелкие, у внешнего края)
    for idx, x, y, typ, extra in cells:
        px, py = x * MM, y * MM
        d.text((px - mm(3), py + mm(16) if y > CY else py - mm(22)),
               str(idx + 1), font=font(4.5), fill=(150, 160, 175))

    # башни игроков (внутри лучей)
    v = star_vertices()
    for s in range(4):
        tip = v[2 * s]
        dx, dy = tip[0] - CX, tip[1] - CY
        L = math.hypot(dx, dy)
        ux, uy = dx / L, dy / L
        base = 0.46 * ROUT
        for k, dist in enumerate([base, base + 0.12 * ROUT, base + 0.24 * ROUT]):
            tx = CX + ux * dist
            ty = CY + uy * dist
            w, h = mm(15), mm(10)
            col = PLAYER_COLORS[s]
            x0, y0 = tx * MM - w / 2, ty * MM - h / 2
            rr(d, [x0, y0, x0 + w, y0 + h], 3, fill=(255, 255, 255),
               outline=col, width=mm(1.4))
            d.text((x0 + w / 2 - mm(3), y0 + h / 2 - mm(3.2)), str(k + 1), font=font(6, True), fill=col)
        # кран-силуэт на башне
        tx = CX + ux * base - uy * mm(4)
        ty = CY + uy * base + ux * mm(4)
        d.polygon([(tx * MM, ty * MM), (tx * MM - uy * mm(1.6) - ux * mm(0), ty * MM - ux * mm(1.6) + uy * mm(0))],
                  fill=(0, 0, 0))  # место под кран - упрощённо
    # маленький кран рядом с башней: палка с крюком
    for s in range(4):
        tip = v[2 * s]
        dx, dy = tip[0] - CX, tip[1] - CY
        L = math.hypot(dx, dy)
        ux, uy = dx / L, dy / L
        bx = CX + ux * (0.46 * ROUT) - uy * mm(10)
        by = CY + uy * (0.46 * ROUT) + ux * mm(10)
        px1 = (bx - ux * mm(6)) * MM
        py1 = (by - uy * mm(6)) * MM
        px2 = (bx + ux * mm(8)) * MM
        py2 = (by + uy * mm(8)) * MM
        d.line([(px1, py1), (px2, py2)], fill=(90, 100, 115), width=mm(1.2))
        d.line([(px2, py2), (px2 + uy * mm(4), py2 - ux * mm(4))], fill=(90, 100, 115), width=mm(1.2))
        d.ellipse([px2 + uy * mm(4) - mm(1.2), py2 - ux * mm(4) - mm(1.2),
                   px2 + uy * mm(4) + mm(1.2), py2 - ux * mm(4) + mm(1.2)],
                  fill=(200, 90, 70))

    # Мэрия (центр)
    R = mm(62)
    d.ellipse([CX * MM - R, CY * MM - R, CX * MM + R, CY * MM + R],
              fill=(255, 255, 255), outline=(160, 180, 210), width=mm(2))
    centered(d, CX * MM, CY * MM - mm(22), "МЭРИЯ", font(13, True), (24, 34, 56))
    centered(d, CX * MM, CY * MM - mm(10), "Обойди звезду и построй башню", font(5.6), (110, 118, 132))
    centered(d, CX * MM, CY * MM - mm(3), "Этаж = 3 материала", font(6, True), (200, 90, 70))
    centered(d, CX * MM, CY * MM + mm(6), "Событие  Вперёд  Назад", font(5), (140, 148, 160))
    centered(d, CX * MM, CY * MM + mm(13), "Здесь лежит кубик", font(5), (140, 148, 160))
    d.ellipse([CX * MM - mm(14), CY * MM + mm(22), CX * MM + mm(14), CY * MM + mm(50)],
              outline=(160, 180, 210), width=mm(1.2))

    # нижняя легенда
    y0 = mm(552)
    legend_items = [
        ("MAT_BRICK", "Склад кирпича - возьми 1 кирпич"),
        ("MAT_WOOD", "Лесопилка - возьми 1 дерево"),
        ("MAT_STEEL", "Металлург - возьми 1 сталь"),
        ("MAT_GLASS", "Стеклодув - возьми 1 стекло"),
        ("EVENT", "Событие - возьми карту"),
        ("FWD", "Стрелка вперёд - иди на 2 вперёд"),
        ("BACK", "Стрелка назад - вернись на 2"),
        ("BASE", "База - +1 материал и построй этаж за 3 материала"),
    ]
    x = mm(20)
    for key, txt in legend_items:
        d.ellipse([x, y0, x + mm(9), y0 + mm(9)], fill=(255, 255, 255),
                  outline=(160, 170, 185), width=mm(0.8))
        if key == "MAT_BRICK":
            icon_brick(d, x + mm(4.5), y0 + mm(4.5), mm(3.2))
        elif key == "MAT_WOOD":
            icon_wood(d, x + mm(4.5), y0 + mm(4.5), mm(3.2))
        elif key == "MAT_STEEL":
            icon_steel(d, x + mm(4.5), y0 + mm(4.5), mm(3.2))
        elif key == "MAT_GLASS":
            icon_glass(d, x + mm(4.5), y0 + mm(4.5), mm(3.2))
        elif key == "EVENT":
            icon_event(d, x + mm(4.5), y0 + mm(4.5), mm(3.2))
        elif key == "FWD":
            icon_chevron(d, x + mm(4.5), y0 + mm(4.5), mm(3.2), True)
        elif key == "BACK":
            icon_chevron(d, x + mm(4.5), y0 + mm(4.5), mm(3.2), False)
        else:
            d.ellipse([x + mm(2.5), y0 + mm(2.5), x + mm(6.5), y0 + mm(6.5)],
                      fill=PLAYER_COLORS[0], outline=(255, 255, 255))
        d.text((x + mm(12), y0 + mm(1)), txt, font=font(5.6), fill=(70, 78, 92))
        x += mm(2) + max(text_w(d, txt, font(5.6)), mm(60)) + mm(10)

    d.rectangle([mm(20), y0 - mm(6), mm(400), y0 + mm(16)], outline=(190, 200, 215), width=mm(0.8))

    img.save(os.path.join(OUT, "board_a2.png"))
    return img


icon_map = {"BRICK": icon_brick, "WOOD": icon_wood, "STEEL": icon_steel, "GLASS": icon_glass}


# ============================ КАРТЫ ============================
CARD_W, CARD_H = 56, 86
COLS, ROWS = 3, 3
MARGIN = 12
GAP = 5


def card_box(page, i):
    c, r = i % COLS, i // COLS
    x = MARGIN + c * (CARD_W + GAP)
    y = MARGIN + r * (CARD_H + GAP)
    return mm(x), mm(y)


def draw_card_back(d, x, y, title, sub, fill, accent):
    rr(d, [x + mm(1), y + mm(1), x + mm(CARD_W - 1), y + mm(CARD_H - 1)], mm(3), fill=fill)
    rr(d, [x + mm(1), y + mm(1), x + mm(CARD_W - 1), y + mm(CARD_H - 1)], mm(3), outline=accent, width=mm(1.2))
    centered(d, x + mm(CARD_W / 2), y + mm(10), title, font(8, True), (255, 255, 255))
    centered(d, x + mm(CARD_W / 2), y + mm(18), sub, font(5), (255, 255, 255))


def material_cards_page(colors, names):
    page = Image.new("RGB", (A4_W, A4_H), (255, 255, 255))
    d = ImageDraw.Draw(page)
    # рубашки
    for i in range(9):
        x, y = card_box(page, i)
        col = colors[i % len(colors)]
        draw_card_back(d, x, y, names[i % len(names)], "1 карта материала", col, (255, 255, 255))
    # лицевые стороны
    for i in range(9):
        x, y = card_box(page, i)
        col = colors[i % len(colors)]
        rr(d, [x + mm(1), y + mm(1), x + mm(CARD_W - 1), y + mm(CARD_H - 1)], mm(3),
           fill=(255, 255, 255), outline=col, width=mm(1.2))
        icon_map[["BRICK", "WOOD", "STEEL", "GLASS"][i % 4]](d, x + mm(28), y + mm(30), mm(11))
        centered(d, x + mm(CARD_W / 2), y + mm(58), names[i % len(names)], font(9, True), col)
        centered(d, x + mm(CARD_W / 2), y + mm(66), "1 материал", font(6), (120, 128, 140))
    return page


EVENTS = [
    ("Поставка", "+2 материала", 3),
    ("Ассортимент", "+1 материал каждого типа", 2),
    ("Попутный ветер", "Передвинься на 3 вперёд", 2),
    ("Яма на дороге", "Вернись на 3 назад", 2),
    ("Выходной", "Пропусти ход", 2),
    ("Клад", "+3 материала", 1),
    ("Скоростной режим", "Передвинься на 5 вперёд", 1),
    ("Авария", "Вернись на 5 назад", 1),
    ("Двойная смена", "Брось кубик ещё раз и двигайся", 1),
    ("Потерянный ящик", "Отдай 1 материал в банк", 1),
]


def event_cards_pages():
    deck = []
    for name, effect, count in EVENTS:
        for _ in range(count):
            deck.append((name, effect))
    pages = []
    for start in range(0, len(deck), 9):
        page = Image.new("RGB", (A4_W, A4_H), (255, 255, 255))
        d = ImageDraw.Draw(page)
        chunk = deck[start:start + 9]
        for i, (name, effect) in enumerate(chunk):
            x, y = card_box(page, i)
            # рубашка
            rr(d, [x + mm(1), y + mm(1), x + mm(CARD_W - 1), y + mm(CARD_H - 1)], mm(3),
               fill=(140, 96, 190))
            icon_event(d, x + mm(28), y + mm(28), mm(10))
            centered(d, x + mm(28), y + mm(50), "СОБЫТИЕ", font(6, True), (255, 255, 255))
            # лицо
            rr(d, [x + mm(CARD_W + 2), y + mm(1), x + mm(2 * CARD_W - 1), y + mm(CARD_H - 1)], mm(3),
               fill=(245, 240, 252), outline=(140, 96, 190), width=mm(1.2))
            fx, fy = x + mm(CARD_W + 2), y + mm(1)
            centered(d, fx + mm(27), fy + mm(12), "СОБЫТИЕ", font(7, True), (140, 96, 190))
            d.rectangle([fx + mm(6), fy + mm(18), fx + mm(48), fy + mm(19.5)], fill=(140, 96, 190))
            lines = []
            s = effect
            while s:
                cut = s
                while cut and text_w(d, cut, font(6.5)) > mm(44):
                    cut = cut.rsplit(" ", 1)[0]
                lines.append(cut)
                s = s[len(cut):].strip()
            for j, ln in enumerate(lines[:4]):
                centered(d, fx + mm(27), fy + mm(30) + j * mm(9), ln, font(6.5), (60, 52, 80))
            centered(d, fx + mm(27), fy + mm(72), name, font(7, True), (140, 96, 190))
        pages.append(page)
    return pages


# ============================ ФИШКИ ============================
PAWNS = [
    ("Башенный кран", (236, 118, 34)),
    ("Экскаватор", (60, 60, 60)),
    ("Бульдозер", (180, 140, 40)),
    ("Самосвал", (200, 90, 40)),
    ("Автокран", (80, 150, 220)),
    ("Миксер", (150, 90, 60)),
    ("Каток", (120, 160, 90)),
    ("Подъёмник", (170, 90, 160)),
]


def pawns_page():
    page = Image.new("RGB", (A4_W, A4_H), (255, 255, 255))
    d = ImageDraw.Draw(page)
    centered(d, A4_W / 2, mm(8), "ФИШКИ-СТРОЙТЕХНИКА", font(14, True), (30, 40, 60))
    centered(d, A4_W / 2, mm(16), "вырежи жетон, наклей на картон или вставь в подставку", font(6), (120, 128, 140))
    R = mm(15)
    for i, (name, col) in enumerate(PAWNS):
        c, r = i % 4, i // 4
        cx = MARGIN + mm(2) + c * (mm(46)) + mm(19)
        cy = mm(34) + r * (mm(44)) + mm(15)
        d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=col, outline=(40, 40, 40), width=mm(1.5))
        d.ellipse([cx - R + mm(3), cy - R + mm(3), cx + R - mm(3), cy + R - mm(3)],
                  outline=(255, 255, 255), width=mm(1))
        icon_helmet(d, cx, cy, mm(7.5), (255, 214, 90))
        centered(d, cx, cy + mm(22), str(i + 1), font(9, True), (40, 40, 40))
        centered(d, cx, cy + mm(30), name, font(5.2), (70, 78, 92))
    # подставки
    centered(d, A4_W / 2, mm(128), "ПОДСТАВКИ (сложить треугольником)", font(8, True), (30, 40, 60))
    for i in range(4):
        x = MARGIN + i * mm(47)
        y = mm(136)
        rr(d, [x, y, x + mm(42), y + mm(16)], mm(2), outline=(90, 100, 115), width=mm(1))
        d.text((x + mm(2), y + mm(5)), f"фишка {i + 1}", font=font(5), fill=(90, 100, 115))
    return page


# ============================ КУБИКИ ============================
def dice_page():
    page = Image.new("RGB", (A4_W, A4_H), (255, 255, 255))
    d = ImageDraw.Draw(page)
    centered(d, A4_W / 2, mm(10), "КУБИКИ d6", font(14, True), (30, 40, 60))
    centered(d, A4_W / 2, mm(18), "вырежи по контуру, сложи по линиям, склей клапаны", font(6), (120, 128, 140))
    side = mm(15)
    for die in range(2):
        ox = mm(55) + die * mm(95)
        oy = mm(42)
        # сетка: 4 в крест + 1
        faces = {(0, 1): 1, (1, 0): 3, (1, 1): 5, (2, 1): 2, (1, 2): 4}
        for (fx, fy), val in faces.items():
            x = ox + fx * side
            y = oy + fy * side
            rr(d, [x, y, x + side, y + side], mm(2.5), outline=(40, 50, 70), width=mm(1.2))
            pips = [(px, py) for px in range(3) for py in range(3)][:val]
            for px, py in pips:
                d.ellipse([x + side / 2 + (px - 1) * mm(4.5) - mm(1.6),
                           y + side / 2 + (py - 1) * mm(4.5) - mm(1.6),
                           x + side / 2 + (px - 1) * mm(4.5) + mm(1.6),
                           y + side / 2 + (py - 1) * mm(4.5) + mm(1.6)], fill=(40, 50, 70))
        # клапаны
        for fx, fy in [(0, 1), (1, 0), (2, 1), (1, 2)]:
            x = ox + fx * side
            y = oy + fy * side
            rr(d, [x + side / 4, y - mm(4.5), x + 3 * side / 4, y], mm(1.5), outline=(120, 128, 140), width=mm(0.8))
            rr(d, [x + side / 4, y + side, x + 3 * side / 4, y + side + mm(4.5)], mm(1.5), outline=(120, 128, 140), width=mm(0.8))
        centered(d, ox + side * 1.5, oy + mm(78), f"кубик {die + 1}", font(7, True), (40, 50, 70))
    return page


# ============================ ПРАВИЛА ============================
def rules_page():
    img = Image.new("RGB", (A4_W, A4_H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    x = mm(18)
    y = mm(14)
    lines = [
        ("ЗВЕЗДА СТРОИТЕЛЕЙ - правила", 14, True, (24, 34, 56)),
        ("Цель: первым обойти звезду по кругу и вернуться на базу с башней из 3 этажей.", 8, False, (40, 48, 64)),
        ("Этаж строится за 3 любых материала.", 8, True, (200, 90, 70)),
        ("", 6, False, (0, 0, 0)),
        ("Подготовка:", 9, True, (24, 34, 56)),
        ("1. Выбери фишку и цвет, поставь её на свою базу (луч звезды).", 7.5, False, (60, 68, 84)),
        ("2. Возьми 2 стартовых материала на выбор.", 7.5, False, (60, 68, 84)),
        ("3. Перемешай карты Событий.", 7.5, False, (60, 68, 84)),
        ("4. Первым ходит тот, кто выбросит больше на кубике.", 7.5, False, (60, 68, 84)),
        ("", 6, False, (0, 0, 0)),
        ("Ход (по шагам):", 9, True, (24, 34, 56)),
        ("1. Брось кубик.", 7.5, False, (60, 68, 84)),
        ("2. Передвинь фишку по часовой стрелке на выпавшую сумму.", 7.5, False, (60, 68, 84)),
        ("3. Выполни действие клетки, на которую встал.", 7.5, False, (60, 68, 84)),
        ("Если прошёл свою базу - реши, строить ли этаж.", 7.5, True, (200, 90, 70)),
        ("", 6, False, (0, 0, 0)),
        ("Клетки:", 9, True, (24, 34, 56)),
        ("Склад (кирпич/дерево/сталь/стекло) - возьми 1 карту материала.", 7.5, False, (60, 68, 84)),
        ("Событие - возьми верхнюю карту Событий и выполни её.", 7.5, False, (60, 68, 84)),
        ("Стрелка вперёд/назад - передвинься на 2 клетки (без действия новой клетки).", 7.5, False, (60, 68, 84)),
        ("База: встал ровно - получи +1 материал. Можно строить этаж за 3 материала.", 7.5, False, (60, 68, 84)),
        ("За один проход базы - только 1 этаж.", 7.5, True, (200, 90, 70)),
        ("", 6, False, (0, 0, 0)),
        ("Победа:", 9, True, (24, 34, 56)),
        ("Вернись на базу с построенной башней из 3 этажей - ты победил.", 7.5, True, (200, 90, 70)),
        ("", 6, False, (0, 0, 0)),
        ("Варианты:", 9, True, (24, 34, 56)),
        ("Начинающим: старт 4 материала, башня 2 этажа.", 7.5, False, (60, 68, 84)),
        ("Опытным: башня 5 этажей, проходя чужую базу - плати 1 материал.", 7.5, False, (60, 68, 84)),
    ]
    for txt, sz, b, col in lines:
        d.text((x, y), txt, font=font(sz, b), fill=col)
        y += mm(sz * 1.9)
    return img


# ============================ PDF ============================
def png_to_pdf(png_path, pdf_path, fmt):
    from fpdf import FPDF
    pdf = FPDF(unit="mm", format=fmt)
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()
    w, h = fmt
    pdf.image(png_path, x=0, y=0, w=w, h=h)
    pdf.output(pdf_path)
    print("[OK]", pdf_path)


def main():
    print("Поле A2 ...")
    board = draw_board()
    board.save(os.path.join(OUT, "board_a2.png"))
    png_to_pdf(os.path.join(OUT, "board_a2.png"), os.path.join(OUT, "board_a2.pdf"), (420, 594))

    print("Карты материалов ...")
    mats = material_cards_page([MAT_COLORS[t] for t in MAT_ROT],
                               [MAT_NAMES[t] for t in MAT_ROT])
    mats.save(os.path.join(OUT, "cards_materials.png"))
    png_to_pdf(os.path.join(OUT, "cards_materials.png"), os.path.join(OUT, "cards_materials.pdf"), (210, 297))

    print("Карты событий ...")
    pages = event_cards_pages()
    for i, p in enumerate(pages):
        p.save(os.path.join(OUT, f"cards_events_{i}.png"))
        png_to_pdf(os.path.join(OUT, f"cards_events_{i}.png"), os.path.join(OUT, f"cards_events_{i}.pdf"), (210, 297))

    print("Фишки ...")
    pawns_page().save(os.path.join(OUT, "pawns.png"))
    png_to_pdf(os.path.join(OUT, "pawns.png"), os.path.join(OUT, "pawns.pdf"), (210, 297))

    print("Кубики ...")
    dice_page().save(os.path.join(OUT, "dice.png"))
    png_to_pdf(os.path.join(OUT, "dice.png"), os.path.join(OUT, "dice.pdf"), (210, 297))

    print("Правила ...")
    rules_page().save(os.path.join(OUT, "rules.png"))
    png_to_pdf(os.path.join(OUT, "rules.png"), os.path.join(OUT, "rules.pdf"), (210, 297))

    print("Готово. Файлы в", OUT)


if __name__ == "__main__":
    main()
