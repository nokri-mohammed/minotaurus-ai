import hashlib
import io
import json
import tarfile
from pathlib import Path

import pytest

from minotaurus.bundle import (
    BUNDLE_VERSION,
    MAX_MEMBERS,
    BundleError,
    Manifest,
    build_bundle,
    read_bundle,
)
from minotaurus.trainer.config import ConfigFile
from minotaurus.trainer.train import train
from tests.test_trainer import small_qtable_config


@pytest.fixture(scope="module")
def run_dir(tmp_path_factory) -> Path:
    config = ConfigFile.model_validate(small_qtable_config(episodes=20))
    return train(config, config.resolve_levels(), tmp_path_factory.mktemp("runs"))


@pytest.fixture
def bundle_bytes(run_dir, tmp_path) -> bytes:
    path = build_bundle(run_dir, tmp_path / "out.tar")
    return path.read_bytes()


def rebuild(data: bytes, change) -> bytes:
    """Open a good bundle, let `change(members)` edit the {name: bytes} dict, write it again."""
    members = {}
    with tarfile.open(fileobj=io.BytesIO(data)) as tar:
        for member in tar.getmembers():
            members[member.name] = tar.extractfile(member).read()
    change(members)
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode="w") as tar:
        for name, content in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(content)
            tar.addfile(info, io.BytesIO(content))
    return out.getvalue()


def test_a_built_bundle_reads_back(bundle_bytes, run_dir):
    bundle = read_bundle(bundle_bytes)
    assert bundle.manifest.version == BUNDLE_VERSION
    assert bundle.manifest.brain_id == hashlib.sha256(bundle.files["brain.onnx"]).hexdigest()
    assert bundle.config.name
    assert "config.json" in bundle.files
    assert "checkpoints" not in " ".join(bundle.files)


def test_the_manifest_lists_every_file_with_size_and_hash(bundle_bytes):
    bundle = read_bundle(bundle_bytes)
    listed = {}
    for entry in bundle.manifest.files:
        listed[entry.name] = entry
    assert set(listed) == set(bundle.files)
    for name, content in bundle.files.items():
        assert listed[name].size == len(content)
        assert listed[name].sha256 == hashlib.sha256(content).hexdigest()


def test_a_wrong_version_is_refused(bundle_bytes):
    def change(members):
        manifest = json.loads(members["manifest.json"])
        manifest["version"] = 99
        members["manifest.json"] = json.dumps(manifest).encode()

    with pytest.raises(BundleError, match="version 99 is not supported"):
        read_bundle(rebuild(bundle_bytes, change))


def test_a_changed_file_is_refused(bundle_bytes):
    def change(members):
        members["config.json"] = members["config.json"] + b" "

    with pytest.raises(BundleError, match="config.json"):
        read_bundle(rebuild(bundle_bytes, change))


def test_a_missing_listed_file_is_refused(bundle_bytes):
    def change(members):
        del members["metrics.jsonl"]

    with pytest.raises(BundleError, match="missing"):
        read_bundle(rebuild(bundle_bytes, change))


def test_a_file_not_in_the_manifest_is_refused(bundle_bytes):
    def change(members):
        manifest = json.loads(members["manifest.json"])
        kept = []
        for entry in manifest["files"]:
            if entry["name"] != "metrics.jsonl":
                kept.append(entry)
        manifest["files"] = kept
        members["manifest.json"] = json.dumps(manifest).encode()

    with pytest.raises(BundleError):
        read_bundle(rebuild(bundle_bytes, change))


def test_a_missing_manifest_is_refused(bundle_bytes):
    def change(members):
        del members["manifest.json"]

    with pytest.raises(BundleError, match="manifest.json"):
        read_bundle(rebuild(bundle_bytes, change))


