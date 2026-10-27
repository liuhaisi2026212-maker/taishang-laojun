#!/usr/bin/env python3
"""中文口播去 AI 味预检：标出假对比句壳和空转词。

用法：
    python3 ai_tell_linter.py 稿子.txt
    python3 ai_tell_linter.py 稿子.txt --format json
    python3 ai_tell_linter.py 稿子.txt --fail-on-hard --allow 允许清单.txt

脚本只做机械预检：命中不等于一定要改，没命中也不等于没有 AI 味。
硬拦截（假对比）默认要改；只有在纠正可核实的事实、区分适用范围时才保留。
软提醒是空转词和句式，结合语境判断。

来源：柳爷（taishang-laojun 作者）自用的去 AI 味预检脚本。空转词与句式清单部分参考
op7418/Humanizer-zh（MIT），见仓库 THIRD-PARTY-NOTICES.md。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


HARD_PATTERNS = {
    "不是X而是Y": r"不是[^。！？\n]{1,45}(?:，|,)?(?:而是|是)[^。！？\n]{1,45}",
    "并非X而是Y": r"并非[^。！？\n]{1,45}(?:，|,)?而是[^。！？\n]{1,45}",
    "不在于X而在于Y": r"不在于[^。！？\n]{1,45}(?:，|,)?而在于[^。！？\n]{1,45}",
    "你以为X其实Y": r"你以为[^。！？\n]{1,45}(?:，|,)?其实[^。！？\n]{1,45}",
    "不只是X更是Y": r"不(?:只|仅)是?[^。！？\n]{1,45}(?:，|,)?(?:更是|还(?:是|要)?)[^。！？\n]{1,45}",
    "只X不够还要Y": r"(?:只|光)[^。！？\n]{1,45}(?:不够|不行|没用)[^。！？\n]{0,12}(?:还要|还得|才)[^。！？\n]{1,45}",
    "只是X才是Y": r"只是[^。！？\n]{1,45}(?:，|,)?[^。！？\n]{0,12}才是[^。！？\n]{1,45}",
    # 换了动词的同一种壳：这不叫努力，这叫瞎练；不难，难的是天天做；不卖苹果，卖的是眼光
    "X不是问题，Y才是": r"不是[^。！？，,\n]{1,20}[，,][^。！？，,\n]{1,20}才是",
    "不叫X，叫Y": r"不(?:叫|算)[^。！？，,\n]{1,20}[，,][^。！？，,\n]{0,4}(?:叫|算)[^。！？\n]{1,30}",
    "不AX，A的是Y": r"不([\u4e00-\u9fa5])[^。！？，,\n]{0,20}[，,][^。！？，,\n]{0,6}\1(?:的是|才是)[^。！？\n]{1,30}",
}

SOFT_TERMS = [
    "本质上", "真正的核心", "这背后反映的是", "归根结底", "值得注意的是",
    "随着AI的发展", "在这个AI时代", "赋能", "抓手", "认知跃迁",
    "助力", "全方位", "无缝", "深度融合", "生态闭环", "底层逻辑", "重塑", "颠覆性",
    "总而言之", "综上所述", "让我们一起", "未来可期", "希望对你有帮助", "如果你有任何问题",
    "值得一提的是", "不可否认", "毋庸置疑",
    "说了这么多", "收个总", "正确姿势", "行业公开的秘密", "干货来了", "关注我，下期",
]

SOFT_REGEX = {
    "“随着……发展”式开头": r"(?m)^\s*随着[^。，！？\n]{1,20}(?:的)?(?:发展|到来|普及|兴起)",
    "“进行＋动词”": r"进行(?:了)?(?:一次|一番)?[一-龥]{2}",
    "层叠的“的”（一句里 4 个以上）": r"[^。！？\n]*?(?:的[^。！？，\n]{0,8}){4,}",
    "四字词排比": r"(?:[一-龥]{4}[、，,]){3,}[一-龥]{4}",
    "“最后送你/给你几个”式清单": r"(?:送你|给你|教你)[两三四五六七八九十]个",
}
DASH_LIMIT = 5  # 一篇里破折号超过这个数，合并成一条“破折号过多”提醒


def line_number(text: str, position: int) -> int:
    return text.count("\n", 0, position) + 1


def load_allow(path: str | None) -> list[str]:
    """允许清单：每行一段原文片段，命中文字包含其中任一片段时不算硬拦截。# 开头为注释。"""
    if not path:
        return []
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.lstrip().startswith("#")]


def analyze(text: str, allow: list[str] | None = None) -> dict[str, object]:
    allow = allow or []
    hard: list[dict[str, object]] = []
    for name, pattern in HARD_PATTERNS.items():
        for match in re.finditer(pattern, text):
            snippet = match.group(0).strip()
            if any(item in snippet or snippet in item for item in allow):
                continue
            hard.append({"line": line_number(text, match.start()), "pattern": name, "text": snippet})

    soft: list[dict[str, object]] = []
    for term in SOFT_TERMS:
        for match in re.finditer(re.escape(term), text):
            soft.append({"line": line_number(text, match.start()), "term": term})
    for name, pattern in SOFT_REGEX.items():
        for match in re.finditer(pattern, text):
            soft.append({"line": line_number(text, match.start()), "term": name})
    dashes = [line_number(text, m.start()) for m in re.finditer("——", text)]
    if len(dashes) > DASH_LIMIT:
        soft.append({"line": dashes[0], "term": f"破折号过多（全文 {len(dashes)} 处，超过 {DASH_LIMIT} 处）"})

    hard.sort(key=lambda item: (int(item["line"]), str(item["pattern"])))
    soft.sort(key=lambda item: (int(item["line"]), str(item["term"])))
    return {
        "status": "reject" if hard else "pass",
        "hard_block_count": len(hard),
        "hard_blocks": hard,
        "soft_warning_count": len(soft),
        "soft_warnings": soft,
    }


def to_markdown(result: dict[str, object]) -> str:
    lines = [
        "# 中文去 AI 味预检",
        "",
        f"- 结论：{'退回重写' if result['status'] == 'reject' else '通过硬拦截'}",
        f"- 假对比硬拦截：{result['hard_block_count']}",
        f"- 软提醒：{result['soft_warning_count']}",
    ]
    if result["hard_blocks"]:
        lines.extend(["", "## 硬拦截"])
        for item in result["hard_blocks"]:
            lines.append(f"- 第{item['line']}行｜{item['pattern']}｜{item['text']}")
    if result["soft_warnings"]:
        lines.extend(["", "## 软提醒"])
        for item in result["soft_warnings"]:
            lines.append(f"- 第{item['line']}行｜{item['term']}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="标出中文稿子里的假对比句壳和空转词。")
    parser.add_argument("path", nargs="?", help="UTF-8 文本文件；不填或填 - 时读标准输入")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--fail-on-hard", action="store_true", help="有硬拦截时以状态码 1 退出")
    parser.add_argument("--allow", help="允许清单文件：每行一段确实在纠正事实或区分范围的原文片段")
    args = parser.parse_args()

    text = Path(args.path).read_text(encoding="utf-8") if args.path and args.path != "-" else sys.stdin.read()
    result = analyze(text, load_allow(args.allow))
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.format == "json" else to_markdown(result))
    return 1 if args.fail_on_hard and result["hard_block_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
