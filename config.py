import pygame

# Screen & Layout
WIDTH, HEIGHT = 1600, 900
PANEL_W = 450
SIM_W = WIDTH - PANEL_W
CENTER_X, CENTER_Y = SIM_W // 2, HEIGHT // 2
FPS = 60

# Physics
REPULSION_STRENGTH = 2500.0 
DAMPING = 0.85

# Spring Constants
K_SOCIAL = 0.01  
K_HOME = 0.08  
K_WORK = 0.02  
L_SOCIAL = 30.0  
L_STRUCT = 15.0  

# Visuals
RING_RAD_MID = 160   
RING_RAD_OUTER = 400 
RING_RAD_FAR = 460   

# Time
UPDATES_PER_TICK = 600 
TICKS_PER_DAY = 3
UPDATES_PER_DAY = UPDATES_PER_TICK * TICKS_PER_DAY
DAYS_PER_UPDATE = 1.0 / UPDATES_PER_DAY

# Colors
C_BG = (10, 12, 16)
C_PANEL = (20, 22, 28)
C_BORDER = (40, 50, 60)
C_TEXT = (200, 210, 220)
C_TEXT_DIM = (120, 130, 140)
C_ACCENT = (0, 160, 255)
C_EDGE_STATIC = (80, 90, 100, 20) 

COLORS = {
    'S': (50, 100, 180),    # Susceptible
    'V': (0, 180, 180),     # Vaccinated 
    'L': (255, 255, 100),   # Latent
    'IA': (255, 165, 0),    # Asymptomatic
    'IS': (255, 50, 50),    # Symptomatic
    'H': (200, 50, 255),    # Hospitalized
    'R': (50, 220, 100),    # Recovered
    'D': (80, 80, 80)       # Dead
}

class Params:
    def __init__(self):
        self.pop_size = 500       
        self.init_infected = 3
        self.k_neighbors = 5      
        self.rewire_prob = 0.1    
        self.social_engagement = 1.0
        
        self.beta = 40.0            
        self.kappa = 20.0           
        self.latent_mean = 2.0      
        self.inf_mean = 10.0        
        self.asymp_prob = 0.4       
        self.shedding_symp = 1.0    
        self.shedding_asymp = 0.5
        self.superspreader_prob = 0.05
        
        self.hosp_stay_mean = 10.0
        self.base_mortality = 0.005
        self.hosp_mortality_mult = 0.5 
        self.no_bed_mult = 5.0      
        
        self.immunity_waning = 0.005 
        self.immunity_efficacy = 0.9 
        
        self.mask_compliance = 0.0
        self.mask_efficacy = 0.6
        
        self.vaccine_rate = 0.0
        self.vaccine_efficacy = 0.8
        
        self.quarantine_rate = 0.5 
        self.sim_speed = 1.0

CONFIG = Params()