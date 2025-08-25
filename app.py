import os

import streamlit as st
import time
from os import listdir
from os.path import isfile, join
from PIL import Image
from collections import Counter
import requests
import xml.etree.ElementTree as ET
from io import BytesIO
import validators


PATH = './images'
image_urls = []
sizes = []
format = []
bg = []
url_with_bg = []


# def is_gb_image(img, tolerance:int=10):
#     # Конвертируем в RGB если нужно
#     if img.mode != 'RGB':
#         img = img.convert('RGB')
#
#     # Получаем размеры изображения
#     width, height = img.size
#
#     # Получаем пиксели из 4 углов
#     top_left = img.getpixel((10, 10))
#     top_right = img.getpixel((width - 10, 10))
#     bottom_left = img.getpixel((10, height - 10))
#     bottom_right = img.getpixel((width - 10, height - 10))
#
#     color_diff = []
#     color_diff.extend([a - b for a, b in zip(top_left, top_right)])
#     color_diff.extend([a - b for a, b in zip(top_left, bottom_left)])
#     color_diff.extend([a - b for a, b in zip(top_left, bottom_right)])
#     color_diff.extend([a - b for a, b in zip(top_right, bottom_left)])
#     color_diff.extend([a - b for a, b in zip(top_right, bottom_right)])
#     color_diff.extend([a - b for a, b in zip(bottom_left, bottom_right)])
#
#     return max(color_diff) > tolerance


def is_gb_image(img, tolerance: int = 20):
    # Конвертируем в RGB если нужно
    if img.mode != 'RGB':
        img = img.convert('RGB')

    # Получаем размеры изображения
    width, height = img.size

    spep_width = width // 50
    spep_height = height // 50
    color_diff_result = []

    for w in range(50):
        width = spep_width * w

        for r in range(50):
            height = spep_height * r

            # Получаем пиксели из 4 углов
            # print((width, height), (width + spep_width, height),(width, height+spep_height),(width+spep_width, height+spep_height))
            top_left = img.getpixel((width, height))
            top_right = img.getpixel((width+spep_width-1, height))
            bottom_left = img.getpixel((width, height+spep_height-1))
            bottom_right = img.getpixel((width+spep_width-1, height+spep_height-1))


            color_diff = []
            color_diff.extend([a - b for a, b in zip(top_left, top_right)])
            color_diff.extend([a - b for a, b in zip(top_left, bottom_left)])
            color_diff.extend([a - b for a, b in zip(top_left, bottom_right)])
            color_diff.extend([a - b for a, b in zip(top_right, bottom_left)])
            color_diff.extend([a - b for a, b in zip(top_right, bottom_right)])
            color_diff.extend([a - b for a, b in zip(bottom_left, bottom_right)])

            color_diff_result.append(max(color_diff) < tolerance)
            # print('color_diff')
            # print(color_diff)
            # return False

    color_diff_result = Counter(color_diff_result)
    print(f'is_bg: {color_diff_result[True] < color_diff_result[False]}', end=' ')
    print(Counter(color_diff_result))

    return color_diff_result[True] < color_diff_result[False]



st.title("Анализ картинок в фиде",)

url_feed = st.text_input("URL feed.xml", "https://bungly.ru/marketplace/4232924.xml")
# https://bungly.ru/marketplace/4232924.xml
# https://med-online.ru/bitrix/catalog_export/export_ALL.xml

is_limit = st.checkbox("Установить лимит")
if is_limit:
    column_limit, column_tolerance = st.columns(2)
    limit_input = column_limit.number_input(label="Число изображений для анализа",
                            value=None,
                            format="%0f",
                            # placeholder="Число изображений для анализа"
                            )
    tolerance_input = column_tolerance.number_input(label="Цветовой допуск для BG",
                                      value=20,
                                      # format="%0f",
                                      # placeholder="Число изображений для анализа"
                                      )

start_analyse = st.button("Start Analyse", type="primary", width="stretch")


