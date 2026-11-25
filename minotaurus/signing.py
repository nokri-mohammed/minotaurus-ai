"""Sign a bundle's manifest with an Ed25519 key, and check the signature.

A signature says who made the bundle and that nobody changed it since. It does not say the scores
are true (minotaurus/verify.py does that). The manifest lists the sha256 of every file, so one
signature over manifest.json covers the whole bundle.

The signature file is `signature.json` inside the bundle:
{"format": "minotaurus-brain-signature", "version": 1, "algorithm": "ed25519",
 "public_key": "<64 hex>", "signature": "<128 hex>"}.
The author is shown as a fingerprint: the first 16 hex characters of sha256(public key).
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

SIGNATURE_NAME = "signature.json"
SIGNATURE_FORMAT = "minotaurus-brain-signature"
SIGNATURE_VERSION = 1
KEY_ENV = "MINOTAURUS_SIGNING_KEY"
DEFAULT_KEY_PATH = Path.home() / ".config" / "minotaurus" / "signing.key"


class SignatureError(ValueError):
    """The signature is missing, malformed or does not match. The message says why."""


def fingerprint(public_key_hex: str) -> str:
    """The short author id: 16 hex characters. Example: "9f3a1c0b7e2d4a58"."""
    return hashlib.sha256(bytes.fromhex(public_key_hex)).hexdigest()[:16]


def default_key_path() -> Path:
    """The key training signs with: $MINOTAURUS_SIGNING_KEY, else ~/.config/minotaurus/signing.key."""
    from_env = os.environ.get(KEY_ENV)
    if from_env:
        return Path(from_env)
    return DEFAULT_KEY_PATH


def existing_default_key() -> Path | None:
    """The default key file when it exists (training then signs its bundles), else None."""
    path = default_key_path()
    if path.is_file():
        return path
    return None


def generate_key(path: Path) -> str:
    """Write a new private key (PEM, readable by you only). Returns its fingerprint.

    Refuses to overwrite an existing key: losing a key means losing your author id.
    """
    path = Path(path)
    if path.exists():
        raise SignatureError(f"{path} already exists; it is not overwritten")
    path.parent.mkdir(parents=True, exist_ok=True)
    key = Ed25519PrivateKey.generate()
    pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(pem)
    return fingerprint(_public_hex(key))


def load_key(path: Path) -> Ed25519PrivateKey:
    try:
        key = serialization.load_pem_private_key(Path(path).read_bytes(), password=None)
    except (OSError, ValueError) as exc:
        raise SignatureError(f"cannot read the signing key {path}: {exc}") from exc
    if not isinstance(key, Ed25519PrivateKey):
        raise SignatureError(f"{path} is not an Ed25519 key")
    return key


def _public_hex(key: Ed25519PrivateKey) -> str:
    raw = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return raw.hex()


def sign_manifest(manifest_bytes: bytes, key: Ed25519PrivateKey) -> bytes:
    """The bytes of signature.json for these manifest bytes."""
    body = {
        "format": SIGNATURE_FORMAT,
        "version": SIGNATURE_VERSION,
        "algorithm": "ed25519",
        "public_key": _public_hex(key),
        "signature": key.sign(manifest_bytes).hex(),
    }
    return (json.dumps(body, indent=2) + "\n").encode()


def check_signature(manifest_bytes: bytes, signature_bytes: bytes) -> str:
    """Check signature.json against the manifest. Returns the author's fingerprint.

    Raises SignatureError when the file is malformed or the signature does not match.
    """
    try:
        body = json.loads(signature_bytes)
    except ValueError as exc:
        raise SignatureError(f"{SIGNATURE_NAME} is not valid JSON: {exc}") from exc
    if not isinstance(body, dict) or body.get("format") != SIGNATURE_FORMAT:
        raise SignatureError(f"{SIGNATURE_NAME} is not a minotaurus signature")
    if body.get("version") != SIGNATURE_VERSION:
        raise SignatureError(f"signature version {body.get('version')} is not supported")
    if body.get("algorithm") != "ed25519":
        raise SignatureError("only ed25519 signatures are supported")
    try:
        public_hex = str(body["public_key"])
        public = Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_hex))
        public.verify(bytes.fromhex(str(body["signature"])), manifest_bytes)
    except (KeyError, ValueError) as exc:
        raise SignatureError(f"{SIGNATURE_NAME} is malformed: {exc}") from exc
    except InvalidSignature as exc:
        raise SignatureError("the signature does not match the manifest") from exc
    return fingerprint(public_hex)
