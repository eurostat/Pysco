from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsRuleBasedRenderer,
    QgsMarkerSymbol,
    QgsSymbolLayer,
    QgsSimpleMarkerSymbolLayer,
    QgsFeature,
    QgsGeometry
)
from qgis.PyQt.QtGui import QColor

def apply_custom_style(layer):
    # Root rule
    root_rule = QgsRuleBasedRenderer.Rule()

    # Rule for _T < 100
    rule_lt_100 = QgsRuleBasedRenderer.Rule()
    rule_lt_100.setFilterExpression('\"_T\" < 100')
    rule_lt_100.setSymbol(QgsMarkerSymbol.createSimple({
        'name': 'circle',
        'size': '300',  # size in map units (meters)
        'color_border': 'transparent'
    }))

    # Rule for _T >= 100
    rule_ge_100 = QgsRuleBasedRenderer.Rule()
    rule_ge_100.setFilterExpression('\"_T\" >= 100')
    rule_ge_100.setSymbol(QgsMarkerSymbol.createSimple({
        'name': 'circle',
        'size': '1200',  # size in map units (meters)
        'color_border': 'transparent'
    }))

    # Apply color based on perc_
    for rule in [rule_lt_100, rule_ge_100]:
        symbol = rule.symbol()
        for i in range(symbol.symbolLayerCount()):
            layer = symbol.symbolLayer(i)
            if isinstance(layer, QgsSimpleMarkerSymbolLayer):
                # Blue fill for perc_ < 80
                layer.setDataDefinedProperty(QgsSymbolLayer.PropertyFillColor, 
                                             QgsProperty.fromExpression('if(\"perc_\" < 80, \'blue\', \'red\')'))

    # Add rules to the root rule
    root_rule.appendChild(rule_lt_100)
    root_rule.appendChild(rule_ge_100)

    # Create and apply the renderer
    renderer = QgsRuleBasedRenderer(root_rule)
    layer.setRenderer(renderer)

    # Refresh the layer to apply changes
    layer.triggerRepaint()

# Load the layer (assuming it is already loaded in the QGIS project)
layer = QgsProject.instance().mapLayersByName('grid_1km_point')[0]

# Apply the custom style function
apply_custom_style(layer)
