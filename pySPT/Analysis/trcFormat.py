# -*- coding: utf-8 -*-
"""
Created on Fri Jan 25 14:14:32 2019

@author: Johanna Rahm

Research group Heilemann
Institute for Physical and Theoretical Chemistry, Goethe University Frankfurt a.M.

Convert a rapidSTORM localization .txt or thunderSTORM localization .csv file into .trc format (like PALMTracer).
trc starts counting from 1, localizations in px, intensity in adc.
"""

import numpy as np
import datetime
import pandas as pd

class TrcFormat():
    def __init__(self):
        self.software = ""  # either thunderSTORM or rapidSTORM
        self.column_order = {}
        self.file_name = ""
        self.loaded_file = []
        self.trc_file = []
        self.trc_file_sorted = []  # the localized file is sorted by (1) frame (2) track_id
        self.trc_filtered = []  # all trajectories < min track length are neglected
        self.pixel_size = 158  # PALMTracer stores localizations as pixel -> converting factor is needed because rapidSTORM localizes in nm
        self.min_track_length = 2  # min track length
               
    def load_localization_file(self):
        """
        Array with columns:
        col0 = sed_id (seg_id = track_id if segmentation is False)
        col1 = frame
        col2 = x
        col3 = y
        col4 = intensity
        """
