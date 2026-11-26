"""Regression checks for UTF-8 I/O, Windows Markdown links, and compliance linter."""
from pathlib import Path
import importlib.util
import json
import ntpath
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import build_mindmap
import build_views
import check_package


def load_compliance_linter():
    script_path = build_views.ROOT / 'skills/taishang-laojun/scripts/compliance_linter.py'
    spec = importlib.util.spec_from_file_location('compliance_linter', script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, script_path


class PortabilityTests(unittest.TestCase):
    def test_windows_links_match_published_views(self):
        expected = (build_views.ROOT / 'docs/formulas.md').read_text(encoding='utf-8')
        with patch('os.path.relpath', ntpath.relpath):
            self.assertEqual(build_views.render(), expected)

    def test_build_and_check_with_gbk_default(self):
        # Work on a copy so the test never regenerates the user's repository.
        original_open = Path.open

        def gbk_open(path, mode='r', buffering=-1, encoding=None, errors=None, newline=None):
            if 'b' not in mode and encoding is None:
                encoding = 'gbk'
            return original_open(path, mode, buffering, encoding, errors, newline)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'repo'
            shutil.copytree(build_views.ROOT, root, ignore=shutil.ignore_patterns('.git', '__pycache__'))
            expected = {name: (root / name).read_bytes() for name in
                        list(build_views.GENERATED) + list(build_mindmap.VIEWS)}
            with patch.object(build_views, 'ROOT', root), \
                    patch.object(Path, 'open', gbk_open), patch('os.path.relpath', ntpath.relpath):
                build_views.main()
                check_package.check()
            for name, content in expected.items():
                self.assertEqual((root / name).read_bytes(), content)


class ComplianceLinterTests(unittest.TestCase):
    def setUp(self):
        self.linter, self.script = load_compliance_linter()

    def run_cli(self, *args, stdin=None):
        return subprocess.run(
            [sys.executable, str(self.script), *args],
            input=stdin,
            text=True,
            encoding="utf-8",
            capture_output=True,
        )

    def test_multi_char_superlatives_and_no_false_positives(self):
        hit = self.linter.analyze("这款东西最便宜也最好用。")
        matches = [item["match"] for item in hit["high_risks"]]
        self.assertIn("最便宜", matches)
        self.assertIn("最好用", matches)
        clean = self.linter.analyze("这个方案最便于理解，也适合最宜居的城市。")
        self.assertEqual(clean["high_count"], 0)
        self.assertEqual(clean["warn_count"], 0)

    def test_long_line_snippet_and_allow_suppresses_nested_warnings(self):
        prefix = "前面是一段很长的口播铺垫内容，用来把单行长度拉到超过八十个字，确保后面的词落在八十字之外，继续补足字数让总长度超过一百字。"
        text = prefix + "提醒大家不要相信绝对有效，也不要在公域写加微信。"
        res = self.linter.analyze(text)
        self.assertEqual(res["high_count"], 2)
        self.assertEqual(res["warn_count"], 0)
        for item in res["high_risks"]:
            self.assertIn(item["match"], item["snippet"])

        # 允许清单按整行片段放行高危词后，同位置不再被提醒项（绝对、微信）重复捞出
        allowed = self.linter.analyze(text, allow=["不要相信绝对有效", "不要在公域写加微信"])
        self.assertEqual(allowed["high_count"], 0)
        self.assertEqual(allowed["warn_count"], 0)

    def test_cli_exit_codes_and_chinese_error_messages(self):
        r_ok = self.run_cli("--text", "今天分享一条短视频复盘心得。", "--format", "json")
        self.assertEqual(r_ok.returncode, 0)
        self.assertEqual(json.loads(r_ok.stdout)["status"], "clear")

        r_high = self.run_cli("--text", "稳赚不赔，加微信领资料", "--fail-on-high")
        self.assertEqual(r_high.returncode, 1)
        self.assertIn("命中高危红线", r_high.stdout)

        with tempfile.TemporaryDirectory() as td:
            bad_bin = Path(td) / "sample.docx"
            bad_bin.write_bytes(b"PK\x03\x04")
            r_bin = self.run_cli(str(bad_bin))
            self.assertEqual(r_bin.returncode, 2)
            self.assertIn("暂不支持", r_bin.stderr)

            bad_allow = Path(td) / "gbk_allow.txt"
            bad_allow.write_bytes("中文".encode("gbk"))
            r_allow_gbk = self.run_cli("--text", "测试", "--allow", str(bad_allow))
            self.assertEqual(r_allow_gbk.returncode, 2)
            self.assertIn("UTF-8", r_allow_gbk.stderr)

            r_allow_missing = self.run_cli("--text", "测试", "--allow", str(Path(td) / "missing.txt"))
            self.assertEqual(r_allow_missing.returncode, 2)
            self.assertIn("找不到允许清单文件", r_allow_missing.stderr)

        r_mutex = self.run_cli(str(build_views.ROOT / "README.md"), "--text", "hello")
        self.assertEqual(r_mutex.returncode, 2)


if __name__ == '__main__':
    unittest.main()
