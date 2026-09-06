# Build the image from the root of the gitinspector sources:
#   docker build -t gitinspector .
#
# Analyze a repository by mounting it on /repo:
#   docker run --rm -v "$PWD:/repo" gitinspector -f py -T
#   docker run --rm -v "$PWD:/repo" gitinspector -F html > report.html
#   docker run --rm gitinspector --help

FROM python:3-alpine

ENV PYTHONIOENCODING=utf-8

# The mounted repository belongs to the user on the host and not to root,
# which git refuses to read from unless the directory is marked as safe.
RUN apk add --no-cache git && \
    git config --global --add safe.directory '*'

COPY gitinspector/ /opt/gitinspector/gitinspector/
COPY gitinspector.py /opt/gitinspector/

WORKDIR /repo

ENTRYPOINT ["python3", "/opt/gitinspector/gitinspector.py"]
