"""Build the panorama SVG and interactive HTML from one data source."""
from html import escape
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
VERSION = json.loads((ROOT / '.claude-plugin/plugin.json').read_text(encoding='utf-8'))['version']  # 唯一的版本号来源

TITLE = '太上老君 · AI炼丹炉'
SUBTITLE = '把别人的爆款，炼成你自己的视频'
STANCE = ('总控台：按你此刻在哪，调对的兵器', '有灵感就用自己的事直接拍；没灵感就刷对标、拆爆款、存弹药库。需要认识你时才访谈。AI 下判断，你来校准。')

CORE = [
    ('破冰先于一切', '陌生人只给你一两秒，先让他感兴趣，信任靠后面的证据挣'),
    ('观众在想什么', '想躺平的贪和懒、没意识到的痛点、对你的防御'),
    ('用事件衬托内核', '直白说没人信，让观众从一件事里自己看出来'),
    ('判断力胜过教程', '热点是载体，判断是内容；只露果，不穷尽'),
    ('钩子马上兑现', '下一秒就用画面或事件接住，接住它的又是下一个钩子'),
    ('展示什么，吸引什么人', '成品招要成品的，过程招学习者，忙碌招求职者'),
    ('适合自己的才是兵器', '对标、工具、表达都放进自己的条件里掂量'),
]

MODULES = [
    ('01 选材 · 找对标拆爆款', '#ff898d',
     ['找条件一致、想吸引的人也一致的对标', '拆开看它为什么爆：撑着它的是哪一两个机制', '复读、客户、替换三关掂量，用你自己的事接住'],
     '交付：保留什么、换掉什么、用你的哪件事接住',
     '柳爷找对标只看条件一致的口播号；主动搜的常不对，无意刷到、想一直看的才是。'),
    ('02 看火 · 选题决策链', '#ffbd72',
     ['起点 → 观众最关心什么 → 你拿什么接住', '靠哪种吸引力：娱乐 / 帮助 / 实力 / 下危机', '会招来谁？开头的承诺拿什么兑现？'],
     '交付：1–3 个私人定制方向，推荐一个',
     '世界杯：抢热点 → 球迷最关心比分 → 用 AI 做预测工作台 → 摊开思考维度。'),
    ('03 丹方 · 系列策划', '#f4a6d7',
     ['判断型、现场型、事件型、串联型、上手型，选一个当主线', '服务观众不服务自己；列不出五期就撑不住', '一个人拍得动吗？一期期拍下去，来的是谁？'],
     '交付：固定什么、换什么、首批五期、第一期怎么拍',
     '像素范每周只讲一件事和自己的判断，讲多了就成了“AI 的内容看他就够了”。'),
    ('04 开炉 · 开头与结构', '#78dcad',
     ['一句话里装几个好懂的信息，完成破冰', '勾证衔接，最好接成钩子链', '收尾给看完的理由和关注的理由，然后干脆结束'],
     '交付：第一句、证据画面、推进、收尾和理由',
     '机场：“刚下飞机遇到件恶心事” → 马上接一块广告牌 → 广告牌又是下一个钩子。'),
    ('05 回炉 · 完整成稿', '#c8a4ff',
     ['逐字稿是弹药库，先存不急着改', '先有场景和目的，再翻弹药库找观点', '借观点不借脉络；AI 初稿按改稿六刀做减法'],
     '交付：可以直接念的完整稿',
     '柳爷改 AI 初稿时，信息大多保留，动作几乎全是“删”。'),
    ('06 收丹 · 标题', '#8ec9ff',
     ['标题不等于选题，剪完再想', '补信息 / 给期待 / 替开头当“总”', '跟我有关：认人、认事、认心，用陌生人的眼睛检查'],
     '交付：需要几个给几个，每个说清“有关”在哪',
     '“一人公司有个致命的缺点”：把观众心里那句“肯定有坑”变成标题。'),
    ('07 成丹 · 变现承接', '#ffd36a',
     ['点赞、咨询、成交分开看', '预期用户 ≠ 实际用户：纠偏、顺势，或拒绝', '一个能兑现的交付，只走平台允许的承接'],
     '交付：一个交付、承接路径、交付成本与观察点',
     '一人公司招来求职者：可以纠偏，也可以顺势为他们设计一个交付。'),
]

