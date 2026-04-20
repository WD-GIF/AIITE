# 日常写代码：拉取、提交、合并（简明版）

明天开始写代码时，按下面顺序做即可。**主分支 `main` 由主开发者合并**；协作者通过 **Pull Request（PR）** 把改动交给你审阅后再并进 `main`。

---

## 目录在哪

| 谁 | 本机工程路径 |
|----|----------------|
| 主开发者（ubuntu） | `/home/AIITE` |
| 协作者（huacz） | `/home/huacz/AIITE`（即 huacz 用户下的 `~/AIITE`） |

若协作者登录的是 **`huacz666`** 用户，则路径为 **`/home/huacz666/AIITE`**（同样是家目录里的 `~/AIITE`）。

---

## 1. 开工：先拉最新代码

**两个人都要做**（在各自目录里）：

```bash
# 主开发者
cd /home/AIITE

# 协作者（huacz）
cd ~/AIITE
# 或：cd /home/huacz/AIITE
```

然后：

```bash
git checkout main
git pull origin main
```

说明：`git pull` = 从 GitHub 拉取 `main` 的最新提交并合并到你本机的 `main`。

---

## 2. 改代码：请在自己的分支上改

**不要两个人直接在 `main` 上改**，避免冲突和不好追溯。协作者（以及主开发者做大功能时）建议：

```bash
git checkout -b feature/简短说明
# 例如：feature/huacz-login-fix
```

然后正常编辑文件。小功能请尽量只在约定目录里改（如 `features/`、`contrib/`、`docs/`，见 `docs/collaboration-access.md`）。

---

## 3. 提交并推到 GitHub

改完后：

```bash
git status
git add .
git commit -m "一句话说明改了什么"
git push -u origin feature/简短说明
```

第一次推这个分支要用 `-u origin 分支名`；以后在同一分支上可以直接 `git push`。

---

## 4. 合并到 `main`：谁点「合并」

### 协作者（huacz）

1. 打开浏览器进入仓库：**https://github.com/WD-GIF/AIITE**  
2. 一般会看到 **Compare & pull request**，或点 **Pull requests → New pull request**。  
3. **base** 选 **`main`**，**compare** 选你的 **`feature/...`**。  
4. 写清楚标题和说明 → **Create pull request**。  
5. **不要自己合并**（若仓库要求审批）：等主开发者在 GitHub 上 **Review → Approve → Merge pull request**。

### 主开发者（你）

1. 打开 GitHub 上对方发来的 **PR**。  
2. 看 **Files changed**，没问题就 **Approve**，再点 **Merge pull request**（或按团队规则 **Squash and merge**）。  
3. 合并后，在你本机更新 `main`：

```bash
cd /home/AIITE
git checkout main
git pull origin main
```

协作者那边也同样执行一次 `git checkout main` 和 `git pull origin main`，下次再从最新 `main` 拉分支开发。

---

## 5. 主开发者自己改完想并进 `main`

若你也在 **`feature/你的分支`** 上开发：

```bash
cd /home/AIITE
git push -u origin feature/你的分支
```

若仓库规定 **`main` 也必须走 PR**：同样在网页上开 PR，自己审自己合（或等第二人审，看你们规则）。

若允许你 **直接推 `main`**（且分支保护未禁止）：

```bash
git checkout main
git pull origin main
# 改代码…
git add .
git commit -m "说明"
git push origin main
```

你们当前仓库若已对 **`main` 开启保护**，一般**不能**直推，请仍以 **PR 合并**为准。

---

## 6. 一句话流程

1. `cd` 到各自的 **AIITE** 目录 → `git checkout main` → **`git pull origin main`**  
2. **`git checkout -b feature/xxx`** → 写代码 → **`git add` / `git commit` / `git push`**  
3. 网页上 **New Pull Request** → 主开发者 **Merge** → 双方再 **`git pull origin main`**

---

有问题时先看：`docs/collaboration-access.md`（权限与 SSH）、根目录 `CODEOWNERS`（谁审哪些路径）。
