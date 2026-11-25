import json
import os
import stat

import pytest

from minotaurus.signing import (
    SignatureError,
    check_signature,
    default_key_path,
    fingerprint,
    generate_key,
    load_key,
    sign_manifest,
)


@pytest.fixture
def key(tmp_path):
    generate_key(tmp_path / "k.key")
    return load_key(tmp_path / "k.key")


def test_a_signature_checks_and_gives_the_authors_fingerprint(key):
    manifest = b'{"brain_id": "x"}\n'
    signature = sign_manifest(manifest, key)
    author = check_signature(manifest, signature)
    assert len(author) == 16
    assert author == check_signature(manifest, sign_manifest(manifest, key))  # same key, same id


def test_a_changed_manifest_breaks_the_signature(key):
    signature = sign_manifest(b"original", key)
    with pytest.raises(SignatureError, match="does not match"):
        check_signature(b"changed", signature)


def test_another_persons_signature_gives_another_fingerprint(tmp_path, key):
    generate_key(tmp_path / "other.key")
    other = load_key(tmp_path / "other.key")
    one = check_signature(b"m", sign_manifest(b"m", key))
    two = check_signature(b"m", sign_manifest(b"m", other))
    assert one != two


def test_the_key_file_is_private_and_never_overwritten(tmp_path):
    path = tmp_path / "sub" / "k.key"
    generate_key(path)
    assert stat.S_IMODE(os.stat(path).st_mode) == 0o600
    with pytest.raises(SignatureError, match="already exists"):
        generate_key(path)


def test_bad_signature_files_are_refused(key):
    good = json.loads(sign_manifest(b"m", key))
    cases = [
        b"not json",
        b"[]",
        json.dumps({**good, "format": "other"}).encode(),
        json.dumps({**good, "version": 2}).encode(),
        json.dumps({**good, "algorithm": "rsa"}).encode(),
        json.dumps({**good, "public_key": "zz"}).encode(),
        json.dumps({k: v for k, v in good.items() if k != "signature"}).encode(),
    ]
    for case in cases:
        with pytest.raises(SignatureError):
            check_signature(b"m", case)


def test_a_missing_or_wrong_key_file_is_a_clear_error(tmp_path):
    with pytest.raises(SignatureError, match="cannot read"):
        load_key(tmp_path / "nope.key")
    (tmp_path / "junk.key").write_text("junk")
    with pytest.raises(SignatureError, match="cannot read"):
        load_key(tmp_path / "junk.key")


def test_the_default_key_path_follows_the_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("MINOTAURUS_SIGNING_KEY", str(tmp_path / "x.key"))
    assert default_key_path() == tmp_path / "x.key"
    monkeypatch.delenv("MINOTAURUS_SIGNING_KEY")
    assert default_key_path().name == "signing.key"


def test_fingerprint_is_sixteen_hex_characters():
    assert fingerprint("00" * 32) == fingerprint("00" * 32)
    assert len(fingerprint("00" * 32)) == 16


# ---- the commands ----


def test_keygen_then_pack_signs_the_bundle(tmp_path, monkeypatch):
    from typer.testing import CliRunner

    from minotaurus.bundle import read_bundle
    from minotaurus.cli import app
    from minotaurus.trainer.config import ConfigFile
    from minotaurus.trainer.train import train
    from tests.test_trainer import small_qtable_config

    key_path = tmp_path / "me.key"
    monkeypatch.setenv("MINOTAURUS_SIGNING_KEY", str(key_path))
    runner = CliRunner()
    config = ConfigFile.model_validate(small_qtable_config(episodes=20))
    run_dir = train(config, config.resolve_levels(), tmp_path / "runs")

    unsigned = runner.invoke(app, ["pack", str(run_dir), "--out", str(tmp_path / "a.tar")])
    assert unsigned.exit_code == 0
    assert read_bundle((tmp_path / "a.tar").read_bytes()).signer is None

    made = runner.invoke(app, ["keygen"])
    assert made.exit_code == 0
    assert "your author id" in made.output
    again = runner.invoke(app, ["keygen"])
    assert again.exit_code == 1  # never overwrites a key

    signed = runner.invoke(app, ["pack", str(run_dir), "--out", str(tmp_path / "b.tar")])
    assert "signed, author id" in signed.output
    author = read_bundle((tmp_path / "b.tar").read_bytes()).signer
    assert author is not None

    result = runner.invoke(app, ["sign", str(tmp_path / "a.tar")])
    assert result.exit_code == 0
    assert read_bundle((tmp_path / "a.tar").read_bytes()).signer == author


def test_sign_with_a_missing_key_fails_with_a_message(tmp_path):
    from typer.testing import CliRunner

    from minotaurus.cli import app

    not_a_bundle = tmp_path / "x.tar"
    not_a_bundle.write_bytes(b"nope")
    result = CliRunner().invoke(app, ["sign", str(not_a_bundle)])
    assert result.exit_code == 1
    assert "cannot sign" in result.output


# ---- the notice before training ----


def test_the_notice_says_signing_is_off_and_how_to_turn_it_on(tmp_path, monkeypatch):
    from minotaurus.signing import signing_notice

    monkeypatch.setenv("MINOTAURUS_SIGNING_KEY", str(tmp_path / "none.key"))
    text = signing_notice()
    assert text.startswith("Signing: off")
    assert "uv run minotaurus keygen" in text
    assert str(tmp_path / "none.key") in text


def test_the_notice_says_signing_is_on_with_the_author_id(tmp_path, monkeypatch):
    from minotaurus.signing import generate_key, signing_notice

    path = tmp_path / "me.key"
    author = generate_key(path)
    monkeypatch.setenv("MINOTAURUS_SIGNING_KEY", str(path))
    text = signing_notice()
    assert text.startswith("Signing: on")
    assert author in text


def test_the_notice_says_so_when_the_key_file_is_broken(tmp_path, monkeypatch):
    from minotaurus.signing import signing_notice

    bad = tmp_path / "bad.key"
    bad.write_text("junk")
    monkeypatch.setenv("MINOTAURUS_SIGNING_KEY", str(bad))
    assert signing_notice().startswith("Signing: off. The key")


def test_train_prints_the_notice_before_it_starts_and_signs_when_a_key_exists(
    tmp_path, monkeypatch
):
    import json

    from typer.testing import CliRunner

    from minotaurus.bundle import read_bundle
    from minotaurus.cli import app
    from minotaurus.signing import generate_key
    from tests.test_trainer import small_qtable_config

    config = tmp_path / "c.json"
    config.write_text(json.dumps(small_qtable_config(episodes=20)))

    def args(runs_name):
        return [
            "train",
            "--config",
            str(config),
            "--runs-dir",
            str(tmp_path / runs_name),
            "--no-plot",
        ]

    monkeypatch.setenv("MINOTAURUS_SIGNING_KEY", str(tmp_path / "k.key"))
    off = CliRunner().invoke(app, args("runs-off"))
    assert off.exit_code == 0
    assert off.output.index("Signing: off") < off.output.index("bundle written")

    author = generate_key(tmp_path / "k.key")
    on = CliRunner().invoke(app, args("runs-on"))
    assert on.exit_code == 0
    assert f"Signing: on. The bundle will be signed as author id {author}" in on.output
    assert on.output.index("Signing: on") < on.output.index("bundle written")
    unsigned = next((tmp_path / "runs-off").rglob("bundle.tar"))
    signed = next((tmp_path / "runs-on").rglob("bundle.tar"))
    assert read_bundle(unsigned.read_bytes()).signer is None
    assert read_bundle(signed.read_bytes()).signer == author
