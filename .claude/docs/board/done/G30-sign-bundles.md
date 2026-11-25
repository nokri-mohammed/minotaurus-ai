# G30: sign bundles

- **Owner:** minotaurus-ai-dev (the lead)
- **Area:** server, trainer, web
- **Model:** opus
- **CEO go:** 2026-11-25 ("ok publish changes then build 1 and 2"; the new dependency `cryptography` is covered by that go)

## Report

- **Done:** `minotaurus/signing.py` (Ed25519 key, signature over `manifest.json`, author id = first
  16 hex characters of sha256 of the public key). `bundle.py`: `build_bundle(signing_key=...)`,
  `sign_bundle`, and `read_bundle` checks `signature.json` (a bad one is refused; `signature.json` is
  not listed in the manifest). Commands `minotaurus keygen` (never overwrites, mode 0600) and
  `minotaurus sign`; `train` and `pack` sign by themselves when the key exists
  ($MINOTAURUS_SIGNING_KEY or ~/.config/minotaurus/signing.key). The recipe reply has `signed_by`
  and `author_first_seen` (trust on first use, table `authors`); Recipe shows Signed / Unsigned.
  Fixed on the way: a kept verification is dropped when the same brain is uploaded again.
- **Tests:** pytest 456 passed, `bun test` 81 passed, build clean.
- **Not seen:** Recipe in a browser. No real key made on this machine (the CEO runs `keygen`).
- **Left:** no key rotation or revoking; the author id has no human name; the private key is not
  encrypted (file mode 0600 only). Sharing and trusting keys is for the online race (P1).
- **Lessons:** see LESSONS.md.
