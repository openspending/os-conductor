from flask import request, abort
from flask.ext.jsonpify import jsonpify

mock_progress = {}


class ApiLoad:
    """Autorize a client for the file uploading.
    """

    # Public

    def __call__(self):
        datapackage = request.values.get('datapackage')
        if datapackage is None:
            abort(400)
        mock_progress[datapackage] = 0
        ret = {
            "progress": 0,
            "status": "progress"
        }
        return jsonpify(ret)


class ApiPoll:
    """Autorize a client for the file uploading.
    """

    # Public

    def __call__(self):
        datapackage = request.values.get('datapackage')
        if datapackage is None:
            abort(400)
        if datapackage not in mock_progress:
            abort(404)
        num = mock_progress[datapackage]
        ret = {
            "progress": num*1000+123,
            "status": "progress" if num < 10 else "done"
        }
        if num < 10:
            mock_progress[datapackage] += 1
        return jsonpify(ret)
