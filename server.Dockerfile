FROM openvino/model_server:latest
LABEL maintainer="kaka <vn503024@gmail.com>"

COPY ./model /models/yolov3
