import zipfile

from apng import APNG

import pytest

import responses

from ugoira.lib import (
    PixivError,
    download_ugoira_zip,
    get_illust_url,
    is_ugoira,
    make_apng,
    make_gif,
    make_zip,
)

from wand.image import Image

ugoira_id = 74442143
non_ugoira_id = 74073488
zip_url = 'https://i.pximg.net/img-zip-ugoira/img/' \
          '2019/04/29/16/09/38/74442143_ugoira600x600.zip'


def test_is_ugoira_true(fx_ugoira_body):
    """Test :func:`ugoira.lib.ugoira`.

    Result is :const:`True`.

    """

    @responses.activate
    def test():
        responses.reset()
        responses.add(**{
            'method': responses.GET,
            'url': get_illust_url(ugoira_id),
            'body': fx_ugoira_body,
            'content_type': 'text/html; charset=utf-8',
            'status': 200,
            'match_querystring': True,
        })

        assert is_ugoira(ugoira_id)

    test()


def test_is_ugoira_false(fx_non_ugoira_body):
    """Test :func:`ugoira.lib.ugoira`.

    Result is :const:`False`.

    """

    @responses.activate
    def test():
        responses.reset()
        responses.add(**{
            'method': responses.GET,
            'url': get_illust_url(non_ugoira_id),
            'body': fx_non_ugoira_body,
            'content_type': 'text/html; charset=utf-8',
            'status': 200,
            'match_querystring': True,
        })

        assert not is_ugoira(non_ugoira_id)

    test()


def test_download_ugoira_zip_fail_head(fx_ugoira_body):
    """Test :func:`ugoira.lib.download_ugoira_zip` with broken link.

    It must raise :class:`ugoira.lib.PixivError`.

    """

    @responses.activate
    def test():
        responses.reset()
        responses.add(**{
            'method': responses.GET,
            'url': get_illust_url(ugoira_id),
            'body': fx_ugoira_body,
            'content_type': 'text/html; charset=utf-8',
            'status': 200,
            'match_querystring': True,
        })
        responses.add(**{
            'method': responses.HEAD,
            'url': zip_url,
            'status': 403,
        })

        with pytest.raises(PixivError):
            download_ugoira_zip(ugoira_id)

    test()


def test_download_ugoira_zip_fail_get(fx_ugoira_body):
    """Test :func:`ugoira.lib.download_ugoira_zip` with broken link.

    It must raise :class:`ugoira.lib.PixivError`.

    """

    @responses.activate
    def test():
        responses.reset()
        responses.add(**{
            'method': responses.GET,
            'url': get_illust_url(ugoira_id),
            'body': fx_ugoira_body,
            'content_type': 'text/html; charset=utf-8',
            'status': 200,
            'match_querystring': True,
        })
        responses.add(**{
            'method': responses.HEAD,
            'url': zip_url,
            'status': 200,
        })
        responses.add(**{
            'method': responses.GET,
            'url': zip_url,
            'status': 403,
        })

        with pytest.raises(PixivError):
            download_ugoira_zip(ugoira_id)

    test()


def test_download_ugoira_zip_success(fx_ugoira_body, fx_ugoira_zip):
    """Test :func:`ugoira.lib.download_ugoira_zip` with correct link."""

    @responses.activate
    def test():
        responses.reset()
        responses.add(**{
            'method': responses.GET,
            'url': get_illust_url(ugoira_id),
            'body': fx_ugoira_body,
            'content_type': 'text/html; charset=utf-8',
            'status': 200,
            'match_querystring': True,
        })
        responses.add(**{
            'method': responses.HEAD,
            'url': zip_url,
            'status': 200,
        })
        responses.add(**{
            'method': responses.GET,
            'url': zip_url,
            'body': fx_ugoira_zip,
            'content_type': 'application/zip',
            'status': 200,
        })

        data, frames = download_ugoira_zip(ugoira_id)
        assert data == fx_ugoira_zip

    test()


def test_make_apng(
    fx_tmpdir,
    fx_ugoira_zip,
    fx_ugoira_frames,
):
    """Test :func:`ugoira.lib.make_apng`."""

    dest = str(fx_tmpdir / 'test.apng')
    make_apng(dest, fx_ugoira_zip, fx_ugoira_frames)
    img = APNG.open(dest)

    assert len(img.frames) == 3
    assert img.frames[0][1].delay == 1000
    assert img.frames[1][1].delay == 2000
    assert img.frames[2][1].delay == 3000


def test_make_gif(
    fx_tmpdir,
    fx_ugoira_zip,
    fx_ugoira_frames,
):
    """Test :func:`ugoira.lib.make_gif`."""

    dest = str(fx_tmpdir / 'test.gif')
    make_gif(dest, fx_ugoira_zip, fx_ugoira_frames)
    with Image(filename=dest) as img:
        assert img.format == 'GIF'
        assert len(img.sequence) == 3
        assert img.sequence[0].delay == 100
        assert img.sequence[1].delay == 200
        assert img.sequence[2].delay == 300


def test_make_zip(
    fx_tmpdir,
    fx_ugoira_zip,
    fx_ugoira_frames,
):
    """Test :func:`ugoira.lib.make_zip` with correct link."""

    dest = str(fx_tmpdir / 'test.zip')

    make_zip(dest, fx_ugoira_zip)

    with zipfile.ZipFile(dest) as f:
        assert set(f.namelist()) == set(fx_ugoira_frames.keys())
