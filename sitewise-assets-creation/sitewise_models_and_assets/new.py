# /*
__author__ = "Srikanth Kodali - skkodali@"
# */

from aws_cdk import (
    aws_iotsitewise as sitewise,
    core
)
import configparser
import pathlib
import string, random

file = pathlib.Path('config/sitewise-config.cfg')

main_asset_model_properties = []
config = configparser.ConfigParser()
if file.exists ():
    config.read(file)
else:
    print("Config file does not exists.")
    exit(1)

def get_asset_model_property(datatype, logicalid, name, unit_type):
    measurement_type = sitewise.CfnAssetModel.PropertyTypeProperty(type_name = "Measurement")
    measurement_definition = sitewise.CfnAssetModel.AssetModelPropertyProperty(
        data_type = datatype,
        logical_id= logicalid,
        name = name,
        unit = unit_type,
        type = measurement_type
    )
    return measurement_definition

def get_all_model_properties(model_name):
    asset_model_properties = []
    measurements_names = dict(config.items(model_name+"-measurements-names"))
    measurements_units = dict(config.items(model_name+"-measurements-units"))
    measurements_data_types = dict(config.items(model_name+"-measurements-data-types"))

    measurements_names_values = list(measurements_names.values())
    measurements_units_values = list(measurements_units.values())
    measurements_data_types_values = list(measurements_data_types.values())

    for measurement_name, measurement_unit, measurement_data_type in zip(measurements_names_values, measurements_units_values, measurements_data_types_values):
        #print("name : {} unit : {} and data_type: {} ".format(measurement_name, measurement_unit, measurement_data_type))
        asset_model_prop = get_asset_model_property(measurement_data_type, model_name + "-" + measurement_name + "-id", measurement_name, measurement_unit)
        #print("Asset model prop is : ")
        #print(asset_model_prop)
        asset_model_properties.append(asset_model_prop)

    #print("======================")
    #print(asset_model_properties)
    return asset_model_properties

def get_asset_aliases_properties(logical_id, alias_tag, notification):
    asset_alias_property_definition = sitewise.CfnAsset.AssetPropertyProperty(
        logical_id=logical_id,
        alias=alias_tag,
        notification_state=notification
    )
    return asset_alias_property_definition

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

class SitewiseModelsAndAssetsStack(core.Stack):
    def __init__(self, scope: core.Construct, construct_id: str, props, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        #create_sitewise_models(scope, construct_id)
        global main_asset_model_properties
        prop = config.items("models")
        sitewise_models = list(dict(prop).values())

        start_index = props[0]
        end_index = props[1]

        for sitewise_model in sitewise_models:
            main_asset_model_properties = get_all_model_properties(sitewise_model)
            sitewise_model_creation = sitewise.CfnAssetModel(self, id=sitewise_model, asset_model_name = sitewise_model, asset_model_properties = main_asset_model_properties)
            #get_all_asset_aliases_properties(sitewise_model, sitewise_model_creation)

            corp_name = config.get('organization', 'name')
            location = config.get('organization', 'plant-location')
            number_of_assets_per_model = config.getint('assets', 'number-of-assets-per-model')
            # sitewise.CfnAsset.AssetPropertyProperty(logical_id=prop1.logical_id, alias="/DayOneEnergyCorp/Generator/5/Power", notification_state="ENABLED")
            model_asset_alias_mappings = dict(config.items(sitewise_model+"-asset-alias-mappings"))

            model_asset_alias_mappings_keys = list(model_asset_alias_mappings.keys())
            model_asset_alias_mappings_values = list(model_asset_alias_mappings.values())

            model_num = 0
            for i in range(number_of_assets_per_model):
                #for i in range(5):
                #i = 0
                index = 0
                asset_aliases_properties = []
                for i in range(200):
                    for mappings_keys, mappings_values in zip(model_asset_alias_mappings_keys, model_asset_alias_mappings_values):
                        alias_tag = "/"+corp_name+"/"+location+"/"+sitewise_model+"/"+str(i)+ "/"+mappings_values
                        asset_model_prop = get_asset_aliases_properties(main_asset_model_properties[index].logical_id, alias_tag, "ENABLED")
                        asset_aliases_properties.append(asset_model_prop)
                        index += 1

                        print(get_asset_aliases_properties)

                    sitewise_asset_creation = sitewise.CfnAsset(self, id="SitewiseAsset-"+sitewise_model+"-"+id_generator(),
                                                                asset_model_id = sitewise_model_creation.attr_asset_model_id,
                                                                asset_name = sitewise_model+"-"+str(model_num),
                                                                asset_properties = asset_aliases_properties)

                    model_num += 1

#if __name__ == '__main__':
#    SitewiseModelsAndAssetsStack.create_sitewise_models()
#SitewiseModelsAndAssetsStack.get_all_model_properties("generator-model")