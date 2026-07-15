FROM 253388214223.dkr.ecr.us-east-1.amazonaws.com/pc7/challenge-server

# Required: challenge-server config
COPY ./grader_config.yml /config.yml

COPY ./files.html /app/templates/files.html
COPY ./KesselRun.png /app/static/KesselRun.png

COPY ./KesselRun.png /hosted_files/

# Ship the proxy source (kept unzipped in source) as a single zip in hosted_files
COPY ./proxies_provided /tmp/proxies_provided
RUN python3 -c "import shutil; shutil.make_archive('/hosted_files/proxies_provided', 'zip', '/tmp', 'proxies_provided')"