# Creator Cover Agent Skill

一套面向中文知识创作者与教程内容的封面 Agent Skill：先确认标题，再生成 6 个不同的视觉事件；母版确认后，可靠适配多平台比例，并为 `5:1` 超宽横幅提供独立保真分支。

[![Agent Skill](https://img.shields.io/badge/Agent-Skill-111827)](./SKILL.md)
[![Ratios](https://img.shields.io/badge/ratios-3%3A4%20%7C%204%3A3%20%7C%201%3A1%20%7C%205%3A2%20%7C%2016%3A9%20%7C%202.35%3A1%20%7C%205%3A1-E66A14)](./references/ratio-native-recomposition.md)
[![QA](https://img.shields.io/badge/QA-text%20%7C%20layout%20%7C%20identity%20%7C%20color-0F766E)](./references/quality-review.md)
[![License](https://img.shields.io/badge/license-MIT-2563EB)](./LICENSE)

## 真实 3:4 封面案例

这些成品展示的不是四套固定模板，而是同一套工作流如何围绕不同标题，重新设计人物动作、核心物、标题身份和品牌色。

<table>
  <tr>
    <td width="50%" valign="top">
      <img src="./examples/approved-covers/minimax-h3-local-deployment-3x4.png" alt="MiniMax H3 本地部署喂饭级教学 3:4 封面" width="100%">
      <br><strong>MiniMax H3 本地部署</strong>
      <br><sub>人物托举两个产品核心，品牌色从左右向中心汇合；大标题、真人与双产品关系在缩略图中仍能同时读清。</sub>
    </td>
    <td width="50%" valign="top">
      <img src="./examples/approved-covers/workbuddy-beginner-tutorial-3x4.png" alt="WorkBuddy 新手入门教学 3:4 封面" width="100%">
      <br><strong>WorkBuddy 新手入门教学</strong>
      <br><sub>把应用图标实体化为巨大工具核心，人物的托举与指向共同解释“入门”，没有退回普通人物站桩。</sub>
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <img src="./examples/approved-covers/workbuddy-seven-office-skills-3x4.png" alt="WorkBuddy 7 个神仙办公 Skill 3:4 封面" width="100%">
      <br><strong>WorkBuddy 7 个神仙办公 Skill</strong>
      <br><sub>用七层办公能力抽屉承载数字与功能关系，人物正在拉出结果层，核心视觉事件只属于这个标题。</sub>
    </td>
    <td width="50%" valign="top">
      <img src="./examples/approved-covers/opensquilla-topic-radar-3x4.png" alt="OpenSquilla 搭建 AI 选题雷达 3:4 封面" width="100%">
      <br><strong>OpenSquilla 搭建 AI 选题雷达</strong>
      <br><sub>品牌核心被改造成近距离雷达装置，人物同时操作与交付结果，黑橙材质统一标题、动作和产品事实。</sub>
    </td>
  </tr>
</table>

以上图片由作者明确授权在本仓库中公开展示。案例图片、人物肖像和第三方商标不随根目录 MIT License 开放再利用，详见 [案例素材许可边界](./examples/LICENSE.md)。

## 它解决什么问题

普通“改尺寸”提示词经常出现两种失败：

- 普通比例被过度重构，原本成熟的标题、人物和 Logo 关系被拆散；
- 超宽比例被直接重绘或压扁，造成人物、文字、色彩和构图失真。

本 Skill 把两类任务分开：

- `3:4 / 4:3 / 1:1 / 5:2 / 16:9 / 2.35:1` 默认保持原构图，只做必要微调；
- 精确 `2000×400` 的 `5:1` 才释放结构重组权限，并优先复用满意母版原像素前景。

每张结果都经过硬文字、空间利用、人物、手部、Logo、尺寸和色彩 Review；只重做失败比例。

## 第一次使用链路

```text
输入选题、正文或现成标题
          ↓
确认唯一封面标题
          ↓
识别必要品牌事实并生成 6 个视觉事件提示词
          ↓
在宿主图像工具中生成并确认满意母版（默认 3:4）
          ↓
普通比例保持构图并行适配 ─┐
                            ├→ 原尺寸 Review → 只修失败比例
5:1 原像素前景保真重排 ───┘
          ↓
生成 1:1 + 2.35:1 公众号组合图并交付
```

## 仓库提供什么

| 能力 | 仓库内置 | 由宿主 Agent 或图像工具完成 |
| --- | --- | --- |
| 标题确认与视觉语义路由 | 是 | Agent 执行 |
| 六套提示词的差异门禁 | 是 | Agent 执行 |
| 普通比例与 5:1 策略 | 是 | Agent 读取规则并调用图像工具 |
| 图像生成与编辑模型 | 否 | 需要宿主具备图像生成或编辑能力 |
| 官方 Logo 获取 | 规则内置 | 需要联网能力或用户提供文件 |
| 确定性 PNG 分层合成 | 是 | Python + Pillow |
| 公众号组合图 | 是 | Python + Pillow |
| 人物身份素材 | 否 | 仅使用用户在当前任务主动提供的附件 |

这不是一个独立的在线生图服务。若宿主 Agent 没有图像生成能力，它仍会交付可复制的提示词和完整 Review 标准，用户可在自己选择的图像工具中完成生成。

## 快速开始

### 1. 克隆

```bash
git clone https://github.com/s840207702/creator-cover-agent-skill.git
cd creator-cover-agent-skill
python3 -m pip install -r requirements.txt
```

### 2. 安装为项目 Skill

Codex 项目：

```bash
mkdir -p .agents/skills
ln -s "$(pwd)" .agents/skills/creator-cover
```

Claude Code 项目：

```bash
mkdir -p .claude/skills
ln -s "$(pwd)" .claude/skills/creator-cover
```

也可以把整个仓库复制到对应的 Skill 目录。

### 3. 直接调用

从主题开始：

```text
使用 $creator-cover，为“本地部署大模型的新手教程”设计封面。先帮我确认标题。
```

标题已确认：

```text
使用 $creator-cover。标题固定为“本地部署大模型”，输出 6 套真正不同的封面提示词。
```

母版已确认：

```text
使用 $creator-cover，把这张满意母版生成完整尺寸包，包括 5:1 和公众号组合图。
```

## 默认输出

- 母版：默认 `3:4`
- 完整尺寸包：`3:4`、`4:3`、`1:1`、`5:2`、`16:9`、`2.35:1`、`5:1`
- `5:1`：精确 `2000×400`
- 公众号组合图：通过 Review 的 `1:1 + 2.35:1`

## 本地脚本

```bash
python3 scripts/render-ratio-pack.py --self-test
python3 scripts/build-wechat-cover-stitch.py --help
python3 scripts/audit_public.py
python3 -m unittest discover -s tests
```

`render-ratio-pack.py` 只用于需要原像素图层重排的确定性任务，尤其是 `5:1`；普通比例首轮不需要预先抠图。

## 隐私与品牌边界

- 除 `examples/approved-covers/` 中明确授权公开展示的成品外，仓库不包含人物原始参考照片、私有案例、历史输出或本机素材目录。
- 人物身份参考只应在当前任务中由用户主动提供，不应被默认归档或提交到 Git。
- 产品名、Logo 和商标归各自权利方所有，只应从官方来源取得并按其规则使用。
- 未经明确授权，不要把客户案例、人物肖像或生成成品提交到公共 `examples/`。
- 示例目录适用单独的 [案例素材说明](./examples/LICENSE.md)。

更多安全边界见 [SECURITY.md](./SECURITY.md)。

## 项目结构

```text
.
├── SKILL.md
├── agents/openai.yaml
├── references/
├── scripts/
├── tests/
├── examples/
├── CONTRIBUTING.md
├── SECURITY.md
└── LICENSE
```

## 贡献

欢迎提交跨平台脚本、比例适配测试、公开授权案例和 Review 改进。请先阅读 [CONTRIBUTING.md](./CONTRIBUTING.md)。

## 许可证

Skill 文本和代码采用 [MIT License](./LICENSE)。案例图片、人物肖像、商标和第三方素材不因根目录 MIT License 自动获得授权。
