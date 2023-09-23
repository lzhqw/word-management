import time
import lxml.etree as ET
import os
import nltk
import re


def get_word_lemma(word):
    """
    检查一个单词的时态并返回其原型
    >>print(get_word_lemma("understood"))
    >>understand
    """
    lemmatizer = nltk.stem.WordNetLemmatizer()  # 初始化Lemmatizer
    lemma = lemmatizer.lemmatize(word, pos='v')  # 获取单词的原型
    lemma = lemmatizer.lemmatize(lemma, pos='n')
    return lemma


def load_word_book():
    print('-- loading word book --')
    start = time.time()
    if not os.path.exists("WordBook.xml"):
        root = ET.Element("words")
        tree = ET.ElementTree(root)
        tree.write("WordBook.xml")
    else:
        tree = ET.parse("WordBook.xml")
        root = tree.getroot()
    end = time.time()
    print(f'-- loading word book done ! time: {end - start} --')
    return tree, root


def add_new_example(word, meaning_num, type_, example_):
    meanings = word.findall('meaning')
    example_ = example_.split(',')
    for example_word in example_:
        example = ET.Element(type_)
        example.text = example_word
        meanings[meaning_num].append(example)


def add_new_meaning(word, class_, meaning_, derivative_=None, synonyms_=None, antonym_=None, example_=None):
    meaning = ET.Element("meaning", {"meaning": meaning_, "class": class_})
    if derivative_:
        derivative = ET.Element("derivative")
        derivative.text = derivative_
        meaning.append(derivative)
    if synonyms_:
        synonyms = ET.Element("synonyms")
        synonyms.text = synonyms_
        meaning.append(synonyms)
    if antonym_:
        antonym = ET.Element("antonym")
        antonym.text = antonym_
        meaning.append(antonym)
    if example_:
        example = ET.Element("example")
        example.text = example_
        meaning.append(example)
    word.append(meaning)


def merge_meaning(word, meaning_, meaning_num):
    meanings = word.findall('meaning')
    meaning = meanings[meaning_num]
    meaning.attrib["meaning"] = meaning.attrib["meaning"] + ',' + meaning_


def add_new_word(root, word_, class_, meaning_, derivative_=None, synonyms_=None, antonym_=None, example_=None):
    word = ET.Element("word", {"word": word_})

    meaning = ET.Element("meaning", {"meaning": meaning_, "class": class_})
    if derivative_:
        derivative_ = derivative_.split(',')
        for derivative_word in derivative_:
            derivative = ET.Element("derivative")
            derivative.text = derivative_word
            meaning.append(derivative)
    if synonyms_:
        synonyms_ = synonyms_.split(',')
        for derivative_word in synonyms_:
            synonyms = ET.Element("synonyms")
            synonyms.text = derivative_word
            meaning.append(synonyms)
    if antonym_:
        antonym_ = antonym_.split(',')
        for derivative_word in antonym_:
            antonym = ET.Element("antonym")
            antonym.text = derivative_word
            meaning.append(antonym)
    if example_:
        example = ET.Element("example")
        example.text = example_
        meaning.append(example)

    word.append(meaning)
    show_word(word)
    root.append(word)


def find_word(root, word_):
    word = root.find('word[@word="{}"]'.format(word_))
    return word


def show_word(word):
    print("---------------------------------------------------------------")
    print(word.attrib["word"])
    print("---------------------------------------------------------------")
    for num, meaning in enumerate(word):
        print("  {}.".format(num + 1), end=" ")
        print(meaning.attrib["class"], end=".")
        print(meaning.attrib["meaning"])
        flag = 0
        for example in meaning:
            if example.tag == "derivative":
                if flag == 0:
                    print("    -derivative")
                    flag = 1
                print("        ", end="")
                print(example.text)
        flag = 0
        for example in meaning:
            if example.tag == "synonyms":
                if flag == 0:
                    print("    -synonyms")
                    flag = 1
                print("        ", end="")
                print(example.text)
        flag = 0
        for example in meaning:
            if example.tag == "antonym":
                if flag == 0:
                    print("    -antonym")
                    flag = 1
                print("        ", end="")
                print(example.text)
        flag = 0
        for example in meaning:
            if example.tag == "example":
                if flag == 0:
                    print("    -example")
                    flag = 1
                print("        ", end="")
                print(example.text)
        print("---------------------------------------------------------------")


