"""Resuming DPO training after a crash: same remaining batches, same optimizer state."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from resume import plan_updates  # noqa: E402


def test_plan_covers_every_pair_once_per_epoch():
    plan = plan_updates(n_pairs=10, accum=4, epochs=2, seed=0)
    assert [u for _ep, u, _idx in plan] == list(range(1, 7))
    for ep in (0, 1):
        idx = [i for e, _u, batch in plan for i in batch if e == ep]
        assert sorted(idx) == list(range(10))


def test_resuming_gives_exactly_the_remaining_batches():
    fresh = plan_updates(n_pairs=120, accum=4, epochs=1, seed=0)
    resumed = plan_updates(n_pairs=120, accum=4, epochs=1, seed=0, start=9)
    assert resumed == fresh[9:]


def test_optimizer_state_round_trips(tmp_path):
    import mlx.core as mx
    import mlx.nn as nn
    import mlx.optimizers as optim

    from resume import load_checkpoint, save_checkpoint

    model = nn.Linear(3, 2)
    opt = optim.Adam(learning_rate=1e-2)
    loss = lambda m: (m(mx.ones((1, 3))) ** 2).sum()  # noqa: E731
    _, g = nn.value_and_grad(model, loss)(model)
    opt.update(model, g)
    mx.eval(model.parameters(), opt.state)
    save_checkpoint(tmp_path, model.trainable_parameters(), opt, update=7)

    model2, opt2 = nn.Linear(3, 2), optim.Adam(learning_rate=1e-2)
    assert load_checkpoint(tmp_path, model2, opt2) == 7
    assert mx.allclose(model2.weight, model.weight)
    assert mx.allclose(opt2.state["weight"]["m"], opt.state["weight"]["m"])
    assert int(opt2.state["step"]) == int(opt.state["step"])
