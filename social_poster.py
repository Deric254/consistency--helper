"""Simple social posting helper (stubs).

This module provides small helpers to post to social platforms.
Currently these are safe stubs that will attempt a minimal request when
credentials are provided, but they will not perform complex posting flows.

Extend these functions with real API flows and proper error handling when
you add real credentials.
"""
import json
import os
import requests
from pathlib import Path

SECRETS_PATH = Path('secrets.json')


def load_secrets():
    if not SECRETS_PATH.exists():
        return {}
    try:
        return json.loads(SECRETS_PATH.read_text())
    except Exception:
        return {}


def post_to_linkedin(text, creds):
    token = creds.get('linkedin_token')
    if not token:
        return False, 'No LinkedIn token configured'

    # Minimal check (get basic profile) to validate token — do NOT post here
    headers = {'Authorization': f'Bearer {token}'}
    try:
        r = requests.get('https://api.linkedin.com/v2/me', headers=headers, timeout=10)
        if r.status_code == 200:
            # This is a stub — real posting requires additional fields/scopes
            return True, 'LinkedIn token validated (posting not implemented)'
        else:
            return False, f'LinkedIn API returned {r.status_code}: {r.text[:200]}'
    except Exception as e:
        return False, str(e)


def post_to_twitter(text, creds):
    token = creds.get('twitter_bearer')
    if not token:
        return False, 'No Twitter bearer token configured'
    # Minimal validation: request application rate limit endpoint
    headers = {'Authorization': f'Bearer {token}'}
    try:
        r = requests.get('https://api.twitter.com/2/tweets', headers=headers, timeout=10)
        # Twitter will likely return 403 for write without proper scopes — treat any response as 'validated' if reachable
        return True, f'Twitter API reachable (status {r.status_code})'
    except Exception as e:
        return False, str(e)


def post_to_facebook(text, creds):
    token = creds.get('facebook_page_token')
    if not token:
        return False, 'No Facebook Page token configured'
    # Minimal: attempt Graph API version endpoint
    try:
        r = requests.get(f'https://graph.facebook.com/me?access_token={token}', timeout=10)
        if r.status_code == 200:
            return True, 'Facebook token validated (posting not implemented)'
        else:
            return False, f'Facebook API returned {r.status_code}: {r.text[:200]}'
    except Exception as e:
        return False, str(e)


def post_to_whatsapp(text, creds):
    # WhatsApp Business API varies; user should provide full endpoint and token
    url = creds.get('whatsapp_url')
    token = creds.get('whatsapp_token')
    if not url or not token:
        return False, 'WhatsApp URL or token not configured'
    try:
        r = requests.post(url, headers={'Authorization': f'Bearer {token}'}, json={'text': text}, timeout=10)
        return (r.status_code in (200,201)), f'Status {r.status_code}: {r.text[:200]}'
    except Exception as e:
        return False, str(e)


def post(platform, text):
    creds = load_secrets()
    platform = platform.lower()
    if platform == 'linkedin':
        return post_to_linkedin(text, creds)
    if platform == 'twitter':
        return post_to_twitter(text, creds)
    if platform == 'facebook':
        return post_to_facebook(text, creds)
    if platform == 'whatsapp':
        return post_to_whatsapp(text, creds)
    # Instagram posting requires Facebook Graph API with special endpoints
    return False, 'Posting for this platform is not implemented yet'
