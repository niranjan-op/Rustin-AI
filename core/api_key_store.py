"""
Secure API key storage with Fernet encryption, OS keyring master key,
and SHA-256 integrity hashing.

Security layers:
  - Confidentiality: Fernet (AES-128-CBC + HMAC-SHA256) encryption
  - Key management:  OS keyring (Windows Credential Locker / macOS Keychain)
  - Integrity:       SHA-256 hash of ciphertext detects DB tampering
  - Key derivation:  PBKDF2-HMAC-SHA256, 600k iterations, random 16-byte salt
"""

import base64
import hashlib
import json
import os
import sqlite3
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

DB_PATH = ".files/test.db"
SERVICE_NAME = "rustin_ai"
KEYRING_USERNAME = "master_key"

# ---------------------------------------------------------------------------
# Master key management via OS keyring
# ---------------------------------------------------------------------------

def _get_or_create_master_key() -> bytes:
    """Retrieve master secret from OS keyring; create one if it doesn't exist."""
    import keyring

    secret = keyring.get_password(SERVICE_NAME, KEYRING_USERNAME)
    if not secret:
        secret = base64.urlsafe_b64encode(os.urandom(32)).decode()
        keyring.set_password(SERVICE_NAME, KEYRING_USERNAME, secret)
    return secret.encode()


