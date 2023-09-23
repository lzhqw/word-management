from xml_func import load_word_book
from xml_func import show_word as show_word_xml
from sql_func import *

tree, root = load_word_book()
conn = connect()
initialize_database(conn)

for word in root:
    word_ = word.attrib["word"]
    for num, meaning in enumerate(word):
        pos = meaning.attrib["class"]
        meaning_ = meaning.attrib["meaning"]
        derivatives = []
        for example in meaning:
            if example.tag == "derivative":
                derivatives.append(example.text)
        synonyms = []
        for example in meaning:
            if example.tag == "synonyms":
                synonyms.append(example.text)
        antonyms = []
        for example in meaning:
            if example.tag == "antonym":
                antonyms.append(example.text)
        examples = []
        for example in meaning:
            if example.tag == "example":
                examples.append(example.text)
        print(word_, pos, meaning_, derivatives, synonyms, antonyms, examples)
        similarWords = []
        insert(conn, word_, pos, meaning_, examples, derivatives, synonyms, antonyms, similarWords)
