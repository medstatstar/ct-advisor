# -*- coding: utf-8 -*-
import re
src = open('icon.svg', encoding='utf-8').read()
sil = re.search(r'<path d="([^"]+)" fill="#1C6DD0"', src).group(1)

def badge(cx, cy):
    return (f'<g transform="translate({cx},{cy})">'
            f'<circle r="8" fill="#FFFFFF" stroke="#1C6DD0" stroke-width="1.2"/>'
            f'<rect x="-1.6" y="-5" width="3.2" height="10" rx="0.8" fill="#E2342E"/>'
            f'<rect x="-5" y="-1.6" width="10" height="3.2" rx="0.8" fill="#E2342E"/>'
            f'</g>')

def emit_base():
    return (
        '<rect x="-52" y="-52" width="104" height="104" rx="20" fill="#EEEDFE" stroke="#C5DCF5" stroke-width="0.5" transform="translate(52,52)"/>'
        '<g transform="translate(7,13)">'
        '<text font-family="Arial Black,Helvetica Neue,Arial,sans-serif" font-size="16" font-weight="900" font-style="italic" fill="#1C6DD0" stroke="#1C6DD0" stroke-width="0.25" paint-order="stroke" stroke-linejoin="round">Clinical</text>'
        '<text y="12" font-family="Arial Black,Helvetica Neue,Arial,sans-serif" font-size="16" font-weight="900" font-style="italic" fill="#1C6DD0" stroke="#1C6DD0" stroke-width="0.25" paint-order="stroke" stroke-linejoin="round">Trial</text>'
        '</g>'
        f'<path d="{sil}" fill="#1C6DD0" stroke="#1657A8" stroke-width="1"/>'
        '<g transform="translate(59.0,62.2)">'
        '<path d="M0 -24 L5.5 0 L-5.5 0 Z" fill="#D85A30"/>'
        '<path d="M0 24 L-5.5 0 L5.5 0 Z" fill="#9FE1CB"/>'
        '<path d="M-24 0 L0 -5.5 L0 5.5 Z" fill="#AFA9EC" opacity="0.95"/>'
        '<path d="M24 0 L0 5.5 L0 -5.5 Z" fill="#C5DCF5" opacity="0.95"/>'
        '<circle r="2.4" fill="#FFFFFF"/>'
        '</g>'
    )

options = [
    ('顶部正中 (D区)', 57, 43),
    ('右上部-后脑勺上方', 83, 43),
    ('右上部-稍偏下', 81, 52),
]

S = 1.8
W = 200
GAP = 40
OX0 = 20
OY = 60
H = 104 * S

body = ''
for i, (name, bx, by) in enumerate(options):
    ox = OX0 + i * (W + GAP)
    cy = OY + H / 2
    body += f'<g transform="translate({ox},{OY}) scale({S})">' + emit_base() + badge(bx, by) + '</g>'
    body += f'<text x="{ox + W/2}" y="{OY + H + 28}" font-family="Helvetica,Arial,sans-serif" font-size="15" font-weight="700" fill="#1C3A5E" text-anchor="middle">{name}</text>'

HEAD = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 320" width="100%">'
        '<rect x="0" y="0" width="680" height="320" fill="#FFFFFF"/>'
        '<text x="340" y="30" font-family="Helvetica,Arial,sans-serif" font-size="18" font-weight="800" fill="#1C3A5E" text-anchor="middle">红十字落点对比：头像上部</text>')
open('upper_compare.svg', 'w', encoding='utf-8').write(HEAD + body + '</svg>')
print('wrote upper_compare.svg with', len(options), 'options')
