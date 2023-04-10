from xml_func import *
import pandas as pd
import os


def input_from_console():
    word_ = input("word: ")
    class_ = input("class: ")
    meaning_ = input("meaning: ")
    example_ = input("example: ")

    assert word_ != "" and class_ != "" and meaning_ != ""
    if class_ == 'p':
        class_ = 'phrase'
    assert class_ in ['n', 'v', 'adj', 'adv', 'phrase']

    if example_ == "":
        example_ = None
    return {"word_": word_, "class_": class_, "meaning_": meaning_, "example_": example_}


def input_from_csv(data, i):
    word_ = data.loc[i, 'word']
    class_ = data.loc[i, 'class']
    meaning_ = data.loc[i, 'meaning']
    example_ = data.loc[i, 'example']
    if pd.isnull(example_):
        example_ = None
    if class_ == 'p':
        class_ = 'phrase'
    assert class_ in ['n', 'v', 'adj', 'adv', 'phrase']
    return {"word_": word_, "class_": class_, "meaning_": meaning_, "example_": example_}


def create_csv_template():
    data = pd.DataFrame(columns=['word', 'class', 'meaning', 'example'])
    data.to_csv('word.csv', encoding='utf_8_sig', index=False)


if __name__ == '__main__':
    # setting ---------------- #
    # input_type = 'csv'
    input_type = 'console'
    # ------------------------ #

    tree, root = load_word_book()
    convert_xml_to_md(root)
    # if input_type == 'console':
    #     while True:
    #         word_dict = input_from_console()
    #         upgrade_word(root, **word_dict)
    #         save_word_book(tree)
    # elif input_type == 'csv':
    #     if not os.path.exists('word.csv'):
    #         create_csv_template()
    #     else:
    #         data = pd.read_csv('word.csv')
    #         for i in range(len(data)):
    #             word_dict = input_from_csv(data, i)
    #             upgrade_word(root, **word_dict)
    #             save_word_book(tree)
