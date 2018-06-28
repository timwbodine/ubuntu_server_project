# Catalog Project
This is the server configuration project for the Udacity Fullstack Nanodegree program.   
In this project I have configured an amazon lightsail instance running Ubuntu to serve my catalog app

This app is live and available at http://18.216.11.149.xip.io/allrecipes
I reconfigured the app to use postgres instead of sqlite, and the app interacts with the database as the "catalog" postgres user.

## QuickStart
1. Grader can ssh into my server with the as user grader, using the private key grader_rsa, ip address 18.216.11.149, port 2200 
2. I have provided a config file to make this process a little easier.  You can put the config file and grader_rsa in ~/.ssh on your machine and then run the command ssh grader to connect.
3. Once connected to server, the catalog project is located at /var/www/catalog

## Software installed
To complete this configuration, I installed apache2 in order to serve my Flask app.  I used mod_wsgi to connect my flask app to apache2.  I used postgres as my database and connected my app to the database using sqlalchemy.  
Configuration-wise, I changed the ssh port from 22 to 2200 and disabled password authentication, allowing only private key authentication.  I also disabled remote login with root.

## 3rd party resources
Douara and Sowmia from the Udacity chat helped me troubleshoot some issues I had with connecting to lightsail and with authorized javascript origins for google authentication of my app.  
I loosely followed this guide in setting up my server configuration: https://www.digitalocean.com/community/tutorials/how-to-deploy-a-flask-application-on-an-ubuntu-vps and https://www.digitalocean.com/community/tutorials/how-to-install-and-use-postgresql-on-ubuntu-16-04
I also made use of the Flask and Postgres official documentation, particularly http://flask.pocoo.org/docs/0.12/deploying/mod_wsgi/
