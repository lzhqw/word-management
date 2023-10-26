import time
import tkinter as tk
from sql_func import *
import tkinter.font as tkFont
from tkinter import Menu
from pronunciation import pronounce_word, quit_prononciation


class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.connect()
        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self.quit_)
        self.pack()
        self.component = []
        self.create_menu()
        self.createWidget()
        self.first = True

    def connect(self):
        self.conn = connect_to_mysql()

    def create_menu(self):
        """
        创建菜单栏
        :return:
        """

        def edit():
            """
            跳转到编辑界面
            :return:
            """
            self.clear_frame()
            self.createWidget()

        def review_all():
            """
            跳转到复习界面
            :return:
            """
            self.cnt = 0
            self.word_list = get_review_word_list(conn=self.conn, type='all')
            self.clear_frame()
            self.createreviewWidget(word=self.word_list[self.cnt], detail=False)

        def review_forget():
            self.cnt = 0
            self.word_list = load_word_book()[200:250]
            random.shuffle(self.word_list)
            print(len(self.word_list))
            self.clear_frame()
            self.createreviewWidget(word=self.word_list[self.cnt], detail=False)

        def review_order_by_forget_rate():
            self.cnt = 0
            self.word_list = get_review_word_list(conn=self.conn, type='oderByForgetRate')
            print(len(self.word_list))
            self.clear_frame()
            self.createreviewWidget(word=self.word_list[self.cnt], detail=False)

        menu_bar = Menu(self.master)
        self.master.config(menu=menu_bar)
        file_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Connect", command=self.connect)
        file_menu.add_command(label="Edit", command=edit)
        file_menu.add_command(label="Review", command=self.review)
        file_menu.add_command(label="Review Forget", command=review_forget)
        file_menu.add_command(label="按照记错比例复习", command=review_order_by_forget_rate)
        file_menu.add_command(label="导出今日记错单词", command=lambda conn=self.conn: get_today_forget_word_list(conn))
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit_)

    def quit_(self):
        quit_prononciation()
        self.master.quit()

    def createWidget(self):
        # word
        self.label_word = tk.Label(self, text="word: ", width=6, height=1, font=font_en)
        self.label_word.grid(row=0, column=0)
        self.word_entry = tk.Entry(self, font=font_en)
        self.word_entry.grid(row=0, column=1, sticky="w")
        self.word_entry.bind("<Return>", lambda event: self.show_word(self.conn, self.word_entry.get()))
        self.word_entry.bind("<Tab>", self.focus_next_widget_for_word)

        # -------------------------------------- #
        # similarWords
        # -------------------------------------- #
        self.label_similarWords = tk.Label(self, text="similar words: ", width=15, height=1, font=font_en)
        self.label_similarWords.grid(row=7, column=0)
        self.similarWords_text = tk.Text(self, height=1, width=20, font=font_en)
        self.similarWords_text.grid(row=7, column=1, sticky="w")
        self.similarWords_text.bind("<KeyRelease>",
                                    lambda event, text_box=self.similarWords_text: self.update_text_height(text_box,
                                                                                                           event))
        self.similarWords_text.bind("<Tab>", self.focus_next_widget)
        self.add_meaning_box()

        # -------------------------------------- #
        # 按钮：insert
        # -------------------------------------- #
        self.button_insert = tk.Button(self, text="insert", command=self.insert, font=font_en)
        self.button_insert.grid(row=0, column=2)

        # -------------------------------------- #
        # 按钮：add meaning
        # -------------------------------------- #
        self.button_insert = tk.Button(self, text="add meaning", command=self.add_meaning_box, font=font_en)
        self.button_insert.grid(row=1, column=2)

        # -------------------------------------- #
        # 按钮：clear
        # -------------------------------------- #
        self.button_clear = tk.Button(self, text="clear", command=self.clear, font=font_en)
        self.button_clear.grid(row=2, column=2)

        # -------------------------------------- #
        # 按钮：update_meaning
        # -------------------------------------- #
        self.button_update_meaning = tk.Button(self, text="update meaning", command=self.update_meaning, font=font_en)
        self.button_update_meaning.grid(row=3, column=2)

        # -------------------------------------- #
        # 按钮：get_word_book
        # -------------------------------------- #
        self.button_get_word_book = tk.Button(self, text="导出单词",
                                              command=lambda conn=self.conn: get_word_book(conn=conn),
                                              font=font_cn)
        self.button_get_word_book.grid(row=4, column=2)

    def add_meaning_box(self):
        """
        添加meaning box
        一个单词的组成是一个word+若干meaning box + 一个 similar word
        meaning box中包含单词的词性，含义，衍生词，同义词，例句，反义词
        :return:
        """
        num_meaning = 6 * len(self.component)
        # -------------------------------------- #
        # pos
        # -------------------------------------- #
        label_pos = tk.Label(self, text="pos: ", width=5, height=1, font=font_en)
        label_pos.grid(row=num_meaning + 1, column=0)
        pos_entry = tk.Entry(self, font=font_en)
        pos_entry.grid(row=num_meaning + 1, column=1, sticky="w")
        pos_entry.bind("<Tab>", self.focus_next_widget)

        # -------------------------------------- #
        # meaning
        # -------------------------------------- #
        label_meaning = tk.Label(self, text="meaning: ", width=9, height=1, font=font_en)
        label_meaning.grid(row=num_meaning + 2, column=0)
        meaning_entry = tk.Entry(self, font=font_cn)
        meaning_entry.grid(row=num_meaning + 2, column=1, sticky="w")
        meaning_entry.bind("<Tab>", self.focus_next_widget)

        # -------------------------------------- #
        # example
        # -------------------------------------- #
        label_example = tk.Label(self, text="example: ", width=9, height=1, font=font_en)
        label_example.grid(row=num_meaning + 3, column=0)
        example_text = tk.Text(self, height=1, width=20, font=font_en)
        example_text.grid(row=num_meaning + 3, column=1, sticky="w")
        example_text.bind("<KeyRelease>",
                          lambda event, text_box=example_text: self.update_text_height(text_box, event))
        example_text.bind("<Tab>", self.focus_next_widget)

        # -------------------------------------- #
        # derivative
        # -------------------------------------- #
        label_derivative = tk.Label(self, text="derivative: ", width=12, height=1, font=font_en)
        label_derivative.grid(row=num_meaning + 4, column=0)
        derivative_text = tk.Text(self, height=1, width=20, font=font_en)
        derivative_text.grid(row=num_meaning + 4, column=1, sticky="w")
        derivative_text.bind("<KeyRelease>",
                             lambda event, text_box=derivative_text: self.update_text_height(text_box, event))
        derivative_text.bind("<Tab>", self.focus_next_widget)

        # -------------------------------------- #
        # synonyms
        # -------------------------------------- #
        label_synonyms = tk.Label(self, text="synonyms: ", width=10, height=1, font=font_en)
        label_synonyms.grid(row=num_meaning + 5, column=0)
        synonyms_text = tk.Text(self, height=1, width=20, font=font_en)
        synonyms_text.grid(row=num_meaning + 5, column=1, sticky="w")
        synonyms_text.bind("<KeyRelease>",
                           lambda event, text_box=synonyms_text: self.update_text_height(text_box, event))
        synonyms_text.bind("<Tab>", self.focus_next_widget)

        # -------------------------------------- #
        # synonyms
        # -------------------------------------- #
        label_antonym = tk.Label(self, text="antonym: ", width=9, height=1, font=font_en)
        label_antonym.grid(row=num_meaning + 6, column=0)
        antonym_text = tk.Text(self, height=1, width=20, font=font_en)
        antonym_text.grid(row=num_meaning + 6, column=1, sticky="w")
        antonym_text.bind("<KeyRelease>",
                          lambda event, text_box=antonym_text: self.update_text_height(text_box, event))
        antonym_text.bind("<Tab>", self.focus_next_widget)

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

    def review(self, next=True):
        get_today_forget_word_list(self.conn)
        if self.first:
            self.cnt1 = 0
            self.cnt = 0
            self.all_word_list = get_review_word_list(conn=self.conn, type='ForgetAndForgetRate')
            self.word_list = self.all_word_list[self.cnt1:self.cnt1 + 10]
            self.first = False
        else:
            if next:
                get_today_forget_word_list(self.conn)
                self.cnt1 += 10
                print(self.cnt1)
                self.word_list = self.all_word_list[self.cnt1:self.cnt1 + 10]
                print(self.word_list)
            else:
                pass

            self.cnt = 0
        self.clear_frame()
        self.createreviewWidget(word=self.word_list[self.cnt], detail=False)

    def next(self):
        self.cnt += 1
        if self.cnt == len(self.word_list):
            self.createreviewWidget(word=None, detail=False)
        else:
            self.createreviewWidget(word=self.word_list[self.cnt], detail=False)

    def createreviewWidget(self, word, detail=False):
        self.clear_frame()
        # self.unbind()
        if detail:
            self.label_word = tk.Label(self, text="word: ", width=6, height=1, font=font_en)
            self.label_word.grid(row=0, column=0)
            self.word_entry = tk.Entry(self, font=font_en)
            self.word_entry.grid(row=0, column=1, sticky="w")
            # self.word_entry.bind("<Return>", lambda event: self.show_word(self.conn, self.word_entry.get()))
            # self.word_entry.bind("<Tab>", self.focus_next_widget_for_word)

            # -------------------------------------- #
            # similarWords
            # -------------------------------------- #
            self.label_similarWords = tk.Label(self, text="similar words: ", width=15, height=1, font=font_en)
            self.label_similarWords.grid(row=7, column=0)
            self.similarWords_text = tk.Text(self, height=1, width=20, font=font_en)
            self.similarWords_text.grid(row=7, column=1, sticky="w")
            self.similarWords_text.bind("<KeyRelease>",
                                        lambda event, text_box=self.similarWords_text: self.update_text_height(text_box,
                                                                                                               event))
            self.similarWords_text.bind("<Tab>", self.focus_next_widget)
            self.add_meaning_box()
            self.button_remember = tk.Button(self, text="记住了", command=self.remember,
                                             font=font_cn)
            self.button_remember.grid(row=0, column=2)

            self.button_forgot = tk.Button(self, text="忘了", command=self.forgot, font=font_cn)
            self.button_forgot.grid(row=1, column=2)

            self.button_next = tk.Button(self, text="Next", command=self.next, font=font_en)
            self.button_next.grid(row=2, column=2)
            self.unbind("<Return>")
            self.focus_set()
            self.bind("<Return>", lambda event: self.next())
            self.bind("<space>", lambda event: self.remember())
            self.bind("<f>", lambda event: self.forgot())
            print(self.cnt, len(self.word_list))
            self.show_word(conn=self.conn, word=word)
            self.update()
        else:
            if self.cnt == len(self.word_list):
                self.button_next_iter = tk.Button(self, text="下一轮", command=self.review, font=font_cn)
                self.button_retry = tk.Button(self, text="继续复习当前单词", command=lambda: self.review(False),
                                              font=font_cn)
                self.button_next_iter.pack()
                self.button_retry.pack()
                already_review_num = get_today_already_review_num(conn=self.conn)
                already_review_num_label = tk.Label(self, text=str(already_review_num), font=font_en)
                already_review_num_label.pack()
            else:
                word_label = tk.Label(self, text=word, font=font_en)
                word_label.pack(pady=20)
                word_label.bind("<Button-1>", lambda event, word=word: self.createreviewWidget(word, True))
                self.focus_set()
                self.bind("<Return>", lambda event, word=word: self.createreviewWidget(word, True))
                cnt_label = tk.Label(self, text=f'{self.cnt + 1}/{len(self.word_list)}')
                cnt_label.pack(pady=20)
                self.update()
                pronounce_word(word)

    def remember(self):
        word = self.word_entry.get()
        review_remember(conn=self.conn, word=word)
        self.next()

    def forgot(self):
        word = self.word_entry.get()
        review_forget(conn=self.conn, word=word)
        self.next()

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
            if pos == 'p':
                pos = 'phrase'
            assert pos in ['n', 'v', 'adj', 'adv', 'prep', 'phrase', 'conj']
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

            insert(conn=self.conn,
                   word=word,
                   pos=pos,
                   meaning=meaning,
                   example=example,
                   derivative=derivative,
                   synonyms=synonyms,
                   antonym=antonym,
                   similarWords=similarWords)
        time.sleep(0.1)
        self.clear()

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
        self.word_entry.delete(0, tk.END)
        self.similarWords_text.delete("1.0", tk.END)
        self.update_text_height(self.similarWords_text, None)
        for num_meaning in range(len(self.component)):
            for key in self.component[num_meaning].keys():
                self.component[num_meaning][key].destroy()
        self.component = []
        self.add_meaning_box()

    def clear_frame(self):
        # 清空 frame
        for widget in self.winfo_children():
            widget.destroy()
        self.component = []

    def update_meaning(self):
        word = self.word_entry.get()
        word_list = show_word(conn=self.conn, word=word)
        for num_meaning in range(len(self.component)):
            old_meaning = word_list[num_meaning]['meaning']
            meaning = self.component[num_meaning]['meaning_entry'].get()
            print(old_meaning, meaning)
            update_meaning(conn=self.conn, word=word, meaning=old_meaning, new_meaning=meaning)

    def focus_next_widget(self, event):
        current_widget = event.widget
        current_info = current_widget.grid_info()
        row = current_info['row']
        widgets = self.grid_slaves(column=1)
        for widget in widgets:
            info = widget.grid_info()
            if info['row'] == (row + 1) % len(widgets):
                widget.focus_set()
                break

        return "break"

    def focus_next_widget_for_word(self, event):
        self.show_word(self.conn, self.word_entry.get())
        widgets = self.grid_slaves(column=1)
        for widget in widgets:
            info = widget.grid_info()
            if info['row'] == 1:
                widget.focus_set()
                break

        return "break"


if __name__ == '__main__':
    root = tk.Tk()
    # 设置字体
    font_en = tkFont.Font(family="Californian FB", size=16)
    font_cn = tkFont.Font(family="华光小标宋", size=16)
    # 设置title
    root.title("GUI")
    # 设置大小及位置
    root.geometry('700x600+500+50')

    app = Application(master=root)
    root.mainloop()
