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
  'Tongchuan, Shaanxi': ee.Geometry.Point([108.97886725893385,34.912815304164866]), 
  'Sanya, Hainan': ee.Geometry.Point([109.49646174716976,18.25739391478926]), 
  'Temecula-Murrieta': ee.Geometry.Point([-117.1548531038731,33.49608093668129]), 
  'Iloilo City': ee.Geometry.Point([122.57619224057632,10.692190551032605]), 
  'Yongcheng, Henan': ee.Geometry.Point([116.43948966757146,33.92335674422714]), 
  # 'Port Sudan': ee.Geometry.Point(), # GHSL model problem 
  'Yamunanagar': ee.Geometry.Point([77.28705786152865,30.13161296771658]), 
  'Las Palmas': ee.Geometry.Point([-15.425431689019783,28.15132087846939]), 
  'Ahmadnagar': ee.Geometry.Point([74.73740023858795,19.09234571105569]), 
  'Ziyang, Sichuan': ee.Geometry.Point([104.64683534160156,30.121222096840697]), 
  'Buenaventura': ee.Geometry.Point([-77.0245753502145,3.8822565856119104]), 
  'Meishan, Sichuan': ee.Geometry.Point([103.83420951654202,30.04494883675573]), 
  'Pattaya, Bang Lamung': ee.Geometry.Point([100.88579760887355,12.9353767202565]), 
  'Guang'an, Sichuan': ee.Geometry.Point([106.63827892993167,30.47635384542008]), 
  'Habra': ee.Geometry.Point([88.6572796514051,22.841217134963387]), 
  # 'Iquique': ee.Geometry.Point(), # GHSL model problem 
  'Karimnagar': ee.Geometry.Point([79.12963068822373,18.438979139100713]), 
  # 'Aizawl': ee.Geometry.Point(), # rural in 1980
  'Thanjavur': ee.Geometry.Point([79.13704784176936,10.787366842642031]), 
  'Dindigul': ee.Geometry.Point([77.97133364836422,10.360707284914254]), 
  'Wah': ee.Geometry.Point([72.7497765336954,33.77337050426921]), 
  'Anand': ee.Geometry.Point([72.95950601852336,22.556151619708643]), 
  'Ratlam': ee.Geometry.Point([75.03557950251906,23.333863277037846]), 
  # 'Yakutsk': ee.Geometry.Point(), # GHSL model problem 
  'Pengzhou, Sichuan': ee.Geometry.Point([103.94017442609707,30.986599248800818]), 
  'Los Mochis': ee.Geometry.Point([-108.99119756782892,25.786213993076075]), 
  'Long Xuyen': ee.Geometry.Point([105.44254177509923,10.382952676869156]), 
  'Lianyuan, Hunan': ee.Geometry.Point([111.66595064594073,27.690509688793448]), 
  'Hurghada': ee.Geometry.Point([33.82443314923356,27.248258224734627]), 
  'Paramaribo': ee.Geometry.Point([-55.16342723604126,5.825445744845321]), 
  'Yanbu': ee.Geometry.Point([38.05625399383388,24.085255044698545]), 
  'Jayapura': ee.Geometry.Point([140.71535493310628,-2.5612073032863285]),  
  'Milton Keynes': ee.Geometry.Point([-0.7528375876019266,52.04236427093296]), 
  'Udhagamandalam': ee.Geometry.Point([76.7000104948069,11.408405675541424]), 
  'Kanhangad': ee.Geometry.Point([75.08606440947625,12.323815416335593]), 
  'Palmas': ee.Geometry.Point([-48.32337339327039,-10.184077496520429]), # possible GHSL model problem 
  'Buon Me Thoat': ee.Geometry.Point([108.04330839170343,12.683621138384744]), 
  'Mage': ee.Geometry.Point([-43.039390302271144,-22.65649794663944]), 
  'Tokchon': ee.Geometry.Point([126.30518756705335,39.75867562614185]), 
  'Proddatur': ee.Geometry.Point([78.55143063930467,14.750771852281707]), 
  'Mahbubnagar': ee.Geometry.Point([77.98805954091664,16.74482820070142]), 
  'Haldia': ee.Geometry.Point([88.10401764757688,22.04048176368915]), 
  'Hechi, Guangxi': ee.Geometry.Point([108.05245421323114,24.697534623371652]), 
  'Fenhu, Jiangsu': ee.Geometry.Point([120.84733390061464,31.053257991703546]), 
  'Siem Reap city': ee.Geometry.Point([103.85418440760162,13.354747710768363]), 
  'Liangshi, Hunan': ee.Geometry.Point([111.74112129949387,27.247701079233547]), 
  'Hardoi': ee.Geometry.Point([80.12649518181401,27.39434210879812]), 
  'Sullana': ee.Geometry.Point([-80.68875026959199,-4.896863600777863]), 
  'Chhindwara': ee.Geometry.Point([78.94040823728278,22.053724555378746]), 
  'La Ceiba': ee.Geometry.Point([-86.79172154785468,15.785443665488494]), 
  'Zhili, Zhejiang': ee.Geometry.Point([120.25586969185073,30.878699595892858]), 
  '10th of Ramadan City': ee.Geometry.Point([31.7425918666052,30.285826816195275]), 
  'Kolar Gold Fields': ee.Geometry.Point([78.12887124922943,13.136808130202057]), # original centroid in "Kolar" instead of "Kolar Gold Fields"
  'Jiande, Zhejiang': ee.Geometry.Point([119.27021601384536,29.474593192687]), 
  'Bhuj': ee.Geometry.Point([69.67003390139584,23.249996517457316]), 
  'Bobai, Guangxi': ee.Geometry.Point([109.97714909503249,22.274700447742724]), 
  'Botshabelo': ee.Geometry.Point([26.728687265534642,-29.262751755307107]), 
  'Shivapuri': ee.Geometry.Point([77.65686150252502,25.42517927697791]), 
  'Bintulu': ee.Geometry.Point([113.03993083390277,3.1837271812184995]), # possible GHSL model problem 
  'Neyveli': ee.Geometry.Point([79.48071267154572,11.538963509336664]), 
  'Samawah': ee.Geometry.Point([45.28161046809783,31.31555140609793]), # duplicate city
  # 'Weitang, Zhejiang': ee.Geometry.Point(), # two missing cities with same name, may need to recode by City ID
  # 'Weitang, Zhejiang': ee.Geometry.Point(), # two missing cities with same name, may need to recode by City ID
  'Madanapalle': ee.Geometry.Point([78.50094612522804,13.55513040260974]), # possible GHSL model problem 
  'Shuangjiang, Chongqing': ee.Geometry.Point([108.71986426692655,30.92689670667686]), 
  'Anju': ee.Geometry.Point([125.68334874234691,39.65382925380534]), 
  'Shimla': ee.Geometry.Point([77.17114337841222,31.102450524706352]), 
  'Chengguan, Anhui': ee.Geometry.Point([117.19497699443556,32.95965897629651]), 
  'Phan Rang': ee.Geometry.Point([108.98876587685064,11.56154138283224]), 
  'Sirajgang': ee.Geometry.Point([89.70609149771096,24.458315296507298]), 
  'RobertsonPet': ee.Geometry.Point([78.27256887178822,12.959291264081994]), 
  'Chengguan, Guizhou': ee.Geometry.Point([106.02904023821081,27.032147088073874]), 
  'Jalpaiguri': ee.Geometry.Point([88.72455598197737,26.52631122257753]), 
  'Balurghat': ee.Geometry.Point([88.77712851947156,25.222546218343428]), 
  'Luziania': ee.Geometry.Point([-47.95492538786642,-16.25464580496828]), 
  'Mancherial': ee.Geometry.Point([79.44679501073952,18.875405683552366]), 
  'Zhongwei, Ningxia': ee.Geometry.Point([105.18412461495434,37.51517184194114]), 
  'Zhongwei, Ningxia': ee.Geometry.Point([105.18412461495434,37.51517184194114]), # duplicate centroid
  'Dundee': ee.Geometry.Point([-2.970441802079613,56.462677235175335]), 
  'Lashio': ee.Geometry.Point([97.7504970468847,22.937931754116917]), 
  'Aguas Lindas de Goias': ee.Geometry.Point([-48.265382638811104,-15.761892747634654]), # possible GHSL model problem 
  'San Cristobal de las Casas': ee.Geometry.Point([-92.63651697883235,16.737413297931823]), 
  'Iraklion': ee.Geometry.Point([25.133354101933357,35.33896769184916]), # possible GHSL model problem 
  'Nampa': ee.Geometry.Point([-116.56253942400451,43.57726155131625]), 
  'Thanesar': ee.Geometry.Point([76.8426467142052,29.971303470826268]), 
  'Beichuan, Sichuan': ee.Geometry.Point([104.47941316358167,31.591390967496743]), 
  'Beichuan, Sichuan': ee.Geometry.Point([104.47941316358167,31.591390967496743]), # duplicate centroid
  'Mughalsarai': ee.Geometry.Point([83.11707684805359,25.283448263221178]), 
  'Bhadravati': ee.Geometry.Point([75.70482760506047,13.848209747164503]), 
  'Quevedo': ee.Geometry.Point([-79.46225633950499,-1.0240525744272888]), 
  'Damoh': ee.Geometry.Point([79.44063000871924,23.83588746012982]), 
  'Satara': ee.Geometry.Point([73.99093015363363,17.68337024339524]), 
  'Viet Tri': ee.Geometry.Point([105.38853348876825,21.320689446606387]), 
  'Chhatarpur': ee.Geometry.Point([79.59066605655205,24.91628968934399]), 
  #'Yongan, Chongqing': ee.Geometry.Point(), # No existing centroid? 
  'Basirhat': ee.Geometry.Point([88.86531468907195,22.661654370209916]), 
  'Fushi, Sichuan': ee.Geometry.Point([104.99012100670018,29.18284568824579]), 
  'Ankleshwar': ee.Geometry.Point([72.99260320839001,21.63166922192213]), 
  'Wudan, Inner Mongolia': ee.Geometry.Point([119.02412258879161,42.930535608578076]), 
  'Jishan, Anhui': ee.Geometry.Point([118.3292610157374,30.92231962776307]), 
  'Khairpur': ee.Geometry.Point([68.76104577245928,27.53186605034018]), 
  'Gonda': ee.Geometry.Point([81.96501485068623,27.132157339565275]), 
  'Bankura': ee.Geometry.Point([87.07125774711564,23.23370941332484]), 
  'Jimma': ee.Geometry.Point([36.82992323633357,7.676439972268592]), 
  'Kolar': ee.Geometry.Point([78.12887124922943,13.136808130202057]), 
  'Yima, Henan': ee.Geometry.Point([111.87097812372912,34.742166564465705]), 
  'Linghai, Liaoning': ee.Geometry.Point([121.11399566493397,28.846500900385657]), 
  'Fuji, Sichuan': ee.Geometry.Point([105.3770566127296,29.150981918335756]), 
  'Lalitpur': ee.Geometry.Point([78.42051749560233,24.691707212958157]), 
  'Manzanillo': ee.Geometry.Point([-104.35262437097077,19.119805486886637]), 
  'Darjiling': ee.Geometry.Point([88.26708512051962,27.038737508615593]), 
  'Chowmohoni': ee.Geometry.Point([91.12193004518645,22.94522981486578]), # original centroid in wrong region
  'Jizan': ee.Geometry.Point([42.541911291511965,16.89329648209869]), 
  'Fengcheng, Shanxi': ee.Geometry.Point([112.02250678087194,37.4365231886347]), # multiple cities with same name
  # 'Georgetown': ee.Geometry.Point(), # multiple cities with same name # centroid looks good, possible GHSL model problem 
  'Gaoliangjian, Jiangsu': ee.Geometry.Point([118.84571330212547,33.29772124432854]), 
  'Raniganj': ee.Geometry.Point([87.11569164858312,23.6088232485505]), 
  'Shunling, Hunan': ee.Geometry.Point([111.93772315602936,25.591981047187556]), 
  'Bangtou, Fujian': ee.Geometry.Point([118.74891639378922,25.425925567214794]), 
  # 'Ekibastuz': ee.Geometry.Point(), # centroid looks good, possible GHSL model problem 
  'Alipurduar': ee.Geometry.Point([89.52348347408696,26.480177957710836]), 
  'Changanassery': ee.Geometry.Point([76.53960704117867,9.446530180083736]), 
  # 'Cua': ee.Geometry.Point(), # centroid looks good, possible GHSL model problem 
  'Marica': ee.Geometry.Point([-42.81872820279865,-22.916790150978482]), 
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
  'Rio de Janerio',
  'Jayapura',
  'Yanbu'
  
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



