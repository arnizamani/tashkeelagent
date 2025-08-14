from tashkeel_agent import extract_arabic_words, make_chunks

def test_extract_arabic_words():
    lines = [
        "<html>",
        "علم عَلِيمٌ",
        "اشتريت ٣ كتب",
        "  ",
        ",",
        "English text with Arabicالعربية",
        "English number 123",
        "",
    ]
    expected_all_words = [
        ["<html>"],
        ["علم", " ", "عَلِيمٌ"],
        ["اشتريت", " ", "٣", " ", "كتب"],
        ["  "],
        [","],
        ["English text with Arabic", "العربية"],
        ["English number ", "123"],
        []
    ]
    expected_arabic_words = [
        (1, 0, "علم"),
        (1, 2, "عَلِيمٌ"),
        (2, 0, "اشتريت"),
        (2, 2, "٣"),
        (2, 4, "كتب"),
        (5, 1, "العربية"),
    ]
    all_words, arabic_words = extract_arabic_words(lines)
    assert all_words == expected_all_words
    assert arabic_words == expected_arabic_words

    chunks = make_chunks(arabic_words, max_chunk_size=20)
    assert chunks == [
        [(1, 0, "علم"), (1, 2, "عَلِيمٌ"), (2, 0, "اشتريت")],
        [(2, 2, "٣"), (2, 4, "كتب"), (5, 1, "العربية")],
    ]
