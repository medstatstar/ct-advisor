# -*- coding: utf-8 -*-
"""生成 ct-advisor logo 红十字放置位置的三个候选方案 + 单SVG并排对比预览（symbol复用，无嵌套）。"""
import re

src = open('icon.svg', encoding='utf-8').read()
m = re.search(r'<path d="([^"]+)" fill="#1C6DD0"', src)
silhouette = m.group(1)

POINTERS = '''<path d="M0 -24 L5.5 0 L-5.5 0 Z" fill="#D85A30"/>
    <path d="M0 24 L-5.5 0 L5.5 0 Z" fill="#9FE1CB"/>
    <path d="M-24 0 L0 -5.5 L0 5.5 Z" fill="#AFA9EC" opacity="0.95"/>
    <path d="M24 0 L0 5.5 L0 -5.5 Z" fill="#C5DCF5" opacity="0.95"/>'''

HEAD = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 104 104" width="100%">\n  <defs>\n    <filter id="logoShadow" x="-30%" y="-30%" width="160%" height="160%">\n      <feDropShadow dx="0" dy="2.5" stdDeviation="2.5" flood-color="#1C6DD0" flood-opacity="0.30"/>\n    </filter>\n  </defs>\n'
TAIL = '</svg>'

FRAME = '''  <rect x="-52" y="-52" width="104" height="104" rx="20" fill="#EEEDFE" stroke="#C5DCF5" stroke-width="0.5" transform="translate(52,52)" filter="url(#logoShadow)"/>
  <g transform="translate(7,13)">
    <text font-family="Arial Black,Helvetica Neue,Arial,sans-serif" font-size="16" font-weight="900" font-style="italic" fill="#1C6DD0" stroke="#1C6DD0" stroke-width="0.25" paint-order="stroke" stroke-linejoin="round">Clinical</text>
    <text y="12" font-family="Arial Black,Helvetica Neue,Arial,sans-serif" font-size="16" font-weight="900" font-style="italic" fill="#1C6DD0" stroke="#1C6DD0" stroke-width="0.25" paint-order="stroke" stroke-linejoin="round">Trial</text>
  </g>
  <path d="{sil}" fill="#1C6DD0" stroke="#1657A8" stroke-width="1"/>'''

# A 中心红十字
A = HEAD + FRAME.format(sil=silhouette) + '''
  <g transform="translate(59.0,62.2)">
{p}
    <rect x="-2.6" y="-10.5" width="5.2" height="21" rx="1.3" fill="#E2342E" stroke="#FFFFFF" stroke-width="1.1"/>
    <rect x="-10.5" y="-2.6" width="21" height="5.2" rx="1.3" fill="#E2342E" stroke="#FFFFFF" stroke-width="1.1"/>
  </g>'''.format(p=POINTERS) + TAIL

# C 肩部徽章
C = HEAD + FRAME.format(sil=silhouette) + '''
  <g transform="translate(59.0,62.2)">
{p}
    <circle r="2.4" fill="#FFFFFF"/>
  </g>
  <g transform="translate(75,93)">
    <circle r="8" fill="#FFFFFF" stroke="#1C6DD0" stroke-width="1.2"/>
    <rect x="-2" y="-5.5" width="4" height="11" rx="1" fill="#E2342E"/>
    <rect x="-5.5" y="-2" width="11" height="4" rx="1" fill="#E2342E"/>
  </g>'''.format(p=POINTERS) + TAIL

# D 北向医学标（北红 + 北尖白十字）
D = HEAD + FRAME.format(sil=silhouette) + '''
  <g transform="translate(59.0,62.2)">
    <path d="M0 -24 L5.5 0 L-5.5 0 Z" fill="#E2342E"/>
    <path d="M0 24 L-5.5 0 L5.5 0 Z" fill="#9FE1CB"/>
    <path d="M-24 0 L0 -5.5 L0 5.5 Z" fill="#AFA9EC" opacity="0.95"/>
    <path d="M24 0 L0 5.5 L0 -5.5 Z" fill="#C5DCF5" opacity="0.95"/>
    <circle r="2.4" fill="#FFFFFF"/>
    <g transform="translate(0,-21)">
      <rect x="-1.6" y="-4.5" width="3.2" height="9" rx="0.8" fill="#FFFFFF"/>
      <rect x="-4.5" y="-1.6" width="9" height="3.2" rx="0.8" fill="#FFFFFF"/>
    </g>
  </g>'''.format() if False else HEAD + FRAME.format(sil=silhouette) + '''
  <g transform="translate(59.0,62.2)">
    <path d="M0 -24 L5.5 0 L-5.5 0 Z" fill="#E2342E"/>
    <path d="M0 24 L-5.5 0 L5.5 0 Z" fill="#9FE1CB"/>
    <path d="M-24 0 L0 -5.5 L0 5.5 Z" fill="#AFA9EC" opacity="0.95"/>
    <path d="M24 0 L0 5.5 L0 -5.5 Z" fill="#C5DCF5" opacity="0.95"/>
    <circle r="2.4" fill="#FFFFFF"/>
    <g transform="translate(0,-21)">
      <rect x="-1.6" y="-4.5" width="3.2" height="9" rx="0.8" fill="#FFFFFF"/>
      <rect x="-4.5" y="-1.6" width="9" height="3.2" rx="0.8" fill="#FFFFFF"/>
    </g>
  </g>''' + TAIL