def test_a_bad_brain_is_refused_even_with_matching_hashes(bundle_bytes):
    def change(members):
        junk = b"not an onnx file"
        members["brain.onnx"] = junk
        manifest = json.loads(members["manifest.json"])
        manifest["brain_id"] = hashlib.sha256(junk).hexdigest()
        for entry in manifest["files"]:
            if entry["name"] == "brain.onnx":
                entry["size"] = len(junk)
                entry["sha256"] = hashlib.sha256(junk).hexdigest()
        members["manifest.json"] = json.dumps(manifest).encode()

    with pytest.raises(BundleError, match="brain.onnx"):
        read_bundle(rebuild(bundle_bytes, change))


def test_a_bad_config_is_refused(bundle_bytes):
    def change(members):
        bad = b'{"name": "x"}'
        members["config.json"] = bad
        manifest = json.loads(members["manifest.json"])
        for entry in manifest["files"]:
            if entry["name"] == "config.json":
                entry["size"] = len(bad)
                entry["sha256"] = hashlib.sha256(bad).hexdigest()
        members["manifest.json"] = json.dumps(manifest).encode()

    with pytest.raises(BundleError, match="config.json"):
        read_bundle(rebuild(bundle_bytes, change))


def test_unsafe_member_names_are_refused():
    for name in ("../evil.txt", "/etc/passwd", "sub/dir.txt", "brain.onnx.exe"):
        out = io.BytesIO()
        with tarfile.open(fileobj=out, mode="w") as tar:
            info = tarfile.TarInfo(name)
            info.size = 1
            tar.addfile(info, io.BytesIO(b"x"))
        with pytest.raises(BundleError):
            read_bundle(out.getvalue())


def test_links_and_folders_are_refused():
    for kind in (tarfile.SYMTYPE, tarfile.DIRTYPE):
        out = io.BytesIO()
        with tarfile.open(fileobj=out, mode="w") as tar:
            info = tarfile.TarInfo("manifest.json")
            info.type = kind
            info.linkname = "/etc/passwd"
            tar.addfile(info)
        with pytest.raises(BundleError):
            read_bundle(out.getvalue())


def test_too_many_members_are_refused():
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode="w") as tar:
        for number in range(MAX_MEMBERS + 1):
            info = tarfile.TarInfo(f"f{number}.txt")
            info.size = 1
            tar.addfile(info, io.BytesIO(b"x"))
    with pytest.raises(BundleError, match="too many"):
        read_bundle(out.getvalue())


def test_not_a_tar_is_refused():
    with pytest.raises(BundleError, match="not a tar"):
        read_bundle(b"hello")


def test_manifest_rejects_a_bad_id():
    with pytest.raises(ValueError):
        Manifest.model_validate(
            {
                "format": "minotaurus-brain-bundle",
                "version": 1,
                "brain_id": "short",
                "name": "x",
                "method": "qtable",
                "files": [],
            }
        )


def test_names_that_differ_are_refused(bundle_bytes):
    def change(members):
        manifest = json.loads(members["manifest.json"])
        manifest["name"] = "someone-else"
        members["manifest.json"] = json.dumps(manifest).encode()

    with pytest.raises(BundleError, match="names differ"):
        read_bundle(rebuild(bundle_bytes, change))


def test_the_manifest_schema_file_matches_the_model():
    from minotaurus.bundle import manifest_schema_text

    schema_file = (
        Path(__file__).resolve().parents[1] / "data" / "schemas" / "bundle-manifest.schema.json"
    )
    assert schema_file.read_text() == manifest_schema_text()


def test_several_seeds_write_a_bundle_per_seed(tmp_path):
    from minotaurus.trainer.multi import run_seeds

    config = ConfigFile.model_validate(small_qtable_config(episodes=10))
    results = list(run_seeds(config, [1], 1, tmp_path / "run", 10, False))
    bundle_file = Path(results[0].run_dir) / "bundle.tar"
    assert bundle_file.is_file()
    read_bundle(bundle_file.read_bytes())
