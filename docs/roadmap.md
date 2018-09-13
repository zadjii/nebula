# Roadmap

Nebula as come quite a long way since work started on it in 2015, but there's still a long way to go. This gives a little bit of an outline of what's done and where we have yet to go.

## Alpha Roadmap

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
  See [multiple-hosts.md](./multiple-hosts.md) for colleted thoughts on implementation.

- [ ] **v0.5 Improved security (SSL/HTTPS)**
  If no one has told you yet, you should be using https. While it's relatively trivial to get a SSL cert for a domain you control, it's very hard to issue valid, trusted SSL certificates for arbitrary host computers.
  This is probably the biggest remaining hurdle for a proper nebula implentation. The remote needs to be able to authenticate the hosts and issue signed certs for them, in a way that will be trusted by any old browser, without any other system coniguration.
  See [https-thoughts.md](./https-thoughts.md) for colleted thoughts on implementation.

- [ ] **v0.6 Email Support**
  Running a mail server is definitely non-trivial, but I think it would be an absolutely perfect application of the technology. Imagine, all of the benefits of a webmail client, all while you know that your emails are safe on a device you control, and not subject to the operator being able to scan their contents.

- [ ] **v0.7 Application Isolation**
  Right now, once you've logged in to a lient application, it has free reign to do whatever it wants to your cloud, including reading and writing all over the entire tree. This is obviously *not ideal*. Applications need to have permissions only over a subset of the tree, and granting an application access needs to be an explicit action by the user.

After this point, the platform will be "Beta-Complete", and hopefully should only require minor bugfixes to be "feature-complete" - though I'm sure there's a long list of features I'd love to continue to add.

## Post-Alpha Roadmap

- [ ] **v1.1 Simple Cloud Gets**
  There's no way to get all the files from a cloud without creating a mirror of the cloud, which would sync your copy of the cloud with other hosts. This milestone will enable users to get the files on a cloud without creating mirrors.

- [ ] **v1.2 Partial Mirrors**
  Currently a mirror is all-or-nothing - you need to copy the entire cloud to your device to get at any of the files. One might imagine however, only wanting a particular subdirectory copied to the device, ex a `music/` directory filled with audio tracks. This milestone whould enable users (and applications) to create partial mirrors of a cloud

- [ ] **v1.3 Pure HTTP access**
  Enable client applications to use HTTP verbs to access and manipulate data on the cloud. Imagine a web application being able to issue a `GET https://<cloud_url>/zadjii/home/hello_world.txt` and retrieve the file `hello_world.txt` from the cloud `zadjii/home`. This would greatly simplify a lot of web applications, allowing them to issue HTTP requests instead of using the websocket API.
