from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
import random, string


Base = declarative_base()
secret_key = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)


class Destination(Base):
    __tablename__ = 'destination'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    description = Column(String(2000))
    image = Column(String(250))
    times = Column(String(250))
    phone = Column(String(250))
    email = Column(String(250))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
            'description': self.description,
            'image': self.image,
            'times': self.times,
            'phone': self.phone,
            'email': self.email,
            'user_id': self.user_id 
        }



class Address(Base):
    __tablename__ = 'address'

    destination_id = Column(Integer, ForeignKey('destination.id'), primary_key=True)
    a_line_1 = Column(String(250))
    a_line_2 = Column(String(250))
    town = Column(String(250))
    postcode = Column(String(250))
    country = Column(String(250))
    user_id = Column(Integer, ForeignKey('user.id'))
    destination = relationship(Destination)
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'destination' : self.destination_id,
            'address line 1': self.a_line_1,
            'address line 2': self.a_line_2,
            'town' : self.town,
            'postcode' : self.postcode,
            'country' : self.country
        }



class Attraction(Base):
    __tablename__ = 'attraction'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    price = Column(String(8))
    image = Column(String(500))
    category = Column(String(250))
    info = Column(String(2000))
    image = Column(String(500))
    destination_id = Column(Integer, ForeignKey('destination.id'))
    destination = relationship(Destination)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'description': self.description,
            'info':self.info,
            'image': self.image,
            'id': self.id,
            'price': self.price,
            'category': self.category,
        }


engine = create_engine('sqlite:///LAFDatabase.db')
Base.metadata.create_all(engine)
