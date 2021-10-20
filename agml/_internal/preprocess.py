import os
import sys
import json
import glob
import shutil

import cv2
import numpy as np
import pandas as pd

from shutil import copytree

from tqdm import tqdm
from PIL import Image

from agml.utils.io import create_dir, nested_dir_list, get_dir_list, get_file_list
from agml._internal.process_utils import read_txt_file, get_image_info, get_label2id
from agml._internal.process_utils import convert_bbox_to_coco, get_coco_annotation_from_obj, convert_xmls_to_cocojson
from agml._internal.process_utils import mask_annotation_per_bbox, move_segmentation_dataset
from agml._internal.process_utils import create_sub_masks, create_sub_mask_annotation_per_bbox
from agml.utils.data import load_public_sources

class PreprocessData(object):
    """Internal data preprocessing class."""
    def __init__(self, data_dir):
        self.data_dir = os.path.abspath(data_dir)
        self.data_original_dir = os.path.join(self.data_dir, 'original')
        self.data_processed_dir = os.path.join(self.data_dir, 'processed')
        self.data_sources = load_public_sources()

    def preprocess(self, dataset_name):
        """Preprocesses the provided dataset.

        Parameters
        ----------
        dataset_name : str
            name of dataset to preprocess
        """
        if dataset_name == 'bean_disease_uganda':
            pass

        elif dataset_name == 'carrot_weeds_macedonia':
            pass

        elif dataset_name == 'leaf_counting_denmark':
            pass

        elif dataset_name == 'rangeland_weeds_australia':
            # Get the file information.
            dataset_dir = os.path.join(self.data_original_dir, dataset_name)
            images = get_file_list(os.path.join(dataset_dir, 'images'))
            df = pd.read_csv(os.path.join(dataset_dir, 'labels.csv'))

            # Construct the new structure.
            processed_dir = os.path.join(self.data_processed_dir, dataset_name)
            unique_labels = np.unique(df['Species'])
            for unique_label in unique_labels:
                os.makedirs(os.path.join(
                    processed_dir, unique_label.title()), exist_ok = True)
            for file in tqdm(images, desc = "Moving Images", file = sys.stdout):
                save_dir = df.loc[df['Filename'] == file]['Species'].values[0].title()
                shutil.copyfile(
                    os.path.join(dataset_dir, 'images', file),
                    os.path.join(processed_dir, save_dir, file)
                )

        elif dataset_name == 'fruit_detection_worldwide':
            dataset_dir = os.path.join(self.data_original_dir, dataset_name, 'datasets')

            # get folder list
            dataset_folders = get_dir_list(dataset_dir)
            label2id = get_label2id(dataset_folders)
            anno_data_all = []
            for folder in dataset_folders:
                annotations = ['test_RGB.txt', 'train_RGB.txt']
                dataset_path = os.path.join(dataset_dir, folder)
                # @TODO: Make separate json files for train and test?
                for anno_file_name in annotations:
                    # get img folder name
                    name = anno_file_name.split('.')[0].upper()

                    # Read annotations
                    try:
                        anno_data = read_txt_file(os.path.join(dataset_path, anno_file_name))
                    except:
                        try:
                            anno_data = read_txt_file(os.path.join(dataset_path, anno_file_name + '.txt'))
                        except:
                            raise

                    # Concat fruit name at head of line
                    for i, anno in enumerate(anno_data):
                        # Change to test path if the text file is test
                        if "test" in anno_file_name and "TRAIN" in anno[0]:
                            anno_data[i][0] = anno[0].replace("TRAIN", "TEST")
                        anno_data[i][0] = os.path.join(dataset_path, anno_data[i][0])

                    anno_data_all += anno_data

            # Process annotation files
            save_dir_anno = os.path.join(self.data_processed_dir, dataset_name, 'annotations')
            create_dir(save_dir_anno)
            output_json_file = os.path.join(save_dir_anno, 'instances.json')

            general_info = {
                "description": "fruits dataset",
                "url": "https://drive.google.com/drive/folders/1CmsZb1caggLRN7ANfika8WuPiywo4mBb",
                "version": "1.0",
                "year": 2018,
                "contributor": "Inkyu Sa",
                "date_created": "2018/11/12"
            }

            # Process image files
            output_img_path = os.path.join(self.data_processed_dir, dataset_name, 'images')
            create_dir(output_img_path)

            convert_bbox_to_coco(
                anno_data_all, label2id, output_json_file,output_img_path, general_info)

        elif dataset_name == "plant_weeds_denmark":
            # resize the dataset
            resize = 0.25

            # Read public_datasources.json to get class information
            category_info = self.data_sources[dataset_name]['crop_types']
            labels_str = []
            labels_ids = []
            for info in category_info:
                labels_str.append(category_info[info])
                labels_ids.append(int(info))

            label2id = dict(zip(labels_str, labels_ids))

            # Task 1: Image classification
            dataset_dir = os.path.join(self.data_original_dir, dataset_name, 'OPPD-master')
            obj_Detection_data = os.path.join(dataset_dir, "DATA/images_full")

            # get folders
            plant_folders = get_dir_list(obj_Detection_data)

            # do tasks along folders
            anno_data_all = []
            img_ids = []
            bbox_ids = []
            print("Reading annotation files..")
            for folder in tqdm(plant_folders):
                # Get image file and xml file
                full_path = os.path.join(obj_Detection_data,folder)
                all_files = get_file_list(full_path)
                anno_files = [x for x in all_files if "json" in x]
                for anno_file in anno_files:
                    anno_line = []
                    anno_path = os.path.join(full_path,anno_file)
                    # Opening JSON file
                    with open(anno_path,) as f:
                        # returns JSON object as 
                        # a dictionary
                        data = json.load(f)
                        
                        # Iterating through the json
                        
                        # get image file name
                        image_file_name =  data['filename']

                        # file name
                        anno_line.append(os.path.join(full_path,image_file_name))
                        img_ids.append(data['image_id'])
                        # bbox cnt
                        anno_line.append(len(data['plants']))
                        # bboxes
                        b_ids = []
                        for plant in data['plants']:
                            anno_line.append(plant['bndbox']['xmin'])
                            anno_line.append(plant['bndbox']['ymin'])
                            anno_line.append(plant['bndbox']['xmax'])
                            anno_line.append(plant['bndbox']['ymax'])
                            if plant['eppo']:
                                plant_name = plant['eppo'].strip() # strip() function will remove leading and trailing whitespaces.
                            else:
                                plant_name = "OTHER"

                            anno_line.append(label2id[plant_name])
                            b_ids.append(plant['bndbox_id'])

                        bbox_ids.append(b_ids)
                        anno_data_all.append(anno_line)

                # Process annotation files
                save_dir_anno = os.path.join(self.data_processed_dir, dataset_name, 'annotations')
                create_dir(save_dir_anno)
                output_json_file = os.path.join(save_dir_anno, 'instances.json')

            # Process annotation files
            save_dir_anno = os.path.join(self.data_processed_dir, dataset_name, 'annotations')
            create_dir(save_dir_anno)
            output_json_file = os.path.join(save_dir_anno, 'instances.json')

            general_info = {
                "description": "plants dataset",
                "url": "https://gitlab.au.dk/AUENG-Vision/OPPD",
                "version": "1.0",
                "year": 2020,
                "contributor": "Madsen, Simon Leminen and Mathiassen, Solvejg Kopp and Dyrmann, Mads and Laursen, Morten Stigaard and Paz, Laura-Carlota and J{\o}rgensen, Rasmus Nyholm",
                "date_created": "2020/04/20"
            }
            

            # Process image files
            output_img_path = os.path.join(self.data_processed_dir, dataset_name, 'images')
            create_dir(output_img_path)

            convert_bbox_to_coco(anno_data_all,label2id,output_json_file, output_img_path, general_info,img_ids,bbox_ids,get_label_from_folder=False, resize=resize)

            # classification
            source_dir = os.path.join(dataset_dir, "DATA/images_plants")
            output_img_path = os.path.join(self.data_processed_dir, dataset_name, 'classification')
            create_dir(output_img_path)
            plant_folders = get_dir_list(source_dir)
            for folder in plant_folders:
                # copy cropped image folders into classification
                src = os.path.join(source_dir,folder)
                copytree(src, os.path.join(output_img_path,folder))
                print("Copied {} to {}.".format(src,os.path.join(output_img_path,folder)))
                # Process annotation files
                save_dir_anno = os.path.join(self.data_processed_dir, dataset_name, 'annotations')
                create_dir(save_dir_anno)
                output_json_file = os.path.join(save_dir_anno, 'instances.json')

                general_info = {
                    "description": "plants dataset",
                    "url": "https://gitlab.au.dk/AUENG-Vision/OPPD",
                    "version": "1.0",
                    "year": 2020,
                    "contributor": "Madsen, Simon Leminen and Mathiassen, Solvejg Kopp and Dyrmann, Mads and Laursen, Morten Stigaard and Paz, Laura-Carlota and J{\o}rgensen, Rasmus Nyholm",
                    "date_created": "2020/04/20"
                }

                # Process image files
                output_img_path = os.path.join(self.data_processed_dir, dataset_name, 'images')
                create_dir(output_img_path)

                print("Convert annotations into COCO JSON and process the images")
                convert_bbox_to_coco(
                    anno_data_all, label2id, output_json_file, output_img_path,
                    general_info, img_ids, bbox_ids, get_label_from_folder=False, resize=resize)

                # classification
                source_dir = os.path.join(dataset_dir, "DATA/images_plants")
                output_img_path = os.path.join(self.data_processed_dir, dataset_name, 'classification')
                create_dir(output_img_path)
                plant_folders = get_dir_list(source_dir)
                for folder in plant_folders:
                    # copy cropped image folders into classification
                    src = os.path.join(source_dir, folder)
                    shutil.copytree(src, os.path.join(output_img_path, folder))
                print("Copied {} to {}.".format(src, os.path.join(output_img_path,folder)))

        elif dataset_name == "apple_detection_usa":
            # resize the dataset
            resize = 1.0

            # Read public_datasources.json to get class information
            category_info = self.data_sources[dataset_name]['crop_types']
            labels_str = []
            labels_ids = []
            for info in category_info:
                labels_str.append(category_info[info])
                labels_ids.append(int(info))

            label2id = dict(zip(labels_str, labels_ids))

            # Task 1: Image classification
            dataset_dir = os.path.join(self.data_original_dir, dataset_name)
            obj_Detection_data = os.path.join(dataset_dir, 'Dataset')

            # get folders
            plant_folders = nested_dir_list(obj_Detection_data)

            # do tasks along folders
            anno_data_all = []
            img_ids = []
            bbox_ids = []
            for folder in plant_folders:
                # Get image file and xml file
                full_path = os.path.join(obj_Detection_data,folder)
                all_files = get_file_list(full_path)
                anno_files = [x for x in all_files if "txt" in x]
                for anno_file in anno_files:
                    anno_line = []
                    anno_path = os.path.join(full_path,anno_file)
                    # Opening annotation file
                    anno_data = read_txt_file(anno_path,delimiter=',')
                    
                    for i, anno in enumerate(anno_data):
                        new_anno = []
                        # Add bbox count
                        # Update image file path to abs path
                        new_anno.append(os.path.join(dataset_dir, anno_data[i][0]))
                        bbox_cnt = int((len(anno_data[i]) - 1) / 4)
                        new_anno.append(str(bbox_cnt))
                        for idx in range(bbox_cnt):
                            xmin = int(anno[1 + 4 * idx])
                            ymin = int(anno[1 + 4 * idx+1])
                            w = int(anno[1 + 4 * idx+2])
                            h = int(anno[1 + 4 * idx+3])

                            new_anno.append(str(xmin))  # xmin
                            new_anno.append(str(ymin))  # ymin
                            new_anno.append(str(xmin + w))  # xmax
                            new_anno.append(str(ymin + h))  # ymax
                            new_anno.append(str(1)) # label
                        anno_data[i] = new_anno                      
                    anno_data_all += anno_data

            # Process annotation files
            save_dir_anno = os.path.join(self.data_processed_dir, dataset_name, 'annotations')
            create_dir(save_dir_anno)
            output_json_file = os.path.join(save_dir_anno, 'instances.json')

            general_info = {
                "description": "apple dataset",
                "url": "https://research.libraries.wsu.edu:8443/xmlui/handle/2376/17721",
                "version": "1.0",
                "year": 2019,
                "contributor": "Bhusal, Santosh, Karkee, Manoj, Zhang, Qin",
                "date_created": "2019/04/20"
            }

            # Process image files
            output_img_path = os.path.join(self.data_processed_dir, dataset_name, 'images')
            create_dir(output_img_path)
            convert_bbox_to_coco(anno_data_all,label2id,output_json_file, output_img_path, general_info,None,None,get_label_from_folder=False, resize=resize, add_foldername=True)

        elif dataset_name == "fruit_detection_australia":
            # resize the dataset
            resize = 1.0

            # Read public_datasources.json to get class information
            datasource_file = os.path.join(os.path.dirname(__file__), "../_assets/public_datasources.json")
            with open(datasource_file) as f:
                data = json.load(f)
                category_info = data[dataset_name]['crop_types']
                labels_str = []
                labels_ids = []
                for info in category_info:
                    labels_str.append(category_info[info])
                    labels_ids.append(int(info))

                label2id = dict(zip(labels_str, labels_ids))

            # Task 1: Image classification
            dataset_dir = os.path.join(self.data_original_dir, dataset_name)
            obj_Detection_data = os.path.join(dataset_dir, 'acfr-fruit-dataset')

            # get folders
            # plant_folders = get_dirlist(obj_Detection_data)
            plant_folders = nested_dir_list(obj_Detection_data)

            # do tasks along folders
            anno_data_all = []
            img_ids = []
            bbox_ids = []
            for folder in plant_folders:
                # Get image filse and annotation files
                full_path = os.path.join(obj_Detection_data,folder)
                all_files = get_file_list(full_path)
                anno_files = [x for x in all_files if "csv" in x]
                if len(anno_files) > 0:
                    for anno_file in anno_files:
                        anno_line = []
                        anno_path = os.path.join(full_path,anno_file)
                        # Opening annotation file
                        anno_lines, headline = read_txt_file(anno_path,delimiter=',',header=True)
                        
                        new_anno = []
                        # Add bbox count
                        # Update image file path to abs path
                        img_name = anno_file.split('/')[-1].replace('.csv','.png')
                        img_parent = full_path.replace("annotations","images")
                        new_anno.append(os.path.join(img_parent, img_name))
                        bbox_cnt = len(anno_lines)
                        new_anno.append(str(bbox_cnt))
                        if "mango" in full_path.split('/')[-2]:
                            label = "mango"
                        elif "apple" in full_path.split('/')[-2]:
                            label = "apple"
                        elif "almond" in full_path.split('/')[-2]:
                            label = "almond"
                        else:
                            label = full_path.split('/')[-2][:-1]

                        for i, anno in enumerate(anno_lines):
                            
                            if "radius" in headline:
                                cx = float(anno[1])
                                cy = float(anno[2])
                                radi = float(anno[3])
                                xmin = cx - radi  # xmin
                                ymin = cy - radi  # ymin
                                w = h = 2 * radi
                            else:
                                xmin = float(anno[1])
                                ymin = float(anno[2])
                                w = float(anno[3])
                                h = float(anno[4])

                            new_anno.append(str(xmin))  # xmin
                            new_anno.append(str(ymin))  # ymin
                            new_anno.append(str(xmin + w))  # xmax
                            new_anno.append(str(ymin + h))  # ymax
                            new_anno.append(label2id[label]) # label                   
                        anno_data_all.append(new_anno)

            # Process annotation files
            save_dir_anno = os.path.join(self.data_processed_dir, dataset_name, 'annotations')
            create_dir(save_dir_anno)
            output_json_file = os.path.join(save_dir_anno, 'instances.json')

            general_info = {
                "description": "Deep Fruit Detection in Orchards",
                "url": "http://data.acfr.usyd.edu.au/ag/treecrops/2016-multifruit/",
                "version": "1.0",
                "year": 2016,
                "contributor": "Bargoti, Suchet and Underwood, James",
                "date_created": "2016/10/12"
            }
            

            # Process image files
            output_img_path = os.path.join(self.data_processed_dir, dataset_name, 'images')
            create_dir(output_img_path)

            json_dict = convert_bbox_to_coco(anno_data_all,label2id,output_json_file, output_img_path, general_info,None,None,get_label_from_folder=False, resize=resize, add_foldername=False, extract_num_from_imgid=True)

            # Add segmentation for apple
            apple_seg_dir = os.path.join(obj_Detection_data,"apples/segmentations")
            seg_imgs = get_file_list(apple_seg_dir)

            # Define which colors match which categories in the images
            apple_id = label2id['apple']
            category_ids = {
                label2id['apple']: {
                    '(128, 0, 0)': apple_id,
                },
            }
            is_crowd = 0
            # Create the annotations
            # These ids will be automatically increased as we go
            print("Processing image segmentaitons..")
            for seg_img in tqdm(seg_imgs):
                annotation_id = 100 # Starts with 100
                mask_image = Image.open(os.path.join(apple_seg_dir,seg_img))
                sub_masks = create_sub_masks(mask_image)
                image_id = int(''.join(filter(str.isdigit, seg_img)))
                for color, sub_mask in sub_masks.items():
                    category_id = label2id['apple']                   
                    annotations = create_sub_mask_annotation_per_bbox(sub_mask, image_id, category_id, annotation_id, is_crowd)
                    json_dict['annotations'] += annotations
                    annotation_id += 1

            # Rewrite json file
            with open(output_json_file, 'w') as f:
                output_json = json.dumps(json_dict)
                f.write(output_json)

        elif dataset_name == "apple_detection_spain":
            # resize the dataset
            resize = 1.0

            # Read public_datasources.json to get class information
            datasource_file = os.path.join(os.path.dirname(__file__), "../_assets/public_datasources.json")
            with open(datasource_file) as f:
                data = json.load(f)
                category_info = data[dataset_name]['crop_types']
                labels_str = []
                labels_ids = []
                for info in category_info:
                    labels_str.append(category_info[info])
                    labels_ids.append(int(info))

                name_converter = dict(zip(["Poma"], ["apple"])) # src -> dst
                label2id = dict(zip(labels_str, labels_ids))

            dataset_dir = os.path.join(self.data_original_dir, dataset_name)
            ann_dir = os.path.join(dataset_dir, "preprocessed data/square_annotations1")

            # Get image file and xml file
            all_files = get_file_list(ann_dir)
            anno_files = [os.path.join(ann_dir,x) for x in all_files if "xml" in x]
            img_files = [x.replace(".xml","hr.jpg").replace("square_annotations1","images") for x in anno_files]

            # Process annotation files
            save_dir_anno = os.path.join(self.data_processed_dir, dataset_name, 'annotations')
            create_dir(save_dir_anno)
            output_json_file = os.path.join(save_dir_anno, 'instances.json')

            # Process image files
            output_img_path = os.path.join(self.data_processed_dir, dataset_name, 'images')
            create_dir(output_img_path)

            general_info = {
                "description": "KFuji RGB-DS database",
                "url": "http://www.grap.udl.cat/en/publications/KFuji_RGBDS_database.html",
                "version": "1.0",
                "year": 2018,
                "contributor": "Gené-Mola J, Vilaplana V, Rosell-Polo JR, Morros JR, Ruiz-Hidalgo J, Gregorio E",
                "date_created": "2018/10/19"
            }

            convert_xmls_to_cocojson(
                general_info,
                annotation_paths=anno_files,
                img_paths=img_files,
                label2id=label2id,
                name_converter = name_converter,
                output_jsonpath=output_json_file,
                output_imgpath = output_img_path,
                extract_num_from_imgid=True
            )
    
        elif dataset_name == "mango_detection_australia":
            # resize the dataset
            resize = 1.0

            # Read public_datasources.json to get class information
            datasource_file = os.path.join(
                os.path.dirname(__file__), "../_assets/public_datasources.json")
            with open(datasource_file) as f:
                data = json.load(f)
                category_info = data[dataset_name]['crop_types']
                labels_str = []
                labels_ids = []
                for info in category_info:
                    labels_str.append(category_info[info])
                    labels_ids.append(int(info))

                name_converter = dict(zip(["M"], ["mango"])) # src -> dst
                label2id = dict(zip(labels_str, labels_ids))

            dataset_dir = os.path.join(self.data_original_dir, dataset_name)
            ann_dir = os.path.join(dataset_dir, "VOCDevkit/VOC2007/Annotations")

            # Get image file and xml file
            all_files = get_file_list(ann_dir)
            anno_files = [os.path.join(ann_dir, x) for x in all_files if "xml" in x]
            img_files = [x.replace(".xml", ".jpg").replace(
                "Annotations", "JPEGImages") for x in anno_files]

            # Process annotation files
            save_dir_anno = os.path.join(
                self.data_processed_dir, dataset_name, 'annotations')
            create_dir(save_dir_anno)
            output_json_file = os.path.join(
                save_dir_anno, 'instances.json')

            # Process image files
            output_img_path = os.path.join(
                self.data_processed_dir, dataset_name, 'images')
            create_dir(output_img_path)

            general_info = {
                "description": "MangoYOLO data set",
                "url": "https://researchdata.edu.au/mangoyolo-set/1697505",
                "version": "1.0",
                "year": 2019,
                "contributor": "Anand Koirala, Kerry Walsh, Z Wang, C McCarthy",
                "date_created": "2019/02/25"
            }

            convert_xmls_to_cocojson(
                general_info,
                annotation_paths=anno_files,
                img_paths=img_files,
                label2id=label2id,
                name_converter = name_converter,
                output_jsonpath=output_json_file,
                output_imgpath = output_img_path,
                extract_num_from_imgid=True
            )

        elif dataset_name == "apple_detection_spain":
            # resize the dataset
            resize = 1.0

            # Read public_datasources.json to get class information
            datasource_file = os.path.join(os.path.dirname(__file__),
                                           "../_assets/public_datasources.json")
            with open(datasource_file) as f:
                data = json.load(f)
                category_info = data[dataset_name]['crop_types']
                labels_str = []
                labels_ids = []
                for info in category_info:
                    labels_str.append(category_info[info])
                    labels_ids.append(int(info))

                label2id = dict(zip(labels_str, labels_ids))

            # Get image file and xml file
            dataset_dir = os.path.join(self.data_original_dir, dataset_name)
            all_files = get_file_list(dataset_dir)
            anno_files = [os.path.join(dataset_dir,x) for x in all_files if "csv" in x]

            # do tasks along folders
            anno_data_all = []
            img_ids = []
            bbox_ids = []

            if len(anno_files) > 0:
                for anno_file in anno_files:
                    anno_line = []
                    anno_path = os.path.join(dataset_dir, anno_file)
                    # Opening annotation file
                   
                    new_anno = []
                    # Add bbox count
                    # Update image file path to abs path
                    img_name = anno_file.replace(".csv",".jpg").replace("mask__","_")
                    new_anno.append(os.path.join(dataset_dir, img_name))
                    bbox_cnt = 0
                    new_anno.append(str(bbox_cnt))

                    anno_data_all.append(new_anno)

            # Process annotation files
            save_dir_anno = os.path.join(self.data_processed_dir, dataset_name, 'annotations')
            create_dir(save_dir_anno)
            output_json_file = os.path.join(save_dir_anno, 'instances.json')

            general_info = {
                "description": "Fuji-SfM dataset",
                "url": "http://www.grap.udl.cat/en/publications/Fuji-SfM_dataset.html",
                "version": "1.0",
                "year": 2020,
                "contributor": ("Gené-Mola J, Sanz-Cortiella R, Rosell-Polo JR, Morros J-R, "
                               "Ruiz-Hidalgo J, Vilaplana V, , Gregorio E."),
                "date_created": "2020/04/24"
            }
            

            # Process image files
            output_img_path = os.path.join(self.data_processed_dir, dataset_name, 'images')
            create_dir(output_img_path)

            json_dict = convert_bbox_to_coco(
                anno_data_all, label2id, output_json_file, output_img_path, general_info,
                None, None, get_label_from_folder=False, resize=resize,
                add_foldername=False, extract_num_from_imgid=True)

            # Add segmentation for apple
            is_crowd = 0
            # Create the annotations
            # These ids will be automatically increased as we go
            print("Processing image segmentations..")
            for anno_path in tqdm(anno_files):
                annotation_id = 100 # Starts with 100
                # Read CSV
                anno_lines, headline = read_txt_file(anno_path,delimiter=',',header=True)
                # print(headline, anno_lines)
                image_id = int(''.join(filter(str.isdigit, anno_path.split('/')[-1])))
                for anno_line in anno_lines:
                    category_id = label2id['apple']                   
                    annotations = mask_annotation_per_bbox(anno_line, image_id, category_id, annotation_id, is_crowd)
                    json_dict['annotations'] += annotations
                    annotation_id += 1

            # Rewrite json file
            with open(output_json_file, 'w') as f:
                output_json = json.dumps(json_dict)
                f.write(output_json)

            convert_bbox_to_coco(
                anno_data_all, label2id, output_json_file, output_img_path, general_info,
                None, None, get_label_from_folder=False, resize=resize, make_unique_name=True)
            save_dir_imgs = os.path.join(self.data_processed_dir, dataset_name, 'images')
            create_dir(save_dir_imgs)
            for anno in tqdm(anno_data_all):
                img_name = anno[0].split('/')[-1]
                dest_path = os.path.join(save_dir_imgs, img_name)
                try:
                    shutil.copyfile(anno[0], dest_path)
                except:
                    # Cannot copy the image file
                    pass

        elif dataset_name == 'cotton_seedling_counting':
            # Get all of the relevant data
            dataset_dir = os.path.join(self.data_original_dir, dataset_name)
            image_dir = os.path.join(dataset_dir, 'Images')
            images = sorted([os.path.join(image_dir, i) for i in os.listdir(image_dir)])
            with open(os.path.join(dataset_dir, 'Images.json'), 'r') as f:
                annotations = json.load(f)

            # Get all of the unique labels
            labels = []
            for label_set in annotations['frames'].values():
                for individual_set in label_set:
                    labels.extend(individual_set['tags'])
            labels = np.unique(labels).tolist()
            label2id = get_label2id(labels) # noqa

            # Extract all of the bounding boxes and images
            image_data = []
            annotation_data = []
            valid_paths = [] # some paths are not in the annotations, track the ones which are
            for indx, (img_path, annotation) in enumerate(
                    zip(tqdm(images, file = sys.stdout, desc = "Generating Data"),
                        annotations['frames'].values())):
                image_data.append(get_image_info(img_path, indx))
                valid_paths.append(img_path)
                for a_set in annotation:
                    formatted_set = [
                        a_set['x1'], a_set['y1'], a_set['x2'], a_set['y2'],
                        label2id[a_set['tags'][0]]]
                    base_annotation_data = get_coco_annotation_from_obj(formatted_set, a_set['name'])
                    base_annotation_data['image_id'] = indx + 1
                    annotation_data.append(base_annotation_data)

            # Set up the annotation dictionary
            all_annotation_data = {
                "images": [], "type": "instances",
                "annotations": [], "categories": [],
                "info": {
                    "description": "cotton seedling counting dataset",
                    "url": "https://figshare.com/s/616956f8633c17ceae9b",
                    "version": "1.0",
                    "year": 2019,
                    "contributor": "Yu Jiang",
                    "date_created": "2019/11/23"
                }
            }

            # Populate the annotation dictionary
            for label, label_id in label2id.items():
                category_info = {'supercategory': 'none', 'id': label_id, 'name': label}
                all_annotation_data['categories'].append(category_info)
            all_annotation_data['images'] = image_data
            all_annotation_data['annotations'] = annotation_data

            # Recreate the dataset and zip it
            processed_dir = os.path.join(self.data_processed_dir, dataset_name)
            processed_img_dir = os.path.join(processed_dir, 'images')
            if os.path.exists(processed_dir):
                shutil.rmtree(processed_dir)
            os.makedirs(processed_dir, exist_ok = True)
            os.makedirs(processed_img_dir, exist_ok = True)
            for path in images:
                if path not in valid_paths:
                    continue
                shutil.copyfile(path, os.path.join(processed_img_dir, os.path.basename(path)))
            with open(os.path.join(processed_dir, 'labels.json'), 'w') as f:
                json.dump(all_annotation_data, f, indent = 4)

            # Zip the dataset
            shutil.make_archive(
                processed_dir, "zip", os.path.dirname(processed_dir))

        elif dataset_name == 'apple_flower_segmentation':
            # Get all of the relevant data.
            dataset_dir = os.path.join(self.data_original_dir, dataset_name)
            apple_a_dir = os.path.join(dataset_dir, 'FlowerImages')
            apple_a_images = os.listdir(apple_a_dir)
            apple_a_label_dir = os.path.join(dataset_dir, 'AppleA_Labels')
            apple_a_labels = os.listdir(apple_a_label_dir)
            apple_b_dir = os.path.join(dataset_dir, 'AppleB')
            apple_b_images = os.listdir(apple_b_dir)
            apple_b_label_dir = os.path.join(dataset_dir, 'AppleB_Labels')
            apple_b_labels = os.listdir(apple_b_label_dir)

            # Map image filenames with their corresponding labels.
            fname_map_a, fname_map_b = {}, {}
            for fname in apple_a_images:
                fname_id = str(int(float(
                    os.path.splitext(fname)[0].split('_')[-1]))) + ".png"
                if fname_id in apple_a_labels:
                    fname_map_a[os.path.join(apple_a_dir, fname)] \
                        = os.path.join(apple_a_label_dir, fname_id)
            for fname in apple_b_images:
                fname_id = str(int(float(
                    os.path.splitext(fname)[0].split('_')[-1]))) + ".png"
                if fname_id in apple_b_labels:
                    fname_map_b[os.path.join(apple_b_dir, fname)] \
                        = os.path.join(apple_b_label_dir, fname_id)

            # Process and move the images.
            processed_dir = os.path.join(
                self.data_processed_dir, dataset_name)
            os.makedirs(processed_dir, exist_ok = True)
            processed_image_dir = os.path.join(processed_dir, 'images')
            os.makedirs(processed_image_dir, exist_ok = True)
            processed_annotation_dir = os.path.join(processed_dir, 'annotations')
            os.makedirs(processed_annotation_dir, exist_ok = True)
            for image_path, label_path in tqdm(
                    fname_map_a.items(), desc = "Processing Part A", file = sys.stdout):
                image = cv2.resize(cv2.imread(image_path), (2074, 1382))
                label = cv2.resize(cv2.imread(label_path), (2074, 1382)) // 255
                label_path = os.path.basename(label_path)
                out_image_path = os.path.join(processed_image_dir, label_path)
                out_label_path = os.path.join(processed_annotation_dir, label_path)
                cv2.imwrite(out_image_path.replace('.png', '.jpg'), image)
                cv2.imwrite(out_label_path, label)
            for image_path, label_path in tqdm(
                    fname_map_b.items(), desc = "Processing Part B", file = sys.stdout):
                image = cv2.resize(cv2.imread(image_path), (2074, 1382))
                label = cv2.resize(cv2.imread(label_path), (2074, 1382)) // 255
                label_path = os.path.basename(label_path)
                out_image_path = os.path.join(processed_image_dir, label_path)
                out_label_path = os.path.join(processed_annotation_dir, label_path)
                cv2.imwrite(out_image_path.replace('.png', '.jpg'), image)
                cv2.imwrite(out_label_path, label)

        elif dataset_name == "sugarbeet_weed_segmentation":
            # Get all of the relevant data
            dataset_dir = os.path.join(self.data_original_dir, dataset_name)
            train_dir = os.path.join(dataset_dir, 'train')
            train_images = sorted(get_file_list(train_dir))
            annotation_dir = os.path.join(dataset_dir, 'trainannot') # noqa
            annotation_images = sorted(get_file_list(annotation_dir))

            # Move the images to the new directory
            move_segmentation_dataset(
                self.data_processed_dir, dataset_name, train_images,
                annotation_images, train_dir, annotation_dir)

        elif dataset_name == 'carrot_weeds_germany':
            # Get all of the relevant data.
            dataset_dir = os.path.join(self.data_original_dir, dataset_name)
            train_dir = os.path.join(dataset_dir, 'images')
            train_images = sorted(get_file_list(train_dir))
            annotation_dir = os.path.join(dataset_dir, 'annotations')
            annotation_images = sorted(get_file_list(annotation_dir, ext = 'png'))

            # Move the images to the new directory.
            def _annotation_preprocess_fn(annotation_path, out_path):
                an_img = cv2.cvtColor(cv2.imread(annotation_path), cv2.COLOR_BGR2RGB)
                crop, weed = (0, 255, 0), (255, 0, 0)
                out_annotation = np.zeros(shape = an_img.shape[:-1])
                crop_indices = np.stack(np.where(np.all(an_img == crop, axis = -1))).T
                weed_indices = np.stack(np.where(np.all(an_img == weed, axis = -1))).T
                for indxs in crop_indices:
                    out_annotation[indxs[0]][indxs[1]] = 1
                for indxs in weed_indices:
                    out_annotation[indxs[0]][indxs[1]] = 2
                return cv2.imwrite(out_path, out_annotation.astype(np.int8))
            move_segmentation_dataset(
                self.data_processed_dir, dataset_name, train_images,
                annotation_images, train_dir, annotation_dir,
                annotation_preprocess_fn = _annotation_preprocess_fn
            )

        elif dataset_name == 'apple_segmentation_minnesota':
            # Get all of the relevant data.
            dataset_dir = os.path.join(self.data_original_dir, dataset_name)
            train_dir = os.path.join(dataset_dir, 'train', 'images')
            train_images = sorted(get_file_list(train_dir))
            masks_dir = os.path.join(dataset_dir, 'train', 'masks')
            mask_images = sorted(get_file_list(masks_dir))

            # Move the images to the new directory.
            def _annotation_preprocess_fn(annotation_path, out_path):
                mask = cv2.imread(annotation_path, cv2.IMREAD_GRAYSCALE)
                ids = np.unique(mask)[1:]
                masks = mask == ids[:, np.newaxis, np.newaxis]
                masks = masks.astype(np.int32)
                if len(masks) == 1:
                    mask = mask
                elif len(masks) >= 2:
                    mask = np.logical_or(masks[0], masks[1])
                    if len(masks) > 2:
                        for mask_ in masks[2:]:
                            mask = np.logical_or(mask, mask_)
                mask = mask.astype(np.int32)
                return cv2.imwrite(out_path, mask)
            move_segmentation_dataset(
                self.data_processed_dir, dataset_name, train_images,
                mask_images, train_dir, masks_dir,
                annotation_preprocess_fn = _annotation_preprocess_fn
            )

        elif dataset_name == 'rice_seedling_segmentation':
            # Get all of the relevant data.
            data_dir = os.path.join(self.data_original_dir, dataset_name)
            images = sorted(glob.glob(os.path.join(data_dir, 'image_*.jpg')))
            labels = sorted(glob.glob(os.path.join(data_dir, 'Label_*.png')))
            images = [os.path.basename(p) for p in images]
            labels = [os.path.basename(p) for p in labels]

            # Move the images to the new directory
            move_segmentation_dataset(
                self.data_processed_dir, dataset_name,
                images, labels, data_dir, data_dir
            )




