# They All Float Down Here

Pick away at several floating-point puzzles. Some are normal floating-point operations and some are bitwise operations.

**NICE Work Roles**

- [Secure Software Development](https://niccs.cisa.gov/tools/nice-framework/)
- [Vulnerability Analysis](https://niccs.cisa.gov/tools/nice-framework/)

**NICE Tasks**

- [T1117](https://niccs.cisa.gov/tools/nice-framework/): Determine if desired program results are produced
- [T1197](https://niccs.cisa.gov/tools/nice-framework/): Identify common coding flaws
- [T1118](https://niccs.cisa.gov/tools/nice-framework/): Identify vulnerabilities

## Background

Sometimes integer overflows cause strange software bugs. Sometimes these bugs have security implications. But what about floating-point values and *their* handling in code?

## Getting Started

From kali, download the convenience script from `http://float-server:8000/curl_command.sh` (e.g., `curl -O http://float-server:8000/curl_command.sh && chmod +x curl_command.sh`). This script makes it easy to interact with the target server. The first argument is the challenge part number. The next two arguments are input values. All values are expected to be JSON `number` values. An example submission might be `./curl_command.sh 1 8.5 9e123`, which would attempt to submit the values `8.5` and `9e123` for part 1.

Upon sending a valid request to the server, the server will do a hidden computation. If the server, using your two input values in the computation for each part, computes its expected result, you will receive a token for that part. Otherwise the server will send back the bit string it expects and the value it corresponds to in [IEEE 754](https://en.wikipedia.org/wiki/IEEE_754) double-precision.

As mentioned above, some of these operations are more natural operations on floating-point, while others are bitwise operations and will require engineered inputs.

## Tokens

- Token 1: `float-server:8000/part1` token.
- Token 2: `float-server:8000/part2` token.
- Token 3: `float-server:8000/part3` token.
- Token 4: `float-server:8000/part4` token.

## System and Tool Credentials

|system/tool|username|password|
|-----------|--------|--------|
|kali|user|password|
|`http://float-server:8000`|N/A|N/A|
