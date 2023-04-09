
def id_from_uri(uri: str):
    """Helper method to get the ID from a URI string like so:
    URI: 'spotify:artist:012345...'
    ID: '012345...'
    """
    return uri.split(':')[2]