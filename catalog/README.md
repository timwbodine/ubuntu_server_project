#test push from ubuntu
# Catalog Project
This is the Catalog project for the Udacity Full Stack Nanodegree program.
I chose to make a recipe app which allows you to create, edit and delete
recipes, as well as create, edit and delete ingredients for those recipes.  You
can view recipes and ingredients posted by other users but can only change ones
you've created.  I used google for authentication and authorization.
## QuickStart
This project assumes you are running the Vagrant VM specified for this project.
1. Clone or download this repo into a directory accessible by your vagrant machine
2. Install the google-auth python library with ```pip install google-auth``` 
3. register an OAuth2 client ID at the google developer console with
```http://localhost:5000```as the javascript origins and ```http://localhost:5000/allrecipes```and 
```http://localhost:5000/login``` as the redirect urls
4. Download the JSON of the client ID and rename it client_secrets.json. 
5. Place client_secrets.json in the project directory 
6. Run ```python make_recipes.py``` to populate database with a few sample recipes 
7. Run ```python views.py``` to launch the server.
8. open ```http://localhost:5000/allrecipes``` in your browser. 
