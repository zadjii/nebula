from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table, BigInteger
from host.models import nebs_base as base
__author__ = 'Mike'


class Client(base):
    """
    This Client represents a host's view of a connecting client.
    Whenever a client message comes in, we'll first see if we have seen that
    client before.
     - If we have, great. Update any relevant info in here, and use it.
    Else, go to the Remote, and ask them if this session is legit
    (HostVerifyClient)
     - If it is, make one of these entries, and use it.
     - If it isn't, reject the request.
    """
    __tablename__ = 'client'

    id = Column(Integer, primary_key=True)

    # This entry represents the client asking for one particular cloud.
    # if the same client is used for multiple clouds on this host, that's fine.
    # there will just be many Session objects for them.
    cloud_id = Column(ForeignKey('cloud.id'))
    uuid = Column(String)  # todo:11 length should be the uuid length
    # todo:11 fix the type of this ^

    # I'm going to not add this.
    # If a client comes to ask for the cloud, it doesn't really matter which
    # copy of the cloud

    # ---When we go ask the remote, "Hey is this client supposed to be here?"
    # We'll provide a list of our hosts that have the cloud, then the remote
    # will respond with which one it is, which we'll store here.
    # host_id_from_remote = Column(db.Integer)---
    # nope we have a cloud object that will know what it's host_id is
    created_on = Column(DateTime)
    last_refresh = Column(DateTime)

    user_id = Column(Integer)

    # def __init__(self, uuid, user_id):
    def __init__(self):
        now = datetime.utcnow()
        self.created_on = now
        self.last_refresh = now
        # self.uuid = uuid
        # self.user_id = user_id

    def has_timed_out(self):
        delta = datetime.utcnow() - self.last_refresh
        return (delta.total_seconds()/60) > 30
        # return (delta.seconds) > 3

    def refresh(self):
        self.last_refresh = datetime.utcnow()

