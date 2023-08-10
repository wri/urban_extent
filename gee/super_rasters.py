import ee
import helpers as h
import data
import math
import re
from unidecode import unidecode
from pprint import pprint
ee.Initialize()



#
# CONFIG
#
"""""""""""""""""""""""""""""""""""""""""""""""""""
Note on STUDY_AREA_SCALE_FACTOR:

if A=a*b=w*a^2, and w=4*alpha
R(circle) ~ alpha * sqrt(A)
ratio=A(circle)/A ~ alpha^2 * pi 

* for w = 16, ratio ~ 12
* for w = 36, ratio ~ 30

Note that city centers might be far from "centered"
"""""""""""""""""""""""""""""""""""""""""""""""""""
STUDY_AREA_SCALE_FACTOR=20
# VECTOR_SCALE=100
VECTOR_SCALE=None
OFFSET=None
LIMIT=None
DRY_RUN=False
OFFSET=0
# LIMIT=500

# DRY_RUN=True
# OFFSET=500
# LIMIT=5000

"""
 RUN 1 ERRORS:  [4189, 2292, 1500, 2062]   
"""

# DRY_RUN=True


#
# CONSTANTS
#
# Set output image collection for all processed cities
#
# ROOT='projects/wri-datalab/cities/urban_land_use/data/dev'
ROOT='projects/wri-datalab/cities/urban_land_use/data'
# IC_ID=f'{ROOT}/builtup_density_GHSL_WSF1519_WC21'
# ROOT = 'users/emackres'
# IC_ID=f'{ROOT}/builtup_density_WSFevo_2015'
# IC_ID=f'{ROOT}/builtup_density_GHSL2023_2015'
# IC_ID=f'{ROOT}/builtup_density_GHSL_WSFunion_2015'
# IC_ID=f'{ROOT}/builtup_density_GHSL_WSFintersection_2015'
# IC_ID=f'{ROOT}/builtup_density_WSFevo'
# IC_ID=f'{ROOT}/builtup_density_GHSL-WSFunion'
# IC_ID=f'{ROOT}/builtup_density_GHSL-WSFunion_GHSLthresh2pct'
# IC_ID=f'{ROOT}/builtup_density_GHSL_GHSLthresh2pct'
# IC_ID=f'{ROOT}/builtup_density_GHSL_GHSLthresh5pct'
# IC_ID=f'{ROOT}/builtup_density_GHSL_GHSLthresh10pct'
# IC_ID=f'{ROOT}/builtup_density_GHSL-WSFunion_GHSLthresh2pct_WSFres'
# IC_ID=f'{ROOT}/builtup_density_GHSL-WSFunion_GHSLthresh2pct_GHSLres'
# IC_ID=f'{ROOT}/builtup_density_Kigali_GHSL_GHSLthresh10pct'
IC_ID=f'{ROOT}/builtup_density_GHSL_BUthresh10pct'







if VECTOR_SCALE:
  IC_ID=f'{IC_ID}-vs{VECTOR_SCALE}'


HALTON_TYPE_KEY='Locale sampling (0=Halton only, 1=Halton+)'
MAX_NNN_DISTANCE=2500
MAX_ERR=10
MINPIXS=10
SUBURBAN_BOUND=0.25
URBAN_BOUND=0.5
COM_SEED=1234
NB_COM_SAMPLES=5000
GROWTH_RATE=0.0666
DENSITY_RADIUS=564
DENSITY_UNIT='meters'
CENTROID_SEARCH_RADIUS=200
USE_TESTCITIES=False
USE_REGION_FILTER=False
USE_COMPLETED_FILTER=True
USE_COM=False
# USE_COM=True
COM_CITIES=[
  # 'Bidar',
  # 'Boras',
  # 'Budaun',
  # 'Chandausi',
  # 'Godhra',
  # # 'Ingolstad', ## <=== FAILED Error: Image.clip: The geometry for image clipping must not be empty. 
  # # 'Jaranwala', ## <=== FAILED Error: Image.clip: The geometry for image clipping must not be empty. 
  # # 'Johnson City', ## <=== FAILED Error: Image.clip: The geometry for image clipping must not be empty. 
  # 'La Victoria',
  # 'Mahendranagar',
  # 'Salzgitter',
  # 'Sawai Madhopur',
  # 'Tadepalligudem',
  # 'Tando Adam',
  # # 'Thunder Bay',
  # 'Yeosu'
  ]

