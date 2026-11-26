#!/usr/bin/env python3
"""全赛道通用发前合规排雷预检：标出常见高危红线词与需核对的提醒词。

用法：
    python3 compliance_linter.py 稿子.txt
    python3 compliance_linter.py --text "待检查的口播文案"
    python3 compliance_linter.py 稿子.txt --format json --fail-on-high
    python3 compliance_linter.py 稿子.txt --allow 允许清单.txt

退出码：
    0 = 检查完成（无高危命中，或未开启 --fail-on-high）
    1 = 开启 --fail-on-high 且命中高危红线
    2 = 参数错误、文件不存在、格式不支持或编码无法读取

说明：
    脚本只做机械初筛：命中不等于一定违规，0 命中也不等于 100% 过审。
    请结合语境、画面、字幕、人设及所在平台官方最新规则人工复核。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


BINARY_EXTS = {
    ".doc", ".docx", ".pdf", ".xls", ".xlsx", ".xlsm", ".ppt", ".pptx",
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".mp4", ".mov", ".mp3", ".m4a", ".zip",
}

# 高危红线：全平台普遍严查的典型表述（分类, 正则, 建议）
HIGH_RULES: list[tuple[str, str, str]] = [
    (
        "极限与绝对化用语",
        r"(?:最便宜|最有效|最好用|最[大高好强快佳优低少牛稳]|全网第一|第一品牌|全网最低|顶级|首选|绝对有效|绝对安全|100%|百分百|彻底解决|永久有效|万能)",
        "删掉极限或绝对化表述，收回你有真实证据的范围",
    ),
    (
        "医疗与疾病功效宣称",
        r"(?:根治|治愈|防癌|抗癌|降血压|降血糖|降血脂|消炎杀菌|排毒养颜|预防疾病|治疗[^。，！？\n]{0,4}病)",
        "非持证医疗内容严禁宣称疾病治疗、预防或医疗功效",
    ),
    (
        "金融保本与暴富承诺",
        r"(?:稳赚不赔|保本保收益|零风险|百分之百收益|躺赚|包赚|暴富|内幕消息)",
        "严禁承诺投资收益或零风险，必须保留必要风险提示",
    ),
    (
        "无凭证权威背书与虚假原价",
        r"(?:恢复原价|央视推荐|电视台推荐|国家级认证|权威认证|首席专家|联合研发人员)",
        "无真实授权或官方凭证时，严禁借官媒/权威背书或喊恢复原价",
    ),
    (
        "公域站外导流词",
        r"(?:加微信|加我微|加微|加[Vv]|微信号|微信聊|扫码加|二维码|扫一扫|绿泡泡)",
        "公域口播、字幕、封面、评论区与平台群内避免站外导流表述",
    ),
]

# 提醒项：是否违规取决于行业资质、凭证或发布场景，需人工结合语境判断
WARN_RULES: list[tuple[str, str, str]] = [
    (
        "行业高敏功效词（无对应资质慎用）",
        r"(?:减肥|减脂|瘦身|暴瘦|掉秤|美白|祛斑|助眠|改善睡眠|抗炎|抗氧化|调理代谢|产后恢复|包过)",
        "普通食品、普通化妆品或非持证内容慎用功效词，请核对品类与资质边界",
    ),
    (
        "价格与专利表述（须有凭证）",
        r"(?:原价|破价|福利价|专利成分|[一二三两四五六七八九十\d]+大专利)",
        "涉及价格对比或专利数量时，须留存依据并按平台要求展示凭证",
    ),
    (
        "强绝对口吻或时间承诺（核实依据）",
        r"(?:绝对|一定能|一定可以|[一二三两四五六七八九十\d]+天见效|不到[一二三两四五六七八九十\d]+个月就)",
        "避免在缺乏证据时做绝对保证或效果周期承诺",
    ),
    (
        "泛站外与隐私词（公域场景慎用）",
        r"(?:微信|扫码|私下转账|手机号)",
        "若用于公域引流或带货场景，请确认是否触发平台站外导流管控",
    ),
]


def line_number(text: str, position: int) -> int:
    return text.count("\n", 0, position) + 1


def line_bounds(text: str, position: int) -> tuple[int, int]:
    start = text.rfind("\n", 0, position) + 1
    end = text.find("\n", position)
    if end == -1:
        end = len(text)
    return start, end


def line_snippet(text: str, match_start: int, match_end: int, max_len: int = 80) -> str:
    l_start, l_end = line_bounds(text, match_start)
    raw = text[l_start:l_end]
    stripped = raw.strip()
    if len(stripped) <= max_len:
        return stripped
    # 围绕命中词居中截取，确保单行很长时 snippet 一定包含命中词
    rel_start = match_start - l_start
    rel_end = match_end - l_start
    match_len = rel_end - rel_start
    pad = max(0, (max_len - match_len) // 2)
    win_start = max(0, rel_start - pad)
    win_end = min(len(raw), win_start + max_len)
    win_start = max(0, win_end - max_len)
    piece = raw[win_start:win_end].strip()
    if win_start > 0:
        piece = "…" + piece
    if win_end < len(raw):
        piece = piece + "…"
    return piece


def load_allow(path: str | None) -> list[str]:
    """允许清单：每行一段原文片段，命中所在整行包含其中任一片段时跳过。# 开头为注释。"""
    if not path:
        return []
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"找不到允许清单文件：{path}")
    if p.is_dir():
        raise ValueError(f"允许清单路径是文件夹，请传入文本文件：{path}")
    try:
        lines = p.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise ValueError(f"允许清单文件不是 UTF-8 编码文本，请另存为 UTF-8 后再试：{path}") from exc
    return [line.strip() for line in lines if line.strip() and not line.lstrip().startswith("#")]


