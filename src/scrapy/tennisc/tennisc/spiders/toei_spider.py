import scrapy
import os
import psycopg2
import psycopg2.extras
import slackweb
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

court_status = ["×","－","休","■"]

db_hostname = os.environ.get('DB_HOSTNAME')
db_name = os.environ.get('DB_NAME')
db_user_name = os.environ.get('DB_USER_NAME')
db_user_password = os.environ.get('DB_USER_PASSWORD')
slack_webhook_toei = os.environ.get('SLACK_WEBHOOK_TOEI')

# slack接続情報
slack = slackweb.Slack(url=slack_webhook_toei)

# 古いデータは削除
conn = psycopg2.connect(host=db_hostname, dbname=db_name, user=db_user_name, password=db_user_password, port=5432)
cursor = conn.cursor()
cursor.execute('DELETE FROM toei_court')
conn.commit()

# コートを2つ選択した場合
def search_court2(response):
    # コート1名前取得
    court1_name = response.xpath('//*[@id="disp"]/center/form/table[4]/tbody/tr/td[1]/center/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr[1]/td/text()').extract_first()
    print(court1_name)
    # コート1時間帯取得
    court1_time_list = []
    list = response.xpath('//*[@id="disp"]/center/form/table[4]/tbody/tr/td[1]/center/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr[2]/td').extract()
    for court1_time in list:
        response_court1_time = response.replace(body=court1_time)
        court1_time = response_court1_time.xpath('//td/text()').extract_first()
        court1_time_list.append(court1_time[0:5])

    # コート2名前取得
    court2_name = response.xpath('//*[@id="disp"]/center/form/table[4]/tbody/tr/td[1]/center/table/tbody/tr/td/table/tbody/tr/td[3]/table/tbody/tr[1]/td/text()').extract_first()
    print(court2_name)
    # コート2時間帯取得
    court2_time_list = []
    list = response.xpath('//*[@id="disp"]/center/form/table[4]/tbody/tr/td[1]/center/table/tbody/tr/td/table/tbody/tr/td[3]/table/tbody/tr[2]/td').extract()
    for court2_time in list:
        response_court2_time = response.replace(body=court2_time)
        court2_time = response_court2_time.xpath('//td/text()').extract_first()
        court2_time_list.append(court2_time[0:5])

    # 日付一覧取得
    day_dotw_list = []
    list = response.xpath('//*[@id="disp"]/center/form/table[4]/tbody/tr/td[1]/center/table/tbody/tr/td/table/tbody/tr/td[1]/table/tbody/tr[@valign]').extract()
    for day_dotw in list:
        response_day_dotw = response.replace(body=day_dotw)
        day_dotw = response_day_dotw.xpath('//td/text()').extract_first()
        day_dotw_list.append([day_dotw[0:5],day_dotw[6]])

    # コート結果格納
    court1_table = response.xpath('//*[@id="disp"]/center/form/table[4]/tbody/tr/td[1]/center/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr').extract()
    court1_table = court1_table[2:len(court1_table)]
    court2_table = response.xpath('//*[@id="disp"]/center/form/table[4]/tbody/tr/td[1]/center/table/tbody/tr/td/table/tbody/tr/td[3]/table/tbody/tr').extract()
    court2_table = court2_table[2:len(court2_table)]
    court_row = 0
    # postgresのコネクション情報
    conn = psycopg2.connect(host=db_hostname, dbname=db_name, user=db_user_name, password=db_user_password, port=5432)
    cursor = conn.cursor()
    for day_dotw in day_dotw_list:
        # コート1結果格納
        court1_row_result = response.replace(body=court1_table[court_row])
        court1_item_count = 1
        for court1_time in court1_time_list:
            court1_item = court1_row_result.xpath('//td[%d]/text()' % court1_item_count).extract()
            if not court1_item:
                court1_item = court1_row_result.xpath('//td[%d]/b/text()' % court1_item_count).extract_first()
            court1_item_count+=1
            # 取得した空き状況が数字以外だったら、0をセット
            if court1_item[0] in court_status:
                court1_item[0] = 0
            # SQL実行
            cursor.execute('INSERT INTO toei_court VALUES (%s,%s,%s,%s,%s) ON CONFLICT ON CONSTRAINT upst_pkey DO UPDATE SET free_num=%s', (court1_name,day_dotw[0],day_dotw[1],court1_time,court1_item[0],court1_item[0],))
            conn.commit()

        # コート2結果格納
        court2_row_result = response.replace(body=court2_table[court_row])
        court2_item_count = 1
        for court2_time in court2_time_list:
            court2_item = court2_row_result.xpath('//td[%d]/text()' % court2_item_count).extract()
            if not court2_item:
                court2_item = court2_row_result.xpath('//td[%d]/b/text()' % court2_item_count).extract_first()
            court2_item_count+=1
            # 取得した空き状況が数字以外だったら、0をセット
            if court2_item[0] in court_status:
                court2_item[0] = 0
            # SQL実行
            cursor.execute('INSERT INTO toei_court VALUES (%s,%s,%s,%s,%s) ON CONFLICT ON CONSTRAINT upst_pkey DO UPDATE SET free_num=%s', (court2_name,day_dotw[0],day_dotw[1],court2_time,court2_item[0],court2_item[0],))
            conn.commit()
        court_row+=1

