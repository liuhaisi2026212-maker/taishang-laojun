# 安装炼丹炉

这是一套文本技能包，不内置视频下载器、剪辑器或模型服务。完整使用需要智能体能读取技能文件；普通聊天产品可使用自包含 Bot 文本，实际能力取决于宿主。

## Codex：先用完整项目

下载/克隆整个仓库作为项目打开，输入“使用炼丹炉，我想拍视频但不知道拍什么”。根目录 AGENTS.md 指向总入口。已有稿件可直接给稿并说只改标题。

需要安装到其他项目时，把 `skills/` **下面的八个子文件夹**一并放进宿主配置的技能目录，保持八个文件夹为同级。每个文件夹中的 references 也必须一起保留；不要再套一层 skills 文件夹。不得覆盖已有同名自定义版本，先备份。只装总入口不够完整使用。

## Claude Code

在当前修复版完整仓库中可先用本地方式（无需上传）：

```sh
claude plugin marketplace add .
claude plugin install taishang-laojun@taishang-laojun
```

仓库发布本修复版后，远程方式为：

```sh
claude plugin marketplace add liuhaisi2026212-maker/taishang-laojun
claude plugin install taishang-laojun@taishang-laojun
```

也可把八个子文件夹复制到 Claude Code 配置的 skills 目录。完整项目使用 CLAUDE.md 入口，不能假设它自动读取 AGENTS.md。

参考：[Claude marketplace 文档](https://code.claude.com/docs/en/plugin-marketplaces)。本地结构校验命令：`claude plugin validate .claude-plugin/marketplace.json` 和 `claude plugin validate .claude-plugin/plugin.json`。结构通过不等于真实宿主使用验收。

## 豆包、WorkBuddy、Grok 等

本版不声称这些客户端自动发现技能的路径已实测。若客户端明确支持导入 Skills，按其说明导入全部八个目录并检查能否读取引用文件；没有这个能力时，用下一节的 Bot 版。不得仅凭生成了三个选题判断安装成功。

## 只想给一个智能体一份文件

使用 `bot-prompt/liuye-bot-prompt.md`。它包含总入口、炉心、推理示范、七个模块和全部参考正文，不依赖仓库文件。设定框装不下时，把 `bot-prompt/liuye-bot-lite.md`（总入口、炉心、底味访谈、七个模块）放进设定，完整版作为知识库附件上传。粘贴到支持的系统提示词位置，或作为参考文件附上并明确要求按它工作。宿主若截断长度、不能遵循文件或不支持持久上下文，效果可能受限；普通附件不等于系统级安装。

## 如果出来的稿子明显不守规则

比如编了“我做了二十年”这类你没提供过的经历、写成一篇五个小标题的长文、满篇破折号，多半是平台没有完整读进这份文件，而是按它自己的写作习惯出了稿。可以这样处理：

- 把 Bot 精简版放进智能体的设定（人设）里，完整版作为知识库附件；
- 或者把 Bot 文件开头“先读这六条”整段复制到对话的第一条消息里；
- 出稿前先口述一段你自己的真事，让它在你的原话上改。

WorkBuddy 等平台尚未实测，有人反馈过这类情况。

## 验证是否可用

- 新手无材料：先问一个容易回答的具体问题，聊出一件事后由智能体先总结、先推荐，不虚构经历。
- 给一条参考：智能体直接给出“借 / 调整后试拍 / 暂不适合”的结论和理由，而不是反问一串定位问题。
- 给定稿件只改一个标题：只做该任务，不强制重访谈。
- 提供素材要求完整稿：返回正文，不在开炉与回炉间来回转交。
- 核对智能体实际读取的技能与引用文件；有缺失就补包，不用猜测性内容掩盖。

本地自动检查运行 `python3 scripts/check_package.py`；当前测试范围见 `docs/validation.md`。语料、个人底味不需要上传本仓库。

## 许可

本体沿用 CC BY-NC 4.0，第三方部分见相应声明。涉及收费客户服务或其他商业用途时，不能把本指南当额外授权；需按许可与权利人明确授权判断。输出内容的权利和使用场景另行判断。
