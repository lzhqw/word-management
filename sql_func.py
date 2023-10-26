import random
from datetime import datetime, timedelta
import pymysql
import pandas as pd
import numpy as np
from pymysql.err import IntegrityError
import os
import json
from typing import Union, List, Tuple, Any


def connect_to_mysql():
    """
    连接到MySQL数据库
    :return: 数据库连接对象
    """
    with open('db_config.json', 'r') as f:
        config = json.load(f)

    DBHOST = config['host']
    DBUSER = config['user']
    DBPASS = config['password']
    DBNAME = config['database']

    try:
        conn = pymysql.connect(
            host=DBHOST,
            user=DBUSER,
            password=DBPASS,
            database=DBNAME
        )
        return conn
    except pymysql.MySQLError as e:
        print(f"Error while connecting to MySQL: {e}")
        return None


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


def generate_select_sql(table: str, col: Union[str, List[str], Tuple[str, ...]]) -> str:
    """
    生成SELECT SQL查询语句。
    :param table: 表名
    :param col: 列名，可以是单个列名的字符串或多个列名组成的列表/元组
    :return: SQL查询语句
    """
    if isinstance(col, (list, tuple)):
        columns = " = %s AND ".join(col)
        sql = f"SELECT * FROM {table} WHERE {columns} = %s;"
    else:
        sql = f"SELECT * FROM {table} WHERE {col} = %s;"

    return sql


def generate_insert_sql(table: str, col: Union[str, List[str], Tuple[str, ...]]) -> str:
    """
    生成INSERT SQL语句。
    :param table: 表名
    :param col: 列名，可以是单个列名的字符串或多个列名组成的列表/元组
    :return: SQL插入语句
    """
    if isinstance(col, (list, tuple)):
        columns = ",".join(col)
        placeholders = ",".join("%s" for _ in col)
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    else:
        sql = f"INSERT INTO {table} ({col}) VALUES (%s)"

    return sql


def insert_if_not_exists(conn, table_name: str, col_name: str, value: Any, lastrowId: bool = False):
    """
       如果数据库中不存在特定值，则插入它。
       :param conn: 数据库连接
       :param table_name: 表名
       :param col_name: 列名
       :param value: 要插入或查找的值
       :param lastrowId: 是否返回最后插入行的ID
       :return: 返回查找或插入的值，如果lastrowId为True，则返回最后插入行的ID
    """
    try:
        with conn.cursor() as cursor:
            sql = generate_select_sql(table_name, col_name)
            cursor.execute(sql, value)
            result = cursor.fetchone()
            if result:
                return result[0] if lastrowId else value
            sql = generate_insert_sql(table_name, col_name)
            cursor.execute(sql, value)
            conn.commit()
            return cursor.lastrowid if lastrowId else value
    except Exception as e:
        print(f"Error occurred: {e}")
        conn.rollback()
        return None


def batch_insert_and_link(conn, items_to_insert: Union[List[str], Tuple[str]], main_table: str, main_col: str,
                          rel_table: str, rel_cols: Tuple[str, str], rel_value: Union[int, str]):
    """
    批量插入单词并建立与给定值的关联。
    :param conn: 数据库连接
    :param items_to_insert: 要插入的单词列表
    :param main_table: 主表名
    :param main_col: 主表列名
    :param rel_table: 关联表名
    :param rel_cols: 关联表列名
    :param rel_value: 用于建立关联的值
    """
    try:
        for item in items_to_insert:
            # 插入单词到主表
            insert_if_not_exists(conn=conn, table_name=main_table, col_name=main_col, value=item)

            # 插入关联信息到关联表
            insert_if_not_exists(conn=conn, table_name=rel_table, col_name=rel_cols, value=(rel_value, item))

        # 提交事务
        conn.commit()
    except Exception as e:
        print(f"Error occurred: {e}")
        conn.rollback()


