#!/usr/bin/env python3
"""
Google OAuth to AWS SES Email Sender
這個腳本展示如何：
1. 從 Google OAuth 獲取 ID Token
2. 使用 AWS STS AssumeRoleWithWebIdentity 換取臨時憑證
3. 使用臨時憑證透過 AWS SES 發送郵件
"""

import json
import os

import boto3

# 載入 .env 文件
from dotenv import load_dotenv
from google.oauth2 import service_account

load_dotenv()

# ============================================
# 配置參數
# ============================================

# AWS 配置 - 從環境變數讀取以避免暴露 Account ID
AWS_REGION = os.getenv("AWS_SES_REGION_NAME", "us-east-1")
AWS_ROLE_ARN = os.getenv(
    "AWS_ROLE_ARN", ""
)  # 例: arn:aws:iam::123456789012:role/your-role
AWS_OIDC_PROVIDER_ARN = os.getenv(
    "AWS_OIDC_PROVIDER_ARN", ""
)  # 例: arn:aws:iam::123456789012:oidc-provider/accounts.google.com

# Google 配置 - 從環境變數讀取
GOOGLE_OAUTH_CLIENT_ID = os.getenv(
    "GOOGLE_SA_CLIENT_ID", ""
)  # Service Account Unique ID
GOOGLE_SERVICE_ACCOUNT = os.getenv(
    "GOOGLE_SERVICE_ACCOUNT", ""
)  # Service Account Email

# Email 配置 - 從 .env 讀取
SENDER_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "your-email@example.com")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", "your-email@example.com")
EMAIL_SUBJECT = "Test Email via Google-to-AWS Federation"
EMAIL_BODY = """
This is a test email sent via:
1. Google OAuth authentication
2. AWS STS AssumeRoleWithWebIdentity
3. AWS SES

If you received this, the federation is working correctly!
"""


def get_id_token_via_iam_api():
    """
    使用 IAM Credentials API (generateIdToken) 獲取 Token
    這需要執行環境的憑證擁有 roles/iam.serviceAccountTokenCreator 權限
    """
    import json

    import google.auth.transport.requests

    print("   🔄 調用 IAM Credentials API generateIdToken...")

    # 1. 使用 Service Account 金鑰檔案認證（而非 ADC）
    #    這樣才能使用 SA 自己的 Token Creator 權限
    from google.oauth2 import service_account as sa_module

    key_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not key_file:
        print("   ⚠️ 未設定 GOOGLE_APPLICATION_CREDENTIALS，無法使用 IAM API 方法")
        return None

    creds = sa_module.Credentials.from_service_account_file(
        key_file, scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    auth_req = google.auth.transport.requests.Request()
    creds.refresh(auth_req)

    # 2. 建構 API 請求
    # IAM API 產生的 token 沒有 azp claim，AWS 會直接用 aud 驗證
    # 所以 target_audience 必須與 AWS Trust Policy 的 accounts.google.com:aud 一致
    target_audience = GOOGLE_SERVICE_ACCOUNT  # 使用 service account email 作為 audience

    service_account_email = GOOGLE_SERVICE_ACCOUNT
    url = f"https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/{service_account_email}:generateIdToken"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {creds.token}",
    }

    body = {"audience": target_audience, "includeEmail": True}

    # 3. 發送請求
    import urllib.error
    import urllib.request

    try:
        req = urllib.request.Request(
            url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST"
        )
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            token = result.get("token")
            print("   ✅ IAM API 调用成功")
            return token
    except urllib.error.HTTPError as e:
        # 這是專門處理 HTTP 錯誤（如 403, 500）的情況
        print(f" ❌ IAM API 調用失敗，HTTP 狀態碼: {e.code}")
        try:
            err_body = e.read().decode("utf-8")
            print(f"      錯誤詳情: {err_body}")
        except (OSError, UnicodeDecodeError) as read_err:
            # 只捕獲讀取或解碼時可能發生的具體錯誤
            print(f"      無法讀取錯誤內容: {read_err}")
        return None
    except urllib.error.URLError as e:
        # 處理連線問題（如 DNS 錯誤、斷網）
        print(f" ❌ 網路連線失敗: {e.reason}")
        return None
    except Exception as e:
        # 處理其他非預期的程式邏輯錯誤
        print(f" ❌ 發生非預期錯誤: {e}")
        return None


