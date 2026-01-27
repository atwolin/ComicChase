# Google OAuth to AWS SES Email Federation

這個專案展示如何透過 Workload Identity Federation 讓 Google Cloud 身分存取 AWS SES 發送郵件。

## 📋 架構流程

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Google    │         │   AWS STS   │         │   AWS SES   │
│   OAuth     │ Token   │  AssumeRole │ Creds   │  SendEmail  │
│             ├────────>│             ├────────>│             │
└─────────────┘         └─────────────┘         └─────────────┘
      (1)                     (2)                     (3)
```

### 步驟說明

1. **獲取 Google ID Token**
   - 使用 Google OAuth 驗證
   - 可透過 ADC (Application Default Credentials) 或服務帳戶金鑰

2. **換取 AWS 臨時憑證**
   - 使用 `sts:AssumeRoleWithWebIdentity`
   - 提供 Google ID Token 作為 WebIdentityToken
   - 獲得 AWS 臨時憑證（AccessKey、SecretKey、SessionToken）

3. **發送郵件**
   - 使用臨時憑證調用 AWS SES
   - 發送測試郵件

---

## 🔧 前置設定

### 1. AWS 端設定

#### 1.1 建立 OIDC Identity Provider

```bash
# 透過 AWS CLI
aws iam create-open-id-connect-provider \
    --url https://accounts.google.com \
    --client-id-list YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com \
    --thumbprint-list YOUR_GOOGLE_THUMBPRINT
```

或透過 AWS Console:

- 前往 **IAM** → **Identity providers** → **Add provider**
- 選擇 **OpenID Connect**
- Provider URL: `https://accounts.google.com`
- Audience: 您的 Google OAuth Client ID

#### 1.2 建立 IAM Role

複製檔案 `trust-policy.example.json`，並改名為 `trust-policy.json` 更新相關參數。

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::YOUR_AWS_ACCOUNT_ID:oidc-provider/accounts.google.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "accounts.google.com:aud": "http://YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com"
        }
      }
    }
  ]
}
```

建立 Role:

```bash
aws iam create-role \
    --role-name GoogleFederationRole \
    --assume-role-policy-document file://trust-policy.json
```

#### 1.3 附加 SES 權限

建立檔案 `ses-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ses:SendEmail",
        "ses:SendRawEmail"
      ],
      "Resource": "*"
    }
  ]
}
```

附加權限:

```bash
aws iam put-role-policy \
    --role-name GoogleFederationRole \
    --policy-name SESPolicy \
    --policy-document file://ses-policy.json
```

#### 1.4 清理設定檔（可選）

上述步驟中建立的 `trust-policy.json` 和 `ses-policy.json` 僅在初始設定時需要。設定完成後，這些政策已存在於 AWS IAM 中，本地檔案可以刪除：

```bash
# 刪除臨時設定檔（政策已存在於 AWS IAM，不再需要本地檔案）
rm trust-policy.json
rm ses-policy.json
```

> **💡 提示**: 如果需要保留作為文檔參考，可以改名為 `.example` 後綴（如 `trust-policy.example.json`）並提交到版本控制。

#### 1.5 驗證 SES 郵件地址

```bash
# 驗證發件人郵箱
aws ses verify-email-identity --email-address your-email@example.com

# 驗證收件人郵箱（沙盒模式需要）
aws ses verify-email-identity --email-address recipient@example.com

# 檢查驗證狀態
aws sesv2 list-email-identities
```

---

### 2. Google Cloud 端設定

#### 2.1 啟用必要 API

```bash
gcloud services enable iamcredentials.googleapis.com
gcloud services enable sts.googleapis.com
```

#### 2.2 設定本地驗證

```bash
# 使用 Application Default Credentials
gcloud auth application-default login
```

---

## 🚀 執行腳本

### Python 版本

```bash
# 安裝依賴
pip install boto3 google-auth google-auth-httplib2

