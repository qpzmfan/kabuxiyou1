import requests
import time
import csv
import json
import re

# ------------------------------------------------------------
# 1. 从官方获取 names.js 并提取所有内部 ID
# ------------------------------------------------------------
names_url = 'https://news.4399.com/kabuxiyou/js/ygjsq/names.js'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
resp_names = requests.get(names_url, headers=headers, timeout=10)
resp_names.encoding = 'gbk'
names_js = resp_names.text

match = re.search(r'var\s+bogyNames\s*=\s*({.*?});', names_js, re.DOTALL)
if not match:
    raise RuntimeError('未找到 bogyNames 定义')
obj_str = match.group(1)
obj_str = re.sub(r'([{,]\s*)(\d+)\s*:', r'\1"\2":', obj_str)
bogyNames = json.loads(obj_str)
ids = [int(key) for key in bogyNames.keys()]
print(f"从官方获取到 {len(ids)} 个妖怪内部 ID")

# ------------------------------------------------------------
# 2. 从官方获取 xb_names.js 并提取系别映射
# ------------------------------------------------------------
xibie_url = 'https://news.4399.com/kabuxiyou/js/ygjsq/xb_names.js'
resp_xibie = requests.get(xibie_url, headers=headers, timeout=10)
resp_xibie.encoding = 'gbk'
xibie_js = resp_xibie.text

# 注意变量名是 xb_names
match = re.search(r'xb_names\s*=\s*({[^;]+});', xibie_js, re.DOTALL)
if not match:
    raise RuntimeError('未找到 xb_names 定义，请检查网络或文件内容')
obj_str = match.group(1)
obj_str = re.sub(r'([{,]\s*)(\d+)\s*:', r'\1"\2":', obj_str)
raw_data = json.loads(obj_str)
# 提取系别名称
xibie_map = {key: val["name"] for key, val in raw_data.items()}
print(f"从官方获取到 {len(xibie_map)} 个系别映射")

# ------------------------------------------------------------
# 3. 遍历所有 ID，请求详细数据并生成 CSV 和 JSON
# ------------------------------------------------------------
base_url = 'https://news.4399.com/kabuxiyou/js/ygjsq/bogies/{}.json'

csv_file = open('kabu_full.csv', 'w', newline='', encoding='utf-8-sig')
writer = csv.writer(csv_file)
writer.writerow(['内部ID', '名称', '图鉴编号', '系别ID', '系别名称', '体力', '攻击', '防御', '法术', '抗性', '速度'])

all_pokemon = []
success_count = 0
fail_count = 0

for idx, id in enumerate(ids, 1):
    url = base_url.format(id)
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            name = data.get('name', '')
            tujian_id = data.get('tujian_id', '')
            tid = data.get('tid', '')
            xibie_name = xibie_map.get(str(tid), '')
            strength = data.get('strength', '')
            attack = data.get('attack', '')
            defence = data.get('defence', '')
            magic = data.get('magic', '')
            resistance = data.get('resistance', '')
            speed = data.get('speed', '')

            writer.writerow([id, name, tujian_id, tid, xibie_name, strength, attack, defence, magic, resistance, speed])

            pokemon_info = {
                "name": name,
                "id": tujian_id,
                "type": xibie_name,
                "hp": int(strength) if strength else 0,
                "atk": int(attack) if attack else 0,
                "def": int(defence) if defence else 0,
                "spa": int(magic) if magic else 0,
                "spd": int(resistance) if resistance else 0,
                "spe": int(speed) if speed else 0
            }
            all_pokemon.append(pokemon_info)

            success_count += 1
            print(f"[{idx}/{len(ids)}] ID {id} 下载成功 -> {name}")
        else:
            print(f"[{idx}/{len(ids)}] ID {id} 不存在 (HTTP {resp.status_code})")
            fail_count += 1
    except Exception as e:
        print(f"[{idx}/{len(ids)}] ID {id} 请求出错：{e}")
        fail_count += 1

        time.sleep(0.3)
    

csv_file.close()
print(f"CSV 完成！成功 {success_count} 条，失败 {fail_count} 条，结果已保存到 kabu_full.csv")

with open('all_pokemon.json', 'w', encoding='utf-8') as f:
    json.dump(all_pokemon, f, ensure_ascii=False, indent=2)
print(f"已生成 all_pokemon.json，共 {len(all_pokemon)} 条记录")