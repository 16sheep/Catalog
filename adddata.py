#!/usr/bin/python
# -*- coding: utf-8 -*-
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from modules import Destination, Base, Attraction, User, Address

engine = create_engine('sqlite:///LAFDatabase.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Create dummy users
User1 = User(name="Lily Cross", email="lilycross03948@gmail.com")
session.add(User1)
session.commit()

User2 = User(name="Ray Hirsh", email="rayhirsh69@gmail.com")
session.add(User2)
session.commit()



# Destinations with attractions
destination1 = Destination(user_id=1, name="3 Tractors", description="Learn to drive a tractor and ride around our farm",
                            image="https://c.pxhere.com/photos/9f/65/farm_tractor_agricultural_equipment_machine_farmer_farming_agriculture-799939.jpg!d",
                            times="Friday-Sunday 9am - 4pm", phone="7700 900077", email="lilycross03948@gmail.com")

session.add(destination1)
session.commit()

address1 = Address(user_id=1, a_line_1="Berry Shute", a_line_2=None, town="Newport", postcode="PO30 3HA", country="United Kingdom", destination=destination1)

session.add(address1)
session.commit()

attraction1 = Attraction(user_id=1, name="Driving Lesson", description="Learn to drive a tractor" ,price="30", category="Learn something new", info="20 minute tractor driving lessons which end with completing an obstacle course. Must be sober and own a driving licence", destination=destination1)

session.add(attraction1)
session.commit()

attraction2 = Attraction(user_id=1, name="Tractor trailer tour", description="Discover our farm and newarby community from the back of a tractor trailer",
                     price="10", category="Family", info="See what is happening on our farm and at our neighbour's places, We will visit a sheep farm, dairy farm and traditional crafts center. Minimum group size 4 people. Please call ahead to arrange.", destination=destination1)


session.add(attraction2)
session.commit()

attraction3 = Attraction(user_id=1, name="Drive a Tractor", description="Drive a tractor around our farm",
                     price="20", category="Thing to do", info="Bring your friends and experience our 3 different tractors which can be driven around our 10 acre patch. Must have a driving licence, Must be sober.", destination=destination1)

session.add(attraction3)
session.commit()


destination2 = Destination(user_id=2, name="Ray's Bees", description="Come visit our independent organic honey farm",
                            image="https://c.pxhere.com/photos/38/78/hive_beehive_honey_apiary_bees_beekeeping_distributional_effects_meadow-536167.jpg!d",
                            times="Every day 11am - 6pm", phone="7700 900077", email="rayhirsh69@gmail.com")

session.add(destination2)
session.commit()

address2 = Address(user_id=2, a_line_1="Thorley Road", a_line_2=None, town="Yarmouth", postcode="PO41 0SJ", country="United Kingdom", destination=destination2)

session.add(address2)
session.commit()

attraction1 = Attraction(user_id=2, name="Honey tasting", description="Try our organic honey and honey products",
                     price="15", category="Food", info="Honey tasting package includes flavoured honey, raw honey, propolis health drink and honey cakes. The experience lasts about one hour.", destination=destination2)

session.add(attraction1)
session.commit()

attraction2 = Attraction(user_id=1, name="Make a beeswax candle", description="Make a beeswax candle from our wax",
                     price="10", category="Lesson", info="Take home a beautiful self made beeswax candle which can be made into any shape. Great activity for kids and adults", destination=destination2)

session.add(attraction1)
session.commit()

print "added destinations"