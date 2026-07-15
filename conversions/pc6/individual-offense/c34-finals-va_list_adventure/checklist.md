# The ModFather

All parts of this checklist must be complete before the challenge dev can mark the challenge as 100% complete

## VMs

- [x] VM command history has been cleared/removed
- [x] VM logs have been cleared/removed (where applicable)
- [x] VM browser history has been cleared/removed
- [x] Team challenges have replicas = -1 on competitor workstations
- [x] Challenge Server is configured with `required_services` for all parts of the challenge where a service/host/port is required for the challenge to operate
- [x] Challenge Server is used for all startup scripts (Startup scripts on other VMs should be on the Challenge Server if possible, and only on other VMs when required)
- [x] All VMs running services that are required for the challenge are forwarding logs to Graylog

## Workspace

- [x] Challenge Workspace has the required `code` and `variant` transforms configured for the Challenge Server
- [x] Workspace Description contains a brief (1-2 sentence) description of the challenge
- [x] Workspace Tags contains `pc6-<challenge-id> prescup` 
- [x] Workspace Audience contains `cisa-playtest prescup`

## Challenge Guide

TODO: Need review from challenge dev

- [x] Challenge Guide follows the [standard template](~/templates/challenge-guide.md)
- [ ] Challenge Guide is concise, has a clear call to action, and is free of spelling/grammar errors
- [ ] Challenge Guide has been reviewed by at least 1 other Challenge Developer that did not help develop the challenge **(list the other Challenge Dev here)**
- [x] Challenge Guide does not reference "internal nomenclature" (e.g., "challenge server", "c01", etc. )

## Challenge Questions

- [ ] Questions are clear, concise, and free of spelling/grammar errors
- [x] Question weights add up to 100% (or 1)
- [x] There are no more than 5 Challenge Questions
- [x] The configured answer type is as permissive as possible (e.g., accepted answers for a file path should use `MatchAlpha` to ignore differences in `/` vs. `\\`, )

## Solution Guide

- [x] Solution Guide follows the [standard template](~/templates/solution-guide.md)
- [x] Challenge can be solved by following the steps in the solution guide without any additional context/knowledge

## GitLab

- [x] GitLab folder contains the challenge guide in `README.md`
- [x] GitLab folder contains the solution guide in `solution/README.md`
- [x] GitLab folder contains a complete `technical-details.md`
- [x] GitLab folder contains challenge artifacts in `challenge/` along with `challenge/README.md` to explain what the artifacts are and how to use them 

## Challenge Solve

- [x] Challenge Developer has run through a full solve of the challenge (if there if more than one challenge dev, **all devs** must complete a full solve of the challenge)