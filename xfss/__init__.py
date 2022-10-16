from functools import update_wrapper

from flask import request, Response

from xfss.HTTPStatus import NOT_ACCEPTABLE
from xfss.Util import included


def requires_payload(required_fields: set):
	def decorator(operation):
		def verify_payload(*args, **kwargs):
			if not included(required_fields, request.json):
				response = Response(status=NOT_ACCEPTABLE)
			else:
				response = operation(*args, **kwargs)
			return response

		return update_wrapper(verify_payload, operation)

	return decorator
