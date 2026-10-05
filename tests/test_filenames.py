import pytest

from phone_lan_transfer.filenames import validate_destination_name


@pytest.mark.parametrize(
    "name",
    ["photo.jpg", "report final.pdf", ".env", "résumé.pdf", "é" * 125 + ".txt"],
)
def test_valid_destination_name_is_returned(name: str) -> None:
    assert validate_destination_name(name) == name


@pytest.mark.parametrize(
    "name",
    [
        "",
        ".",
        "..",
        " folder.txt",
        "folder.txt ",
        "photo.",
        "../photo.jpg",
        "folder/photo.jpg",
        "folder\\photo.jpg",
        "photo:copy.jpg",
        "photo\x00.jpg",
        "photo\n.jpg",
        "CON.txt",
        "lpt1.pdf",
        "COM¹.txt",
        "é" * 126 + ".txt",
        "\ud800",
    ],
)
def test_unsafe_destination_name_is_rejected(name: str) -> None:
    with pytest.raises(ValueError):
        validate_destination_name(name)
