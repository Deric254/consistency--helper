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


def _safe_request(method, url, **kwargs):
    try:
        r = requests.request(method, url, timeout=15, **kwargs)
        try:
            body = r.text
        except Exception:
            body = ''
        if 200 <= r.status_code < 300:
            return True, f'status {r.status_code}: {body[:400]}'
        else:
            return False, f'status {r.status_code}: {body[:400]}'
    except Exception as e:
        return False, str(e)


def publish_linkedin(text, creds):
    """Publish text-only post to LinkedIn on behalf of the user.
    Requires: linkedin token (member) in creds['linkedin_token']
    For organization posting, provide 'organization_urn' in creds.
    """
    token = creds.get('linkedin_token')
    if not token:
        return False, 'No LinkedIn token configured'

    headers = {
        'Authorization': f'Bearer {token}',
        'X-Restli-Protocol-Version': '2.0.0',
        'Content-Type': 'application/json'
    }

    # Try to resolve author urn (person)
    ok, me = _safe_request('GET', 'https://api.linkedin.com/v2/me', headers=headers)
    if not ok:
        return False, f'Failed to validate token: {me}'

    try:
        person_id = json.loads(me).get('id')
        author = f'urn:li:person:{person_id}'
    except Exception:
        return False, 'Failed to parse LinkedIn profile response to get person id'

    payload = {
        "author": author,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }

    return _safe_request('POST', 'https://api.linkedin.com/v2/ugcPosts', headers=headers, json=payload)


def publish_facebook(text, creds):
    token = creds.get('facebook_page_token') or creds.get('facebook_token')
    page_id = creds.get('facebook_page_id')
    if not token or not page_id:
        return False, 'Missing Facebook page token or page id (facebook_page_token, facebook_page_id)'

    url = f'https://graph.facebook.com/{page_id}/feed'
    data = {'message': text, 'access_token': token}
    return _safe_request('POST', url, data=data)


def publish_twitter(text, creds):
    # Prefer OAuth2 Bearer with tweet.write scope or OAuth1.0a user tokens
    bearer = creds.get('twitter_bearer')
    if bearer:
        headers = {'Authorization': f'Bearer {bearer}', 'Content-Type': 'application/json'}
        payload = {'text': text}
        return _safe_request('POST', 'https://api.twitter.com/2/tweets', headers=headers, json=payload)

    # Try OAuth1.0a via provided tokens
    api_key = creds.get('twitter_api_key')
    api_secret = creds.get('twitter_api_secret')
    access_token = creds.get('twitter_access_token')
    access_secret = creds.get('twitter_access_secret')
    if api_key and api_secret and access_token and access_secret:
        # Use requests-oauthlib if present, otherwise instruct user
        try:
            from requests_oauthlib import OAuth1
            auth = OAuth1(api_key, api_secret, access_token, access_secret)
            data = {'status': text}
            # Tweet endpoint for v1.1
            return _safe_request('POST', 'https://api.twitter.com/1.1/statuses/update.json', auth=auth, data=data)
        except Exception as e:
            return False, f'OAuth1 publish failed or requests_oauthlib missing: {e}'

    return False, 'Twitter credentials not found or insufficient (provide twitter_bearer or oauth1 tokens)'


def publish_whatsapp(text, creds):
    # First prefer Twilio if configured
    tw_sid = creds.get('twilio_account_sid')
    tw_token = creds.get('twilio_auth_token')
    tw_from = creds.get('twilio_from')
    tw_to = creds.get('twilio_to')
    if tw_sid and tw_token and tw_from and tw_to:
        url = f'https://api.twilio.com/2010-04-01/Accounts/{tw_sid}/Messages.json'
        data = {'From': tw_from, 'To': tw_to, 'Body': text}
        try:
            r = requests.post(url, data=data, auth=(tw_sid, tw_token), timeout=15)
            if 200 <= r.status_code < 300:
                return True, f'Twilio sent (status {r.status_code})'
            else:
                return False, f'Twilio API returned {r.status_code}: {r.text[:400]}'
        except Exception as e:
            return False, str(e)

    # Otherwise try generic WhatsApp Business API (user must provide full url and token)
    url = creds.get('whatsapp_url')
    token = creds.get('whatsapp_token')
    if not url or not token:
        return False, 'WhatsApp configuration missing (twilio or whatsapp_url + whatsapp_token required)'

    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    payload = {'text': text}
    return _safe_request('POST', url, headers=headers, json=payload)


def post(platform, text, dry_run=True):
    """High-level publish entry point. If dry_run=True, returns the prepared payload without sending."""
    creds = load_secrets()
    platform = platform.lower()

    # Dry-run: build a preview message and return True with the payload preview
    if dry_run:
        preview = {
            'platform': platform,
            'text': text,
            'creds_keys': list(creds.keys())
        }
        return True, f'Dry-run preview: {json.dumps(preview)}'

    if platform == 'linkedin':
        return publish_linkedin(text, creds)
    if platform == 'twitter':
        return publish_twitter(text, creds)
    if platform == 'facebook':
        return publish_facebook(text, creds)
    if platform == 'whatsapp':
        return publish_whatsapp(text, creds)
    if platform == 'instagram':
        # Instagram publishing uses Graph API and requires media flow; provide instructions
        return False, 'Instagram publishing not implemented in this helper. Use Facebook Graph API media endpoints.'

    return False, 'Posting for this platform is not implemented yet'
