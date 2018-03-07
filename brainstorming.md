# Brainstorming

A file to keep assorted ideas as I work on development.


## Remote disconnecting
If for any reason the host gets disconnnected from the network, it won't be able
  to communicate with the remote. We might not know that such a disconnect has
  happened until we actually try the handshake (eg, the host might have been
  able to get a legit IP, but the remote connection failed.)
Couple possible things:
 * retry remote handshaking
   - This is easy, just retry the connection a few times. Might have failed once
 * graceful network disconnecting
   - This could be a mode entered for any number of reasons.
   - We should continue checking for updates, but don't send them out
   - ?? We should process external connections?? If we get one, then we're back online?
   - We should continue checking the network every 30 seconds until reconnect