NEW_CENTER_CITIES_CENTROIDS=ee.Dictionary({
  'Bidar': ee.Geometry.Point([77.52078709614943,17.91547247737295]),
  # 'Boras': ee.Geometry.Point([12.938561020772944,57.720750492018205]), 
  'Boras': ee.Geometry.Point([12.94152909517508,57.72269986139307]), #alternative centroid
  'Budaun': ee.Geometry.Point([79.12604991161326,28.03265316498389]),
  'Chandausi': ee.Geometry.Point([78.78058247689171,28.448365699750184]),
  'Godhra': ee.Geometry.Point([73.61165263489295,22.776999673547973]),
  'Ingolstad': ee.Geometry.Point([11.426204876844523,48.76507718332393]),
  'Jaranwala': ee.Geometry.Point([73.42116841076808,31.336663434272804]),
  'Johnson City': ee.Geometry.Point([-82.35209572307961,36.316573488567336]),
  'Poughkeepsie-Newburgh': ee.Geometry.Point([-73.93297541879508,41.7040681411346]),
  'Thunder Bay': ee.Geometry.Point([-89.24631353030803,48.383971133391135]),
  'La Victoria': ee.Geometry.Point([-67.3305393088188,10.228463012210497]),
  'Mahendranagar': ee.Geometry.Point([80.18115644779526,28.96697665223218]),
  'Salzgitter': ee.Geometry.Point([10.349910259625208,52.15521892854932]),
  'Sawai Madhopur': ee.Geometry.Point([76.35285818958363,26.018074137423426]),
  'Tadepalligudem': ee.Geometry.Point([81.53108158157536,16.811913769903555]),
  'Tando Adam': ee.Geometry.Point([68.65803649614065,25.762683447436615]),
  'Yeosu': ee.Geometry.Point([127.66493701053658,34.762903988911475]),
  'Gandhinagar': ee.Geometry.Point([72.64005494165245,23.21867028416773]),
  'Satkhira': ee.Geometry.Point([89.07194075069569,22.717846552580642]),
  'Valsad': ee.Geometry.Point([72.92758546565402,20.607285530986754]),
  'Ipswich': ee.Geometry.Point([1.1554162793974454,52.052821477844404]),
  'Bimbo': ee.Geometry.Point([18.521348031397014,4.328534006175151]),
  # 'Billings': ee.Geometry.Point([-108.5025730262764,45.784598612542126]),
  'Billings': ee.Geometry.Point([-108.50067893095184,45.786345365857734]), #alternative centroid
  'Giessen': ee.Geometry.Point([8.670619693008112,50.58343761451457]),
  'El Centro--Calexico, CA                                                                             ': ee.Geometry.Point([-115.56038988156142,32.79286256561882]),
  'Clarksville': ee.Geometry.Point([-87.35841285561979,36.52914617995032]),
  'Barnstable Town': ee.Geometry.Point([-70.28320083696039,41.65598777966051]),
  # 'Yuma': ee.Geometry.Point([-114.62665249045568,32.692377527395266]),
  'Yuma': ee.Geometry.Point([-114.62853956542635,32.704680060058834]), #alternative centroid
  'South Lyon-Howell-Brighton': ee.Geometry.Point([-83.78094233241319,42.52974952964617]),
  # 'Aberdeen-Havre de Grace-Bel Air': ee.Geometry.Point([-76.16867584833608,39.506544432212074]),
  'Aberdeen-Havre de Grace-Bel Air': ee.Geometry.Point([-76.16709854779967,39.50839272273559]), #alternative centroid
  # failed under GHSL10pct runs
  'Evpatoriya': ee.Geometry.Point([33.365710964210336,45.19421580338069]),
  'Jagdalpur': ee.Geometry.Point([82.02425198674257,19.088325507126125]),
  'Male': ee.Geometry.Point([73.50692301285711,4.171185236260825]),
  'Moncton': ee.Geometry.Point([-64.77742662666752,46.08857439979821]),
  'Cayenne': ee.Geometry.Point([-52.33198615900898,4.940096831911476]),
  'Ottappalam': ee.Geometry.Point([76.37593172251849,10.773660271424795]),
  'Sunchonn': ee.Geometry.Point([125.93430009790484,39.42582405887188]),
  'Sambalpur': ee.Geometry.Point([83.97330824785912,21.465209994433234]),
  'Bokaro Steel City': ee.Geometry.Point([86.14564361652216,23.667304104607762]),
  'Nay Pyi Taw': ee.Geometry.Point([96.11973911325958,19.744494778674444]),

})
NEW_CENTER_CITIES=NEW_CENTER_CITIES_CENTROIDS.keys()
USE_NEW_CENTER_CITIES=False


