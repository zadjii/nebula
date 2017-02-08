from remote import User, Cloud


def list_users(instance, argv):
    db = instance.get_db()
    # users = User.query.all()
    users = db.session.query(User).all()
    print 'There are ', len(users), 'users.'
    print '[{}] {:16} {:16}'.format('id', 'name', 'email')
    for user in users:
        print '[{}] {:16} {:16}'.format(user.id, user.name, user.email)


def list_clouds(instance, argv):
    db = instance.get_db()
    # clouds = Cloud.query.all()
    clouds = db.session.query(Cloud).all()
    print 'There are ', len(clouds), 'clouds.'
    print '[{}] {:16} {:16} {:16}'.format('id', 'name', 'max_size', 'owners')
    for cloud in clouds:
        owners = ''
        for owner in cloud.owners:
            owners = owners + owner.name + ' '
        print '[{}] {:16} {:16} {}'\
            .format(cloud.id, cloud.name, cloud.max_size, owners)
