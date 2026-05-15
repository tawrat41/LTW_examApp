from __future__ import annotations

import base64
import hashlib
import hmac
import secrets


class PasswordHasher:
    """PBKDF2-SHA256 password hashing without external dependencies."""

    algorithm = "pbkdf2_sha256"
    iterations = 120_000
    salt_size = 16

    def hash_password(self, password: str) -> str:
        if not password:
            raise ValueError("Password must not be empty.")

        salt = secrets.token_bytes(self.salt_size)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            self.iterations,
        )
        salt_b64 = base64.b64encode(salt).decode("ascii")
        digest_b64 = base64.b64encode(digest).decode("ascii")
        return f"{self.algorithm}${self.iterations}${salt_b64}${digest_b64}"

    def verify_password(self, password: str, stored_hash: str) -> bool:
        if not password or not stored_hash:
            return False

        try:
            algorithm, iterations_text, salt_b64, digest_b64 = stored_hash.split("$", 3)
        except ValueError:
            return False

        if algorithm != self.algorithm:
            return False

        salt = base64.b64decode(salt_b64.encode("ascii"))
        expected_digest = base64.b64decode(digest_b64.encode("ascii"))
        computed_digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            int(iterations_text),
        )
        return hmac.compare_digest(computed_digest, expected_digest)
