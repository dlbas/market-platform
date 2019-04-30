FROM nginx:latest


# actually copy files in separate lines is considered a good practice
# because when Docker builds the image one more time it will check every file atomically and recreate the layers
# only if needed
COPY ./emulation .
COPY ./market-platform-client-api .
RUN cat ./emulation >> /etc/nginx/conf.d/default.conf && \
    cat ./market-platform-client-api >> /etc/nginx/conf.d/default.conf
