# -*- coding: utf-8 -*-
"""
Created on Fri Feb  1 10:53:42 2019

@author: Johanna Rahm

Research group Heilemann
Institute for Physical and Theoretical Chemistry, Goethe University Frankfurt a.M.

Create a cell object which creats trajectory objects. Cell contains informations about cell size and name.
"""

import numpy as np
from . import trajectory
#from multiprocessing import Pool
from tqdm import tqdm_notebook as tqdm
#from .analysis import trajectory
#from pySPT.analysis import trajectory

class Cell():
    def __init__(self):
        self.trc_file = []  # col0 = trajectory, col1 = frames, col2 = x, col3 = y, col4 = intensity ~ trc file
        self.trajectories = []  # contains trajectory objects
        self.analysed_trajectories = []  # contains analysed trajectory objects
        self.pixel_size = 158  # [nm] multiply with palmtracer in nm -> *10^-3 micrometer!
        self.pixel_amount = 65536 # amount of pixels of detector (256x256) 
        self.size = 0.0  # size from roi [ym^2]
        self.name = ""  # name of cell file (raw base name)
        self.tau_threshold = 0.0  # hand down to trajectory
        self.dt = 0.0   # hand down to trajectory
        self.dof = 0.0  # hand down to trajectory
        self.D_min = 0.0  # hand down to trajectory
        self.points_fit_D = 4  # hand down to trajectory
        self.tau_threshold_min_length = 0.0 
        
    @staticmethod
    def analyse_trajectory(self, trajectory):
        """
        Multiprocessing job: analyse 1 trajectory object.
        """
        trajectory.analyse_particle()
        return trajectory      
     
    def run_processes(self):
        """
        Target: analyse trajectory,
        arg: one trajectory out of the self.trajectories list
        """
        with Pool(None) as p:
            self.analysed_trajectories = p.map(self.analyse_trajectory, self.trajectories)
            print(self.analysed_trajectories)
            return self.analysed_trajectories
                
    def create_trajectories(self):
        """
        Create list with trajectory objects from a trc file.
        """
        self.trc_file[:,2] = np.multiply(self.trc_file[:,2], int(self.pixel_size)*10**(-3))
        self.trc_file[:,3] = np.multiply(self.trc_file[:,3], int(self.pixel_size)*10**(-3))
        for trajectory_number in range(int(self.trc_file[:,0].min()), int(self.trc_file[:,0].max())+1):    
            idx = self.trc_file[:,0] == trajectory_number
            localizations = self.trc_file[idx,:]
            if not (localizations.size==0):
                self.trajectories.append(trajectory.Trajectory(localizations, self.tau_threshold, self.dt, self.dof, self.D_min, self.points_fit_D))
                
    def cell_size(self):
        """
        Convert cell size in pixel^2 to micrometer^2.
        If no Roi was loaded, cell size = amount of pixel^2 * pixelsize^2.
        """
        if self.size == 0:
            self.size = self.pixel_amount * (self.pixel_size/1000)**2  # in micrometer
        else:
            self.size = self.size * (self.pixel_size/1000)**2

    def analyse_trajectories(self):
        """
        Analyse trajectories without multiprocessing
        """
# =============================================================================
#         list(map(lambda x: x.analyse_particle(), self.trajectories))
#         self.analysed_trajectories = self.trajectories
# ============================================================================= 
        for trajectory in tqdm(self.trajectories):
            trajectory.analyse_particle()
        self.analysed_trajectories = self.trajectories
        
        
    def plot_trajectory(self, trajectory_number):
        """
        Plot a defined trajectory by its number.
        """
        self.analysed_trajectories[trajectory_number-1].plot_particle()
        

def main():
    pass


if __name__ == "__main__":
    main()

