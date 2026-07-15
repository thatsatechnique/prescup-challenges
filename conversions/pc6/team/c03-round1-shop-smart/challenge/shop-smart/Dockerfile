FROM php:8.2-apache-bookworm

RUN docker-php-ext-install mysqli \
    && apt-get update \
    && apt-get install -y --no-install-recommends curl mariadb-client unzip \
    && rm -rf /var/lib/apt/lists/*

# Enable output buffering to match the original Apache/PHP environment
RUN echo "output_buffering = 4096" > /usr/local/etc/php/conf.d/output-buffering.ini

# Extract website into webroot
COPY website.zip /tmp/website.zip
RUN unzip /tmp/website.zip -d /var/www/html/ \
    && rm /tmp/website.zip

# Override db.config.php to point at the db container
COPY db.config.php /var/www/html/includes/db.config.php

# Entrypoint handles flag injection at runtime
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Clean up artifacts that should not be in the running image
RUN rm -f /var/www/html/~.bash_history

# Set ownership so www-data (Apache) can read all files and write invoices
RUN chown -R www-data:www-data /var/www/html/

EXPOSE 80

ENTRYPOINT ["/entrypoint.sh"]
