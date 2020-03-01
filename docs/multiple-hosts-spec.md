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
  If we do, then our last_updates is the greatest of those last_modified timestamps (`t_2`).
  If we don't have any changes, we're still going to handshake the remote. It's possible it's been 30s since our last handshake.
  In this case, new_updates will be None.
  If we haven't ever synced, then last_sync will be None.

    - [H] Handshake the remote `HostHandshake(last_sync=t_0, new_updates=t_2)`
        - [R] Recieve a HostHandshake.
          Their last_sync was t_0. (possibly None)
          Their last_update was t_2. (possibly None)
          The cloud's last_update is t_1.
          The current time is t_3.
          The mirror for this cloud with the oldest last_sync is t_4.

        - [R] `if (t_0 is None or t_0 < t_1):` Their last_sync was before the last_update for
          the cloud. They are out of date and need to sync updates.
            - [R] Reply to the host with a list of hosts it can sync with
              `RemoteHandshake(sync_end=t_1, hosts=[hosts])`
                - [H] Using my last_sync time (t_0), and the remote's response
                  (sync_end(=t_1) is not None),
                  I can determine that I need updates from t_0 and t_1 from
                  `[hosts]`.
                - [H] Iterate over the hosts until we find a `FileSyncComplete` message.
                    - [H] send the host `H_i` a `FileSyncRequest(t_0, t_1)`
                        - [`H_i`] If we have files whose last_sync timestamp is in t:(t_0, t_1], send it to the requestor as a `FileChangeProposal`
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
            - [R] `if (t_2 is None or t_2 == t_1):`
                - [R] This is fine. Their last update was at the last sync time,
                  or they have no updates.
                  reply `RemoteHandshake(new_sync=t_2, last_all_sync=t_4)`
            - [R] `elif (t_2 > t_1):`
                - [R] This host has a new update.
                  Mark the others as out-of-date.
                  Set the cloud's last_update to t_2.
                  Reply `RemoteHandshake(new_sync=t_2, last_all_sync=t_4, hosts=[hosts])`
            - [R] `elif (t_2 < t_1):`
                - [R] This host has updates from before our current latest sync,
                  but we're tracking them with a new sync timestamp, t_3.
                  Mark the others as out-of-date.
                  Set the clouds last_update to t_3.
                  Reply `RemoteHandshake(new_sync=t_3, last_all_sync=t_4, hosts=[hosts])`

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
    - [H] The remote _did not_ give us info on other hosts to update.
          It's their responsibility to ask us for updates.

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

<!-- zadjii, 29 Jan, 2019 -->
Do we want to have a handshake step separately at all?
Let's examine the following:
```
local
network
```
What happens here:
A.1. The thread wakes up due to watchdog signalling it
A.2. We query the DB, and find that a node has changed.
A.3. We send a HostHandshake to the remote, and the remote replies with a list of hosts to update
A.4. we send the file to other hosts to update
A.5. we're now sync'd up with last sync
A.6. we prune any nodes deleted after the last_all_sync
A.7. we deque any network messages that have arrived

Or:
B.1 The thread wakes up because it's been 30s
B.2 We query the db, find no changes
(B.2.5 Another host handshakes the remote with an update, is given a list of
    hosts to sync with, and proposes it's change to them. In that list is the
    host from steps 1&2, because it's not offline, it's just hanging out waiting for a change.)
B.3 We send a HostHandshake to the remote, the remote tells us that we're out of date
B.4 we ask a host from the remote for the updates we missed
<-- we're deadlocked here:
    * The other host is currently locked trying to send updates in response to their remoteHandshake.
    * Because they're locked, then they won't ever be able to deque the message from us asking for updates.
B.5 they tell us, we update our db
B.6 we handshake the remote, they tell us we're synced up
B.7 we deque any network connections
B.8 we find the file sync request correlated to the change we just got from another host before
B.9 we ack it

So looking at case B, we should remove the FileSyncRequest? Or the FileChangeProposal?
- FileSyncRequest is needed for a newly online host to find out what it's missed
  - If we removed it, then when hosts come online, they wouldn't be able to get any updates.
  - Hosts that had changes they missed already sent the changes, and won't be sending them again.
  - WE'd need to modiy the remote to tell hosts that ARE up to date to go back and re-update a new host.
  - That's ridiculous.
- FileChangeProposal is how one host updates the others. If we removed it:
  - Without it, then hosts are not responsible for updating the others only telling the remote that they have something new.
  - we lean on FileSyncRequest heavily, with each host waking up, finding out it's out of date, then asking the other host for whatever updates it needs to get, BEFORE they can send any other updates
  - If two hosts have contemporaneous updates:
    - Clouds original last sync is t_0
    - A tells the remote it has an update u_0 at t_2. the remote assigns u_0 a timestamp of t_2. The remote marks B out of date. A is done, and unlocks.
    - B tells the remote it has an update u_1 at t_1 < t_2. Remote tells B to sync with A.
      * (If a client tries to query for a host here, it will only get A, which doesn't have B's change yet.)
      - B queries A for changes from t_0 to t_2, A replies with u_0@t_2
      - If the files are the same, then B will reject. something would happen for moves/deletes, else B will accept.
      - B is done getting updates from others, updates it's last_sync to t_2
    - B again tries to tell the remote it has an update u_1@t_1. (the host can know this will get a new timestamp)
    The remote assigns u_1 the timestamp t_3, and marks A out of date.
  - In the above scenario, and also in probably any scenario honestly, when a client has a connection to a host, if that host ever becomes out of date, the client won't know. This isn't made worse by the lack of a FileChangeProposal

