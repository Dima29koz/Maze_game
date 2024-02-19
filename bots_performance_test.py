import json
import random
import time

from game_core.app import LocalGame


def performance_test(seeds: list, num_players=2, verbose=False):
    all_times = []
    all_steps = []
    all_steps_tr = []
    shots, shoots_s = 0, 0
    all_leaves = []
    for i in range(len(seeds)):
        game = LocalGame(num_players=num_players, seed=seeds[i], with_bot=True)
        times, steps, tr_steps, sh, sh_s, leaves = game.run_performance_test(verbose)
        all_steps.append(steps)
        all_steps_tr.append(tr_steps)
        all_times.append(times)
        shots += sh
        shoots_s += sh_s
        all_leaves.append(leaves)
    return {
        'steps': all_steps,
        'tr_steps': all_steps_tr,
        'times': all_times,
        'shooting res': (shots, shoots_s),
        'leaves': all_leaves
    }


def _save_result(result):
    filename = f'test_results/performance_res_{time.strftime("%m-%d-%Y_%H-%M-%S", time.localtime())}.json'
    with open(filename, 'w') as f:
        json.dump(result, f)


def _gen_seeds(iters):
    return [random.random() for _ in range(iters)]


if __name__ == "__main__":
    _iters = 100
    _seed = 0.5380936623177652  # сравнивать чиселки на этом сиде
    # _seed = 0.41856783943105225  # работает в 3 раза дольше
    _num_players = 4
    res = performance_test(seeds=[_seed], num_players=_num_players, verbose=False)
    # res = performance_test(seeds=_gen_seeds(_iters), num_players=_num_players, verbose=False)
    # _save_result(res)
    # print(res)
