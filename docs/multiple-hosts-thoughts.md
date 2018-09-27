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

```python
class FileChange(host_db.Model):
    origin_timestamp: datetime
    relative_path: str
    change_type: {create, update, delete, move}
    is_dir: bool
    target_path: str # moves only?
    origin_host_id: int
    mirror_id = host_db.ForeignKey('mirror.id')
```
Do we want a relationship to the FileNode too? How does hat work with moves, deletes?
```python
class FileChangeSchema(marsh.ModelSchema):
    class Meta:
        # Fields to expose
        additional = ('origin_timestamp', 'relative_path', 'change_type', 'is_dir', 'target_path', 'origin_host_id')
    def prototype(self):
        # type: () -> str
        empty_dict = dict.fromkeys(['origin_timestamp', 'relative_path', 'change_type', 'is_dir', 'target_path', 'origin_host_id'])
        return self.dumps(empty_dict).data
```


How do we decide which  host is actually available? When one host notices a change, and a client tries to access another host for that file, that client _wont_ be able to know that file is out of date.
Similarly, if the client writes the file right after another host has changed the file
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

### File Change Proposal Algorithm With the Remote
- [HOST] When we find a file change, add it to the list of changes <!-- for one tick. --> to be sync'd.
- [HOST] When we wake up,
    - [HOST] Handshake the remote "<!-- I last handshook you at --> My last update timestamp was t_0, I have updates t_2" `HostHandshake(t_0, t_2, ...)`
        - [REMOTE] We recieve the HostHandshake.
          Their last_sync was t_0.
          Their last_update was t_2.
          The cloud's last_update is t_1.

        - [REMOTE] if t_0 is less than the current last_update(t_1) for that cloud,
          then the host is out of date and needs to get updates.
            - [REMOTE] If t_2 is greater than the cloud's last_update timestamp (t_1), the host has new files for the
              cloud, but it's still out of date (it last synced at t_0 < t_1).
              *todo:The host will send these changes later?*
            - [REMOTE] The remote will reply with a list of hosts that the host can go ask for updates from.
              `RemoteHostHandshake(t_0, t_1, [hosts])`

                - [HOST] we (H_a) will then attempt to get the changes from each other host(H_i). `FileSyncRequest(t_0, t_1)`
                    - [HOST] If H_i has any changes in that timeframe, (it should), it will send FileChangeProposals for each of them.
                    - [HOST] We will accept, reject or acknowledge each of these
                        - If we accept (its a newer version of our file, or a file we didn't modify), we'll recv the file's contents
                        - if we reject, it's because our local unsync'd changes (t_2, f_n, any) haven't been sent yet. We'll send the update later.
                        - if we ack, then we were in a weird state. Possibly we have a change at the exact same time as the other? **TODO**
                            - This does seem improbable, but not impossible. I'd think that as a policy, in the case of an ack, we'd instead accespt the other host's change. The other host is more up-to-date with the remote, so it's possible there are other hosts that also have H_i's state.

                - [HOST] We'll keep looking for FileChangeProposal's until we read a FileSyncComplete.
                - [HOST] Only once we read a FileSyncComplete are we done. If the connection is broken before we see that, then we'll move on to the next host.
                - [HOST] Once we're done, we'll update our last handshake time to t_1.
                - [HOST] We'll send another HostHandshake(t_1, t_2). We basically repeat this loop until the remote returns <!-- *todo: what? until the remote returns...?* -->

        - [REMOTE] ELSE if t_0 is the current update (t_1), (the host was up-to-date)
            - If (t_2 > t_1) then then this host is now the only active host, and mark the others as out of date.
            - if (t_2 == t_1), then great, that's perfectly fine
            - else (t_2 < t_1) ->
              <!-- That's probably an error. How does the host think that the last change it has is older than the last update time? Log error, mark inactive, `RemoteHostHandshake(t_2, t_1, hosts)`. -->
              In this case, the host has an update from while it was offline, before one of changes that an online host made.
              That technically means that this host is the only one that's up-to-date, because now it has the updates from other hosts. HOWEVER when they handshake, they'll find that their last update (t_2) is newer than the t_1 they don't have. Hmm.
              The host will later in the loop send it's updates from t_1. When that happens, the other hosts will accept our changes, BUT ONLY AFTER THEYVE ALREADY HANDSHOOK THE REMOTE AGAIN. Uhg. thats bad. *TODO* and then they'll

        - [REMOTE] ELSE (t_0 is greater the current update), *TODO*: what do?
            - Log an error in the remote, DEFINITELY reject the host's message because that's wrong.
    <!-- - [HOST] Take each of those changes and add it to the database. -->
    <!-- Here, the remote either told the host it was up to date, or it had to go get updates, and it got those updates from the hosts that had them. H_a's changes have not been sent out though. -->
    - [HOST]
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

--------------------------------------------------------------------------------------------
#### local updates
- When we find a file change, add it to the list of changes for one tick.
- when we wake up:
    - Take each of the local changes and add it to the database.
    - Generate FileChangeProposals for each of those events.
    - for each other host:
        - for each message:
            - send the message proposal
            - receive a response.
            - if accept:
                - send the file change
            - if reject:
                - Nothing? Receive the file?
            - if acknowledge:
                - Do nothing, they already have the change.

#### Network Updates

#### Remote Handshake
- Handshake the remote "I last handshook you at t_0, I have updates t_2" `HostHandshake(t_0, t_2, ...)`
    - if t_0 is less than the current last_update for that cloud, then the host is out of date and needs to get updates.
        - If t_2 is greater than the last timestamp, the host has new files for the cloud, but it's still out of date (it last synced at t_0 < t_1)
        - The remote will reply with a list of hosts that the host can go ask for updates from. `RemoteHostHandshake(t_0, t_1, [hosts])`
        - we (H_a) will then attempt to get the changes from each other host(H_i). `FileSyncRequest(t_0, t_1)`
            - If H_i has any changes in that timeframe, (it should), it will send FileChangeProposals for each of them.
            - We will accept, reject or acknowledge each of these
                - If we accept, we'll recv the file's contents
                - if we reject, it's because our local unsyync'd changes haven't been sent yet. We'll send the update later.
                - if we ack, then we were in a weird state. Possibly we have a change at the exact same time as the other? **TODO**
        - We'll keep looking for FileChangeProposal's until we read a FileSyncComplete.
        - Only once we read a FileSyncComplete are we done. If the connection is broken before we see that, then we'll move on to the next host.
        - Once we're done, we'll update our last handshake time to t_1.
        - We'll send another HostHandshake(t_1, t_2). We basically repeat this loop until the remote returns
    - if t_0 is the current update (t_1),
        - If t_2> t_1 then then this host is now the only active host, and mark the others as out of date.
        - if t_2 == t_1, then great, that's perfectly fine
        - t_2 < t_1 -> That's probably an error. How does the host think that the last change it has is older than the last update time? Log error, mark inactive, `RemoteHostHandshake(t_2, t_1, hosts)`.
    - if t_0 is greater the current update, what do? log an error in the remote, DEFINITELY reject the host's message because that's wrong.
--------------------------------------------------------------------------------

### Limited changes
Do we store all the changes in the DB? Storing all the changes in the DB seems like it would be insane. So what then?
Originally I think I had planned that we'd store like 256 changes per mirror, and if a host came looking for changes before that it would just force all the changes to sync.
There's a probably optimal way of culling all the changes that all the other hosts have ack'd. Though, that will also be hard.
We could probably also coalesce changes that haven't been ack'd.
But again with both of those two, if there's a host that is behaving poorly we still have to track a bunch of changes

What if we do the coalescing per-file based on when we last knew everyone ack'd? nope that's not it, because then if there's one host that's offline then we have to track every single change since that host went offline.

what if it was instead we coalesce the changes since someone went offline?

ehg thats not great. maybe we can get by with just the last update? we scan all the files for changes between the sync window? Each file only has one file change?
**That might work...**

<!-- 2018 Sept 18 -->
This is a conclusion I must have come to earlier, because that's very similar to how the database is already set up.
The `host.models.Cloud` tracks it's `last_update`, which is when it last sync'd? I'm not totally sure.
Why does a `remote.models.Mirror` have both a `last_update` and a `last_handshake`? `last_update` here doesn't appear to be used anywhere, so I'm going to presume that was an oversight.
`host.models.Cloud::last_update` is *never* used, so I just put it there for future use I guess.

So when a local update happens, wtachdog signals the main thread, and we check everyone for updates.
We have a last_handshake that's local to that function, that tracks when the last time we handshook the remotes was.



## To-Do
- [ ] Create a FileChange in the Host DB
- [ ] When files are changed, create FileChange's and track them in the DB
- [ ] spec messages for proposed changes
    - [ ] HostHandshake(last_handshake, current_change, ...)
    - [ ] RemoteHandshake(sync_start, sync_end, [hosts])
    - [ ] FileChangeProposal() (see above spec)
    - [ ] FileSyncRequest(sync_start, sync_end)
    - [ ] FileSyncComplete()
- [ ] msg_blueprints for messages
- [ ] rewrite host to use proposed change method
    - [ ] Add code for directtly using file change events
    - [ ] Convert those events into `FileChange`s
    - [ ] In a way that's reusable below:
        - [ ] Convert those objects into `FileChangeProposals`
        - [ ] Send them to the other hosts, and handles their response
- [ ] Update Host to be able to handle a FileChangeProposal Message
- [ ] Update the host to be able to handle a FileSyncRequest
    - [ ] Generate all the FileChangeProposals between sync_start and sync_end
    - [ ] send them to the other host, reusing the code above
- [ ] add code for moves -> this is a bigger issue
- [ ] asdf
- [ ] asdf
- [ ] asdf


### File Opening
This kinda makes it clearer why there was a "ClientFilePut" originally. The Put was just a blind write.
"Open" is a different verb from "write". We'd have to make sure we tell other hosts that we're opening the file. When other clients attempt to open the file on other hosts, they'll need to come to the host it's already open on. We'd need to handle what should happen if a host fails to communicate that the file is no longer open (what if the host goes offline?)
Additionally, what happens if a host H_a is offline while a client opens a file with hosts H_b...H_n, then H_a comes back online and C_b connects to H_a and tries to read/write the file?
Maybe FileOpens should be tracked in the DB in a similar way. When a host asks for all the updates since the time it went offline, if there are outstanding open files, then that should be included in the list of state to sync.


### Notes / stream of consciousness

#### 27 Aug 2018

It's been a long time since I worked on this at all, but I finally have some ideas for SSL so I should come back and look at this too.

I thought I remembered something about not needing FileChanges in the DB at all, but I can't find any notes about that. Did I abandon that idea, or did I just not save it?

Or did I go to try and implement it and realize why I didn't do it that way in the first place? Yea that might be what happened. The first bullet point here is Create FileChange in DB, so I probably went to go implement that and realized that I didn't need them. That a cloud is already tracking the timestamp of it's last sync'd change and the last change it's seen, so it can figure out that the set of FileChanges since the last sync are all the files that are different from the last sync to the new sync.

Though here's a question, what about deletes? If a file is deleted between the sync window, then it's can't at runtime determine that. Do we need to keep the file around in the DB until we sync to everyone that the file is deleted?
We don't even necessarily know per host if all the other hosts have sync'd or what their state is. We only know what our state is relative to the remote.

#### 17 Sept 2018

I've actually typed up most of the notes on SSL that I refer to in the above update. I wrote them down on the 26th of August in my notebook, but never got around to typing them up/formalizing them until just last week for whatever reason. I also only left the above comment in the doc on starmap.io, not in the actual repo.

I guess I need to focus on handling file deletes.
Lets run the algorithm on paper again, just to see what happens.


We could mark the filenode as deleted and give the delete a timestamp, and when we handshake the remote, at the end of the loop we could actually delete all the filenodes that were deleted.
We could even track another filenode's ID in a filenode if the file was moved. We'd have to know at the moment it happens what both paths are, but then when we create the new filenode, we could link it to the one getting deleted.

Then what happens when an offline host comes looking for updates?
Host b (H_b) goes offline at t_0.
File f_1 is deleted at t_1.
Host A (H_a) handshakes the remote with it's newest update (at t_1). The cloud's last update is t_1, and the only active host is H_a, and H_b is out of date AND offline.

// We probably need both the last handshake and the last update for the mirros independently. A mirror will mostly have a handshake that's <30s old (indicating it's online), while the last_update will be the timestamp of the last change it synced.

Host B eventually comes back on line, and it handshakes the remote.
The remote tells h_b that it's out of date, and it needs to sync with H_a.
H_b asks H_a what changes it has since t_0. It knows that it has one, since it's last update is t_1, but because it has no filenode tracking the deleted file, it can't know that (f_1, delete) is the change that H_b needs.


So we could have a last_all_sync member in the remote handshake, tracking the state of the most out-of-date mirror.
When we delete a file, we mark it deleted in the DB with the timestamp t_1, and we tell the remote.
It replies by saying that the last_all_sync was t_0.
We purge all the deleted nodes <=t_9.

That seems better...

Okay so what happens in the reverse?

H_a goes offline at t_0
H_a deletes f_1 at t_1.
H_a fails to handshake the remote, because it's offline. It keeps the FileNode for f_1, marked as deleted.
H_b handshakes the remote, it has some change (f_n, \_) at t_1.



### Scenarios

*TODO* the scenario with host_last_sync < cloud_last_sync < host_last_update

a host_a updated a file offline, and another host_b updated a file online.
host_b is up-to-date.
host_a comes online, get's host_b's update, now host_b is out-of-date, however, it doesn't know that.

Do we need to track a FileNode's last_sync too? So when host_a comes online at t_3, the new last_update for the cloud is t_3, and host_a's pending changes are all sync'd at t_3.
then when h_b handshakes the remote, it sees that it's out of date (it's last_update was t_2, the current is t_3).
h_b asks h_a for all the updates between t_2 and t_3.
H_a knows that it's modified file was sync'd at t_3 (despite a change at t_1)

