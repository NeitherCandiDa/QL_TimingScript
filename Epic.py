# -*- coding=UTF-8 -*-
# @Project          QL_TimingScript
# @fileName         Epic.py
# @author           Leon
# @EditTime         2025/12/12
from datetime import datetime

import httpx

import log


class Epic:
    IS_FREE = False
    START_DATE = ""
    END_DATE = ""

    def __init__(self):
        self.client = httpx.Client(verify=False, timeout=60)

    def get_free_games(self):
        """
        获取免费游戏
        """
        url = "https://store-site-backend-static-ipv4.ak.epicgames.com/freeGamesPromotions"
        params = {
            "country": "CN",
            "locale": "zh-CN",
            "allowCountries": "CN"
        }
        games = []
        data = None
        try:
            response = self.client.get(url, params=params)
            if response.status_code != 200:
                log.log("获取免费游戏请求异常")
            data = response.json()
        except Exception as e:
            log.log(e)
        elements: list = data.get('data').get('Catalog').get('searchStore').get('elements', None)
        if elements is None:
            log.log("获取免费游戏发生异常")
        print('====================================================')
        for element in elements:
            print(element)
        print("====================================================")
        for element in elements:
            title = element.get('title')
            if element.get('promotions') is None or 'Mystery Game' in title:
                continue
            promotionalOffers = element.get('promotions').get('promotionalOffers', [])
            upcomingOffers = element.get('promotions').get('upcomingPromotionalOffers', [])

            for offerSet in promotionalOffers:
                promotionalOffers2 = offerSet.get('promotionalOffers', [])
                for offer in promotionalOffers2:
                    # if offer.get('price', {}).get('totalPrice', {}).get('discountPrice') == 0:
                    #     log.log(f"{element.get('title')} 获取到免费游戏")
                    #     Epic.IS_FREE = True
                    if offer.get('discountSetting').get('discountPercentage') == 0:
                        start_date = datetime.fromisoformat(offer.get('startDate').replace("Z", "+00:00")).strftime(
                            "%Y-%m-%d")
                        end_date = datetime.fromisoformat(offer.get('endDate').replace("Z", "+00:00")).strftime(
                            "%Y-%m-%d")
                        if start_date <= datetime.now().strftime("%Y-%m-%d") <= end_date:
                            self.IS_FREE = True
                            self.START_DATE = start_date
                            self.END_DATE = end_date
                            break
                if self.IS_FREE:
                    break

            if not self.IS_FREE:
                for offerSet in upcomingOffers:
                    for offer in offerSet.get(promotionalOffers, []):
                        if offer.get('discountSetting').get('discountPercentage') == 0:
                            start_date = datetime.fromisoformat(offer.get('startDate').replace("Z", "+00:00"))
                            end_date = datetime.fromisoformat(offer.get('endDate').replace("Z", "+00:00"))
                            now = datetime.now()
                            if (start_date - now).total_seconds() < 24 * 60 * 60:
                                self.IS_FREE = True
                                self.START_DATE = start_date
                                self.END_DATE = end_date
                                break
                    if self.IS_FREE:
                        break
            if self.IS_FREE:
                game_image_url = ''
                keyImages = element.get('keyImages', [])
                offer_image = next((img for img in keyImages if img.get('type') == 'OfferImageWide'), None)
                thumbnail = next((img for img in keyImages if img.get('type') == 'Thumbnail'), None)
                if offer_image:
                    game_image_url = offer_image.get('url')
                elif thumbnail:
                    game_image_url = thumbnail.get('url')
                print(f'game_image_url: {game_image_url}')

                game_url = ''
                if len(element['catalogNs']['mappings']) > 0:
                    game_url = f"https://store.epicgames.com/zh-CN/p/{element['catalogNs']['mappings'][0]['pageSlug']}"
                    print(f'game_url1: {game_url}')
                elif len(element['customAttributes']) > 0:
                    productSlugAttr = next((attr for attr in element.get('customAttributes', [])
                                            if attr.get('key') == 'com.epicgames.app.productSlug'), None)
                    if productSlugAttr:
                        game_url = f'https://store.epicgames.com/zh-CN/p/{productSlugAttr.get("value")}'
                        print(f'game_url2: {game_url}')
                else:
                    game_url = f'https://store.epicgames.com/p/{element.get("id")}'
                    print(f'game_url3: {game_url}')
                games.append(
                    {
                        "title": title,
                        'url': game_url,
                        'image': game_image_url,
                        'offerTimePeriod': f'{self.START_DATE} 至 {self.END_DATE}',
                    }
                )
        return games

    def run(self):
        free_games = self.get_free_games()
        if len(free_games) == 0:
            log.log("本周没有免费游戏")
            return


if __name__ == '__main__':
    epic = Epic()
    print(epic.get_free_games())
