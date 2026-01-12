FROM rockylinux:8

# Set Work Directoy
WORKDIR /app

# Set Environment Variables
ENV PYTHONUNBUFFERED=1

# Update all files
RUN yum -y update

# Install Dependencies
RUN yum install -y git
RUN yum install -y python39
RUN python3 -V
RUN python3 -m pip install --upgrade pip --user
RUN python3 -m pip install --upgrade setuptools --user
RUN python3 -m pip install --upgrade wheel --user
COPY ./requirements.txt .
RUN python3 -m pip install -r requirements.txt --user
# Needed to find gunicorn using python39 now
ENV PATH="/root/.local/bin:${PATH}"

# Copy Project
COPY . .
