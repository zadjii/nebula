## Milestone 0.4: Multiple Hosts Support

I'm trying to transcribe some notes here from pg 28 of the big blue notebook. That page is a mess, but has some great points.

When a change is detected locally, the host should first propose the change to all the other active hosts:
They can then respond with one of three messages:
* **Accept** the change: The source should now send the file
* **Reject** the change: The target has a newer change than the one being proposed.
    * The target is either in the process of sending a FileChangeProposal with their state, or will be soon. The source's file is invalid until they get that update.
* **Acknowledge** the change: the target already has that state, so we can ignore this message.

- What happens when we add support for writing changes piece-wise? What happens if two hosts have both written conflicting sections of a file?
    - We should probably just reject the old change, and then respond with the union of the two ranges of the file that were modified, but in the state they are in the new file
    - eg, Host A changes `f[1000:2000]`, and Host B changes `f[1500:2500]`.
    - Host B rejects Host A's update, then replies with a change `f[1000:2500]`
    - I REALLY don't know if this would work, but it seems sensible. Good thing we won't need to worry about that for a while.


*TODO* How do we decide which host is actually available?
When one host notices a change, and a client tries to access another host for
  that file, that client _wont_ be able to know that file is out of date.
Similarly, if the client writes the file right after another host has changed the file

This seems like a pretty blocking issue. If clients don't have to check with the remote for basically EVERY read that they do.
<!-- We'd need to make sure that getting updates from other hosts is a higher priority than client updates? -->

```
Easy Case:
C->H_a: write(f, t_0)
H_b->H_a: update(f, t_1)
Host A accepts H_b's update of f
Client now doesn't know that it's update was overwritten.
```
```
Hard case: H_b has a change before C, but due to network lag, the message is recieved after C's
H_b: finds update(f, t_0)
C->H_a: write(f, t_1)
H_b->H_a: update(f, t_0)
Host A rejects H_b's update of f, after having already accepted the client's write.
The client's write succeeds
```
```
Hard case: C has a change before H_b, but due to network lag, the message is recieved after H_b's
C: write(f, t_0)
H_b: finds update(f, t_1)
H_b->H_a: update(f, t_1)
C->H_a: write(f, t_0)
Host A accepts H_b's update of f
The client's write fails, as it's put is older than the file's current state
```

Maybe the only definitive way to handle this is with file opening.


### File Change Proposal Algorithm
- When we find a file change, add it to the list of changes for one tick.
- When we wake up,
    - Take each of those changes and add it to the database.
    - Generate FileChangeProposals for each of those events.
    - for each host:
        - for each message:
            - send the message proposal
            - receive a response.
            - if accept:
                - send the file change
            - if reject:
                - Nothing? Receive the file?
            - if acknowledge:
                - Do nothing, they already have the change.
    - Do the network updates.

### Remote Handshaking
Where do we handshake the remote with is our new timestamp? Maybe twice? once before we send our updates, and once after the network updates?

Originally the handshake was supposed to tell us if we were behind, and then we were supposed to get a list of hosts to ask for updates.

### Resuming from being offline
When the device wakes back up, it might have just missed some connections from other hosts. When it handshakes the remote, it's going to be told that it's out of date and it needs to ask other hosts for changes.
BUT ALSO
it might have newer local changes that it needs to sync up too! It'll need to be able to say "I think my last handshake was t_0, and I have updates at t_2", and the remote needs to respond "Go get updates up until t_1, these hosts have what you're looking for".
The out of date host H_a will then go to the hosts and ask for changes to help get it up to date. FlieSyncRequest(timestamp=t_1), and the other host will respond with a FileChangeProposal.
After it's done syncing all those changes (the ones on other hosts since t_0, up until t_1), we'll handshake the remote again, now saying that "I last handshaked at t_1, and I have updates at t_2". The remote will accept this and have no further changes. The remote will mark H_a as the active host and all the other ones as out-of-date
then we'll generate our own file change proposals and send them out normally.


