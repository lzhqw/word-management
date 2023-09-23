import tkinter as tk

# 初始字典
word_dict = {"word": "abc", "meaning": "def"}

# 函数用于更新字典中的单词和意思，并将值返回给终端
def update_word_meaning():
    new_word = word_entry.get()
    new_meaning = meaning_entry.get()
    word_dict["word"] = new_word
    word_dict["meaning"] = new_meaning
    print("更新后的字典：", word_dict)

root = tk.Tk()
root.title("可编辑单词与意思")

word_label = tk.Label(root, text="Word:")
word_label.pack()

word_entry = tk.Entry(root)
word_entry.insert(0, word_dict["word"])
word_entry.pack()

meaning_label = tk.Label(root, text="Meaning:")
meaning_label.pack()

meaning_entry = tk.Entry(root)
meaning_entry.insert(0, word_dict["meaning"])
meaning_entry.pack()

update_button = tk.Button(root, text="更新并输出", command=update_word_meaning)
update_button.pack()

root.mainloop()
