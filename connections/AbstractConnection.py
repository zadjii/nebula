__author__ = 'Mike'
import abc


class AbstractConnection(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def send_obj(self, message_obj):
        """
        Serializes the provided message, and sends it along the connection.
        """
        return

    @abc.abstractmethod
    def recv_obj(self):
        """
        Retrieves a serialized object from whatever the input stream is, and
        converts it to a Message object. If there is any file data coming with
        the message, this will need to retrieve it and pack it into the message
        as well. OR provide a mechanism for reading the data piece by piece.

        I don't really know how websocket file transfer is going to work yet, so
        maybe do that FIRST
        """
        # fixme ^^^^ the part about ws:// file transfer.
        return

    @abc.abstractmethod
    def recv_next_data(self, length):
        """
        Retrieves the next data[length] from this connection.

        So, a websock will keep grabing messages until length == length
        but what if one message gets you nBytes > length??
            THEN ITS PROBABLY BAD.

        :param length: length of the data to return. Might be a little more?
        :return:
        """
        return

    @abc.abstractmethod
    def send_next_data(self, data):
        """
        Sends the specified data down the connection. It just does it.
        No regard for what the data is or how it happens.
        :param data: data to send
        :return:
        """
        return

    @abc.abstractmethod
    def close(self):
        """
        closes the connection.
        """
        return


"""
    OKAY SO HERES THE DEAL.
    Whenever we would be retrieving file data, we always go:
    "What's the message? oh cool, length of file data, lemme just
      while loop to pull the data."
    So, now its basically the same.
    We'll recv_obj -> see that there is file data coming,
      and while loop to pull it all down.
    And similar for the sending of files. Very #fuckitshipit.
"""