def upgrade_word(root, word_, class_, meaning_, derivative_=None, synonyms_=None, antonym_=None, example_=None):
    # --------------------------------------------------- #
    # step1. 该单词的原型是否存在，如不存在直接插入
    # --------------------------------------------------- #
    # word_ = get_word_lemma(word_)
    word = find_word(root, word_)
    if word is not None:
        show_word(word)
        # --------------------------------------------------- #
        # step2. 如果已经存在，可能的操作有：
        # 1. 添加新的意思
        # 2. 在旧有意思上对意思进行补充 - 1) 选择意思 2) 合并属性
        # 3. 在旧有意思上添加例句 - 1) 选择意思 2) 增加例句
        # 4. 添加衍生词
        # 5. 添加同义词
        # 6. 添加反义词
        # 7. 添加形近词
        # 4. 放弃
        # --------------------------------------------------- #
        prompt = ("1. 添加新的意思\n2. 在旧有意思上对意思进行补充\n3. 在旧有意思上添加例句\n"
                  "4. 添加衍生词\n5. 添加同义词\n6. 添加反义词\n7. 放弃")
        print(prompt)
        choice = input("请输入选项：")
        if "1" in choice:
            add_new_meaning(word, class_, meaning_, derivative_, synonyms_, antonym_, example_)
        if "2" in choice:
            meaning_num = int(input("请输入序号：")) - 1
            merge_meaning(word, meaning_, meaning_num)
        if "3" in choice:
            meaning_num = int(input("请输入序号：")) - 1
            add_new_example(word, meaning_num, "example", example_)
        if "4" in choice:
            meaning_num = int(input("请输入序号：")) - 1
            add_new_example(word, meaning_num, "derivative", derivative_)
        if "5" in choice:
            meaning_num = int(input("请输入序号：")) - 1
            add_new_example(word, meaning_num, "synonyms", synonyms_)
        if "6" in choice:
            meaning_num = int(input("请输入序号：")) - 1
            add_new_example(word, meaning_num, "antonym", antonym_)
        if choice == "7":
            pass
        else:
            print("输入错误")
        show_word(word)

    else:
        add_new_word(root, word_, class_, meaning_, derivative_, synonyms_, antonym_, example_)


def save_word_book(tree):
    tree.write("WordBook.xml", encoding='utf-8')


def notPhrase(word):
    for meaning in word:
        class_ = meaning.attrib["class"]
        if class_ == 'phrase':
            return False
    return True


def get_all_word(root, phrase=False):
    if phrase:
        with open('words.txt', 'w') as file:
            for word in root:
                word_ = word.attrib["word"]
                file.write(word_ + '\n')
    else:
        with open('words.txt', 'w') as file:
            for word in root:
                if notPhrase(word):
                    word_ = word.attrib["word"]
                    file.write(word_ + '\n')


# 暂时未修改
def convert_xml_to_md(root):
    with open('word.md', mode='w') as f:
        for word in root:
            word_ = word.attrib["word"]
            f.write(f"**{word_}**\n")
            for meaning in word:
                meaning_ = meaning.attrib["meaning"]
                class_ = meaning.attrib["class"]
                f.write(f"* {class_}.{meaning_}\n")
                for example in meaning:
                    example_ = example.text
                    f.write(f"  * {example_}\n")
            f.write("\n")
            f.write("---\n")
    f.close()

# if __name__ == '__main__':
# tree, root = load_word_book()
# print(get_word_lemma("contextualize"))
# add_new_word(root, "rate", "v", "打分", "when they later rated the work")
# print(ET.tostring(root, pretty_print=True).decode('utf-8'))
# tree.write("WordBook.xml", encoding='utf-8')
# upgrade_word(root, "rate", "v", "打分", "when they later rated the work")
# rate = find_word(root, "rate")
# show_word(rate)
