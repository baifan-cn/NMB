from __future__ import annotations

import os
from dataclasses import dataclass
from hashlib import sha256
from typing import Tuple

from Crypto.Cipher import AES  # PyCryptodome implied via python-jose[cryptography], but better to add explicitly if needed
from Crypto.Random import get_random_bytes


BLOCK_SIZE = 16


def _pad_pkcs7(data: bytes) -> bytes:
    pad_len = BLOCK_SIZE - (len(data) % BLOCK_SIZE)
    return data + bytes([pad_len] * pad_len)


def _unpad_pkcs7(data: bytes) -> bytes:
    pad_len = data[-1]
    if pad_len < 1 or pad_len > BLOCK_SIZE:
        raise ValueError("Invalid padding")
    return data[:-pad_len]


def derive_key(magazine_id: int, master_key: str) -> bytes:
    # Simple derivation using SHA-256(magazine_id || master_key)
    seed = f"{magazine_id}:{master_key}".encode("utf-8")
    return sha256(seed).digest()


def encrypt_aes_cbc(data: bytes, key: bytes) -> Tuple[bytes, bytes]:
    iv = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(_pad_pkcs7(data))
    return iv, ciphertext


def decrypt_aes_cbc(iv: bytes, ciphertext: bytes, key: bytes) -> bytes:
    cipher = AES.new(key, AES.MODE_CBC, iv)
    plaintext_padded = cipher.decrypt(ciphertext)
    return _unpad_pkcs7(plaintext_padded)


def compress_pdf(data: bytes) -> bytes:
    # Placeholder: real compression can use qpdf/ghostscript/pikepdf; here we return as-is
    return data