--------------------------------------------------------------------------------
### File Change Proposal Algorithm With the Remote and sync Timestamps


- [H] Watchdog finds a change,
  Mark the file as modified. It's last_modified > last_sync.
add it to our runtime list of changes to be sync'd.
  *TODO*: what happens if we're shutdown with unsync'd changes?
  Especially if we're offline - we'll have a buildup of changes that weren't syncd to the other hosts. We should be able to recreate that state
  See: Algorithm for determining unsynced modifications
- [H] When we wake up,
  Determine if we have any changes:
  `changes = [f for f in mirror.files if f.last_modified>f.last_sync]`.
  If we do, then out last_updates is the greatest of those last_modified timestamps.

    - [H] Handshake the remote `HostHandshake(last_update=t_0, last_updates=t_2)`
        - [R] Recieve a HostHandshake.
          Their last_sync was t_0.
          Their last_update was t_2.
          The cloud's last_update is t_1.
          The current time is t_3.
          The mirror for this cloud with the oldest last_sync is t_4.

        - [R] `if (t_0 < t_1):` Their last_sync was before the last_update for
          the cloud. They are out of date and need to sync updates.
            - [R] Reply to the host with a list of hosts it can sync with
              <!-- `RemoteHandshake(last_sync=t_0, sync_end=t_1, hosts=[hosts])` -->
              `RemoteHandshake(sync_end=t_1, hosts=[hosts])`
                - [H] Using my last_sync time (t_0), and the remote's response
                  (sync_end(=t_1) is not None),
                  I can determine that I need updates from t_0 and t_1 from
                  `[hosts]`.
                - [H] Iterate over the hosts until we find a `FileSyncComplete` message.
                    - [H] send the host H_i a `FileSyncRequest(t_0, t_1)`
                        - [H_i] If we have files whose last_sync timestamp is in t:(t_0, t_1], send it to the requestor as a `FileChangeProposal`
                            - [HOST] We will accept, reject or acknowledge each,
                              based on the last_sync of the file
                                - if we reject,
                                  `(file.last_sync <= proposed.last_sync && proposed.last_sync < file.last_modified)`
                                  it's because our local unsync'd changes (t_2, f_n, any) haven't been sent yet.
                                  The file was modified since it's last sync, and our change timestamp is newer than the proposed sync timestamp.
                                  We'll send the update later.
                                - If we accept
                                  `(file.last_sync < proposed.last_sync)`
                                  (its a newer version of our file, or a file we didn't modify),
                                    - We'll recv the file's contents.
                                - if we ack,
                                  `(file.last_sync == proposed.last_sync)`
                                  We have whatever change they're talking about. ACK.
                                  <!-- Actually maybe not that weird of a state.
                                  We could have gotten that file from another host earlier in the syncing process.
                                  We'll need to compare the sync timestamps. If the file's last_sync is less than the
                                  Possibly we have a change at the exact same time as the other? **TODO**
                                    - This does seem improbable, but not impossible. I'd think that as a policy, in the case of an ack, we'd instead accespt the other host's change. The other host is more up-to-date with the remote, so it's possible there are other hosts that also have H_i's state. -->
                                - if weird case: `(file.last_sync > proposed.last_sync)`:
                                  Reject. Our version is newer than the other's.
                                  The other should know that... *TODO?*


                        - [H_i] If we have no changes, or we've sent all the changes we had, finish the connection by sending a `FileSyncComplete` message.
                    - [H] If the connection has broken before we recieve a
                      `FileSyncComplete`, we try again with the next host.
                    - [H] If we iterate over all the hosts, and don't recieve a
                      FileSyncComplete message, *TODO* what should we do? Just
                      try our original remote handshake again?
                - [H] We completed syncing files between t_0 and t_1 from the
                  other hosts.
                  Our new last_handshake is t_1.
                - [H] Send a new `HostHandshake(last_update=t_1, last_updates=t_2)`.

        - [R] `elif (t_0 == t_1):` Their last_sync is the cloud's last_sync.
          (The host's response to these messages is detailed below.)
            - [R] `if (t_2 > t_1):`
                - [R] This host has a new update.
                  Mark the others as out-of-date.
                  Set the clouds last_update to t_2.
                  <!-- Reply `RemoteHandshake(last_sync=t_1, new_sync=t_2, hosts=[hosts])` -->
                  Reply `RemoteHandshake(new_sync=t_2, last_all_sync=t4, hosts=[hosts])`
            - [R] `elif (t_2 == t_1):`
                - [R] This is fine. Their last update was at the last sync time.
                  <!-- recall that here t_0==t_1==t_2 -->
                  <!-- reply `RemoteHandshake(last_sync=t_1, new_sync=t_2)` -->
                  reply `RemoteHandshake(new_sync=t_2, last_all_sync=t4)`
            - [R] `elif (t_2 < t_1):`
                - [R] This host has updates from before our current latest sync,
                  but we're tracking them with a new sync timestamp, t_3.
                  Mark the others as out-of-date.
                  Set the clouds last_update to t_3.
                  <!-- Reply `RemoteHandshake(last_sync=t_1, new_sync=t_3, hosts=[hosts])` -->
                  Reply `RemoteHandshake(new_sync=t_3, last_all_sync=t4, hosts=[hosts])`


        - [R] `elif (t_0 > t_1):` Their last_sync is after the cloud's last_sync
            - [R] This is definitely an error. The host can't have possibly synced at a later time than what we have. Log an error, and reply with an error message.
            - *TODO*: How should the host respond to this? Take itself offline? Or is there a way to try and right itself?

    - [H] At this point, we've recieved a `RemoteHandshake` indicating that we're up to date
      (without a `sync_end` value, and with a `new_sync` value).
      the value of last_sync is t_1, the last time we sync'd the remote.
      (This value is from our latest request to the remote)
      the value of new_sync is t_2 or t_3. (This value is >=last_sync)
      the value of last_all_sync is t_4. (This value is >=last_sync)

    - [H] The remote has assigned these updates a sync timestanp t_3 (>= t_2).
      It also gives us a list of hosts that need to be updated with our change at t_3.

    - [H] for each other host:
        - [H] For each of our pending changes `[{update:t_i, sync:t_3,...}, ]`,
            - [H] Generate and send a `FileChangeProposal`
            - [H] Recieve a response (`FileSyncResponse`).
            - [H] if (accept)
                - [H] Send the file data.
            - [H] if (reject)
                - [H] *TODO* Nothing? do we instead recieve the other hosts view of the file?
            - [H] if (acknowledge)
                - [H] Nothing, they already have this change.

    - [H] We can prune any deleted or moved nodes that were deleted before `last_all_sync` now.

    - [H] Do network updates
      This includes replying to new `FileChangeProposals`.
--------------------------------------------------------------------------------

This algorithm supposes that local updates are handled before the network updates, however, the host currently operates in the reverse order. Is there a compelling reason for one over the other?

```
- remote handshake
- while(!exit)
    - handshake the remote
    - network updates
    - local updates
```
This one is wrong. If the local updates finds something, then we don't handshake the remote with the update until we come back thrugh again.

```
network
local
handshake
```
This might be right
If we're offline, then network won't have any updates, and remote handshake will do nothing.
If someone sends us an update to a file we have a newer change for, then unfortunately we'll accept their change and overwrite the local changes. So thi si wrong too

```
local
network
handshake
```
If we're offline, we won't be able to send any local updates.
If we're online, and another host has proposed a older file change to a file we've locally updated, then we'll reject it.
In fact, we'll probably have already proposed the change to them.
Any changes that get rejected will be received in the network portion
If we were offline last time through the loop, then there aren't going to be new network updates
if we were offline but now we're online, we'll have updated the local changes, then we'll tell the remote that we were last online and we're now online

### RemoteHandshake signature

Thak means the signature is
  `RemoteHandshake(sync_end=None, new_sync=None, hosts=None)`
With only one of the two of `sync_end` or `new_sync` timestamps being set.
`hosts` is a list of hosts to sync with or from
`last_all_sync` is the oldest of all the mirrors' last_sync's.


--------------------------------------------------------------------------------------------


## To-Do
- [ ] Add a last_sync to the `FileNode`s in a cloud
- [ ] Add fields to `FileNode` to be able to
    - [ ] mark as deleted
    - [ ] mark as moved
- [ ] Add a last_sync to the host.models.Mirror
- [ ] Add a last_sync to the remote.models.Cloud
- [ ] Spec messages
    - [ ] `HostHandshakeMessage`
    - [ ] `RemoteHandshakeMessage`
    - [ ] `FileSyncRequest`
    - [ ] `FileSyncProposal`
    - [ ] `FileSyncComplete`
- [ ] msg_blueprints for messages
- [ ] watchdog makes modifications straight to db, then notifies main thread
    - [ ] Adds files to db when created
    - [ ] Marks files as modified when they change
    - [ ] Marks files as deleted when they are deleted
    - [ ] Creates a new filenode, and marks the old one moved when a file is moved.
- [ ] Host deletes filenodes that have been deleted before last_all_handshake
- [ ] rewrite host to use proposed change method
    - [ ] calculate pending changes from the files with modifications since our last sync.
    - [ ] In a way that's reusable below:
        - [ ] Convert those objects into `FileChangeProposals`
        - [ ] Send them to the other hosts, and handles their response
- [ ] Add support to remote to handle `HostHandshake`s according to the above algorithm.
    - [ ] Remote can tell the host to get updates from others
    - [ ] Remote can tell the host it's up to data
    - [ ] Remote can tell the host it's up to data and should send updates
    - [ ] Remote can tell the host when others last_sync'd
- [ ] Update Host to be able to handle a `FileChangeProposal` Message
- [ ] Update the host to be able to handle a `FileSyncRequest`
    - [ ] Generate all the `FileChangeProposals` between sync_start and sync_end
    - [ ] send them to the other host, reusing the code above
- [ ]

### File Opening
This kinda makes it clearer why there was a "ClientFilePut" originally. The Put was just a blind write.
"Open" is a different verb from "write". We'd have to make sure we tell other hosts that we're opening the file. When other clients attempt to open the file on other hosts, they'll need to come to the host it's already open on. We'd need to handle what should happen if a host fails to communicate that the file is no longer open (what if the host goes offline?)
Additionally, what happens if a host H_a is offline while a client opens a file with hosts H_b...H_n, then H_a comes back online and C_b connects to H_a and tries to read/write the file?
Maybe FileOpens should be tracked in the DB in a similar way. When a host asks for all the updates since the time it went offline, if there are outstanding open files, then that should be included in the list of state to sync.


### Deleting files

We could mark the filenode as deleted and give the delete a timestamp, and when
  we handshake the remote, at the end of the loop we could actually delete all
  the filenodes that were deleted.
We could even track another filenode's ID in a filenode if the file was moved.
  We'd have to know at the moment it happens what both paths are, but then when
  we create the new filenode, we could link it to the one getting deleted.

This actually won't work all by itself.
We need to have a `last_all_sync` member in the `RemoteHandshake`, tracking the
  state of the most out-of-date mirror. When we delete a file, we mark it
  deleted in the DB with the timestamp t_1. We'll handshake the remote, it'll
  assign our chnge a timestamp t_2(>=t_1), and it will tell us that all the
  other hosts were up to date as of t_0.
We purge all the deleted nodes <=t_0.

