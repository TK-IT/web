# Use an official Python runtime as a parent image
FROM python:3
ENV PYTHONUNBUFFERED 1

RUN mkdir /code

# Set the working directory to /app
WORKDIR /code

# Copy the current directory contents into the container at /app
ADD . /code

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

EXPOSE 8000

ENV DJANGO_SETTINGS_MODULE=tkweb.settings.docker

ENTRYPOINT ["/code/docker-entrypoint.sh"]

CMD python3 manage.py runserver 0.0.0.0:8000
