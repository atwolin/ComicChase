# 快速入門指南：Google-to-AWS Email Federation

## 🚀 5 分鐘快速開始

### 步驟 1: 安裝依賴

選擇以下任一方式安裝：

#### 方式 A: 一鍵安裝（推薦）

```bash
# Python 依賴
pip install boto3 google-auth google-auth-httplib2 google-auth-oauthlib python-dotenv
```

#### 方式 B: 分別安裝

**Python 版本:**

```bash
pip install boto3 google-auth google-auth-httplib2 google-auth-oauthlib python-dotenv
```

> 💡 **提示**: 安裝完成後，請執行 `python test_environment.py` 檢查環境是否正確配置。

### 步驟 2: 設定 Google 認證

```bash
gcloud auth application-default login
```

### 步驟 3: 檢查環境

```bash
python test_environment.py
```

### 步驟 4: 更新配置

編輯腳本中的以下參數：

**Python**: `send_email_via_google_aws.py`

```python
# 必須更新的配置
AWS_ROLE_ARN = 'arn:aws:iam::YOUR_ACCOUNT:role/YOUR_ROLE'
SENDER_EMAIL = 'your-verified@email.com'
RECIPIENT_EMAIL = 'recipient@email.com'
```

### 步驟 5: 執行

```bash
# Python
python send_email_via_google_aws.py
```

---

## 📋 前置檢查清單

在執行前，確保：

### AWS 端

- [ ] 已建立 OIDC Provider (`accounts.google.com`)
- [ ] 已建立 IAM Role 並配置 Trust Policy
- [ ] Role 已附加 SES SendEmail 權限
- [ ] 發件人郵箱已在 SES 驗證
- [ ] 收件人郵箱已在 SES 驗證（如在沙盒模式）

驗證方法：

```bash
# 檢查 OIDC Provider
aws iam list-open-id-connect-providers

# 檢查 Role
aws iam get-role --role-name GoogleFederationRole

# 檢查已驗證郵箱
aws sesv2 list-email-identities
```

### Google 端

- [ ] 已執行 `gcloud auth application-default login`
- [ ] 或已設定 `GOOGLE_APPLICATION_CREDENTIALS` 環境變數

驗證方法：

```bash
# 檢查登入狀態
gcloud auth application-default print-access-token

# 檢查 Project
gcloud config get-value project
```

---

## 🔧 快速設定命令

### AWS 快速設定

```bash
# 1. 建立 IAM Role
aws iam create-role \
    --role-name GoogleFederationRole \
    --assume-role-policy-document file://trust-policy.json

# 2. 附加 SES 權限
cat > ses-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["ses:SendEmail", "ses:SendRawEmail"],
    "Resource": "*"
  }]
}
EOF

aws iam put-role-policy \
    --role-name GoogleFederationRole \
    --policy-name SESPolicy \
    --policy-document file://ses-policy.json

# 3. 驗證郵箱
aws ses verify-email-identity --email-address your@email.com
```

### Google 快速設定

```bash
# 登入並設定 ADC
gcloud auth application-default login

# 啟用必要 API
gcloud services enable iamcredentials.googleapis.com
gcloud services enable sts.googleapis.com
```

---

## 🐛 常見問題排除

### Q: 執行時出現 "Could not automatically determine credentials"

**A:** 執行以下命令：

```bash
gcloud auth application-default login
```

### Q: AWS STS 返回 "Not authorized to perform sts:AssumeRoleWithWebIdentity"

**A:** 檢查：

1. OIDC Provider 是否已建立
2. Trust Policy 中的 `aud` 是否正確
3. Role ARN 是否正確

```bash
# 檢查 Trust Policy
aws iam get-role --role-name GoogleFederationRole --query 'Role.AssumeRolePolicyDocument'
```

### Q: SES 返回 "Email address is not verified"

**A:** 驗證郵箱：

```bash
aws ses verify-email-identity --email-address your@email.com
aws sesv2 list-email-identities
```

檢查您的郵箱，點擊驗證連結。

---

## 📊 執行流程圖

```
開始
  ↓
[檢查依賴] → ❌ → 執行 pip install / npm install
  ↓ ✅
[Google 登入] → ❌ → gcloud auth application-default login
  ↓ ✅
[檢查 AWS 設定] → ❌ → 建立 OIDC Provider 和 Role
  ↓ ✅
[檢查 SES 郵箱] → ❌ → aws ses verify-email-identity
  ↓ ✅
[執行腳本]
  ↓
成功發送郵件！ 🎉
```

---

## 📁 檔案說明

| 檔案 | 說明 |
|------|------|
| `send_email_via_google_aws.py` | Python 主腳本 |
| `test_environment.py` | 環境檢查腳本 |
| `trust-policy.json` | AWS IAM Role Trust Policy |
| `config.template.json` | 配置檔案模板 |
| `README_EMAIL_FEDERATION.md` | 完整技術文檔 |
| `QUICKSTART.md` | 本快速入門指南 |

---

## 🎯 下一步

1. ✅ 完成前置設定
2. ✅ 執行 `test_environment.py` 確認環境
3. ✅ 更新腳本配置
4. ✅ 執行主腳本發送測試郵件
5. 📖 閱讀 `README_EMAIL_FEDERATION.md` 了解進階用法

---

## 💡 提示

- 首次使用建議先執行 `test_environment.py` 檢查環境
- SES 沙盒模式下，發件人和收件人都需要驗證
- 生產環境請移出 SES 沙盒模式
- 詳細架構說明請參考 `README_EMAIL_FEDERATION.md`

有問題？查看完整文檔： `README_EMAIL_FEDERATION.md`
