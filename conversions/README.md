# Converted Challenges

This directory holds President's Cup challenges from seasons **prior to Season 7 (2026)** rebuilt for the modern **CTF-NG** platform. Every challenge in here is fully self-contained: the artifacts needed to build, run, and solve it ship alongside it, so anyone can stand the challenge up locally with Docker, deploy it to CTF-NG, or adapt it to another environment — no proprietary VM images, no hosted-only dependencies.

Conversion is ongoing. Earlier seasons were authored as virtual-machine builds tied to the President's Cup hosted practice area; those don't translate directly to a containerized, reproducible format. This directory is where each challenge lands once it's been reworked, verified, and confirmed to run end-to-end. It will grow over time — the goal is to bring the full back-catalog forward.

## Why this matters

- **Genuine open source.** A challenge you can't run isn't really released. These conversions replace VM snapshots and hosted infrastructure with plain Docker services and source you can read, so the published artifacts are the whole challenge — not a description of one.
- **Full platform replication.** Each challenge is a complete, deployable unit. Clone the repo, and you have everything required to reproduce the competition environment on your own hardware or in your own CTF-NG instance.
- **Reproducible and portable.** Builds are deterministic and containerized. What runs on a laptop is the same thing that runs on the platform, which makes the challenges reliable for training, practice, and study long after the original event.
- **Readable and adaptable.** Source is baked into the images at build time rather than hidden in a VM disk. Instructors and learners can inspect how a challenge works, modify it, or lift techniques into new material.

## What each challenge contains

```
<season>/<track>/<challenge>/
├── README.md            # player-facing brief: scenario, tasks, tokens
├── challenge/
│   ├── docker-compose.yml   # CTF-NG x-challenge block + services + competitor_net
│   └── <service>/...        # Dockerfiles and application source (baked into images)
└── solution/
    └── README.md        # full walkthrough and answer key
```

Naming follows the source competition: `{track}/{round}-{challenge-name}`.

## Running a challenge

Challenges ship in the production (CTF-NG) network posture. Two ways to run one:

**Locally with Docker** — pre-create the shared network once, flip the challenge to local networking, and bring it up:

```bash
# once per machine
docker network create --driver bridge competitor_net

# once — builds the shared challenge-server base image (pccc/challenge-server:base)
# that a few challenges' customized graders build from. Harmless to run always.
./build-base.sh

cd <season>/<track>/<challenge>/challenge
# in docker-compose.yml, comment `internal: true` and uncomment the
# `external: true` line under competitor_net (marked "enable if running locally")
docker compose up --build
```

Every service builds from source in the repo — no image is pulled from a private
registry. The challenge server lives at [`challenge-server/`](./challenge-server/);
services that need it build it directly, and the handful with a customized grader
build `FROM pccc/challenge-server:base` (produced by `build-base.sh`).

**On CTF-NG** — the platform provisions networking, DNS (`*.pccc` via the challenge server), and sizing; leave `internal: true` active. See the individual challenge and solution READMEs for tokens, hostnames, and any per-challenge notes.

## Status

Conversion is **in progress** and will take time. Everything that has been fully converted and verified lives here; a challenge only appears once it runs cleanly.

Currently converted:

| Season | Track | Challenges |
|---|---|---|
| **pc6** (Season 6, 2025) | team | The Triple Lindy · Throw Me a Bone · Shop Smart · They All Float Down Here · Finsta · Ransomware Rhapsody · WWW (Weak Web Warnings) |
| **pc6** (Season 6, 2025) | individual-offense | Let Loose the Logs of War · va_list Adventure · Kessel Run · The Crucible · Mindhunter |

More seasons (pc5 and earlier, pc6 Round 1) will be added here as they're completed. The original, unconverted challenge content remains in the year-season directories at the repository root (`/pc5`, `/pc6`, `/pc6-round1`, …).
