# -*- coding: utf-8 -*-
"""生成 C 方案（肩部徽章）下，红十字徽章在头像剪影内不同落点的 4-up 对比图。"""
import re
src=open('icon.svg',encoding='utf-8').read()
m=re.search(r'<path d="([^"]+)" fill="#1C6DD0"',src)
sil=m.group(1)

POINTERS='''    <path d="M0 -24 L5.5 0 L-5.5 0 Z" fill="#D85A30"/>
    <path d="M0 24 L-5.5 0 L5.5 0 Z" fill="#9FE1CB"/>
    <path d="M-24 0 L0 -5.5 L0 5.5 Z" fill="#AFA9EC" opacity="0.95"/>
    <path d="M24 0 L0 5.5 L0 -5.5 Z" fill="#C5DCF5" opacity="0.95"/>'''

cands=[('上胸/锁骨',68,86),('胸口正中',71,95),('胸口偏下(当前)',75,93),('肩部',82,99)]

HEAD='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 230" width="100%">\n'
DEF='''  <defs>
    <filter id="ls" x="-30%" y="-30%" width="160%" height="160%">
      <feDropShadow dx="0" dy="2.5" stdDeviation="2.5" flood-color="#1C6DD0" flood-opacity="0.30"/>
    </filter>
    <symbol id="frame" viewBox="0 0 104 104">
      <rect x="-52" y="-52" width="104" height="104" rx="20" fill="#EEEDFE" stroke="#C5DCF5" stroke-width="0.5" transform="translate(52,52)" filter="url(#ls)"/>
      <g transform="translate(7,13)">
        <text font-family="Arial Black,Helvetica Neue,Arial,sans-serif" font-size="16" font-weight="900" font-style="italic" fill="#1C6DD0" stroke="#1C6DD0" stroke-width="0.25" paint-order="stroke" stroke-linejoin="round">Clinical</text>
        <text y="12" font-family="Arial Black,Helvetica Neue,Arial,sans-serif" font-size="16" font-weight="900" font-style="italic" fill="#1C6DD0" stroke="#1C6DD0" stroke-width="0.25" paint-order="stroke" stroke-linejoin="round">Trial</text>
      </g>
      <path d="__SIL__" fill="#1C6DD0" stroke="#1657A8" stroke-width="1"/>
    </symbol>
  </defs>
'''

body='<rect x="0" y="0" width="680" height="230" fill="#FFFFFF"/>\n'
for i,(label,x,y) in enumerate(cands):
    col=i*170
    tx=col+30
    body+='  <text x="%d" y="24" font-family="Arial,Helvetica,sans-serif" font-size="13" font-weight="700" fill="#333">%s</text>\n'%(col+10,label)
    body+='  <use href="#frame" x="%d" y="40" width="104" height="104"/>\n'%(col+13)
    # 四向指针（绝对坐标 = 图标原点 col+13+59, 40+62）
    px=col+13+59; py=40+62
    body+='  <g transform="translate(%d,%d)">\n%s\n    <circle r="2.4" fill="#FFFFFF"/>\n  </g>\n'%(px,py,POINTERS)
    # 徽章（绝对坐标 = col+13+x, 40+y）
    bx=col+13+x; by=40+y
    body+='  <g transform="translate(%d,%d)">\n    <circle r="8" fill="#FFFFFF" stroke="#1C6DD0" stroke-width="1.2"/>\n    <rect x="-2" y="-5.5" width="4" height="11" rx="1" fill="#E2342E"/>\n    <rect x="-5.5" y="-2" width="11" height="4" rx="1" fill="#E2342E"/>\n  </g>\n'%(bx,by)

open('badge_position_compare.svg','w',encoding='utf-8').write((HEAD+DEF+body+'</svg>').replace('__SIL__',sil))
print('wrote badge_position_compare.svg')