""" ERIC CENTROIDS
 'Bidar', [77.52078709614943,17.91547247737295]
 'Boras', [12.938561020772944,57.720750492018205]
 'Budaun', [79.12604991161326,28.03265316498389]
 'Chandausi', [78.78058247689171,28.448365699750184]
 'Godhra', [73.61165263489295,22.776999673547973]
 'Ingolstad', [11.426204876844523,48.76507718332393]
 'Jaranwala', [73.42116841076808,31.336663434272804]
 'Johnson City', [-82.35209572307961,36.316573488567336]
 'La Victoria', [-67.3305393088188,10.228463012210497]
 'Mahendranagar', [80.18115644779526,28.96697665223218]
 'Salzgitter', [10.349910259625208,52.15521892854932]
 'Sawai Madhopur', [76.35285818958363,26.018074137423426]
 'Tadepalligudem', [81.53108158157536,16.811913769903555]
 'Tando Adam', [68.65803649614065,25.762683447436615]
 'Thunder Bay', [-89.24631353030803,48.383971133391135]
 'Yeosu' [127.66493701053658,34.762903988911475]

New additions 6/3/2023 - missing or very small builtup density images 
  'Gandhinagar', [72.64005494165245,23.21867028416773]
  'Poughkeepsie-Newburgh', [-73.93297541879508,41.7040681411346]
  'Satkhira', [89.07194075069569,22.717846552580642]
  'Valsad', [72.92758546565402,20.607285530986754]
  'Ipswich', [1.1554162793974454,52.052821477844404]
  'Boras', [12.938771515859585,57.722630559655784]
  'Bimbo', [18.521348031397014,4.328534006175151]
  'Billings', [-108.5025730262764,45.784598612542126]
  'Giessen', [8.670619693008112,50.58343761451457]
  'El Centro--Calexico, CA', [-115.56038988156142,32.79286256561882]
  'Clarksville', [-87.35841285561979,36.52914617995032]
  'Barnstable Town', [-70.28320083696039,41.65598777966051]
  'Yuma', [-114.62665249045568,32.692377527395266]
  'South Lyon-Howell-Brighton', [-83.78094233241319,42.52974952964617]
  'Aberdeen-Havre de Grace-Bel Air', [-76.16867584833608,39.506544432212074]

New additions 8/9/2023 - Cities that work in some later year(s), but for 1980 receive Error: Image.clip: The geometry for image clipping must not be empty. (Error code: 3)
  'Abuja': ee.Geometry.Point([7.478280522539826,9.063242749572446]),
  'Yantai, Shandong': ee.Geometry.Point([121.3749378997016,37.547713687836136]), 
  'Malappuram': ee.Geometry.Point([76.08188061368155,11.04189898978775]), 
  'Nashik': ee.Geometry.Point([73.79145731999836,20.000012251988963]), 
  'Palembang': ee.Geometry.Point([104.76365120290319,-2.9796579529336444]), 
  'Taizhou, Zhejiang': ee.Geometry.Point([121.43429069821823,28.6817640387459]), 
  'Yancheng, Jiangsu': ee.Geometry.Point([120.13168862294013,33.394676035552955]), 
  'Islamabad': ee.Geometry.Point([73.04056229885364,33.68780139164149]), 
  'Dongying, Shandong': ee.Geometry.Point([118.50351106829504,37.45873900992769]), 
  'Zamboanga City': ee.Geometry.Point([122.0762901968634,6.937038761068384]), 
  'Rajshahi': ee.Geometry.Point([88.58521451461779,24.373335615864278]), 
  'Warangal': ee.Geometry.Point([79.59920807579847,17.98366119193612]), 
  'Aden': ee.Geometry.Point([45.0083038082666,12.792403911840374]), 
  'Lilongwe': ee.Geometry.Point([33.77344389179475,-13.97754300371363]), 
  'Jinhua, Zhejiang': ee.Geometry.Point([119.64028627257649,29.10402766701154]), 
  'Yixing, Jiangsu': ee.Geometry.Point([119.8132470013679,31.369521760803412]), 
  'Yichun, Heilongjiang': ee.Geometry.Point([128.8894324851581,47.72415021954703]), 
  'Uyo': ee.Geometry.Point([7.92176004833856,5.032193499857169]), 
  'Mangalore': ee.Geometry.Point([74.83509800462366,12.864616697377642]), 
  'Jiujiang, Jiangxi': ee.Geometry.Point([115.97424022409739,29.719992498318497]), 
  'Zhoushan, Zhejiang': ee.Geometry.Point([122.23816470490492,29.969200590789747]), 
  'Bacolod': ee.Geometry.Point([122.94906706835545,10.66794952770812]), 
  'Erdos, Inner Mongolia': ee.Geometry.Point([109.99582280020206,39.81559591604334]), 
  # 'Feira De Santana': ee.Geometry.Point(), # GHSL model problem 
  'Linhai, Zhejiang': ee.Geometry.Point([121.12606568700242,28.846819764887197]), 
  'Nasiriyah': ee.Geometry.Point([46.252282948154,31.044915158338185]), 
  'Matamoros': ee.Geometry.Point([-103.23035765665854,25.529377881382633]), 
  'Bazhong, Sichuan': ee.Geometry.Point([106.76211868650547,31.85258212620844]), 
  'Tongchuan, Shaanxi': ee.Geometry.Point(), 
  'Sanya, Hainan': ee.Geometry.Point(), 
  'Temecula-Murrieta': ee.Geometry.Point(), 
  'Iloilo City': ee.Geometry.Point(), 
  'Yongcheng, Henan': ee.Geometry.Point(), 
  'Port Sudan': ee.Geometry.Point(), 
  'Yamunanagar': ee.Geometry.Point(), 
  'Las Palmas': ee.Geometry.Point(), 
  'Ahmadnagar': ee.Geometry.Point(), 
  'Ziyang, Sichuan': ee.Geometry.Point(), 
  'Buenaventura': ee.Geometry.Point(), 
  'Meishan, Sichuan': ee.Geometry.Point(), 
  'Pattaya, Bang Lamung': ee.Geometry.Point(), 
  'Guangan, Sichuan': ee.Geometry.Point(), 
  'Habra': ee.Geometry.Point(), 
  'Iquique': ee.Geometry.Point(), 
  'Karimnagar': ee.Geometry.Point(), 
  'Aizawl': ee.Geometry.Point(), 
  'Thanjavur': ee.Geometry.Point(), 
  'Dindigul': ee.Geometry.Point(), 
  'Wah': ee.Geometry.Point(), 
  'Anand': ee.Geometry.Point(), 
  'Ratlam': ee.Geometry.Point(), 
  'Yakutsk': ee.Geometry.Point(), 
  'Pengzhou, Sichuan': ee.Geometry.Point(), 
  'Los Mochis': ee.Geometry.Point(), 
  'Long Xuyen': ee.Geometry.Point(), 
  'Lianyuan, Hunan': ee.Geometry.Point(), 
  'Hurghada': ee.Geometry.Point(), 
  'Paramaribo': ee.Geometry.Point(), 
  'Yanbu': ee.Geometry.Point(), 
  'Jayapura': ee.Geometry.Point(),  
  'Milton Keynes': ee.Geometry.Point(), 
  'Udhagamandalam': ee.Geometry.Point(), 
  'Kanhangad': ee.Geometry.Point(), 
  'Palmas': ee.Geometry.Point(), 
  'Buon Me Thoat': ee.Geometry.Point(), 
  'Mage': ee.Geometry.Point(), 
  'Tokchon': ee.Geometry.Point(), 
  'Proddatur': ee.Geometry.Point(), 
  'Mahbubnagar': ee.Geometry.Point(), 
  'Haldia': ee.Geometry.Point(), 
  'Hechi, Guangxi': ee.Geometry.Point(), 
  'Fenhu, Jiangsu': ee.Geometry.Point(), 
  'Siem Reap city': ee.Geometry.Point(), 
  'Liangshi, Hunan': ee.Geometry.Point(), 
  'Hardoi': ee.Geometry.Point(), 
  'Sullana': ee.Geometry.Point(), 
  'Chhindwara': ee.Geometry.Point(), 
  'La Ceiba': ee.Geometry.Point(), 
  'Zhili, Zhejiang': ee.Geometry.Point(), 
  '10th of Ramadan City': ee.Geometry.Point(), 
  'Kolar Gold Fields': ee.Geometry.Point(), 
  'Jiande, Zhejiang': ee.Geometry.Point(), 
  'Bhuj': ee.Geometry.Point(), 
  'Bobai, Guangxi': ee.Geometry.Point(), 
  'Botshabelo': ee.Geometry.Point(), 
  'Shivapuri': ee.Geometry.Point(), 
  'Bintulu': ee.Geometry.Point(), 
  'Neyveli': ee.Geometry.Point(), 
  'Samawah': ee.Geometry.Point(), 
  'Weitang, Zhejiang': ee.Geometry.Point(), 
  'Madanapalle': ee.Geometry.Point(), 
  'Shuangjiang, Chongqing': ee.Geometry.Point(), 
  'Anju': ee.Geometry.Point(), 
  'Shimla': ee.Geometry.Point(), 
  'Chengguan, Anhui': ee.Geometry.Point(), 
  'Phan Rang': ee.Geometry.Point(), 
  'Sirajgang': ee.Geometry.Point(), 
  'Robertson Pet': ee.Geometry.Point(), 
  'Chengguan, Guizhou': ee.Geometry.Point(), 
  'Jalpaiguri': ee.Geometry.Point(), 
  'Balurghat': ee.Geometry.Point(), 
  'Luziania': ee.Geometry.Point(), 
  'Mancherial': ee.Geometry.Point(), 
  'Zhongwei, Ningxia': ee.Geometry.Point(), 
  'Zhongwei, Ningxia': ee.Geometry.Point(), 
  'Dundee': ee.Geometry.Point(), 
  'Lashio': ee.Geometry.Point(), 
  'Aguas Lindas de Goias': ee.Geometry.Point(), 
  'San Cristobal de las Casas': ee.Geometry.Point(), 
  'Iraklion': ee.Geometry.Point(), 
  'Nampa': ee.Geometry.Point(), 
  'Thanesar': ee.Geometry.Point(), 
  'Beichuan, Sichuan': ee.Geometry.Point(), 
  'Beichuan, Sichuan': ee.Geometry.Point(), 
  'Mughalsarai': ee.Geometry.Point(), 
  'Bhadravati': ee.Geometry.Point(), 
  'Quevedo': ee.Geometry.Point(), 
  'Weitang, Zhejiang': ee.Geometry.Point(), 
  'Damoh': ee.Geometry.Point(), 
  'Satara': ee.Geometry.Point(), 
  'Viet Tri': ee.Geometry.Point(), 
  'Chhatarpur': ee.Geometry.Point(), 
  'Yongan, Chongqing': ee.Geometry.Point(), 
  'Basirhat': ee.Geometry.Point(), 
  'Fushi, Sichuan': ee.Geometry.Point(), 
  'Ankleshwar': ee.Geometry.Point(), 
  'Wudan, Inner Mongolia': ee.Geometry.Point(), 
  'Jishan, Anhui': ee.Geometry.Point(), 
  'Khairpur': ee.Geometry.Point(), 
  'Gonda': ee.Geometry.Point([81.96501485068623,27.132157339565275]), 
  'Bankura': ee.Geometry.Point(), 
  'Jimma': ee.Geometry.Point(), 
  'Kolar': ee.Geometry.Point(), 
  'Yima, Henan': ee.Geometry.Point(), 
  'Linghai, Liaoning': ee.Geometry.Point(), 
  'Fuji, Sichuan': ee.Geometry.Point(), 
  'Lalitpur': ee.Geometry.Point(), 
  'Manzanillo': ee.Geometry.Point(), 
  'Darjiling': ee.Geometry.Point(), 
  'Chowmohoni': ee.Geometry.Point(), 
  'Jizan': ee.Geometry.Point(), 
  'Fengcheng, Shanxi': ee.Geometry.Point(), 
  'Georgetown': ee.Geometry.Point(), 
  'Gaoliangjian, Jiangsu': ee.Geometry.Point(), 
  'Raniganj': ee.Geometry.Point(), 
  'Shunling, Hunan': ee.Geometry.Point(), 
  'Bangtou, Fujian': ee.Geometry.Point(), 
  'Ekibastuz': ee.Geometry.Point(), 
  'Alipurduar': ee.Geometry.Point(), 
  'Changanassery': ee.Geometry.Point(), 
  'Cua': ee.Geometry.Point(),
  'Marica': ee.Geometry.Point(), 
  'Motihari': ee.Geometry.Point(), 
  'Alagoinhas': ee.Geometry.Point(), 
  'Barreiras': ee.Geometry.Point(), 
  'Wanzhi, Anhui': ee.Geometry.Point(), 
  'Bhairab': ee.Geometry.Point(), 
  'Chunxi, Jiangsu': ee.Geometry.Point(), 
  'Yuting, Jiangxi': ee.Geometry.Point(), 
  'Quibdo': ee.Geometry.Point(), 
  'Shengfang, Hebei': ee.Geometry.Point(), 
  'Pithampur': ee.Geometry.Point(), 
  'Dumaguete': ee.Geometry.Point(), 
  'Dharmavaram': ee.Geometry.Point(), 
  'Bole, Xinjiang': ee.Geometry.Point(), 
  'Longxun, Fujian': ee.Geometry.Point(), 
  'Churu': ee.Geometry.Point(), 
  'Gudivada': ee.Geometry.Point(), 
  'Kipushi': ee.Geometry.Point(), 
  'Chikmagalur': ee.Geometry.Point(), 
  'Yuyue, Hubei': ee.Geometry.Point(), 
  'Pudukkottai': ee.Geometry.Point(),
  'Hoshangabad': ee.Geometry.Point(), 
  'Butwal': ee.Geometry.Point(), 
  'Vaniyambadi': ee.Geometry.Point(), 
  'Fotang, Zhejiang': ee.Geometry.Point(), 
  'Songyang, Yunnan': ee.Geometry.Point(), 
  'Amanfrom': ee.Geometry.Point(), 
  'Ambur': ee.Geometry.Point(), 
  'Haiyu, Jiangsu': ee.Geometry.Point(), 
  'Hongguo, Guizhou': ee.Geometry.Point(), 
  'Meishan, Anhui': ee.Geometry.Point(), 
  'Myeik': ee.Geometry.Point(), 
  'Baerum': ee.Geometry.Point(), 
  'Funchal': ee.Geometry.Point(), 
  'Noakhali': ee.Geometry.Point(), 
  'Matou, Guangxi': ee.Geometry.Point(), 
  'Dera Ismail Khan': ee.Geometry.Point(), 
  'Kothamangalam': ee.Geometry.Point(), 
  'Nazilli': ee.Geometry.Point(), 
  'Hecheng, Zhejiang': ee.Geometry.Point(), 
  'Chujiang, Hunan': ee.Geometry.Point(), 
  'Achinsk': ee.Geometry.Point(), 
  'Tangjiawan, Guangdong': ee.Geometry.Point(), 
  'Firozpur': ee.Geometry.Point(), 
  'Xiazhen, Shandong': ee.Geometry.Point(), 
  'Jiaxiang, Shandong': ee.Geometry.Point(), 
  'Huayuan, Hubei': ee.Geometry.Point(), 
  'Chengguan, Henan': ee.Geometry.Point(), 
  'Aflou': ee.Geometry.Point(), 
  'Jingchuan, Anhui': ee.Geometry.Point(), 
  'Gaosha Town, Hunan': ee.Geometry.Point(), 
  'Paoy Pet': ee.Geometry.Point(), 
  'Wardha': ee.Geometry.Point(), 
  'Ranibennur': ee.Geometry.Point(), 
  'Lufu, Yunnan': ee.Geometry.Point(), 
  'Ocumaredel Tuy': ee.Geometry.Point(), 
  'Ishwardi': ee.Geometry.Point(), 
  'Mormugao': ee.Geometry.Point(), 
  'Maoping, Hubei': ee.Geometry.Point(), 
  'Anuradhapura': ee.Geometry.Point(), 
  'Fengting, Fujian': ee.Geometry.Point(), 
  'Navapolack': ee.Geometry.Point(), 
  ....

Missing cities needed?
  'San Jose, CA', [-121.89081977186525,37.33545249552986] # or alternative population needed for 'San Francisco-Oakland', 7150739

Cities for which current algorythm may be excluding important urban clusters:
  'Brasilia',
  'Rio de Janerio'
  
  """

