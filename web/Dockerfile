FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY mockup.html /tmp/mockup.html

# mockup.html is a page body (it doubles as a Claude artifact), so wrap it in a full document
RUN { \
      echo '<!doctype html><html lang="en"><head><meta charset="utf-8">'; \
      echo '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'; \
      echo '</head><body>'; \
      cat /tmp/mockup.html; \
      echo '</body></html>'; \
    } > /usr/share/nginx/html/index.html && rm /tmp/mockup.html
