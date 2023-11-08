FROM ghcr.io/natescherer/sre-devcontainer:latest

# Fix for https://github.com/python-babel/babel/issues/990
RUN rm -f /etc/localtime && ln -s /usr/share/zoneinfo/Etc/UTC /etc/localtime
