# Project instructions

- Version control: this repository uses **jj** (Jujutsu), not git. Use `jj` commands (e.g. `jj status`, `jj diff`, `jj describe`, `jj new`).
- Runtime: dependencies are installed and code is run via Docker using the `Dockerfile` at the repo root.
- Dependencies are managed with **uv**, but never run `uv` on the host — always run it inside the Docker container (image `laya-agent`, see `justfile`).
- Command runner: use **just** via the `justfile` at the repo root. Check existing recipes first (`just --list`); record complicated or repeated invocations (e.g. docker build/run) as new recipes instead of running them ad hoc.