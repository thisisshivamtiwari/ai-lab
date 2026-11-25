"""Synthetic hotel paperwork with known number tokens. No real hotel, guest or client data.
Makes 3 document types x 4 image conditions x N seeds as PNGs, plus truth.json."""
import json, random, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

N_SEEDS = int(sys.argv[1]) if len(sys.argv) > 1 else 5
OUT = Path("docs"); OUT.mkdir(exist_ok=True)
FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"
BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
MONO = "/System/Library/Fonts/Supplemental/Courier New.ttf"
HOTELS = ["The Harbour Light Hotel", "Ashdown Park House", "Northgate Suites", "The Old Mill Inn", "Castle Bay Resort"]
ROOMS = ["Classic Double", "Superior King", "Junior Suite", "Family Room", "Garden View Twin", "Penthouse Suite"]
ITEMS = ["Room charge", "Breakfast x2", "Dinner (Terrace)", "Minibar", "Spa treatment", "Parking", "Laundry", "Late checkout", "Room service", "Bar"]
SUPPLIES = ["Linen service (sets)", "Toiletries (cases)", "Coffee beans (kg)", "Cleaning chemicals", "Welcome cards", "Bottled water (crates)", "Towels (bales)", "Printer paper (reams)"]

def money(r, lo, hi):
    v = round(r.uniform(lo, hi), 2)
    return f"£{v:,.2f}"

def date(r):
    d, m = r.randint(1, 28), r.randint(1, 12)
    y = r.choice([2026, 2027])
    return f"{d:02d}/{m:02d}/{y}"

def ref(r, p):
    return f"{p}-{r.randint(10000, 99999)}"

def rate_card(r, hotel):
    tokens = []
    lines = [("title", f"{hotel}"), ("h", "RATE CARD")]
    start = date(r); end = date(r)
    season = ref(r, "RC")
    lines.append(("t", f"Season ref {season}   Valid {start} to {end}"))
    tokens += [season, start, end]
    lines.append(("gap", ""))
    lines.append(("row", ["Room type", "Mon-Thu", "Fri-Sat", "Sun", "Min stay"]))
    for room in r.sample(ROOMS, 5):
        a, b, c = money(r, 79, 420), money(r, 99, 560), money(r, 69, 390)
        ms = str(r.randint(1, 3))
        lines.append(("row", [room, a, b, c, ms]))
        tokens += [a, b, c]
    lines.append(("gap", ""))
    occ = f"{r.randint(55, 96)}%"
    adr = money(r, 90, 260)
    lines.append(("t", f"Target occupancy {occ}   Target ADR {adr}"))
    tokens += [occ, adr]
    vat = f"VAT {r.randint(5, 20)}% included.  Rates per room per night."
    lines.append(("t", vat))
    tokens.append(vat.split()[1])
    return lines, tokens

def folio(r, hotel):
    tokens = []
    lines = [("title", f"{hotel}"), ("h", "GUEST FOLIO")]
    bk = ref(r, "BK"); room = str(r.randint(101, 912))
    ci, co = date(r), date(r)
    lines.append(("t", f"Booking {bk}   Room {room}   Arrive {ci}   Depart {co}"))
    tokens += [bk, room, ci, co]
    lines.append(("gap", ""))
    lines.append(("row", ["Date", "Item", "Qty", "Amount"]))
    total = 0.0
    for _ in range(r.randint(6, 9)):
        d = date(r); it = r.choice(ITEMS); q = str(r.randint(1, 4))
        amt = round(r.uniform(4, 380), 2); total += amt
        a = f"£{amt:,.2f}"
        lines.append(("row", [d, it, q, a]))
        tokens += [d, a]
    lines.append(("gap", ""))
    sub = f"£{total:,.2f}"; vatv = f"£{total*0.2:,.2f}"; grand = f"£{total*1.2:,.2f}"
    lines.append(("row", ["", "Subtotal", "", sub]))
    lines.append(("row", ["", "VAT 20%", "", vatv]))
    lines.append(("row", ["", "TOTAL DUE", "", grand]))
    tokens += [sub, "20%", vatv, grand]
    card = f"Card ending {r.randint(1000, 9999)}   Auth {r.randint(100000, 999999)}"
    lines.append(("t", card))
    tokens += [card.split()[2], card.split()[4]]
    return lines, tokens

