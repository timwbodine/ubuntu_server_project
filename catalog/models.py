import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
engine = create_engine('postgresql+psycopg2://catalog:password@/catalog')
Base = declarative_base()

# Class declarations

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key = True)
    name = Column(String(32), index = True)
    email = Column(String(250), index = True)
    picture = Column(String(250), index = True)
    
class Cuisine(Base):
    __tablename__ = 'cuisines'
    cuisine_id = Column(String(80), primary_key=True)
    
    @property
    def serialize(self):
        return {
            'cuisine_id' : self.cuisine_id
        }
class Recipe(Base):
    __tablename__ = 'recipes'
    name = Column(String(80), nullable = False)
    description = Column(String(10000))
    difficulty = Column(String, ForeignKey('difficulties.difficulty_id'), nullable=False)
    cuisine_id = Column(String, ForeignKey('cuisines.cuisine_id'), nullable=False)
    cuisine = relationship(Cuisine)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship(User)
    id = Column(Integer, primary_key=True)
    @property
    def serialize(self):
        return {
            'name' : self.name,
            'description' : self.description,
            'difficulty' : self.difficulty,
            'cuisine_id' : self.cuisine_id,
            'user_id' : self.user_id,
            'id' : self.id
        }

class Difficulty(Base):
    __tablename__ = 'difficulties'
    difficulty_id = Column(String(80), primary_key=True)

class Ingredient(Base):
    __tablename__ = 'ingredients'
    name = Column(String(80), nullable = False)
    id = Column(Integer, primary_key = True)
    recipe_id = Column(Integer, ForeignKey('recipes.id'))
    recipe = relationship(Recipe)
    amount = Column(String(80))
    unit = Column(String(80))
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship(User)

Base.metadata.create_all(engine)