FOOTER = [
    ('底味访谈', '需要认识你时才用：让你越聊越想说，AI 替你总结成使用者档案'),
    ('反馈复盘', '沿链条找第一个偏掉的环节，再选纠偏或顺势'),
    ('底线', '不编经历和数字 · 钩子要兑现 · 合规承接 · 不服务害人的需求'),
]
NOTE = '方法来自柳爷做内容的经验，不是流量保证。'
PAGES_URL = 'https://liuhaisi2026212-maker.github.io/taishang-laojun/mindmap/preview.html'


def svg():
    w, pad = 1200, 40
    out = []
    t = lambda x, y, s, size, color, weight=400: out.append(
        f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}">{escape(s)}</text>')
    box = lambda x, y, bw, bh, stroke: out.append(
        f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" rx="16" fill="#192439" stroke="{stroke}"/>')
    t(44, 66, TITLE, 42, '#ffd36a', 700)
    t(44, 106, f'{SUBTITLE}　·　版本 {VERSION}', 23, '#d4dce9')
    box(pad, 136, w - 2 * pad, 96, '#ffd36a')
    t(64, 174, STANCE[0], 27, '#ffd36a', 700)
    t(64, 210, STANCE[1], 21, '#d4dce9')
    y = 268
    t(44, y, '炉心：七条底层判断（每个模块都从这里推）', 25, '#eef3fc', 600)
    y += 22
    col_w = (w - 2 * pad - 20) // 2
    for i, (name, line) in enumerate(CORE):
        cx = pad + (i % 2) * (col_w + 20)
        cy = y + (i // 2) * 74
        box(cx, cy, col_w, 62, '#3a4a66')
        t(cx + 18, cy + 27, f'{i + 1}. {name}', 21, '#ffd36a', 650)
        t(cx + 18, cy + 51, line, 16, '#b8c3d6')
    y += 4 * 74 + 26
    bw, bh = col_w, 206
    for i, (name, color, lines, deliver, _case) in enumerate(MODULES):
        bx = pad + (i % 2) * (bw + 20)
        by = y + (i // 2) * (bh + 18)
        box(bx, by, bw, bh, color)
        t(bx + 22, by + 38, name, 26, color, 650)
        for j, line in enumerate(lines):
            t(bx + 22, by + 76 + j * 31, line, 18, '#d4dce9')
        t(bx + 22, by + 180, deliver, 18, color)
    y += -(-len(MODULES) // 2) * (bh + 18) + 8
    for i, (name, line) in enumerate(FOOTER):
        t(44, y + i * 34, f'{name}：{line}', 19, '#9facbf' if i < 2 else '#ffbd72')
    y += 3 * 34 + 10
    t(44, y, NOTE + ' 点击图片进入可展开的交互版。', 16, '#6f7d93')
    h = y + 34
    head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            'role="img" aria-labelledby="title desc">\n'
            f'<title id="title">太上老君AI炼丹炉：创作方法全景图</title>\n'
            '<desc id="desc">AI 先下判断、用户校准；七条底层判断贯穿选材、看火、丹方、开炉、回炉、收丹、成丹七个模块。</desc>\n'
            f'<rect width="{w}" height="{h}" rx="24" fill="#101725"/>\n'
            '<g font-family="-apple-system,BlinkMacSystemFont,\'Segoe UI\',\'Noto Sans CJK SC\',\'Microsoft YaHei\',sans-serif">\n')
    return head + '\n'.join(out) + '\n</g>\n</svg>\n'


def html():
    cards, details = [], []
    for i, (name, color, lines, deliver, case) in enumerate(MODULES):
        cards.append(
            f'<button class="card" style="--c:{color}" aria-controls="d{i}" aria-expanded="false" onclick="tgl({i})">'
            f'<span class="name">{escape(name)}</span><span class="hint">点击展开</span></button>')
        items = ''.join(f'<li>{escape(x)}</li>' for x in lines)
        details.append(
            f'<section id="d{i}" class="detail" style="--c:{color}" hidden><h3>{escape(name)}</h3><ul>{items}</ul>'
            f'<p class="deliver">{escape(deliver)}</p><p class="case">柳爷的案例：{escape(case)}<br>'
            '<span>学的是推理过程，换成你自己的场景和材料重新推一遍。</span></p></section>')
    core = ''.join(f'<li><b>{escape(n)}</b>{escape(l)}</li>' for n, l in CORE)
    foot = ''.join(f'<li><b>{escape(n)}</b>{escape(l)}</li>' for n, l in FOOTER)
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>炼丹炉全景图</title>
<style>
:root{{--bg:#101725;--panel:#192439;--deep:#0f1526;--text:#e6ebf4;--muted:#9facbf;--gold:#ffd36a}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--text);font-family:'PingFang SC','Microsoft YaHei',sans-serif;line-height:1.7}}
main{{max-width:1080px;margin:0 auto;padding:24px 16px 40px}}
h1{{color:var(--gold);font-size:28px;margin:0}}
.sub{{color:var(--muted);margin:4px 0 18px}}
.stance{{background:var(--panel);border:2px solid var(--gold);border-radius:14px;padding:14px 16px}}
.stance b{{color:var(--gold);font-size:18px;display:block}}
h2{{font-size:18px;margin:22px 0 10px}}
.core{{list-style:none;padding:0;margin:0;display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:10px}}
.core li,.foot li{{background:var(--deep);border-radius:10px;padding:10px 12px;font-size:14px;color:#c7d0de}}
.core b,.foot b{{color:var(--gold);display:block;font-size:15px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}}
.card{{background:var(--panel);border:2px solid var(--c);border-radius:14px;padding:14px;text-align:left;color:inherit;font:inherit;cursor:pointer}}
.card .name{{color:var(--c);font-weight:700;font-size:17px;display:block}}
.card .hint{{color:var(--muted);font-size:13px}}
.detail{{background:var(--deep);border:1px solid var(--c);border-radius:12px;padding:12px 16px;margin-top:12px}}
.detail h3{{color:var(--c);margin:0 0 6px}}
.detail ul{{margin:0;padding-left:20px}}
.deliver{{color:var(--c);margin:8px 0 0}}
.case{{background:#1a2a3a;border-radius:8px;padding:8px 10px;margin-top:8px;font-size:14px}}
.case span{{color:var(--muted);font-size:13px}}
.foot{{list-style:none;padding:0;display:grid;gap:8px}}
.note{{color:#6f7d93;font-size:12px;text-align:center;margin-top:18px}}
</style>
</head>
<body>
<main>
<h1>{escape(TITLE)}</h1>
<p class="sub">{escape(SUBTITLE)}　·　版本 {VERSION}</p>
<div class="stance"><b>{escape(STANCE[0])}</b>{escape(STANCE[1])}</div>
<h2>炉心：七条底层判断</h2>
<ul class="core">{core}</ul>
<h2>七个模块（按需调用，不必从头走完）</h2>
<div class="cards">{''.join(cards)}</div>
{''.join(details)}
<h2>贯穿全程</h2>
<ul class="foot">{foot}</ul>
<p class="note">{escape(NOTE)}</p>
</main>
<script>
function tgl(n){{
  document.querySelectorAll('.detail').forEach(function(d,i){{
    var open = i===n && d.hidden;
    d.hidden = !open;
    document.querySelectorAll('.card')[i].setAttribute('aria-expanded', open);
  }});
}}
</script>
</body>
</html>
'''


VIEWS = {'docs/mindmap/overview.svg': svg, 'docs/mindmap/preview.html': html, 'docs/mindmap/炼丹炉全景图.html': html}


def main(root=ROOT):
    for name, render in VIEWS.items():
        (root / name).write_text(render(), encoding='utf-8')


if __name__ == '__main__':
    main()
