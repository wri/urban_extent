import ee
ee.Initialize()

NEW_INSPECTED_CENTROIDS_IDS=ee.Dictionary({
#   '10248': ee.Geometry.Point([96.185, 16.870]),#Yangon???
#   '9905': ee.Geometry.Point([90.79, 24.43]),#Kishoreganj check
#   '702': ee.Geometry.Point([-84.173, 39.706]),#Dayton check
#   '3289': ee.Geometry.Point([22.585, 51.23]),#Lublin check
  '115': ee.Geometry.Point([-102.54, 22.758]),#Zacatecas check
#   '541': ee.Geometry.Point([-90.58, 41.525]),#Davenport check
#   '656': ee.Geometry.Point([-81.11, 32.055]),#Savannah check
  '5250': ee.Geometry.Point([47.52, 42.964]),#Makhachkala check COM
  '2125': ee.Geometry.Point([3.297, 6.6]),#Lagos
  })
