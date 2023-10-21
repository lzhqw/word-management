import random
from datetime import datetime, timedelta
import pymysql
import pandas as pd
import numpy as np
from pymysql.err import IntegrityError


def connect():
    DBHOST = 'localhost'
    DBUSER = 'root'
    DBPASS = '123456'
    DBNAME = 'dbwords'
    conn = pymysql.connect(host=DBHOST,
                           user=DBUSER,
                           password=DBPASS,
                           database=DBNAME
                           )
    return conn


def initialize_database(conn):
    """
    表1：
    """
    with open("dbwords - 副本.sql") as file:
        raw_sql = file.readlines()
        raw_sql = "".join(sql for sql in raw_sql)
    print(raw_sql)
    sql_statements = [statement.strip() for statement in raw_sql.strip().split(';') if statement.strip()]
    print(sql_statements)
    cursor = conn.cursor()
    for sql_statement in sql_statements:
        print(sql_statement)
        cursor.execute(sql_statement)
    conn.commit()
    cursor.close()


def get_select_sql(table, col):
    if isinstance(col, (list, tuple)):
        sql = f"SELECT * FROM {table} WHERE " + " =%s AND ".join(col for col in col) + " =%s"
    else:
        sql = f"SELECT * FROM {table} WHERE {col} = %s;"
    return sql


def get_insert_sql(table, col):
    if isinstance(col, (list, tuple)):
        sql = (f"INSERT INTO {table} (" + ",".join(i for i in col) +
               ") VALUES (" + ",".join("%s" for i in col)) + ')'
    else:
        sql = f"INSERT INTO {table} ({col}) VALUES (%s)"
    return sql


def insert_(conn, table_name, col_name, value, lastrowId=False):
    # step1. 查找是否存在
    cursor = conn.cursor()
    sql = get_select_sql(table_name, col_name)
    cursor.execute(sql, value)
    result = cursor.fetchone()
    if result:
        if lastrowId:
            return result[0]
        else:
            return value
    else:
        sql = get_insert_sql(table_name, col_name)
        cursor.execute(sql, value)
        conn.commit()
        if lastrowId:
            return cursor.lastrowid
        else:
            return value


def multiple_insert_rel(conn, words: (list, tuple), table, col, rel_table, rel_col, rel_value):
    for word in words:
        insert_(conn=conn, table_name=table, col_name=col, value=word)
        insert_(conn=conn, table_name=rel_table,
                col_name=rel_col,
                value=(rel_value, word))


def multiple_insert_simmilarWords(conn, words: (list, tuple), value):
    for word in words:
        insert_(conn=conn, table_name='words', col_name='word', value=word)
        cursor = conn.cursor()
        sql = get_select_sql('relSimilarWords', ('word', 'similarWord'))
        cursor.execute(sql, (word, value))
        result1 = cursor.fetchone()
        sql = get_select_sql('relSimilarWords', ('similarWord', 'word'))
        cursor.execute(sql, (word, value))
        result2 = cursor.fetchone()

        if result1 or result2:
            pass
        else:
            sql = get_insert_sql('relSimilarWords', ('word', 'similarWord'))
            cursor.execute(sql, (word, value))
            conn.commit()


def insert(conn, word, pos, meaning, example, derivative, synonyms, antonym, similarWords):
    insert_(conn=conn, table_name='words', col_name='word', value=word)
    insert_(conn=conn, table_name='pos', col_name='POS', value=pos)
    meaningId = insert_(conn=conn, table_name='meanings', col_name='meaning', value=meaning)
    wordMeaningId = insert_(conn=conn,
                            table_name='relWordMeaning',
                            col_name=('word', 'pos', 'meaning'),
                            value=(word, pos, meaningId),
                            lastrowId=True)
    # step5. 插入example并关联relExample表
    multiple_insert_rel(conn=conn,
                        words=example,
                        table='examples',
                        col='example',
                        rel_table='relExample',
                        rel_col=('relWordMeaningId', 'example'),
                        rel_value=wordMeaningId)

    multiple_insert_rel(conn=conn,
                        words=derivative,
                        table='words',
                        col='word',
                        rel_table='relDerivative',
                        rel_col=('relWordMeaningId', 'derivative'),
                        rel_value=wordMeaningId)

    # step7. 关联同义词表
    multiple_insert_rel(conn=conn,
                        words=synonyms,
                        table='words',
                        col='word',
                        rel_table='relSynonyms',
                        rel_col=('relWordMeaningId', 'synonyms'),
                        rel_value=wordMeaningId)

    # step8. 关联反义词表
    multiple_insert_rel(conn=conn,
                        words=antonym,
                        table='words',
                        col='word',
                        rel_table='relAntonym',
                        rel_col=('relWordMeaningId', 'antonym'),
                        rel_value=wordMeaningId)
    # step9. 关联形近词表
    multiple_insert_simmilarWords(conn=conn,
                                  words=similarWords,
                                  value=word)


