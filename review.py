from xml_func import *
import time
import datetime

if __name__ == '__main__':

    tree, root = load_word_book()
    while True:
        word_ = input("word: ")
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        with open('review.txt', mode='a') as rv:
            rv.write(word_ + ',' + current_time + '\n')
        try:
            word = find_word(root, word_)
            show_word(word)
        except:
            print("单词未记录在word book中！")
            with open('not recorded.txt', mode='a') as nr:
                nr.write(word_ + '\n')