def analyze(text: str, allow: list[str] | None = None) -> dict[str, object]:
    allow = allow or []

    def scan(
        rules: list[tuple[str, str, str]],
        exclude_spans: list[tuple[int, int]] | None = None,
    ) -> tuple[list[dict[str, object]], list[tuple[int, int]]]:
        exclude_spans = exclude_spans or []
        hits: list[dict[str, object]] = []
        covered_spans: list[tuple[int, int]] = []
        for category, pattern, advice in rules:
            for match in re.finditer(pattern, text):
                start, end = match.span()
                if any(es <= start and end <= ee for es, ee in exclude_spans):
                    continue
                word = match.group(0).strip()
                l_start, l_end = line_bounds(text, start)
                full_line = text[l_start:l_end]
                # 无论是否被允许清单跳过，都记录已覆盖区间，避免高危放行后被提醒项重复捞出
                covered_spans.append((start, end))
                if any(item in word or item in full_line for item in allow):
                    continue
                hits.append({
                    "line": line_number(text, start),
                    "category": category,
                    "match": word,
                    "snippet": line_snippet(text, start, end),
                    "advice": advice,
                })
        hits.sort(key=lambda item: (int(item["line"]), str(item["category"]), str(item["match"])))
        return hits, covered_spans

    high, high_spans = scan(HIGH_RULES)
    warn, _ = scan(WARN_RULES, exclude_spans=high_spans)
    return {
        "status": "review_high" if high else ("review_warn" if warn else "clear"),
        "high_count": len(high),
        "high_risks": high,
        "warn_count": len(warn),
        "warnings": warn,
    }


def to_markdown(result: dict[str, object]) -> str:
    status_label = {
        "review_high": "命中高危红线，建议先改再发",
        "review_warn": "无高危红线，有语境/资质提醒项需人工核对",
        "clear": "机械初筛 0 命中（仍需人工核对画面、字幕与语境）",
    }[str(result["status"])]
    lines = [
        "# 通用发前合规预检",
        "",
        f"- 结论：{status_label}",
        f"- 高危红线：{result['high_count']}",
        f"- 提醒项：{result['warn_count']}",
    ]
    if result["high_risks"]:
        lines.extend(["", "## 高危红线"])
        for item in result["high_risks"]:
            lines.append(
                f"- 第{item['line']}行｜{item['category']}｜命中“{item['match']}”｜建议：{item['advice']}"
            )
    if result["warnings"]:
        lines.extend(["", "## 提醒项（结合语境与资质核对）"])
        for item in result["warnings"]:
            lines.append(
                f"- 第{item['line']}行｜{item['category']}｜命中“{item['match']}”｜建议：{item['advice']}"
            )
    lines.extend([
        "",
        "> 说明：脚本只做机械初筛，命中不等于一定违规，0 命中也不等于 100% 过审；请结合画面、字幕和所在平台官方规则复核。",
    ])
    return "\n".join(lines)


def read_input(path_arg: str | None, text_arg: str | None) -> str:
    if text_arg is not None:
        return text_arg
    if not path_arg or path_arg == "-":
        return sys.stdin.read()
    path = Path(path_arg)
    if not path.exists():
        raise FileNotFoundError(f"找不到文件：{path_arg}")
    if path.is_dir():
        raise ValueError(f"目标是文件夹，请传入文本文件：{path_arg}")
    if path.suffix.lower() in BINARY_EXTS:
        raise ValueError(f"暂不支持直接检查 {path.suffix.lower()} 格式，请导出为 UTF-8 纯文本（.txt / .md）后再试。")
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"文件不是 UTF-8 编码文本，请另存为 UTF-8 后再试：{path_arg}") from exc


def main() -> int:
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="全赛道通用发前合规排雷预检。")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("path", nargs="?", help="UTF-8 文本文件；不填或填 - 时读标准输入")
    group.add_argument("--text", help="直接传入待检查的文案字符串（与文件路径互斥）")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--fail-on-high", action="store_true", help="命中高危红线时以状态码 1 退出")
    parser.add_argument("--allow", help="允许清单文件：每行一段确认合规的原文片段")
    args = parser.parse_args()

    try:
        text = read_input(args.path, args.text)
        allow = load_allow(args.allow)
    except (OSError, ValueError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2

    result = analyze(text, allow)
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.format == "json" else to_markdown(result))
    return 1 if args.fail_on_high and result["high_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
