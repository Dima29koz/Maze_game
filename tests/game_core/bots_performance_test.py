import argparse
import cProfile
import json
import os
import pstats
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


def _get_filename(prefix: str, ext: str):
    here = os.path.dirname(os.path.abspath(__file__))
    base_path = 'test_results'
    filename = f'{prefix}_{time.strftime("%m-%d-%Y_%H-%M-%S", time.localtime())}.{ext}'
    return os.path.join(here, base_path, filename)


def _save_result(result):
    filename = _get_filename('performance_res', 'json')
    with open(filename, 'w') as f:
        json.dump(result, f)


def _gen_seeds(iters):
    return [random.random() for _ in range(iters)]


def main(args):
    save_res = True
    _iters = 100
    _seed = 0.5380936623177652  # сравнивать чиселки на этом сиде
    # _seed = 0.41856783943105225  # работает в 3 раза дольше
    _num_players = 4

    if args.file:
        here = os.path.dirname(os.path.abspath(__file__))
        base_path = 'test_results'
        filename = str(os.path.join(here, base_path, args.file))
        p = pstats.Stats(filename + '.prof')
        p.sort_stats('cumtime').print_stats()
        return

    if args.profile:
        pr = cProfile.Profile()
        pr.enable()
        res = performance_test(seeds=[_seed], num_players=_num_players, verbose=False)
        # res = performance_test(seeds=_gen_seeds(_iters), num_players=_num_players, verbose=False)
        pr.disable()
        _filename = f'profile_res_{time.strftime("%m-%d-%Y_%H-%M-%S", time.localtime())}.prof'
        pr.dump_stats(_get_filename('profile_res', 'prof'))
    else:
        res = performance_test(seeds=[_seed], num_players=_num_players, verbose=False)

    if save_res:
        _save_result(res)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", action='store_true')
    parser.add_argument("--file", type=str, help='profile_res.prof')
    main(parser.parse_args())
