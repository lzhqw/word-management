import pymysql


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
    with open("dbwords.sql") as file:
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


def get_select_sql(table_name, col_name):
    if isinstance(col_name, (list, tuple)):
        sql = f"SELECT * FROM {table_name} WHERE " + " =%s AND ".join(col for col in col_name) + " =%s"
    else:
        sql = f"SELECT * FROM {table_name} WHERE {col_name} = %s;"
    return sql


def get_insert_sql(table_name, col_name):
    if isinstance(col_name, (list, tuple)):
        sql = (f"INSERT INTO {table_name} (" + ",".join(col for col in col_name) +
               ") VALUES (" + ",".join("%s" for col in col_name)) + ')'
    else:
        sql = f"INSERT INTO {table_name} ({col_name}) VALUES (%s)"
    return sql


def insert_(conn, table_name, col_name, value):
    # step1. 查找是否存在
    cursor = conn.cursor()

    sql = get_select_sql(table_name, col_name)
    cursor.execute(sql, value)
    results = cursor.fetchall()

    # step2. 如果存在则返回id，否则插入并返回id
    if len(results) != 0:
        return results[0][0]
    else:
        sql = get_insert_sql(table_name, col_name)
        cursor.execute(sql, value)
        conn.commit()
        rowId = cursor.lastrowid
        return rowId


def multiple_insert_rel(conn,words: (list, tuple), table_name, col_name, rel_table_name, rel_col_names, rel_value):
    for word in words:
        wordId = insert_(conn=conn, table_name=table_name, col_name=col_name, value=word)
        relId = insert_(conn=conn, table_name=rel_table_name,
                        col_name=rel_col_names,
                        value=(rel_value, wordId))


def insert(conn, word, pos, meaning, example, derivative, synonyms, antonym, similarWords):
    # step1. 插入word
    wordId = insert_(conn=conn, table_name='words', col_name='word', value=word)
    # step2. 插入pos
    posId = insert_(conn=conn, table_name='pos', col_name='POS', value=pos)
    # step3. 插入meaning
    meaningId = insert_(conn=conn, table_name='meanings', col_name='meaning', value=meaning)
    # step4. 关联relWordMeaning表
    wordMeaningId = insert_(conn=conn,
                            table_name='relWordMeaning',
                            col_name=('wordId', 'POSId', 'meaningId'),
                            value=(wordId, posId, meaningId))
    # step5. 插入example并关联relExample表
    multiple_insert_rel(conn=conn,
                        words=example,
                        table_name='examples',
                        col_name='example',
                        rel_table_name='relExample',
                        rel_col_names=('relWordMeaningId', 'exampleId'),
                        rel_value=wordMeaningId)
    # for examp in example:
    #     exampleId = insert_(conn=conn, table_name='examples', col_name='example', value=examp)
    #     relExampleId = insert_(conn=conn, table_name='relExample',
    #                            col_name=('relWordMeaningId', 'exampleId'),
    #                            value=(wordMeaningId, exampleId))
    # step6. 关联衍生词表
    multiple_insert_rel(conn=conn,
                        words=derivative,
                        table_name='words',
                        col_name='word',
                        rel_table_name='relDerivative',
                        rel_col_names=('relWordMeaningId', 'wordId'),
                        rel_value=wordMeaningId)

    # step7. 关联同义词表
    multiple_insert_rel(conn=conn,
                        words=synonyms,
                        table_name='words',
                        col_name='word',
                        rel_table_name='relSynonyms',
                        rel_col_names=('relWordMeaningId', 'wordId'),
                        rel_value=wordMeaningId)

    # step8. 关联反义词表
    multiple_insert_rel(conn=conn,
                        words=antonym,
                        table_name='words',
                        col_name='word',
                        rel_table_name='relAntonym',
                        rel_col_names=('relWordMeaningId', 'wordId'),
                        rel_value=wordMeaningId)
    # step9. 关联形近词表
    multiple_insert_rel(conn=conn,
                        words=similarWords,
                        table_name='words',
                        col_name='word',
                        rel_table_name='relSimilarWords',
                        rel_col_names=('wordId', 'similarWordId'),
                        rel_value=wordId)


def get_word_id(conn, table_name, col_name, where_col_name, word):
    # Step 1: 从words表中查找word对应的wordId
    sql = f"SELECT {col_name} FROM {table_name} WHERE {where_col_name} = %s"
    cursor = conn.cursor()
    cursor.execute(sql, word)
    word_id = cursor.fetchone()
    if word_id:
        return word_id[0]
    else:
        return None


