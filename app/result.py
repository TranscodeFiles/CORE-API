import swiftclient
import magic

mime = magic.Magic(mime=True)

user = 'johndoe:swift'
key = 'cuNxJ4p0kWUfutRtsyYNOEJ5y6PeRNew5UkClepN'

conn = swiftclient.Connection(
    user=user,
    key=key,
    authurl='http://10.0.2.15/auth',
)

container_name = '208515'
conn.put_container(container_name)

for container in conn.get_account()[1]:
    print(container['name'])

for data in conn.get_container(container_name)[1]:
    print('{0}\t{1}\t{2}'.format(data['name'], data['bytes'], data['last_modified']))
