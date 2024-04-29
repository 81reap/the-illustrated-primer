FROM ghcr.io/tursodatabase/libsql-server:main

ENV SQLD_NODE=primary
ENV DB_PATH="/data"
ENV HTTP_LISTEN_ADDR="0.0.0.0:8085"
ENV ADMIN_LISTEN_ADDR="0.0.0.0:8580"
ENV ENABLE_NAMESPACES=true
ENV GRPC_LISTEN_ADDR="0.0.0.0:5001"

VOLUME /data

EXPOSE 8085 8580 5001

CMD sqld --db-path $DB_PATH \
  --http-listen-addr $HTTP_LISTEN_ADDR \
  --admin-listen-addr $ADMIN_LISTEN_ADDR \
  --grpc-listen-addr $GRPC_LISTEN_ADDR 
  #--enable-namespaces