def _derive_fernet_key(salt: bytes) -> bytes:
    """Derive a Fernet-compatible key from the master secret + salt."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(_get_or_create_master_key()))


# ---------------------------------------------------------------------------
# Encrypt / decrypt helpers
# ---------------------------------------------------------------------------

def encrypt_api_key(plaintext: str) -> tuple[bytes, str]:
    """
    Encrypt an API key.

    Returns:
        (blob, hash) where blob = salt(16 bytes) + Fernet ciphertext,
        and hash = SHA-256 hex digest of blob for integrity verification.
    """
    salt = os.urandom(16)
    key = _derive_fernet_key(salt)
    ciphertext = Fernet(key).encrypt(plaintext.encode())
    blob = salt + ciphertext
    integrity_hash = hashlib.sha256(blob).hexdigest()
    return blob, integrity_hash


def decrypt_api_key(blob: bytes, expected_hash: str) -> Optional[str]:
    """
    Decrypt an API key blob after verifying integrity.

    Returns the plaintext key, or None if integrity check or decryption fails.
    """
    # Integrity check
    actual_hash = hashlib.sha256(blob).hexdigest()
    if actual_hash != expected_hash:
        print(f"[SECURITY] Integrity check failed for stored API key — possible tampering")
        return None

    salt = blob[:16]
    ciphertext = blob[16:]
    try:
        key = _derive_fernet_key(salt)
        return Fernet(key).decrypt(ciphertext).decode()
    except (InvalidToken, Exception) as e:
        print(f"[SECURITY] Decryption failed: {e}")
        return None


# ---------------------------------------------------------------------------
# Database CRUD
# ---------------------------------------------------------------------------

def _get_conn():
    return sqlite3.connect(DB_PATH)


def save_api_keys(user_id: str, provider: str, keys: list[str]):
    """Save (encrypt) API keys for a provider. Empty strings are deleted."""
    conn = _get_conn()
    cursor = conn.cursor()
    try:
        # Delete all existing keys for this provider first
        cursor.execute(
            "DELETE FROM user_api_keys WHERE user_id = ? AND provider = ?",
            (user_id, provider),
        )
        for slot, key_value in enumerate(keys, start=1):
            if key_value and key_value.strip():
                blob, key_hash = encrypt_api_key(key_value.strip())
                cursor.execute(
                    """INSERT OR REPLACE INTO user_api_keys
                       (user_id, provider, key_slot, encrypted_key, key_hash)
                       VALUES (?, ?, ?, ?, ?)""",
                    (user_id, provider, slot, blob, key_hash),
                )
        conn.commit()
    finally:
        conn.close()


def load_api_keys(user_id: str, provider: str) -> list[str]:
    """Load and decrypt API keys for a provider. Returns list of plaintext keys."""
    conn = _get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """SELECT key_slot, encrypted_key, key_hash FROM user_api_keys
               WHERE user_id = ? AND provider = ?
               ORDER BY key_slot""",
            (user_id, provider),
        )
        rows = cursor.fetchall()
        keys = []
        for slot, encrypted_key, key_hash in rows:
            plaintext = decrypt_api_key(encrypted_key, key_hash)
            if plaintext:
                keys.append(plaintext)
            else:
                keys.append("")  # Failed decryption — slot exists but unreadable
        return keys
    finally:
        conn.close()


def save_provider_settings(user_id: str, provider: str, model_name: str, extra: dict = None):
    """Save model selection and extra settings for a provider."""
    conn = _get_conn()
    cursor = conn.cursor()
    try:
        extra_json = json.dumps(extra or {})
        # Mark this provider as last active, clear others
        cursor.execute(
            "UPDATE user_provider_settings SET last_active = 0 WHERE user_id = ?",
            (user_id,),
        )
        cursor.execute(
            """INSERT OR REPLACE INTO user_provider_settings
               (user_id, provider, model_name, last_active, extra_json)
               VALUES (?, ?, ?, 1, ?)""",
            (user_id, provider, model_name, extra_json),
        )
        conn.commit()
    finally:
        conn.close()


def load_provider_settings(user_id: str, provider: str) -> dict:
    """Load saved settings for a specific provider."""
    conn = _get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """SELECT model_name, extra_json FROM user_provider_settings
               WHERE user_id = ? AND provider = ?""",
            (user_id, provider),
        )
        row = cursor.fetchone()
        if row:
            extra = {}
            try:
                extra = json.loads(row[1]) if row[1] else {}
            except json.JSONDecodeError:
                pass
            return {"model_name": row[0], **extra}
        return {}
    finally:
        conn.close()


def load_last_provider(user_id: str) -> Optional[str]:
    """Get the last-active provider for a user."""
    conn = _get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """SELECT provider FROM user_provider_settings
               WHERE user_id = ? AND last_active = 1""",
            (user_id,),
        )
        row = cursor.fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def load_all_saved_settings(user_id: str) -> dict:
    """
    Hydrate a full settings dict from saved DB state.
    Used on chat start/resume to pre-fill the settings panel.
    """
    settings = {}

    # Determine last-used provider
    last_provider = load_last_provider(user_id)
    if last_provider:
        settings["llm_provider"] = last_provider

    # Load Gemini keys
    gemini_keys = load_api_keys(user_id, "gemini")
    key_fields = ["gemini_api_key", "gemini_api_key_2", "gemini_api_key_3", "gemini_api_key_4"]
    for i, field in enumerate(key_fields):
        settings[field] = gemini_keys[i] if i < len(gemini_keys) else ""

    gemini_settings = load_provider_settings(user_id, "gemini")
    if gemini_settings.get("model_name"):
        settings["gemini_model"] = gemini_settings["model_name"]

    # Load OpenRouter keys
    or_keys = load_api_keys(user_id, "openrouter")
    or_fields = ["openrouter_api_key", "openrouter_api_key_2", "openrouter_api_key_3", "openrouter_api_key_4"]
    for i, field in enumerate(or_fields):
        settings[field] = or_keys[i] if i < len(or_keys) else ""

    or_settings = load_provider_settings(user_id, "openrouter")
    if or_settings.get("model_name"):
        settings["openrouter_model_name"] = or_settings["model_name"]

    # Load Groq key (single key)
    groq_keys = load_api_keys(user_id, "groq")
    settings["groq_api_key"] = groq_keys[0] if groq_keys else ""

    groq_settings = load_provider_settings(user_id, "groq")
    if groq_settings.get("model_name"):
        settings["groq_model"] = groq_settings["model_name"]

    # Load Ollama settings
    ollama_settings = load_provider_settings(user_id, "ollama")
    if ollama_settings.get("model_name"):
        settings["ollama_model"] = ollama_settings["model_name"]
    if "base_url" in ollama_settings:
        settings["ollama_base_url"] = ollama_settings["base_url"]
    if "auto_start" in ollama_settings:
        settings["ollama_auto_start"] = ollama_settings["auto_start"]

    return settings
