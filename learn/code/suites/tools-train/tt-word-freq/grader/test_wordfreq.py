from wordfreq import count_words, main


def test_ignores_case_and_punctuation_between_words():
    assert count_words("Red,green; RED--blue. red!") == [("red", 3), ("blue", 1), ("green", 1)]


def test_keeps_apostrophes_inside_words():
    assert count_words("Don't stop. don't 'quote'") == [("don't", 2), ("quote", 1), ("stop", 1)]


def test_command_prints_top_n_with_alphabetical_ties(tmp_path, capsys):
    path = tmp_path / "words.txt"
    path.write_text("zeta alpha Beta.\nbeta ALPHA zeta, gamma\n")
    main([str(path), "3"])
    assert capsys.readouterr().out.splitlines() == ["alpha 2", "beta 2", "zeta 2"]
