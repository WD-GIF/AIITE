# 协作权限说明（ubuntu 主开发 + huacz 协作者）

本文档说明服务器侧已完成的配置，以及 **必须在 GitHub 网页上** 由主开发者完成的步骤。

## 服务器侧（已完成）

| 项 | 说明 |
|----|------|
| Linux 用户 | `ubuntu`：主开发者工作区 `/home/AIITE` |
| Linux 用户 | `huacz`：工作区 `/home/huacz/AIITE`（从主仓库本地克隆，远程为 `git@github.com:WD-GIF/AIITE.git`） |
| Linux 用户 | `huacz666`：工作区 `/home/huacz666/AIITE`，`origin` 已从 HTTPS 改为 **SSH**（`git@github.com:WD-GIF/AIITE.git`） |
| huacz Git 身份 | `user.name=huacz`，`user.email=3248197416@qq.com`（`huacz` 与 `huacz666` 两个 Linux 用户均已设相同提交身份，可按需分别修改） |
| huacz / huacz666 SSH | 各用户独立密钥 `~/.ssh/id_ed25519` 与 `~/.ssh/config`（两把公钥均需加到 **同一 GitHub 账号 huacz** 的 SSH keys 中） |

### huacz 将公钥登记到 GitHub（必做，否则无法 push）

在服务器上执行（或由 huacz 登录后执行）：

```bash
sudo cat /home/huacz/.ssh/id_ed25519.pub
```

复制整行输出，使用 **GitHub 账号 huacz** 登录 → **Settings → SSH and GPG keys → New SSH key** → 粘贴保存。

验证：

```bash
sudo -u huacz ssh -T git@github.com
```

看到 `Hi huacz!` 即表示成功。

### Linux 用户 `huacz666`（第二把公钥，必做）

若协作者用 **`huacz666`** 登录服务器开发，该账号使用 **另一把** SSH 私钥，必须在 **同一 GitHub 账号 `huacz`** 下再添加一条 SSH key（GitHub 允许多个 key）。

```bash
sudo cat /home/huacz666/.ssh/id_ed25519.pub
```

复制整行 → **Settings → SSH and GPG keys → New SSH key**（标题可写 `server-huacz666`）。

验证：

```bash
sudo -u huacz666 ssh -T git@github.com
```

应出现 `Hi huacz!`。添加前 `git push` 会报 `Permission denied (publickey)`，属正常现象。

## GitHub 仓库侧（主开发者 WD-GIF 在网页上操作）

### 1. 邀请协作者

仓库 **WD-GIF/AIITE** → **Settings → Collaborators** → 添加 **`huacz`**，角色建议 **Write**（具体以团队策略为准）。

### 2. 保护主线（推荐：仅主开发者可合并进 main）

**Settings → Branches → Branch protection rules** → 为 **`main`** 新增规则，建议勾选：

- **Require a pull request before merging**
- **Require approvals**（至少 1，由主开发者审核）
- **Do not allow bypassing the above settings**（按需）
- 如界面提供 **Restrict who can push to matching branches**：仅允许 **`WD-GIF`** 直接推 `main`（或仅管理员）

这样 **huacz 只能推 feature 分支并通过 PR 合并**，无法单独决定主线内容。

### 3. CODEOWNERS（已提交到仓库）

根目录 `CODEOWNERS` 已指定 **`@WD-GIF`** 为默认所有者；`/docs/` 由 **`@WD-GIF`** 与 **`@huacz`** 共同列出。若启用 **Require review from Code Owners**，请确认组织/仓库设置支持该选项。

## 日常协作命令（huacz）

```bash
cd /home/huacz/AIITE
git fetch origin
git checkout main
git pull origin main
git checkout -b feature/huacz-简述
# 修改后
git add .
git commit -m "说明"
git push -u origin feature/huacz-简述
```

随后在 GitHub 上 **New Pull Request**，由 **WD-GIF** 审核并合并。

## 日常协作命令（huacz666）

与 `huacz` 相同，工作目录为 `/home/huacz666/AIITE`，使用 SSH 远程后 **不再出现** `Username for 'https://github.com':` 提示。

```bash
cd ~/AIITE
git pull origin main
git push -u origin feature/分支名
```
