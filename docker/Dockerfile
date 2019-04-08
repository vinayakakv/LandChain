FROM alpine
RUN apk add --no-cache gcc make musl-dev py3-pip python3-dev libffi-dev openssl-dev g++ libstdc++ \
 && pip3 install flask bigchaindb_driver rapidjson pymongo\
 && apk del g++ make gcc
RUN adduser -D -u 1000 cryptoman
USER cryptoman
WORKDIR /home/cryptoman
COPY ../project-final /home/cryptoman/app
EXPOSE 8080
ENTRYPOINT ["python3","app/app.py"]
