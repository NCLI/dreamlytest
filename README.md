To start the server, enter the src directory and run "docker-compose up".

When starting the server for the first time, make sure to run "docker-compose exec web python manage.py migrate" from the src directory in a separate window. This must be done after starting the server using docker-compose, but before attempting to access the site.
