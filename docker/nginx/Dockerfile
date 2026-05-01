FROM nginx:1.29.1-alpine

# Copy common and frontend files
COPY frontend /frontend
COPY docker/nginx /docker
WORKDIR /frontend

# install NPM and NPX
RUN rm -rf /frontend/out; \
    apk add --update --no-cache bash gettext npm; \
    chmod +x /docker/scripts/entrypoint.sh; \
    dos2unix /docker/scripts/entrypoint.sh; \
    if ! grep -q "^NEXT_PUBLIC_BACKEND_URL=" /frontend/.env /frontend/.env.local 2>/dev/null; then \
      echo "NEXT_PUBLIC_BACKEND_URL=http://localhost:80" > /frontend/.env.local; \
    fi; \
    rm /etc/nginx/conf.d/default.conf; \
    cp /docker/nginx.conf /etc/nginx/conf.d/nginx.conf; \
    rm -rf /var/cache/apk/*

# Prepare entrypoint
EXPOSE 80
CMD ["/docker/scripts/entrypoint.sh"]
