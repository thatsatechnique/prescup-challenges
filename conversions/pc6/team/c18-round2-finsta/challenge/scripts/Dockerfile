FROM pccc/challenge-server:base

# Node.js for doXSS.js, paramiko for the SSH/SFTP pull of socialmedia.db
RUN apt-get update && \
    apt-get install -y nodejs npm && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir paramiko

# Required: challenge-server config
COPY ./grader_config.yml /config.yml

# Grading script (triggers Greg's XSS visit) and the jsdom harness it shells out to
COPY ./runXSS.py /custom_scripts/
COPY ./xss /custom_scripts/xss/

# npm install for jsdom. The upstream file is named packages.json; rename so `npm install` picks it up.
RUN mv /custom_scripts/xss/packages.json /custom_scripts/xss/package.json && \
    cd /custom_scripts/xss && npm install

RUN chmod -R +x /custom_scripts
