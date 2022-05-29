# description:500彩票网欧赔数据爬虫
# author:LevyXie
# Date:2022/3/15 17:09

import requests
from bs4 import BeautifulSoup

base_url = 'https://odds.500.com'
base_headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/98.0.4758.102 Safari/537.36'
        }
next_base_url = 'https://odds.500.com/fenxi1/inc/ouzhi_sameajax.php?'
update_headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/98.0.4758.102 Safari/537.36',
    'x-requested-with': 'XMLHttpRequest',
    'referer': 'https://odds.500.com'
}


class GambleSpider(object):
    # 获得soup对象
    def get_soup_from_url(self, url):
        headers = base_headers
        session = requests.session()
        response = session.get(url=url, headers=headers)
        response.encoding = 'gbk'

        page_info = response.text
        soup = BeautifulSoup(page_info, 'lxml')
        return soup

    # 解析soup中的赔率
    def get_now_odds(self, soup, title):
        target_odd_index = soup.find(attrs={'title': title}).parent.contents[5].table.tbody.contents[3].text
        temp = target_odd_index.split('\n')
        odds = [float(temp[1]), float(temp[2]), float(temp[3])]
        return odds

    def get_team_from_soup(self,soup):
        team = []
        raw_teams = soup.find_all(attrs={'class': 'hd_name'})
        for rTeam in raw_teams:
            team.append(rTeam.text)
        return team

    # 获取爬取同赔json数据的网址
    def get_next_url(self, soup, title):
        target_attrs = soup.find(attrs={'title': title}).parent.find(text='同').parent.attrs
        process_url = target_attrs.get('href')
        part_url = process_url.split('?')[1].replace('fixtureid','id')
        next_url = next_base_url + part_url
        return next_url

    # 从soup获取json格式数据
    def get_json_from_url(self, url):
        headers = update_headers
        session = requests.session()
        response = session.get(url=url, headers=headers)
        response.encoding = 'utf-8'
        json = response.json()
        return json

    # 将爬取到的json数据转为字典
    def parse_json_to_result(self, json, odds):
        result = {}
        same_odds_data = []
        like = []
        advice = {}
        win_count = 0
        draw_count = 0
        loss_count = 0
        min_diff = 100
        data = json.get('row')

        for item in data:
            d = {}
            d['胜赔'] = float(item[-7])
            d['平赔'] = float(item[-6])
            d['负赔'] = float(item[-5])
            if item[-8] == 0:
                d['赛果'] = '主胜'
            if item[-8] == 1:
                d['赛果'] = '平局'
            if item[-8] == 2:
                d['赛果'] = '主负'
            d['主队'] = item[5]
            d['客队'] = item[8]
            # 取得所有同赔数据
            same_odds_data .append(d)
            # 处理同赔数据
            diff_win = abs(d['胜赔'] - odds[0])
            diff_loss = abs(d['平赔'] - odds[1])
            diff_draw = abs(d['负赔'] - odds[2])
            diff = diff_win ** 2 + diff_loss ** 2 + diff_draw ** 2
            if diff < min_diff:
                advice = d
                min_diff = diff
            if min(diff_win, diff_loss, diff_draw) < 0.05 and diff_win < 0.2 and diff_loss < 0.2 and diff_draw < 0.2:
                like.append(d)

        result['same'] = same_odds_data
        for like_item in like:
            if like_item.get('赛果') == '主胜':
                win_count += 1
            if like_item.get('赛果') == '平局':
                draw_count += 1
            if like_item.get('赛果') == '主负':
                loss_count += 1

        result['advice'] = advice.get('赛果') + ' 参考场次:' + advice.get('主队') + ' vs ' + advice.get('客队') + ' 胜平负赔率' \
                                    '依次为:' + str(advice.get('胜赔')) + ',' + str(advice.get('平赔')) + ',' + str(advice.get('负赔'))
        result['like'] = like
        result['odds'] = '胜赔:' + str(odds[0]) + ' 平赔:' + str(odds[1]) + ' 负赔:' + str(odds[2])
        if len(like) != 0:
            result['likecount'] = '共计' + str(len(like)) + '场相似赔率比赛,其中主胜' + str(win_count) + ',平局' + str(draw_count) + ',主负' + str(loss_count) + '.'
        else:
            result['likecount'] = '近似赔率比赛场次为0 ~'
        return result

# 测试代码
# if __name__ == '__main__':
#     spider = GambleSpider()
#     soup = spider.get_soup_from_url('https://odds.500.com/fenxi/ouzhi-990213.shtml')
#     url = spider.get_next_url(soup, '立博')
#     odds = spider.get_now_odds(soup, '立博')
#     json = spider.get_json_from_url(url)
#     result = spider.parse_json_to_result(json, odds)
#     print(result.get('like'))





