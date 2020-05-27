import shutil
from pathlib import Path

import pytest
from graphene.test import Client

from .schema import schema

GET_ALBUM = """
query GetAlbum($path: String!) {
  album(path: $path) {
    path
    contents {
      pageInfo {
        startCursor
        endCursor
      }
      edges {
        node {
          ... on Image {
            path
            __typename
          }
          ... on Album {
            path
            __typename
          }
        }
      }
    }
  }
}
"""
GET_IMAGE = """
query GetImage($path: String!) {
  image(path: $path) {
    path
    iptc {
        caption
        keywords
    }
    xmp {
        rating
    }
    __typename
  }
}
"""
SET_RATING = """
mutation SetImageRating($input: SetRatingInput!) {
  setRating(input: $input) {
    image {
      path
      fileInfo {
        created
      }
      xmp {
        rating
      }
    }
  }
}
"""


@pytest.fixture
def image() -> str:
    existing = Path("./gallery/fixtures/existing.jpg")
    test_image = Path("./gallery/fixtures/tmpImage.jpg")
    shutil.copyfile(existing, test_image)
    return str(test_image.relative_to("./gallery"))


def test_album_lists_contents():
    client = Client(schema)
    executed = client.execute(GET_ALBUM, variables={"path": "fixtures"})
    assert "errors" not in executed
    assert executed["data"]["album"]["path"] == "fixtures"
    assert len(executed["data"]["album"]["contents"]["edges"]) == 5


def test_image_gets_meta():
    client = Client(schema)
    executed = client.execute(GET_IMAGE, variables={"path": "fixtures/Lenna.jpg"})
    assert "errors" not in executed
    assert executed["data"]["image"]["iptc"]["caption"] == "I am a caption"
    assert executed["data"]["image"]["xmp"]["rating"] == 0


def test_set_rating(image):
    client = Client(schema)
    executed = client.execute(
        SET_RATING, variables={"input": {"path": image, "rating": 5}}
    )
    assert "errors" not in executed
    assert executed["data"]["setRating"]["image"]["xmp"]["rating"] == 5
