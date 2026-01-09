# Git 安装指南

## 方法 1：下载并安装 Git（推荐）

1. 访问 Git 官网：https://git-scm.com/downloads
2. 下载 Windows 版本（64-bit Git for Windows Setup）
3. 运行下载的安装程序
4. 在安装过程中，保持默认设置即可：
   - 选择安装路径（默认：C:\Program Files\Git）
   - 选择组件（保持默认）
   - 选择开始菜单文件夹（保持默认）
   - 选择 Git 默认编辑器（推荐使用 Vim 或 Notepad++）
   - 调整 PATH 环境变量（推荐选择 "Git from the command line and also from 3rd-party software"）
   - 选择 HTTPS 传输后端（推荐使用 OpenSSL）
   - 配置行尾转换（推荐选择 "Checkout Windows-style, commit Unix-style line endings"）
   - 选择终端模拟器（推荐使用 MinTTY）
   - 选择默认的 git pull 行为（推荐选择默认）
   - 选择凭证助手（推荐选择默认）
   - 额外配置选项（保持默认）
   - 实验性功能（保持默认）

5. 点击 "Install" 开始安装
6. 安装完成后，点击 "Finish"

## 方法 2：使用 Chocolatey（如果已安装）

如果您已经安装了 Chocolatey 包管理器，可以运行：

```powershell
choco install git
```

## 验证安装

安装完成后，打开新的 PowerShell 窗口，运行：

```powershell
git --version
```

如果显示 Git 版本号（如 git version 2.43.0），说明安装成功。

## 配置 Git

安装完成后，建议配置您的用户信息：

```powershell
git config --global user.name "您的用户名"
git config --global user.email "您的邮箱"
```

## 上传项目到 GitHub

安装 Git 后，返回此目录，运行以下命令上传项目：

```powershell
cd "c:\Users\longyaosi\Downloads\离线网页下载器（版本2）"
git init
git add .
git commit -m "初始提交：离线网页下载器 v2"
git branch -M main
git remote add origin git@github.com:2489742701/HtmlDown2.git
git push -u origin main
```

## 注意事项

- 如果使用 SSH 方式（git@github.com），需要先配置 SSH 密钥
- 如果没有 SSH 密钥，可以使用 HTTPS 方式：
  ```powershell
  git remote add origin https://github.com/2489742701/HtmlDown2.git
  ```
- 确保 GitHub 仓库已经创建

## SSH 密钥配置（可选）

如果需要使用 SSH 方式：

1. 生成 SSH 密钥：
   ```powershell
   ssh-keygen -t ed25519 -C "您的邮箱"
   ```

2. 将公钥添加到 GitHub：
   - 复制公钥内容：`cat ~/.ssh/id_ed25519.pub`
   - 访问 GitHub Settings -> SSH and GPG keys -> New SSH key
   - 粘贴公钥内容并保存

3. 测试连接：
   ```powershell
   ssh -T git@github.com
   ```

安装完成后，请告诉我，我会帮您继续上传项目。
