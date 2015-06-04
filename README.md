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
