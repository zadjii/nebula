# HTTPS / SSL Implementation (Milestone v0.5)

The goal here isn't to ensure security necessarily. Total security would be great, but acting as a CA and issuing certs to each host is likely infeasible, at least in the short term.

The goal of this spec is not real proper securty, but merely enabling HTTPS as a communication mechanism to the host. If you wanted to create a web frontend client for nebula, you'd probably want to serve that site using HTTPS. If you have a site that's delivered using HTTPS, then you can only connect to websockets that are served using HTTPS (`wss://`) as well. So the host needs to be able to have a valid HTTPS cert to be able to connect to it.
Not only does the cert need to be valid, but it also needs to be trusted by the browser itself, which means it can't just come from your own local CA, it needs to be signed by a proper, trusted CA. That's where things get tricky.
Now, this isn't necessarily something that needs to be enabled for all nebula instances. If someone wants to run nebula without supporting HTTPS this way, they absolutely should be able to. Nebula works just fine over plain old HTTP.

This document outlines some plans to implement optional support for HTTPS.

## Remote Keypair Provider

Remote has an `IRemoteKeypairProvider` that provides keypairs for the host.

This is a dumb solution that isn't actually secure, it's just HTTPS enough to enable wss connections to hosts. This is mostly brainstorming to support the `starmap.io` scenario of having a public web frontend to as a nebula client.

We implement a `SingularKeypairProvider` that basically gives every host the same (private key, cert) pair.
For this to work in production, that cert would need to be a wildcard cert, for a domain like `*.host.starmap.io`.
The remote is configured to use this as it's keypair provider somehow.

> **TODO**: How? Via the commandline? Via a python module passed on the commandline/via a .conf file? It'd need to be configured somehow,

I think these providers should be configured using our existing `.conf` file setup. When a host or remote is parsing the config for it's default/root settings, we should keep the config object on the instance. During the default parsing during startup (`Neb.Instance::load_conf`), we'd see if a `KEYPAIR_PROVIDER` is configured, and if it is, we'll set that up. During the provider's initialization, we'd pass the provider the config object from the instance, and it can query it's own members.

```python
class IRemoteKeypairProvider(object):
    def configure(self, config):
        pass
    def gen_keypair(self, host):
        # type: (remote.models.Host) -> (str, str)
        """
        Use host.public_address to get the public_address of the host here.
        """
        pass
```

## Host keypair Provider

Maybe the host should be responsible for generating it's private key? That's certainly one idea. I think that's how I had it originally. The host would send a public key to the host when the host moved, and the remote would then sign the public key with it's signing cert.

If the remote were configured to do this (`SigningKeypairProvider`), then the remote should reject the host's initial move request, with an error that contains it's new public address. The host should then generate the keypair, and try the move again with the publickey, and the remote would sign it and give the signed key back.

I don't believe this is necessary to implement.

## Public Address Provider

Then, we have the remote configured to add each host's IP to a DNS configuration for `.host.starmap.io`.
E.g., `A ip.host.starpam.io -> <ip>`, for each and every IP that ever registers as a host.
Presumably, we could create a DNS server that just replies with those responses for any IP, without even needing to register records manually.

In fact, having records in the DNS server for each host is probably a terrible idea. But if we needed to, here's how we could:

We'd add a `IPublicAddressProvider` that gets the public IP the remote should use for that host. By default, it's unimplemented, and the remote uses the host's IP as the public IP. But with the `DNSIpRegistrar`, then the the provider registers the IP with the DNS service and returns the full name for that IP. Alternatively, the `DnsAddressForwarder` can be configured with just a top-level domain (`.host.starmap.io`) and it'll prepend the IP to it and return that, no registration involved.
`DNSIpRegistrar` would probably be a subclass of `DnsIpProvider`, but

```python
class IPublicAddressProvider(object):
    def configure(self, config):
        pass
    def get_public_address(self, host):
        # type: (remote.models.Host) -> str
        """
        Use the host's ip (host.ip()) to generate a publicly accessible DNS name
        for the host.
        """
        pass
```

So yea we definitely want to have the `IPublicAddressProvider`, regardless if it's hooked up to DNS or not.


## Complete Host Move (no host keypair)

Host A tells the remote that it has just moved to 1.1.1.1.

The remote invokes it's `IPublicAddressProvider` (if it has one) for the host's new IP to get the public address to use for the host. It will store the public address in it's Host model.
It then checks if it has a keypair provider configured. If it does, it'll call the `IRemoteKeypairProvider` for the host, and get a keypair for the host.
The remote replies to the host move request with a `HostMoveResponse(public_address, privatekey, cert)`

