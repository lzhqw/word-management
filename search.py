from xml_func import *


def input_from_console():
    word_ = input("word: ")
    class_ = input("class: ")
    meaning_ = input("meaning: ")
    example_ = input("example: ")
    derivative_ = input("derivative: ")
    synonyms_ = input("synonyms: ")
    antonym_ = input("antonym: ")

    assert word_ != "" and class_ != "" and meaning_ != ""
    if class_ == 'p':
        class_ = 'phrase'
    assert class_ in ['n', 'v', 'adj', 'adv', 'phrase']

    if example_ == "":
        example_ = None
    return {"word_": word_, "class_": class_, "meaning_": meaning_, "example_": example_,
            "derivative_": derivative_, "synonyms_": synonyms_, "antonym_": antonym_}


tree, root = load_word_book()
while True:
    word_ = input("word: ")
    word = find_word(root, word_)
    if word is None:
        print("word not in word book")
        addtowordbook = input("是否加入词书：0表示不加入，1表示加入")
        if addtowordbook != '1':
            continue
        word_dict = input_from_console()
        upgrade_word(root, **word_dict)
        save_word_book(tree)
    word = find_word(root, word_)
    show_word(word)
