import sys
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import create_engine


engine = create_engine('sqlite:///fakecatalog.db')
Base = declarative_base(bind=engine)

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))
    categories = relationship("Category", backref="user")
class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key = True)
    name = Column(String(255), nullable = False)
    item = relationship("SportItem", backref="category")
    user_id = Column(Integer, ForeignKey('user.id'))
    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'name': self.name
        }
class SportItem(Base):
    __tablename__ = 'sport_item'

    id = Column(Integer, primary_key = True)
    name = Column(String(255), nullable = False)
    description = Column(String(2048))
    price = Column(String(255))
    created = Column(DateTime(timezone=True), default=func.now())
    category_id = Column(Integer, ForeignKey('category.id'))
    user_id = Column(Integer, ForeignKey('user.id'))
    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
        }


