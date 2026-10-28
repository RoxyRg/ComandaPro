from app.security import (
    create_access_token, decode_access_token, hash_password,
    hash_refresh_token, new_refresh_token, verify_password,
)


def test_password_hash_is_not_plaintext_and_verifies():
    encoded = hash_password("correct-horse-42!")
    assert encoded != "correct-horse-42!"
    assert verify_password("correct-horse-42!", encoded)
    assert not verify_password("wrong-password", encoded)


def test_access_token_has_subject_and_expiry():
    token = create_access_token(7, 2)
    claims = decode_access_token(token)
    assert claims["sub"] == "7"
    assert claims["sucursal_id"] == 2
    assert claims["type"] == "access"
    assert claims["exp"] - claims["iat"] == 15 * 60


def test_access_token_tampering_is_rejected():
    token = create_access_token(7, 2)
    header, payload, signature = token.split(".")
    try:
        decode_access_token(f"{header}.{payload}.{signature[:-1]}x")
    except ValueError:
        pass
    else:
        raise AssertionError("A tampered token must be rejected")


def test_refresh_tokens_are_opaque_and_hashable():
    first = new_refresh_token()
    second = new_refresh_token()
    assert first != second
    assert hash_refresh_token(first) != first
    assert hash_refresh_token(first) != hash_refresh_token(second)