def get_words(conn, table_rel, col_rel, table_content, col_content, where_rel, where_content, where_value):
    sql = f"SELECT {col_rel} FROM {table_rel} WHERE {where_rel} = %s"
    cursor = conn.cursor()
    cursor.execute(sql, where_value)
    results = cursor.fetchall()
    words = []
    for result in results:
        wordId = result[0]
        sql = f"SELECT {col_content} FROM {table_content} WHERE {where_content} = %s"
        cursor.execute(sql, wordId)
        results = cursor.fetchone()
        words.append(results[0])
    return words


def get_meaning_result(conn, wordId):
    sql = "SELECT relWordMeaningId, meaningId, POSId FROM relWordMeaning WHERE wordId = %s"
    cursor = conn.cursor()
    cursor.execute(sql, wordId)
    results = cursor.fetchall()
    return results


def show_word(conn, word):
    print('-' * 70)
    print(word)
    print('-' * 70)
    # step1. 先从words表中查到word对应的wordId
    wordId = get_word_id(conn=conn, table_name='words', col_name='wordId', where_col_name='word', word=word)
    # step2. 从relWordMeaning表中查到relWordMeaningId,meaningId和POSId（可能有多个结果）
    results = get_meaning_result(conn, wordId)
    for i,result in enumerate(results):
        relWordMeaningId, POSId, meaningId = result
        # 对于每个结果
        # step3. 从meanings表中根据meaningId获取meaning
        meaning = get_word_id(conn=conn, table_name='meanings', col_name='meaning',
                              where_col_name='meaningId', word=meaningId)
        # step4. 从pos表中根据POSId获取POS
        pos = get_word_id(conn=conn, table_name='pos', col_name='POS',
                          where_col_name='POSId', word=POSId)
        # step5. 根据relWordMeaningId从relExample表中查到exampleId
        example = get_words(conn=conn,
                            table_rel='relExample',
                            col_rel='exampleId',
                            table_content='examples',
                            col_content='example',
                            where_rel='relWordMeaningId',
                            where_content='exampleId',
                            where_value=relWordMeaningId)

        derivative = get_words(conn=conn,
                               table_rel='relDerivative',
                               col_rel='wordId',
                               table_content='words',
                               col_content='word',
                               where_rel='relWordMeaningId',
                               where_content='wordId',
                               where_value=relWordMeaningId)

        synonyms = get_words(conn=conn,
                             table_rel='relSynonyms',
                             col_rel='wordId',
                             table_content='words',
                             col_content='word',
                             where_rel='relWordMeaningId',
                             where_content='wordId',
                             where_value=relWordMeaningId)

        antonym = get_words(conn=conn,
                            table_rel='relAntonym',
                            col_rel='wordId',
                            table_content='words',
                            col_content='word',
                            where_rel='relWordMeaningId',
                            where_content='wordId',
                            where_value=relWordMeaningId)

        print(f'  {i+1}. {pos}.{meaning}')
        print('    --example')
        for w in example:
            print(f'        {w}')
        print('    --derivative')
        for w in derivative:
            print(f'        {w}')
        print('    --synonyms')
        for w in synonyms:
            print(f'        {w}')
        print('    --antonym')
        for w in antonym:
            print(f'        {w}')
        print('-' * 70)

    similarWords = get_words(conn=conn,
                             table_rel='relSimilarWords',
                             col_rel='similarWordId',
                             table_content='words',
                             col_content='word',
                             where_rel='wordId',
                             where_content='wordId',
                             where_value=wordId)
    print('    --similar words')
    for w in similarWords:
        print(f'        {w}')

    pass


def update(db, table, content):
    pass

def delete_word(word):
    pass


def generate_table_columns_dict(conn):
    table_columns = {}  # 创建一个字典来存储表-列名的映射
    cursor = conn.cursor()
    # 获取当前连接的数据库名称
    current_database = conn.db

    # 查询所有表的列信息
    query = "SELECT table_name, column_name FROM information_schema.columns WHERE table_schema = %s"
    cursor.execute(query, (current_database,))
    results = cursor.fetchall()

    for result in results:
        table_name, column_name = result
        if table_name not in table_columns:
            table_columns[table_name] = []
        table_columns[table_name].append(column_name)
    for key in table_columns.keys():
        item = table_columns[key]
        col_dict = {}
        for i, col in enumerate(item):
            col_dict[col] = i
        table_columns[key] = col_dict
    return table_columns

def trans_data_from_xml_to_sql():
    pass

# conn = connect()
# table_columns = generate_table_columns_dict(conn)
# print(table_columns)
# initialize_database(conn)
# insert(conn, word='test', pos='v', meaning='测试1', example=['this is a test1', 'this is the test1'],
#        derivative=['testtest1','testtest123'], synonyms=['test11'], antonym=['detest1'], similarWords=['testb1'])
# insert(conn, word='test', pos='n', meaning='测试2', example=['this is a test2'],
#        derivative=['testtest2'], synonyms=['test22'], antonym=['detest2'], similarWords=['testb2'])
# show_word(conn=conn, word='test')
