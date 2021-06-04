import pandas as pd

class DoexcleByPandas(object):

    def get_data_for_pytest(self, filename, sheet_name):
        """
        :param filename:
        :param sheet_name:
        :return:
        """
        df =pd.read_excel(filename, sheet_name=sheet_name, keep_default_na=False) #默认读取第一个表单，读出来是一个二维矩阵
        test_data = []
        for i in df.values.tolist():
            test_data.append(i)
        return test_data

    def get_data_for_allure(self, filename, sheet_name):
        """
        :param filename:
        :param sheet_name:
        :return:
        """
        df = pd.read_excel(filename, sheet_name=sheet_name, keep_default_na=False)  # 默认读取第一个表单，读出来是一个二维矩阵
        test_data = []
        #获取索引号，并对其进行遍历
        for i in df.index.values:
            #根据i获取该行的数据，通过[]指定需要获取的字段，并通过to_dict转化为字典--这立不能用iloc（iloc只能用数字索引）
            row_data = df.loc[i, ['story']].to_dict()
            test_data.append(row_data)
        return test_data
        # for i in test_data:
        #     #遍历字典，并取出severity的值
        #     return i['story']