def get_google_id_token():
    """
    獲取 Google ID Token
    根據使用者要求，優先使用 IAM Credentials API (generateIdToken)
    """
    print("🔑 獲取 Google ID Token...")

    import google.auth.transport.requests
    import google.oauth2.id_token

    token = None

    # 優先嘗試使用 IAM API (因為可以自訂 Audience)
    try:
        print("   嘗試使用 IAM Credentials API (generateIdToken)...")
        token = get_id_token_via_iam_api()
    except Exception as e:
        print(f"   ⚠️  IAM API 方法失敗: {e}")

    # 如果 API 方法失敗，才嘗試本地簽署 (ADC/Key)
    if not token:
        print("   ⚠️  API 方法失敗，嘗試使用本地簽署 (ADC/Key)...")
        try:
            # 檢查是否有 GOOGLE_APPLICATION_CREDENTIALS 環境變數
            if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
                print(f"   使用金鑰檔案: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")

                creds = service_account.IDTokenCredentials.from_service_account_file(
                    os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
                    target_audience=GOOGLE_OAUTH_CLIENT_ID,
                )
                request = google.auth.transport.requests.Request()
                creds.refresh(request)
                token = creds.token

            else:
                # 使用 ADC
                print("   使用 Application Default Credentials")
                credentials, project = google.auth.default()

                request = google.auth.transport.requests.Request()

                # 如果是 User Credentials (gcloud auth application-default login)
                if hasattr(credentials, "refresh"):
                    credentials.refresh(request)
                    token = credentials.id_token
                # 如果是 Service Account Credentials
                elif hasattr(credentials, "signer"):
                    token = credentials.token
                else:
                    # 嘗試使用 id_token 模組獲取
                    token = google.oauth2.id_token.fetch_id_token(
                        request, GOOGLE_OAUTH_CLIENT_ID
                    )
        except Exception as e:
            print(f"   ❌ 本地簽署也失敗: {e}")

    if not token:
        raise Exception("無法獲取 Token")

    # DEBUG: 解析 Token 查看 Audience
    import base64

    parts = token.split(".")
    if len(parts) > 1:
        padding = "=" * (4 - len(parts[1]) % 4)
        payload = json.loads(
            base64.urlsafe_b64decode(parts[1] + padding).decode("utf-8")
        )
        print(f"   ℹ️  Token Audience (aud): {payload.get('aud')}")
        print(f"   ℹ️  Token Issuer (iss): {payload.get('iss')}")
        if payload.get("azp"):
            print(f"   ℹ️  Token AZP (azp): {payload.get('azp')}")

    print(f"✅ 成功獲取 Google ID Token (前20字符): {token[:20]}...")
    return token

    # except Exception as e: # 舊的錯誤處理被移除了，因為上面已經有 raise
    #    print(f"❌ 獲取 Google ID Token 失敗: {e}")
    # ... (省略舊的代碼)


def assume_role_with_web_identity(google_id_token):
    """
    使用 Google ID Token 透過 AWS STS 換取臨時憑證
    """
    print("\n🔄 使用 Google ID Token 換取 AWS 臨時憑證...")

    # 創建 STS 客戶端（不需要憑證）
    sts_client = boto3.client("sts", region_name=AWS_REGION)

    try:
        # 使用 AssumeRoleWithWebIdentity
        response = sts_client.assume_role_with_web_identity(
            RoleArn=AWS_ROLE_ARN,
            RoleSessionName="GoogleFederationSession",
            WebIdentityToken=google_id_token,
            DurationSeconds=3600,  # 1小時
        )

        credentials = response["Credentials"]

        print("✅ 成功獲取 AWS 臨時憑證")
        print(f"   AccessKeyId: {credentials['AccessKeyId'][:20]}...")
        print(f"   過期時間: {credentials['Expiration']}")

        return credentials

    except Exception as e:
        print(f"❌ 換取 AWS 憑證失敗: {e}")
        print("\n💡 提示：")
        print("   1. 確保 AWS Role 已建立並配置正確的 Trust Policy")
        print("   2. 確保 Google OIDC Provider 已在 AWS IAM 中註冊")
        print("   3. 檢查 Role ARN 是否正確")
        raise


def send_email_via_ses(aws_credentials):
    """
    使用 AWS 臨時憑證透過 SES 發送郵件
    """
    print("\n📧 使用 AWS SES 發送郵件...")

    # 使用臨時憑證創建 SES 客戶端
    ses_client = boto3.client(
        "ses",
        region_name=AWS_REGION,
        aws_access_key_id=aws_credentials["AccessKeyId"],
        aws_secret_access_key=aws_credentials["SecretAccessKey"],
        aws_session_token=aws_credentials["SessionToken"],
    )

    try:
        response = ses_client.send_email(
            Source=SENDER_EMAIL,
            Destination={"ToAddresses": [RECIPIENT_EMAIL]},
            Message={
                "Subject": {"Data": EMAIL_SUBJECT, "Charset": "UTF-8"},
                "Body": {"Text": {"Data": EMAIL_BODY, "Charset": "UTF-8"}},
            },
        )

        print("✅ 郵件發送成功！")
        print(f"   Message ID: {response['MessageId']}")
        return response

    except Exception as e:
        print(f"❌ 發送郵件失敗: {e}")
        print("\n💡 提示：")
        print("   1. 確保發件人和收件人郵箱已在 SES 中驗證（沙盒模式）")
        print("   2. 確保 IAM Role 有 ses:SendEmail 權限")
        print("   3. 如果在生產環境，確保已移出 SES 沙盒")
        raise


def main():
    """
    主流程：Google OAuth → AWS STS → AWS SES
    """
    print("=" * 60)
    print("Google OAuth to AWS SES Email Sender")
    print("=" * 60)

    try:
        # 步驟 1: 獲取 Google ID Token
        google_token = get_google_id_token()

        # 步驟 2: 使用 Google Token 換取 AWS 臨時憑證
        aws_credentials = assume_role_with_web_identity(google_token)

        # 步驟 3: 使用 AWS 憑證發送郵件
        send_email_via_ses(aws_credentials)

        print("\n" + "=" * 60)
        print("✅ 完成！整個流程執行成功！")
        print("=" * 60)

    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ 執行失敗: {e}")
        print("=" * 60)
        return 1

    return 0


if __name__ == "__main__":
    import sys

    print("""
⚠️  使用前請更新以下配置：
    1. AWS_ROLE_ARN - 您的 AWS IAM Role ARN
    2. SENDER_EMAIL - 已驗證的發件人郵箱
    3. RECIPIENT_EMAIL - 收件人郵箱

📝 前置作業：
    1. 在 AWS IAM 中建立 OIDC Provider (accounts.google.com)
    2. 建立 IAM Role 並配置 Trust Policy 允許 Google 聯盟
    3. 在 SES 中驗證發件人和收件人郵箱
    4. 執行: gcloud auth application-default login

    或提供服務帳戶金鑰：
    export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
    """)

    user_input = input("\n按 Enter 繼續執行，或 Ctrl+C 取消...")

    sys.exit(main())
