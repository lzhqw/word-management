import pymysql
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
    multiple_insert_rel(conn=conn,
                        words=similarWords,
                        table='words',
                        col='word',
                        rel_table='relSimilarWords',
                        rel_col=('word', 'similarWord'),
                        rel_value=word)


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


def show_word(conn, word):
    word_dict_list = []

    print('-' * 70)
    print(word)
    print('-' * 70)
    # step2. 从relWordMeaning表中查到relWordMeaningId,meaningId和POSId（可能有多个结果）
    results = get_meaning_result(conn, word)
    for i, result in enumerate(results):
        relWordMeaningId, meaning, pos = result
        # step5. 根据relWordMeaningId从relExample表中查到exampleId
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

        print(f'  {i + 1}. {pos}.{meaning}')
        if len(example) != 0:
            print('    --example')
        for w in example:
            print(f'        {w[0]}')
        if len(derivative) != 0:
            print('    --derivative')
        for w in derivative:
            print(f'        {w[0]}')
        if len(synonyms) != 0:
            print('    --synonyms')
        for w in synonyms:
            print(f'        {w[0]}')
        if len(antonym) != 0:
            print('    --antonym')
        for w in antonym:
            print(f'        {w[0]}')
        print('-' * 70)
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
        print('    --similar words')
    for w in similarWords1 + similarWords2:
        print(f'        {w[0]}')
    word_dict_list.append(similarWords1 + similarWords2)
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


def input_from_console(conn, mode='insert'):
    word = input("word: ")
    word_dict_list = show_word(conn=conn, word=word)
    print(word_dict_list)


def get_word_book(conn):
    sql = "SELECT DISTINCT word FROM relWordMeaning WHERE pos != 'phrase'"
    cursor = conn.cursor()
    cursor.execute(sql)
    results = cursor.fetchall()
    with open('words.txt', 'w') as f:
        for word in results:
            f.write(word[0] + '\n')


conn = connect()
get_word_book(conn)
# input_from_console(conn)
# initialize_database(conn=conn)
# insert(conn=conn,
#        word='test',
#        pos='v',
#        meaning='测试1',
#        example=['this is a test', 'this is the test'],
#        derivative=['testa', 'testb'],
#        synonyms=['test sy'],
#        antonym=['un test'],
#        similarWords=['ttest']
#        )
# insert(conn=conn,
#        word='test',
#        pos='n',
#        meaning='测试2',
#        example=['this is a test2', 'this is the test2'],
#        derivative=['testa2', 'testb2'],
#        synonyms=['test sy2'],
#        antonym=['un test2'],
#        similarWords=['ttest2', 'test3']
#        )
#
# show_word(conn, 'test')