# 執行
python send_email_via_google_aws.py
```

---

## 🔍 故障排除

### 問題 1: Google ID Token 獲取失敗

**錯誤訊息**: `Could not automatically determine credentials`

**解決方案**:

```bash
# 確保已登入 gcloud
gcloud auth application-default login
```

### 問題 2: AWS STS AssumeRole 失敗

**錯誤訊息**: `Not authorized to perform sts:AssumeRoleWithWebIdentity`

**檢查清單**:

1. ✅ OIDC Provider 是否已在 AWS IAM 中建立
2. ✅ Role Trust Policy 中的 `accounts.google.com:aud` 是否正確
3. ✅ Google Client ID 是否正確
4. ✅ Role ARN 是否正確

**驗證 Trust Policy**:

```bash
aws iam get-role --role-name GoogleFederationRole
```

### 問題 3: SES 發送郵件失敗

**錯誤訊息**: `Email address is not verified`

**解決方案**:

```bash
# 驗證郵箱
aws ses verify-email-identity --email-address your-email@example.com

# 檢查驗證狀態
aws sesv2 list-email-identities

# 等待驗證郵件並點擊確認連結
```

**錯誤訊息**: `Access Denied`

**檢查 IAM 權限**:

```bash
# 檢查 Role 的 Policy
aws iam list-role-policies --role-name GoogleFederationRole
aws iam get-role-policy --role-name GoogleFederationRole --policy-name SESPolicy
```

---

## 📊 測試流程

### 1. 測試 Google Token 獲取

```bash
# Python
python -c "
from send_email_via_google_aws import get_google_id_token
token = get_google_id_token()
print(f'Token 長度: {len(token)}')
"

# Node.js
node -e "
const { getGoogleIdToken } = require('./send_email_via_google_aws');
getGoogleIdToken().then(token => console.log('Token 長度:', token.length));
"
```

### 2. 測試 AWS STS

```bash
aws sts assume-role-with-web-identity \
    --role-arn arn:aws:iam::YOUR_AWS_ACCOUNT_ID:role/GoogleFederationRole \
    --role-session-name test-session \
    --web-identity-token "YOUR_GOOGLE_ID_TOKEN"
```

### 3. 測試 SES（使用臨時憑證）

```bash
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_SESSION_TOKEN="..."

aws ses send-email \
    --from your-email@example.com \
    --to recipient@example.com \
    --subject "Test" \
    --text "Test message"
```

---

## 📝 配置檢查清單

在執行腳本前，請確認：

- [ ] AWS OIDC Provider 已建立 (`accounts.google.com`)
- [ ] AWS IAM Role 已建立並配置 Trust Policy
- [ ] IAM Role 已附加 SES 權限
- [ ] SES 發件人郵箱已驗證
- [ ] SES 收件人郵箱已驗證（沙盒模式）
- [ ] Google Cloud 已啟用 IAM Credentials API
- [ ] 已執行 `gcloud auth application-default login`
- [ ] 腳本中的配置已更新（Role ARN, Email 等）

---

## 🎯 下一步

### 生產環境部署

1. **移出 SES 沙盒模式**

   ```bash
   # 提交移出沙盒請求
   # 前往 AWS Console → SES → Account dashboard → Request production access
   ```

2. **使用 Workload Identity Pool**（推薦）
   - 設定 Google Cloud Workload Identity Pool
   - 配置 service account impersonation
   - 移除對服務帳戶金鑰的依賴

3. **監控和日誌**

   ```bash
   # AWS CloudWatch 日誌
   aws logs tail /aws/sts/AssumeRoleWithWebIdentity --follow

   # SES 發送統計
   aws sesv2 get-account
   ```

---

## 🔗 參考資源

- [Google Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation)
- [AWS STS AssumeRoleWithWebIdentity](https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRoleWithWebIdentity.html)
- [AWS SES Developer Guide](https://docs.aws.amazon.com/ses/latest/dg/Welcome.html)
- [Google Auth Library](https://github.com/googleapis/google-auth-library-nodejs)
