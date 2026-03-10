import ast
import sys

try:
    with open(r'd:\Program Files\novel-bot - 副本\webui.py', 'r', encoding='utf-8') as f:
        source = f.read()
    ast.parse(source)
    print("✅ webui.py 语法检查通过！")
except SyntaxError as e:
    print(f"❌ webui.py 有语法错误：{e}")
    sys.exit(1)

try:
    with open(r'd:\Program Files\novel-bot - 副本\novel_bot\cli\main.py', 'r', encoding='utf-8') as f:
        source = f.read()
    ast.parse(source)
    print("✅ novel_bot/cli/main.py 语法检查通过！")
except SyntaxError as e:
    print(f"❌ novel_bot/cli/main.py 有语法错误：{e}")
    sys.exit(1)

print("\n所有文件语法检查完成！")
