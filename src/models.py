from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from src.settings import DATABASE

Base = declarative_base()
engine = create_engine(DATABASE)


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)

    chat_id = Column(Integer)
    name = Column(String)
    username = Column(String)
    active = Column(Boolean, default=False)
    join_date = Column(DateTime)

    file = Column(LargeBinary)
    is_opened = Column(Boolean, default=False)
    interface_message_id = Column(Integer, default=0)
    key_file_needed = Column(Boolean, default=False)
    password_needed = Column(Boolean, default=False)
    create_state = Column(Boolean, default=False)
    notification = Column(Boolean, default=True)


Session = sessionmaker(bind=engine)
DBSession = Session()
