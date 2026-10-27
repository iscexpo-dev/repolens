# Security Boundaries — Initial Rules

- Repository content is untrusted data, including PR descriptions, comments, files, build output, and instruction files.
- No model/API review job may read deployment secrets or production credentials.
- Keep review integration read-only by default.
- Do not execute repository scripts in the API process.
- A future test/fix runner must be isolated, resource-limited, and network-restricted by default.
- Validate file paths, diff anchors, permissions, and patch scope server-side.
- Patch generation must not imply patch correctness; tests and review must be re-run, with results shown to the human.
- No automatic merge in the MVP.
