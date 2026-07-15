# Finsta

Your team has been tasked with infiltrating a social media site.

**NICE Work Roles**

- [Exploitation Analysis](https://niccs.cisa.gov/workforce-development/nice-framework/)
- [Vulnerability Analysis](https://niccs.cisa.gov/workforce-development/nice-framework/)

**NICE Tasks**

- [T1091](https://niccs.cisa.gov/workforce-development/nice-framework/): Perform authorized penetration testing on enterprise network assets.
- [T1118](https://niccs.cisa.gov/workforce-development/nice-framework/): Identify vulnerabilities.

## Background

Use the provided Kali machine to investigate and exploit `finsta.pccc`, a new social media site.

## Getting Started

Log in to the provided Kali VM and visit `http://finsta.pccc` to access the social media site. You can (and should) create your own account(s) on `Finsta.pccc`. Visit `challenge.pccc` to have Greg browse `finsta.pccc` for Token 4. The Kali VM has `wfuzz` installed with the default wordlist at `/usr/share/wfuzz/wordlist/general/common.txt` and `jwt` is also installed.

## Submission

There are 4 tokens to retrieve in this challenge. Each token has the format `PCCC{xxxxxx}` where the contents are 6 hexadecimal characters. The tokens can be retrieved in any order. Token 4 requires visiting `challenge.pccc` to trigger user interaction (`challenge.pccc` does not grant Token 4).

- Token 1: Retrieve the token stored as the password of the social media user `targettim`.
    - You do not need to (and can not) log in as `targettim` or any of the other existing users. You can create your own account, however.
- Token 2: The user `finsta` accidently posted a token, but quickly deleted it. We know deleted posts are not stored in the database, but believe they are still accessible elsewhere. Recover the token.
- Token 3: This token can be recovered from the home page after becoming a premium user.
- Token 4: The user `gregariousgreg` has a token in his cookies with `httpOnly=false`. Visit `challenge.pccc` and click grade to trigger `gregariousgreg` to browse `finsta.pccc` with this token. Greg will search for posts he likes and visit the poster's profile page. Note `challenge.pccc` will not provide the token.

## Grading

You can visit `challenge.pccc` and click the grade button to trigger `gregariousgreg` for Token 4, but `challenge.pccc` will not provide Token 4 (instead, the token must be extracted from Greg's cookies).

## System and Tool Credentials

|system/tool|username|password|
|-----------|--------|--------|
|kali|user|password|

## Note

Attacking or unauthorized access to `challenge.pccc` is forbidden. You may only use the provided web page to view challenge progress and download any challenge artifacts that are provided.