def get_words(conn, table, col, select_col, value):
    sql = f"SELECT {col} FROM {table} WHERE {select_col} = %s"
    cursor = conn.cursor()
    cursor.execute(sql, value)
    results = cursor.fetchall()
    return results


def get_meaning_result(conn, word):
    sql = "SELECT relWordMeaningId, meaning, pos FROM relWordMeaning WHERE word = %s"
    cursor = conn.cursor()
    cursor.execute(sql, word)
    results = cursor.fetchall()
    return results


def show_word(conn, word, file_path=None):
    word_dict_list = []
    output_list = []

    def print_and_save(s):
        print(s)
        if file_path:
            output_list.append(s)

    print_and_save('-' * 70)
    print_and_save(word)
    print_and_save('-' * 70)

    results = get_meaning_result(conn, word)
    for i, result in enumerate(results):
        relWordMeaningId, meaning, pos = result
        example = get_words(conn=conn,
                            table='relExample',
                            col='example',
                            select_col='relWordMeaningId',
                            value=relWordMeaningId)
        derivative = get_words(conn=conn,
                               table='relDerivative',
                               col='derivative',
                               select_col='relWordMeaningId',
                               value=relWordMeaningId)
        synonyms = get_words(conn=conn,
                             table='relSynonyms',
                             col='synonyms',
                             select_col='relWordMeaningId',
                             value=relWordMeaningId)
        antonym = get_words(conn=conn,
                            table='relAntonym',
                            col='antonym',
                            select_col='relWordMeaningId',
                            value=relWordMeaningId)

        print_and_save(f'  {i + 1}. {pos}.{meaning}')
        if len(example) != 0:
            print_and_save('    --example')
        for w in example:
            print_and_save(f'        {w[0]}')
        if len(derivative) != 0:
            print_and_save('    --derivative')
        for w in derivative:
            print_and_save(f'        {w[0]}')
        if len(synonyms) != 0:
            print_and_save('    --synonyms')
        for w in synonyms:
            print_and_save(f'        {w[0]}')
        if len(antonym) != 0:
            print_and_save('    --antonym')
        for w in antonym:
            print_and_save(f'        {w[0]}')
        print_and_save('-' * 70)

        word_dict_list.append({'word': word,
                               'pos': pos,
                               'meaning': meaning,
                               'example': example,
                               'derivative': derivative,
                               'synonyms': synonyms,
                               'antonym': antonym})

    similarWords1 = get_words(conn=conn,
                              table='relSimilarWords',
                              col='similarWord',
                              select_col='word',
                              value=word)
    similarWords2 = get_words(conn=conn,
                              table='relSimilarWords',
                              col='word',
                              select_col='similarWord',
                              value=word)
    if len(similarWords1 + similarWords2) != 0:
        print_and_save('    --similar words')
    for w in similarWords1 + similarWords2:
        print_and_save(f'        {w[0]}')

    word_dict_list.append(similarWords1 + similarWords2)

    if file_path:
        with open(file_path, 'a') as f:
            f.write('\n'.join(output_list))

    return word_dict_list


def supplement(conn):
    sql = "SELECT w.word FROM words w LEFT JOIN relWordMeaning rwm ON w.word = rwm.word WHERE rwm.word IS NULL;"
    cursor = conn.cursor()
    cursor.execute(sql)
    results = cursor.fetchall()
    for result in results:
        print(result)


