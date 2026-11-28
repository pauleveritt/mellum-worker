from shell import command


def test_values_are_quoted_literals_kept():
    branch, who = "main", "Ada Lovelace"
    assert command(t"git log {branch} --author {who}") == "git log main --author 'Ada Lovelace'"


def test_injection_stays_one_argument():
    name = "x; rm -rf /"
    assert command(t"touch {name}") == "touch 'x; rm -rf /'"


def test_plain_command():
    assert command(t"ls -la") == "ls -la"