That might need to be the case. The algorithm outline should be updated to reflect this. *TODO*



#### Scenario 1
```
t_0: H_a goes offline
t_1: H_a has (f_0, del)
t_2: H_b has (f_1, _)
t_3: H_c has (f_2, _)
t_4: H_a comes online
```

#### Scenario 2
```
t_0: H_a goes offline
t_1: H_a has (f_0, del)
t_2: H_b has (f_1, _)
t_3: H_c has (f_1, _)
t_4: H_a comes online
```

#### Scenario 3
```
t_0: H_a goes offline
t_1: H_a has (f_0, del)
t_2: H_b has (f_1, del)
t_3: H_c has (f_1, mod)
t_4: H_a comes online
```

#### Scenario 4
*todo* Is there any way that two hosts culd nearly simultaneously change, and then both would get marked invalid, and then never be able to come back online, because none of the hosts would be up-to-date anymore?

### File Change Proposal Algorithm With the Remote and sync Timestamps
*TODO* whats the signature of the remote handshake?
We have a few uses for it:
- To tell a host that it's out of date and it needs to get updates in the range
  (t_0, t_1] from a set of hosts
- To tell a host that it's up to date, and doesnt need to do anything.
- To tell the host that it's up to date, and it needs to send updates to others
- To tell a host that it's up to date, and it should change it's sync timestamp
  from t_2 (s.t. t_2&lt;t_1 ) to t_3, and tell other hosts about the change.