def update_word(conn, word, new_word):
    cursor = conn.cursor()
    # step1. 在words表中新增words
    sql = "SELECT * FROM words WHERE word = %s"
    cursor.execute(sql, new_word)
    result = cursor.fetchone()
    if not result:
        sql = "INSERT INTO words(word) VALUES (%s)"
        cursor.execute(sql, new_word)
        conn.commit()
    for table, col in [('relWordMeaning', 'word'),
                       ('relSynonyms', 'synonyms'),
                       ('relDerivative', 'derivative'),
                       ('relAntonym', 'antonym'),
                       ('relSimilarWords', 'word'),
                       ('relSimilarWords', 'similarWord')]:
        sql = f"UPDATE {table} SET {col} = %s WHERE {col} = %s"
        cursor.execute(sql, (new_word, word))
    conn.commit()
    sql = "DELETE FROM words WHERE word = %s"
    cursor.execute(sql, word)
    conn.commit()


def update_meaning(conn, word, meaning, new_meaning):
    if meaning == new_meaning:
        return
    cursor = conn.cursor()
    # step1. 在words表中新增words
    sql = "SELECT * FROM meanings WHERE meaning = %s"
    cursor.execute(sql, new_meaning)
    result = cursor.fetchall()
    if not result:
        sql = "INSERT INTO meanings(meaning) VALUES (%s)"
        cursor.execute(sql, new_meaning)
        conn.commit()

    sql = f"UPDATE relWordMeaning SET meaning = %s WHERE word=%s and meaning = %s"
    cursor.execute(sql, (new_meaning, word, meaning))
    conn.commit()
    # 考虑到一个意思可能多用，因此如果有多个词使用同一个意思的时候，仅更改当前意思
    sql = "SELECT * FROM relWordMeaning WHERE meaning = %s"
    cursor.execute(sql, meaning)
    result = cursor.fetchall()
    if len(result) == 0:
        sql = "DELETE FROM meanings WHERE meaning = %s"
        cursor.execute(sql, meaning)
        conn.commit()


def input_from_console(conn, mode='insert'):
    word = input("word: ")
    word_dict_list = show_word(conn=conn, word=word)
    print(word_dict_list)


def get_word_book(conn, sql="SELECT DISTINCT word FROM relWordMeaning WHERE pos != 'phrase'"):
    # sql = "SELECT DISTINCT word FROM relWordMeaning WHERE pos != 'phrase'"
    cursor = conn.cursor()
    cursor.execute(sql)
    results = cursor.fetchall()
    results = [item[0] for item in results]
    random.shuffle(results)

    with open('words.txt', 'w') as f:
        for word in results:
            f.write(word + '\n')
    return results


def review_remember(conn, word):
    # 验证一下word是否存在
    cursor = conn.cursor()
    sql = "SELECT word FROM words WHERE word = %s"
    cursor.execute(sql, word)
    result = cursor.fetchone()
    if result:
        # 先获取一下review times
        sql = "SELECT review_times FROM words WHERE word = %s"
        cursor.execute(sql, word)
        review_times = cursor.fetchone()[0]
        review_times = review_times + 1 if review_times else 1
        # 获取一下当前日期
        today = get_date()
        # today = '2023-10-11'
        # 获取一下连续记住了多少次
        sql = "SELECT continuous_remember_count FROM words WHERE word = %s"
        cursor.execute(sql, word)
        continuous_remember_count = cursor.fetchone()[0]
        continuous_remember_count = continuous_remember_count + 1 if continuous_remember_count else 1

        sql = "UPDATE words SET last_review_date=%s,review_times=%s,continuous_remember_count=%s WHERE word=%s "
        cursor.execute(sql, (today, review_times, continuous_remember_count, word))
        conn.commit()
    else:
        raise Exception("单词不存在")


def review_forget(conn, word):
    # 验证一下word是否存在
    cursor = conn.cursor()
    sql = "SELECT word FROM words WHERE word = %s"
    cursor.execute(sql, word)
    result = cursor.fetchone()
    if result:
        # 先获取一下review times
        sql = "SELECT review_times FROM words WHERE word = %s"
        cursor.execute(sql, word)
        review_times = cursor.fetchone()[0]
        review_times = review_times + 1 if review_times else 1
        # 再获取一下forget times
        sql = "SELECT forget_times FROM words WHERE word = %s"
        cursor.execute(sql, word)
        forget_times = cursor.fetchone()[0]
        forget_times = forget_times + 1 if forget_times else 1
        # 获取一下当前日期
        today = get_date()
        # today = '2023-10-11'
        sql = "UPDATE words SET last_review_date=%s,review_times=%s,continuous_remember_count=%s,forget_times=%s WHERE word=%s"
        cursor.execute(sql, (today, review_times, 0, forget_times, word))
        conn.commit()
    else:
        raise Exception("单词不存在")


