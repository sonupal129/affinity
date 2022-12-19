FROM python:3.7

ENV PYTHONUNBUFFERED 1
RUN apt-get update
RUN apt-get upgrade -y
RUN useradd affinity
RUN mkdir /affinity
RUN chown -R affinity:affinity /affinity
COPY . /affinity
WORKDIR /affinity
RUN pip install -r requirements.txt
USER affinity

# RUN chown -R atom:atom /home/atom
# ENV PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/hatom/.local/bin