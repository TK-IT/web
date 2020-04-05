FROM python:3.7 AS dist

LABEL org.opencontainers.image.title="TKWEB" \
  org.opencontainers.image.vendor="TÅGEKAMMERET" \
  org.opencontainers.image.url="https://TAAGEKAMMERET.dk" \
  org.opencontainers.image.source="https://github.com/TK-IT/web"


# Force the stdout and stderr streams from python to be unbuffered. See
# https://docs.python.org/3/using/cmdline.html#cmdoption-u
ENV PYTHONUNBUFFERED=1


WORKDIR /code/
#COPY docker/sys-requirements.txt sys-requirements.txt
# hadolint ignore=DL3008,DL4006
RUN set -ex \
  # Add a tkammer group and user. Note: this is a system user/group, but have
  # UID/GID above the normal SYS_UID_MAX/SYS_GID_MAX of 999, but also above the
  # automatic ranges of UID_MAX/GID_MAX used by useradd/groupadd. See
  # `/etc/login.defs`. Hopefully there will be no conflicts with users of the
  # host system or users of other docker containers.
  && groupadd -g 847587 -r tkammer\
  && useradd -u 847587 --no-log-init -r -g tkammer tkammer
  # Install system dependencies from file.
  #&& apt-get -y update \
  #&& apt-get -y install --no-install-recommends "$(grep -Eo '^(\w|-)+' sys-requirements.txt | paste -sd ' ')" \
  # clean up after apt-get and man-pages
  #&& apt-get clean && rm -rf "/var/lib/apt/lists/*" "/tmp/*" "/var/tmp/*" "/usr/share/man/??" "/usr/share/man/??_*"

# Install requirements
COPY requirements.txt /code/requirements.txt
RUN pip3 install -r requirements.txt

COPY docker ./docker
COPY manage.py ./manage.py
COPY tkweb ./tkweb

# Copy frontend code.
#COPY --from=frontend /code/frontend/package.json ./frontend/package.json
#COPY --from=frontend /code/frontend/dist ./frontend/dist

# Run the server as the mora user on port 5000
USER tkammer:tkammer
EXPOSE 5000
#ENTRYPOINT ["/code/docker/docker-entrypoint.sh"]
CMD ["gunicorn", "-b", "0.0.0.0:5000", "tkweb.wsgi"]
