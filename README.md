# nebula

Nebula is a platform for personal, private clouds. It enables users to host their own files in a "Cloud" that's running on a device they own, and enables them to access those files directly from that device, _without_ the files ever passing through a third party. This means that the users have full control over their data.

Nebula is about so much more than just plain file storage. Applications built on top of nebula can guarentee that their user's data remains private to the user. Imagine a social media site, where you can be sure that your post is only visible to you and your friends, and impossible for the site operator to scrape your data, or knowing that when you delete a post (or even all your profile information) it's really gone for good! Imagine a web email service where the contents of your email aren't scraped to better serve you advertising. This is what nebula is for.

## How it Works

Nebula is a system mainly comprised of three parts: the Remote, the Host, and the Client.

The Remote is the service running at a well known location responsible for tracking clouds and orchestrating communication between them. The Remote doesn't know anything about the contents of the cloud, only where the hosts for a cloud are, when they were last updated, and is responsible for authenticating a client's access to a cloud.

The Host is the device actually hosting the cloud's files. Each host for a cloud communicates with each other via the remote, and updates each other's files in a peer-to-peer fashion, so the remote never knows the contents of the files. Because the files on a host are just plain-old files, the user can interact with them directly through any old piece of software, and nebula will automatically keep the other hosts in sync.

Clients are the applications that the users interact directly with their clouds from another computer. For example: a web-based file browser that would let a user upload files to their cloud and download them to another machine. Clients can read and write the files on a host directly, without the files ever passing through the remote, so the remote operator never knows what a user is doing to their cloud.

```
    +---------+
    |         |
    | Client  |
    |         |
    +-------^-+
           ||
XXXXXXXXXXX||XXXXXXXXXXXXXXXXXXXXXXXXXX
           ||
           ||     +---------------+
           ||     | Remote        |
           ||     | +---+         |
           ||     | |   |         |
           ||     | +---+         |
           ||     +---------------+
           ||        | |
XXXXXXXXXXX||XXXXXXXX| |XXXXXXXXXXXXXXX
           ||        | |
        +--v------+  | |   +--------+
        | Host 1  <--+ +---> Host 2 |
        |         |        |        |
        |         <-------->        |
        +---------+        +--------+

```
*fig 1: A really okay ascii diagram of the remote, client, and host relationships*



## Roadmap

Nebula as come quite a long way since work started on it in 2015, but there's still a long way to go. This gives a little bit of an outline of what's done and where we have yet to go.

- [x] **v0.1 Basic end-to-end proof of concept**
  This milestone demonstrated that syncing files from host to host, as orchestrated by a remote, without the files passing through the remote.

- [x] **v0.2 Client File Access**
  Enable users to access the files on their clouds being at the PC hosting those files. This involves, ut is not limited to:
    * Additional work to enable the nebula host to be communicated with over WebSocket
    * Work to expose nebula hosts to the internet, using upnp
    * A bunch of messages just to be able to interact with the hosts remotely

- [x] **v0.3 File Sharing, linking**
  This milestome enabled users to share files on their clouds with other users, and to be able to create static "links" on a Remote, such that a client could access a file via a link without knowing anything about the underlying structure of the coud hosting the linked file.

  As of this milestone, it's possible to write fairly feature-rich applications on top of the nebula platform, and the platform is considered "Alpha-complete"

- [ ] **v0.4 Multiple hosts per cloud**
  At the moment, each cloud can only support one host per cloud reliably. Remotes without `ENABLE_MULTIPLE_HOSTS=1` in their config will reject any attempts to create a second host. There's definitely some support there currently for replicating the files, but there's almost no support for syncing updates in the scenario where a host's network connection is dropped, the file is changed, and the host re-connects.

- [ ] **v0.5 Improved security (SSL/HTTPS)**
  If no one has told you yet, you should be using https. While it's relatively trivial to get a SSL cert for a domain you control, it's very hard to issue valid, trusted SSL certificates for arbitrary host computers.
  This is probably the biggest remaining hurdle for a proper nebula implentation. The remote needs to be able to authenticate the hosts and issue signed certs for them, in a way that will be trusted by any old browser, without any other system coniguration.

- [ ] **v0.6 Email Support**
  Running a mail server is definitely non-trivial

- [ ] **v0.7 Application Isolation**
  Right now, once you've logged in to a lient application, it has free reign to do whatever it wants to your cloud, including reading and writing all over the entire tree. This is obviously *not ideal*. Applications need to have permissions only over a subset of the tree, and granting an application access needs to be an explicit action by the user.

After this point, the platform will be "Beta-Complete", and hopefully should only require minor bugfixes to be "feature-complete" - though I'm sure there's a long list of features I'd love to continue to add.

## Contributing

As you can see, there's still a lot left to do! If your interested in helping contribute, feel free to fork the repo and have at it! There are plenty of issues that are open, as well as numerous undocumented TODOs in the code itself.

You can also take a look at the `CONTRIBUTING.md` file in the root of the project for some notes on how the project works.