# コートを1つ選択した場合
def search_court1(response):
    # コート1名前取得
    court1_name = response.xpath('//*[@id="disp"]/center/form/table[4]/tbody/tr/td[1]/center/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr[1]/td/text()').extract_first()
    print(court1_name)
    # コート1時間帯取得
    court1_time_list = []
    list = response.xpath('//*[@id="disp"]/center/form/table[4]/tbody/tr/td[1]/center/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr[2]/td').extract()
    for court1_time in list:
        response_court1_time = response.replace(body=court1_time)
        court1_time = response_court1_time.xpath('//td/text()').extract_first()
        court1_time_list.append(court1_time[0:5])

    # 日付一覧取得
    day_dotw_list = []
    list = response.xpath('//*[@id="disp"]/center/form/table[4]/tbody/tr/td[1]/center/table/tbody/tr/td/table/tbody/tr/td[1]/table/tbody/tr[@valign]').extract()
    for day_dotw in list:
        response_day_dotw = response.replace(body=day_dotw)
        day_dotw = response_day_dotw.xpath('//td/text()').extract_first()
        day_dotw_list.append([day_dotw[0:5],day_dotw[6]])

    # コート結果格納
    court1_table = response.xpath('//*[@id="disp"]/center/form/table[4]/tbody/tr/td[1]/center/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr').extract()
    court1_table = court1_table[2:len(court1_table)]
    court_row = 0
    # postgresのコネクション情報
    conn = psycopg2.connect(host=db_hostname, dbname=db_name, user=db_user_name, password=db_user_password, port=5432)
    cursor = conn.cursor()
    for day_dotw in day_dotw_list:
        # コート1結果格納
        court1_row_result = response.replace(body=court1_table[court_row])
        court1_item_count = 1
        for court1_time in court1_time_list:
            court1_item = court1_row_result.xpath('//td[%d]/text()' % court1_item_count).extract()
            if not court1_item:
                court1_item = court1_row_result.xpath('//td[%d]/b/text()' % court1_item_count).extract_first()
            court1_item_count+=1
            # 取得した空き状況が数字以外だったら、0をセット
            if court1_item[0] in court_status:
                court1_item[0] = 0
            # SQL実行
            cursor.execute('INSERT INTO toei_court VALUES (%s,%s,%s,%s,%s) ON CONFLICT ON CONSTRAINT upst_pkey DO UPDATE SET free_num=%s', (court1_name,day_dotw[0],day_dotw[1],court1_time,court1_item[0],court1_item[0],))
            conn.commit()
        court_row+=1