So we definitely need a `hosts:[Host]` member.
How can the host use `last_sync` and `new_sync` to know that it's out of date? I don't think it can.
So the `RemoteHandshake` needs 3 parts:
* last_sync:
* new_sync:
* sync_end:

if (sync_end is not None):
    the host needs to get updates between last_sync and sync_end.
else:
    the host is up to date.
    If it has updates, use new_sync as their sync timestamp.
    set our last_sync to new_sync.

again, but wth 2 values:
last_sync, new_sync
if response.last_sync > request.last_update,
    then we need to sync from last_update to last_sync.
else (response.last_sync == request.last_update),
    we should use new_sync(==resp.last_sync, >=req.last_update) as the sync timestamp for our outstanding changes.
That's not right...

Is response.last_sync useful at all? I don't think so. It's always t_0, the value we sent as our last sync time.
The only thing that's different is the other value is either t_1!=t_0, indicating that we need to sync those updates, or we get t_3?=t_2. Unfortunately, t_3 will always be >t_1, and t_1 will always be >=t_0, so I don't think we can identify just from one value and our request what the response time means.

Thak means the signature is
  `RemoteHandshake(sync_end=None, new_sync=None, hosts=None)`
With only one of the two timestamps being set.

- [H] Watchdog finds a change, add it to our runtime list of changes to be sync'd.
  *TODO*: what happens if we're shutdown with unsync'd changes?
  Especially if we're offline - we'll have a buildup of changes that weren't syncd to the other hosts. We should be able to recreate that state
  See: Algorithm for determining unsynced modifications
