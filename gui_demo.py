import tkinter as tk
from sql_func import *


class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.component = []
        self.createWidget()

    def createWidget(self):
        # word
        self.label_word = tk.Label(self, text="word: ", width=6, height=1)
        self.label_word.grid(row=0, column=0)
        self.word_entry = tk.Entry(self)
        self.word_entry.grid(row=0, column=1, sticky="w")
        self.word_entry.bind("<Return>", lambda event: self.show_word(conn, self.word_entry.get()))

        # -------------------------------------- #
        # similarWords
        # -------------------------------------- #
        self.label_similarWords = tk.Label(self, text="similar words: ", width=15, height=1)
        self.label_similarWords.grid(row=7, column=0)
        self.similarWords_text = tk.Text(self, height=1, width=20)
        self.similarWords_text.grid(row=7, column=1, sticky="w")
        self.similarWords_text.bind("<KeyRelease>",
                                    lambda event, text_box=self.similarWords_text: self.update_text_height(text_box,
                                                                                                           event))
        self.add_meaning_box()

        # -------------------------------------- #
        # 按钮：insert
        # -------------------------------------- #
        self.button_insert = tk.Button(self, text="insert", command=self.insert)
        self.button_insert.grid(row=0, column=2)

        # -------------------------------------- #
        # 按钮：add meaning
        # -------------------------------------- #
        self.button_insert = tk.Button(self, text="add meaning", command=self.add_meaning_box)
        self.button_insert.grid(row=1, column=2)

        # -------------------------------------- #
        # 按钮：clear
        # -------------------------------------- #
        self.button_clear = tk.Button(self, text="clear", command=self.clear)
        self.button_clear.grid(row=2, column=2)

    def add_meaning_box(self):
        num_meaning = 6 * len(self.component)
        # -------------------------------------- #
        # pos
        # -------------------------------------- #
        label_pos = tk.Label(self, text="pos: ", width=5, height=1)
        label_pos.grid(row=num_meaning + 1, column=0)
        pos_entry = tk.Entry(self)
        pos_entry.grid(row=num_meaning + 1, column=1, sticky="w")

        # -------------------------------------- #
        # meaning
        # -------------------------------------- #
        label_meaning = tk.Label(self, text="meaning: ", width=9, height=1)
        label_meaning.grid(row=num_meaning + 2, column=0)
        meaning_entry = tk.Entry(self)
        meaning_entry.grid(row=num_meaning + 2, column=1, sticky="w")

        # -------------------------------------- #
        # example
        # -------------------------------------- #
        label_example = tk.Label(self, text="example: ", width=9, height=1)
        label_example.grid(row=num_meaning + 3, column=0)
        example_text = tk.Text(self, height=1, width=40)
        example_text.grid(row=num_meaning + 3, column=1, sticky="w")
        example_text.bind("<KeyRelease>",
                          lambda event, text_box=example_text: self.update_text_height(text_box, event))

        # -------------------------------------- #
        # derivative
        # -------------------------------------- #
        label_derivative = tk.Label(self, text="derivative: ", width=12, height=1)
        label_derivative.grid(row=num_meaning + 4, column=0)
        derivative_text = tk.Text(self, height=1, width=20)
        derivative_text.grid(row=num_meaning + 4, column=1, sticky="w")
        derivative_text.bind("<KeyRelease>",
                             lambda event, text_box=derivative_text: self.update_text_height(text_box, event))

        # -------------------------------------- #
        # synonyms
        # -------------------------------------- #
        label_synonyms = tk.Label(self, text="synonyms: ", width=10, height=1)
        label_synonyms.grid(row=num_meaning + 5, column=0)
        synonyms_text = tk.Text(self, height=1, width=20)
        synonyms_text.grid(row=num_meaning + 5, column=1, sticky="w")
        synonyms_text.bind("<KeyRelease>",
                           lambda event, text_box=synonyms_text: self.update_text_height(text_box, event))

        # -------------------------------------- #
        # synonyms
        # -------------------------------------- #
        label_antonym = tk.Label(self, text="antonym: ", width=9, height=1)
        label_antonym.grid(row=num_meaning + 6, column=0)
        antonym_text = tk.Text(self, height=1, width=20)
        antonym_text.grid(row=num_meaning + 6, column=1, sticky="w")
        antonym_text.bind("<KeyRelease>",
                          lambda event, text_box=antonym_text: self.update_text_height(text_box, event))

        self.component.append({'pos_entry': pos_entry,
                               'meaning_entry': meaning_entry,
                               'example_text': example_text,
                               'derivative_text': derivative_text,
                               'synonyms_text': synonyms_text,
                               'antonym_text': antonym_text,
                               'label_pos': label_pos,
                               'label_meaning': label_meaning,
                               'label_example': label_example,
                               'label_derivative': label_derivative,
                               'label_synonyms': label_synonyms,
                               'label_antonym': label_antonym})

        self.label_similarWords.grid(row=num_meaning + 7, column=0)
        self.similarWords_text.grid(row=num_meaning + 7, column=1, sticky="w")
        self.update()

    def update_text_height(self, text_box, event):
        # 获取文本框的行数（按换行符分割文本）
        lines = text_box.get("1.0", "end-1c").split("\n")
        num_lines = len(lines)

        # 设置文本框的高度，最小高度为4行
        new_height = max(num_lines, 1)
        # 更新grid布局的行高度
        text_box.config(height=new_height)

    def insert(self):
        word = self.word_entry.get()
        for num_meaning in range(len(self.component)):
            pos = self.component[num_meaning]['pos_entry'].get()
            meaning = self.component[num_meaning]['meaning_entry'].get()
            example = self.component[num_meaning]['example_text'].get("1.0", "end")
            example = [line.strip() for line in example.split('\n') if line.strip()]
            derivative = self.component[num_meaning]['derivative_text'].get("1.0", "end")
            derivative = [line.strip() for line in derivative.split('\n') if line.strip()]
            synonyms = self.component[num_meaning]['synonyms_text'].get("1.0", "end")
            synonyms = [line.strip() for line in synonyms.split('\n') if line.strip()]
            antonym = self.component[num_meaning]['antonym_text'].get("1.0", "end")
            antonym = [line.strip() for line in antonym.split('\n') if line.strip()]
            similarWords = self.similarWords_text.get("1.0", "end")
            similarWords = [line.strip() for line in similarWords.split('\n') if line.strip()]

            print(word + ' ' + pos + ' ' + meaning)
            print(example)
            print(derivative)
            print(synonyms)
            print(antonym)
            print(similarWords)

            insert(conn=conn,
                   word=word,
                   pos=pos,
                   meaning=meaning,
                   example=example,
                   derivative=derivative,
                   synonyms=synonyms,
                   antonym=antonym,
                   similarWords=similarWords)

    def show_word(self, conn, word):
        self.clear()
        word_list = show_word(conn, word)
        print(word_list)
        # word = word_list[0]['word']
        similarWords = word_list[-1]
        similarWords = '\n'.join([item[0] for item in similarWords])
        self.word_entry.insert(0, word)
        for num_meaning in range(len(word_list) - 1):
            if num_meaning > 0:
                self.add_meaning_box()
            pos = word_list[num_meaning]['pos']
            meaning = word_list[num_meaning]['meaning']
            example = word_list[num_meaning]['example']
            example = '\n'.join([item[0] for item in example])
            derivative = word_list[num_meaning]['derivative']
            derivative = '\n'.join([item[0] for item in derivative])
            synonyms = word_list[num_meaning]['synonyms']
            synonyms = '\n'.join([item[0] for item in synonyms])
            antonym = word_list[num_meaning]['antonym']
            antonym = '\n'.join([item[0] for item in antonym])

            self.component[num_meaning]['pos_entry'].delete(0, tk.END)
            self.component[num_meaning]['pos_entry'].insert(0, pos)

            self.component[num_meaning]['meaning_entry'].delete(0, tk.END)
            self.component[num_meaning]['meaning_entry'].insert(0, meaning)

            self.component[num_meaning]['example_text'].delete("1.0", tk.END)
            self.component[num_meaning]['example_text'].insert("1.0", example)
            self.update_text_height(self.component[num_meaning]['example_text'], None)

            self.component[num_meaning]['derivative_text'].delete("1.0", tk.END)
            self.component[num_meaning]['derivative_text'].insert("1.0", derivative)
            self.update_text_height(self.component[num_meaning]['derivative_text'], None)

            self.component[num_meaning]['synonyms_text'].delete("1.0", tk.END)
            self.component[num_meaning]['synonyms_text'].insert("1.0", synonyms)
            self.update_text_height(self.component[num_meaning]['synonyms_text'], None)

            self.component[num_meaning]['antonym_text'].delete("1.0", tk.END)
            self.component[num_meaning]['antonym_text'].insert("1.0", antonym)
            self.update_text_height(self.component[num_meaning]['antonym_text'], None)

        self.similarWords_text.delete("1.0", tk.END)
        self.similarWords_text.insert("1.0", similarWords)
        self.update_text_height(self.similarWords_text, None)

    def clear(self):
        print(self.component)
        self.word_entry.delete(0, tk.END)
        self.similarWords_text.delete("1.0", tk.END)
        for num_meaning in range(len(self.component)):
            for key in self.component[num_meaning].keys():
                self.component[num_meaning][key].destroy()
        self.component = []
        self.add_meaning_box()


if __name__ == '__main__':
    conn = connect()

    root = tk.Tk()
    # 设置title
    root.title("GUI")
    # 设置大小及位置
    root.geometry('500x720+500+50')

    app = Application(master=root)
    root.mainloop()
