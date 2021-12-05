# /*
# __author__ = "Srikanth Kodali - skkodali@"
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
# */

from aws_cdk import (
    aws_iotsitewise as sitewise,
    core
)
import configparser

class SitewiseModelsAndAssetsStack(core.Stack):
    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        prop1 = sitewise.CfnAssetModel.AssetModelPropertyProperty(
            data_type = "DOUBLE",
            logical_id="gen1-id",
            name = "prop-1",
            type = sitewise.CfnAssetModel.PropertyTypeProperty(type_name = "Measurement")
        )
        asset_model_properties = [
            prop1
        ]

        sitewise_model = sitewise.CfnAssetModel(self, "SitewiseModels", asset_model_name = "GEN1", asset_model_properties = asset_model_properties)
        #sitewise_model
        print(sitewise_model)

        asset_properties = [
            sitewise.CfnAsset.AssetPropertyProperty(logical_id=prop1.logical_id, alias="/DayOneEnergyCorp/Generator/5/Power", notification_state="ENABLED")
        ]

        config = configparser.ConfigParser()
        sitewise_asset = sitewise.CfnAsset(self, "SitewiseAsset",
                                           asset_model_id = sitewise_model.attr_asset_model_id,
                                           asset_name = "Generator-5",
                                           asset_properties = asset_properties)