- [H] When we wake up,
    - [H] Handshake the remote `HostHandshake(last_update=t_0, last_updates=t_2)`

        - [R] Recieve a HostHandshake.
          Their last_sync was t_0.
          Their last_update was t_2.
          The cloud's last_update is t_1.
          The current time is t_3

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
                            - [H] *todo* finish writing up how H handles the proposal
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
                  Reply `RemoteHandshake(new_sync=t_2, hosts=[hosts])`
            - [R] `elif (t_2 == t_1):`
                - [R] This is fine. Their last update was at the last sync time.
                  <!-- recall that here t_0==t_1==t_2 -->
                  <!-- reply `RemoteHandshake(last_sync=t_1, new_sync=t_2)` -->
                  reply `RemoteHandshake(new_sync=t_2)`
            - [R] `elif (t_2 < t_1):`
                - [R] This host has updates from before our current latest sync,
                  but we're tracking them with a new sync timestamp, t_3.
                  Mark the others as out-of-date.
                  Set the clouds last_update to t_3.
                  <!-- Reply `RemoteHandshake(last_sync=t_1, new_sync=t_3, hosts=[hosts])` -->
                  Reply `RemoteHandshake(new_sync=t_3, hosts=[hosts])`


        - [R] `elif (t_0 > t_1):` Their last_sync is after the cloud's last_sync
            - [R] This is definitely an error. The host can't have possibly synced at a later time than what we have. Log an error, and reply with an error message.
            - *TODO*: How should the host respond to this? Take itself offline? Or is there a way to try and right itself?

    - [H] At this point, we've recieved a `RemoteHandshake` indicating that we're up to date
      (without a `sync_end` value, and with a `new_sync` value).
      the value of last_sync is t_1, the last time we sync'd the remote.
      (This value is from our latest request to the remote)
      the value of new_sync is t_2 or t_3. (This value is >=last_sync)

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
    - [H] Do network updates
      This includes replying to new FileChangeProposals.


### Algorithm for determining unsynced modifications

any files that have a modification after their last sync timestamp

okay that's not much of an algorithim but that's it.
