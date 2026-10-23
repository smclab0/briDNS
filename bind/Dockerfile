FROM alpine:3.20

RUN apk add --no-cache bind bind-tools tzdata \
 && mkdir -p /var/lib/bind /var/cache/bind /run/named \
 && chown -R named:named /var/lib/bind /var/cache/bind /run/named

EXPOSE 53/udp 53/tcp

# -g: foreground, log to stderr
CMD ["named", "-g", "-u", "named", "-c", "/etc/bind/named.conf"]
