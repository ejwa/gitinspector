FROM python:2-alpine3.7

ENV PYTHONIOENCODING=utf-8

RUN apk add --no-cache git \
 && apk add --no-cache tree

ADD gitinspector/ /tmp/gitinspector/gitinspector/
ADD DESCRIPTION.txt /tmp/gitinspector/
ADD setup.py /tmp/gitinspector/

WORKDIR /tmp/gitinspector
RUN python setup.py install

WORKDIR /
RUN rm -r /tmp/gitinspector

WORKDIR /repo

ENTRYPOINT ["gitinspector"]