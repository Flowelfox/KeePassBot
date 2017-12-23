from peewee import CharField, DateTimeField, BlobField, Model, SqliteDatabase, DoesNotExist, BooleanField, IntegerField

from settings import DATABASE

database = SqliteDatabase(DATABASE)

# model definitions -- the standard "pattern" is to define a base model class
# that specifies which database to use.  then, any subclasses will automatically
# use the correct storage.
class BaseModel(Model):
    class Meta:
        database = database


class User(BaseModel):
    username = CharField(unique=True)
    join_date = DateTimeField()
    file = BlobField(null=True)
    is_opened = BooleanField(default=False)
    interface_message_id = IntegerField(default=0)
    key_file_needed = BooleanField(default=False)
    password_needed = BooleanField(default=True)

    class Meta:
        order_by = ('username',)

    @classmethod
    def get_or_none(cls,**kwargs):
        try:
            return User.get(**kwargs)
        except DoesNotExist:
            return None



def create_tables():
    database.connect()
    database.create_tables([User])

if __name__ == "__main__":
    create_tables()