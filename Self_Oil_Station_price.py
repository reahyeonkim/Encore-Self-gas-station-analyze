# -*- coding: utf-8 -*-
"""
Created on Wed Oct 20 13:33:43 2021

@author: admin

셀프 주유소는 과연 저렴한지
"""

import pandas as pd
from glob import glob

import matplotlib.pyplot as plt
import seaborn as sns
import platform

import json
import folium
import googlemaps
import warnings
warnings.simplefilter(action = "ignore", category = FutureWarning)

import numpy as np
# 반복문 실행에 대한 진행율 표시(Console) %
from tqdm import tqdm_notebook

path = "c:/Windows/Fonts/malgun.ttf"
from matplotlib import font_manager, rc
if platform.system() == 'Darwin':
    rc('font', family='AppleGothic')
elif platform.system() == 'Windows':
    font_name = font_manager.FontProperties(fname=path).get_name()
    rc('font', family=font_name)
else:
    print('Unknown system... sorry~~~~')
    

### 1. 구별 주유 가격에 대한 데이터의 정리
# 데이터 파일들 확인
glob('./data/지역_위치별*xls')

# 총 24개의 엑셀 파일들 위치와 파일명 저장
stations_files = glob('./data/지역_위치별*xls')

# 총 24개의 엑셀 파일 로드
tmp_raw = []

# 총 24개의 엑셀 파일을 데이터 프레임 형태로 로드하여 리스트에 추가
for file_name in stations_files:
    tmp = pd.read_excel(file_name, header=2)
    tmp_raw.append(tmp)

# 리스트에 추가된 각 데이터 프레임을 하나로 연결    
station_raw = pd.concat(tmp_raw)

# 하나로 합해진 데이터프레임 정보 확인
station_raw.info()
station_raw.head()


# 전체 데이터로부터 상호/주소/휘발유/셀프여부/상표 만 추츨하여 데이터프레임화
# 이 때 각 컬럼명을 새롭게 설정
stations = pd.DataFrame({'Oil_store':station_raw['상호'], 
                         '주소':station_raw['주소'],
                         '가격':station_raw['휘발유'],
                         '셀프':station_raw['셀프여부'],
                         '상표':station_raw['상표']  })
stations.head()


# 구 컬럼 추가
stations['구'] = [eachAddress.split()[1] for eachAddress in stations['주소']]
stations.head()

# 구 컬럼내의 데이터 결측치 여부 확인
stations['구'].unique()

# 구 컬럼의 데이터가 서울특별시로 되어 있는지 확인
stations[stations['구']=='서울특별시']

# 구 컬럼의 데이터가 서울특별시 
stations.loc[stations['구']=='서울특별시', '구'] = '성동구'
stations['구'].unique()


# 구 컬럼의 데이터가 특별시 
stations[stations['구']=='특별시']

stations.loc[stations['구']=='특별시', '구'] = '도봉구'
stations['구'].unique()



# 가격 컬럼에 '-' 부호가 있는지 확인
stations[stations['가격']=='-']
stations = stations[stations['가격'] != '-']
stations.head()

# 가격 컬럼 데이터를 실수로 변환
stations['가격'] = [float(value) for value in stations['가격']]


stations.reset_index(inplace=True)
del stations['index']
stations.info()
stations.head()




### 2. 셀프 주유소는 정말 저렴한지 boxplot으로 확인

# 기본
stations.boxplot(column='가격', by='셀프', figsize=(12,8))

# 셀프 컬럼을 이용한 분리
plt.figure(figsize=(12,8))
sns.boxplot(x="상표", y="가격", 
            hue="셀프", data=stations, 
            palette="Set3")
plt.show()


# swarmplot() 추가
plt.figure(figsize=(12,8))
sns.boxplot(x="상표", y="가격", data=stations, 
            palette="Set3")
sns.swarmplot(x="상표", y="가격", data=stations, 
              color=".6")
plt.show()



### 3. 서울시 구별 주유 가격 확인
# 가격을 기준으로 정렬
stations.sort_values(by='가격', ascending=False).head(10)
stations.sort_values(by='가격', ascending=True).head(10)

# 피벗 테이블을 이용
gu_data = pd.pivot_table(stations, index=["구"], values=["가격"], aggfunc=np.mean)
gu_data.head()


# 구글 맵데이터 로드
geo_path = './data/02. skorea_municipalities_geo_simple.json'
geo_str = json.load(open(geo_path, encoding='utf-8'))

map = folium.Map(location=[37.5502, 126.982], zoom_start=10.5, 
                 tiles='Stamen Toner')