for name, body in [('opt_a_center', A), ('opt_c_badge', C), ('opt_d_north', D)]:
    open(name + '.svg', 'w', encoding='utf-8').write(body)
    print('wrote', name + '.svg')

# 单SVG对比图（symbol 复用 frame，无嵌套 svg）
compare = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 210" width="100%">
  <defs>
    <filter id="ls" x="-30%" y="-30%" width="160%" height="160%">
      <feDropShadow dx="0" dy="2.5" stdDeviation="2.5" flood-color="#1C6DD0" flood-opacity="0.30"/>
    </filter>
    <symbol id="frame" viewBox="0 0 104 104">
      <rect x="-52" y="-52" width="104" height="104" rx="20" fill="#EEEDFE" stroke="#C5DCF5" stroke-width="0.5" transform="translate(52,52)" filter="url(#ls)"/>
      <g transform="translate(7,13)">
        <text font-family="Arial Black,Helvetica Neue,Arial,sans-serif" font-size="16" font-weight="900" font-style="italic" fill="#1C6DD0" stroke="#1C6DD0" stroke-width="0.25" paint-order="stroke" stroke-linejoin="round">Clinical</text>
        <text y="12" font-family="Arial Black,Helvetica Neue,Arial,sans-serif" font-size="16" font-weight="900" font-style="italic" fill="#1C6DD0" stroke="#1C6DD0" stroke-width="0.25" paint-order="stroke" stroke-linejoin="round">Trial</text>
      </g>
      <path d="{sil}" fill="#1C6DD0" stroke="#1657A8" stroke-width="1"/>
    </symbol>
  </defs>
  <rect x="0" y="0" width="680" height="210" fill="#FFFFFF"/>
  <text x="46" y="28" font-family="Arial,Helvetica,sans-serif" font-size="15" font-weight="700" fill="#333">A · 中心红十字</text>
  <text x="286" y="28" font-family="Arial,Helvetica,sans-serif" font-size="15" font-weight="700" fill="#333">C · 肩部徽章</text>
  <text x="526" y="28" font-family="Arial,Helvetica,sans-serif" font-size="15" font-weight="700" fill="#333">D · 北向医学标</text>
  <use href="#frame" x="36" y="44" width="104" height="104"/>
  <use href="#frame" x="276" y="44" width="104" height="104"/>
  <use href="#frame" x="516" y="44" width="104" height="104"/>
  <g transform="translate(95,106)">
{p}
    <rect x="-2.6" y="-10.5" width="5.2" height="21" rx="1.3" fill="#E2342E" stroke="#FFFFFF" stroke-width="1.1"/>
    <rect x="-10.5" y="-2.6" width="21" height="5.2" rx="1.3" fill="#E2342E" stroke="#FFFFFF" stroke-width="1.1"/>
  </g>
  <g transform="translate(335,106)">
{p}
    <circle r="2.4" fill="#FFFFFF"/>
  </g>
  <g transform="translate(351,137)">
    <circle r="8" fill="#FFFFFF" stroke="#1C6DD0" stroke-width="1.2"/>
    <rect x="-2" y="-5.5" width="4" height="11" rx="1" fill="#E2342E"/>
    <rect x="-5.5" y="-2" width="11" height="4" rx="1" fill="#E2342E"/>
  </g>
  <g transform="translate(575,106)">
    <path d="M0 -24 L5.5 0 L-5.5 0 Z" fill="#E2342E"/>
    <path d="M0 24 L-5.5 0 L5.5 0 Z" fill="#9FE1CB"/>
    <path d="M-24 0 L0 -5.5 L0 5.5 Z" fill="#AFA9EC" opacity="0.95"/>
    <path d="M24 0 L0 5.5 L0 -5.5 Z" fill="#C5DCF5" opacity="0.95"/>
    <circle r="2.4" fill="#FFFFFF"/>
    <g transform="translate(0,-21)">
      <rect x="-1.6" y="-4.5" width="3.2" height="9" rx="0.8" fill="#FFFFFF"/>
      <rect x="-4.5" y="-1.6" width="9" height="3.2" rx="0.8" fill="#FFFFFF"/>
    </g>
  </g>
</svg>'''.format(sil=silhouette, p=POINTERS)
open('options_compare.svg', 'w', encoding='utf-8').write(compare)
print('wrote options_compare.svg')
