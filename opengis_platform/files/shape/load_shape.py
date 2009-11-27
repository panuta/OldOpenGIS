from django.contrib.gis.utils.layermapping import LayerMapping
from django.contrib.gis.gdal import DataSource
from opengis.models import ThailandProvince

ds = DataSource('changwat_region_Project.shp')

mapping = {
    'name_th' : 'TNAME',
    'name' : 'ENAME',
    'polygon' : 'POLYGON',
}

lm = LayerMapping(ThailandProvince, ds, mapping, encoding='tis-620')
lm.save(verbose=True)
