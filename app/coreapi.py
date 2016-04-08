# -*- coding: utf-8 -*-
"""
    coreapi
    ~~~~~~~~~~~~~~

    Core api make transcoding

    :copyright: (c) 2016 by SUPINFO.
    :license: LICENSE_NAME, see LICENSE_FILE for more details.
"""

from factory import create_app
from resources.transcode import Transcode

app, api = create_app()


api.add_resource(Transcode, '/transcode/name=<string:name>&type_file=<string:type_file>&call_back=<string:call_back>')


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')