test_cities=[
  # "Dhaka",
  # "Hong Kong, Hong Kong",
  # "Wuhan, Hubei", 
  # "Bangkok",
  # "Cairo",
  # "Minneapolis-St. Paul", 
  # "Baku", 
  # "Bogota", 
  # "Kinshasa", 
  # "Madrid",
  # "Shanghai, Shanghai",
  # "New York-Newark",
  "Kigali",
]

PI=ee.Number.expression('Math.PI')

PPOLICY={
  'builtup': 'mode',
  'density': 'mean',
}

FIT_PARAMS=ee.Dictionary({
    'East Asia and the Pacific (EAP)':
        {'intercept': 6.844359028945421,
         'offset': 1.791926332415592,
         'score': 0.7375592105175173,
         'slope': 0.9005954865250072},
    'Europe and Japan (E&J)':
        {'intercept': 8.69494278584463,
         'offset': 1.3765398939200644,
         'score': 0.8282268575495757,
         'slope': 0.7909946578460973},
    'Land-Rich Developed Countries (LRDC)':
        {'intercept': 8.815887085043352,
         'offset': 0.7586211992962966,
         'score': 0.8838364233047373,
         'slope': 0.8478077958637914},
    'Latin America and the Caribbean (LAC)':
        {'intercept': 7.304395215265931,
         'offset': 0.6775184545295296,
         'score': 0.9053339438612787,
         'slope': 0.8450702344066737},
    'South and Central Asia (SCA)':
        {'intercept': 7.749750012982069,
         'offset': 1.8054134632856353,
         'score': 0.7487748140929972,
         'slope': 0.7759435551490513},
    'Southeast Asia (SEA)':
        {'intercept': 6.82616432868558,
         'offset': 0.9686848696989969,
         'score': 0.8143299893665737,
         'slope': 0.8944201392252237},
    'Sub-Saharan Africa (SSA)':
        {'intercept': 7.406971326898002,
         'offset': 0.9996327596950607,
         'score': 0.765974222675155,
         'slope': 0.8380261492251289},
    'Western Asia and North Africa (WANA)':
        {'intercept': 6.781561303548658,
         'offset': 0.6353709001657144,
         'score': 0.9426792637978123,
         'slope': 0.877341649095773}
})


