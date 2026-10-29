# 模型访问

模型权重托管在 Hugging Face 的手动审批仓库：

<https://huggingface.co/xujianing1990/qwen3.5-9b-fp8-1949-1978-r79-public>

GitHub 项目邀请码：

```text
R79-GH-345F33542A6AA0D3
```

## 申请和下载

1. 登录你自己的 Hugging Face 账号并打开上面的模型页。
2. 点击申请访问，在 `GitHub invitation code` 字段填写本页邀请码，并说明用途。
3. 等待仓库所有者按账号审核。邀请码正确不代表自动批准；访问权绑定到申请人的 Hugging Face 账号。
4. 获批后在本机登录 Hugging Face：

   ```bash
   hf auth login
   ```

   请使用你自己的只读 token，不要把 token 提交到 GitHub。

5. 在项目根目录运行：

   ```bash
   r79-legal download-model
   ```

   或直接运行 `bash scripts/bootstrap.sh`；Windows PowerShell 可运行 `scripts/bootstrap.ps1`。

未登录或未获批账号可以查看模型卡，但不能从 Hugging Face 下载模型文件。批准后，项目仍按 `.env.example` 中冻结的仓库与 revision 下载，以保证运行内容可复现。

## 访问边界

- 邀请码只用于证明申请人来自本 GitHub 项目，不是 Hugging Face 密码。
- Hugging Face 的门禁按个人账号授权；不要共享账号或 token。
- 仓库所有者可随时撤销单个账号的访问权。
- 模型仍受模型卡、Apache-2.0 许可和项目中的安全/法律限制约束。
