# Catalog Project
This is the server configuration project for the Udacity Fullstack Nanodegree program.   
In this project I have configured an amazon lightsail instance running Ubuntu to serve my catalog app.
This app is live and available at http://18.216.11.149.xip.io/allrecipes
I reconfigured the app to use postgres instead of sqlite, and the app interacts with the database as the "catalog" postgres user.

## QuickStart
1. Grader can ssh into my server with the as user grader, using the private key grader_rsa, on port 2200
2.  I have provided a config file to make this process a little easier.  You can put the config file and grader_rsa in ~/.ssh on your machine and then run the command ssh grader to connect.
