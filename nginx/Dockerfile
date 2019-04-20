FROM nginx:latest

COPY ./emulation .
COPY ./market-platform-client-api .
RUN cat ./emulation >> /etc/nginx/conf.d/default.conf
RUN cat ./market-platform-client-api >> /etc/nginx/conf.d/default.conf
