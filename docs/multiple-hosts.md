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

``` python
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
``` python
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
- When we find a file change, add it to the list of changes for one tick.
- When we wake up,
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
--------------------------------------------------------------------------------------------

### Limited changes
Do we store all the changes in the DB? Storing all the changes in the DB seems like it would be insane. So what then?
Originally I think I had planned that we'd store like 256 changes per mirror, and if a host came looking for changes before that it would just force all the changes to sync.
There's a probably optimal way of culling all the changes that all the other hosts have ack'd. Though, that will also be hard.
We could probably also coalesce changes that haven't been ack'd.
But again with both of those two, if there's a host that is behaving poorly we still have to track a bunch of changes

What if we do the coalescing per-file based on when we last knew everyone ack'd? nope that's not it, because then if there's one host that's offline then we have to track every single change since that host went offline.

what if it was instead we coalesce the changes since someone went offline?

ehg thats not great. maybe we can get by with just the last update? we scan all the files for changes between the sync window? Each file only has one file change?
THat might work...

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
