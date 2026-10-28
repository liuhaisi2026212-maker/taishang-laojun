"""Verify portable skill references and generated views without installing anything."""
from pathlib import Path
import json
import re
import shutil
import tempfile
import build_mindmap
import build_views
from build_views import ORDER

def check():
    ROOT = build_views.ROOT
    errors = []
    market = json.loads((ROOT/'.claude-plugin/marketplace.json').read_text(encoding="utf-8"))
    plugin = json.loads((ROOT/'.claude-plugin/plugin.json').read_text(encoding="utf-8"))
    if not isinstance(market.get('owner'), dict) or not isinstance(market.get('plugins'), list):
        errors.append('Invalid marketplace owner/plugins')
    elif market['plugins'][0]['name'] != plugin['name'] or market['plugins'][0]['version'] != plugin['version']:
        errors.append('Plugin identity/version mismatch')
    version = plugin['version']
    if f'当前版本 **{version}**' not in (ROOT / 'README.md').read_text(encoding='utf-8'):
        errors.append(f'README version is not {version}')
    if not (ROOT / 'docs/validation.md').read_text(encoding='utf-8').startswith(f'# {version} '):
        errors.append(f'docs/validation.md does not start with a {version} entry')
    with tempfile.TemporaryDirectory() as tmp:
        installed = Path(tmp)/'skills'
        shutil.copytree(ROOT/'skills', installed)
        for name in ORDER:
            entry = installed/name/'SKILL.md'
            text = entry.read_text(encoding="utf-8")
            if not text.startswith('---\n') or f'name: {name}\n' not in text.split('---\n', 2)[1]:
                errors.append(f'Missing skill identity: {name}')
        for path in installed.rglob('*.md'):
            # Third-party notice contains descriptive root paths, not runtime links.
            for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)', path.read_text(encoding="utf-8")):
                if '://' in target or target.startswith('#'):
                    continue
                dest = (path.parent/target.split('#')[0]).resolve()
                if not dest.is_relative_to(installed.resolve()) or not dest.is_file():
                    errors.append(f'Broken isolated-install reference: {path.relative_to(installed)} -> {target}')
    generated = {name: build() for name, build in build_views.GENERATED.items()}
    generated.update({name: render() for name, render in build_mindmap.VIEWS.items()})
    for filename, content in generated.items():
        if not (ROOT/filename).is_file() or (ROOT/filename).read_text(encoding="utf-8") != content:
            errors.append(f'Stale generated view: {filename}')
    entry = (ROOT/'skills/taishang-laojun/SKILL.md').read_text(encoding="utf-8")
    for ref in build_views.REFERENCES:
        if f'references/{ref}.md' not in entry:
            errors.append(f'Entry skill does not route to reference: {ref}')
    for name in ['LICENSE', 'THIRD-PARTY-NOTICES.md']:
        if (ROOT/'skills/taishang-laojun/references'/name).read_bytes() != (ROOT/name).read_bytes():
            errors.append(f'Stale distribution notice: {name}')
    # Also verify repository Markdown links, including documentation entry points.
    for path in ROOT.rglob('*.md'):
        if '.git' in path.parts:
            continue
        for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)', path.read_text(encoding="utf-8")):
            if '://' not in target and not target.startswith('#'):
                if not (path.parent/target.split('#')[0]).exists():
                    errors.append(f'Broken repository link: {path.relative_to(ROOT)} -> {target}')
    # Skill text teaches the AI how to talk, so it must pass the same fake-contrast gate.
    import importlib.util
    spec = importlib.util.spec_from_file_location('ai_tell_linter', ROOT/'skills/taishang-laojun/scripts/ai_tell_linter.py')
    linter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(linter)
    allow = linter.load_allow(str(ROOT/'scripts/ai_tell_allow.txt'))
    for path in sorted((ROOT/'skills').rglob('*.md')):
        if path.name in ('deai-rulebook.md', 'THIRD-PARTY-NOTICES.md', 'LICENSE'):
            continue  # the rulebook quotes the patterns it bans
        for hit in linter.analyze(path.read_text(encoding="utf-8"), allow)['hard_blocks']:
            errors.append(f"Fake-contrast shell in skill text: {path.relative_to(ROOT)}:{hit['line']} {hit['text'][:30]}")
    if errors:
        raise SystemExit('\n'.join(errors))
    print(f'PASS: {len(ORDER)} skill identities, isolated copied-package references, repository links, synchronized views, mindmap, notices and fake-contrast gate')

if __name__ == '__main__':
    check()