def batch_insert_similar_words(conn, words: list, value: str):
    """
    在数据库中插入同义词。
    :param conn: 数据库连接对象
    :param words: 需要插入的单词列表
    :param value: 与单词列表中的单词相似的值
    :return: None
    """
    with conn.cursor() as cursor:
        for word in words:
            insert_if_not_exists(conn=conn, table_name='words', col_name='word', value=word)

            select_sql = generate_select_sql('relSimilarWords', ('word', 'similarWord'))
            cursor.execute(select_sql, (word, value))
            result_forward = cursor.fetchone()

            select_sql = generate_select_sql('relSimilarWords', ('similarWord', 'word'))
            cursor.execute(select_sql, (word, value))
            result_reverse = cursor.fetchone()

            if result_forward or result_reverse:
                continue

            insert_sql = generate_insert_sql('relSimilarWords', ('word', 'similarWord'))
            cursor.execute(insert_sql, (word, value))
            conn.commit()


def insert(conn, word, pos, meaning, example, derivative, synonyms, antonym, similarWords):
    insert_if_not_exists(conn=conn, table_name='words', col_name='word', value=word)
    insert_if_not_exists(conn=conn, table_name='pos', col_name='POS', value=pos)
    meaningId = insert_if_not_exists(conn=conn, table_name='meanings', col_name='meaning', value=meaning)
    wordMeaningId = insert_if_not_exists(conn=conn,
                                         table_name='relWordMeaning',
                                         col_name=('word', 'pos', 'meaning'),
                                         value=(word, pos, meaningId),
                                         lastrowId=True)
    # step5. 插入example并关联relExample表
    batch_insert_and_link(conn=conn,
                          items_to_insert=example,
                          main_table='examples',
                          main_col='example',
                          rel_table='relExample',
                          rel_cols=('relWordMeaningId', 'example'),
                          rel_value=wordMeaningId)

    batch_insert_and_link(conn=conn,
                          items_to_insert=derivative,
                          main_table='words',
                          main_col='word',
                          rel_table='relDerivative',
                          rel_cols=('relWordMeaningId', 'derivative'),
                          rel_value=wordMeaningId)

    # step7. 关联同义词表
    batch_insert_and_link(conn=conn,
                          items_to_insert=synonyms,
                          main_table='words',
                          main_col='word',
                          rel_table='relSynonyms',
                          rel_cols=('relWordMeaningId', 'synonyms'),
                          rel_value=wordMeaningId)

    # step8. 关联反义词表
    batch_insert_and_link(conn=conn,
                          items_to_insert=antonym,
                          main_table='words',
                          main_col='word',
                          rel_table='relAntonym',
                          rel_cols=('relWordMeaningId', 'antonym'),
                          rel_value=wordMeaningId)
    # step9. 关联形近词表
    batch_insert_similar_words(conn=conn,
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
    cursor = conn.cursor()
    sql = "SELECT word,last_review_date FROM words WHERE word = %s"
    cursor.execute(sql, word)
    result = cursor.fetchone()
    print(result[1])
    if str(result[1]) == str(get_date()):
        return
    if result:
        # 先写入到review_data
        insert_review_data(conn=conn, word=word, remember=1)
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
    # 检测一下是不是第一次复习，只有第一次复习允许写入
    cursor = conn.cursor()
    sql = "SELECT word,last_review_date FROM words WHERE word = %s"
    cursor.execute(sql, word)
    result = cursor.fetchone()
    print(result[1])
    if str(result[1]) == str(get_date()):
        return
    if result:
        # 先写入到review_data
        insert_review_data(conn=conn, word=word, remember=0)
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


def get_last_forget_words():
    today = get_date()
    today = datetime.strptime(today, '%Y-%m-%d').date()

    # 获取log文件夹中的所有文件
    log_dir = './log/'
    log_files = os.listdir(log_dir)

    # 初始化一个变量来存储找到的最近日期和对应的文件名
    latest_date = None
    latest_file = None

    # 遍历所有文件，找出离当前日期最近但不是当前日期的文件
    for file in log_files:
        # 假设文件名是日期，格式为 'YYYY-MM-DD.xxx'
        try:
            file_date_str = file.split('.')[0]  # 提取日期部分
            file_date = datetime.strptime(file_date_str, '%Y-%m-%d').date()  # 转换为日期对象
        except ValueError:
            continue  # 如果文件名不是预期格式，则跳过

        if file_date == today:
            continue  # 如果文件日期是今天，则跳过

        if latest_date is None or file_date > latest_date:
            latest_date = file_date
            latest_file = file

    if latest_file:
        return latest_file
    else:
        return None


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

    elif type == "ForgetAndForgetRate":
        """
        1.之前复习过的暂时不再复习，只复习前一天中错误的
        2.仍然是按照错误率来排序
        """
        today = get_date()
        # step1. 读取某一轮开始日期：
        with open('log/start_date.txt', 'r') as f:
            start_date = f.readline().strip()
            print(start_date)
        # step2. 判断一下这一轮有没有结束
        sql = "SELECT COUNT(*) FROM words WHERE last_review_date <=%s OR last_review_date IS NULL"
        cursor.execute(sql, start_date)
        result = cursor.fetchone()
        if result[0] == 0:
            start_date = get_date()
        sql = ("SELECT DISTINCT words.word,words.review_times, "
               "CASE "
               "WHEN COALESCE(review_times, 0) = 0 THEN 1 "
               "ELSE CAST(forget_times AS FLOAT) / review_times "
               "END AS forget_rate "
               "FROM relWordMeaning "
               "JOIN words ON relWordMeaning.word = words.word "
               "WHERE last_review_date IS NULL "
               "OR last_review_date <%s"
               "ORDER BY forget_rate DESC, review_times ASC;")

        cursor.execute(sql, start_date)
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
        latest_file = get_last_forget_words()
        print(f"上一天记错的单词文件：{latest_file}")
        with open(f'log/{latest_file}', 'r') as f:
            words_from_file = [line.strip() for line in f.readlines()]

        df_from_file = pd.DataFrame({
            'word': [],
            'review_times': [],
            'forget_rate': []
        })
        # 对每一个单词进行检查
        for word in words_from_file:
            cursor.execute("SELECT word, last_review_date FROM words WHERE word=%s", word)
            data = cursor.fetchone()
            # 如果该单词今天没有复习
            if str(data[1]) != str(today):
                new_row = pd.DataFrame({
                    'word': [word],
                    'review_times': [0],
                    'forget_rate': [0]
                })
                df_from_file = pd.concat([df_from_file, new_row], ignore_index=True)

        print(df_from_file)
        combined_df = pd.concat([df_from_file, sorted_df], ignore_index=True)
        print(combined_df)
        combined_df = list(combined_df.itertuples(index=False, name=None))
        results = [item[0] for item in combined_df]
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


def get_today_already_review_num(conn):
    today = get_date()
    sql = f"SELECT COUNT(*) FROM words WHERE last_review_date='{today}'"
    cursor = conn.cursor()
    cursor.execute(sql)
    result = cursor.fetchone()[0]
    return result


def load_word_book():
    with open('words.txt') as f:
        word_list = f.readlines()
        word_list = [w.replace('\n', '') for w in word_list]
    return word_list


def delete_meaning(conn, meaning, relWordMeaningId):
    cursor = conn.cursor()

    sql = 'DELETE FROM relWordMeaning WHERE relWordMeaningId = %s'
    cursor.execute(sql, relWordMeaningId)
    # 检查一下meaning被多少个单词用了
    sql = "SELECT COUNT(*) FROM relWordMeaning WHERE meaning = %s"
    cursor.execute(sql, meaning)
    result = cursor.fetchone()
    if result[0] == 0:
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


def delete_rel_row(conn, table, col, relWordMeaningId):
    # 先找一下同义词啊之类的
    cursor = conn.cursor()
    sql = f"SELECT {col} FROM {table} WHERE relWordMeaningId = %s"
    cursor.execute(sql, relWordMeaningId)
    results = cursor.fetchall()
    print(results)
    # 删掉所有的含有word的行
    sql = f"DELETE FROM {table} WHERE relWordMeaningId = %s"
    cursor.execute(sql, relWordMeaningId)
    conn.commit()
    # 如果同义词等没有释义，表明该次仅依赖于word，因此也删掉
    for row in results:
        sql = "SELECT COUNT(*) FROM relWordMeaning WHERE word = %s"
        cursor.execute(sql, row[0])
        result = cursor.fetchone()
        print(result)
        if result[0] == 0:
            delete_word_with_no_foreign_key(conn, row[0])
    conn.commit()


def delete_rel_example(conn, relWordMeaningId):
    cursor = conn.cursor()
    sql = f"SELECT example FROM relExample WHERE relWordMeaningId = %s"
    cursor.execute(sql, relWordMeaningId)
    results = cursor.fetchall()
    # 删掉所有的含有word的行
    sql = f"DELETE FROM relExample WHERE relWordMeaningId = %s"
    cursor.execute(sql, relWordMeaningId)
    conn.commit()
    # 如果example没在relExample出现，表明该example仅依赖于word，因此也删掉
    for row in results:
        sql = "SELECT COUNT(*) FROM relExample WHERE example = %s"
        cursor.execute(sql, row[0])
        result = cursor.fetchone()
        if result[0] == 0:
            sql = 'DELETE FROM examples WHERE example=%s'
            cursor.execute(sql, row[0])
    conn.commit()


def delete_word_with_no_foreign_key(conn, word):
    try:
        cursor = conn.cursor()
        sql = "DELETE FROM words WHERE word=%s"
        cursor.execute(sql, word)
        conn.commit()
    except Exception as e:
        print(f"{word}未删除，原因：{e}")


def delete_word(conn, word):
    """
    删除word
    :param conn:
    :param word:
    :return:
    """
    cursor = conn.cursor()
    # step1. 在relSimilarWord中删掉有word这一行
    # 检查similar_word是否在relWordMeaning中，如果不在，也删掉
    sql = "SELECT word, similarWord FROM relSimilarWords WHERE word = %s OR similarWord = %s"
    cursor.execute(sql, (word, word))
    results = cursor.fetchall()

    sql = "DELETE FROM relSimilarWords WHERE word = %s OR similarWord = %s"
    cursor.execute(sql, (word, word))
    conn.commit()
    print(results)
    for row in results:
        if word == row[0]:
            delete_word_with_no_foreign_key(conn, row[1])
        else:
            delete_word_with_no_foreign_key(conn, row[0])

    # step2. 在review_data中删掉有word这一行
    sql = "DELETE FROM review_data WHERE word = %s"
    cursor.execute(sql, word)
    conn.commit()

    # step3. 在relWordMeaning中找到id，meaning
    sql = "SELECT relWordMeaningId, meaning FROM relWordMeaning WHERE word=%s"
    cursor.execute(sql, word)
    results = cursor.fetchall()
    print(results)
    for row in results:
        meaning = row[1]
        relWordMeaningId = row[0]
        print(relWordMeaningId)
        # 在 relDerivative relSynonyms relAntonym relExample中按照id检索，删掉对应行
        # 如果对应行的另一个单词不在relWordMeaning中，则表明该单词完全依赖与被删掉的单词，因此在words中删掉
        delete_rel_row(conn, "relDerivative", "derivative", relWordMeaningId)
        delete_rel_row(conn, "relSynonyms", "synonyms", relWordMeaningId)
        delete_rel_row(conn, "relAntonym", "antonym", relWordMeaningId)
        delete_rel_example(conn, relWordMeaningId)

        delete_meaning(conn, meaning, relWordMeaningId)

    # 在word中删掉word
    delete_word_with_no_foreign_key(conn, word)


def insert_review_data(conn, word, remember):
    today = get_date()
    cursor = conn.cursor()
    sql = f"SELECT last_review_date,review_times,continuous_remember_count,forget_times FROM words WHERE word = %s"
    cursor.execute(sql, word)
    result = cursor.fetchone()
    # 计算时间差
    if result[0] is None:
        review_date_gap = None
    else:
        last_review_date = str(result[0])
        last_review_date = datetime.strptime(last_review_date, '%Y-%m-%d')
        current_date = get_date()
        current_date = datetime.strptime(current_date, '%Y-%m-%d')
        review_date_gap = (current_date - last_review_date).days  # 计算时间差（以天为单位）

    sql = f"INSERT INTO review_data (word,review_date_gap,review_times,continuous_remember_count,forget_times,remember,date) VALUES (%s,%s,%s,%s,%s,%s,%s)"
    cursor.execute(sql, (word, review_date_gap, result[1], result[2], result[3], remember, today))
    pass

