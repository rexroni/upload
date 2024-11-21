# upload.py

A personal upload server.

Hide it behind nginx, at a url you only give to your friends, and which you
only leave up for a short time.

## Nginx config

    server {
        server_name rexroni.com;
        listen 443 ssl;
        # typical ssl details

        # whatever your normal server does
        # root /srv/http;
        # location / {
        #     ...
        # }

        # personal upload server
        location /<your-freshly-generated-uuid-here> {
            proxy_pass http://localhost:3030;
            client_max_body_size 10000M;
        }
    }

## Installation

* `useradd --system -M -s /bin/true upload`
* `cp upload.py /usr/local/bin`
* `cp upload.service /etc/systemd/system`
* `systemctl daemon-reload`
* configure your nginx proxy with a fresh uuid