#
# IMPORTS
#
# City centroids
# CITY_DATA=ee.FeatureCollection('projects/wri-datalab/AUE/AUE200_Universe')
CITY_DATA=ee.FeatureCollection('projects/wri-datalab/AUE/AUEUniverseofCities')

# Built-up layer options
GHSL=ee.Image('JRC/GHSL/P2016/BUILT_LDSMT_GLOBE_V1')
WSF=ee.ImageCollection("users/mattia80/WSF2015_v1").reduce(ee.Reducer.firstNonNull())
WC21=ee.ImageCollection("ESA/WorldCover/v200").reduce(ee.Reducer.firstNonNull())
WSF19=ee.ImageCollection("users/mattia80/WSF2019_20211102").reduce(ee.Reducer.firstNonNull())
# DW=ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1").select('label').filterDate('2022-03-01','2022-11-01').mode()

# https://gee-community-catalog.org/projects/wsf/
wsf_evo = ee.ImageCollection("projects/sat-io/open-datasets/WSF/WSF_EVO")
wsf_evoImg = wsf_evo.reduce(ee.Reducer.firstNonNull()).selfMask().rename(['bu'])

GHSL2023release = ee.Image("users/emackres/GHS_BUILT_S_MT_2023_100_BUTOT_MEDIAN")
# Map.addLayer(GHSL2023release.gte(500).reduce(ee.Reducer.anyNonZero()).selfMask(),{palette:['red','blue']},"GHSLraw",false)
# b1: 1950, b2: 1955, b3: 1960, b4: 1965, b5: 1970, b6: 1975, b7: 1980, b8: 1985, b9: 1990, b10: 1995, b11: 2000, b12: 2005, b13: 2010, b14: 2015, b15: 2020, b16: 2025, b17: 2030)
# count = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17]
count = [17,16,15,14,13,12,11,10,9,8,7,6,5,4,3,2,1]
year = [1950,1955,1960,1965,1970,1975,1980,1985,1990,1995,2000,2005,2010,2015,2020,2025,2030]
# select pixel built-up density threshold for GHSL2023release
BuiltAreaThresh = 1000 # minimum m2 built out of possible 10000 for each GHSL grid cell included
GHSL2023releaseYear = GHSL2023release.gte(BuiltAreaThresh).selfMask().reduce(ee.Reducer.count()).remap(count,year).selfMask().rename(['bu']) 