So lets do B again w/o the FileChangeProposal
C.1 The thread wakes up because it's been 30s
C.2 We query the db, find no changes
C.3 We send a HostHandshake to the remote, the remote tells us that we're out of date
C.4 we ask a host from the remote for the updates we missed
C.6 we handshake the remote, they tell us we're synced up
C.7 we deque any network connections

Seems good to me.


<!-- zadjii, 2019-02-22 -->
What if a host creates a change, then goes offline? !!!!!!!!!!
ex:
  two hosts, A and B. B is offline.
  A changes f (t_0), then goes offline.
  B comes online (t_1).
  When B asks the remote for active hosts, the only one that's up to date is A.
    However, it's offline. So either the remote will tell B to go to A, and B will fail,
    or the remote will tell B there are no online active hosts.
  No one has that change now!

This is obviously bad! B isn't up to date, but there are no other hosts.
So unfortunately, we can't really resolve this.
There are two possible solutions:
 1. We can mark B as the new active host. THIS COMES WITH CONSEQUENCES
    However, we do need to make sure that B can be marked as the new active host.
    So when B comes to handshake, and it's behind the last sync time, but there are no active hosts
    we could change the last_sync to B's.
    However, when A comes back online (t_2), it'll be very confused.
    It'll say it's last_sync is t_0, the remote will tell it to get updates from B at t_1.
    B may have no changes. It may have a change to f from t_-1, that the remote now assigned to t_1, meaning that the original change to f at t_0 is lost now.

 2. We can prevent anyone from becoming up to date until A comes back online.
    When B needs to come up-to-date, and the remote doesn't find an active up-to-date host, then B can't be marked as up to date. B can accumulate changes, but it'll never be marked as up-to-date.
    Clients will not be able to connect to B even though it's online.
    A could theoretically also be accumlating changes while offline (maybe A and B are both laptops)
    When A comes back online, it's changes will be prioritized over B's, right?
    It'll come online, say that it's last_sync was the same as the cloud's last_sync, and the remote will assign all it's new changes that handshake timestamp.
    Then, B will handshake, and find that there's an online host.
    B will ask A, and A's timestamp for those changes will be newer than B's, even if B's change happened after A's, A actually got a handshake.
    So, B's changes will be overwritten by A's
    This means data loss, and is shitty

Ideally, what do we wish would happen? If this problem was solved, what would that be like for the user?

<!-- zadjii 27-Feb-2019 -->
I've explored this case quite a bit prvately in my notes. In conclusion, one of these changes is going to get lost. Our policy in general is to keep the latest change. So, we're going to be pursuing 1, with a small modification to the algorithm. When A comes back online, A'll be told to request from B, who is the current active online host.
When A does that, B will respond by proposing a change (file, last_modified, last_sync)=(f, t_-1, t_1), which A will compare with it's view of f, (f, t_0, t_0). A's f was changed after the proposed file, so it'll reject the change. A will then need to be able to tell the remote that A needs to be made the new active host.

In this case, A handshakes:
* `HostHandshake(last_sync=t_0, new_updates=t_0)`
* `RemoteHandshake(sync_end=t_1, new_sync=t_2, mirrors=[B], last_all_sync=...)`
* A->B `FileSyncRequest()`
* B->A `FileChangeProposal()`
  - A rejects
  - A marks the t_-1 change as being syncd at t_2
* `HostHandshake(last_sync=t_0, new_updates=t_2)`

### RemoteHandshake signature

Thak means the signature is
  `RemoteHandshake(sync_end=None, new_sync=None, hosts=None)`
With only one of the two of `sync_end` or `new_sync` timestamps being set.
`hosts` is a list of hosts to sync with or from
`last_all_sync` is the oldest of all the mirrors' last_sync's.

<!-- zadjii 27-Feb-2019 -->
The signature should be
  `RemoteHandshake(sync_end=None, new_sync=None, mirrors=None, last_all_sync=None)`

* we'll stash our current `last_sync` as `initial_last_sync`

* if `sync_end` is set, then this mirror will need to go ask the `mirrors` for updates between (our `last_sync`, `sync_end`].
  - If during the course of any of the proposals, we have a newer revision to a file than the cloud version,
    we'll need to mark that file's last_sync as `new_sync`
* if `sync_end is None`, then we're the newest mirror.
  - update any files that were modified after our previous `initial_last_sync`

--------------------------------------------------------------------------------------------


