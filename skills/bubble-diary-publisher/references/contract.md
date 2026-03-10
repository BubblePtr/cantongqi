# bubble-build 合同

`bubble-build` 是 Bubble 的原始日记收件箱仓库，不负责博客渲染。

## 仓库结构

```text
bubble-build/
  entries/
    YYYY/
      YYYY-MM-DD.json
  schemas/
    diary-entry.schema.json
```

## entry 规则

- 文件路径必须是 `entries/YYYY/YYYY-MM-DD.json`
- `entry_id` 必须等于 `bubble-${date}`
- `content_markdown` 只能是 Markdown，不能包含 `import`、`export`、`<script>`
- 默认不覆盖同日文件，除非显式传 `--allow-overwrite`

## 发布前置条件

- 本地已有 `bubble-build` clone
- 已为该仓库配置 `git config user.name "Bubble"` 和 `git config user.email "bubble@local"`
- 本地 Git 工作区保持干净
- 仓库远端和认证已经配置好

## 发布结果

成功时会：

1. 把 entry 写入 `entries/YYYY/YYYY-MM-DD.json`
2. 创建一条 commit
3. push 到 `bubble-build`
4. 返回 commit hash
