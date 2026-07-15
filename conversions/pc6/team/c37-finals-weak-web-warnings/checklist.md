# Challenge Title

All parts of this checklist must be complete before the challenge dev can mark the challenge as 100% complete.

## VMs

- [ ] VM command history has been cleared/removed
- [ ] VM logs have been cleared/removed (where applicable)
- [ ] VM browser history has been cleared/removed
- [ ] Team challenges have replicas = -1 on competitor workstations
- [ ] Challenge Server is configured with `required_services` for all parts of the challenge where a service/host/port is required for the challenge to operate
- [ ] Challenge Server is used for all startup scripts (Startup scripts on other VMs should be on the Challenge Server if possible, and only on other VMs when required)
- [ ] All VMs running services that are required for the challenge are forwarding logs to Graylog

## Workspace

- [ ] Challenge Workspace has the required `code` and `variant` transforms configured for the Challenge Server
- [ ] Workspace Description contains a brief (1-2 sentence) description of the challenge
- [ ] Workspace Tags contains `pc6-<challenge-id> prescup` 
- [ ] Workspace Audience contains `cisa-playtest prescup`

## Challenge Guide

- [ ] Challenge Guide follows the [standard template](~/templates/challenge-guide.md)
- [ ] Challenge Guide is concise, has a clear call to action, and is free of spelling/grammar errors
- [ ] Challenge Guide has been reviewed by at least 1 other Challenge Developer that did not help develop the challenge **(list the other Challenge Dev here)**
- [ ] Challenge Guide does not reference "internal nomenclature" (e.g., "challenge server", "c01", etc. )

## Challenge Questions

- [ ] Questions are clear, concise, and free of spelling/grammar errors
- [ ] Question weights add up to 100% (or 1)
- [ ] There are no more than 5 Challenge Questions
- [ ] The configured answer type is as permissive as possible (e.g., accepted answers for a file path should use `MatchAlpha` to ignore differences in `/` vs. `\\`, )

## Solution Guide

- [ ] Solution Guide follows the [standard template](~/templates/solution-guide.md)
- [ ] Challenge can be solved by following the steps in the solution guide without any additional context/knowledge

## GitLab

- [ ] GitLab folder contains the challenge guide in `README.md`
- [ ] GitLab folder contains the solution guide in `solution/README.md`
- [ ] GitLab folder contains a complete `technical-details.md`
- [ ] GitLab folder contains challenge artifacts in `challenge/` along with `challenge/README.md` to explain what the artifacts are and how to use them 

## Challenge Solve

- [ ] Challenge Developer has run through a full solve of the challenge (if there if more than one challenge dev, **all devs** must complete a full solve of the challenge)