def get_review_word_list(conn, type='all'):
    cursor = conn.cursor()
    today = get_date()
    if type == 'all':
        sql = "SELECT DISTINCT word FROM relWordMeaning"
        cursor.execute(sql)
        results = cursor.fetchall()
        results = [item[0] for item in results]
        random.shuffle(results)
    elif type == 'oderByForgetRate':
        sql = ("SELECT DISTINCT words.word,words.review_times, "
               "CASE "
               "WHEN COALESCE(review_times, 0) = 0 THEN 1 "
               "ELSE CAST(forget_times AS FLOAT) / review_times "
               "END AS forget_rate "
               "FROM relWordMeaning "
               "JOIN words ON relWordMeaning.word = words.word "
               "WHERE last_review_date IS NULL "
               "OR last_review_date != %s "
               "ORDER BY forget_rate DESC, review_times ASC;")
        cursor.execute(sql, today)
        results = cursor.fetchall()
        df = pd.DataFrame(results, columns=['word', 'review_times', 'forget_rate'])
        df['forget_rate'] = df['forget_rate'].fillna(0)
        df['review_times'] = df['review_times'].fillna(0)
        np.random.seed(0)

        # 对每个 forget_rate 层级随机打乱单词
        shuffled_df = df.sample(frac=1).reset_index(drop=True)

        # 将打乱的数据合并回一个 DataFrame
        sorted_df = shuffled_df.sort_values(by=['forget_rate', 'review_times'], ascending=[False, True]).reset_index(
            drop=True)
        sorted_df.to_csv('./log/temp.csv')
        sorted_df = list(sorted_df.itertuples(index=False, name=None))
        results = [item[0] for item in sorted_df]
        print(results)

    else:
        today = '2023-10-07'
        sql = ("SELECT DISTINCT words.word"
               " FROM relWordMeaning, words "
               "WHERE relWordMeaning.word = words.word "
               "AND (last_review_date != %s OR last_review_date IS NULL)")
        cursor.execute(sql, today)
        results = cursor.fetchall()
        results = [item[0] for item in results]
        random.shuffle(results)

    return results


def get_today_forget_word_list(conn):
    today = get_date()
    sql = 'SELECT word FROM words WHERE last_review_date=%s AND continuous_remember_count=0'
    cursor = conn.cursor()
    cursor.execute(sql, today)
    results = cursor.fetchall()
    results = [item[0] for item in results]

    # 获取已经写入文件的单词
    file_path = f'./log/{today}.txt'
    existing_words = set()
    try:
        with open(file_path, 'r') as f:
            existing_words = set(f.read().splitlines())
    except FileNotFoundError:
        pass  # 文件不存在，可以忽略

    # 过滤掉已经存在于文件中的单词
    words_to_write = [word for word in results if word not in existing_words]

    # 将新单词写入文件
    with open(file_path, 'a') as f:
        for word in words_to_write:
            f.write(word + '\n')

    return words_to_write


def load_word_book():
    with open('words.txt') as f:
        word_list = f.readlines()
        word_list = [w.replace('\n', '') for w in word_list]
    return word_list


def delete_meaning(conn, word, meaning):
    cursor = conn.cursor()

    sql = 'DELETE FROM relWordMeaning WHERE word=%s AND meaning=%s'
    cursor.execute(sql, (word, meaning))
    sql = 'DELETE FROM meanings WHERE meaning=%s'
    cursor.execute(sql, meaning)
    conn.commit()


def clear_review_data(conn):
    sql = 'UPDATE words SET last_review_date=NULL, review_times=NULL, forget_times=NULL'
    cursor = conn.cursor()
    cursor.execute(sql)
    conn.commit()


def get_date():
    now = datetime.now()
    hour = now.hour
    if 0 <= hour < 6:
        date = now - timedelta(days=1)
    else:
        date = now
    return date.strftime('%Y-%m-%d')
