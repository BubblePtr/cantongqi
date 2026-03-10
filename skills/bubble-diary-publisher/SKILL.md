---
name: bubble-diary-publisher
description: Validate and publish Bubble daily diary entries to the bubble-build Git repository on the Mac mini. Use when Bubble or another agent needs to turn a day's diary into a JSON entry, enforce the Bubble entry contract, and commit/push it to entries/YYYY/YYYY-MM-DD.json in bubble-build.
---

# Bubble Diary Publisher

## 概览

把 Bubble 的单日日记发布到 `bubble-build` 收件箱仓库。先生成符合契约的 JSON，再调用脚本校验并发布，不要手写零散的 Git 命令。

## 工作流

如果本地还没有 `bubble-build` 工作区，先做一次初始化：

1. clone `bubble-build` 到 Bubble 自己决定的工作目录。
2. 在该仓库内配置提交身份：

```bash
git clone git@github.com:BubblePtr/bubble-build.git
git -C <bubble-build-repo> config user.name "Bubble"
git -C <bubble-build-repo> config user.email "bubble@local"
```

日常发布时执行：

1. 生成当天 entry JSON。
2. 运行 `scripts/validate_entry.mjs` 校验字段、格式和业务规则。
3. 进入 Bubble 自己维护的 `bubble-build` 工作区，运行 `scripts/publish_entry.sh` 把文件写入 `entries/YYYY/YYYY-MM-DD.json`，然后 `git pull --rebase`、`git add`、`git commit`、`git push`。
4. 把脚本输出里的 commit hash 或错误信息回报给调用方。

## 使用规则

- 只发布 Bubble 的日记 entry，不处理博客渲染、Cloudflare 或 `ZenBlog` 代码。
- 不要直接手写 Git 流程，统一走 `scripts/publish_entry.sh`。
- 不要修改 `entries/` 之外的文件。
- 如果需要确认字段约束，读取 `references/diary-entry.schema.json`。
- 如果需要确认仓库职责、目录和约束，读取 `references/contract.md`。

## 常用命令

先单独校验：

```bash
node scripts/validate_entry.mjs /tmp/bubble-2026-03-06.json
```

在 `bubble-build` 工作区内直接发布：

```bash
cd <bubble-build-repo>
bash scripts/publish_entry.sh \
  --entry /tmp/bubble-2026-03-06.json
```

允许覆盖同日文件：

```bash
cd <bubble-build-repo>
bash scripts/publish_entry.sh \
  --entry /tmp/bubble-2026-03-06.json \
  --allow-overwrite
```

## 失败处理

- 校验失败：先修 entry JSON，再重新运行脚本。
- `git pull --rebase` 失败：先解决远端冲突，再重试。
- 工作区不干净：先清理仓库，再运行发布脚本。
- 如果目标文件已存在且未传 `--allow-overwrite`，脚本会直接中断。