class ToeiSpider(scrapy.Spider):
    name = "toei"
    allowed_domains = ['yoyaku.sports.metro.tokyo.jp']
    start_urls = [
        "https://yoyaku.sports.metro.tokyo.jp/web/"
    ]

    def parse(self, response):
        options = Options()
        options.add_argument("--headless") # ヘッドレスモードのオプションを追加
        driver = webdriver.Chrome(options=options)
        src = "https://yoyaku.sports.metro.tokyo.jp/web/"

        # 月数の確認
        driver.get(src)
        # 施設の空き状況があるframeを取得
        seni1 = driver.find_element_by_xpath("html/frameset/frameset/frame[1]").get_attribute("src")
        driver.get(seni1)

        # 「施設の空き状況」をクリック
        driver.find_element_by_xpath("/html/body/table[2]/tbody/tr[2]/td/a").click()

        # 「検索」をクリック
        driver.find_element_by_xpath('//*[@id="disp"]/center/form/table[2]/tbody/tr[1]/td/a').click()

        month_num_page_source = response.replace(body=driver.page_source)
        month_num = len(month_num_page_source.xpath('//*[@id="disp"]/center/table[4]/tbody/tr[1]/td/a').extract())

        # ハードコート数の確認
        court_hard_num = 0
        driver.get(src)
        # 施設の空き状況があるframeを取得
        seni1 = driver.find_element_by_xpath("html/frameset/frameset/frame[1]").get_attribute("src")
        driver.get(seni1)

        # 「施設の空き状況」をクリック
        driver.find_element_by_xpath("/html/body/table[2]/tbody/tr[2]/td/a").click()

        # 「検索」をクリック
        driver.find_element_by_xpath('//*[@id="disp"]/center/form/table[2]/tbody/tr[1]/td/a').click()

        # 「種目指定」をクリック
        driver.find_element_by_xpath('//*[@id="disp"]/center/table[4]/tbody/tr[3]/td/a').click()

        # 「テニス(ハード)」をクリック
        driver.find_element_by_xpath('//*[@id="disp"]/center/form/table[3]/tbody/tr[1]/td[3]/a').click()

        court_hard_num_page_source = response.replace(body=driver.page_source)
        tr_num = len(court_hard_num_page_source.xpath('//*[@id="disp"]/center/table[4]/tbody/tr[4]/td/form/table/tbody/tr').extract())
        for num in range(1,tr_num+1):
            court_hard_num += len(court_hard_num_page_source.xpath('//*[@id="disp"]/center/table[4]/tbody/tr[4]/td/form/table/tbody/tr[%s]/td' % num).extract())

        # オムニコート数の確認
        court_omni_num = 0
        driver.get(src)
        # 施設の空き状況があるframeを取得
        seni1 = driver.find_element_by_xpath("html/frameset/frameset/frame[1]").get_attribute("src")
        driver.get(seni1)

        # 「施設の空き状況」をクリック
        driver.find_element_by_xpath("/html/body/table[2]/tbody/tr[2]/td/a").click()

        # 「検索」をクリック
        driver.find_element_by_xpath('//*[@id="disp"]/center/form/table[2]/tbody/tr[1]/td/a').click()

        # 「種目指定」をクリック
        driver.find_element_by_xpath('//*[@id="disp"]/center/table[4]/tbody/tr[3]/td/a').click()

        # 「テニス(人工芝)」をクリック
        driver.find_element_by_xpath('//*[@id="disp"]/center/form/table[3]/tbody/tr[1]/td[4]/a').click()

        court_omni_num_page_source = response.replace(body=driver.page_source)
        tr_num = len(court_omni_num_page_source.xpath('//*[@id="disp"]/center/table[4]/tbody/tr[4]/td/form/table/tbody/tr').extract())
        for num in range(1,tr_num+1):
            court_omni_num += len(court_omni_num_page_source.xpath('//*[@id="disp"]/center/table[4]/tbody/tr[4]/td/form/table/tbody/tr[%s]/td' % num).extract())

        # テニス(ハード)の取得
        month_num_current = 1
        while month_num_current <= month_num:
            current_row_num = 1
            current_item_num = 1
            current_search_num = 1
            while current_search_num <= court_hard_num:
                driver.get(src)
                # 施設の空き状況があるframeを取得
                seni1 = driver.find_element_by_xpath("html/frameset/frameset/frame[1]").get_attribute("src")
                driver.get(seni1)

                # 「施設の空き状況」をクリック
                driver.find_element_by_xpath("/html/body/table[2]/tbody/tr[2]/td/a").click()

                # 「検索」をクリック
                driver.find_element_by_xpath('//*[@id="disp"]/center/form/table[2]/tbody/tr[1]/td/a').click()

                # 「月指定」をクリック
                driver.find_element_by_xpath('//*[@id="disp"]/center/table[4]/tbody/tr[1]/td/a[%s]' % month_num_current).click()

                # 「曜日指定」で「月」をクリック
                driver.find_element_by_xpath('//*[@id="disp"]/center/table[4]/tbody/tr[2]/td/a[1]').click()

                # 「曜日指定」で「火」をクリック
                driver.find_element_by_xpath('//*[@id="disp"]/center/table[4]/tbody/tr[2]/td/a[2]').click()

                # 「曜日指定」で「水」をクリック
                driver.find_element_by_xpath('//*[@id="disp"]/center/table[4]/tbody/tr[2]/td/a[3]').click()

                # 「曜日指定」で「木」をクリック
                driver.find_element_by_xpath('//*[@id="disp"]/center/table[4]/tbody/tr[2]/td/a[4]').click()

                # 「曜日指定」で「金」をクリック
                driver.find_element_by_xpath('//*[@id="disp"]/center/table[4]/tbody/tr[2]/td/a[5]').click()

                # 「曜日指定」で「土」をクリック
                driver.find_element_by_xpath('//*[@id="disp"]/center/table[4]/tbody/tr[2]/td/a[6]').click()

                # 「曜日指定」で「日」をクリック
                driver.find_element_by_xpath('//*[@id="disp"]/center/table[4]/tbody/tr[2]/td/a[7]').click()

                # 「曜日指定」で「祝」をクリック
                driver.find_element_by_xpath('//*[@id="disp"]/center/table[4]/tbody/tr[2]/td/a[8]').click()

                # 「種目指定」をクリック
                driver.find_element_by_xpath('//*[@id="disp"]/center/table[4]/tbody/tr[3]/td/a').click()

                # 「テニス(ハード)」をクリック
                driver.find_element_by_xpath('//*[@id="disp"]/center/form/table[3]/tbody/tr[1]/td[3]/a').click()

                # コート1をクリック
                driver.find_element_by_xpath('//*[@id="disp"]/center/table[4]/tbody/tr[4]/td/form/table/tbody/tr[%d]/td[%d]/div/a' % (current_row_num,current_item_num)).click()
                if current_item_num==1 or current_item_num ==2:
                    current_item_num+=1
                else:
                    current_item_num=1
                    current_row_num+=1
                # コート2をクリック
                if current_search_num!=court_hard_num:
                    driver.find_element_by_xpath('//*[@id="disp"]/center/table[4]/tbody/tr[4]/td/form/table/tbody/tr[%d]/td[%d]/div/a' % (current_row_num,current_item_num)).click()
                    if current_item_num==1 or current_item_num==2:
                        current_item_num+=1
                    else:
                        current_item_num=1
                        current_roe_num+=1

                # 「検索開始」をクリック
                driver.find_element_by_xpath('//*[@id="disp"]/center/table[3]/tbody/tr/td/a[1]').click()

                response = response.replace(body=driver.page_source)

                if current_search_num!=court_hard_num:
                    search_court2(response)
                else:
                    search_court1(response)

                current_search_num+=2
            month_num_current+=1

        # テニス(オムニ)の取得
        month_num_current = 1
        while month_num_current <= month_num:
            current_row_num = 1
            current_item_num = 1
            current_search_num = 1
            while current_search_num <= court_omni_num:
                driver.get(src)
                # 施設の空き状況があるframeを取得
                seni1 = driver.find_element_by_xpath("html/frameset/frameset/frame[1]").get_attribute("src")
                driver.get(seni1)

                # 「施設の空き状況」をクリック
                driver.find_element_by_xpath("/html/body/table[2]/tbody/tr[2]/td/a").click()

                # 「検索」をクリック
                driver.find_element_by_xpath('//*[@id="disp"]/center/form/table[2]/tbody/tr[1]/td/a').click()

                # 「月指定」をクリック
                driver.find_element_by_xpath('//*[@id="disp"]/center/table[4]/tbody/tr[1]/td/a[%s]' % month_num_current).click()

                # 「曜日指定」で「月」をクリック
                driver.find_element_by_xpath('//*[@id="disp"]/center/table[4]/tbody/tr[2]/td/a[1]').click()

                # 「曜日指定」で「火」をクリック
                driver.find_element_by_xpath('//*[@id="disp"]/center/table[4]/tbody/tr[2]/td/a[2]').click()

                # 「曜日指定」で「水」をクリック
                driver.find_element_by_xpath('//*[@id="disp"]/center/table[4]/tbody/tr[2]/td/a[3]').click()

                # 「曜日指定」で「木」をクリック
                driver.find_element_by_xpath('//*[@id="disp"]/center/table[4]/tbody/tr[2]/td/a[4]').click()

                # 「曜日指定」で「金」をクリック
                driver.find_element_by_xpath('//*[@id="disp"]/center/table[4]/tbody/tr[2]/td/a[5]').click()

                # 「曜日指定」で「土」をクリック
                driver.find_element_by_xpath('//*[@id="disp"]/center/table[4]/tbody/tr[2]/td/a[6]').click()

                # 「曜日指定」で「日」をクリック
                driver.find_element_by_xpath('//*[@id="disp"]/center/table[4]/tbody/tr[2]/td/a[7]').click()

                # 「曜日指定」で「祝」をクリック
                driver.find_element_by_xpath('//*[@id="disp"]/center/table[4]/tbody/tr[2]/td/a[8]').click()

                # 「種目指定」をクリック
                driver.find_element_by_xpath('//*[@id="disp"]/center/table[4]/tbody/tr[3]/td/a').click()

                # 「テニス(人工芝)」をクリック
                driver.find_element_by_xpath('//*[@id="disp"]/center/form/table[3]/tbody/tr[1]/td[4]/a').click()

                # コート1をクリック
                driver.find_element_by_xpath('//*[@id="disp"]/center/table[4]/tbody/tr[4]/td/form/table/tbody/tr[%d]/td[%d]/div/a' % (current_row_num,current_item_num)).click()
                if current_item_num==1 or current_item_num ==2:
                    current_item_num+=1
                else:
                    current_item_num=1
                    current_row_num+=1
                # コート2をクリック
                if current_search_num!=court_omni_num:
                    driver.find_element_by_xpath('//*[@id="disp"]/center/table[4]/tbody/tr[4]/td/form/table/tbody/tr[%d]/td[%d]/div/a' % (current_row_num,current_item_num)).click()
                    if current_item_num==1 or current_item_num==2:
                        current_item_num+=1
                    else:
                        current_item_num=1
                        current_row_num+=1
                # 「検索開始」をクリック
                driver.find_element_by_xpath('//*[@id="disp"]/center/table[3]/tbody/tr/td/a[1]').click()

                response = response.replace(body=driver.page_source)

                if current_search_num!=court_omni_num:
                    search_court2(response)
                else:
                    search_court1(response)
                current_search_num+=2
            month_num_current+=1

        # 希望するコートが空いていたらslackに通知
        conn_notifcation = psycopg2.connect(host=db_hostname, dbname=db_name, user=db_user_name, password=db_user_password, port=5432)
        conn_toei = psycopg2.connect(host=db_hostname, dbname=db_name, user=db_user_name, password=db_user_password, port=5432)

        cursor_notification = conn_notifcation.cursor()
        cursor_toei = conn_toei.cursor()

        notification_result = ""
        cursor_notification.execute('SELECT court_name,dotw,start_time FROM notification_court')
        for row_notification in cursor_notification:
            court_name = row_notification[0]
            dotw = row_notification[1]
            start_time = row_notification[2]

            cursor_toei.execute('SELECT * FROM toei_court WHERE court_name = %s AND dotw = %s AND start_time = %s AND free_num != 0', (court_name,dotw,start_time,))
            for row_toei in cursor_toei:
                notification_result = notification_result + str(row_toei) + '\n'

        if len(notification_result) != 0:
            slack.notify(text=notification_result)
