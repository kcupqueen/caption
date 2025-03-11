from peewee import SqliteDatabase, Model, IntegerField, CharField
from bs4 import BeautifulSoup
import spacy


# Define the base model class without binding to a specific database
class BaseModel(Model):
    class Meta:
        database = None  # Will be set later

# Define Mdx model inheriting from BaseModel
class Mdx(BaseModel):
    entry = CharField(primary_key=True)  # 把 `entry` 设为主键
    paraphrase = CharField()  # TEXT not null

    class Meta:
        table_name = "mdx"  # 明确指定数据库表名
        indexes = (
            (('entry',), False),  # False 表示索引不是唯一的
        )

class WordTranslation:
    def __init__(self, meanings, audios):
        self.meanings = meanings
        self.audios = meanings

    def __repr__(self):
        return f"[WordTranslation] {self.meanings}, {self.audios}"

    def __str__(self):
        return f"[WordTranslation] {self.meanings}, {self.audios}"


class OfflineTranslator:
    def __init__(self, mdx_db_path):
        self.mdx_db_path = mdx_db_path
        self.db = SqliteDatabase(mdx_db_path)
        self.nlp = spacy.load("en_core_web_sm")

        # 绑定数据库到 Peewee 模型
        self.db.bind([Mdx])

        # 连接数据库
        self.db.connect()

        # print all tables
        print(self.db.get_tables())


    @staticmethod
    def parse_mdx(paraphrase):
        soup = BeautifulSoup(paraphrase, "html.parser")
        meanings = []
        # get sblocks
        sblocks = soup.find("div", class_="sblocks")
        if sblocks:
            # get all sblock sblock_entry
            sblock_entries = sblocks.find_all("div", class_="sblock_entry")
            # get span, def_text
            for sblock_entry in sblock_entries:

                def_text_list = sblock_entry.find_all("span", class_="def_text")
                for def_text in def_text_list:
                    # get all elements in def_text
                    mw_zh_list = def_text.find_all("span", class_="mw_zh")
                    for mw_zh in mw_zh_list:
                        print(mw_zh.text)
                        meanings.append(mw_zh.text)
        return WordTranslation(meanings, [])





    def lookup(self, text, retry=0):
        """查找词条的释义"""
        try:
            if retry > 1:
                raise Exception("retry too many times")
            raw = text
            doc = self.nlp(text)
            lemmas = [token.lemma_ for token in doc]
            print("raw", lemmas)
            if len(lemmas) > 1:
                raise Exception("multi words")
            if len(lemmas) > 0:
                raw = lemmas[0]
            mdx = Mdx.get_or_none(Mdx.entry == text)
            print("sql done", mdx)
            if mdx and mdx.paraphrase:
                #print(mdx.paraphrase
                print("get mdx entry", mdx.entry)
                return OfflineTranslator.parse_mdx(mdx.paraphrase)
            else:
                print("retry lookup", raw)
                return self.lookup(raw, retry + 1)
        except Exception as e:
            print("lookup error", e)
            return None

    def __del__(self):
        """确保对象销毁时关闭数据库连接"""
        if not self.db.is_closed():
            self.db.close()


# def test_lookup():
#     # print current path
#     import os
#     print(os.getcwd())
#     """测试 OfflineTranslator 的 lookup 方法"""
#     # 使用一个临时数据库（避免影响正式数据）
#     test_db_path = "./mdx.db"
#     #
#     # # 初始化翻译器
#     translator = OfflineTranslator(test_db_path)
#     # # 测试查找
#     # print("Testing lookup:")
#     print("cursor =>", translator.lookup("money"))
#     # print("world =>", translator.lookup("broken"))
#     # print("python =>", translator.lookup("python"))
#     # # 关闭数据库
#     # del translator
#
# # 运行测试
# test_lookup()
