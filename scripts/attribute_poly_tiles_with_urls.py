####################################
#   File name: attribute_poly_tiles_with_urls.py
#   About: Attributes Imagery and LiDAR polygon tile reference geometry with file url's
#   Author: Geoff Taylor | Imagery & Remote Sensing Team | Esri
#   Date created: 01/21/2021
#   Date last modified: 01/26/2021
#   Python Version: 3.7
####################################

from arcpy.management import AddField, CopyFeatures, Delete
from os.path import join, split
from arcpy import AddError, env, CheckOutExtension, CheckInExtension, ExecuteError, GetMessages
import pandas as pd
from arcpy import da
from pathlib import Path

env.overwriteOutput = True


def process():
    class LicenseError(Exception):
        pass

    try:
        if CheckExtension("ImageAnalyst") == "Available":
            CheckOutExtension("ImageAnalyst")
        else:
            # raise a custom exception
            raise LicenseError

        # System Parameters
        tile_name = "FileName"

        # Begin Script
        temp_fc = join("in_memory", "temp_fc")
        CopyFeatures(in_fc, temp_fc)
        for f in file_names:
            AddField(temp_fc, f, "TEXT")

        df = pd.read_excel(in_xlsx, index_col=0)

        def attribute_tile(in_feature_class, in_tile_name, in_df, in_name, xlsx_row_name=xlsx_row_name):
            with da.UpdateCursor(in_feature_class, [in_tile_name, in_name]) as cursor:
                for fc_r in cursor:
                    for df_i, df_r in in_df.iterrows():
                        url = df_r[xlsx_row_name]
                        n = Path(url).stem
                        t_name = fc_r[0]
                        t_n = Path(t_name).stem
                        if n.startswith(in_name) and t_n in n:
                            fc_r[1] = url
                    cursor.updateRow(fc_r)

        # Attribute the LiDAR Derivatives
        for n in file_names:
            attribute_tile(temp_fc, tile_name, df, n)

        def attribute_tile_lidar(in_feature_class, in_tile_name, in_df, in_name, xlsx_row_name=xlsx_row_name):
            with da.UpdateCursor(in_feature_class, [in_tile_name, in_name]) as cursor:
                for fc_r in cursor:
                    for df_i, df_r in in_df.iterrows():
                        url = df_r[xlsx_row_name]
                        n = split(url)[1]
                        t_name = fc_r[0]
                        if n == t_name:
                            fc_r[1] = url
                    cursor.updateRow(fc_r)

        # Attribute the LiDAR tile now
        AddField(temp_fc, in_lidar_format, "TEXT")
        attribute_tile_lidar(temp_fc, tile_name, df, in_lidar_format, xlsx_row_name=xlsx_row_name)

        '''
        # Print Fields for debugging/assessing results of above operations
        file_names.append(in_lidar_format)
        print(file_names)
        with da.SearchCursor(temp_fc, file_names) as cursor:
            for fc_r in cursor:
                print(fc_r)
        '''

        # Delete Pandas Dataframe from Memory
        del df

        # Copy in_memory temporary feature class to output location
        CopyFeatures(temp_fc, out_fc)

        # Delete Temporary Feature Class
        Delete(temp_fc)

        # Check back in Image Analyst license
        CheckInExtension("ImageAnalyst")
    except LicenseError:
        AddError("ImageAnalyst license is unavailable")
        print("ImageAnalyst license is unavailable")
    except ExecuteError:
        AddError(GetMessages(2))
        print(GetMessages(2))


def strlist2list(file_names):
    if ";" in file_names:
        return file_names.split(";")
    else:
        return [file_names]


if __name__ == "__main__":
    debug = False
    if debug:
        in_fc = r'C:\Users\geof7015\Documents\ArcGIS\Projects\Ohio_LiDAR_Demo\Ohio_LiDAR_Demo.gdb\LiDAR_Processed_PointFileInf'
        file_names = ['building_dsm', 'building_ndsm', 'dsm', 'dtm', 'ndsm']
        in_lidar_format = 'zlas'
        in_xlsx = r'C:\Users\geof7015\Documents\ArcGIS\Projects\Ohio_LiDAR_Demo\s3_bucket_files3_4.xlsx'
        xlsx_row_name = 'full_path'
        out_fc = r'C:\Users\geof7015\Documents\ArcGIS\Projects\Ohio_LiDAR_Demo\Ohio_LiDAR_Demo.gdb\letsTestIt'
    else:
        from arcpy import GetParameterAsText
        in_fc = GetParameterAsText(0)
        file_names = strlist2list(GetParameterAsText(1))
        in_lidar_format = GetParameterAsText(2)
        in_xlsx = GetParameterAsText(3)
        xlsx_row_name = 'full_path'
        out_fc = GetParameterAsText(4)
    process()
