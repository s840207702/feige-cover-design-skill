# 贡献指南

感谢你改进 Feige Cover Design Skill。

## 可以贡献什么

- 普通比例和超宽比例的可复现失败用例；
- 更可靠的文字、构图、人物和 Logo Review 方法；
- Windows、macOS、Linux 可运行的确定性图像脚本；
- 明确获得公开展示授权的示例；
- 更清晰、但不扩大权限边界的 Skill 指令。

## 提交要求

1. 不提交真人身份参考、客户素材、私有输出、访问凭证或本机绝对路径。
2. 不提交来源不明的 Logo、字体、截图、图片和电影画面。
3. 新脚本应提供可重复的自测或单元测试。
4. 修改 Skill 行为时，说明真实失败场景和预期改进，不为单个偶发现象增加通用强制规则。
5. 提交前运行：

```bash
python3 scripts/audit_public.py
python3 scripts/render-ratio-pack.py --self-test
python3 -m unittest discover -s tests
```

## 案例贡献

案例必须说明作者、来源、人物肖像授权、Logo/商标用途和允许的再使用范围。默认情况下，案例只用于仓库展示与回归测试，不随 MIT License 开放再利用。
