# coding=utf-8
"""" Utility functions and classes for data management

.. note:: This program is free software; you can redistribute it and/or modify
    it under the terms of the Mozilla Public License 2.0.

"""

__author__ = 'lorenzetti@gis3w.it'
__date__ = '2023-12-27'
__copyright__ = 'Copyright 2015 - 2023, Gis3w'
__license__ = 'MPL 2.0'

from qgis.PyQt.QtCore import (
    QDate,
    QRegExp,
    Qt,
    QVariant
)

from matplotlib.dates import date2num, num2date
import numpy as np


def get_base_plot_data(qgs_feature, qgs_layer, qps_timeseries_layer=None):
    """
    Get base plot data

    :param qgs_feature: QgsFeature
    :param qps_timeseries_layer: QgsVectorLayer
    :return type: dict
    :return: Dict of base plot data
    """

    attrs = qgs_feature.attributes()

    x, y = [], []  # lists containg x,y values
    infoFields = []  # list of the fields containing info to be displayed

    ps_source = qgs_layer.source()
    ps_fields = qgs_layer.dataProvider().fields()

    providerType = qgs_layer.providerType()
    uri = ps_source
    subset = ""

    # if providerType == 'ogr' and ps_source.lower().endswith(".shp"):
    # Shapefile
    for idx, fld in enumerate(ps_fields):
        if QRegExp("D\\d{8}", Qt.CaseInsensitive).indexIn(fld.name()) < 0:
            # info fields are all except those containing dates
            infoFields.append(fld.name())
        else:

            x_date = QDate.fromString(fld.name()[1:], "yyyyMMdd").toPyDate()
            value_original = attrs[idx]
            if isinstance(value_original, QVariant):
                value = value_original.value()
            else:
                value = value_original
            # Only for date >= qps_timeseries_layer.min_date and <= qps_timeseries_layer.max_date
            if qps_timeseries_layer:
                if x_date >= qps_timeseries_layer.min_date and x_date <= qps_timeseries_layer.max_date:
                    try:
                        x.append(x_date)
                        y.append(float(value))
                    except ValueError:
                        continue
            else:
                try:
                    x.append(x_date)
                    y.append(float(value))
                except ValueError:
                    continue

    if qps_timeseries_layer and qps_timeseries_layer.detrending:
        y = np.array(y) - np.array(get_line_trend_plot_data(x, y)[1])

    # If std properties is true add std as error_y
    error_y = []
    if qps_timeseries_layer and  qps_timeseries_layer.std:
        std = np.std(np.array(y))
        error_y = [std for p in y]


    return {
        'x': x,
        'y': y,
        'error_y': error_y,
        'fields': infoFields
    }

def get_line_trend_plot_data(x, y, d=1):
    """
    Get x and y values for trend line (line and poly)

    Following code from QGIS desktop plugin PS Tme series
    https://gitlab.com/faunalia/ps-speed/-/blob/master/ps-speed/pstimeseries_dlg.py#L204

    :param x: x values (datetime)
    :param y: y values (float)
    :param d: degree of polynomial
    :return type: tuple
    """

    x = date2num(np.array(x))
    y = np.array(y)
    p = np.polyfit(x, y, d)
    return num2date(x), np.polyval(p, x)