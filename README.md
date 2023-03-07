To start the server, enter the src directory and run "docker-compose up".

When starting the server for the first time, make sure to run "docker-compose exec web python manage.py migrate" from the src directory in a separate windo after running docker-compose, but before attempting to access the site.
