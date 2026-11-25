# qianxing-kb

> 米哈游《原神》千星奇域（Miliastra Wonderland）官方综合指南的**离线知识库 + 检索技能**。
> 222 篇官方文档全文快照，本地检索、带原文证据回答，不依赖网页动态渲染。

## 这是什么

千星奇域官方综合指南是一个 Vue 单页应用，正文通过前端数据源动态加载，普通网页抓取只能拿到目录。本项目直接抽取官方数据源，把 222 篇文档全文做成可离线检索的知识库，并封装成一个 WorkBuddy 项目级 Skill（`SKILL.md` + 检索脚本），让 AI 能"查文档后按原文回答"，而不是凭印象编造。

**数据来源**

- 官方入口：<https://act.mihoyo.com/ys/ugc/tutorial/detail/mhs2w008wf14>
- 抽取地址：`https://act-webstatic.mihoyo.com/ugc-tutorial/knowledge/cn/zh-cn/` 下的 `textMap.json` / `catalog.json` / `headingsMap.json`
- 快照时间：2026-11-25；目录最后更新约 2026-10-10，正文含 7.2 版本（2026/11/04）更新日志
- 文档总量：**222 篇**

## 能回答什么问题（能力清单）

| 能力 | 说明 | 典型提问 |
|---|---|---|
| **功能支持判定** | 查某能力是否支持、有无版本/模式前提，给原文证据 | 「是否支持 2D 游戏？」 |
| **API / 节点查询** | Lua 脚本 API、服务器/客户端节点、控件接口是否存在及签名 | 「GridScrollerControl 怎么用？」 |
| **控件与 UI 实现** | 27 种界面控件、客户端控件容器、预设按钮、网格视窗等 | 「怎么做背包网格列表？」 |
| **概念解释** | 单位、造物、物件、白盒物件、节点图、阵营、负载优化等 | 「白盒物件是什么？」 |
| **模式差异对比** | 超限模式 vs 经典模式的可用内容差异 | 「经典模式有没有职业？」 |
| **更新日志追溯** | 各版本新增/修改的章节与能力 | 「7.1 更新了什么？」 |
| **限制与边界** | 原文中的"不支持/仅支持/不可用"逐条给出 | 「Lua 标准库有哪些限制？」 |

### 实测示例

提问：`是否支持2d游戏`

检索命中 `mhbgxf0nynww`，原文：

> 客户端脚本可以实现绝大多数2D玩法，以及界面的动态效果

检索命中 `mhtakr07vej4`，原文：

> 运行时使用 Lua 5.3……以下标准库能力不可用：string.dump、io.*、coroutine.*

结论：**支持 2D 玩法**，通过客户端 Lua 脚本 + 客户端控件实现；限制是 Lua 5.3 且部分标准库不可用。

## 目录结构

```
qianxing-kb/
├── README.md                 本文件
├── SKILL.md                  WorkBuddy 技能定义（检索流程、推理规则、输出格式）
├── scripts/
│   └── query_kb.py           检索脚本，仅依赖 Python 标准库
└── references/
    ├── textMap.json          222 篇文档正文（doc_id → 纯文本，约 1 MB）
    ├── catalog.json          目录树与标题路径
    └── headingsMap.json      各文档标题层级（定位章节用）
```

## 用法

### 1. 作为 WorkBuddy Skill 使用

把本仓库放到 WorkBuddy 工作区的 `.workbuddy/skills/qianxing-kb/`，然后在对话里用 `/query` 提问：

```
/query 帮我查询一下是否支持2d游戏
```

Skill 会自动拆解检索词、并行检索、按原文判断"支持/有前提/受限/未找到"，并输出带 `doc_id` 与原文片段的结论。

### 2. 直接命令行检索

```bash
# 基础检索
python3 scripts/query_kb.py "2D Lua 脚本"

# 限定返回数与上下文长度
python3 scripts/query_kb.py "网格视窗" --limit 3 --context 240

# 限定某篇文档
python3 scripts/query_kb.py "脚本" --doc-id mhtakr07vej4

# 列出全部 222 篇文档 ID 与标题
python3 scripts/query_kb.py "x" --list-docs

# 输出某篇文档全文
python3 scripts/query_kb.py "x" --raw-doc mhs2w008wf14
```

参数：

| 参数 | 默认 | 说明 |
|---|---|---|
| `--limit` | 5 | 返回文档数 |
| `--context` | 180 | 每个片段的上下文字符数 |
| `--doc-id` | — | 限定单篇文档 |
| `--doc-title` | — | 按标题关键字限定范围 |
| `--list-docs` | — | 列出全部文档 ID 与标题 |
| `--raw-doc` | — | 输出指定文档全文 |

## 设计原则

1. **证据优先**：所有结论必须带 `doc_id` 和原文片段，禁止只给结论。
2. **不臆测**：检索不到时回答"官方文档未检索到相关描述"，不推断为"不支持"，也不用外部社区资料替代官方口径。
3. **离线可复现**：检索不联网，222 篇全文都在本地，避免官方页面动态渲染带来的抓取失败。
4. **版本敏感**：官方标注文档"测试阶段，不定时勘误"，涉及版本差异时注明版本。

## 更新知识库快照

官方文档更新后，重新下载三个 JSON 覆盖 `references/` 即可，脚本与 SKILL.md 无需改动：

```bash
BASE="https://act-webstatic.mihoyo.com/ugc-tutorial/knowledge/cn/zh-cn"
curl -s "$BASE/catalog.json"      -o references/catalog.json
curl -s "$BASE/textMap.json"      -o references/textMap.json
curl -s "$BASE/headingsMap.json"  -o references/headingsMap.json
```

## 许可与说明

- 文档内容版权归米哈游所有，本项目仅做个人学习用途的离线整理与检索封装。
- 本项目不含米哈游官方背书，结论以官方文档原文为准。
