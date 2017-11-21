# nebula

## Installing

### Dependencies

Hey watch out it's python 2.7. I know that I'm terrible for not using python 3. 
I know that I'm terrible for not using virtualenvs. 

Most all of the python dependencies should be in `requirements.txt`, so those 
can all be installed with `pip install -r requirements.txt`. 

There is one tricky dependency - MiniUPnP. On linux, it should install just fine from pip.
However, I've found that the Windows install doesn't exactly work. I have the 
`miniupnpc.pyd` to add to the project if installing from pip doesn't work.
You'll need to drop it in `dep/win64`, and `NetworkController` will automatically look for it there.

### SSL Stuff

I started doing some ssl work and then gave up on it to get the prototype 
working, but there are still remnants. In order for anything to work, you'll 
need to  generate a `key` and `cert` using OpenSSL and drop them into the 
`remote` directory for using TLS/SSL.

This can be done as follows:

``` bash
openssl genrsa 1024 > remote/key

openssl req -new -x509 -nodes -sha1 -days 365 -key remote/key > remote/cert
```

TODO: Find out how do do this w/in python.

  The host will definitely need certs/keys too. I'll give the host come as well.

``` bash
openssl genrsa 1024 > host/host.key

openssl req -new -x509 -nodes -sha1 -days 365 -key host/host.key > host/host.crt
```

## Running nebula

There are two different components of nebula - the "remote" and the "host".

The remote is frequently abbreviated `nebr`, and can be run via `nebr.py`. 
The remote acts as the controller for an entire system of clouds, and should be 
operated by a central authority. This could be either nebula.com 
(working title), or a buisiness could have their own instance they operate. 
This is much like how anyone could operate their own git remote.

The host is also frequently called the "Server", and is usually abbreviated 
`nebs`, and is similarly run with `nebs.py`.
Many different nebs can "mirror" clouds from a remote onto their local machine.
While the nebs process is running, it will use the remote to sync file changes 
with any other nebs for that cloud. 

### Simple Setup

If you're on Windows, you can use `launch_both.bat` to launch both a nebr and a
 nebs for an instance. by default, this launches the `default` instance, but 
 `launch_both sunio` will run both for the `sunio` instance.

### Running Tests

Right now, the most complete set of tests is in `NebsTest002.py`. It's pretty 
easy to run them in IntelliJ, or from the commandline, in the root of the project:

`python -m test.NebsTest002`

I am VERY sure that the tests don't pass currently, and at best like 53/56 
cases worked. But specifically, right now, they're broken and I haven't figured 
out why yet.

The tests clean up startup of the test, and leave the database after running 
them, so you can use them as repopulation script for testing.

### Instances

nebula supports running multiple instances at the same time, with different 
sets of settings. These instances can each also have their own database 
associated with them, which makes them very useful for testing.

By default, both nebs and nebr default to the `default` instance. 
You can run a differnet instance with the `-i <instance>` commandline arg.

eg. The tests are currently configured to create run for the `sunio` instance.
So, if you want to run that nebs instance from the commandline, you would run
`nebs.py -i sunio start`.

Instances keep their files under the nebula root directory, under 
`nebula/instances/<host or remote>/<instance_name>`. The database and .conf file
live in there, and the tests generate directories to mirror test clouds into 
under there as well.

You can also use a arbitrary directory as the root of an instance with the 
`-w <working dir>` argument, but it's less supported and a little awkward to use.
`-i foo` is basically the same as `-w instances/<host or remote>/foo`.


### bash aliases

You'll probably want to add the following aliases to your `.bashrc`
I generally place the "installed" nebula at `var/lib/nebula`, I don't know if that
  really makes any sense but that's what I like.

``` sh
alias nebs='python /var/lib/nebula/nebs.py'

alias nebr='python /var/lib/nebula/nebr.py'

# Might be useful for watching log
alias logr='less +F --follow-name -B'
```


## Weirdness ##

### nebr/nebs instantly exits
There's a little bit of awkwardness now where you can launch a nebs/nebr process
and it will immediatly exit. That's due to the process seeing a leftover `.pid` 
file from the last time you ran it, and it will immediately exit. 

I haven't quite figured that out yet. So, here be dragons.

### PrivateData / .nebs files
In the process of running, nebs uses a .nebs file in the root of the cloud to 
track file permissions. This is a plain json file.  It is the mechanism by which
files can be shared with people or groups of people, or even made public. It's 
loaded when nebs boots up, and because it's under the cloud root, any changes to
the file will be sync'd with the other mirrors. If you try and change it while 
nebs is running, nebs will revert your changes to try and keep it correct.  

Not every file will be listed in there, only files that hae been shared with 
other users.

It does have versions in the schema, but like, lol. I clearly haven't done anything with it.

### message_blueprints
Nebula works by exchanging messages back and forth between Host, Remote, and 
Client. And instead of writing(copying and pasting) all these classes by hand, 
I created a `message_blueprints` file that can be used to  generate them automatically.

The schema is basically:
```
<ID>, <NAME_OF_MESSAGE> [, <type:arg>] 
```
But of course, the types are pretty much ignored. I can help with this if needed.


### ResultAndData (rd)

All over the codebase, in both nebula and sunburst, I'll use a ResultAndData 
struct as a return type. I don't really know why I started doing this. I guess I 
don't love using exceptions or something.

Basically, an rd has two members: `rd.success` and `rd.data`. `success` is a 
simple bool indicating if the function succeeded. `data` is the tricky bit -
 Usually, in failure cases this will either be `None` or a string with a message.
 In success cases, this is usually whatever the return value of that function 
 is supposed to be.

Here's an example, from RemoteController.py,
``` python

def do_client_get_clouds(db, session_id):
    # type: (SimpleDB, str) -> ResultAndData
    # type: (SimpleDB, str) -> ResultAndData(True, ([dict], [dict]) )
    # type: (SimpleDB, str) -> ResultAndData(False, BaseMessage )
    rd = get_user_from_session(db, session_id)
    if not rd.success:
        msg = 'generic CGCHsR error: "{}"'.format(rd.data)
        mylog(msg, '31')
        return Error(InvalidStateMessage(msg))
    else:
        user = rd.data

    mylog('getting clouds for {}'.format(user.username))

    owned_clouds = [c.to_dict() for c in user.owned_clouds.all()]
    contributed_clouds = [c.to_dict() for c in user.contributed_clouds.all()]
    return Success((owned_clouds, contributed_clouds))
```

`Success(data)` and `Error(data)` are defined as:

```python
def Error(data=None):
    return ResultAndData(False, data)
def Success(data=None):
    return ResultAndData(True, data)
```

 Because the `.data` member is essentially a void*, there's not a lot of help 
   that type-hinting can give us, so when I'm writing functions that return a 
   ResultAndData, I usually like to include three lines of type hinting - the 
   official one, and then one for the success and one for the failure case.

This probably isn't a real programming pattern, it's just something dumb that I do.
I can only really get away with it because python isn't strongly typed.


