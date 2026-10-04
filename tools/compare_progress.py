import glob
import json

for i in ['01', '02', '03', '04', '05']:
    p_m2 = list(glob.glob(f'D:/Strata/benchmark_runs/group_mode2/{i}_*/metrics.json'))
    p_spd = list(glob.glob(f'D:/Strata/benchmark_runs/group_mode2_speed/{i}_*/metrics.json'))
    if p_m2 and p_spd:
        m2 = json.load(open(p_m2[0], encoding='utf-8'))
        spd = json.load(open(p_spd[0], encoding='utf-8'))
        tname = m2['benchmark_title'][:32]
        print(f"=== Task {i}: {tname} ===")
        print(f"  [Mode 2 原版] 思考: {m2['thinking_tokens']:,} | 代码: {m2['content_tokens']:,} | 耗时: {m2['duration_sec']:.1f}s | 速度: {m2['decode_tokens_per_second']:.1f} tok/s | 字节: {m2['code_bytes']:,}")
        print(f"  [Mode 2 极速] 思考: {spd['thinking_tokens']:,} | 代码: {spd['content_tokens']:,} | 耗时: {spd['duration_sec']:.1f}s | 速度: {spd['decode_tokens_per_second']:.1f} tok/s | 字节: {spd['code_bytes']:,}")
        diff_speed = spd['decode_tokens_per_second'] - m2['decode_tokens_per_second']
        diff_dur = spd['duration_sec'] - m2['duration_sec']
        print(f"  --> 速度差: {diff_speed:+.1f} tok/s | 耗时差: {diff_dur:+.1f}s\n")
