import re, statistics, sys

def analyze(filename, label):
    with open(filename, encoding='utf-8') as f:
        lines = f.readlines()
    
    # 从每行提取 ms 数值，格式如 "[FPS] 38.4ms | 26.0fps"
    ms_values = []
    for line in lines:
        m = re.search(r'\[FPS\]\s+([\d.]+)ms', line)
        if m:
            ms_values.append(float(m.group(1)))
    
    if len(ms_values) < 10:
        print(f"{label}: 数据不足，请检查文件")
        return
    
    avg_ms  = statistics.mean(ms_values)
    std_ms  = statistics.stdev(ms_values)
    min_ms  = min(ms_values)
    max_ms  = max(ms_values)
    avg_fps = 1000 / avg_ms
    
    print(f"\n── {label} ──")
    print(f"  样本帧数 : {len(ms_values)}")
    print(f"  最小耗时 : {min_ms:.1f} ms")
    print(f"  最大耗时 : {max_ms:.1f} ms")
    print(f"  平均耗时 : {avg_ms:.1f} ms  →  平均FPS: {avg_fps:.1f}")
    print(f"  标准差   : {std_ms:.1f} ms")

analyze("fps_深蹲.txt",   "深蹲（正面站立）")
analyze("fps_俯卧撑.txt", "俯卧撑（侧面水平）")
analyze("fps_弯举.txt",   "哑铃弯举（正面站立）")