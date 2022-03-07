import fsspec

_fs = fsspec.filesystem("http")


class FileserverFileSystem(fsspec.implementations.http.HTTPFileSystem):
    """Wrapper around HTTPFileSystem of fspec which implements rm_file"""

    def __init__(
        self,
        simple_links=True,
        block_size=None,
        same_scheme=True,
        size_policy=None,
        cache_type="bytes",
        cache_options=None,
        asynchronous=False,
        loop=None,
        client_kwargs=None,
        **storage_options,
    ):
        super().__init__(
            simple_links=simple_links,
            block_size=block_size,
            same_scheme=same_scheme,
            size_policy=size_policy,
            cache_type=cache_type,
            cache_options=cache_options,
            asynchronous=asynchronous,
            loop=loop,
            client_kwargs=client_kwargs,
            **storage_options,
        )

    async def _rm_file(self, path, **kwargs):
        session = await self.set_session()
        async with session.delete(path, **self.kwargs) as r:
            assert r.status == 204
