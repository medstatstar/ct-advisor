import numpy as np, cv2
from PIL import Image
from skimage import measure
import cairosvg, os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = r'C:\Users\WintoneFileSrv\.workbuddy\clipboard-images\clipboard-2026-08-01T12-08-51-088Z-d2266cca.png'

gray = np.array(Image.open(SRC).convert('L'))
blur = cv2.GaussianBlur(gray, (5, 5), 1.5)
_, binimg = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
binimg = (binimg // 255).astype(np.uint8)
cnts, _ = cv2.findContours(binimg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
c = max(cnts, key=cv2.contourArea)
mask = np.zeros_like(binimg)
cv2.drawContours(mask, [c], -1, 1, -1)
cs = measure.find_contours(mask.astype(float), 0.5)
c0 = max(cs, key=len)
pts = c0[:, ::-1]
d = np.cumsum(np.r_[0, np.sqrt(((pts[1:] - pts[:-1]) ** 2).sum(1))])
d = d / d[-1]
newd = np.linspace(0, 1, 100)
xy = np.column_stack([np.interp(newd, d, pts[:, 0]), np.interp(newd, d, pts[:, 1])])

minx, maxx = xy[:, 0].min(), xy[:, 0].max()
miny, maxy = xy[:, 1].min(), xy[:, 1].max()
pad_l, pad_t = 18, 32
avail_w, avail_h = 100 - pad_l, 104 - pad_t
s = min(avail_w / (maxx - minx), avail_h / (maxy - miny))
w, h = (maxx - minx) * s, (maxy - miny) * s
offx, offy = pad_l + (avail_w - w) / 2, pad_t
m = np.c_[(xy[:, 0] - minx) * s + offx, (xy[:, 1] - miny) * s + offy]
dpath = 'M' + ' L'.join(f'{x:.1f} {y:.1f}' for x, y in m) + ' Z'

cx, cy = round(offx + w / 2, 1), round(offy + h * 0.42, 1)

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 104 104" width="100%">
  <defs>
    <filter id="logoShadow" x="-30%" y="-30%" width="160%" height="160%">
      <feDropShadow dx="0" dy="2.5" stdDeviation="2.5" flood-color="#1C6DD0" flood-opacity="0.30"/>
    </filter>
  </defs>
  <rect x="-52" y="-52" width="104" height="104" rx="20" fill="#EEEDFE" stroke="#C5DCF5" stroke-width="0.5" transform="translate(52,52)" filter="url(#logoShadow)"/>
  <g transform="translate(7,13)">
    <text font-family="Arial Black,Helvetica Neue,Arial,sans-serif" font-size="16" font-weight="900" font-style="italic" fill="#1C6DD0" stroke="#1C6DD0" stroke-width="0.25" paint-order="stroke" stroke-linejoin="round">Clinical</text>
    <text y="12" font-family="Arial Black,Helvetica Neue,Arial,sans-serif" font-size="16" font-weight="900" font-style="italic" fill="#1C6DD0" stroke="#1C6DD0" stroke-width="0.25" paint-order="stroke" stroke-linejoin="round">Trial</text>
  </g>
  <path d="{dpath}" fill="#1C6DD0" stroke="#1657A8" stroke-width="1"/>
  <g transform="translate({cx},{cy})">
    <circle r="20" fill="none" stroke="#FFFFFF" stroke-width="2.6"/>
    <circle r="16" fill="none" stroke="#FFFFFF" stroke-width="1" opacity="0.55"/>
    <g stroke="#FFFFFF" stroke-width="1.4" stroke-linecap="round" opacity="0.9">
      <line x1="0" y1="-20" x2="0" y2="-15.5"/><line x1="0" y1="20" x2="0" y2="15.5"/>
      <line x1="-20" y1="0" x2="-15.5" y2="0"/><line x1="20" y1="0" x2="15.5" y2="0"/>
      <line x1="-14.1" y1="-14.1" x2="-11" y2="-11"/><line x1="14.1" y1="14.1" x2="11" y2="11"/>
      <line x1="-14.1" y1="14.1" x2="-11" y2="11"/><line x1="14.1" y1="-14.1" x2="11" y2="-11"/>
    </g>
    <path d="M0 -24 L-3.4 -17.5 L3.4 -17.5 Z" fill="#D85A30"/>
    <path d="M0 -18 L4 0 L-4 0 Z" fill="#D85A30"/>
    <path d="M0 18 L-4 0 L4 0 Z" fill="#9FE1CB"/>
    <path d="M-18 0 L0 -4 L0 4 Z" fill="#AFA9EC" opacity="0.95"/>
    <path d="M18 0 L0 4 L0 -4 Z" fill="#C5DCF5" opacity="0.95"/>
    <circle r="4" fill="#FFFFFF"/><circle r="1.5" fill="#1C6DD0"/>
  </g>
</svg>'''

with open(os.path.join(HERE, 'icon.svg'), 'w') as f:
    f.write(svg)
cairosvg.svg2png(url=os.path.join(HERE, 'icon.svg'), write_to=os.path.join(HERE, 'icon_4x.png'), output_width=416, output_height=416)
cairosvg.svg2png(url=os.path.join(HERE, 'icon.svg'), write_to=os.path.join(HERE, 'icon_8x.png'), output_width=832, output_height=832)
print('compass center', cx, cy, 'scale', round(s, 4))
print('final icon.svg + PNG written')
