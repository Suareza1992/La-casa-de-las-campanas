from sqlalchemy import Column, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class ProductItem(Base):
    __tablename__ = 'product_items'

    id = Column(Integer, primary_key=True)
    image_name = Column(String, nullable=False)
    caption = Column(Text, nullable=True)
    name = Column(String, nullable=True)
    price = Column(String, nullable=True)
    category = Column(String, nullable=True)

engine = create_engine('sqlite:///product_data.db')
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)