def invoice(r, hotel):
    tokens = []
    lines = [("title", "Severn Valley Supplies Ltd"), ("h", "INVOICE")]
    inv = ref(r, "INV"); po = ref(r, "PO"); d = date(r); due = date(r)
    lines.append(("t", f"Invoice {inv}   PO {po}   Issued {d}   Due {due}"))
    lines.append(("t", f"Bill to: {hotel}"))
    tokens += [inv, po, d, due]
    lines.append(("gap", ""))
    lines.append(("row", ["Description", "Qty", "Unit", "Net"]))
    total = 0.0
    for s in r.sample(SUPPLIES, r.randint(5, 7)):
        q = r.randint(1, 60); u = round(r.uniform(2, 120), 2); n = round(q * u, 2); total += n
        us, ns = f"£{u:,.2f}", f"£{n:,.2f}"
        lines.append(("row", [s, str(q), us, ns]))
        tokens += [str(q), us, ns]
    lines.append(("gap", ""))
    vatp = r.choice([0, 5, 20]); vatv = round(total * vatp / 100, 2)
    sub, vs, gr = f"£{total:,.2f}", f"£{vatv:,.2f}", f"£{total+vatv:,.2f}"
    lines.append(("row", ["", "Net total", "", sub]))
    lines.append(("row", ["", f"VAT {vatp}%", "", vs]))
    lines.append(("row", ["", "Amount due", "", gr]))
    tokens += [sub, f"{vatp}%", vs, gr]
    acct = f"Sort code {r.randint(10,99)}-{r.randint(10,99)}-{r.randint(10,99)}   Account {r.randint(10000000, 99999999)}"
    lines.append(("t", acct))
    tokens += [acct.split()[2], acct.split()[4]]
    return lines, tokens

def render(lines, w=1654, h=2339):  # A4 at 200 dpi
    img = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(img)
    f_t, f_h, f_b, f_m = ImageFont.truetype(BOLD, 48), ImageFont.truetype(BOLD, 36), ImageFont.truetype(FONT, 30), ImageFont.truetype(MONO, 30)
    y = 140; cols = [120, 760, 1040, 1300, 1500]
    for kind, val in lines:
        if kind == "title": d.text((120, y), val, font=f_t, fill="black"); y += 80
        elif kind == "h": d.text((120, y), val, font=f_h, fill="black"); y += 70
        elif kind == "t": d.text((120, y), val, font=f_b, fill="black"); y += 52
        elif kind == "gap": y += 30
        elif kind == "row":
            for i, c in enumerate(val):
                font = f_b if i == 0 else f_m
                x = cols[i] if i < len(cols) else cols[-1]
                if i > 0 and i < len(val):
                    tw = d.textlength(c, font=font); x = cols[i] + 200 - tw  # right-align numbers
                d.text((x, y), c, font=font, fill="black")
            y += 50
            d.line((120, y - 4, 1540, y - 4), fill=(200, 200, 200), width=1)
    return img

def degrade(img, cond, r):
    if cond == "clean":
        return img
    if cond == "scan":  # photocopier: slight rotation, blur, grain, grey tint
        out = img.rotate(r.uniform(-1.2, 1.2), resample=Image.BICUBIC, fillcolor="white", expand=False)
        out = out.filter(ImageFilter.GaussianBlur(0.9))
        px = out.load(); w, h = out.size
        for _ in range(int(w * h * 0.004)):
            x, y = r.randrange(w), r.randrange(h); g = r.randint(90, 200); px[x, y] = (g, g, g)
        return out.point(lambda v: int(v * 0.92 + 10))
    if cond == "phone":  # uneven lighting, lower contrast, mild blur, downscale
        w, h = img.size
        shade = Image.linear_gradient("L").resize((w, h)).rotate(r.choice([0, 90, 180, 270]))
        shade = shade.point(lambda v: 150 + v * 0.4)  # 150..252 brightness map
        out = Image.composite(img, Image.new("RGB", (w, h), (40, 40, 40)), shade.point(lambda v: v - 20))
        out = out.filter(ImageFilter.GaussianBlur(1.1)).rotate(r.uniform(-2.5, 2.5), resample=Image.BICUBIC, fillcolor=(120, 120, 120))
        return out.resize((int(w * 0.75), int(h * 0.75)), Image.BILINEAR)
    if cond == "lowres":  # fax-like: 100 dpi
        w, h = img.size
        return img.resize((w // 2, h // 2), Image.BILINEAR).convert("L").point(lambda v: 255 if v > 150 else 0).convert("RGB")
    raise ValueError(cond)

truth = []
for seed in range(N_SEEDS):
    for kind, fn in [("ratecard", rate_card), ("folio", folio), ("invoice", invoice)]:
        r = random.Random(f"{kind}-{seed}")
        hotel = r.choice(HOTELS)
        lines, tokens = fn(r, hotel)
        base = render(lines)
        for cond in ["clean", "scan", "phone", "lowres"]:
            name = f"{kind}-{seed}-{cond}.png"
            degrade(base, cond, random.Random(f"{name}")).save(OUT / name)
            truth.append({"file": name, "doc": kind, "seed": seed, "cond": cond, "tokens": tokens})
json.dump(truth, open("truth.json", "w"), indent=1)
print(len(truth), "pages,", sum(len(t["tokens"]) for t in truth), "number tokens")
