import swiftclient
import magic

mime = magic.Magic(mime=True)

user = 'johndoe:swift'
key = 'rJrk5aYy8d6kCM1N1IasVQJmFJyXIawSu0d1L224'

conn = swiftclient.Connection(
    user=user,
    key=key,
    authurl='http://10.0.2.15/auth',
)

container_name = '208515'
conn.put_container(container_name)

for container in conn.get_account()[1]:
    print(container['name'])

with open('./media/test.mp4', 'r') as my_file:
    conn.put_object(container_name, 'test.mp4', contents=my_file.read(),
                    content_type=mime.from_file('./media/test.mp4'))

for data in conn.get_container(container_name)[1]:
    print('{0}\t{1}\t{2}'.format(data['name'], data['bytes'], data['last_modified']))
