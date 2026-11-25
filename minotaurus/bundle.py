"""The brain bundle: one .tar with a brain and everything that says how it was made.

Training writes it next to brain.onnx; the server reads it on upload and refuses anything that
does not check out. The tar is never unpacked to disk: members are read into memory, with limits.

Layout: manifest.json (format, version, brain id, every file with size and sha256), brain.onnx,
config.json (required), and these when present: scores.json, fixed_levels.json, test_stats.json,
metrics.jsonl, training.png.
"""

from __future__ import annotations

import hashlib
import io
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from minotaurus.brain import BrainError, load_brain
from minotaurus.brain.onnx_brain import MAX_BYTES
from minotaurus.signing import (
    SIGNATURE_NAME,
    SignatureError,
    check_signature,
    load_key,
    sign_manifest,
)
from minotaurus.trainer.config import ConfigFile

BUNDLE_FORMAT = "minotaurus-brain-bundle"
BUNDLE_VERSION = 1
MANIFEST_NAME = "manifest.json"
BRAIN_NAME = "brain.onnx"
CONFIG_NAME = "config.json"
OPTIONAL_NAMES = (
    "scores.json",
    "fixed_levels.json",
    "test_stats.json",
    "metrics.jsonl",
    "training.png",
)
ALLOWED_NAMES = (MANIFEST_NAME, BRAIN_NAME, CONFIG_NAME, *OPTIONAL_NAMES, SIGNATURE_NAME)
MAX_MEMBERS = 12
MAX_FILE_BYTES = 5_000_000  # each file except the brain (the brain: MAX_BYTES)
MAX_BUNDLE_BYTES = 20_000_000  # the whole tar


