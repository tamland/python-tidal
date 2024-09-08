class AuthenticationError(Exception):
    pass


class AssetNotAvailable(Exception):
    pass


class TooManyRequests(Exception):
    pass


class URLNotAvailable(Exception):
    pass


class StreamNotAvailable(Exception):
    pass


class MetadataNotAvailable(Exception):
    pass


class ObjectNotFound(Exception):
    pass


class UnknownManifestFormat(Exception):
    pass


class ManifestDecodeError(Exception):
    pass


class MPDNotAvailableError(Exception):
    pass


class InvalidISRC(Exception):
    pass


class InvalidUPC(Exception):
    pass
