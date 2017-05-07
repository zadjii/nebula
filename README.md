# nebula


You're gonna want to make sure to generate a `key` and `cert` using OpenSSL and drop them into the `remote` directory 
for using TLS/SSL.

This can be done as follows:

```
openssl genrsa 1024 > key
```

```
openssl req -new -x509 -nodes -sha1 -days 365 -key key > cert
```

TODO: Find out how do do this w/in python.

To populate the db:
```
sh repop.sh
```


To run a remote:

```
./nebr start
```

Open a new window and config a host to point to a local directory:
```
./nebs mirror -r <remote location> -d <root dir location> <cloudname>
```

Open a new window to be consumed by host server communications:
```
./nebs start
```

Default remote location is localhost.
Default cloudname is qwer.
User/pass is asdf asdf.


## aliases

You'll probably want to add the following aliases to your `.bashrc`
I generally place the "installed" nebula at `var/lib/nebula`, I don't know if that
  really makes any sense but that's what I like.

`` sh
alias nebs='python /var/lib/nebula/nebs.py'
``


`` sh
alias nebr='python /var/lib/nebula/nebr.py'
``
`