## To-Do
- [x] Add a last_sync to the `FileNode`s in a cloud
- [x] Add fields to `FileNode` to be able to
    - [x] mark as deleted
    - [x] mark as moved
- [x] Add a last_sync() to the host.models.Cloud (The host mirror model)
    - [x] Does the mirror need to have a separate last_sync timestamp? or can it derive it from the latest last_sync of all it's children?
        - It can derive it I believe
    - [x]  Does the remote.Mirror AND remote.Cloud need a last_sync? or can it be figured out?
<!-- - [ ] Add a last_sync to the remote.models.Mirror -->
- [x] Rename the remote.mirror's last_update to last_sync
- [x] Add a last_sync_time() to the remote.models.Cloud
- [ ] host.models.Cloud needs a `last_modified()` function to find the newest modification to a child, or None if none have been modified after their last_sync
- [x] msg_blueprints for messages
    - [x] `HostHandshakeMessage` needs extra members, last_sync and new_updates
    - [x] `RemoteHandshakeMessage`
    - [x] `FileSyncRequest`
    - [x] `FileSyncProposal`
    - [x] `FileSyncComplete`
- [x] watchdog makes modifications straight to db, then notifies main thread
    <!-- - This actually doesn't seem right - what if the main thread
      Nevermind, the watchdog thread owns the lock when it notices a change. Disregard that. -->
    - [x] Adds files to db when created
    - [x] Marks files as modified when they change
    - [x] Marks files as deleted when they are deleted
    - [x] Creates a new filenode, and marks the old one moved when a file is moved.
- [x] Remove the code to handle a `FileChangeProposal` in filter_func. The Host should not send these - instead the host will ask other hosts if it's out of date ONLY.
- [ ] Host handshakes the remote when it notices a file change, and handles the remote handshake
    - [ ] When changes are noticed, send a handshake to the Remote
    - [ ] Add support to remote to handle `HostHandshake`s according to the above algorithm.
        - [ ] Remote can tell the host to get updates from others
        - [ ] Remote can tell the host it's up to date
        - [ ] Remote can tell the host it's up to date with a new timestamp t_3
        - [ ] Remote can tell the host when others last_sync'd
    - [ ] Host supports recieving a RemoteHandshake after a HostHandshake.
        - [ ] During a `RemoteHandshake`, Host deletes filenodes that have been deleted before `last_all_handshake`
    <!-- - [ ] rewrite host to use proposed change method -->
        <!-- - [ ] calculate pending changes from the files with modifications since our last sync. -->
        <!-- - [ ] In a way that's reusable below: -->
            <!-- - [ ] Convert those objects into `FileChangeProposals` -->
            <!-- - [ ] Send them to the other hosts, and handles their response -->
- [ ] Update the host to be able to handle a `FileSyncRequest`
    - [ ] Verify the other host with the remote
        * see `host_verify_host` in `remote/.../mirror.py`
        * see `verify_host` in `network_updates.py`
          * We need something with the same form, but more general purpose. HOST_VERIFY_HOST really should be HOST_VERIFY_HOST_FOR_FETCH, because it's used specifically when the mirror needs to verify the requesting mirror was approved to mirror the cloud.
          * Since each mirror has uniquely one cloud, we can remove the uname/cname params from host_verify_host
          * ~~~We'll need another message type, HostVerifyHostSync~~~
          * If we do this, then the remote needs another set of mappings, for hosts that have been told to sync messages from another host. Is this necessary? Or coud we just overload the existing mapping?
          * We'll need to make sure to remove these mappings when we're done mirroring and done syncing
    - [ ] Generate all the `FileChangeProposals` between sync_start and sync_end
    - [ ] send them to the other host
    - [ ] Requesting host handles FileChangeProposals
- [ ] Update Host to be able to handle a `FileChangeProposal` Message
    - [x] ack their change
    - [x] reject their change
    - [x] accept their change (`FileChangeResponse`, followed by (HOST_FILE_TRANSFER, file_data))
    - [ ] modify our DB appropriately to match their change
        * We need to make sure to update the last_sync of any new files, and that's new. Before host_file_transfer's wouldn't nclude the sync timestamp the file belonged to
            - [ ] `HOST_FILE_TRANSFER` needs to add the `last_sync` timestamp to the message, so both transfers during a sync and during the initial mirroring will update the last_sync timestamp
              * Actually though, are we even keeping `HostFileTransfer`? -> yes, that's used for actually transfering the files
        - [x] Creates
        - [x] modifies
        - [ ] deletes
        - [ ] moves

- [ ] When the Host handshakes a remote and is out of date, the host must set `FileSyncRequest`s to other hosts
    * see `host.models.Cloud.modified_between()`
- [ ] Add support for mirroring with multiple hosts
    * I might need to just run the feature test to see what breaks.
    * If the first param to `recv_file_tree` is None, then `do_recv_file_transfer` is going to return an error. With multile hosts, I believe this is a path that's actually hittable. Unfortunately, during mirroring, there won't be a HostController that's been initialized yet.
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

