FROM ubuntu:latest

RUN apt-get update -y && \
    apt-get upgrade -y && \
    apt-get install -y python3 git python3-pip apt-utils build-essential python3-dev libbz2-dev libssl-dev && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install zeroc-ice

RUN apt-get install -y zeroc-icebox libzeroc-icestorm3.7

RUN mkdir -p /practica_distribuidos/FileService

RUN git clone git@github.com:molinem/ICEFLIX-FILESERVICE.git /practica_distribuidos/FileService
RUN cd /practica_distribuidos/FileService/ICEFLIX-FILESERVICE
RUN pip install dist/iceflix_file-0.1.tar.gz

WORKDIR /practica_distribuidos/FileService/ICEFLIX-FILESERVICE

CMD ./run_service