if start_analyse:
    if not validators.url(url_feed):
        st.error('URL Error', icon="🚨")
    else:
        progress_text = "Download feed"
        analyse_progress_bar = st.progress(0, text=progress_text)

        # Скачивание фида
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
        }
        r = requests.get(url_feed, headers=headers)
        with open("temp/feed.xml", "wb") as file:
            file.write(r.content)

        # Выделение url изображений
        tree = ET.parse("temp/feed.xml")
        root = tree.getroot()

        for offer in root.iter('offer'):
            image_url = offer.find('picture').text.strip()
            if not image_url:
                continue
            image_urls.append(image_url)

        # for image_tag in root.findall('.//picture'):
        #     image_url = image_tag.text.strip()
        #     if not image_url:
        #         continue
        #     image_urls.append(image_url)

        container = st.container(border=True)
        left_1, right_1 = container.columns(2)
        left_1.subheader('Размеры изображений')
        right_1.subheader('Ширина/высота')
        left, right = container.columns(2)
        l = left.empty()
        r = right.empty()
        # left_4, right_4 = container.columns(1)
        container.subheader('Анализ фона')
        # r_3 = right_4.subheader('Изображения с фоном')
        # left_3, right_3 = container.columns(2)
        l_3 = container.empty()
        container.write('**Изображения с фоном**')
        r_3 = container.empty()

        for index, image_url in enumerate(image_urls):
            print(image_url)
            if '.mp4' in image_url:
                print('Detected .mp4')
                continue
            analyse_progress_bar.progress(index / len(image_urls), text=f'Analyse images: {index}/{len(image_urls)}')

            # Загружаем изображение
            response = requests.get(image_url, stream=True)
            response.raise_for_status()

            # Открываем изображение с помощью PIL
            img = Image.open(BytesIO(response.content))
            width, height = img.size
            sizes.append(f'{width}x{height}')
            print(f'{width}x{height}', end=' ')
            format.append(f'{width / height:.2f}')
            print(f'{width / height:.2f}', end=' ')

            l.empty()
            # l.subheader('Размеры изображений')
            size_analyse = Counter(sizes)
            l.write(size_analyse)

            r.empty()
            # r.subheader('Ширина/высота')
            format_analyse = Counter(format)
            r.write(format_analyse)


            try:
                if tolerance_input:
                    tolerance = tolerance_input
            except:
                tolerance = 20


            is_bg = is_gb_image(img, tolerance=tolerance)
            bg.append('Background' if is_bg else 'NO Background')
            if is_bg:
                url_with_bg.append(image_url)

            l_3.empty()
            bg_analyse = Counter(bg)
            l_3.write(bg_analyse)

            r_3.empty()
            # bg_analyse = Counter(url_with_bg)
            a = r_3.write(url_with_bg)

            try:
                if limit_input:
                    if index == limit_input-1:
                        st.balloons()
                        break
            except:
                pass

        analyse_progress_bar.empty()
        os.remove('temp/feed.xml')

        st.success('Анализ картинок завершен', icon="✅")

        # left, right = st.columns(2)
        # size_analyse = Counter(sizes)
        # left.subheader('Размеры изображений')
        # left.write(size_analyse)
        # format_analyse = Counter(format)
        # right.subheader('Ширина/высота')
        # right.write(format_analyse)





    # files_path = [f for f in listdir(PATH) if isfile(join(PATH, f))]
    # progress_text = "Operation in progress. Please wait."
    # analyse_progress_bar = st.progress(0, text=progress_text)
    # left, right = st.columns(2)
    # l = left.empty()
    # r = right.empty()
    #
    # for index, file_path in enumerate(files_path):
    #     img = Image.open(f'{PATH}/{file_path}')
    #
    #     width, height = img.size
    #     sizes.append(f'{width}x{height}')
    #     format.append(f'{width / height:.2f}')
    #
    #     analyse_progress_bar.progress(index/len(files_path), text=f'Analyse images: {index}/{len(files_path)}')
    #     time.sleep(0.01)
    #
    #     l.empty()
    #     size_analyse = Counter(sizes)
    #     l.write(size_analyse)
    #
    #     r.empty()
    #     format_analyse = Counter(format)
    #     r.write(format_analyse)
    #
    #
    #
    # analyse_progress_bar.empty()
    #
    #
    # size_analyse = Counter(sizes)
    # left.subheader('Размеры изображений')
    # left.write(size_analyse)
    # format_analyse = Counter(format)
    # right.subheader('Ширина/высота')
    # right.write(format_analyse)