# set the built-up year for which to produce extents
mapYear = 1980

# input options for built-up layers
wsfyear = wsf_evoImg.updateMask(wsf_evoImg.lte(mapYear)).gt(0)
GHSLyear = GHSL2023releaseYear.updateMask(GHSL2023releaseYear.lte(mapYear)).gt(0)
GHSL_WSFcomb = wsfyear.unmask().gt(0).add(GHSLyear.unmask().gt(0)).selfMask()
GHSL_WSFintersect = GHSL_WSFcomb.updateMask(GHSL_WSFcomb.eq(2)).gt(0)
GHSL_WSFunion = GHSL_WSFcomb.updateMask(GHSL_WSFcomb.gte(1)).gt(0)

# obtain projection, CRS and Transform for input layer
# _proj=GHSL.select('built').projection().getInfo()
_proj=GHSL2023release.projection().getInfo()
# _proj=wsf_evo.first().projection().getInfo()

# GHSL_CRS=_proj['crs']
GHSL_CRS= "EPSG:3857" #"ESRI:54009" # for use with GHSL2023release image which doesn't have CRS in metadata. 
GHSL_TRANSFORM=_proj['transform']
print("GHSL PROJ:",GHSL_CRS,GHSL_TRANSFORM)


if VECTOR_SCALE:
  TRANSFORM=None
else:
  TRANSFORM=GHSL_TRANSFORM
  VECTOR_SCALE=None
#
# Select built-up IMAGE
#
# BU_GHSL=GHSL.select(['built']).gte(3).selfMask().rename(['bu']).toUint8()
# BU_WSF=WSF.eq(255).selfMask().rename(['bu']).toUint8()
# BU_WC21=WC21.eq(50).selfMask().rename(['bu']).toUint8()
# BU_WSF19=WSF19.eq(255).selfMask().rename(['bu']).toUint8()
# # BU_DW=DW.eq(6).selfMask().rename(['bu']).toUint8()
# BU=ee.ImageCollection([
#     BU_WSF,
#     BU_GHSL,
#     BU_WC21,
#     BU_WSF19
#     ]).reduce(ee.Reducer.firstNonNull()).rename('bu')
BU = GHSLyear

# create band ("builtup") with binary builtup value
IS_BUILTUP=BU.gt(0).rename(['builtup'])

# create band ("density") with the percent of pixels that are built-up within radius of each pixel
_usubu_rededucer=ee.Reducer.mean()
_usubu_kernel=ee.Kernel.circle(
  radius=DENSITY_RADIUS, 
  units=DENSITY_UNIT, 
  normalize=True,
  magnitude=1
)
_density=IS_BUILTUP.unmask(0).reduceNeighborhood(
  reducer=_usubu_rededucer,
  kernel=_usubu_kernel,
  skipMasked=True,
)
# create band ("builtup_class") with built-up classification (urban, suburban, rural) for each built-up pixel based on its "density" value
_usubu=ee.Image(0).where(_density.gte(SUBURBAN_BOUND).And(_density.lt(URBAN_BOUND)),1).where(_density.gte(URBAN_BOUND),2).rename(['builtup_class'])
_density=_density.multiply(100).rename(['density'])
BU_DENSITY_CAT=_usubu.addBands([_density,IS_BUILTUP]).toUint8()
# create image of all urban or suburban builtup pixels that have at least MINPIXS neighbors that are also urban or suburban builtup pixels
BU_CONNECTED=IS_BUILTUP.multiply(_usubu.gt(0)).selfMask().connectedPixelCount(MINPIXS).eq(MINPIXS).selfMask()
BU_LATLON=BU_CONNECTED.addBands(ee.Image.pixelLonLat())


#
# UTILS
#
def get_info(**kwargs):
  return ee.Dictionary(kwargs).getInfo()


def print_info(**kwargs):
  print(get_info(**kwargs))


def safe_keys(name):
  return ee.String(name).replace(' ','__','g').replace('#','NB','g')


#
# DATA PREP
#
prop_names=CITY_DATA.first().propertyNames()
prop_names=prop_names.remove(HALTON_TYPE_KEY)
safe_prop_names=prop_names.map(safe_keys)
CITY_DATA=CITY_DATA.select(prop_names,safe_prop_names)

# filter options to select subsets of cities
COM_FILTER=ee.Filter.inList('City__Name',COM_CITIES)
if USE_COM:
  CITY_DATA=CITY_DATA.filter(COM_FILTER)
else:
  CITY_DATA=CITY_DATA#.filter(COM_FILTER.Not())

TESTCITIES_FILTER=ee.Filter.inList('City__Name',test_cities)
if USE_TESTCITIES:
  CITY_DATA=CITY_DATA.filter(TESTCITIES_FILTER)
else:
  CITY_DATA=CITY_DATA

REGION_FILTER=ee.Filter.eq('Reg_Name','East Asia and the Pacific (EAP)') # 'Land-Rich Developed Countries (LRDC)'
if USE_REGION_FILTER:
  CITY_DATA=CITY_DATA.filter(REGION_FILTER)
else:
  CITY_DATA=CITY_DATA

NCC_FILTER=ee.Filter.inList('City__Name',NEW_CENTER_CITIES)
if USE_NEW_CENTER_CITIES:
  CITY_DATA=CITY_DATA.filter(NCC_FILTER)
else:
  CITY_DATA=CITY_DATA.filter(NCC_FILTER.Not())

if LIMIT:
  CITY_DATA=CITY_DATA.limit(LIMIT,'Pop_2010',False)#.filter(ee.Filter.inList('City__Name',['Yingtan, Jiangxi']))
