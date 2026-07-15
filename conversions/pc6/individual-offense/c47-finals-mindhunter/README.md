# Mindhunter

**Difficulty:** Hard | **Type:** Offensive / Individual | **Estimated time:** 3-4 hours

It's all about perspective. You have manifested a set of systems riddled with
complex web vulnerabilities that all share one thing in common: everything is not
as it seems. Traverse your `mind`, `body`, `soul`, and `peace` to regain control,
one perspective at a time.

**NICE Work Roles**

- [Vulnerability Analysis](https://niccs.cisa.gov/workforce-development/nice-framework/)
- [Exploitation Analysis](https://niccs.cisa.gov/workforce-development/nice-framework/)

**NICE Tasks**

- [T0280](https://niccs.cisa.gov/workforce-development/nice-framework/): Identify and validate vulnerabilities in the system.
- [T0653](https://niccs.cisa.gov/workforce-development/nice-framework/): Identify and recommend methods for exploiting target systems.
- [T0269](https://niccs.cisa.gov/workforce-development/nice-framework/): Conduct exploitation of targets using identified vulnerabilities.
- [T0650](https://niccs.cisa.gov/workforce-development/nice-framework/): Conduct target and technical analysis of systems and vulnerabilities.

## Background

Four internal web applications, each a different perspective of the same
troubled mind, guard a token behind a distinct web vulnerability. The
applications cannot be reached directly. A single jump host straddles your
network and theirs; you must pivot through it to reach them, then chain each
exploit in turn. Every application also watches which of its endpoints you
explore before it will yield, so thorough enumeration is as important as the
exploit itself. Progress is cumulative: each perspective you conquer reveals the
headers and tokens you need for the next.

## Getting Started

Launch the provided Kali workstation. From it, enumerate the competitor network
to locate the reachable jump host `perspective` (it listens for `SSH`). Log in
with the credentials below and use it as a pivot (for example an `SSH` dynamic
`SOCKS` proxy with `ssh -D`, optionally driven through `proxychains`) to reach
the four internal applications.

From the jump host, enumerate the internal network to discover the four target
applications, referred to as `mind`, `body`, `soul`, and `peace`. Each serves a
web application on its own port (`5001`, `5002`, `5003`, and `5004`) and exposes
an `/explorer` page describing its endpoints. Enumeration is key to success:
each application requires you to interact with a subset of its endpoints, using
the correct headers, before its vulnerability is exposed.

## Submission

There are four tokens to retrieve. Each token has the format `PCCC{...}`. A token
may be presented in a longer phrase such as `token: PCCC{...}`; submit only the
`PCCC{...}` value. Tokens must generally be recovered in order, because each
application requires the tokens and headers earned from the previous one.

- **Token 1 (300 points):** Recover the token revealed by the `mind` application
  on port `5001`.
- **Token 2 (400 points):** Recover the token revealed by the `body` application
  on port `5002`.
- **Token 3 (500 points):** Recover the token revealed by the `soul` application
  on port `5003`.
- **Token 4 (600 points):** Recover the token revealed by the `peace` application
  on port `5004`.

**Total: 1800 points.**

## Infrastructure and Access

| System | Role | Access |
|--------|------|--------|
| `perspective` | Pivot / jump host | `SSH` as `user` / `tartans` |
| `challenge.pccc` | Progress and challenge artifacts | Web page only |

The four target applications (`mind`, `body`, `soul`, `peace`) are on an internal
network and are reachable only by pivoting through `perspective`. Challengers must
determine their location.

## System and Tool Credentials

| System | Username | Password |
|--------|----------|----------|
| `perspective` | `user` | `tartans` |

## Rules

Attempting to circumvent portions of this challenge will increase the difficulty
and may lock you out of certain tokens. Be careful of the types of attacks used
and their timing; as your perspective changes, so do the defenses in your `mind`.
Source spoofing of headers such as `X-Forwarded-For` will not bypass the pivot
requirement.

## Skills Tested

- Network enumeration and pivoting through a `SOCKS` proxy
- Server-Side Request Forgery (`SSRF`)
- Prototype / parameter pollution
- Encoded command injection and restricted file retrieval
- Race-condition and timing-based exploitation
- HTTP header chaining and API endpoint enumeration

## Note

Attacking or unauthorized access to `challenge.pccc` is forbidden. You may only
use the provided web page to view challenge progress and download any challenge
artifacts that are provided.
