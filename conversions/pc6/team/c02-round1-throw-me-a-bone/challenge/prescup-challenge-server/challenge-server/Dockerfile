FROM 253388214223.dkr.ecr.us-east-1.amazonaws.com/pc7/challenge-server

# The grading check and the in-challenge scanner both SSH into the six servers
RUN pip install --no-cache-dir paramiko

# c02-specific config + grading scripts (the standard server, src, dns, coredns,
# wallpapers, etc. all come from the base image)
COPY ./grader_config.yml /config.yml
COPY grader_scripts/ /custom_scripts/
RUN chmod +x /custom_scripts/*.py

# Hosted challenge artifacts (NTDS.dit, SYSTEM, vuln report, wordlist)
COPY hosted_files/ /hosted_files/

# In-challenge vulnerability scanner (served on :5555 by the entrypoint)
COPY scanner/ /app/scanner/

# Custom entrypoint launches the scanner before the standard challenge server
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
