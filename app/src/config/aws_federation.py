"""
AWS Federation Module for Cloud Run

This module provides Google-to-AWS Workload Identity Federation
for authenticating with AWS SES from Cloud Run.

Usage:
    from config.aws_federation import get_federated_ses_client

    ses_client = get_federated_ses_client()
    ses_client.send_email(...)
"""

import logging
import os
from functools import lru_cache

import boto3
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# Cloud Run metadata server URL for getting ID tokens
METADATA_URL = "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity"


def is_cloud_run_environment():
    """
    Check if we're running in Cloud Run (Services or Jobs).

    Cloud Run Services set K_SERVICE
    Cloud Run Jobs set CLOUD_RUN_JOB
    """
    # Cloud Run Services
    if os.environ.get("K_SERVICE"):
        return True
    # Cloud Run Jobs
    if os.environ.get("CLOUD_RUN_JOB"):
        return True
    # Also check if we can reach the metadata server (GCP environment)
    # This is a fallback for any GCP compute environment
    try:
        response = requests.get(
            "http://metadata.google.internal/computeMetadata/v1/",
            headers={"Metadata-Flavor": "Google"},
            timeout=1,
        )
        return response.status_code == 200
    except Exception:
        return False


def get_google_id_token_cloud_run(audience: str) -> str:
    """
    Get Google ID Token from Cloud Run metadata server.

    Cloud Run automatically provides ID tokens through the metadata server.
    No service account key file needed.

    Args:
        audience: The target audience for the token (usually the service account email)

    Returns:
        str: The Google ID Token
    """
    import base64
    import json as json_module

    print("🔐 Getting Google ID Token from Cloud Run metadata server...")
    print(f"🔐 Requested audience: {audience}")

    try:
        response = requests.get(
            f"{METADATA_URL}?audience={audience}",
            headers={"Metadata-Flavor": "Google"},
            timeout=10,
        )
        response.raise_for_status()
        token = response.text

        # Debug: Decode JWT to see actual claims
        try:
            parts = token.split(".")
            if len(parts) >= 2:
                # Add padding if needed
                payload = parts[1]
                padding = "=" * (4 - len(payload) % 4)
                decoded = base64.urlsafe_b64decode(payload + padding)
                claims = json_module.loads(decoded.decode("utf-8"))
                print(f"🔐 Token claims - aud: {claims.get('aud')}")
                print(f"🔐 Token claims - sub: {claims.get('sub')}")
                print(f"🔐 Token claims - email: {claims.get('email')}")
                print(f"🔐 Token claims - iss: {claims.get('iss')}")
        except Exception as decode_err:
            print(f"⚠️ Could not decode token for debugging: {decode_err}")

        print("✅ Successfully obtained Google ID Token from metadata server")
        return token
    except requests.RequestException as e:
        logger.error(f"Failed to get ID token from metadata server: {e}")
        raise


def get_google_id_token_local(audience: str) -> str:
    """
    Get Google ID Token using local service account key file.

    For local development/testing with GOOGLE_APPLICATION_CREDENTIALS.

    Args:
        audience: The target audience for the token

    Returns:
        str: The Google ID Token
    """
    import google.auth.transport.requests
    from google.oauth2 import service_account

    logger.info("Getting Google ID Token using local credentials...")

    key_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not key_file:
        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS not set for local environment")

    credentials = service_account.IDTokenCredentials.from_service_account_file(
        key_file,
        target_audience=audience,
    )

    request = google.auth.transport.requests.Request()
    credentials.refresh(request)

    logger.info("Successfully obtained Google ID Token from local credentials")
    return credentials.token


def get_google_id_token(audience: str) -> str:
    """
    Get Google ID Token - automatically detects environment.

    In Cloud Run: Uses metadata server
    Locally: Uses GOOGLE_APPLICATION_CREDENTIALS

    Args:
        audience: The target audience for the token

    Returns:
        str: The Google ID Token
    """
    if is_cloud_run_environment():
        return get_google_id_token_cloud_run(audience)
    else:
        return get_google_id_token_local(audience)


