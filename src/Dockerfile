# Base image
FROM python:3.9

# Set the working directory to /app
WORKDIR /app

# Install dependencies
RUN apt-get update && \
    apt-get install -y postgresql-client gdal-bin libgeos-dev libgdal-dev python3-psycopg2 graphviz-dev postgresql-contrib

# Clone the project repository
RUN git clone https://github.com/NCLI/dreamlytest.git 

# Copy the requirements file and install dependencies
RUN pip install -r /app/dreamlytest/src/requirements.txt
RUN ls -la

WORKDIR /app/dreamlytest/src/daikoudream

# Expose port 8000
EXPOSE 8000

# Run the Django server
CMD ["python", "manage.py", "runserveir", "0.0.0.0:8000"]