map.save('./result/토너지도.html')


map = folium.Map(location=[37.5502, 126.982], zoom_start=10.5, 
                 tiles='Stamen Toner')
map.choropleth(geo_data = geo_str,
               data = gu_data,
               columns=[gu_data.index, '가격'],
               fill_color='PuRd',      # 또는 PuRd, YlGnBu
               key_on='feature.id')

map.save('./result/가격.html')


map_sample = folium.Map(location=[45.5236, -122.6750],
                            zoom_start=13)
folium.RegularPolygonMarker([45.5012, -122.6655],
                            popup='Ross Island Bridge', fill_color='#132b5e',
                            number_of_sides=3, radius=10).add_to(map_sample)
folium.RegularPolygonMarker([45.5132, -122.6708],
                            popup='Hawthorne Bridge', fill_color='#45647d',
                            number_of_sides=4, radius=10).add_to(map_sample)
folium.RegularPolygonMarker([45.5275, -122.6692],
                            popup='Steel Bridge', fill_color='#769d96',
                            number_of_sides=6, radius=10).add_to(map_sample)
folium.RegularPolygonMarker([45.5318, -122.6745],
                            popup='Broadway Bridge', fill_color='#769d96',
                            number_of_sides=8, radius=10).add_to(map_sample)

map_sample.save('folium_kr.html')


### 4. 서울시 주유 가격 상하위 10개 주유소 지도에 표기
# 서울시 주유 가격 상하위 10개 데이터 추출
oil_price_top10 = stations.sort_values(by='가격', ascending=False).head(10)
oil_price_top10

oil_price_bottom10 = stations.sort_values(by='가격', ascending=True).head(10)
oil_price_bottom10

# 반복문 실행에 대한 진행율 표시(Console) %
# from tqdm import tqdm_notebook

# 구글 맵을 가져오기위한 구글 key를 입력
gmap_key = "AIzaSyC-ezB2J00Td105d4jqtdi2-JmZKuZ-5lY" 
gmaps = googlemaps.Client(key=gmap_key)


# 상위 10개 주유소 주소를 이용하여 위도/경도를 추출
lat = []
lng = []

for n in tqdm_notebook(oil_price_top10.index):
    try:
        tmp_add = str(oil_price_top10['주소'][n]).split('(')[0]
        tmp_map = gmaps.geocode(tmp_add)

        tmp_loc = tmp_map[0].get('geometry')
        lat.append(tmp_loc['location']['lat'])
        lng.append(tmp_loc['location']['lng'])
        
    except:
        lat.append(np.nan)
        lng.append(np.nan)
        print("Here is nan !")

# 추출된 위도/경도를 데이터 프레임에 추가        
oil_price_top10['lat'] = lat
oil_price_top10['lng'] = lng
oil_price_top10


# 하위 10개 주유소 주소를 이용하여 위도/경도를 추출
lat = []
lng = []

for n in tqdm_notebook(oil_price_bottom10.index):
    try:
        tmp_add = oil_price_bottom10['주소'][n].split('(')[0]
        tmp_map = gmaps.geocode(tmp_add)

        tmp_loc = tmp_map[0]['geometry']
        lat.append(tmp_loc['location']['lat'])
        lng.append(tmp_loc['location']['lng'])
        
    except:
        lat.append(np.nan)
        lng.append(np.nan)
        print("Here is nan !")
  
# 추출된 위도/경도를 데이터 프레임에 추가   
oil_price_bottom10['lat'] = lat
oil_price_bottom10['lng'] = lng
oil_price_bottom10


# folium 을 이용하여 지도위에 주유소 위치 marking
map = folium.Map(location=[37.5202, 126.975], zoom_start=10.5)

for n in oil_price_top10.index:
    if pd.notnull(oil_price_top10['lat'][n]):
        folium.CircleMarker([oil_price_top10['lat'][n], oil_price_top10['lng'][n]], 
                                  radius=15, color='#CD3181', 
                                  fill_color='#CD3181',
                                  fill=True).add_to(map)
    
for n in oil_price_bottom10.index:
    if pd.notnull(oil_price_bottom10['lat'][n]): 
        folium.CircleMarker([oil_price_bottom10['lat'][n], 
                                  oil_price_bottom10['lng'][n]], 
                                  radius=15, color='#3186cc', 
                                  fill_color='#3186cc',
                                  fill=True).add_to(map)
        
map.save('./result/주유소 위치.html')

import webbrowser
webbrowser.open_new('./result/주유소 위치.html')









