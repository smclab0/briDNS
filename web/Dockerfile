FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY mockup.html login.html /tmp/pages/

# The pages are bodies only (they double as Claude artifacts), so wrap each in a full document
RUN for p in mockup:index login:login; do \
      src=${p%%:*}; dst=${p##*:}; \
      { echo '<!doctype html><html lang="en"><head><meta charset="utf-8">'; \
        echo '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'; \
        echo '</head><body>'; \
        cat /tmp/pages/$src.html; \
        echo '</body></html>'; \
      } > /usr/share/nginx/html/$dst.html; \
    done && rm -r /tmp/pages