else:
  CITY_DATA=CITY_DATA

# filter to limit cities to be run to those not already in the output ImageCollection. 
COMPLETED_IDS=ee.ImageCollection(IC_ID).aggregate_array('City__ID__Number')
COMPLETED_FILTER=ee.Filter.And(ee.Filter.inList('City__ID__Number',COMPLETED_IDS),ee.Filter.equals('builtup_year',mapYear))
COMPLETED_CITIES_LIST=ee.ImageCollection(IC_ID).filter(COMPLETED_FILTER).aggregate_array('City__ID__Number')

if USE_COMPLETED_FILTER:
  CITY_DATA=CITY_DATA.filter(ee.Filter.inList('City__ID__Number',COMPLETED_CITIES_LIST).Not())
else:
  CITY_DATA=CITY_DATA

pprint(CITY_DATA.aggregate_array('City__Name').getInfo())
pprint(CITY_DATA.aggregate_array('Reg_Name').getInfo())
# raise

#
# HELPERS
#
def get_area(pop,region):
    pop=ee.Number(pop).log()
    params=ee.Dictionary(FIT_PARAMS.get(region))
    slope=params.getNumber('slope')
    intercept=params.getNumber('intercept')
    log_area=slope.multiply(pop).add(intercept)
    return log_area.exp()


def get_radius(area):
  return ee.Number(area).divide(PI).sqrt()


def nearest_non_null(centroid):
    distance_im=ee.FeatureCollection([centroid]).distance(MAX_NNN_DISTANCE)
    bounds=ee.Geometry.Point(centroid.coordinates()).buffer(MAX_NNN_DISTANCE,MAX_ERR)
    nearest=distance_im.addBands(ee.Image.pixelLonLat()).updateMask(BU).reduceRegion(
      reducer=ee.Reducer.min(3),
      geometry=bounds,
      crs=GHSL_CRS,
      crsTransform=GHSL_TRANSFORM
      )
    return [nearest.getNumber('min1'), nearest.getNumber('min2')]


def get_com(geom):
  pts=BU_LATLON.sample(
    region=geom,
    scale=10,
    numPixels=NB_COM_SAMPLES,
    seed=COM_SEED,
    dropNulls=True,
    geometries=False
  )
  return ee.Algorithms.If(
    pts.size(),
    ee.Geometry.Point([
      pts.aggregate_mean('longitude'),
      pts.aggregate_mean('latitude')]),
    geom.centroid(10)
  )


def get_crs(point):
  coords=point.coordinates()
  lon=ee.Number(coords.get(0))
  lat=ee.Number(coords.get(1))
  zone=ee.Number(32700).subtract((lat.add(45).divide(90)).round().multiply(100)).add(((lon.add(183)).divide(6)).round())
  zone=zone.toInt().format()
  return ee.String('EPSG:').cat(zone)


def get_influence_distance(area):
  return ee.Number(area).sqrt().multiply(GROWTH_RATE)


def polygon_feat_boundry(feat):
  feat=ee.Feature(feat)
  geom=ee.Geometry.Polygon(feat.geometry().coordinates().get(0))
  return ee.Feature(geom)

 
def set_geom_type(feat):
  feat=ee.Feature(feat)
  return feat.set('geomType',feat.geometry().type()) 


def geom_feat(g):
  return ee.Feature(ee.Geometry(g))


def coords_feat(coords):
  return ee.Feature(ee.Geometry.Polygon(coords))


def flatten_geometry_collection(feat):
  feat=ee.Feature(feat)
  geoms=feat.geometry().geometries()
  return ee.FeatureCollection(geoms.map(geom_feat))


def flatten_multipolygon(feat):
  coords_list=ee.Feature(feat).geometry().coordinates()  
  return ee.FeatureCollection(coords_list.map(coords_feat))


def fill_polygons(feats):
  feats=feats.map(set_geom_type)
  gc_filter=ee.Filter.eq('geomType', 'GeometryCollection')
  mpoly_filter=ee.Filter.eq('geomType', 'MultiPolygon')
  poly_filter=ee.Filter.eq('geomType', 'Polygon')
  gc_data=feats.filter(gc_filter).map(flatten_geometry_collection).flatten()
  mpoly_data=feats.filter(mpoly_filter).map(flatten_multipolygon).flatten()
  poly_data=feats.filter(poly_filter)
  feats=ee.FeatureCollection([
      poly_data,
      gc_data,
      mpoly_data]).flatten()
  feats=feats.map(set_geom_type).filter(poly_filter)
  feats=feats.map(polygon_feat_boundry)
  return feats

  
def buffered_feat(feat):
  feat=ee.Feature(feat)
  area=feat.area(MAX_ERR)
  return buffered_feat_area(feat,area)


def buffered_feat_area(feat,area):
  feat=ee.Feature(feat)
  area=ee.Number(area)
  infl=get_influence_distance(area)
  return feat.buffer(infl,MAX_ERR).set('buffer',infl)



#
# MAIN
#
def get_circle_data(feat):
  feat=ee.Feature(feat)
  cname=feat.get('City__Name')
  centroid=feat.geometry()
  crs=get_crs(centroid)
  region=ee.String(feat.get('Reg_Name')).trim()
  pop=feat.getNumber('Pop_2010')
  est_area=get_area(pop,region)
  est_influence_distance=get_influence_distance(est_area)
  scaled_area=est_area.multiply(STUDY_AREA_SCALE_FACTOR)
  radius=get_radius(scaled_area)
  study_bounds=centroid.buffer(radius,MAX_ERR)
  center_of_mass=ee.Geometry(get_com(study_bounds))
  study_bounds=center_of_mass.buffer(radius,MAX_ERR)
  if USE_COM:
    bu_centroid_xy=ee.List(nearest_non_null(center_of_mass))
    _use_inspected_centroid=False
  elif USE_NEW_CENTER_CITIES:
    print('ncc',cname.getInfo())
    inspected_centroid=NEW_CENTER_CITIES_CENTROIDS.get(cname)
    inspected_centroid=ee.Geometry(inspected_centroid)
    bu_centroid_xy=ee.List(nearest_non_null(inspected_centroid))
    _use_inspected_centroid=True
  else:
    bu_centroid_xy=ee.List(nearest_non_null(centroid))    
    _use_inspected_centroid=False
  bu_centroid=ee.Geometry.Point(bu_centroid_xy)
  return ee.Feature(
      study_bounds,
      {
        'city_center': centroid,
        'bu_city_center': bu_centroid,
        'crs': crs,
        'center_of_mass': center_of_mass,
        'est_area': est_area,
        'scaled_area': scaled_area,
        'study_radius': radius,
        'est_influence_distance': est_influence_distance,
        'study_area_scale_factor': STUDY_AREA_SCALE_FACTOR,
        'use_center_of_mass': USE_COM,
        'use_inspected_centroid': _use_inspected_centroid,
        'builtup_year': mapYear
    }).copyProperties(feat)