The host notes it's public address.
The host looks at the values of privatekey and cert.
    If they aren't null, it uses them as it's keypair. It restarts it's network controller, with HTTPS enabled on the websocket.
    If they are null, then the remote doesn't care to have us use HTTPS, and we start normally.

## Complete Host Move (with host keypair)

(I believe this is unecessary to implement, but this is how it would work with this kind of system.)

Host A tells the remote that it has just moved to 1.1.1.1. `HostMoveRequest('1.1.1.1', None)`

The remote invokes it's `IPublicAddressProvider` (if it has one) for the host's new IP to get the public address to use for the host. It will store the public address in it's Host model.
It then checks if it has a keypair provider configured. It does, it has a `SigningKeypairProvider`. The signing keypair provider is provided the public address, and the publickey the host sent (which is None).
The `SigningKeypairProvider` rejects the empty publickey.
The Remote replies to the host with a error message indicating it should send a publickey. The error contains the public address we generated for the host.

The host gets the error message and determines it needs to generate a keypair.
The host invokes it's `IHostKeypairProvider` with the provided public_address and gets a private_key and cert signing request.
The host then attempts the move again `HostMoveRequest('1.1.1.1', csr)`

The remote sees that the host hasn't actually moved to a new address, so it skips assigning it a new public address.
It invokes it's `SigningKeypairProvider` with the public address and the CSR we got from the host, and gets a signed cert for that host.
This succeeds, and we reply to the host with a successful move response. `HostMoveResponse(public_address, None, cert)`

The host notes it's public address.
The Host stores it's private_key and the cert it got from the remote.
The host looks at the values of it's privatekey and cert. Seeing that they aren't null, it uses them as it's keypair. It restarts it's network controller, with HTTPS enabled on the websocket.


## TODO

* [ ] Update HostMoveResponse to include a `public_address` and `private_key` field.
* [ ] Add `IPublicAddressProvider` interface
* [ ] Enable remote to track public_addresses in addition to the ip, port,
      wsport, and use the `public_address` as the ip in messages locating the host.
    - by default, if the public_address is null, just use the IP.
* [ ] Add a `DefaultPublicAddressProvider` that just returns the IP.
* [ ] Hook up the remote to a `IPublicAddressProvider`, to get public addresses on host moves. Use the `DefaultPublicAddressProvider` by default.
* [ ] Hook up the host to look at the public address given to it by the remote
    - It might not actually need to do anything with that by default...
* [x] Determine how to configure the IPublicAddressProvider, such that an
      instance can pick the provider, and specify args to the provider as well.
* [ ] Add a `DnsAddressForwarder` implementation that simply adds the IP to a configurable domain
* [ ] Add a `IRemoteKeypairProvider` interface
* [ ] Hook up the remote to possibly have a keypair provider (None is valid, and default) and use the provider when a host moves.
* [ ] Hook up the host to check the returned cert and privatekey from a host move, and possibly start/restart it's wss connection.
* [ ]

## Miscellanea
### Host Identity

Should the remote sign some kind of identity cert provided by the host, that can be used by host-host communications to identify one another?

One of the benefits of the host-host communication is that it's not done in a borwser, so we don't *need* valid CA-signed certs. We could create our own CA for the sake of signing identidy keys used by the hosts.

The host could then have two different keys, one for tcp and the other for wss://. When clients connect to the wss one, they'd get a generic cert given to them by the remote.

When clients or hosts connect to the tcp socket, the recieving host would wrap it with a SSL connecting using their identity cert. The initiating host could then verify that the cert was signed by the same CA as their identity cert. This would enable hosts to check that what they're communicating with is actually another host for this cloud.

Does this qualify as the same milestone or a differnt milestone? I'd argue different - M0.5 is more about enabling HTTPS clients than actual security.

### Generating certs per-host vs per mirror
If we wanted better security, we'd have one cert per mirror, not per host. That way different users on the same device couldn't necessarily intercept each other's communications. But they're already running the same nebs instance on the same device - I feel like security is already probably not an issue here.

Host identity certs probably *should* be per-mirror, so each _mirror_ can identify each other uniquely, even on the same device. That's probably a good idea.

Part of the trick here is that we only have one wss:// connection per-host - so if we wanted per-mirror ssl certs, then we'd need one wss per mirror. It's not impossible, but not going to be supported before 1.0, that's for sure. Additionally, the moinline plan to implement the IRemoteKeypairProvider is to do the SingularKeypairProvider, which just gives every host the same keypair. This doesn't really add any etra security to have per-mirror keypairs, they all have the same keypair.