# =============================================================================
#         # No smart column loading available, because of current swift header handling (190204).
#         try:
#             self.loaded_file = np.loadtxt(self.file_name, usecols = (10, 4, 0, 2, 5))  # seg_id, image_number, x-position, y-position, intensity
#             self.create_trc_file()
#             self.sort_trc_file()
#             print("Convertion successful.")
#         except IndexError:
#             print("Wrong input file. Check if the tracked swift file has following columns: Position-0-0, Position-0-0-uncertainty, Position-1-0, Position-1-0-uncertainty, ImageNumber-0-0, Amplitude-0-0, PSFWidth-0-0, PSFWidth-1-0, FitResidues-0-0, LocalBackground-0-0, seg_id, track_id.")
#         
# =============================================================================
        if self.software == "thunderSTORM":
            x_index = list(self.column_order.keys())[list(self.column_order.values()).index('"x [nm]"')]
            y_index = list(self.column_order.keys())[list(self.column_order.values()).index('"y [nm]"')]
            seg_id_index = list(self.column_order.keys())[list(self.column_order.values()).index('"seg_id"')]
            frame_index = list(self.column_order.keys())[list(self.column_order.values()).index('"frame"')]
            intensity_index = list(self.column_order.keys())[list(self.column_order.values()).index('"intensity [photon]"')]
            file = pd.read_csv(self.file_name)
            file_x = file.iloc[:,x_index] 
            file_y = file.iloc[:,y_index] 
            file_seg_id = file.iloc[:,seg_id_index] 
            file_frame = file.iloc[:,frame_index] 
            file_intensity = file.iloc[:,intensity_index] 
            self.loaded_file = np.zeros([np.shape(file)[0],5])
            self.loaded_file[:,0] = file_seg_id
            self.loaded_file[:,1] = file_frame
            self.loaded_file[:,2] = file_x
            self.loaded_file[:,3] = file_y
            self.loaded_file[:,4] = file_intensity
        elif self.software == "rapidSTORM":
            x_index = list(self.column_order.keys())[list(self.column_order.values()).index('"Position-0-0"')]
            y_index = list(self.column_order.keys())[list(self.column_order.values()).index('"Position-1-0"')]
            seg_id_index = list(self.column_order.keys())[list(self.column_order.values()).index('"seg_id"')]
            frame_index = list(self.column_order.keys())[list(self.column_order.values()).index('"ImageNumber-0-0"')]
            intensity_index = list(self.column_order.keys())[list(self.column_order.values()).index('"Amplitude-0-0"')]
            self.loaded_file = np.loadtxt(self.file_name, usecols = (seg_id_index, frame_index, x_index, y_index, intensity_index)) # col0 = x uncertainty, col1 = y uncertainty
        self.create_trc_file()
        self.sort_trc_file()
        self.filter_trc_file()
        
        
    def create_trc_file(self):
        """
        Create file in trc PALMTracer style:
        col0 = sed_id (seg_id = track_id if segmentation is False) + 1 -> first index is 1
        col1 = frame + 1 -> first index is 1
        col2 = x / pixel_size [nm] -> position in pixel
        col3 = y / pixel_size [nm] -> position in pixel
        col4 = 0, random col with same integer
        col5 = intensity
        """
        self.trc_file = np.zeros([np.size(self.loaded_file[:,0]),7])
        seg_id = np.add(self.loaded_file[:,0],1)  # trc count starts at 1
        if self.software == "rapidSTORM":  # rapidSTORM starts frame counting at 0, thunderSTORM & PALMTracer at 1
            frame = np.add(self.loaded_file[:,1],1)
        elif self.software == "thunderSTORM":
            frame = self.loaded_file[:,1]
        position_x = np.divide(self.loaded_file[:,2], int(self.pixel_size))
        position_y = np.divide(self.loaded_file[:,3], int(self.pixel_size))
        intensity = self.loaded_file[:,4]
        self.trc_file[:,0] = seg_id
        self.trc_file[:,1] = frame
        self.trc_file[:,2] = position_x
        self.trc_file[:,3] = position_y
        self.trc_file[:,5] = intensity

        
    def sort_trc_file(self):
        """
        Sort trc_file by (1) seg id, (2) frame. 
        """
        dtype = [("seg_id", int), ("frame", int), ("position_x", float), ("position_y", float), ("0", int), ("intensity", float), ("track_length", int)]
        values = list(map(tuple,self.trc_file))  # convert np.ndarrays to tuples
        structured_array = np.array(values, dtype=dtype)  # create structured array
        self.trc_file_sorted = np.sort(structured_array, order=["seg_id", "frame"])  # sort by dtype name
    
    def filter_trc_file(self):
        """
        Throw all trajectories < self.min_track_length out & index continuously starting from 1.
        """       
        # minimum track length has to be at least 2, because otherwise no HMM is possible.
        if int(self.min_track_length) < 2:
            self.min_track_length = 2
        # determine the max trajectory index
        max_trajectory_index = 0
        for i in self.trc_file_sorted:
            if int(i[0]) > max_trajectory_index:
                max_trajectory_index = int(i[0])
        step_count = 0   
        # determine the trajectory lengths and insert the value in the 6th column for all steps of one trajectory
        for i in range(len(self.trc_file_sorted)-1):
            if self.trc_file_sorted[i][0] == self.trc_file_sorted[i+1][0]:
                step_count += 1
            else:
                for frame in range(step_count+1):  # the last column is the duration of the track
                    self.trc_file_sorted[i-frame][6] = step_count+1
                step_count = 0
        # filter for trajectories with lengths > min length
        self.trc_filtered = list(filter(lambda row: row[6] >= int(self.min_track_length), self.trc_file_sorted))
        out_file_name = "C:\\Users\\pcoffice37\\Documents\\thunderSTORM\\swift_analysis\\pySPT_cell01_fp1\\analysis\\trc_format_filtered.trc"
        header = "seg_id\t frame\t x [pixel]\t y [pixel]\t placeholder\t intensity [photon]\t"
        np.savetxt(out_file_name, 
                   X=self.trc_filtered,
                   fmt = ("%i","%i", "%.3f", "%.3f", "%i", "%.3f", "%.3f"),
                   header = header)
        # get rid of last column with track_length (easier with rows being lists instead of np.voids)
        self.trc_filtered = list(map(lambda row: list(row)[:6], self.trc_filtered)) 
        # continuously index the trajectories starting from 1
        continuous_index = 1
        for i in range(len(self.trc_filtered)-1):
            #print("i", i, self.trc_filtered[i][0])
            if self.trc_filtered[i][0] == self.trc_filtered[i+1][0]:
                self.trc_filtered[i][0] = continuous_index
            else:
                self.trc_filtered[i][0] = continuous_index
                continuous_index += 1 
        try:
            self.trc_filtered[len(self.trc_filtered)-1][0] = self.trc_filtered[len(self.trc_filtered)-2][0] # the last entry can't compare the following entry because it is the last. It will get the index from the entry before
        # because the min length has to be >= 2. Therefore the index has to be the same as the entry before.#
            print("Conversion successful.")
        except IndexError:
            print("All trajecoties are shorter as the minimum trajectory length inserted, please select a smaller minimum threshold.")
        
    def save_trc_file(self, directory, base_name):
        now = datetime.datetime.now()
        year = str(now.year)
        year = year[2:]
        month = str(now.month)
        day = str(now.day)
        if len(month) == 1:
            month = str(0) + month
        if len(day) == 1:
            day = str(0) + day
        #out_file_name = "F:\\Marburg\\single_colour_tracking\\resting\\160404_CS5_Cell1\\pySPT_cell_1_MMStack_Pos0\\preAnalysis\\sorted.txt"
        out_file_name = directory + "\\" + year + month + day + "_" + base_name + "_trc_format.trc"
        #header = "seg_id\t frame\t x [pixel]\t y [pixel]\t placeholder\t intensity [photon]\t"
        np.savetxt(out_file_name, 
                   X=self.trc_filtered,
                   fmt = ("%i","%i", "%.3f", "%.3f", "%i", "%.3f"))
        
        out_file_name = directory + "\\" + year + month + day + "_" + base_name + "_trc_format_min_length.txt"        
        file = open(out_file_name, 'w')
        file.write("# min track length\n")
        file.write("%i" %(int(self.min_track_length)))
        file.close()

        
        print(self.file_name + " saved as .trc file.")
        
        
        
        
        
def main():
    trc_format= TrcFormat()
    trc_format.file_name = "F:\\Marburg\\single_colour_tracking\\resting\\160404_CS5_Cell1\\cell_1_MMStack_Pos0.ome.tif.tracked.txt"
    trc_format.load_localization_file()
    trc_format.create_trc_file()
    trc_format.sort_trc_file()
    trc_format.save_trc_file()


if __name__ == "__main__":
    main()
    