# Finsta

## Summary

In Finsta, the team is tasked with exploiting several vulnerabilities available on a new social media website, `finsta.us`.

## VMs

This challenge uses the PC6 Stock Topology competitor network only.

#### Competitor Network

- challenge-server-finsta [OS: Ubuntu 22.04.04 Desktop, Network: (competitor challenge-net), IPv4: 10.5.5.5, Unlinked]
    - Runs the [Grading Script](./challenge/scripts/runXSS.py) which simulates user interaction for task 4 (XSS).

- kali [OS: Kali, Network: competitor, IPv4: DHCP, Unlinked]
    - President's Cup 6 default Kali system 
    - jwt is installed and wordlist for wfuzz copied to desktop

- finsta [OS: Ubuntu 22.04.04 Server, Network: (competitor), IPv4: DHCP (`finsta.us`), Unlinked]
    - Uses gunicorn to host the Finsta Flask application
    - Gunicorn uses a unix socket, exposed on port 80 using nginx 
    - User: `user` Password: `L1k3AndSubscr1b3!?`

## Grading

Task 4 uses a [Grading Script](./challenge/scripts/runXSS.py), however, this grading script does not provide a token. Instead, it stimulates a user (Greg) visiting `finsta.us`. The token is found in Greg's cookies, which should be retrieved using the XSS on their Finsta profile.

## Troubleshooting Tips

#### Quick Look

- The grading logs can be found on the challenge server in `/var/log/challengeGrader/gradingCheck.log`
- The logs for the Finsta site can be found using journalctl on the finsta server: `sudo journalctl -u finsta`

#### Quick Tips

- The Finsta flask service can be reset using systemd: `sudo systemctl stop finsta && sudo systemctl start finsta`
- If there is an error with the grading check, make sure that the challenge server can SSH into the finsta server and that the correct password is in the grading script. The grading script must connect over SSH to download the database to determine which profiles to view.


## Spotting - What to look for when a competitor is solving

By task:

1. The team should be exploring the site, discovering the SQL injection in the search bar on the top right of the website, then trying to use sqlmap to extract the data
2. The team should be reviewing the posts from the `finsta` user account, and then using `wfuzz` in the terminal to work out the valid key and GET params for the API.
3. The team should be reviewing their cookies and using the `jwt` command to read and create a JSON Web Token.
4. The team should be using the profile edit page to inject Javascript into the style textarea, then using something like `python -m http.server` to catch a XSS web request. They should be using `challenge.us` to trigger the XSS interaction. 