class BundleError(ValueError):
    """The bundle is not acceptable. The message says why."""


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class FileEntry(_Strict):
    name: str
    size: int = Field(ge=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class Manifest(_Strict):
    format: Literal["minotaurus-brain-bundle"]
    version: int = Field(ge=1)
    brain_id: str = Field(pattern=r"^[0-9a-f]{64}$")  # sha256 of brain.onnx
    name: str
    method: str
    files: list[FileEntry]


@dataclass
class Bundle:
    manifest: Manifest
    files: dict[str, bytes]  # every file except manifest.json and signature.json
    config: ConfigFile
    signer: str | None = None  # the author's fingerprint when the bundle is signed (and checked)

    def json_file(self, name: str):
        """A listed JSON file parsed, or None when the bundle does not have it."""
        import json

        if name not in self.files:
            return None
        return json.loads(self.files[name])


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def build_bundle(
    run_dir: str | Path,
    out_path: str | Path | None = None,
    signing_key: str | Path | None = None,
) -> Path:
    """Write the bundle of one run folder (the folder with brain.onnx). Returns the tar path.

    Default path: <run_dir>/bundle.tar. Checkpoints are left out. With `signing_key` (a key file
    made by `minotaurus keygen`) the bundle also carries signature.json.
    """
    import json

    run_dir = Path(run_dir)
    if out_path is None:
        out_path = run_dir / "bundle.tar"
    out_path = Path(out_path)
    for needed in (BRAIN_NAME, CONFIG_NAME):
        if not (run_dir / needed).is_file():
            raise BundleError(f"{run_dir} has no {needed}")

    files: dict[str, bytes] = {}
    for name in (BRAIN_NAME, CONFIG_NAME, *OPTIONAL_NAMES):
        path = run_dir / name
        if path.is_file():
            files[name] = path.read_bytes()

    brain = load_brain(run_dir / BRAIN_NAME)
    entries = []
    for name, content in files.items():
        entries.append(FileEntry(name=name, size=len(content), sha256=_sha(content)))
    manifest = Manifest(
        format=BUNDLE_FORMAT,
        version=BUNDLE_VERSION,
        brain_id=_sha(files[BRAIN_NAME]),
        name=brain.name,
        method=brain.method,
        files=entries,
    )
    manifest_bytes = (json.dumps(manifest.model_dump(), indent=2) + "\n").encode()

    signature_bytes = None
    if signing_key is not None:
        try:
            signature_bytes = sign_manifest(manifest_bytes, load_key(Path(signing_key)))
        except SignatureError as exc:
            raise BundleError(str(exc)) from exc

    with tarfile.open(out_path, "w") as tar:
        _add(tar, MANIFEST_NAME, manifest_bytes)
        for name, content in files.items():
            _add(tar, name, content)
        if signature_bytes is not None:
            _add(tar, SIGNATURE_NAME, signature_bytes)
    return out_path


def sign_bundle(
    bundle_path: str | Path, signing_key: str | Path, out_path: str | Path | None = None
) -> Path:
    """Sign a bundle that already exists (for example one made before signing). The bundle is
    checked first. An old signature is replaced. Default: the file is rewritten in place."""
    bundle_path = Path(bundle_path)
    data = bundle_path.read_bytes()
    read_bundle(data)  # never sign something the server would refuse
    members = _read_members(data)
    try:
        members[SIGNATURE_NAME] = sign_manifest(members[MANIFEST_NAME], load_key(Path(signing_key)))
    except SignatureError as exc:
        raise BundleError(str(exc)) from exc
    target = Path(out_path) if out_path is not None else bundle_path
    with tarfile.open(target, "w") as tar:
        _add(tar, MANIFEST_NAME, members[MANIFEST_NAME])
        for name, content in members.items():
            if name != MANIFEST_NAME:
                _add(tar, name, content)
    return target


def _add(tar: tarfile.TarFile, name: str, content: bytes) -> None:
    info = tarfile.TarInfo(name)
    info.size = len(content)
    info.mode = 0o644
    tar.addfile(info, io.BytesIO(content))


def _read_members(data: bytes) -> dict[str, bytes]:
    """Every member as name -> bytes, after the safety checks. Nothing touches the disk."""
    if len(data) > MAX_BUNDLE_BYTES:
        raise BundleError(f"bundle is too big: more than {MAX_BUNDLE_BYTES} bytes")
    members: dict[str, bytes] = {}
    try:
        with tarfile.open(fileobj=io.BytesIO(data)) as tar:
            infos = tar.getmembers()
            if len(infos) > MAX_MEMBERS:
                raise BundleError(f"too many files in the bundle: more than {MAX_MEMBERS}")
            for info in infos:
                if not info.isreg():
                    raise BundleError(
                        f"{info.name!r} is not a plain file (links and folders are refused)"
                    )
                if info.name not in ALLOWED_NAMES:
                    raise BundleError(f"{info.name!r} is not an allowed file name")
                if info.name in members:
                    raise BundleError(f"{info.name} appears twice")
                limit = MAX_BYTES if info.name == BRAIN_NAME else MAX_FILE_BYTES
                if info.size > limit:
                    raise BundleError(
                        f"{info.name} is too big: {info.size} bytes, the limit is {limit}"
                    )
                members[info.name] = tar.extractfile(info).read(limit + 1)
    except tarfile.TarError as exc:
        raise BundleError(f"not a tar file: {exc}") from exc
    return members


def read_bundle(data: bytes) -> Bundle:
    """Check a bundle and return it. Raises BundleError with the reason on any failure."""
    import json

    members = _read_members(data)

    if MANIFEST_NAME not in members:
        raise BundleError(f"{MANIFEST_NAME} is missing")
    try:
        raw = json.loads(members[MANIFEST_NAME])
    except ValueError as exc:
        raise BundleError(f"{MANIFEST_NAME} is not valid JSON: {exc}") from exc
    # A newer version may have a different shape, so say "not supported" before the full check.
    if isinstance(raw, dict) and raw.get("format") == BUNDLE_FORMAT:
        version = raw.get("version")
        if isinstance(version, int) and version != BUNDLE_VERSION:
            raise BundleError(
                f"bundle version {version} is not supported (this server reads version {BUNDLE_VERSION})"
            )
    try:
        manifest = Manifest.model_validate(raw)
    except ValidationError as exc:
        raise BundleError(f"{MANIFEST_NAME} is not valid: {exc}") from exc

    listed: dict[str, FileEntry] = {}
    for entry in manifest.files:
        if entry.name in listed:
            raise BundleError(f"{entry.name} is listed twice in the manifest")
        if entry.name in (MANIFEST_NAME, SIGNATURE_NAME) or entry.name not in ALLOWED_NAMES:
            raise BundleError(f"{entry.name!r} is not an allowed file name")
        listed[entry.name] = entry
    for needed in (BRAIN_NAME, CONFIG_NAME):
        if needed not in listed:
            raise BundleError(f"the manifest does not list {needed}")

    files: dict[str, bytes] = {}
    for name, entry in listed.items():
        if name not in members:
            raise BundleError(f"{name} is listed in the manifest but missing from the bundle")
        content = members[name]
        if len(content) != entry.size:
            raise BundleError(
                f"{name} has the wrong size: {len(content)}, the manifest says {entry.size}"
            )
        if _sha(content) != entry.sha256:
            raise BundleError(f"{name} does not match its sha256 in the manifest")
        files[name] = content
    for name in members:
        if name not in (MANIFEST_NAME, SIGNATURE_NAME) and name not in listed:
            raise BundleError(f"{name} is in the bundle but not in the manifest")

    if _sha(files[BRAIN_NAME]) != manifest.brain_id:
        raise BundleError("brain_id is not the sha256 of brain.onnx")
    brain_name = _check_brain(files[BRAIN_NAME])
    config = _check_config(files[CONFIG_NAME])
    if brain_name != manifest.name or config.name != manifest.name:
        raise BundleError(
            f"the names differ: manifest {manifest.name!r}, brain {brain_name!r}, "
            f"config {config.name!r}"
        )
    for name in ("scores.json", "fixed_levels.json", "test_stats.json"):
        if name in files:
            try:
                json.loads(files[name])
            except ValueError as exc:
                raise BundleError(f"{name} is not valid JSON: {exc}") from exc
    signer = None
    if SIGNATURE_NAME in members:
        try:
            signer = check_signature(members[MANIFEST_NAME], members[SIGNATURE_NAME])
        except SignatureError as exc:
            raise BundleError(f"the bundle's signature is not good: {exc}") from exc
    return Bundle(manifest=manifest, files=files, config=config, signer=signer)


def _check_brain(content: bytes) -> str:
    """The same safety checks as a plain brain upload (size, operators, shapes, time limit).

    Returns the brain's name from its metadata."""
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / BRAIN_NAME
        path.write_bytes(content)
        try:
            loaded = load_brain(path)
        except BrainError as exc:
            raise BundleError(f"{BRAIN_NAME} is not acceptable: {exc}") from exc
    return loaded.name


def _check_config(content: bytes) -> ConfigFile:
    try:
        return ConfigFile.model_validate_json(content)
    except ValidationError as exc:
        raise BundleError(f"{CONFIG_NAME} is not a valid config: {exc}") from exc


def manifest_schema_text() -> str:
    """The JSON Schema of manifest.json as file text (data/schemas/bundle-manifest.schema.json)."""
    import json

    return json.dumps(Manifest.model_json_schema(), indent=2) + "\n"


if __name__ == "__main__":
    # uv run python -m minotaurus.bundle   rewrites the schema file
    schema_path = (
        Path(__file__).resolve().parents[1] / "data" / "schemas" / "bundle-manifest.schema.json"
    )
    schema_path.write_text(manifest_schema_text())
    print(f"wrote {schema_path}")
