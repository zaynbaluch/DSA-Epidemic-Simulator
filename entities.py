import pygame
import random
from config import COLORS, CONFIG, DAMPING
from enums import LocationType, State, AgeGroup

class Hub:
    def __init__(self, uid, x, y, r, l_type, label, capacity, risk_mult):
        self.id = uid
        self.sim_pos = pygame.math.Vector2(x, y) 
        self.graph_pos = pygame.math.Vector2(x, y)
        self.radius = r
        self.type = l_type
        self.label = label
        self.capacity = capacity
        self.risk_mult = risk_mult
        self.agents_present = [] 
        self.temp_viral_load = 0.0 
        
        self.base_color = (35, 40, 50)
        if l_type == LocationType.HOSPITAL: self.base_color = (60, 20, 40)
        elif l_type == LocationType.CEMETERY: self.base_color = (15, 15, 15)
        elif l_type == LocationType.PARK: self.base_color = (25, 40, 25)
        elif l_type == LocationType.CAFE: self.base_color = (60, 45, 30)
        elif l_type == LocationType.MARKET: self.base_color = (40, 50, 60)
        elif l_type == LocationType.QUARANTINE: self.base_color = (60, 60, 20)

    def draw(self, surface, mode="SIM"):
        if mode == "GRAPH" and self.type == LocationType.HOUSEHOLD: return

        draw_pos = self.sim_pos if mode == "SIM" else self.graph_pos
        color = list(self.base_color)
        r = self.radius if mode == "SIM" else self.radius * 0.6 
        
        pygame.draw.circle(surface, color, (int(draw_pos.x), int(draw_pos.y)), int(r))
        
        border_col = (60, 70, 80)
        if self.type == LocationType.QUARANTINE: border_col = (150, 150, 50)
        
        if self.temp_viral_load > 0.1:
            val = min(255, int(self.temp_viral_load * 50))
            border_col = (val, 50, 50)
            
        pygame.draw.circle(surface, border_col, (int(draw_pos.x), int(draw_pos.y)), int(r), 2)
        
        if self.type != LocationType.HOUSEHOLD:
            font = pygame.font.SysFont("Arial", 10, bold=True)
            txt = font.render(self.label, True, (220, 220, 220))
            text_rect = txt.get_rect(center=(int(draw_pos.x), int(draw_pos.y)))
            surface.blit(txt, text_rect)

class Person:
    def __init__(self, uid, home, age, mob):
        self.id = uid
        self.home = home
        self.age = age
        self.mobility = mob
        self.state = State.SUSCEPTIBLE
        self.vaccinated = False
        self.in_quarantine = False
        
        self.days_in_state = 0.0
        base_const = {AgeGroup.CHILD: 0.8, AgeGroup.ADULT: 0.6, AgeGroup.SENIOR: 0.3}
        self.constitution = min(1.0, max(0.1, base_const[age] + random.uniform(-0.15, 0.15)))
        self.immunity = 0.0
        
        self.latent_dur = 0
        self.inf_dur = 0
        self.peak_shedding = 0
        self.is_superspreader = (random.random() < CONFIG.superspreader_prob)
        self.hospital_stay_dur = 0
        self.masked = (random.random() < CONFIG.mask_compliance)
        
        self.assigned_hub = None
        self.target = home
        self.current_hub = home 
        self.sim_pos = self._get_random_point(home)
        self.target_pos = self.sim_pos 
        
        # Graph Physics
        self.graph_pos = pygame.math.Vector2(home.graph_pos.x, home.graph_pos.y)
        self.vel = pygame.math.Vector2(0,0)
        self.acc = pygame.math.Vector2(0,0)
        
        self.graph_neighbors = []      
        self.structural_edges = {} 
        self.permanent_affiliations = []

    def _get_random_point(self, hub):
        offset = pygame.math.Vector2(random.uniform(-1,1), random.uniform(-1,1))
        if offset.length() > 0: offset.normalize_ip()
        return hub.sim_pos + offset * random.uniform(0, hub.radius - 2)

    def set_target(self, hub):
        if self.target == hub: return
        self.target = hub
        self.target_pos = self._get_random_point(hub)

    def get_shedding(self):
        if self.state not in [State.INF_ASYMP, State.INF_SYMP, State.HOSPITALIZED]: return 0.0
        progress = self.days_in_state / self.inf_dur
        if progress < 0 or progress > 1: return 0.0
        val = (progress / 0.3) if progress < 0.3 else 1.0 - ((progress - 0.3) / 0.7)
        amt = val * self.peak_shedding
        if self.masked: amt *= (1.0 - CONFIG.mask_efficacy)
        return amt

    def move_spatial(self, dt):
        if self.state == State.DEAD:
            if self.current_hub and self.current_hub.type == LocationType.CEMETERY: return
        
        dest = self.target_pos
        dist = self.sim_pos.distance_to(dest)
        speed = 500.0 * (1.0 if self.state != State.DEAD else 0.2)
        step_dist = speed * dt * 5.0
        
        if dist <= step_dist:
            self.sim_pos = dest
            self.current_hub = self.target 
            if self.state != State.DEAD and random.random() < 0.05:
                self.sim_pos += pygame.math.Vector2(random.uniform(-0.5,0.5), random.uniform(-0.5,0.5))
        else:
            self.current_hub = None
            direction = dest - self.sim_pos
            if direction.length() > 0: direction.normalize_ip()
            self.sim_pos += direction * step_dist

        self.update_edge_weights(dt)

    def update_edge_weights(self, dt):
        fade_speed = 5.0 * dt 
        for hub, weight in self.structural_edges.items():
            target_w = 1.0 if self.current_hub == hub else 0.0
            
            if weight < target_w:
                weight = min(target_w, weight + fade_speed)
            elif weight > target_w:
                weight = max(target_w, weight - fade_speed)
            self.structural_edges[hub] = weight

    def update_physics(self):
        self.vel += self.acc
        self.vel *= DAMPING
        if self.vel.length() > 8: self.vel.scale_to_length(8) 
        self.graph_pos += self.vel
        self.acc *= 0

    def draw(self, surface, mode):
        key = 'S'
        if self.state == State.LATENT: key = 'L'
        elif self.state == State.INF_ASYMP: key = 'IA'
        elif self.state == State.INF_SYMP: key = 'IS'
        elif self.state == State.HOSPITALIZED: key = 'H'
        elif self.state == State.RECOVERED: key = 'R'
        elif self.state == State.DEAD: key = 'D'
        
        color = COLORS[key]
        if self.state == State.SUSCEPTIBLE and self.vaccinated:
            color = COLORS['V']

        pos = self.sim_pos if mode == "SIM" else self.graph_pos
        radius = 3 if mode == "SIM" else 4
        
        pygame.draw.circle(surface, color, (int(pos.x), int(pos.y)), radius)
        if mode == "GRAPH":
            pygame.draw.circle(surface, (20,20,20), (int(pos.x), int(pos.y)), radius, 1)