def assume_role_with_web_identity(
    google_id_token: str,
    role_arn: str,
    region: str = "ap-northeast-1",
    session_name: str = "CloudRunEmailSession",
) -> dict:
    """
    Exchange Google ID Token for AWS temporary credentials.

    Args:
        google_id_token: The Google ID Token
        role_arn: The AWS IAM Role ARN to assume
        region: AWS region
        session_name: Name for the role session

    Returns:
        dict: AWS credentials with AccessKeyId, SecretAccessKey, SessionToken
    """
    logger.info(f"Exchanging Google token for AWS credentials (Role: {role_arn})...")

    # Create STS client without credentials
    sts_client = boto3.client("sts", region_name=region)

    try:
        response = sts_client.assume_role_with_web_identity(
            RoleArn=role_arn,
            RoleSessionName=session_name,
            WebIdentityToken=google_id_token,
            DurationSeconds=3600,  # 1 hour
        )

        credentials = response["Credentials"]
        logger.info(
            f"Successfully obtained AWS credentials"
            f"(expires: {credentials['Expiration']})"
        )

        return credentials

    except Exception as e:
        logger.error(f"Failed to assume AWS role: {e}")
        raise


# Cache credentials for 50 minutes (they're valid for 1 hour)
@lru_cache(maxsize=1)
def _get_cached_credentials():
    """Get and cache AWS credentials."""
    import time

    # Get configuration from Django settings
    role_arn = getattr(settings, "AWS_ROLE_ARN", os.getenv("AWS_ROLE_ARN", ""))
    region = getattr(
        settings,
        "AWS_SES_REGION_NAME",
        os.getenv("AWS_SES_REGION_NAME", "ap-northeast-1"),
    )

    # Use the service account email as the audience
    # This must match the Trust Policy condition in AWS
    # Using cloudrun-serviceaccount for unified SA approach
    google_sa_email = os.getenv(
        "GOOGLE_SERVICE_ACCOUNT",
        "cloudrun-serviceaccount@comicchase.iam.gserviceaccount.com",
    )

    if not role_arn:
        raise ValueError("AWS_ROLE_ARN not configured")

    # Get Google ID Token
    google_token = get_google_id_token(audience=google_sa_email)

    # Exchange for AWS credentials
    credentials = assume_role_with_web_identity(
        google_id_token=google_token,
        role_arn=role_arn,
        region=region,
    )

    return {
        "credentials": credentials,
        "timestamp": time.time(),
    }


def get_aws_temp_credentials() -> dict:
    """
    Get AWS temporary credentials via Federation.

    Credentials are cached for 50 minutes.

    Returns:
        dict: AWS credentials
    """
    import time

    cached = _get_cached_credentials()

    # Check if credentials are still fresh (< 50 minutes old)
    if time.time() - cached["timestamp"] > 3000:  # 50 minutes
        # Clear cache and get new credentials
        _get_cached_credentials.cache_clear()
        cached = _get_cached_credentials()

    return cached["credentials"]


def get_federated_ses_client():
    """
    Get an AWS SES client using federated credentials.

    Returns:
        boto3.client: SES client configured with temporary credentials
    """
    region = getattr(
        settings,
        "AWS_SES_REGION_NAME",
        os.getenv("AWS_SES_REGION_NAME", "ap-northeast-1"),
    )

    credentials = get_aws_temp_credentials()

    ses_client = boto3.client(
        "ses",
        region_name=region,
        aws_access_key_id=credentials["AccessKeyId"],
        aws_secret_access_key=credentials["SecretAccessKey"],
        aws_session_token=credentials["SessionToken"],
    )

    logger.info(f"Created SES client with federated credentials (region: {region})")
    return ses_client


def send_email_with_federation(
    source: str,
    to_addresses: list,
    subject: str,
    body_text: str = None,
    body_html: str = None,
) -> dict:
    """
    Send email using AWS SES with federated credentials.

    Args:
        source: Sender email address
        to_addresses: List of recipient email addresses
        subject: Email subject
        body_text: Plain text body (optional)
        body_html: HTML body (optional)

    Returns:
        dict: SES response with MessageId
    """
    ses_client = get_federated_ses_client()

    # Build message
    message = {
        "Subject": {"Data": subject, "Charset": "UTF-8"},
        "Body": {},
    }

    if body_text:
        message["Body"]["Text"] = {"Data": body_text, "Charset": "UTF-8"}
    if body_html:
        message["Body"]["Html"] = {"Data": body_html, "Charset": "UTF-8"}

    response = ses_client.send_email(
        Source=source,
        Destination={"ToAddresses": to_addresses},
        Message=message,
    )

    logger.info(f"Email sent successfully (MessageId: {response['MessageId']})")
    return response
