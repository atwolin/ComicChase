#!/usr/bin/env python3
"""
簡單的測試腳本 - 驗證各個步驟是否正常運作
"""

import sys


def test_google_auth():
    """測試 Google 認證"""
    print("1️⃣ 測試 Google 認證...")
    try:
        import google.auth

        credentials, project = google.auth.default()
        print(f"   ✅ 成功！Project: {project}")
        return True
    except Exception as e:
        print(f"   ❌ 失敗: {e}")
        print("   💡 提示：執行 'gcloud auth application-default login'")
        return False


def test_aws_credentials():
    """測試 AWS 認證（選用）"""
    print("\n2️⃣ 測試 AWS 憑證（選用）...")
    try:
        import boto3

        sts = boto3.client("sts")
        identity = sts.get_caller_identity()
        print(f"   ✅ AWS 身分: {identity['Arn']}")
        return True
    except Exception:
        print("   ⚠️  未配置 AWS 憑證（這是正常的，我們將使用 Google Token）")
        return True


def test_ses_verified_emails():
    """列出 SES 已驗證的郵箱"""
    print("\n3️⃣ 列出 SES 已驗證的郵箱...")
    try:
        import boto3

        ses = boto3.client("sesv2", region_name="us-east-1")
        response = ses.list_email_identities()

        if response["EmailIdentities"]:
            print("   ✅ 已驗證的郵箱：")
            for identity in response["EmailIdentities"]:
                print(f"      - {identity['IdentityName']}")
        else:
            print("   ⚠️  未找到已驗證的郵箱")
            print(
                "   💡 提示：執行 'aws ses verify-email-identity '"
                "     '  --email-address your@email.com '"
            )
        return True
    except Exception as e:
        print(f"   ⚠️  無法檢查 SES: {e}")
        return True


def test_dependencies():
    """測試依賴套件"""
    print("\n4️⃣ 檢查依賴套件...")
    deps = {
        "boto3": "AWS SDK",
        "google.auth": "Google Auth Library",
    }

    all_ok = True
    for module, name in deps.items():
        try:
            __import__(module)
            print(f"   ✅ {name}")
        except ImportError:
            print(f"   ❌ {name} 未安裝")
            all_ok = False

    if not all_ok:
        print("\n   💡 執行安裝: pip install boto3 google-auth google-auth-httplib2")

    return all_ok


def main():
    print("=" * 60)
    print("Google-to-AWS Email 環境檢查")
    print("=" * 60)

    results = []
    results.append(("套件依賴", test_dependencies()))
    results.append(("Google 認證", test_google_auth()))
    results.append(("AWS 憑證", test_aws_credentials()))
    results.append(("SES 郵箱", test_ses_verified_emails()))

    print("\n" + "=" * 60)
    print("檢查結果摘要")
    print("=" * 60)

    for name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {name}")

    all_passed = all(r for _, r in results)

    if all_passed:
        print("\n🎉 環境檢查通過！可以執行主腳本了。")
        print("\n下一步：")
        print("   python send_email_via_google_aws.py")
        return 0
    else:
        print("\n⚠️  部分檢查未通過，請先解決上述問題。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
