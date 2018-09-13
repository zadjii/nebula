# nebula

Nebula is a platform for personal, private clouds. It enables users to host their own files in a "Cloud" that's running on a device they own, and enables them to access those files directly from that device, _without_ the files ever passing through a third party. This means that the users have full control over their data.

Nebula is about so much more than just plain file storage. Applications built on top of nebula can guarentee that their user's data remains private to the user. Imagine a social media site, where you can be sure that your post is only visible to you and your friends, and impossible for the site operator to scrape your data, or knowing that when you delete a post (or even all your profile information) it's really gone for good! Imagine a web email service where the contents of your email aren't scraped to better serve you advertising. This is what nebula is for.

## Installing

At the moment there aren't any pip packages yet, so you'll have to clone the repo and install the dependencies manually with

```sh
git clone https://github.com/zadjii/nebula
cd zadjii/nebula
pip install -r requirements.txt
```

See `CONTRIBUTING.md` for more specifics on installing.

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

See [roadmap.md](docs/roadmap.md)

## Contributing

As you can see, there's still a lot left to do! If your interested in helping contribute, feel free to fork the repo and have at it! There are plenty of issues that are open, as well as numerous undocumented TODOs in the code itself.

You can also take a look at the `CONTRIBUTING.md` file in the root of the project for some notes on how the project works.

