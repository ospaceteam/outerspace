# split a uri
# <path>;<params>?<query>#<fragment>
path_regex = regex.compile (
#        path        params        query       fragment
	'\\([^;?#]*\\)\\(;[^?#]*\\)?\\(\\?[^#]*\)?\(#.*\)?'
	)

def split_path (path):
	if path_regex.match (path) != len(path):
		raise ValueError, "bad path"
	else:
		return map (lambda i,r=path_regex: r.group(i), range(1,5))
