FROM alpine
RUN apk add --no-cache gcc make musl-dev py3-pip python3-dev libffi-dev openssl-dev g++ \
 && pip3 install flask bigchaindb_driver \
 && apk del g++ make gcc
RUN adduser -D -u 1000 cryptoman
RUN apk add --no-cache libstdc++
USER cryptoman
WORKDIR /home/cryptoman
ENTRYPOINT ["python3","app/app.py"]
