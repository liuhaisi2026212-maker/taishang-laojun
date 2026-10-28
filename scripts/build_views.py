"""Build reader and standalone Bot views from the maintained skill files."""
from pathlib import Path
import os
import re

import build_mindmap
from build_mindmap import VERSION

ROOT = Path(__file__).resolve().parents[1]
ORDER = ['taishang-laojun', 'tslj-select', 'tslj-idea', 'tslj-series', 'tslj-open', 'tslj-script', 'tslj-title', 'tslj-monetize']

def body(path):
    text = path.read_text(encoding="utf-8")
    if text.startswith('---\n'):
        text = text.split('---\n', 2)[2]
    return text.strip()

REFERENCES = ['core-mind', 'case-book', 'flavor-interview', 'material-card', 'deai-rulebook', 'edit-six-cuts', 'feedback-review']
LITE = ['taishang-laojun', 'core-mind', 'flavor-interview'] + ORDER[1:]
FIRST_RULES = ('## 先读这六条（读不完全文也要守住）\n\n'
               '1. 不知道用户是谁，就不写第一人称经历：不写“我做了二十年”“上个月一个客户来找我”，不编具体案例和数字来撑开头。先用一句话说明“我还不知道你是谁，这版没写你的经历”。\n'
               '2. 行业价格、比例、损耗这类数字写成“一般”“大概”，交付时提醒用户按当地情况核实。\n'
               '3. 默认写成能直接念的短视频口播，一两分钟；用户明确要图文长文时才写长文。\n'
               '4. 不套模板：不要每节一个格式、三个一组地凑、满篇破折号，不用“不是……而是……”“说了这么多”“关注我，下期……”，结尾讲完最后一个有用的点就停。\n'
               '5. 交稿时提醒一句：这是初稿，用户念一遍、把不像自己会说的话换掉再拍；最好先把自己的真事口述一遍，再让你在原话上改。\n'
               '6. 最后只问一个能让稿子变成用户自己的问题。\n\n')
LICENSE_NOTE = ('本体版权归柳爷，许可 CC BY-NC 4.0：https://creativecommons.org/licenses/by-nc/4.0/ 。'
                '项目：https://github.com/liuhaisi2026212-maker/taishang-laojun 。')


def sources(lite=False):
    paths = [ROOT / 'skills' / name / 'SKILL.md' for name in ORDER]
    paths += [ROOT / 'skills/taishang-laojun/references' / (name + '.md') for name in REFERENCES]
    if lite:
        paths = [p for p in paths if (p.parent.name if p.name == 'SKILL.md' else p.stem) in LITE]
        refs = [p for p in paths if p.name != 'SKILL.md']
        paths = paths[:1] + refs + [p for p in paths[1:] if p not in refs]  # entry, core-mind, interview, modules
    return paths


def render(bot=False, lite=False):
    included = {p.resolve() for p in sources(lite)}
    parts = []
    for path in sources(lite):
        def link(match):
            label, target = match.groups()
            if '://' in target or target.startswith('#'):
                return match.group(0)
            if bot:
                if (path.parent / target).resolve() in included:
                    return label + '（见本文件相应章节）'
                return label + '（完整版 Bot 文件 liuye-bot-prompt.md 中有该章节）'
            relative = os.path.relpath(path.parent / target, ROOT / 'docs').replace("\\", "/")
            return f'[{label}]({relative})'
        parts.append(re.sub(r'\[([^\]]+)\]\(([^)]+)\)', link, body(path)))
    if lite:
        heading = ('# 太上老君·AI炼丹炉：Bot精简版\n\n' + f'版本 {VERSION}。' +
                   '适合系统提示词有长度限制的智能体（如各类 Bot 的人设设定框）。包含总入口、炉心、底味访谈和七个模块；'
                   '推理示范、去AI味、改稿六刀和复盘细则在完整版 Bot 文件里，可作为知识库附件一起上传。'
                   '本文件由技能源生成，不要单独维护另一套规则。\n\n' + FIRST_RULES)
        parts.append('## 许可\n\n' + LICENSE_NOTE + '第三方声明见完整版。')
    elif bot:
        heading = ('# 太上老君·AI炼丹炉：Bot完整流程\n\n' + f'版本 {VERSION}。' +
                   '本文自包含。下面“读取模块/参考”均指本文件内对应章节，不要求另找仓库路径。'
                   '按需使用章节，不按目录顺序逐项执行。宿主权限和用户请求优先；无工具能力时不假装执行。'
                   '本文件由技能源生成，不要单独维护另一套规则。\n\n' + FIRST_RULES)
        parts.append('## 分发许可与第三方说明\n\n' + LICENSE_NOTE + '本修订调整了流程与适用条件，第三方许可如下。'
                     + '\n\n' + (ROOT/'THIRD-PARTY-NOTICES.md').read_text(encoding="utf-8"))
    else:
        heading = ('# 炼丹炉配方全集\n\n' + f'版本 {VERSION}。' + '由技能源生成的人读版；案例经验和推导不等于所有赛道效果验证。'
                   '使用时按当前请求选章节，不要求完整走完所有模块。\n\n')
    return (heading + '\n\n---\n\n'.join(parts)).rstrip() + '\n'


GENERATED = {'docs/formulas.md': lambda: render(),
             'bot-prompt/liuye-bot-prompt.md': lambda: render(True),
             'bot-prompt/liuye-bot-lite.md': lambda: render(True, True)}


def main():
    for name, build in GENERATED.items():
        (ROOT/name).write_text(build(), encoding="utf-8")
    build_mindmap.main(ROOT)
    refs = ROOT/'skills/taishang-laojun/references'
    for name in ['LICENSE', 'THIRD-PARTY-NOTICES.md']:
        (refs/name).write_text((ROOT/name).read_text(encoding="utf-8"), encoding="utf-8")

if __name__ == '__main__':
    main()
