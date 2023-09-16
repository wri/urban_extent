import ee
ee.Initialize()

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
  
# New additions 8/9/2023 - Cities that work in some later year(s), but for 1980 receive Error: Image.clip: The geometry for image clipping must not be empty. (Error code: 3)
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
  'Guang\'an, Sichuan': ee.Geometry.Point([106.63827892993167,30.47635384542008]), 
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
  # 'Weitang, Zhejiang': ee.Geometry.Point(), # two missing cities with same name, recoded by City ID
  # 'Weitang, Zhejiang': ee.Geometry.Point(), # two missing cities with same name, recoded by City ID
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
  'Motihari': ee.Geometry.Point([84.9034942765557,26.64424539343763]), 
  # 'Alagoinhas': ee.Geometry.Point(), # centroid looks good, possible GHSL model problem 
  'Barreiras': ee.Geometry.Point([-45.00058767051543,-12.148496388675781]), 
  'Wanzhi, Anhui': ee.Geometry.Point([118.56811554164432,31.145818740882557]), 
  'Bhairab': ee.Geometry.Point([90.98246568283793,24.05543916330353]), 
  'Chunxi, Jiangsu': ee.Geometry.Point([118.87450763850858,31.32604548469979]), 
  'Yuting, Jiangxi': ee.Geometry.Point([116.68784727831236,28.695160226266914]), 
  # 'Quibdo': ee.Geometry.Point(), # centroid looks good, possible GHSL model problem 
  'Shengfang, Hebei': ee.Geometry.Point([116.68873047083383,39.06018347672968]), 
  'Pithampur': ee.Geometry.Point([75.6792526843316,22.61082699145564]), 
  'Dumaguete': ee.Geometry.Point([123.30719034670932,9.306935923908668]), # possible GHSL model problem 
  'Dharmavaram': ee.Geometry.Point([77.72126620153887,14.414458125602739]), 
  # 'Bole, Xinjiang': ee.Geometry.Point(), # centroid looks good, possible GHSL model problem 
  'Longxun, Fujian': ee.Geometry.Point([118.24332638719892,25.492609943479106]), 
  'Churu': ee.Geometry.Point([74.96765787869523,28.305272358379206]), 
  'Gudivada': ee.Geometry.Point([80.99392092379932,16.43456219693887]), 
  'Kipushi': ee.Geometry.Point([27.24724550110125,-11.755284184490362]), 
  'Chikmagalur': ee.Geometry.Point([75.77351614773391,13.319283145777824]), 
  'Yuyue, Hubei': ee.Geometry.Point([113.90423752186902,29.97623692044738]), 
  'Pudukkottai': ee.Geometry.Point([78.82047582806996,10.382436025483042]), # original centroid in wrong region
  'Hoshangabad': ee.Geometry.Point([77.71514174931906,22.758577721210205]), 
  'Butwal': ee.Geometry.Point([83.46397386924575,27.70250879937087]), 
  # 'Vaniyambadi': ee.Geometry.Point(), # centroid looks good, possible GHSL model problem 
  'Fotang, Zhejiang': ee.Geometry.Point([120.01431421641483,29.205024638918918]), 
  'Songyang, Yunnan': ee.Geometry.Point([103.03614350443604,25.339298793507883]), 
  'Amanfrom': ee.Geometry.Point([-0.5412186494886218,6.192953188722099]), 
  # 'Ambur': ee.Geometry.Point(), # centroid looks good, possible GHSL model problem 
  'Haiyu, Jiangsu': ee.Geometry.Point([120.7984389455408,31.752944431536996]), 
  # 'Hongguo, Guizhou': ee.Geometry.Point(), # centroid looks good, possible GHSL model problem 
  'Meishan, Anhui': ee.Geometry.Point([115.90259636898394,31.849146954929974]), 
  'Myeik': ee.Geometry.Point([98.59723668822582,12.441805859991252]), 
  'Baerum': ee.Geometry.Point([10.501653899017462,59.94663269319062]), 
  # 'Funchal': ee.Geometry.Point(), # centroid looks good, possible GHSL model problem 
  'Noakhali': ee.Geometry.Point([91.09706670097057,22.868936634057867]), 
  'Matou, Guangxi': ee.Geometry.Point([107.57980897099333,23.31804885957945]), 
  'Dera Ismail Khan': ee.Geometry.Point([70.90181229337973,31.827464321785904]), 
  'Kothamangalam': ee.Geometry.Point([76.62722662691942,10.064228236315223]), 
  'Nazilli': ee.Geometry.Point([28.32500314396256,37.91713842339767]), 
  'Hecheng, Zhejiang': ee.Geometry.Point([120.284544023292,28.142873828872464]), 
  'Chujiang, Hunan': ee.Geometry.Point([111.37232717400593,29.587881805303734]), 
  # 'Achinsk': ee.Geometry.Point(), # centroid looks good, possible GHSL model problem 
  'Tangjiawan, Guangdong': ee.Geometry.Point([113.54145560138647,22.382792683944597]), 
  'Firozpur': ee.Geometry.Point([74.62117319951466,30.92691442831906]), 
  'Xiazhen, Shandong': ee.Geometry.Point([117.11848878780731,34.80945239401825]), 
  'Jiaxiang, Shandong': ee.Geometry.Point([116.33662804394508,35.396950373034265]), 
  'Huayuan, Hubei': ee.Geometry.Point([113.96852040855958,31.251871168585666]), 
  'Chengguan, Henan': ee.Geometry.Point([116.36683684379712,33.93564859928222]), 
  'Aflou': ee.Geometry.Point([2.1017010792282065,34.11550026668995]), 
  'Jingchuan, Anhui': ee.Geometry.Point([118.39896795971129,30.689924658920734]), 
  'Gaosha Town, Hunan': ee.Geometry.Point([110.57362116354828,27.06377183540011]), 
  # 'Paoy Pet': ee.Geometry.Point(), # centroid looks good, new city?!
  'Wardha': ee.Geometry.Point([78.59935650898937,20.7399202273765]), 
  'Ranibennur': ee.Geometry.Point([75.63039698402467,14.62140098281825]), 
  'Lufu, Yunnan': ee.Geometry.Point([103.26657774875106,24.760899989674606]), 
  'Ocumare del Tuy': ee.Geometry.Point([-66.77532045477442,10.120453940559678]), # possible GHSL model problem 
  'Ishwardi': ee.Geometry.Point([89.06408162157643,24.129940042649665]), 
  'Mormugao': ee.Geometry.Point([73.81069629284072,15.39770034507545]), 
  # 'Maoping, Hubei': ee.Geometry.Point(), # possible GHSL model problem? new city?
  'Anuradhapura': ee.Geometry.Point([80.40241807362723,8.322070556320547]), 
  'Fengting, Fujian': ee.Geometry.Point([118.8519403174272,25.24922269137163]), 
  'Navapolack': ee.Geometry.Point([28.660830849335436,55.531190460873546])
})


NEW_CENTER_CITIES_CENTROIDS_IDs=ee.Dictionary({
    2387: ee.Geometry.Point([121.42434810223214,29.28432786493907]),
    2216: ee.Geometry.Point([119.67405912161787,29.79404252932662])
})


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


Missing cities needed?
  'San Jose, CA', [-121.89081977186525,37.33545249552986] # or alternative population needed for 'San Francisco-Oakland', 7150739

Cities for which current algorythm may be excluding important urban clusters:
  'Brasilia',
  'Rio de Janerio',
  'Jayapura',
  'Yanbu'
  
  """