def vectorize(data):
  data=ee.Feature(data)
  study_area=data.geometry()
  bu_centroid=ee.Geometry(data.get('bu_city_center'))
  # create vectors from BU_CONNECTED image where it overlaps with city study_area
  feats=BU_CONNECTED.reduceToVectors(
    reducer=ee.Reducer.countEvery(),
    crs=GHSL_CRS,
    scale=VECTOR_SCALE,
    crsTransform=TRANSFORM,
    geometry=study_area,
    maxPixels=1e13,
    bestEffort=True
  )
  centroid_filter=ee.Filter.withinDistance(
    distance=CENTROID_SEARCH_RADIUS,
    leftField='.geo',
    rightValue=bu_centroid, 
    maxError=MAX_ERR
  )
  # buffer each vector feature by its influence distance (function of its area)
  feats=ee.FeatureCollection(feats.map(buffered_feat))
  # dissolve all vectors to merge overlapping influence area features
  geoms=feats.geometry(MAX_ERR).dissolve(MAX_ERR).geometries()
  feats=ee.FeatureCollection(geoms.map(geom_feat))
  # filter to retain only merged vector features that are within CENTROID_SEARCH_RADIUS of bu_centroid 
  feats=feats.filter(centroid_filter)
  # fill holes in vector polygons
  feats=fill_polygons(feats)
  # return vector polygons as a single feature
  return ee.Feature(feats.geometry()).copyProperties(data)


def get_super_feat(feat):
  feat=get_circle_data(feat)
  feat=vectorize(feat)
  return feat


#
# EXPORT
#
# FILTER CITIES HACK
#
# CITIES=[
#   'Dubai',
# ]
# CITY_DATA=CITY_DATA.filter(ee.Filter.inList('City__Name',CITIES))
# print(CITY_DATA.size().getInfo())


pprint(CITY_DATA.sort('City__Name').aggregate_array('City__Name').getInfo())
# print('--')


# FAILED_IDS=[
#     # 1126,
#     # 1057,
#     # 2701,
#     2516,#-
#     # 1750,
#     # 4467,
#     2431,#-
#     # 2600,
#     # 2063,
#     # 2728,
#     # 1241,
#     # 5156,
#     # 5013,
#     # 1012,
#     # 5146,
#     # 1111,
#     # 5047,
#     # 2464,
#     4765,#-
#     # 4618
# ]
# CITY_DATA=CITY_DATA.filter(ee.Filter.inList('City__ID__Number',FAILED_IDS))
# pprint(CITY_DATA.sort('City__Name').aggregate_array('City__Name').getInfo())
# print('--')
# raise


print(f'DEST: {IC_ID}')
# CITY_DATA=CITY_DATA.sort('Pop_2010')
CITY_DATA=CITY_DATA.sort('Pop_2010',False)
if OFFSET and LIMIT:
  LIMIT=LIMIT+OFFSET
IDS=CITY_DATA.aggregate_array('City__ID__Number').getInfo()[OFFSET:LIMIT]
FAILURES=[]
# 
for i,ident in enumerate(IDS):
  # get on city centroid feature 
  feat=ee.Feature(CITY_DATA.filter(ee.Filter.eq('City__ID__Number',ident)).first())
  city_name=feat.getString('City__Name').getInfo()
  print('\n'*1)
  print(f'{i}: {city_name} [{ident}]')
  # get feature for city boundary as defined by vectorize function
  feat=ee.Feature(get_super_feat(feat))
  # print_info(super_feat=feat.toDictionary())
  print('='*100)
  asset_name=unidecode(f'{city_name}-{ident}-{mapYear}')
  asset_name=re.sub(r'[^A-Za-z0-9\-\_]+', '', asset_name)
  bu=ee.Image(BU_DENSITY_CAT.copyProperties(feat))
  geom=feat.geometry()
  # Export image to output ImageCollection with 3 builtup information bands for area within the city boundary 
  task=ee.batch.Export.image.toAsset(
    image=bu,
    description=asset_name,
    assetId=f'{IC_ID}/{asset_name}',
    pyramidingPolicy=PPOLICY,
    region=geom,
    scale=VECTOR_SCALE, 
    crs=GHSL_CRS,
    crsTransform=GHSL_TRANSFORM,
    maxPixels=1e13, #1e11
  )
  if DRY_RUN:
    print('-- dry_run:',asset_name)
  else:
    try:
      task.start()
      print('TASK SUBMITTED:',asset_name,task.status(),'\n')
    except Exception as e:
      print('\n'*2)
      print('*'*100)
      print('*'*100)
      print('\n'*1)
      print(f'CITY_NAME: {city_name}')
      print(f'CITY_ID: {ident}')
      print(f'ASSET_NAME: {asset_name}')
      print(f'ERROR: {e}')
      print('\n'*1)
      print('*'*100)
      print('*'*100)
      print('\n'*2)
      FAILURES.append(ident)
  print('\n'*1)
else:
  print('-')


print('COMPLETE')
print('NB_ERRORS:',len(FAILURES))
print(FAILURES)



