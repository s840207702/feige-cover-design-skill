# NOTICE

## Feige Cover Design Skill

本项目由 Feige（非哥）结合长期中文知识类封面创作、抽卡、评审和多比例交付经验独立维护。

本项目基于以下 MIT 开源项目继续创作：

1. [pyang5166/gbro-cover-design](https://github.com/pyang5166/gbro-cover-design)
   - Copyright (c) 2026 狗哥笔记
   - 提供了从文章内容生成真人封面提示词、3:4 默认画幅、人物参考与构图模板等基础思路。
2. [feitangyuan/oh-my-cover-design](https://github.com/feitangyuan/oh-my-cover-design)
   - Copyright (c) 2026 feitangyuan
   - 是 `gbro-cover-design` 声明的上游项目。

Feige 版本在长期实际使用中重新设计和新增了以下主要能力：

- 标题单独确认与五候选机制；
- 根据平台数量、图标语义和品牌关系自动路由；
- 默认六个内容专属视觉事件，而不是固定风格选择；
- 官方平台图标核验与头像型图标降权；
- 以用户确认母版为唯一事实源的完整多比例适配；
- 硬文字、空间利用、人物、手部、Logo、尺寸和色彩 Review；
- 普通比例保持原构图并只修失败比例；
- 精确 `2000×400` 的 `5:1` 空背景补全与原像素前景重排；
- `1:1 + 2.35:1` 公众号组合图与跨平台确定性脚本。

上游版权声明已保留在根目录 [LICENSE](./LICENSE) 中。当前仓库的案例图片适用 [examples/LICENSE.md](./examples/LICENSE.md)，不随 MIT License 开放再利用。
