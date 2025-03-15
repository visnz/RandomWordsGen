import sys
import subprocess

def install_dependencies():
    required_libraries = ["jieba", "bs4", "PyQt5"]
    for lib in required_libraries:
        try:
            __import__(lib)
        except ImportError:
            print(f"{lib} 未安装，正在安装...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib])

install_dependencies()

import json
import random
import requests
import os
import re
import time
import jieba.posseg as pseg
from bs4 import BeautifulSoup
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QMessageBox, QCheckBox, QSlider
from PyQt5.QtCore import Qt

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
]

JSON_FILE = 'vocabularies.json'

class VocabularyManager:
    def __init__(self):
        self.vocabularies = {'v': [], 'a': [], 'n': []}  # 按词性分类存储
        self.load_vocabularies()

    def load_vocabularies(self):
        if os.path.exists(JSON_FILE):
            try:
                with open(JSON_FILE, 'r', encoding='utf-8') as file:
                    self.vocabularies = json.load(file)
                self.log("成功从 vocabularies.json 加载词汇！")
            except Exception as e:
                self.log(f"加载词汇时出错：{e}")
        else:
            self.log("文件 vocabularies.json 不存在，词汇列表为空。")

    def save_vocabularies(self):
        try:
            with open(JSON_FILE, 'w', encoding='utf-8') as file:
                json.dump(self.vocabularies, file, ensure_ascii=False, indent=4)
            self.log("成功将词汇保存到 vocabularies.json！")
        except Exception as e:
            self.log(f"保存词汇时出错：{e}")

    def crawl_from_website(self, url, depth=1, max_depth=3, use_proxy=False, proxy_port=None):
        new_words_count = 0
        if depth > max_depth:
            return new_words_count

        try:
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Referer': url,
            }

            proxies = None
            if use_proxy and proxy_port:
                proxies = {
                    'http': f'http://127.0.0.1:{proxy_port}',
                    'https': f'http://127.0.0.1:{proxy_port}',
                }

            time.sleep(random.uniform(1, 3))

            response = requests.get(url, headers=headers, proxies=proxies, allow_redirects=True)
            response.encoding = 'utf-8'

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                text = soup.get_text()
                words_with_pos = pseg.lcut(text)
                for word, pos in words_with_pos:
                    if pos.startswith('v'):  # 动词
                        self.vocabularies['v'].append(word)
                    if pos.startswith('a'):  # 形容词
                        self.vocabularies['a'].append(word)
                    if pos.startswith('n'):  # 名词
                        self.vocabularies['n'].append(word)
                new_words_count = len(words_with_pos)
                self.log(f"成功从 {url} 抓取 {new_words_count} 个词汇！")

                # 去重
                for key in self.vocabularies:
                    self.vocabularies[key] = list(set(self.vocabularies[key]))

                if depth < max_depth:
                    links = soup.find_all('a', href=True)
                    if links:
                        next_url = random.choice(links)['href']
                        if not next_url.startswith(('http://', 'https://')):
                            next_url = requests.compat.urljoin(url, next_url)
                        self.log(f"递归深度 {depth + 1}/{max_depth}，抓取新链接：{next_url}")
                        new_words_count += self.crawl_from_website(next_url, depth + 1, max_depth, use_proxy, proxy_port)
            else:
                self.log(f"请求失败，状态码：{response.status_code}")
        except Exception as e:
            self.log(f"抓取词汇时出错：{e}")

        return new_words_count

    def generate_by_format(self, format_str, words_per_line):
        format_map = {
            'v': 'v',  # 动词
            'a': 'a',  # 形容词
            'n': 'n',  # 名词
        }
        format_list = [format_map.get(char, '') for char in format_str.lower()]
        format_list = [f for f in format_list if f]  # 过滤无效字符

        if not format_list:
            return []

        result = []
        for pos in format_list[:words_per_line]:
            if pos in self.vocabularies and self.vocabularies[pos]:
                result.append(random.choice(self.vocabularies[pos]))
        return result

    def log(self, message):
        print(message)  # 输出到控制台
        if hasattr(self, 'log_panel'):
            self.log_panel.append(message)  # 输出到 Log 面板

class VocabularyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.manager = VocabularyManager()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('随机词汇生成器')
        self.setGeometry(100, 100, 800, 600)

        main_layout = QVBoxLayout()

        top_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        self.url_input = QLineEdit(self)
        self.url_input.setPlaceholderText('输入抓取网址（例如：www.sina.com.cn）')
        left_layout.addWidget(self.url_input)

        self.depth_input = QLineEdit(self)
        self.depth_input.setPlaceholderText('输入递归深度（例如：3）')
        left_layout.addWidget(self.depth_input)

        self.proxy_checkbox = QCheckBox('启用代理', self)
        left_layout.addWidget(self.proxy_checkbox)

        self.proxy_port_input = QLineEdit(self)
        self.proxy_port_input.setPlaceholderText('输入代理端口（例如：8080）')
        left_layout.addWidget(self.proxy_port_input)

        self.crawl_button = QPushButton('抓取词汇', self)
        self.crawl_button.clicked.connect(self.on_crawl)
        left_layout.addWidget(self.crawl_button)

        self.log_panel = QTextEdit(self)
        self.log_panel.setReadOnly(True)
        left_layout.addWidget(self.log_panel)

        self.num_lines_input = QLineEdit(self)
        self.num_lines_input.setPlaceholderText('生成的行数（例如：5）')
        right_layout.addWidget(self.num_lines_input)

        self.words_per_line_input = QLineEdit(self)
        self.words_per_line_input.setPlaceholderText('每行词汇数量（例如：3）')
        right_layout.addWidget(self.words_per_line_input)

        self.format_input = QLineEdit(self)
        self.format_input.setPlaceholderText('输入格式（例如：van）')
        right_layout.addWidget(self.format_input)

        self.space_checkbox = QCheckBox('每行词汇之间添加空格', self)
        self.space_checkbox.setChecked(False)
        right_layout.addWidget(self.space_checkbox)

        self.single_char_checkbox = QCheckBox('开启单字模式', self)
        right_layout.addWidget(self.single_char_checkbox)

        self.special_word_input = QLineEdit(self)
        self.special_word_input.setPlaceholderText('输入指定词汇（例如：洋气）')
        right_layout.addWidget(self.special_word_input)

        self.default_button = QPushButton('应用默认值', self)
        self.default_button.clicked.connect(self.apply_defaults)
        right_layout.addWidget(self.default_button)

        self.generate_button = QPushButton('生成随机词汇', self)
        self.generate_button.clicked.connect(self.on_generate)
        right_layout.addWidget(self.generate_button)

        self.font_size_slider = QSlider(Qt.Horizontal, self)
        self.font_size_slider.setMinimum(10)
        self.font_size_slider.setMaximum(30)
        self.font_size_slider.setValue(14)
        self.font_size_slider.valueChanged.connect(self.adjust_font_size)
        right_layout.addWidget(QLabel('字体大小：'))
        right_layout.addWidget(self.font_size_slider)

        top_layout.addLayout(left_layout, 1)
        top_layout.addLayout(right_layout, 1)
        main_layout.addLayout(top_layout)

        self.output_text = QTextEdit(self)
        self.output_text.setReadOnly(True)
        self.output_text.setFontPointSize(14)
        main_layout.addWidget(self.output_text)

        self.setLayout(main_layout)

        # 将 Log 面板绑定到 VocabularyManager
        self.manager.log_panel = self.log_panel

    def on_crawl(self):
        url = self.url_input.text()
        if not url:
            QMessageBox.warning(self, '错误', '请输入抓取网址！')
            return

        depth_text = self.depth_input.text()
        depth = int(depth_text) if depth_text.isdigit() else 1

        use_proxy = self.proxy_checkbox.isChecked()
        proxy_port = self.proxy_port_input.text() if use_proxy else None

        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        initial_count = sum(len(words) for words in self.manager.vocabularies.values())
        new_words_count = self.manager.crawl_from_website(url, max_depth=depth, use_proxy=use_proxy, proxy_port=proxy_port)
        self.manager.save_vocabularies()

        final_count = sum(len(words) for words in self.manager.vocabularies.values())
        self.manager.log(f'词汇抓取完成！\n递归次数：{depth}\n新增词汇数量：{final_count - initial_count}')

    def on_generate(self):
        num_lines_text = self.num_lines_input.text()
        words_per_line_text = self.words_per_line_input.text()
        format_str = self.format_input.text()
        special_word = self.special_word_input.text()

        if not num_lines_text.isdigit() or not words_per_line_text.isdigit():
            QMessageBox.warning(self, '错误', '请输入有效的数字！')
            return

        num_lines = int(num_lines_text)
        words_per_line = int(words_per_line_text)
        use_space = self.space_checkbox.isChecked()
        single_char_mode = self.single_char_checkbox.isChecked()

        output = ''
        for _ in range(num_lines):
            if format_str:
                result = self.manager.generate_by_format(format_str, words_per_line)
                if result:
                    if single_char_mode:
                        result = [random.choice(word) for word in result]
                    line = ' '.join(result) if use_space else ''.join(result)
                    output += line + '\n'
            else:
                random_vocabularies = random.sample(
                    self.manager.vocabularies['v'] + self.manager.vocabularies['a'] + self.manager.vocabularies['n'],
                    words_per_line
                )
                if single_char_mode:
                    random_vocabularies = [random.choice(word) for word in random_vocabularies]
                line = ' '.join(random_vocabularies) if use_space else ''.join(random_vocabularies)
                output += line + '\n'

        # 在每一行随机位置插入指定词汇
        if special_word:
            lines = output.split('\n')
            for i in range(len(lines)):
                if lines[i]:  # 确保行不为空
                    words = lines[i].split(' ') if use_space else list(lines[i])
                    insert_index = random.randint(0, len(words))
                    words.insert(insert_index, special_word)
                    lines[i] = ' '.join(words) if use_space else ''.join(words)
            output = '\n'.join(lines)

        self.output_text.setText(output)

    def apply_defaults(self):
        self.num_lines_input.setText('5')
        self.words_per_line_input.setText('3')
        self.format_input.setText('van')
        self.space_checkbox.setChecked(False)
        self.single_char_checkbox.setChecked(False)
        self.special_word_input.clear()

    def adjust_font_size(self):
        font_size = self.font_size_slider.value()
        self.output_text.setFontPointSize(font_size)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = VocabularyApp()
    ex.show()
    sys.exit(app.exec_())