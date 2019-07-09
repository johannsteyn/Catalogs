from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
#from sqlalchemy_utils import database_exists, drop_database, create_database
from base import Category, SportItem, User, Base

engine = create_engine('sqlite:///fakecatalog.db')
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)

# session.rollback()
session = DBSession()

#inital information
category1 = Category(name="Sports", user_id=1)

session.add(category1)
session.commit()

sportitem1 = SportItem(name="Baseball", description="This set comes with a baseball bat and glove",
                     price="$12.00", category=category1)

session.add(sportitem1)
session.commit()


sportitem2 = SportItem(name="Soccer", description="This set comes with soccer ball and shin guards",
                     price="$11.99", category=category1)

session.add(sportitem2)
session.commit()

sportitem2 = SportItem(name="Golf", description="This set comes with golf club and shoes",
                     price="$50.00", category=category1)

session.add(sportitem2)
session.commit()

sportitem3 = SportItem(name="Baseketball", description="This set comes with a baseketball and foot pump",
                     price="$15.00", category=category1)

session.add(sportitem3)
session.commit()

sportitem4 =SportItem(name="Karate", description="This set comes with a uniform and a belt",
                     price="$40.00", category=category1)

session.add(sportitem4)
session.commit()

sportitem5 = SportItem(name="Lacross", description="This set comes with a helmet and a lacross stick",
                     price="$35.00", category=category1)

session.add(sportitem5)
session.commit()

sportitem6 = SportItem(name="Tennis", description="This set comes with a racket and a tube to tennis balls",
                     price="$11.99", category=category1)

session.add(sportitem6)
session.commit()

sportitem7 = SportItem(name="Hockey", description="This set comes with a hockey stick and a puck",
                     price="$10.99", category=category1)

session.add(sportitem7)
session.commit()

sportitem8 = SportItem(name="Rugby", description="This set comes with a Rugby ball and cleats",
                     price="$30.00", category=category1)
session.add(sportitem8)
session.commit()
categories = session.query(Category).all()
print ("added sport items!")
