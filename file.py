import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import datetime
import random
import time

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
}

except_link = ["/kuhonnye-mojki/", "/aksessuari-dlya-kuhni/", "/oboi/", "/kley-dlya-oboev/", "/lepnina/", "/paneli/", "/reyki/", "/fasadniy-dekor/", "/freski/", "/gipsovie-3d-paneli/", "/vinilovie-paneli/", "/probkovie-pokritiya/", "/linoleum/", "/kovrovaya-plitka/", "/iskusstvennaya-trava/", "/terrasnaya-doska-iz-dpk/", "/dekorativnie-shtukaturki/", "/dekorativnaya-kraska-1/"]

root = ET.Element("yml_catalog", date=f"{datetime.datetime.now()}")

shop = ET.SubElement(root, "shop")
ET.SubElement(shop, "name").text = "santehnika-tut.ru"
ET.SubElement(shop, "company").text = "santehnika-tut.ru"
ET.SubElement(shop, "url").text = "http://santehnika-tut.ru"
currency = ET.SubElement(shop, "currencies")
ET.SubElement(currency, "currency", id="RUB", rate="1")

categories = ET.SubElement(shop, "categories")
offers = ET.SubElement(shop, "offers")

async def get_data(session, url, category, parentID):
    time.sleep(random.randint(1,2))
    while True:
        try:
            async with session.get(url=url, headers=headers) as response:
                response_text = await response.text()

                soup = BeautifulSoup(response_text, "lxml")
                print("здесь")

                product_id = soup.find("div", class_="code").text[-6:]
                try:
                    avalible = soup.find("div", class_="all_wh").text
                    offer = ET.SubElement(offers, "offer", id=product_id, avalible="true")
                except:
                    offer = ET.SubElement(offers, "offer", id=product_id, avalible="true")    

                # id = string[-11:-5]
                name = soup.find("div", class_="s_title").text.replace(" ", "")
                price = soup.find("div", class_="price").text
                description = soup.find(attrs={'itemprop': 'description'})
                article = soup.find("div", {"itemprop": "mpn"}).text

                ET.SubElement(categories, "category", id=product_id, parentId=f"{parentID}").text = soup.find_all("li", {"class": "has-child"})[-2].text

                ET.SubElement(offer, "url").text = url
                ET.SubElement(offer, "categoryId").text = product_id
                ET.SubElement(offer, "vendorCode").text = article

                ET.SubElement(offer, "name").text = name

                ET.SubElement(offer, "currencyId").text = "RUB"
                ET.SubElement(offer, "price").text = price
                ET.SubElement(offer, "description").text = f"{description}"

                pictures = soup.find("div", class_="l_side").find_all("img")
                for picture in pictures:
                    picture_link = picture.get('src')
                    if "sm" in picture_link:
                        picture_link = picture_link.replace("_sm", "_bg")
                        ET.SubElement(offer, "picture_link").text = picture_link
                    else:
                        ET.SubElement(offer, "picture_link").text = picture_link

                characteristics = soup.find("ul", {"class": "chars"}).find_all("li")
                for index in range(len(characteristics)):
                    key = characteristics[index].find("span", {"class": "left"}).text
                    value = characteristics[index].find("div").text
                    ET.SubElement(offer, "param", name=key).text = value

                characteristics_two_part = soup.find_all("div", {"class": "chars_wrapper"})[1].find_all("li")
                for index in range(len(characteristics_two_part)):
                    key = characteristics_two_part[index].find("span", {"class": "left"}).text
                    value = characteristics_two_part[index].find("div").text
                    ET.SubElement(offer, "param", name=key).text = value

                accessories = soup.find_all("span", {"class": "item prod_item"})

                for item in accessories:
                    value = item.find_all("span", {"class": "title"})[1].text
                    # value = item.find("a", {"class": "open_popup"}).text
                    ET.SubElement(offer, "param", name="Аксессуары и доп. оборудование").text = value
                break
        except:
            time.sleep(5)

async def get_links():
    response = requests.get("https://santehnika-tut.ru/catalog/", headers=headers).content
    soup = BeautifulSoup(response, "lxml")

    links = soup.find("div", id="cats").find_all("a", class_="item")
    for link in links[3]:
        if link.get('href') in except_link:
            pass
        else:
            link = link.get('href')
            while True:
                try:
                    async with aiohttp.ClientSession() as session:
                        response = await session.get(url=f"https://santehnika-tut.ru{link}", headers=headers)
                        soup = BeautifulSoup(await response.text(), "lxml")
                        # response = requests.get(f"https://santehnika-tut.ru{link}", headers=headers).content
                        # soup = BeautifulSoup(response, "lxml")
                        category = soup.find("div", class_="s_title").text
                        id = random.randint(1000000000, 10000000000)
                        ET.SubElement(categories, "category", id=f"{id}").text = category
                        sublinks = soup.find_all("div", class_="p_item")
                        pagination = soup.find_all("div", {"class": "pagination"})[1].text

                        tasks = []

                        for sublink in sublinks:
                            link = sublink.find("a", class_="img pos_rel").get('href')
                            task = asyncio.create_task(get_data(session, f"https://santehnika-tut.ru{link}", category, id))
                            tasks.append(task)

                        for number in pagination:
                            link = f"https://santehnika-tut.ru{link}/page{number}"
                            task = asyncio.create_task(get_data(session, f"https://santehnika-tut.ru{link}", category, id))
                            tasks.append(task)
                        await asyncio.gather(*tasks)
                        break
                except:
                    time.sleep(2)

def main():
    asyncio.run(get_links())
    tree = ET.ElementTree(root)
    tree.write(f"data.xml", encoding="utf-8", xml_declaration=True)

if __name__ == "__main__":
    main()