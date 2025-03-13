import json
import random
import requests
import sys
import os
import re
import jieba.posseg as pseg
from bs4 import BeautifulSoup

# 预定义的随机 User-Agent 列表
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
]

# JSON 文件路径
JSON_FILE = 'vocabularies.json'

class VocabularyManager:
    def __init__(self):
        self.vocabularies = []

    def load_vocabularies(self):
        """从 JSON 文件加载词汇"""
        if os.path.exists(JSON_FILE):
            try:
                with open(JSON_FILE, 'r', encoding='utf-8') as file:
                    self.vocabularies = json.load(file)
                print(f"成功从 {JSON_FILE} 加载 {len(self.vocabularies)} 个词汇！")
            except Exception as e:
                print(f"加载词汇时出错：{e}")
        else:
            print(f"文件 {JSON_FILE} 不存在，词汇列表为空。")

    def save_vocabularies(self):
        """将词汇保存到 JSON 文件"""
        try:
            with open(JSON_FILE, 'w', encoding='utf-8') as file:
                json.dump(self.vocabularies, file, ensure_ascii=False, indent=4)
            print(f"成功将 {len(self.vocabularies)} 个词汇保存到 {JSON_FILE}！")
        except Exception as e:
            print(f"保存词汇时出错：{e}")

    def crawl_from_website(self, url):
        """从指定网站抓取词汇"""
        try:
            # 随机选择一个 User-Agent
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Referer': url,
            }

            # 发送请求
            response = requests.get(url, headers=headers, allow_redirects=True)
            response.encoding = 'utf-8'  # 设置编码

            # 检查响应状态码
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # 提取网页中的所有文本内容
                text = soup.get_text()
                # 使用 jieba.posseg 进行词性标注
                words_with_pos = pseg.lcut(text)
                # 过滤词性：只保留名词 (n)、动词 (v)、形容词 (a)
                new_words = [word for word, pos in words_with_pos if pos.startswith(('n', 'v', 'a'))]
                # 去除标点符号和非中文字符
                new_words = [word for word in new_words if re.match(r'^[\u4e00-\u9fa5]+$', word)]
                # 去重并追加到现有词汇列表
                self.vocabularies = list(set(self.vocabularies + new_words))
                print(f"成功从 {url} 抓取 {len(new_words)} 个词汇！")
            else:
                print(f"请求失败，状态码：{response.status_code}")
        except Exception as e:
            print(f"抓取词汇时出错：{e}")

    def generate_random_vocabularies(self, min_count, max_count):
        """随机生成指定数量的词汇"""
        if not self.vocabularies:
            print("词汇列表为空，请先导入或抓取词汇！")
            return []

        count = random.randint(min_count, max_count)
        if count > len(self.vocabularies):
            print(f"词汇数量不足，当前只有 {len(self.vocabularies)} 个词汇。")
            return []

        selected = random.sample(self.vocabularies, count)
        return selected


# 主函数
def main():
    manager = VocabularyManager()

    # 检查是否带有 -crawl 参数
    if '-crawl' in sys.argv:
        # 获取抓取的网址
        if len(sys.argv) > 2:
            url = sys.argv[2]
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url  # 默认使用 https
            # 抓取词汇
            manager.load_vocabularies()  # 先加载现有词汇
            manager.crawl_from_website(url)
            # 保存词汇到 JSON 文件
            manager.save_vocabularies()
        else:
            print("请提供要抓取的网址，例如：python vocabulary_app.py -crawl 'www.sina.com.cn'")
    else:
        # 从 JSON 文件加载词汇
        manager.load_vocabularies()

    # 生成随机词汇
    min_count = 3
    max_count = 6
    random_vocabularies = manager.generate_random_vocabularies(min_count, max_count)

    # 输出结果
    if random_vocabularies:
        print(f"随机生成的 {len(random_vocabularies)} 个词汇：")
        for word in random_vocabularies:
            print(word)


if __name__ == '__main__':
    main()