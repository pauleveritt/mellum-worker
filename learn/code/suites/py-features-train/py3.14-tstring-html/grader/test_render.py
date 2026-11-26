from render import html


def test_values_are_escaped_markup_is_kept():
    name, count = "<b>Ada</b>", 3
    assert html(t"<p>Hello {name}, you have {count} messages</p>") == (
        "<p>Hello &lt;b&gt;Ada&lt;/b&gt;, you have 3 messages</p>")


def test_quotes_in_values_are_escaped():
    title = 'say "hi" & go'
    assert html(t'<a title="{title}">x</a>') == '<a title="say &quot;hi&quot; &amp; go">x</a>'


def test_plain_fragment():
    assert html(t"<hr>") == "<hr>"
