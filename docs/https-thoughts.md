# HTTPS / SSL Implementation (Milestone v0.5)

The goal here isn't to ensure security necessarily. Total security would be great, but acting as a CA and issuing certs to each host is likely infeasible, at least in the short term.

The goal of this spec is not real proper securty, but merely enabling HTTPS as a communication mechanism to the host. If you wanted to create a web frontend client for nebula, you'd probably want to serve that site using HTTPS. If you have a site that's delivered using HTTPS, then you can only connect to websockets that are served using HTTPS (`wss://`) as well. So the host needs to be able to have a valid HTTPS cert to be able to connect to it.
Not only does the cert need to be valid, but it also needs to be trusted by the browser itself, which means it can't just come from your own local CA, it needs to be signed by a proper, trusted CA. That's where things get tricky.


## Keypair Provider

Remote haas an `IKeypairProvider` that provides keypairs for the host.

This is a dumb solution that isn't actually secure, it's just HTTPS enough to enable wss connections to hosts. This is mostly brainstorming to support the `starmap.io` scenario of having a public web frontend to as a nebula client.

We implement a `SingularKeypairProvider` that basically gives every host the same (private key, cert) pair.
For this to work in production, that cert would need to be a wildcard cert, for a domain like `*.host.starmap.io`.
The remote is configured to use this as it's keypair provider somehow.
**TODO**: How? Via the commandline? Via a python module passed on the commadline/via a .conf file? It'd need to be configured somehow,

## Public Address Provider

Then, we have the remote configured to add each host's IP to a DNS configuration for `.host.starmap.io`.
E.g., `A ip.host.starpam.io -> <ip>`, for each and every IP that ever registers as a host.
Presumably, we could create a DNS server that just replies with those responses for any IP, without even needing to register records manually.

In fact, having records in the DNS server for each host is probably a terrible idea. But if we needed too, here's how we could.

<!--
We'd add a list of `IHostMoveTrigger`s to the remote that fire when a host moves. Then, the Starmap scenario would configure a `DNSUpdateTrigger` that would be implemented using Lexicon, that would cause a DNS provider to update it's records to have the new `A ip.host.starpam.io -> <ip>` entry.

Let's try and get away without needing to do that however. If we can somehow configure an application to run as a DNS provider that does what we want, then I don't think we'd need the `IHostMoveTrigger` at all.
-->

ACTUALLY no it should be a `IPublicAddressProvider` that gets the public IP the remote should use for that host. By default, it's unimplemented, and the remote uses the host's IP as the public IP. But with the `DNSIpRegistrar`, then the the provider registers the IP with the DNS service and returns the full name for that IP. alternatively, the `DnsIpForwarder` can be configured with just a top-level domain (`.host.starmap.io`) and it'll prepend the IP to it and return that, no registration involved.
`DNSIpRegistrar` would probably be a subclass of `DnsIpProvider`, but

``` python
class IPublicAddressProvider(object):
    def get_public_address(self, ip):
        pass
```

So yea we definitely want to have the IPublicAddressProvider, regardless if it's hooked up to DNS or not.
